"""Module for dealing with epub -> booki conversions."""

import os, sys
from pprint import pprint
#import zipfile
from cStringIO import StringIO

import lxml, lxml.html, lxml.cssselect
from lxml import etree

from objavi.cgi_utils import log

XHTMLNS = '{http://www.w3.org/1999/xhtml}'
XHTML = 'http://www.w3.org/1999/xhtml'

DC = "http://purl.org/dc/elements/1.1/"

##Construct NCX
BARE_NCX = ('<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" '
            '"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd"> '
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" />')

def add_ncxtext(parent, tag, text):
    """put text in a <text> subelement (as required by navLabel, navInfo)."""
    el = etree.SubElement(parent, tag)
    el2 = etree.SubElement(el, 'text')
    el2.text = text

## toc looks like [
##  [
##    [ "Section Heading", null],
##    [ "Introduction", "Introduction"],
##  ],

def make_ncx(toc, metadata, filemap):
    tree = etree.parse(StringIO(BARE_NCX))
    root = tree.getroot()
    head = etree.SubElement(root, 'head')
    add_ncxtext(root, 'docTitle', metadata['title'])
    navmap = etree.SubElement(root, 'navMap')
    counter, maxdepth = 0, 0
    for subtoc in toc:
        counter, maxdepth = write_navtree(navmap, subtoc, counter, 1, maxdepth, filemap)

    for name, content in (('dtb:uid', metadata['identifier']),
                          ('dtb:depth', str(maxdepth)),
                          ('dtb:totalPageCount', '0'),
                          ('dtb:maxPageNumber', '0')
                          ):
        etree.SubElement(head, 'meta', name=name, content=content)
    return etree.tostring(tree, pretty_print=True, encoding='utf-8')


def write_navtree(parent, subtoc, counter, depth, maxdepth, filemap):
    counter += 1
    if depth > maxdepth:
        maxdepth = depth
    title, url = subtoc
    log(title, url)
    if isinstance(title, basestring): #leaf node
        subsections = []
    else:
        subsections = url
        title, url = title
        if url is None:
            # if the section has no url, it begins with its first child
            #XXX though this mucks with playorder, unless a # is used
            try:
                url = subsections[0][1]
            except IndexError:
                log ("section %s has no contents!" % title)
                #what to do? just not add the section?
                return counter, maxdepth
    if filemap:
        url = filemap.get(url, url)
    log(url, filemap)

    navpoint = make_navpoint(parent, counter, title, url)
    for point in subsections:
        counter, maxdepth = write_navtree(navpoint, point, counter, depth + 1, maxdepth, filemap)

    return counter, maxdepth

def make_navpoint(parent, n, title, url):
    """Make the actual navpoint node"""
    navpoint = etree.SubElement(parent, 'navPoint',
                                id=('navpoint%s' % (n - 1)),
                                playOrder=str(n))
    add_ncxtext(navpoint, 'navLabel', title)
    etree.SubElement(navpoint, 'content', src=url)
    return navpoint

