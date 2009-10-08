#!/usr/bin/python

"""tests for epub.py"""

import os, sys

sys.path.extend(('.', '..'))
#print sys.path

import tempfile
from pprint import pprint, pformat
import epub

from lxml.etree import Element
import lxml


def _xhtml_parse(*args, **kwargs):
    kwargs['parser'] = lxml.html.XHTMLParser(encoding="utf-8")    
    return lxml.html.parse(*args, **kwargs)

def _html_parse(*args, **kwargs):
    kwargs['parser'] = lxml.etree.HTMLParser(encoding="utf-8")
    return lxml.html.parse(*args, **kwargs)

def _find_tag(doc, tag):
    try:
        return doc.iter(epub.XHTMLNS + tag).next()
    except StopIteration:
        return doc.iter(tag).next()

def add_guts(src, dest):
    """Append the contents of the <body> of one tree onto that of
    another.  The source tree will be emptied."""
    #print  lxml.etree.tostring(src)
    sbody = _find_tag(src, 'body')
    dbody = _find_tag(dest, 'body')

    dbody[-1].tail = ((dbody[-1].tail or '') +
                      (sbody.text or '')) or None
    
    for x in sbody:
        dbody.append(x)

    dbody.tail = ((dbody.tail or '') +
                  (sbody.tail or '')) or None

def add_marker(doc, ID, title=None, klass="espri-marker"):
    marker = lxml.etree.Element('hr')
    marker.set('id', ID)
    marker.set('class', klass)
    if title is not None:
        marker.set('title', title)
    dbody = _find_tag(doc, 'body')
    dbody.append(marker)

def concat_chapters(fn):
    e = epub.Epub()
    e.load(open(fn).read())

    e.parse_meta()
    e.parse_opf()
    e.parse_ncx()
    
    lang = e.find_language() or 'UND'
    chapter_depth, toc_points = e.find_probable_chapters()

    doc = epub.new_doc(lang=lang)
    for ID in e.order:
        fn, mimetype = e.manifest[ID]
        print fn
        if mimetype.startswith('image'):
            tree = epub.new_doc(guts='<img src="%s" alt="" />' % fn)
        else:
            tree = e.gettree(fn, parse=_html_parse)

        add_marker(doc, 'espri-new-page-%s' % ID, fn)
        add_guts(tree, doc)

    return doc

if __name__ == '__main__':
    concat_chapters(sys.argv[1])
