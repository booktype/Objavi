#!/usr/bin/python

"""tests for epub.py"""

import os, sys
import tempfile
from pprint import pprint, pformat
import epub

import lxml

DC = "http://purl.org/dc/elements/1.1/"
TEST_FILE_DIR = 'tests/epub-examples/'
TEST_FILES =  sorted( TEST_FILE_DIR + x for x in os.listdir(TEST_FILE_DIR) if x.endswith('.epub'))
#print '\n'.join(os.path.basename(x) for x in TEST_FILES)

## Best_of_TOC.epub
## Bonaparte.epub
## Conrad - Heart of Darkness.epub
## Cowan-Kimberly.epub
## Doctorow - I, Robot.epub
## Doyle - The Adventures of Sherlock Holmes.epub
## GalCuri.epub
## Grimm - Grimm's Fairy Tales.epub
## Hume_Nature.epub
## Lang - The Arabian Nights.epub
## LittleBrother.epub
## McGSome.epub
## Melville - Moby-Dick.epub
## Stevenson - Treasure Island.epub
## Tolstoy - Ivan the Fool.epub
## Treasure_Island.epub
## Twain - The Adventures of Huckleberry Finn.epub
## Wells - The War of the Worlds.epub
## Wilde - The Importance of Being Earnest.epub
## beaglehole-letter-61.epub
## cowan-to-fildes.epub
## ctaquarterly13197477chic.epub
## cyclopedia-wellington.epub
## darwin-autobiography-of-charles-darwin.epub
## early-life-notes.epub
## halfhoursinfarno00newy.epub
## ia-abroad.epub
## ia-huckfin.epub
## ia-letters-from-cat.epub
## ia-old-french.epub
## ia-tomsawyer.epub
## littleroadstoryo00hick.epub
## pg2292.epub
## pg29904-images.epub
## pg829-images.epub
## pg829.epub
## sample.epub
## songssourdough00servuoft.epub
## stevenson-black-arrow.epub
## swift-a-modest-proposal.epub
## takitimu.epub
## twain-adventures-of-huckleberry-finn.epub
## war-economy-recipes.epub
## wells-calibre-pathological.epub

def _test_file(x):
    if isinstance(x, int):
        return TEST_FILES[x]
    elif x in TEST_FILES:
        return x
    elif isinstance(x, basestring):
        for fn in TEST_FILES:
            if x in fn.rsplit('/', 1)[1]:
                return fn


#TEMPDIR = tempfile.mkdtemp(prefix='epub-')

def _load_epub(filename, verbose=False):
    fn = _test_file(filename)
    if fn is None:
        raise ValueError("'%s' doesn't refer to a known file" % filename)
    if verbose:
        print fn
    e = epub.Epub()
    e.load(open(fn).read())
    return e

def _get_elements(book, elements):
    e = _load_epub(book)
    e.parse_meta()
    tree = e.gettree(e.opf_file)
    ns = '{http://www.idpf.org/2007/opf}'
    return [tree.find(ns + x) for x in elements] + [e]



def test_load():
    fn = _test_file('Treasure_Island')
    #print fn
    e = epub.Epub()
    e.load(open(fn).read())
    assert e.names
    assert e.info


def test_meta():
    for book, root in [('Hume', 'OPS/content.opf'),
                       ('Treasure_Island', 'OEBPS/volume.opf'),
                       ('black-arrow', "OPS/epb.opf"),
                       ('LittleBrother', "metadata.opf"),
                       ]:
        #print book
        e = _load_epub(book)
        e.parse_meta()
        assert e.opf_file == root


def test_opf():
    for book in ['ctaquarterly', 'letter-61',
                 'early-life', 'LittleBrother'
                 ]:
        e = _load_epub(book)
        e.parse_meta()
        e.parse_opf()

        for a, t in [('metadata', dict),
                     ('manifest', dict),
                     ('spine', list),
                     ('ncxfile', basestring),
            ]:
            assert hasattr(e, a)
            assert isinstance(getattr(e, a), t)


def test_metadata_count():
    counts = {}
    for book in TEST_FILES:
        #print book
        e = _load_epub(book)
        e.parse_meta()
        e.parse_opf()
        md = e.metadata
        for ns, values in md.items():
            nsdict = counts.setdefault(ns, {})
            for k, v in values.items():
                name = v[0]
                if name:
                    nsdict[k] = nsdict.get(k, 0) + 1

    pprint(counts)
    #sys.exit()

def test_metadata_conformance():
    #at least one:
    #identifier  title  language
    for book in TEST_FILES:
        #print book
        e = _load_epub(book)
        e.parse_meta()
        e.parse_opf()
        md = e.metadata
        dc = md[DC]
        for x in ('identifier', 'title', 'language'):
            assert dc.get(x)


    #the unique-identifier attribute of the package element is a
    #correct XML IDREF to a Dublin Core identifier element; and

    #any extended values specified for the Dublin Core creator and
    #contributor elements' OPF role attribute must be taken from the
    #registered MARC Relator Code list or must begin with oth.; and


