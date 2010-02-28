#!/usr/bin/python
#
# Part of Objavi2, which turns html manuals into books.  This emulates
# the Booki-epub-Espri interface for old TWiki books.
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

import re, traceback
#from pprint import pformat

from objavi.twiki_wrapper import TWikiBook, get_book_list
from objavi.cgi_utils import parse_args, optionise, output_blob_and_exit
from objavi.book_utils import shift_file, log
from objavi import config


def make_booki_package(server, bookid, use_cache=False):
    """Extract all chapters from the specified book, as well as
    associated images and metadata, and zip it all up for conversion
    to epub.

    If cache is true, images that have been fetched on previous runs
    will be reused.
    """
    book = TWikiBook(bookid, server)
    return book.make_bookizip(use_cache=use_cache)


# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).
ARG_VALIDATORS = {
    "book": re.compile(r'^(\w+/?)*\w+$').match, # can be: BlahBlah/Blah_Blah
    "server": config.SERVER_DEFAULTS.__contains__,
    "use-cache": None,
    'mode': ('zip', 'html').__contains__,
    "all": ['all', 'skip-existing'].__contains__,
}

if __name__ == '__main__':

    args = parse_args(ARG_VALIDATORS)
    use_cache = args.get('use-cache')
    if use_cache is None:
        use_cache = (os.environ.get('HTTP_HOST') in config.USE_IMG_CACHE_ALWAYS_HOSTS)

    make_all = args.get('all')
    if 'server' in args and 'book' in args:
        zfn = make_booki_package(args['server'], args['book'], use_cache)
        fn = shift_file(zfn, config.BOOKI_BOOK_DIR)
        ziplink = '<p><a href="%s">%s zip file.</a></p>' % (fn, args['book'])

        mode = args.get('mode', 'html')
        if mode == 'zip':
            f = open(fn)
            data = f.read()
            f.close()
            output_blob_and_exit(data, config.BOOKIZIP_MIMETYPE, args['book'] + '.zip')

    elif 'server' in args and make_all is not None:
        links = []
        for book in get_book_list(args['server']):
            if make_all == 'skip-existing' and book + '.zip' in os.listdir(config.BOOKI_BOOK_DIR):
                log("skipping %s" % book)
                continue
            try:
                zfn = make_booki_package(args['server'], book, use_cache=use_cache)
                fn = shift_file(zfn, config.BOOKI_BOOK_DIR)
                links.append('<a href="%s">%s</a> ' % (fn, book))
            except Exception:
                log('FAILED to make book "%s"' % book)
                traceback.print_exc()
        ziplink = ''.join(links)
    else:
        ziplink = ''

    print "Content-type: text/html; charset=utf-8\n"
    f = open('templates/booki-twiki-gateway.html')
    template = f.read()
    f.close()

    print template % {'ziplink': ziplink,
                      'server-list': optionise(sorted(config.SERVER_DEFAULTS.keys()))}

