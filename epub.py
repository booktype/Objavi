"""Module for dealing with epub -> booki conversions."""

import os, sys
from pprint import pprint
import zipfile
from cStringIO import StringIO

import lxml, lxml.html, lxml.etree, lxml.cssselect

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
        tree = self.zip2tree(self.opf_file)
        root = tree.getroot()
        #print tree.getroot().nsmap
        nsmap = {'opf': 'http://www.idpf.org/2007/opf'}
        metadata = root.xpath('.//opf:metadata', namespaces=nsmap)[0]
        manifest = root.xpath('.//opf:manifest', namespaces=nsmap)[0]
        spine = root.xpath('.//opf:spine', namespaces=nsmap)[0]

        md = parse_metadata(metadata)


        return md



def parse_metadata(metadata, nsmap=None, recurse=True):
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

    for t in metadata.iterchildren():
        #look for special OPF tags
        if t.tag == nstags[None] + 'meta':
            #meta tags <meta name="" content="" />
            #del t.nsmap[None]
            #print lxml.etree.tostring(t)
            name = t.get('name')
            content = t.get('content')
            others = [(k, v) for k, v in t.items() if k not in ('name', 'content')]
            prefix = None
            if ':' in name:
                # the meta tag is using xml namespaces
                prefix, name = name.split(':', 1)
            pfdict.get(prefix, pfdict[None])[name] = (content, others)
            continue

        if t.tag == nstags[None] + 'dc-metadata' and recurse:
            #contents are DC metadata tags, which means (i think) we
            #need to look for sub-elements and set their namespace to
            #DC.  There should only be one level of nesting, so set
            #recurse to False.
            submap = nsmap.copy()
            submap[None] = NAMESPACES['dc']
            subdict = parse_metadata(t, submap, recurse=False)
            for k, v in subdict.items():
                if k not in nsdict:
                    nsdict[k] = {}
                nsdict[k].update(v)
            continue

        if t.tag == nstags[None] + 'x-metadata' and recurse:
            #contents are non-dc-metadata tags.  Namespace is presumably unchanged.
            subdict = parse_metadata(t, nsmap, recurse=False)
            for k, v in subdict.items():
                if k not in nsdict:
                    nsdict[k] = {}
                nsdict[k].update(v)
            continue
        tag = t.tag.replace('{' + nsmap[t.prefix] + '}', '')

        #any key can be duplicate, so store in a list
        values = pfdict[t.prefix].setdefault(tag, [])
        values.append((t.text, tuple((k.replace(default_ns, ''), v) for k, v in t.items())))

    return nsdict




