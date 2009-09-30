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

from _epub import _get_elements, TEST_FILES, _load_epub

OK_TAGS = [
    "body", "head", "html", "title", "abbr", "acronym", "address",
    "blockquote", "br", "cite", "code", "dfn", "div", "em", "h1", "h2",
    "h3", "h4", "h5", "h6", "kbd", "p", "pre", "q", "samp", "span",
    "strong", "var", "a", "dl", "dt", "dd", "ol", "ul", "li", "object",
    "param", "b", "big", "hr", "i", "small", "sub", "sup", "tt", "del",
    "ins", "bdo", "caption", "col", "colgroup", "table", "tbody", "td",
    "tfoot", "th", "thead", "tr", "img", "area", "map", "meta", "style",
    "link", "base"
    ]


def _xhtml_parse(*args, **kwargs):
    kwargs['parser'] = lxml.html.XHTMLParser(encoding="utf-8")
    
    return lxml.html.parse(*args, **kwargs)

def _html_parse(*args, **kwargs):
    kwargs['parser'] = lxml.etree.HTMLParser(encoding="utf-8")
    return lxml.html.parse(*args, **kwargs)


def test_tags(parse=_html_parse):
    #XXX not testing that the tags are correctly used or nested!
    good_tags = dict((x, 0) for x in OK_TAGS)
    bad_tags = {}
    for book in TEST_FILES:
        print book
        e = _load_epub(book, verbose=True)
        e.parse_meta()
        e.parse_opf()
        #e.parse_ncx()
        for ID in e.order:
            try:
                tree = e.gettree(id=ID, parse=parse)
            except Exception, exc:
                print ID, exc
            for x in tree.getiterator(Element):
                t = x.tag
                #print t
                #if not t.startswith(epub.XHTMLNS):
                #    t = '{No namespace}' + t
                #    bad_tags[t] = bad_tags.get(t, 0) + 1
                #    continue
                t = t.replace(epub.XHTMLNS, '')
                if t in good_tags:
                    good_tags[t] += 1
                else:
                    bad_tags[t] = bad_tags.get(t, 0) + 1

    print "GOOD TAGS"

    for n, t in sorted((v, k) for k, v in good_tags.iteritems()):
        print "%20s:%s" % (t, n)
    print "BAD TAGS"
    for t, n in bad_tags.iteritems():
        print "%20s:%s" % (t, n)




def add_guts(src, dest):
    """Append the contents of the <body> of one tree onto that of
    another.  The source tree will be emptied."""
    #print  lxml.etree.tostring(src)
    try:
        sbody = src.iter(epub.XHTMLNS + 'body').next()
    except StopIteration:
        sbody = src.iter('body').next()
    try:
        dbody = dest.iter(epub.XHTMLNS + 'body').next()
    except StopIteration:
        dbody = dest.iter('body').next()
    try:
        dbody.tail += sbody.text
    except TypeError:
        pass
    for x in sbody:
        dbody.append(x)
    try:
        dbody.tail += sbody.tail
    except TypeError:
        pass


def add_marker(doc, ID, title=None, klass="espri-marker"):
    marker = lxml.etree.Element('hr')
    marker.set('id', ID)
    marker.set('class', klass)
    if title is not None:
        marker.set('title', title)
    try:
        dbody = doc.iter(epub.XHTMLNS + 'body').next()
    except StopIteration:
        dbody = doc.iter('body').next()
    dbody.append(marker)

def concat_books():
    for book in TEST_FILES:
        print book
        e = _load_epub(book, verbose=True)
        e.parse_meta()
        e.parse_opf()
        e.parse_ncx()
        lang = e.find_language() or 'UND'
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

        f = open('tests/xhtml/' + os.path.basename(book) + '.html', 'w')
        print >> f, lxml.etree.tostring(doc, encoding='utf-8', method='html').replace('&#13;', '')#.encode('utf-8')
        f.close()

if __name__ == '__main__':
    #test_tags()
    concat_books()
