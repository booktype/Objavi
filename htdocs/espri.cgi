#!/usr/bin/python
#
# Part of the Objavi2 package.  This script imports e-books into Booki
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
os.chdir('..')
sys.path.insert(0, os.path.abspath('.'))

import time
from urllib2 import urlopen, URLError
from urllib import urlencode, unquote
from urlparse import urlsplit
import traceback, tempfile
from subprocess import check_call, CalledProcessError

from objavi import epub
from objavi.book_utils import log
from objavi.cgi_utils import output_blob_and_exit, parse_args, print_template_and_exit, output_blob_and_shut_up
from objavi.cgi_utils import is_utf8, is_url, super_bleach
from objavi import config

IA_EPUB_URL = "http://www.archive.org/download/%s/%s.epub"

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
    #log(sys.stdout, sys.stderr, sys.stdin)


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


def espri(epuburl, bookid):
    log(epuburl, bookid)
    f = urlopen(epuburl)
    s = f.read()
    f.close()
    e = epub.Epub()
    e.load(s)
    e.parse_meta()
    e.parse_opf()
    e.parse_ncx()
    zipfile = '%s/%s.zip' % (config.BOOKI_BOOK_DIR, bookid)    
    e.make_bookizip(zipfile)

def ia_espri(book_id):
    epuburl = IA_EPUB_URL % (book_id, book_id)
    log(epuburl)
    espri(epuburl, book_id)
    return bookid

def inet_espri(epuburl):
    tainted_name = unquote(os.path.basename(urlsplit(epuburl).path))
    filename = super_bleach(tainted_name)
    if filename.lower().endswith('-epub'):
        filename = filename[:-5]
    bookid = '%s-%s' % (filename, time.strftime('%F_%T'))
    espri(epuburl, bookid)
    return bookid


TIMEOUT_CMD = 'timeout'
WIKIBOOKS_TIMEOUT = '600'
WIKIBOOKS_CMD = 'wikibooks2epub'
WIKIBOOKS_CACHE = 'cache/wikibooks'

class TimeoutError(Exception):
    pass

def wikibooks_espri(wiki_url):
    """Wikibooks import using the wikibooks2epub script by Jan Gerber
    to first convert the wikibook to an epub, which can then be turned
    into a bookizip via the espri function.
    """
    os.environ['oxCACHE'] = WIKIBOOKS_CACHE
    tainted_name = unquote(os.path.basename(urlsplit(wiki_url).path))
    bookid = "%s-%s" % (super_bleach(tainted_name),
                        time.strftime('%Y.%m.%d-%H.%M.%S'))
    workdir = tempfile.mkdtemp(prefix=bookid, dir=config.TMPDIR)
    os.chmod(workdir, 0755)
    epub_file = os.path.join(workdir, bookid + '.epub')
    epub_url = 'file://' + os.path.abspath(epub_file)
    #epub_url = 'http://localhost/' + epub_file

    #the wikibooks importer is a separate process, so run that, then collect the epub.
    cmd = [TIMEOUT_CMD, WIKIBOOKS_TIMEOUT,
           WIKIBOOKS_CMD,
           '-i', wiki_url,
           '-o', epub_file
           ]
    log(cmd)

    try:
        check_call(cmd)
    except CalledProcessError, e:
        if e.returncode == 137:
            raise TimeoutError('Wikibooks took too long (over %s seconds)' % WIKIBOOKS_TIMEOUT)
        raise

    espri(epub_url, bookid)
    return bookid




SOURCES = {
    'archive.org': {'function': ia_espri},
    'url': {'function': inet_espri},
    'wikibooks': {'function': wikibooks_espri},
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
