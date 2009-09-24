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
import cgi
import re, time
from urllib2 import urlopen
from getopt import gnu_getopt
from pprint import pformat

from objavi.fmbook import log, Book
from objavi.cgi_utils import parse_args, optionise
from objavi import config

from booki import xhtml_utils
from booki.xhtml_utils import MEDIATYPES

import zipfile

try:
    import simplejson as json
except ImportError:
    import json


def open_booki_zip(filename):
    """Start a new zip and put an uncompressed 'mimetype' file at the
    start.  This idea is copied from the epub specification, and
    allows the file type to be dscovered by reading the first few
    bytes."""
    z = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
    mimetype = zipfile.ZipInfo('mimetype') # defaults to uncompressed
    z.writestr(mimetype, MEDIATYPES['booki'])
    return z

def make_booki_package(server, bookid, clean=False):
    """Extract all chapters from the specified book, as well as
    associated images and metadata, and zip it all up for conversion
    to epub.

    If clean is True, the chapters will be cleaned up and converted to
    XHTML 1.1.
    """
    book = Book(bookid, server, bookid)
    book.load_toc()
    info = book.get_twiki_metadata()

    manifest = {}

    zfn = book.filepath('%s.zip' % bookid)
    zf = open_booki_zip(zfn)

    imagedir = book.filepath('images')
    os.mkdir(imagedir)

    def add_to_package(ID, fn, blob, mediatype=None):
        #log("saving %s bytes to %s, identified as %s" % (len(blob), fn, ID))
        zf.writestr(fn, blob)
        if mediatype is None:
            ext = fn[fn.rfind('.') + 1:]
            mediatype = MEDIATYPES.get(ext, MEDIATYPES[None])
        manifest[ID] = (fn, mediatype)

    for chapter in info['spine']:
        c = xhtml_utils.EpubChapter(server, bookid, chapter, cache_dir=imagedir)
        c.fetch()
        images = c.localise_links()
        for image in images:
            imgdata = c.image_cache.read_local_url(image)
            add_to_package(image, image, imgdata)

        if clean:
            c.remove_bad_tags()
            add_to_package(chapter, chapter + '.xhtml', c.as_xhtml())
        else:
            add_to_package(chapter, chapter + '.html', c.as_html())

    info['manifest'] = manifest
    log(pformat(info))
    infojson = json.dumps(info, indent=2)
    add_to_package('info.json', 'info.json', infojson, 'application/json')
    zf.close()
    return zfn


# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).
ARG_VALIDATORS = {
    "book": re.compile(r'^(\w+/?)*\w+$').match, # can be: BlahBlah/Blah_Blah
    "server": config.SERVER_DEFAULTS.__contains__,
    "clean": None,
}

if __name__ == '__main__':
    args = parse_args(ARG_VALIDATORS)
    clean = bool(args.get('clean', False))
    if 'server' in args and 'book' in args:
        zfn = make_booki_package(args['server'], args['book'], clean)
        here = os.path.abspath('.')
        assert zfn.startswith(here)
        ziplink = '<p><a href="%s">%s zip file.</a></p>' % (zfn[len(here):], args['book'])
    else:
        ziplink = ''

    print "Content-type: text/html; charset=utf-8\n"
    f = open('templates/booki-twiki-gateway.html')
    template = f.read()
    f.close()

    print template % {'ziplink': ziplink,
                      'server-list': optionise(sorted(config.SERVER_DEFAULTS.keys()))}

