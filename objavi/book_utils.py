# Part of Objavi2, which turns html manuals into books
#
# Copyright (C) 2009 Douglas Bagnall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
General utility functions.
"""

import os, sys
import time
from subprocess import Popen, PIPE

#from objavi.fmbook import log
from objavi import config

#general, non-cgi functions
def init_log():
    """Try to redirect stderr to the log file.  If it doesn't work,
    leave stderr as it is."""
    if config.REDIRECT_LOG:
        logfile = os.path.join(config.LOGDIR, 'objavi.log')
        try:
            size = os.stat(logfile).st_size
            if size > config.LOG_ROTATE_SIZE:
                oldlog = os.path.join(config.LOGDIR, time.strftime('objavi-%Y-%m-%d+%H-%M-%S.log'))
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

def make_book_name(book, server, suffix='.pdf', timestamp=None):
    lang = config.SERVER_DEFAULTS.get(server, config.SERVER_DEFAULTS[config.DEFAULT_SERVER])['lang']
    book = ''.join(x for x in book if x.isalnum())
    if timestamp is None:
        timestamp = time.strftime('%Y.%m.%d-%H.%M.%S')
    return '%s-%s-%s%s' % (book, lang,
                           timestamp,
                           suffix)

def guess_lang(server, book):
    lang = config.SERVER_DEFAULTS[server].get('lang')
    if lang is None and '_' in book:
        lang = book[book.rindex('_') + 1:]
    return lang

def guess_text_dir(server, book):
    try:
        dir = config.SERVER_DEFAULTS[server]['dir']
    except KeyError:
        dir = None
    if dir not in ('LTR', 'RTL'):
        log("server %s, book %s: no specified dir (%s)" %(server, book, dir))
        if '_' in book:
            lang = book[book.rindex('_') + 1:]
            dir = config.LANGUAGE_DIR.get(lang, 'LTR')
        elif '.' in server:
            lang = server[:server.index('.')]
            dir = config.LANGUAGE_DIR.get(lang, 'LTR')
        else:
            dir = 'LTR'
    log("server %s, book %s: found dir %s" %(server, book, dir))
    return dir

def run(cmd):
    try:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
    except Exception:
        log("Failed on command: %r" % cmd)
        raise
    log("%s\n%s returned %s and produced\nstdout:%s\nstderr:%s" %
        (' '.join(cmd), cmd[0], p.poll(), out, err))

def shift_file(fn, dir, backup='~'):
    """Shift a file and save backup (only works on same filesystem)"""
    base = os.path.basename(fn)
    dest = os.path.join(dir, base)
    if backup and os.path.exists(dest):
        os.rename(dest, dest + backup)
    os.rename(fn, dest)
    return dest

class ObjaviError(Exception):
    pass
