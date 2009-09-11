#!/usr/bin/python

"""tests for epub.py"""

import os, sys
import tempfile
from pprint import pprint
import epub

TEST_FILE_DIR = 'tests/epub-examples/'
TEST_FILES =  sorted( TEST_FILE_DIR + x for x in os.listdir(TEST_FILE_DIR) )
#print '\n'.join(TEST_FILES)

# Best_of_TOC.epub
# Bonaparte.epub
# Cowan-Kimberly.epub
# GalCuri.epub
# Hume_Nature.epub
# LittleBrother.epub
# Treasure_Island.epub
# beaglehole-letter-61.epub
# cowan-to-fildes.epub
# ctaquarterly13197477chic.epub
# cyclopedia-wellington.epub
# darwin-autobiography-of-charles-darwin.epub
# early-life-notes.epub
# halfhoursinfarno00newy.epub
# littleroadstoryo00hick.epub
# official-history-nz.epub
# songssourdough00servuoft.epub
# stevenson-black-arrow.epub
# stevenson-calibre-pathological.epub
# takitimu.epub
# war-economy-recipes.epub
# wells-calibre-pathological.epub
# wells-war-of-the-worlds.epub

def _test_file(x):
    if isinstance(x, int):
        return TEST_FILES[x]
    elif isinstance(x, str):
        for fn in TEST_FILES:
            if x in fn.rsplit('/', 1)[1]:
                return fn


#TEMPDIR = tempfile.mkdtemp(prefix='epub-')

def _load_epub(filename, verbose=False):
    fn = _test_file(filename)
    if fn is None:
        raise ValueError("'%s' doesn't refer to a known file")
    if verbose:
        print fn
    e = epub.Epub()
    e.load(open(fn).read())
    return e

def test_load():
    fn = _test_file('Treasure_Island')
    #print fn
    e = epub.Epub()
    e.load(open(fn).read())
    assert e.names
    assert e.info


def test_meta():
    for book, root in [('Hume', 'OPS/content.opf'),
                       ('Treasure', 'OEBPS/volume.opf'),
                       ('arrow', "OPS/epb.opf"),
                       ('LittleBrother', "metadata.opf"),
                       ]:
        e = _load_epub(book)
        e.parse_meta()
        assert e.opf_file == root


def test_opf():
    for book in ['ctaquarterly', 'letter-61',
                 'early-life', 'LittleBrother'
                 ]:
        e = _load_epub(book, verbose=True)
        e.parse_meta()
        metadata = e.parse_opf()
        pprint(metadata)



def test_parse_metadata():
    print "TESTING metadata"
    import lxml
    f = open('tests/metadata.xml')
    tree = lxml.etree.parse(f)
    f.close()
    #nsmap = {'opf': 'http://www.idpf.org/2007/opf'}
    #metadata = root.xpath('.//opf:metadata', namespaces=nsmap)[0]

    for metadata in tree.iter('{http://www.idpf.org/2007/opf}metadata'):
        pprint(epub.parse_metadata(metadata))



#test_load()








DC_METATAGS = ['abstract', 'accessRights', 'accrualMethod', 'accrualPeriodicity',
               'accrualPolicy', 'alternative', 'audience', 'available', 'bibliographicCitation',
               'conformsTo', 'contributor', 'coverage', 'created', 'creator', 'date',
               'dateAccepted', 'dateCopyrighted', 'dateSubmitted', 'description',
               'educationLevel', 'extent', 'format', 'hasFormat', 'hasPart',
               'hasVersion', 'identifier', 'instructionalMethod', 'isFormatOf',
               'isPartOf', 'isReferencedBy', 'isReplacedBy', 'isRequiredBy',
               'issued', 'isVersionOf', 'language', 'license', 'mediator',
               'medium', 'modified', 'provenance', 'publisher', 'references',
               'relation', 'replaces', 'requires', 'rights', 'rightsHolder',
               'source', 'spatial', 'subject', 'tableOfContents', 'temporal',
               'title', 'type', 'valid'
               ]
