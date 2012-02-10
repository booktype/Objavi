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

def add_ncxtext(parent, tag, text):
    """put text in a <text> subelement (as required by navLabel, navInfo)."""
    el = etree.SubElement(parent, tag)
    el2 = etree.SubElement(el, 'text')
    el2.text = text


def make_ncx(toc, filemap, ID, title):
    log(filemap)
    tree = etree.parse(StringIO(BARE_NCX))
    root = tree.getroot()
    head = etree.SubElement(root, 'head')
    add_ncxtext(root, 'docTitle', title)
    navmap = etree.SubElement(root, 'navMap')
    counter, maxdepth = 0, 0
    for subtoc in toc:
        counter, maxdepth = write_navtree(navmap, subtoc, counter, 1, maxdepth, filemap)

    for name, content in (('dtb:uid', ID),
                          ('dtb:depth', str(maxdepth)),
                          ('dtb:totalPageCount', '0'),
                          ('dtb:maxPageNumber', '0')
                          ):
        etree.SubElement(head, 'meta', name=name, content=content)
    return etree.tostring(tree, pretty_print=True, encoding='utf-8')


def write_navtree(parent, subtoc, counter, depth, maxdepth, filemap):
    #subtoc has this structure:
    #{
    #  "title":    division title (optional),
    #  "url":      filename and possible fragment ID,
    #  "type":     string indicating division type (optional),
    #  "role":     epub guide type (optional),
    #  "children": list of TOC structures (optional)
    #}
    counter += 1
    if depth > maxdepth:
        maxdepth = depth

    title = subtoc.get('title', '')
    url = subtoc['url']
    children = subtoc.get('children', [])

    if url is None and children:
        # if the section has no url, it begins with its first child
        url = children[0]['url']

    if filemap:
        url = filemap.get(url, url)

    navpoint = make_navpoint(parent, counter, title, url)
    for point in children:
        counter, maxdepth = write_navtree(navpoint, point, counter, depth + 1, maxdepth, filemap)

    return counter, maxdepth

def make_navpoint(parent, n, title, url):
    """Make the actual navpoint node"""
    log((parent, n, title, url))
    if url is None:
        url = ''
    navpoint = etree.SubElement(parent, 'navPoint',
                                id=(NAVPOINT_ID_TEMPLATE % (n - 1)),
                                playOrder=str(n))
    add_ncxtext(navpoint, 'navLabel', title)
    etree.SubElement(navpoint, 'content', src=url)
    return navpoint



class Epub(object):
    ncx_id = 'ncx'
    ncx_path = 'toc.ncx'
    def __init__(self, filename):
        self.now = time.gmtime()[:6] #(Y, m, d, H, M, S)
        self.zipfile = ZipFile(filename, 'w', ZIP_DEFLATED, allowZip64=True)
        self.write_blob('mimetype', MEDIATYPES['booki'], ZIP_STORED)
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
        filename = filename.encode('utf-8')
        self.write_blob(filename, content)
        self.manifest[ID] = {'media-type': mediatype.encode('utf-8'),
                           'id': ID.encode('utf-8'),
                           'href': filename,
                           }
        if properties:
            self.manifest[ID]['properties'] = properties.encode('utf-8')

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
                             nsmap={'dc' : DC}
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


