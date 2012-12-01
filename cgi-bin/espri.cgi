#!/usr/bin/python
#
# Part of the Objavi2 package.  This script imports e-books into Booki
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

import os, sys
os.chdir('..')
os.putenv("OBJAVI_PROJECT_DIR", os.getcwd())
sys.path.insert(0, os.path.abspath('./lib'))

import time
import traceback
from urllib import urlencode
from urllib2 import urlopen, URLError

from objavi import espri
from objavi import epub
from objavi.book_utils import log, init_log
from objavi.cgi_utils import output_blob_and_exit, parse_args, print_template_and_exit, output_blob_and_shut_up
from objavi.cgi_utils import is_utf8, is_url
from objavi import config



def print_form_and_exit(booklink):
    print_template_and_exit('templates/espri.html',
                            {'booklink': booklink, }
                            )

def async_start(content, mimetype):
    """Begin (and in many cases, finish) http output.
    In asynchronous modes, fork and close down stdout.
    """
    output_blob_and_shut_up(content, mimetype)
    log(sys.stdout, sys.stderr, sys.stdin)
    if os.fork():
        os._exit(0)
    sys.stdout.close()
    sys.stdin.close()


def async_callback(callback_url, **kwargs):
    """Call the callback url with each message."""
    pid = os.fork()
    if pid:
        log('child %s is doing callback with message %r' % (pid, kwargs, ))
        return
    data = urlencode(kwargs)
    try:
        f = urlopen(callback_url, data)
        time.sleep(2)
        f.close()
    except URLError, e:
        traceback.print_exc()
        log("ERROR in callback:\n %r\n %s %s" % (e.url, e.code, e.msg))
    os._exit(0)


SOURCES = {
    'archive.org': {'function': espri.ia_espri},
    'url': {'function': espri.inet_espri},
    'wikibooks': {'function': espri.wikibooks_espri},
}

ARG_VALIDATORS = {
    "source": SOURCES.__contains__,
    "book": is_utf8,
    "url": is_url,  #obsolete
    'mode': ('zip', 'html', 'callback').__contains__,
    'callback': is_url,
}


def ensure_backwards_compatibility(args):
    """Mutate args to match previous API"""
    if 'url' in args:
        args['source'] = 'url'
        args['book'] = args['url']
    if 'source' not in args:
        args['source'] = 'archive.org'
    if 'callback' in args and 'mode' not in args:
        args['mode'] = 'callback'


if __name__ == '__main__':
    init_log("espri")
    args = parse_args(ARG_VALIDATORS)
    ensure_backwards_compatibility(args)
    mode = args.get('mode', 'html')
    book = args.get('book')
    source = args.get('source', 'archive.org')
    source_fn = SOURCES.get(source)['function']

    if mode == 'callback':
        callback_url = args['callback']
        async_start('OK, got it...  will call %r when done' % (callback_url,),
                    'text/plain')
    filename = None
    url = None
    if book is not None:
        try:
            filename = source_fn(book)
            url = '%s/%s' % (config.BOOKI_BOOK_URL, filename)
            book_link = '<p>Download <a href="%s">%s</a>.</p>' % (url, url)
        except Exception, e:
            traceback.print_exc()
            log(e, args)
            book_link = '<p>Error: <b>%s</b> when trying to get <b>%s</b></p>' % (e, book)
            if mode != 'html':
                raise
    else:
        book_link = ''

    if mode == 'callback':
        async_callback(callback_url, url=url)

    elif mode == 'zip' and filename is not None:
        f = open(os.path.join(config.BOOKI_BOOK_DIR, filename))
        data = f.read()
        f.close()
        output_blob_and_exit(data, config.BOOKIZIP_MIMETYPE,
                             filename)
    else:
        log(book_link)
        print_form_and_exit(book_link)
    log('done!')
