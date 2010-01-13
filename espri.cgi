#!/usr/bin/python
#
# Part of Espri, an importer of e-books into Booki
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
import re, time
from urllib2 import urlopen, HTTPError
from urlparse import urlsplit
from urllib import unquote
import traceback

from objavi import epub
from objavi.book_utils import log
from objavi.cgi_utils import output_blob_and_exit, is_name, is_url, parse_args, print_template
from objavi import config

IA_EPUB_URL = "http://www.archive.org/download/%s/%s.epub"

def print_form(booklink):
    print_template('templates/espri.html',
                   {'booklink': booklink,
                    }
                   )

def espri(epuburl, zipurl):
    f = urlopen(epuburl)
    s = f.read()
    f.close()
    e = epub.Epub()
    e.load(s)
    e.parse_meta()
    e.parse_opf()
    e.parse_ncx()
    e.make_bookizip(zipurl)

def ia_espri(book_id):
    epuburl = IA_EPUB_URL % (book_id, book_id)
    log(epuburl)
    zipurl = '%s/%s.zip' % (config.BOOKI_BOOK_DIR, book_id)
    espri(epuburl, zipurl)
    return zipurl

def inet_espri(epuburl):
    filename = '_'.join(unquote(os.path.basename(urlsplit(epuburl).path)).split())
    if filename.lower().endswith('.epub'):
        filename = filename[:-5]
    zipurl = '%s/%s-%s.zip' % (config.BOOKI_BOOK_DIR, filename, time.strftime('%F_%T'))
    espri(epuburl, zipurl)
    return zipurl


ARG_VALIDATORS = {
    "book": is_name,
    "url": is_url,
    'mode': ('zip', 'html').__contains__
}

if __name__ == '__main__':
    args = parse_args(ARG_VALIDATORS)
    mode = args.get('mode', 'html')
    if 'book' in args or 'url' in args:
        if 'book' in args:
            source = args['book']
            fn = ia_espri
        else:
            source = args['url']
            fn = inet_espri
        try:
            url = fn(source)
            book_link = '<p>Download <a href="%s">%s</a>.</p>' % (url, url)
        except Exception, e:
            traceback.print_exc()
            log(e, args)
            book_link = '<p>Error: <b>%s</b> when trying to get <b>%s</b></p>' % (e, source)
            if mode == 'zip':
                raise
    else:
        book_link = ''

    if mode == 'zip':
        f = open(url)
        data = f.read()
        f.close()
        output_blob_and_exit(data, config.BOOKIZIP_MIMETYPE, source + '.zip')
    else:
        print_form(book_link)

