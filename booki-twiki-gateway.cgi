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
import re, time
from pprint import pformat

from objavi.fmbook import log, Book
from objavi.cgi_utils import parse_args, optionise
from objavi import config

from booki.xhtml_utils import MEDIATYPES, EpubChapter, BookiZip

DEST_DIR = 'booki-books'


def make_booki_package(server, bookid, clean=False, use_cache=False):
    """Extract all chapters from the specified book, as well as
    associated images and metadata, and zip it all up for conversion
    to epub.

    If clean is True, the chapters will be cleaned up and converted to
    XHTML 1.1.  If cache is true, images that have been fetched on
    previous runs will be reused.
    """
    book = Book(bookid, server, bookid)
    book.load_toc()

    zfn = book.filepath('%s%s.zip' % (bookid, clean and '-clean' or ''))
    bz = BookiZip(zfn)
    bz.info = book.get_twiki_metadata()

    all_images = set()
    for chapter in bz.info['spine']:
        url = config.CHAPTER_URL % (server, bookid, chapter)
        c = EpubChapter(server, bookid, chapter, url,
                        use_cache=use_cache)
        c.fetch()
        images = c.localise_links()
        all_images.update(images)
        if clean:
            c.remove_bad_tags()
            bz.add_to_package(chapter, chapter + '.xhtml', c.as_xhtml())
        else:
            bz.add_to_package(chapter, chapter + '.html', c.as_html())

    # Add images afterwards, to sift out duplicates
    for image in all_images:
        imgdata = c.image_cache.read_local_url(image)
        bz.add_to_package(image, image, imgdata)

    bz.finish()
    return bz.filename


# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).
ARG_VALIDATORS = {
    "book": re.compile(r'^(\w+/?)*\w+$').match, # can be: BlahBlah/Blah_Blah
    "server": config.SERVER_DEFAULTS.__contains__,
    "use-cache": None,
    "clean": None,
}

def shift_file(fn, dir):
    """Shift a file and save backup (only works on same filesystem)"""
    base = os.path.basename(fn)
    dest = os.path.join(dir, base)
    if os.path.exists(dest):
        os.rename(dest, dest + '~')
    os.rename(fn, dest)
    return dest

if __name__ == '__main__':

    args = parse_args(ARG_VALIDATORS)
    clean = bool(args.get('clean', False))
    use_cache = bool(args.get('use-cache', False))
    if 'server' in args and 'book' in args:
        zfn = make_booki_package(args['server'], args['book'], clean, use_cache)
        fn = shift_file(zfn, DEST_DIR)
        ziplink = '<p><a href="%s">%s zip file.</a></p>' % (fn, args['book'])
    else:
        ziplink = ''

    print "Content-type: text/html; charset=utf-8\n"
    f = open('templates/booki-twiki-gateway.html')
    template = f.read()
    f.close()

    print template % {'ziplink': ziplink,
                      'server-list': optionise(sorted(config.SERVER_DEFAULTS.keys()))}

