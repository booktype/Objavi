"""Module for dealing with booki -> epub conversions."""

import os, sys
import time
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, ZIP_STORED

from cStringIO import StringIO

import lxml.html, lxml.cssselect
from lxml import etree

from objavi.book_utils import log
from objavi.config import NAVPOINT_ID_TEMPLATE
from objavi.constants import OPF, DC, DCNS

from booki.bookizip import get_metadata, MEDIATYPES

CONTAINER_PATH = 'META-INF/container.xml'

CONTAINER_XML = '''<?xml version='1.0' encoding='utf-8'?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile media-type="application/oebps-package+xml" full-path="content.opf"/>
  </rootfiles>
</container>
'''

##Construct NCX
BARE_NCX = ('<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" '
            '"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd"> '
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" />')


class NcxState:
    def __init__(self, filemap):
        self.filemap   = filemap
        self.counter   = 0
        self.maxdepth  = 0
        self.next_id   = 0

    def make_src(self, url):
        if self.filemap:
            return self.filemap.get(url, url)
        else:
            return url


def make_ncx(toc, filemap, ID, title):
    """Creates the EPUB NCX file."""

    tree = etree.parse(StringIO(BARE_NCX))
    root = tree.getroot()
    head = etree.SubElement(root, 'head')
    add_ncxtext(root, 'docTitle', title)
    navmap = etree.SubElement(root, 'navMap')

    state = NcxState(filemap)
    for subtoc in toc:
        write_navtree(navmap, subtoc, state, depth = 1)

    for name, content in (('dtb:uid', ID),
                          ('dtb:depth', str(state.maxdepth)),
                          ('dtb:totalPageCount', '0'),
                          ('dtb:maxPageNumber', '0')
                          ):
        etree.SubElement(head, 'meta', name=name, content=content)

    return etree.tostring(tree, pretty_print=True, encoding='utf-8')


def write_navtree(parent, subtoc, state, depth):
    #subtoc has this structure:
    #{
    #  "title":    division title (optional),
    #  "url":      filename and possible fragment ID,
    #  "type":     string indicating division type (optional),
    #  "role":     epub guide type (optional),
    #  "children": list of TOC structures (optional)
    #}
    url      = subtoc.get('url')
    title    = subtoc.get('title', '')
    children = subtoc.get('children', [])

    if subtoc.get('type') == 'booki-section' and len(children) == 0:
        # skip empty sections
        return

    if children:
        first_child_url = children[0].get('url')
    else:
        first_child_url = None

    if url is None:
        # if the section has no url, it begins with its first child
        url = first_child_url

    state.counter += 1
    if depth > state.maxdepth:
        state.maxdepth = depth

    # create the navPoint for this node
    navpoint = make_navpoint(parent, state, title, url)

    if url == first_child_url:
        # first child should start with the same navPoint
        state.counter -= 1

    # create navPoints for all children
    #
    for point in children:
        write_navtree(navpoint, point, state, depth + 1)


def make_navpoint(parent, state, title, url):
    """Make the actual navpoint node"""

    if url is None:
        url = ''

    navpoint_id = NAVPOINT_ID_TEMPLATE % (state.next_id, )
    content_src = state.make_src(url)
    play_order  = str(state.counter)

    state.next_id += 1

    navpoint = etree.SubElement(parent, 'navPoint', id = navpoint_id, playOrder = play_order)
    add_ncxtext(navpoint, 'navLabel', title)
    etree.SubElement(navpoint, 'content', src = content_src)

    return navpoint


def add_ncxtext(parent, tag, text):
    """put text in a <text> subelement (as required by navLabel, navInfo)."""
    el = etree.SubElement(parent, tag)
    el2 = etree.SubElement(el, 'text')
    el2.text = text



class Epub(object):
    ncx_id = 'ncx'
    ncx_path = 'toc.ncx'
    def __init__(self, filename):
        self.now = time.gmtime()[:6] #(Y, m, d, H, M, S)
        self.zipfile = ZipFile(filename, 'w', ZIP_DEFLATED, allowZip64=True)
        self.write_blob('mimetype', MEDIATYPES['epub'], ZIP_STORED)
        self.write_blob(CONTAINER_PATH, CONTAINER_XML)
        self.manifest = {}
        self.spine = []
        self.guide = []

    def write_blob(self, path, blob, compression=ZIP_DEFLATED, mode=0644):
        """Add something to the zip without adding to manifest"""
        zinfo = ZipInfo(path)
        zinfo.external_attr = mode << 16L # set permissions
        zinfo.compress_type = compression
        zinfo.date_time = self.now
        self.zipfile.writestr(zinfo, blob)

    def add_file(self, ID, filename, mediatype, content, properties=None):
        self.write_blob(filename, content)

        self.manifest[ID] = {
            'id': ID,
            'href': unicode(filename, 'utf-8'),
            'media-type': mediatype,
            }

        if properties:
            self.manifest[ID]['properties'] = properties

    def add_ncx(self, toc, filemap, ID, title):
        ncx = make_ncx(toc, filemap, ID, title)
        self.add_file(self.ncx_id, self.ncx_path, MEDIATYPES['ncx'], ncx)

    def add_spine_item(self, ID, linear=None):
        info = {'idref': ID}
        if linear is not None:
            info['linear'] = linear
        self.spine.append(info)

    def add_guide_item(self, type, title, href):
        info = dict(type=type, title=title, href=href)
        self.guide.append(info)

    def write_opf(self, meta_info, primary_id=None):
        if primary_id is None:
            for k, v, a in meta_info:
                if k == DCNS + 'identifier':
                    primary_id = a.setdefault('id', 'primary_id')
                    break

        root = etree.Element('package',
                             {'xmlns' : OPF,
                              'unique-identifier' : primary_id,
                              'version' : '2.0'},
                             nsmap = {'dc' : DC, 'opf' : OPF}
                             )

        metadata = etree.SubElement(root, 'metadata')
        for key, text, attrs in meta_info:
            el = etree.SubElement(metadata, key, attrs)
            el.text = text

        manifest = etree.SubElement(root, 'manifest')
        for ID, v in self.manifest.iteritems():
            v['id'] = ID
            etree.SubElement(manifest, 'item', v)

        spine = etree.SubElement(root, 'spine', {'toc': self.ncx_id})
        for item in self.spine:
            etree.SubElement(spine, 'itemref', item)

        guide = etree.SubElement(root, 'guide', {})
        for item in self.guide:
            etree.SubElement(guide, 'reference', item)

        tree_str = etree.tostring(root, pretty_print=True, encoding='utf-8')
        self.write_blob('content.opf', tree_str)

    def finish(self):
        self.zipfile.close()


