# This file is part of Objavi.
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
import time
import tempfile
from urllib import unquote
from urllib2 import urlopen
from urlparse import urlsplit
from subprocess import check_call, CalledProcessError

from objavi import epub
from objavi.book_utils import log
from objavi.cgi_utils import super_bleach, path2url
from objavi import config


IA_EPUB_URL = "http://www.archive.org/download/%s/%s.epub"


class TimeoutError(Exception):
    pass


def espri(epuburl, bookid, src_id=None):
    """Make a bookizip from the epub at <epuburl> and save it as
    <bookid>.zip."""
    log("starting espri", epuburl, bookid)
    f = urlopen(epuburl)
    s = f.read()
    f.close()
    e = epub.Epub()
    e.load(s)
    if src_id is not None:
        #so that booki knows where the book came from, so e.g. archive.org can find it again
        e.register_source_id(src_id)
    e.parse_meta()
    e.parse_opf()
    e.parse_ncx()
    zipfile = '%s/%s.zip' % (config.BOOKI_BOOK_DIR, bookid)
    e.make_bookizip(zipfile)


def ia_espri(bookid):
    """Import an Internet Archive epub given an archive id"""
    epuburl = IA_EPUB_URL % (bookid, bookid)
    log(epuburl)
    espri(epuburl, bookid, src_id='archive.org')
    return '%s.zip' % bookid


def inet_espri(epuburl):
    """Import an epub from an arbitrary url"""
    tainted_name = unquote(os.path.basename(urlsplit(epuburl).path))
    filename = super_bleach(tainted_name)
    if filename.lower().endswith('-epub'):
        filename = filename[:-5]
    bookid = '%s-%s' % (filename, time.strftime('%F_%T'))
    espri(epuburl, bookid, src_id='URI')
    return '%s.zip' % bookid


def wikibooks_espri(wiki_url):
    """Wikibooks import using the wikibooks2epub script by Jan Gerber
    to first convert the wikibook to an epub, which can then be turned
    into a bookizip via the espri function.
    """
    os.environ['oxCACHE'] = os.path.abspath(config.WIKIBOOKS_CACHE)
    os.environ['LANG'] = 'en_NZ.UTF-8'
    tainted_name = unquote(os.path.basename(urlsplit(wiki_url).path))
    bookid = "%s-%s" % (super_bleach(tainted_name),
                        time.strftime('%Y.%m.%d-%H.%M.%S'))
    workdir = tempfile.mkdtemp(prefix=bookid, dir=os.path.join(config.DATA_ROOT, "tmp"))
    os.chmod(workdir, 0755)
    epub_file = os.path.join(workdir, bookid + '.epub')
    epub_url = path2url(epub_file)

    #the wikibooks importer is a separate process, so run that, then collect the epub.
    cmd = [config.TIMEOUT_CMD, config.WIKIBOOKS_TIMEOUT,
           config.WIKIBOOKS_CMD,
           '-i', wiki_url,
           '-o', epub_file
           ]
    log(cmd)
    log(os.environ)
    log(os.getcwd())

    try:
        check_call(cmd)
    except CalledProcessError, e:
        if e.returncode == 137:
            raise TimeoutError('Wikibooks took too long (over %s seconds)' % WIKIBOOKS_TIMEOUT)
        raise

    espri(epub_url, bookid, src_id='wikibooks')
    return '%s.zip' % bookid
