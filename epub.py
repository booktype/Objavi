"""Module for dealing with epub -> booki conversions."""

import os, sys
from pprint import pprint
import zipfile
from cStringIO import StringIO

import lxml, lxml.html, lxml.etree, lxml.cssselect

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

    def zip2tree(self, name):
        """get an etree from the given zip filename"""
        #Note: python 2.6 (not 2.5) has zipfile.open
        s = self.zip.read(name)
        f = StringIO(s)
        tree = lxml.etree.parse(f)
        f.close()
        return tree


    def parse_opf(self):
        """
        <metadata>
        <dc:title>A Treatise of Human Nature</dc:title>
        <dc:creator>David Hume</dc:creator>
        <dc:date>2008-09-04</dc:date>
        <dc:subject>Philosophy</dc:subject>
        <dc:language>en</dc:language>
        <dc:publisher>web-books.com</dc:publisher>
        <dc:identifier id="BookId">web-books-1053</dc:identifier>
        </metadata>
        <manifest>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
        <item id="W000Title" href="000Title.html" media-type="application/xhtml+xml" />
        <item id="WHume_NatureC01" href="Hume_NatureC01.html" media-type="application/xhtml+xml" />
        <item id="style" href="style.css" media-type="text/css" />
        <item id="cover" href="cover.jpg" media-type="image/jpeg" />
        </manifest>
        <spine toc="ncx">
        <itemref idref="W000Title" />
        <itemref idref="WHume_NatureC01" />
        </spine>
        """
        pwd = os.path.dirname(self.opf_file)
        tree = self.zip2tree(self.opf_file)
        root = tree.getroot()
        #print tree.getroot().nsmap
        nsmap = {'opf': 'http://www.idpf.org/2007/opf'}
        metadata = root.xpath('.//opf:metadata', namespaces=nsmap)[0]
        manifest = root.xpath('.//opf:manifest', namespaces=nsmap)[0]
        spine = root.xpath('.//opf:spine', namespaces=nsmap)[0]

        md = parse_metadata(metadata)
        files = parse_manifest(manifest, pwd)
        ncx, order = parse_spine(spine)


        return md


def parse_metadata(metadata, nsmap=None):

    """metadata is an OPF metadata node, as defined at
    http://www.idpf.org/2007/opf/OPF_2.0_final_spec.html#Section2.2
    (or a dc-metadata or x-metadata child thereof).

    """
    if nsmap is None:
        nsmap = metadata.nsmap

    #print nsmap
    # the node probably has at least dc, opf, and None namespace prefixes.
    # None and opf probably map to the same thing.
    # We ultimately don't care about the prefixes because they are local to the file.
    nsdict = dict((v, {}) for v in nsmap.values())
    pfdict = dict((k, nsdict[v]) for k, v in nsmap.iteritems())
    nstags = dict((k, '{%s}' % v) for k, v in nsmap.iteritems())
    default_ns = nstags[None]

    def add_item(prefix, tag, value, extra):
        #any key can be duplicate, so store in a list        
        values = pfdict[prefix].setdefault(tag, [])
        values.append((value, extra))

    for t in metadata.iterdescendants():
        #look for special OPF tags
        if t.tag == default_ns + 'meta':
            #meta tags <meta name="" content="" />
            name = t.get('name')
            content = t.get('content')
            others = tuple((k, v) for k, v in t.items() if k not in ('name', 'content'))
            if ':' in name:
                # the meta tag is using xml namespaces.
                prefix, name = name.split(':', 1)
            else:
                prefix = None
            add_item(prefix, name, content, others)
            continue

        if t.tag in (default_ns + 'dc-metadata', default_ns + 'x-metadata'):
            # Subelements of these deprecated elements are in either
            # DC or non-DC namespace (respectively).  Of course, this
            # is true of any element anyway, so it is sufficent to
            # ignore this.
            #
            # In an earlier version I assumed this tag cast the child
            # namespace, but it seems not.
            log("found a live %s tag; descending into but otherwise ignoring it" % t.tag[len(default_ns):])
            continue

        tag = t.tag[len(nstags[t.prefix]):]
        add_item(t.prefix, tag, t.text,
                 tuple((k.replace(default_ns, ''), v) for k, v in t.items()))

    return nsdict

def parse_manifest(manifest, pwd):
    """
    Only contains <item>s; each <item> has id, href, and media-type.

    It includes 'toc.ncx', but not 'media-type',
    'META-INF/container.xml' or the pbf file (i.e., the files needed
    to get this far).

    The manifest can specify fallbacks for unrecognised documents, but
    Espri does not use that.

    <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
    <item id="W000Title" href="000Title.html" media-type="application/xhtml+xml" />
    <item id="WHume_NatureC01" href="Hume_NatureC01.html" media-type="application/xhtml+xml" />
    <item id="style" href="style.css" media-type="text/css" />
    <item id="cover" href="cover.jpg" media-type="image/jpeg" />
    </manifest>
    """
    items = {}
    ns = '{%s}' % manifest.nsmap[None]

    for t in manifest.iterchildren(ns + 'item'):
        id = t.get('id')
        href = os.path.join(pwd, t.get('href'))
        media_type = t.get('media-type')
        items[id] = (href, media_type)

    #pprint(items)
    return items

def parse_spine(spine):
    """The spine is an ordered list of xhtml documents (or dtbook, but
    Booki can't edit that, or manifest items that 'fallback' to xhtml,
    which Espri doesn't yet handle).  Also, anything in the manifest
    that can be in the spine, must be.

    Spine itemrefs can have a 'linear' attribute, with a value of
    'yes' or 'no' (defaulting to 'yes').  If an item is linear, it is
    in the main stream of the book.  Readers are allowed to ignore
    this distinction (maybe Booki will).

    The toc attribute points to the ncx file (via manifest id).
    """
    items = []
    ns = '{%s}' % spine.nsmap[None]
    for t in spine.iterchildren(ns + 'itemref'):
        items.append( t.get('idref'))

    for attr in ('toc', ns + 'toc'):
        toc = spine.get(attr)

    return toc, items

def parse_ncx(ncx):
    """
    The NCX file is the closest thing to FLOSS Manuals TOC.txt.  It
    describes the heirarchical structure of the document (wheras the
    spine describes its 'physical' structure).
    """


