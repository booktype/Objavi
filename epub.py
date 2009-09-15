"""Module for dealing with epub -> booki conversions."""

import os, sys
from pprint import pprint
import zipfile
from cStringIO import StringIO

import lxml, lxml.html, lxml.etree, lxml.cssselect

XMLNS = '{http://www.w3.org/XML/1998/namespace}'
DAISYNS = '{http://www.daisy.org/z3986/2005/ncx/}'

def log(*messages, **kwargs):
    for m in messages:
        try:
            print >> sys.stderr, m
        except Exception:
            print >> sys.stderr, repr(m)


NAMESPACES = {
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/', #dublin core
    'tei': 'http://www.tei-c.org/ns/1.0',
    'dcterms': 'http://purl.org/dc/terms/',
    'nzetc': 'http://www.nzetc.org/structure',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

class EpubError(Exception):
    pass


class Epub(object):
    """

    Abstract Container:
    META-INF/
       container.xml
       [manifest.xml]
       [metadata.xml]
       [signatures.xml]
       [encryption.xml]
       [rights.xml]
    OEBPS/
       Great Expectations.opf
       cover.html
       chapters/
          chapter01.html
          chapter02.html
          <other HTML files for the remaining chapters>

    """
    def load(self, src):
        #XXX if zip variability proves a problem, we should just use
        #an `unzip` subprocess
        if isinstance(src, str):
            # Should end with PK<06><05> + 18 more.
            # Some zips contain 'comments' after that, which breaks ZipFile
            zipend = src.rfind('PK\x05\x06') + 22
            if len(src) != zipend:
                log('Bad zipfile?')
                src = src[: zipend]
            src = StringIO(src)
        self.zip = zipfile.ZipFile(src, 'r', compression=zipfile.ZIP_DEFLATED, allowZip64=True)
        self.names = self.zip.namelist()
        self.info = self.zip.infolist()


    def parse_meta(self):
        '''META-INF/container.xml contains one or more <rootfile>
        nodes.  We want the "application/oepbs-package+xml" one.

        <rootfile full-path="OEBPS/Great Expectations.opf" media-type="application/oebps-package+xml" />
        <rootfile full-path="PDF/Great Expectations.pdf" media-type="application/pdf" />

        If there is only one (as is common), forget the media-type.

        Other files are allowed in META-INF, but none of them are much
        use.  They are manifest.xml, metadata.xml, signatures.xml,
        encryption.xml, and rights.xml.
        '''
        xml = self.zip.read('META-INF/container.xml')
        tree = lxml.etree.XML(xml)
        for r in tree.xpath('.//a:rootfile', namespaces={'a': tree.nsmap[None]}):
            if r.attrib['media-type'] == "application/oebps-package+xml":
                rootfile = r.attrib['full-path']
                break
        else:
            raise EpubError("No OPF rootfile found")

        self.opf_file = rootfile

    def gettree(self, name):
        """get an etree from the given zip filename"""
        #Note: python 2.6 (not 2.5) has zipfile.open
        s = self.zip.read(name)
        f = StringIO(s)
        tree = lxml.etree.parse(f)
        f.close()
        return tree


    def parse_opf(self):
        """
        The opf file is arranged like this:
        <package>
        <metadata />
        <manifest />
        <spine />
        <guide />
        </package>

        Metadata, manifest and spine are parsed in separate helper
        functions.
        """
        pwd = os.path.dirname(self.opf_file)
        tree = self.gettree(self.opf_file)
        root = tree.getroot()
        ns = '{http://www.idpf.org/2007/opf}'
        metadata = root.find(ns + 'metadata')
        manifest = root.find(ns + 'manifest')
        spine = root.find(ns + 'spine')
        #there is also an optional guide section, which we ignore

        self.metadata = parse_metadata(metadata)
        self.files = parse_manifest(manifest, pwd)
        ncxid, self.order = parse_spine(spine)
        self.ncxfile = self.files[ncxid][0]

    def parse_ncx(self):
        ncx = self.gettree(self.ncxfile)
        toc = parse_ncx(ncx)
        return toc


def parse_metadata(metadata):
    """metadata is an OPF metadata node, as defined at
    http://www.idpf.org/2007/opf/OPF_2.0_final_spec.html#Section2.2
    (or a dc-metadata or x-metadata child thereof).

    """
    # the node probably has at least 'dc', 'opf', and None namespace
    # prefixes.  None and opf probably map to the same thing. 'dc' is
    # Dublin Core.
    nsmap = metadata.nsmap
    nstags = dict((k, '{%s}' % v) for k, v in nsmap.iteritems())
    default_ns = nstags[None]

    # Collect element data in namespace-bins, and map prefixes to
    # those bins for convenience
    nsdict = dict((v, {}) for v in nsmap.values())

    def add_item(ns, tag, value, extra):
        #any key can be duplicate, so store in a list
        if ns not in nsdict:
            nsdict[ns] = {}
        values = nsdict[ns].setdefault(tag, [])
        values.append((value, extra))

    for t in metadata.iterdescendants():
        #look for special OPF tags
        if t.tag == default_ns + 'meta':
            #meta tags <meta name="" content="" />
            name = t.get('name')
            content = t.get('content')
            others = tuple((k, v) for k, v in t.items() if k not in ('name', 'content'))
            if ':' in name:
                # the meta tag is using xml namespaces in attribute values.
                prefix, name = name.split(':', 1)
            else:
                prefix = None
            add_item(t.nsmap[prefix], name, content, others)
            continue

        if t.tag in (default_ns + 'dc-metadata', default_ns + 'x-metadata'):
            # Subelements of these deprecated elements are in either
            # DC or non-DC namespace (respectively).  Of course, this
            # is true of any element anyway, so it is sufficent to
            # ignore this (unless we want to cause pedantic errors).
            log("found a live %s tag; descending into but otherwise ignoring it"
                % t.tag[len(default_ns):])
            continue

        tag = t.tag[t.tag.rfind('}') + 1:]
        add_item(t.nsmap[t.prefix], tag, t.text,
                 tuple((k.replace(default_ns, ''), v) for k, v in t.items()))

    return nsdict

def parse_manifest(manifest, pwd):
    """
    Only contains <item>s; each <item> has id, href, and media-type.

    It includes 'toc.ncx', but not 'META-INF/container.xml' or the pbf
    file (i.e., the files needed to get this far).

    The manifest can specify fallbacks for unrecognised documents, but
    Espri does not use that (nor do any of the test epub files).

    <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
    <item id="WHume_NatureC01" href="Hume_NatureC01.html" media-type="application/xhtml+xml" />
    <item id="cover" href="cover.jpg" media-type="image/jpeg" />
    </manifest>
    """
    items = {}
    ns = '{%s}' % manifest.nsmap[None]

    for t in manifest.iterchildren(ns + 'item'):
        id = t.get('id')
        href = os.path.join(pwd, t.get('href'))
        media_type = t.get('media-type')
        items[id] = (href, media_type) #XXX does media-type matter?

    #pprint(items)
    return items

def parse_spine(spine):
    """The spine is an ordered list of xhtml documents (or dtbook, but
    Booki can't edit that, or manifest items that 'fallback' to xhtml,
    which Espri doesn't yet handle).  Also, anything in the manifest
    that can be in the spine, must be.

    Spine itemrefs can have a 'linear' attribute, with a value of
    'yes' or 'no' (defaulting to 'yes').  If an item is linear, it is
    in the main stream of the book.  Reader software is allowed to
    ignore this distinction, as Espri does.

    The toc attribute points to the ncx file (via manifest id).
    """
    items = []
    ns = '{%s}' % spine.nsmap[None]
    for t in spine.iterchildren(ns + 'itemref'):
        items.append(t.get('idref'))

    toc = spine.get('toc')

    return toc, items


def get_ncxtext(e):
    #get text from an <xx><text>...</text></xx> xconstruct
    t = e.find(DAISYNS + 'text')
    if t is not None:
        return t.text
    return '' # or leave it at None?

def get_labels(e, tag='{http://www.daisy.org/z3986/2005/ncx/}navLabel'):
    """Make a mapping of languages to labels."""
    # This reads navInfo or navLabel tags. navInfo is unlikely, but
    # navLabel is ubiquitous.  There can be one for each language, so
    # construct a dict.
    labels = {}
    for label in e.findall(DAISYNS + 'navLabel'):
        lang = label.get(XMLNS + 'lang')
        labels[lang] = get_ncxtext(e)
    return labels

def parse_ncx(ncx):
    """
    The NCX file is the closest thing to FLOSS Manuals TOC.txt.  It
    describes the heirarchical structure of the document (wheras the
    spine describes its 'physical' structure).
    """
    #<!ELEMENT ncx (head, docTitle, docAuthor*, navMap, pageList?, navList*)>

    headers = {}
    #if a header is set multiple times, keep all
    def setheader(name, content, scheme=None):
        values = headers.setdefault(name, [])
        values.append((content, scheme))

    head = ncx.find(DAISYNS + 'head')
    #<!ELEMENT head (meta+)>
    for meta in head.findall(DAISYNS + 'itemref'):
        #whatever 'scheme' is
        setheader(meta.get('name'), meta.get('content'), meta.get('scheme'))

    for t in ('docTitle', 'docAuthor'):
        for e in ncx.findall(DAISYNS + t):
            if e is not None:
                setheader(t, get_ncxtext(e))

    root = ncx.getroot()
    for attr, header in (('dir', 'dir'),
                         (XMLNS + 'lang', 'lang')):
        value = root.get(attr)
        if value is not None:
            setheader(header, value)

    #print lxml.etree.tostring(ncx)
    print [x for x in root.getchildren()]
    ret = {
        'headers':  headers,
        'navmap':   parse_navmap(root.find(DAISYNS + 'navMap')),
    }

    #Try adding these bits, even though noone has them and they are no use.
    pagelist = ncx.find(DAISYNS + 'pageList')
    navlist = ncx.find(DAISYNS + 'navList')
    if pagelist is not None:
        ret['pagelist'] = parse_pagelist(pagelist)
    if navlist is not None:
        ret['navlist'] = parse_navlist(navlist)

    return ret


def parse_navmap(e):
    #<!ELEMENT navMap (navInfo*, navLabel*, navPoint+)>
    print e
    return {
        'info': get_labels(e, DAISYNS + 'navInfo'),
        'labels': get_labels(e),
        'points': tuple(parse_navpoint(x) for x in e.findall(DAISYNS + 'navPoint')),
        }

def parse_navpoint(e):
    #<!ELEMENT navPoint (navLabel+, content, navPoint*)>
    c = e.find(DAISYNS + 'content')
    subpoints = tuple(parse_navpoint(x) for x in e.findall(DAISYNS + 'navPoint'))
    return {
        'id': e.get('id'),
        'play_order': e.get('playOrder'), #cast to int?
        #'content_id': c.get('id'),
        'content_src': c.get('src'),
        'labels': get_labels(e),
        'points': subpoints,
        }


def parse_pagelist(e):
    # <!ELEMENT pageList (navInfo*, navLabel*, pageTarget+)>
    return {
        'info': get_labels(e, DAISYNS + 'navInfo'),
        'labels': get_labels(e),
        'targets': tuple(parse_pagetarget(x) for point in e.findall(DAISYNS + 'pageTarget')),
        }

def parse_pagetarget(e):
    #<!ELEMENT pageTarget (navLabel+, content)>
    labels = get_labels(e)
    c = e.find(DAISYNS + 'content')
    ret = {
        'id': e.get('id'),
        'type': e.get('type'),
        'play_order': e.get('playOrder'),
        'content_src': c.get('src'),
        'labels': get_labels(e),
    }
    value = e.get('value')
    if value is not None:
        ret['value'] = value
    return ret

def parse_navlist(e):
    #<!ELEMENT navList (navInfo*, navLabel+, navTarget+)>
    return {
        'info': get_labels(e, DAISYNS + 'navInfo'),
        'labels': get_labels(e),
        'targets': tuple(parse_pagetarget(x) for point in e.findall(DAISYNS + 'navTarget')),
        }

def parse_navtarget(e):
    #<!ELEMENT navTarget (navLabel+, content)>
    labels = get_labels(e)
    c = e.find(DAISYNS + 'content')
    ret = {
        'id': e.get('id'),
        'play_order': e.get('playOrder'),
        'content_src': c.get('src'),
        'labels': get_labels(e),
    }
    value = e.get('value')
    if value is not None:
        ret['value'] = value
    return ret
