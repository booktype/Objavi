# Part of Objavi2, which turns html manuals into books
#
# Copyright (C) 2009 Douglas Bagnall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
General utility functions.
"""

import os, sys
import shutil
import time, re
import fnmatch
from subprocess import Popen, PIPE
from urllib2 import urlopen, HTTPError
import htmlentitydefs

#from objavi.fmbook import log
from objavi import config

#general, non-cgi functions
def init_log(logname='objavi'):
    """Try to redirect stderr to the log file.  If it doesn't work,
    leave stderr as it is."""
    if config.REDIRECT_LOG:
        logfile = os.path.join(config.LOGDIR, logname + '.log')
        try:
            size = os.stat(logfile).st_size
            if size > config.LOG_ROTATE_SIZE:
                oldlog = os.path.join(config.LOGDIR, time.strftime(logname + '-%Y-%m-%d+%H-%M-%S.log'))
                f = open(logfile, 'a')
                print >> f, "CLOSING LOG at size %s, renaming to %s" % (size, oldlog)
                f.close()
                os.rename(logfile, oldlog)
        except OSError, e:
            log(e) # goes to original stderr
        try:
            f = open(logfile, 'a')
            sys.stderr.flush()
            os.dup2(f.fileno(), sys.stderr.fileno())
            # reassign the object as well as dup()ing, in case it closes down out of scope.
            sys.stderr = f
        except (IOError, OSError), e:
            log(e)
            return

def log(*messages, **kwargs):
    """Send the messages to the appropriate place (stderr, or syslog).
    If a <debug> keyword is specified, the message is only printed if
    its value is in the global DEBUG_MODES."""
    if 'debug' not in kwargs or config.DEBUG_ALL or kwargs['debug'] in config.DEBUG_MODES:
        for m in messages:
            try:
                print >> sys.stderr, m
            except Exception:
                print >> sys.stderr, repr(m)
        sys.stderr.flush()

def log_types(*args, **kwargs):
    """Log the type of the messages as well as their value (size constrained)."""
    size = kwargs.get('size', 50)
    for a in args:
        try:
            s = ("%s" % (a,))
        except Exception:
            try:
                s = ("%r" % (a,))
            except Exception:
                s = '<UNPRINTABLE!>'
        log("%s: %s" % (type(a), s[:size]))


def get_server_defaults(server):
    """Returns the defaults dictionary for the specified server.
    """
    defaults = config.SERVER_DEFAULTS.get(server)
    if defaults:
        # found verbatim
        return defaults
    for pattern, defaults in config.SERVER_DEFAULTS.iteritems():
        if fnmatch.fnmatch(server, pattern):
            return defaults


def make_book_name(book, server, suffix='.pdf', timestamp=None):
    lang = guess_lang(server, book)
    book = ''.join(x for x in book if x.isalnum())
    if timestamp is None:
        timestamp = time.strftime('%Y.%m.%d-%H.%M.%S')
    return '%s-%s-%s%s' % (book, lang,
                           timestamp,
                           suffix)

def guess_lang(server, book):
    if server is None:
        server = config.DEFAULT_SERVER
    lang = get_server_defaults(server).get('lang')
    if lang is None and '_' in book:
        lang = book[book.rindex('_') + 1:]
    return lang

def guess_text_dir(server, book):
    dir = get_server_defaults(server).get('dir')
    if dir not in ('LTR', 'RTL'):
        log("server %s, book %s: no specified dir (%s)" %(server, book, dir))
        lang = guess_lang(server, book)
        dir = config.LANGUAGE_DIR.get(lang, config.DEFAULT_DIR)
    log("server %s, book %s: found dir %s" %(server, book, dir))
    return dir

def guess_page_number_style(lang, dir):
    if lang in config.BOILERPLATE_HTML:
        return lang
    elif dir in config.BOILERPLATE_HTML:
        return dir
    return config.DEFAULT_DIR



def get_number_localiser(locale):
    """Create a function that will convert a number into a string in
    the locale appropriate script.  Often the returned function is
    simply 'str'."""
    offset = config.LOCALISED_DIGITS.get(locale)
    if offset is None:
        return str

    def _localiser(n):
        out = []
        for c in str(n):
            if c.isdigit():
                c = unichr(ord(c) + offset)
            out.append(c)
        return ''.join(out)#.encode('UTF-8')

    return _localiser


def run(cmd):
    try:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
    except Exception:
        log("Failed on command: %r" % cmd)
        raise
    log("%s\n%s returned %s and produced\nstdout:%s\nstderr:%s" %
        (' '.join(cmd), cmd[0], p.poll(), out, err))
    return p.poll()

def shift_file(fn, dir, backup='~'):
    """Shift a file and save backup (only works on same filesystem)"""
    log("shifting file %r to %s" % (fn, dir))
    base = os.path.basename(fn)
    dest = os.path.join(dir, base)
    if backup and os.path.exists(dest):
        os.rename(dest, dest + backup)
    shutil.move(fn, dest)
    return dest

class ObjaviError(Exception):
    pass


def decode_html_entities(text):
    for encoding in ('ascii', 'utf-8', 'iso-8859-1'):
        try:
            text = text.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    def fixup(m):
        entity = m.group(0)
        try:
            if entity[:3] == "&#x":
                return unichr(int(entity[3:-1], 16))
            elif entity[:2] == "&#":
                return unichr(int(entity[2:-1]))
            else:
                return unichr(htmlentitydefs.name2codepoint[entity[1:-1]])
        except (ValueError, KeyError):
            log("ignoring bad entity %s" % entity)
            return entity
    return re.sub("&#x[0-9a-fA-F]+;|&#[0-9]+;|&[0-9a-zA-Z]+;", fixup, text).encode('utf-8')

def url_fetch(url, suppress_error=False):
    try:
        f = urlopen(url)
        s = f.read()
        f.close()
        return s
    except HTTPError, e:
        log("HTTPError '%s' trying to fetch '%s'" % (e, url))
        if not suppress_error:
            raise
    #returns None is error is suppressed

def url_fetch2(url, suppress_error=False):
    try:
        f = urlopen(url)
        s = f.read()
        f.close()
        return (s, f.info()['Content-type'])
    except HTTPError, e:
        log("HTTPError '%s' trying to fetch '%s'" % (e, url))
        if not suppress_error:
            raise
    #returns None is error is suppressed


def get_page_settings(args):
    """Find the size and any optional layout settings.

    args['booksize'] is either a keyword describing a size or
    'custom'.  If it is custom, the form is inspected for specific
    dimensions -- otherwise these are ignored.

    The margins, gutter, number of columns, and column
    margins all set themselves automatically based on the page
    dimensions, but they can be overridden.  Any that are are
    collected here."""
    # get all the values including sizes first
    # the sizes are found as 'page_width' and 'page_height',
    # but the Book class expects them as a 'pointsize' tuple, so
    # they are easily ignored.
    settings = {}
    for k, extrema in config.PAGE_EXTREMA.iteritems():
        try:
            v = float(args.get(k))
        except (ValueError, TypeError):
            #log("don't like %r as a float value for %s!" % (args.get(k), k))
            continue
        min_val, max_val, multiplier = extrema
        if v < min_val or v > max_val:
            log('rejecting %s: outside %s' % (v, extrema))
        else:
            log('found %s=%s' % (k, v))
            settings[k] = v * multiplier #convert to points in many cases

    # now if args['size'] is not 'custom', the width and height found
    # above are ignored.
    size = args.get('booksize')
    settings.update(config.PAGE_SIZE_DATA[size])

    #if args['mode'] is 'newspaper', then the number of columns is
    #automatically determined unless set -- otherwise default is 1.
    if args.get('mode') == 'newspaper' and settings.get('columns') is None:
        settings['columns'] = 'auto'

    if args.get('grey_scale'):
        settings['grey_scale'] = True

    if size == 'custom':
        #will raise KeyError if width, height aren't set
        settings['pointsize'] = (settings['page_width'], settings['page_height'])
        del settings['page_width']
        del settings['page_height']

    settings['engine'] = args.get('engine', config.DEFAULT_ENGINE)
    return settings
