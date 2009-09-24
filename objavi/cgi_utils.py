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

from objavi.fmbook import log
from objavi import config

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

