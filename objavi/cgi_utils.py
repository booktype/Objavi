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
import cgi, re
import urllib
from getopt import gnu_getopt

from objavi.book_utils import log
from objavi import config

SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost')

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

def super_bleach(dirty_name):
    """Replace potentially nasty characters with safe ones."""
    # a bit drastic: refine if it matters
    name = ''.join((x if x.isalnum() else '-') for x in dirty_name)
    if name:
        return name
    return 'untitled'


## common between different versions of objavi

def get_server_list():
    return sorted(k for k, v in config.SERVER_DEFAULTS.items() if v['display'])

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
                                  for k, v in config.PAGE_SIZE_DATA.iteritems())
            ]

def url2path(url):
    """convert htdocs-relative addresses to local file paths"""
    return config.HTDOCS + '/' + url.lstrip('/')

_htdocs = os.path.abspath(config.HTDOCS)
def path2url(path, default='/missing_path?%(path)s', full=False):
    """convert local file paths to htdocs-relative addresses.  If the
    file is not in the web tree, return default"""
    if path.startswith('file:///'):
        path = path[7:]
    path = os.path.abspath(path)
    if path.startswith(_htdocs):
        path = path[len(_htdocs):]
    else:
        path = default % {'path': urllib.quote(path)}
    if full:
        return 'http://%s%s' % (SERVER_NAME, path)
    return path


def get_default_css(server=config.DEFAULT_SERVER, mode='book'):
    """Get the default CSS text for the selected server"""
    log(server)
    cssfile = url2path(config.SERVER_DEFAULTS[server]['css-%s' % mode])
    log(cssfile)
    f = open(cssfile)
    s = f.read()
    f.close()
    return s

def font_links():
    """Links to various example pdfs."""
    links = []
    for script in os.listdir(config.FONT_EXAMPLE_SCRIPT_DIR):
        if not script.isalnum():
            log("warning: font-sample %s won't work; skipping" % script)
            continue
        links.append('<a href="%s?script=%s">%s</a>' % (config.FONT_LIST_URL, script, script))
    return links

## Helper functions for parse_args

def isfloat(s):
    #spaces?, digits!, dot?, digits?, spaces?
    #return re.compile(r'^\s*[+-]?\d+\.?\d*\s*$').match
    try:
        float(s)
        return True
    except ValueError:
        return False

def isfloat_or_auto(s):
    return isfloat(s) or s.lower() in ('', 'auto')

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

#output functions

def output_blob_and_exit(blob, content_type="application/octet-stream", filename=None):
    print 'Content-type: %s\nContent-length: %s' % (content_type, len(blob))
    if filename is not None:
        print 'Content-Disposition: attachment; filename="%s"' % filename
    print
    print blob
    sys.exit()

def output_blob_and_shut_up(blob, content_type="application/octet-stream", filename=None):
    print 'Content-type: %s\nContent-length: %s' % (content_type, len(blob))
    if filename is not None:
        print 'Content-Disposition: attachment; filename="%s"' % filename
    print
    print blob
    sys.stdout.flush()
    devnull = open('/dev/null', 'w')
    os.dup2(devnull.fileno(), sys.stdout.fileno())
    log(sys.stdout)

##Decorator function for output
def output_and_exit(f, content_type="text/html; charset=utf-8"):
    """Decorator: prefix function output with http headers and exit
    immediately after."""
    def output(*args, **kwargs):
        content = f(*args, **kwargs)
        print "Content-type: %s" % content_type
        print "Content-length: %s" % len(content)
        print
        print content
        sys.exit()
    return output

@output_and_exit
def print_template_and_exit(template, mapping):
    f = open(template)
    string = f.read()
    f.close()
    return string % mapping

def try_to_kill(pid, signal=15):
    log('kill -%s %s ' % (signal, pid))
    try:
        os.kill(int(pid), signal)
    except OSError, e:
        log('PID %s seems dead (kill -%s gives %s)' % (pid, signal, e))

