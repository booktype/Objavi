#!/usr/bin/python
#
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
import re, time
from urllib2 import urlopen
from getopt import gnu_getopt

from objavi.cgi_utils import parse_args, optionise
from fmbook import log, Book
import config

from booki import xhtml_utils

from pprint import pformat

# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).
ARG_VALIDATORS = {
    "book": re.compile(r'^(\w+/?)*\w+$').match, # can be: BlahBlah/Blah_Blah
    "server": config.SERVER_DEFAULTS.__contains__,
}


def make_booki_package(server, bookid):
    book = Book(bookid, server, bookid)
    book.load_toc()
    info = book.get_twiki_metadata()

    log(pformat(info))
    manifest = {}
    package_dir = book.filepath('epub')
    os.mkdir(package_dir)
    def add_to_package(fn, blob):
        log("saving %s bytes to %s" % (len(blob), fn))
        f = open(os.path.join(package_dir, fn), 'w')
        f.write(blob)
        f.close()

    for chapter in info['spine']:
        c = xhtml_utils.EpubChapter(server, bookid, chapter, cache_dir=package_dir)
        c.fetch()
        c.load_tree()
        images = c.localise_links()

        for image in images:
            imgdata = c.image_cache.read_local_url(image)
            add_to_package(image, imgdata)

        c.remove_bad_tags()
        add_to_package(chapter, c.as_xhtml())



def get_server_list():
    return sorted(config.SERVER_DEFAULTS.keys())


if __name__ == '__main__':
    args = parse_args(ARG_VALIDATORS)
    clean = bool(args.get('clean', False))
    if 'server' in args and 'book' in args:
        zfn = make_booki_package(args['server'], args['book'], clean)
        ziplink = '<a href="%s">%s zip file</a>' %(zfn, args['book'])
    else:
        ziplink = ''

    f = open('templates/booki-twiki-gateway.html')
    template = f.read()
    f.close()
    print "Content-type: text/html; charset=utf-8\n"
    print template % {'ziplink': ziplink,
                      'server-list': optionise(get_server_list())}



