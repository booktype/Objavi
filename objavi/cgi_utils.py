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

import os, sys
import cgi
from getopt import gnu_getopt

#from objavi.fmbook import log
from objavi import config


def log(*messages, **kwargs):
    """Send the messages to the appropriate place (stderr, or syslog).
    If a <debug> keyword is specified, the message is only printed if
    its value ias in the global DEBUG_MODES."""
    if 'debug' not in kwargs or config.DEBUG_ALL or kwargs['debug'] in config.DEBUG_MODES:
        for m in messages:
            try:
                print >> sys.stderr, m
            except Exception:
                print >> sys.stderr, repr(m)


def parse_args(arg_validators):
    """Read and validate CGI or commandline arguments, putting the
    good ones into the returned dictionary.  Command line arguments
    should be in the form --title='A Book'.
    """
    query = cgi.FieldStorage()
    options, args = gnu_getopt(sys.argv[1:], '', [x + '=' for x in arg_validators])
    options = dict(options)
    data = {}
    for key, validator in arg_validators.items():
        value = query.getfirst(key, options.get('--' + key, None))
        log('%s: %s' % (key, value), debug='STARTUP')
        if value is not None:
            if validator is not None and not validator(value):
                log("argument '%s' is not valid ('%s')" % (key, value))
                continue
            data[key] = value

    log(data, debug='STARTUP')
    return data

def clean_args(arg_convertors):
    """Like parse_args, but instead of the validator functions
    returning true or false, they return None if the argument is
    invalid, and a cleansed version if the argument is good.
    """
    query = cgi.FieldStorage()
    options, args = gnu_getopt(sys.argv[1:], '', [x + '=' for x in arg_convertors])
    options = dict(options)
    data = {}
    for key, convertor in arg_convertors.items():
        raw_value = query.getfirst(key, options.get('--' + key, None))
        if raw_value is not None:
            val = convertor(raw_value)
            if val is None:
                log("argument '%s' is not valid ('%s')" % (key, raw_value))
                continue
            data[key] = val
    return data


## Helper functions for parse_args & clean_args

def is_url(s):
    """Check whether the string approximates a valid http URL."""
    s = s.strip()
    if not '://' in s:
        s = 'http://' + s
    m = re.match(r'^https?://'
                 r'(?:(?:[a-z0-9]+(?:-*[a-z0-9]+)*\.)+[a-z]{2,8}|'
                 r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                 r'(?::\d+)?'
                 r'(?:/?|/\S+)$', s, re.I
                 )
    if not m:
        return False
    return s

def is_name(s):
    if re.match(r'^[\w-]+$', s):
        return s


## Formatting of lists

def optionise(items, default=None):
    """Make a list of strings into an html option string, as would fit
    inside <select> tags."""
    options = []
    for x in items:
        if isinstance(x, str):
            x = (x, x)
        if len(x) == 2:
            # couple: value, name
            if x[0] == default:
                options.append('<option selected="selected" value="%s">%s</option>' % x)
            else:
                options.append('<option value="%s">%s</option>' % x)
        else:
            # triple: value, class, name
            if x[0] == default:
                options.append('<option selected="selected" value="%s" class="%s">%s</option>' % x)
            else:
                options.append('<option value="%s" class="%s">%s</option>' % x)

    return '\n'.join(options)


def listify(items):
    """Make a list of strings into html <li> items, to fit in a <ul>
    or <ol> element."""
    return '\n'.join('<li>%s</li>' % x for x in items)


def shift_file(fn, dir, backup='~'):
    """Shift a file and save backup (only works on same filesystem)"""
    base = os.path.basename(fn)
    dest = os.path.join(dir, base)
    if backup and os.path.exists(dest):
        os.rename(dest, dest + backup)
    os.rename(fn, dest)
    return dest


##Decorator functions for output

def output_and_exit(f, content_type="text/html; charset=utf-8"):
    """Decorator: prefix function output with http headers and exit
    immediately after."""
    def output(args):
        print "Content-type: %s\n" % (content_type,)
        f(args)
        sys.exit()
    return output