def test_example_ncx():
    import lxml
    f = open('tests/example.ncx')
    tree = lxml.etree.parse(f)
    f.close()
    data = epub.parse_ncx(tree)
    #pprint(data)
    f = open('tests/example.ncx.result')
    answer = eval(f.read())
    f.close()
    assert data == answer

def test_new_doc():
    #XXX not very comprehensive.
    for guts in ('', "hello", "<h1>HELLO!</h1>"):
        doc = epub.new_doc(guts=guts)
        try:
            body = doc.iter(epub.XHTMLNS + 'body').next()
            print "got %s" % body
        except StopIteration:
            body = doc.iter('body').next()
        guts2 = body.text or ''
        for x in body:
            guts2 += lxml.etree.tostring(x)
        if body.tail is not None:
            guts2 += body.tail
        assert guts == guts2


## def test_parse_ncx():
##     for book in TEST_FILES:
##         print book
##         e = _load_epub(book, verbose=True)
##         e.parse_meta()
##         e.parse_opf()
##         e.parse_ncx()
##        #pprint(e.ncxdata)

def test_raw_json():
    for book in TEST_FILES:
        e = _load_epub(book)
        e.parse_meta()
        e.parse_opf()
        e.parse_ncx()
        js = e.raw_json()
        f = open('tests/json/' + os.path.basename(book) + '.js', 'w')
        print >> f, '/* %s */' % book
        print >> f, js
        f.close()

        #print js

def test_find_language():
    for book in TEST_FILES:
        e = _load_epub(book)
        e.parse_meta()
        e.parse_opf()
        e.parse_ncx()
        print e.find_language(), book



def test_parse_metadata():
    #XXX check unicode!

    print "TESTING metadata"
    import lxml
    f = open('tests/metadata.xml')
    tree = lxml.etree.parse(f)
    f.close()
    #nsmap = {'opf': 'http://www.idpf.org/2007/opf'}
    #metadata = root.xpath('.//opf:metadata', namespaces=nsmap)[0]
    results = []
    for metadata in tree.iter('{http://www.idpf.org/2007/opf}metadata'):
        results.append(epub.parse_metadata(metadata))

    f = open('tests/metadata.result')
    correct = eval(f.read())
    f.close()

    if results != correct:
        # how to do semantic diff of dicts?
        from difflib import unified_diff
        print '\n'.join(unified_diff(pformat(results).split('\n'), pformat(correct).split('\n')))
        raise AssertionError('bad metadata parsing')




def test_parse_manifest():
    # manifest should be dict of ids pointing to name, mime-type pairs
    # names should be found in zipfile
    all_mimetypes = {}
    for book in TEST_FILES:
        manifest, e = _get_elements(book, ['manifest'])
        pwd = os.path.dirname(e.opf_file)
        files = epub.parse_manifest(manifest, pwd)
        #print book
        mimetypes = set()
        filenames = e.names

        for name, mimetype in files.values():
            assert isinstance(name, basestring)
            assert isinstance(mimetype, basestring)
            mimetypes.add(mimetype)
            all_mimetypes[mimetype] = all_mimetypes.get(mimetype, 0) + 1
            if  name not in filenames:
                print book, name, filenames
            assert name in filenames

        print "%s: %s files, %s different types" % (book, len(files), len(mimetypes))

    for x in all_mimetypes.items():
        print "%30s: %s" % x


def test_parse_spine():
    #every item in the spine should be a string
    # the toc should be a string
    #no duplicates
    for book in TEST_FILES:
        spine, e = _get_elements(book, ('spine',))
        toc, order = epub.parse_spine(spine)
        assert isinstance(order, (list, tuple))
        if not isinstance(toc, basestring):
            print book, toc, basestring

        assert isinstance(toc, basestring)
        assert all(isinstance(x, basestring) for x in order)
        assert len(order) == len(set(order))


#XXX turned off because the archive.org ones fail, but I can't just dismiss them.
def _test_spine_manifest_match():
    #every item in the spine should be in the manifest (thence in the zip, tested above)
    #every xhtml in the manifest should be in the spine. (XXX unless there are fallbacks)
    bad_spine_files = []
    for book in TEST_FILES:
        #print book
        spine, manifest, e = _get_elements(book, ('spine', 'manifest'))
        toc, order = epub.parse_spine(spine)
        pwd = os.path.dirname(e.opf_file)
        files = epub.parse_manifest(manifest, pwd)

        assert toc not in order
        xhtmls = set(order)
        for x in order:
            name, mimetype = files.pop(x)
            if mimetype != 'application/xhtml+xml':
                bad_spine_files.append((book, name, mimetype))

        name, mimetype = files.pop(toc)
        assert mimetype == 'application/x-dtbncx+xml'
        remaining = (x[1] for x in files.values())
        if any(x in ('application/x-dtbncx+xml', 'application/xhtml+xml') for x in remaining):
            print book, set(remaining)

        assert not any(x in ('application/x-dtbncx+xml', 'application/xhtml+xml') for x in remaining)

    if bad_spine_files:
        bsf = {}
        for book, fn, mt in bad_spine_files:
            mimecount = bsf.setdefault(book, {})
            mimecount[mt] = mimecount.get(mt, 0) + 1

        pprint(bsf)

        raise AssertionError('bad spine files in %s' % bsf.keys())



