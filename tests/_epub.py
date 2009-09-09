#!/usr/bin/python

"""tests for epub.py"""

import os, sys
import tempfile

import epub

TEST_FILE_DIR = '/home/douglas/fm-data/epub-examples/'
TEST_FILES =  sorted( TEST_FILE_DIR + x for x in os.listdir(TEST_FILE_DIR) )

def _test_file(x):
    if isinstance(x, int):
        return TEST_FILES[x]
    elif isinstance(x, str):
        for fn in TEST_FILES:
            if x in fn.rsplit('/', 1)[1]:
                return fn


#TEMPDIR = tempfile.mkdtemp(prefix='epub-')

def _load_epub(filename='Hume'):
    fn = _test_file(filename)
    print fn
    e = epub.Epub()
    e.load(open(fn).read())
    return e



def test_load():
    fn = _test_file('Treasure_Island')
    print fn
    e = epub.Epub()
    e.load(open(fn).read())
    assert e.names
    assert e.info


def test_meta():
    for book, root in [('Hume', 'OPS/content.opf'),
                       ('Treasure', 'OEBPS/volume.opf'),
                       ('arrow', "OPS/epb.opf")
                       ]:
        e = _load_epub(book)
        e.parse_meta()
        assert e.oepbs_root == root
    






#test_load()
    

