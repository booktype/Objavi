#!/usr/bin/python

import os, sys, time

#sys.path.extend(('.', '..'))
#print sys.path

import tempfile, zlib

from pprint import pprint, pformat

from lxml import etree
import lxml, lxml.html

from objavi import config
from objavi.cgi_utils import log

HERE = os.path.dirname(sys.argv[0])
HTML_FILE = os.path.join(HERE, 'long_html.html')
DEST = '/tmp/'
MARKER_CLASS = 'objavi-splitter'

def get_compressed_size(s):
    return len(zlib.compress(s))

config.EPUB_FILE_SIZE_MAX = 100000

def split_file(fn, splitter, name):
    f = open(fn)
    html = f.read()
    f.close()
    compressed_size = get_compressed_size(html)
    splits = max(compressed_size // config.EPUB_COMPRESSED_SIZE_MAX,
                 len(html) // config.EPUB_FILE_SIZE_MAX)

    log("uncompressed: %s, compressed: %s, splits: %s" % (len(html), compressed_size, splits))

    if splits:
        target = len(html) // (splits + 1)
        s = 0
        fragments = []
        for i in range(splits):
            e = html.find('<', target * (i + 1))
            fragments.append(html[s:e])
            fragments.append('<hr class="%s" id="split_%s" />' % (MARKER_CLASS, i))
            s = e
        fragments.append(html[s:])
        log([len(x) for x in fragments])
        tree = lxml.html.fromstring(''.join(fragments))

        html2 = etree.tostring(tree, encoding='UTF-8', method='html')
        f = open('/tmp/marked.html', 'w')
        f.write(html2)
        f.close()

        t = time.time()
        chapters = splitter(tree)
        print "%s took %s" % (splitter, time.time() - t)

        log(chapters)
        for i, c in enumerate(chapters):
            f = open('/tmp/%s_%s.html' % (name, i + 1,), 'w')
            f.write(etree.tostring(c, encoding='UTF-8', method='html'))
            f.close()



def copy_element(src, create):
    """Return a copy of the src element, with all its attributes and
    tail, using create to make the copy. create is probably an
    Element._makeelement method, to associate the copy with the right
    tree, but it could be etree.HTMLElement."""
    if isinstance(src.tag, basestring):
        dest = create(src.tag)
    else:
        dest = copy.copy(src)

    for k, v in src.items():
        dest.set(k, v)
    dest.tail = src.tail
    return dest

def split_document(doc):
    """Split the document along chapter boundaries."""
    try:
        root = doc.getroot()
    except AttributeError:
        root = doc

    front_matter = copy_element(root, lxml.html.Element)
    chapters = [front_matter]

    _climb_and_split(root, front_matter, chapters)
    return chapters

def _climb_and_split(src, dest, chapters):
    for child in src.iterchildren():
        if child.tag == 'hr' and child.get('class') == MARKER_CLASS:
            log('got a marker')
            new = copy_element(src, lxml.html.Element)

            #build a new tree to this point
            root = new
            for a in src.iterancestors():
                a2 = copy_element(a, root.makeelement)
                a2.append(root)
                root = a2
            chapters.append(root)

            #trim the tail of the finished one.
            dest.tail = None
            for a in dest.iterancestors():
                a.tail = None

            #now the new tree is the destination
            dest = new

        else:
            new = copy_element(child, dest.makeelement)
            new.text = child.text
            dest.append(new)
            new2 = _climb_and_split(child, new, chapters)
            if new2 != new:
                dest = new2.getparent()
    return dest

def split_document_2(doc):
    try:
        root = doc.getroot()
    except AttributeError:
        root = doc

    stacks = []
    for hr in doc.iter(tag='hr'):
        if hr.get('class') == MARKER_CLASS:
            stack = [hr]
            stack.extend(x for x in hr.iterancestors())
            stack.reverse()
            stacks.append(stack)

    iterstacks = iter(stacks)


    src = root
    dest = lxml.html.Element(root.tag, **root.attrib)
    doc = dest
    stack = iterstacks.next()
    marker = stack[-1]


    chapters = []
    try:
        while True:
            for e in src:
                if e not in stack:
                    dest.append(e)
                elif e is marker:
                    # got one
                    src.remove(e)
                    chapters.append(doc)
                    src = root
                    dest = lxml.html.Element(root.tag, **src.attrib)

                    doc = dest
                    stack = iterstacks.next()
                    marker = stack[-1]
                    break
                else:
                    #go in a level
                    dest = etree.SubElement(dest, e.tag, **e.attrib)
                    dest.text = e.text
                    e.text = None
                    src = e
                    break
    except StopIteration:
        #stacks have run out -- the rest of the tree is the last section
        chapters.append(src)

    return chapters



log = lambda x: None
for splitter in (split_document, split_document_2,
                 split_document, split_document_2,
    ):
    split_file(HTML_FILE, splitter, 'stack')



