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

import os
import re
import urllib

from django.conf import settings

from objavi.book_utils import log
from objavi import config


def super_bleach(dirty_name):
    """Replace potentially nasty characters with safe ones."""
    # a bit drastic: refine if it matters
    name = ''.join((x if x.isalnum() else '-') for x in dirty_name)
    if name:
        return name
    return 'untitled'


## common between different versions of objavi

def get_size_list():
    #order by increasing areal size.
    def calc_size(name, pointsize, klass):
        if pointsize:
            mmx = pointsize[0] * config.POINT_2_MM
            mmy = pointsize[1] * config.POINT_2_MM
            return (mmx * mmy, name, klass,
                    '%s (%dmm x %dmm)' % (name, mmx, mmy))

        return (0, name, klass, name) # presumably 'custom'

    return [x[1:] for x in sorted(calc_size(k, v.get('pointsize'), v.get('class', ''))
                                  for k, v in config.PAGE_SIZE_DATA.iteritems() if v.get('display'))
            ]

def path2url(path, default='/missing_path?%(path)s'):
    """Converts absolute local file paths to absolute URL addresses.

    If the specified path is not absolute, throws an exception.
    If the file is not in the web tree, returns default.
    """
    if path.startswith('file:///'):
        path = path[7:]

    if not os.path.isabs(path):
        raise RuntimeError("specified path must be absolute")

    if path.startswith(config.STATIC_ROOT):
        return "%s/%s" % (config.STATIC_URL, path[len(config.STATIC_ROOT):])
    elif path.startswith(config.DATA_ROOT):
        return "%s/%s" % (config.DATA_URL, path[len(config.DATA_ROOT):])
    else:
        path = default % {'path': urllib.quote(path)}
        return '%s/%s' % (settings.OBJAVI_URL, path)


def font_links():
    """Links to various example pdfs."""
    links = []
    for script in os.listdir(config.FONT_EXAMPLE_SCRIPT_DIR):
        if not script.isalnum():
            log("warning: font-sample %s won't work; skipping" % script)
            continue
        links.append('<a href="%s?script=%s">%s</a>' % (config.FONT_LIST_URL, script, script))
    return links


def font_list():
    try:
        font_list_file = open(config.FONT_LIST_INCLUDE, "r")
    except IOError:
        return ['Font lists not yet generated']
    list = []
    for line in font_list_file:
        line = line.strip()
        if line:
            list.append(line)
    return list


## Helper functions for parse_args

def is_float(s):
    #spaces?, digits!, dot?, digits?, spaces?
    #return re.compile(r'^\s*[+-]?\d+\.?\d*\s*$').match
    try:
        float(s)
        return True
    except ValueError:
        return False

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def is_float_or_auto(s):
    return is_float(s) or s.lower() in ('', 'auto')

def is_int_or_auto(s):
    return is_int(s) or s.lower() in ('', 'auto')

def is_isbn(s):
    # 10 or 13 digits with any number of hyphens, perhaps with check-digit missing
    s = s.replace('-', '')
    return (re.match(r'^\d+[\dXx*]$', s) and len(s) in (9, 10, 12, 13))

def is_url(s):
    """Check whether the string approximates a valid http URL."""
    s = s.strip()
    if not '://' in s:
        s = 'http://' + s
    return re.match(r'^https?://'
                    r'(?:(?:[a-z0-9]+(?:-*[a-z0-9]+)*\.)+[a-z]{2,8}|'
                    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                    r'(?::\d+)?'
                    r'(?:/?|/\S+)$', s, re.I
                    )

def is_name(s):
    return re.match(r'^[\w-]+$', s)

def is_utf8(s):
    try:
        s.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

def never_ok(s):
    return False



def try_to_kill(pid, signal=15):
    log('kill -%s %s ' % (signal, pid))
    try:
        os.kill(int(pid), signal)
    except OSError, e:
        log('PID %s seems dead (kill -%s gives %s)' % (pid, signal, e))
