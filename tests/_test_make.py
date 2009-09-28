#!/usr/bin/python

import os, sys

sys.path.extend(('.', '..'))

import tempfile
from pprint import pprint, pformat
import epub

from lxml.etree import Element
import lxml

try:
    import json
except ImportError:
    import simplejson as json

def test_ncx():
    try:
        f = open('tests/firefox-info.json')
    except:
        f = open('firefox-info.json')
    info = json.load(f)
    f.close()

    metadata = info['metadata']
    manifest = info['manifest']
    toc = info['TOC']

    #to switch from id to filename,
    filemap = dict((k, v[0]) for k, v in manifest.iteritems())

    pprint(toc)
    ncx = epub.make_ncx(toc, metadata, filemap)
    #pprint(ncx)
    print ncx






if __name__ == '__main__':
    test_ncx()

