"""Module for dealing with booki -> epub conversions."""

import os, sys
from pprint import pprint
#import zipfile
from cStringIO import StringIO

import lxml, lxml.html, lxml.cssselect
from lxml import etree

from objavi.cgi_utils import log
from objavi.config import DC, XHTML, XHTMLNS, NAVPOINT_ID_TEMPLATE

from booki.bookizip import get_metadata, get_metadata_schemes

##Construct NCX
BARE_NCX = ('<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" '
            '"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd"> '
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" />')

def add_ncxtext(parent, tag, text):
    """put text in a <text> subelement (as required by navLabel, navInfo)."""
    el = etree.SubElement(parent, tag)
    el2 = etree.SubElement(el, 'text')
    el2.text = text


def make_ncx(toc, metadata, filemap):
    log(filemap)
    tree = etree.parse(StringIO(BARE_NCX))
    root = tree.getroot()
    head = etree.SubElement(root, 'head')
    add_ncxtext(root, 'docTitle', get_metadata(metadata, 'title')[0])
    navmap = etree.SubElement(root, 'navMap')
    counter, maxdepth = 0, 0
    for subtoc in toc:
        counter, maxdepth = write_navtree(navmap, subtoc, counter, 1, maxdepth, filemap)

    for name, content in (('dtb:uid', get_metadata(metadata, 'identifier', default=[''])[0]),
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
    log((parent, n, title, url))
    """Make the actual navpoint node"""
    navpoint = etree.SubElement(parent, 'navPoint',
                                id=(NAVPOINT_ID_TEMPLATE % (n - 1)),
                                playOrder=str(n))
    add_ncxtext(navpoint, 'navLabel', title)
    etree.SubElement(navpoint, 'content', src=url)
    return navpoint

