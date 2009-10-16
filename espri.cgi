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
import re
from urllib2 import urlopen, HTTPError
import traceback

from objavi import epub
from objavi.cgi_utils import shift_file, parse_args, optionise, print_template
from objavi.cgi_utils import output_blob_and_exit, log
from objavi import config

IA_EPUB_URL = "http://www.archive.org/download/%s/%s.epub"

def print_form(booklink):
    print_template('templates/espri.html',
                   {'booklink': booklink,
                    }
                   )

def ia_espri(book_id):
    epuburl = IA_EPUB_URL % (book_id, book_id)
    log(epuburl)
    zipurl = '%s/%s.zip' % (config.BOOKI_BOOK_DIR, book_id)
    f = urlopen(epuburl)
    s = f.read()
    f.close()
    e = epub.Epub()
    e.load(s)
    e.parse_meta()
    e.parse_opf()
    e.parse_ncx()
    e.make_bookizip(zipurl)
    return zipurl

def is_name(s):
    if re.match(r'^[\w-]+$', s):
        return s

ARG_VALIDATORS = {
    "book": is_name,
    'mode': ('zip', 'html').__contains__
}

if __name__ == '__main__':
    args = parse_args(ARG_VALIDATORS)
    if 'book' in args:
        try:
            url = ia_espri(args['book'])
            book_link = '<p>Download <a href="%s">%s booki-zip</a>.</p>' % (url, args['book'])
        except Exception, e:
            traceback.print_exc()
            log(e, args)
            book_link = '<p>Error: <b>%s</b> when trying to get %s</p>' % (e, args['book'])
            if mode == 'zip':
                raise
    else:
        book_link = ''

    mode = args.get('mode', 'html')
    if mode == 'zip':
        f = open(url)
        data = f.read()
        f.close()
        output_blob_and_exit(data, 'application/x-booki+zip', args['book'] + '.zip')
    else:
        print_form(book_link)

