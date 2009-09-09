"""Module for dealing with epub -> booki conversions."""

import os, sys
#from urllib2 import urlopen
import zipfile
from cStringIO import StringIO

import lxml, lxml.html, lxml.etree, lxml.cssselect

class EpubError(Exception):
    pass

def string_tree(s):
    f = StringIO(s)    
    tree = lxml.etree.parse(f)
    f.close()
    return tree
    

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
            raise EpubError("No OEPBS rootfile found")

        self.oepbs_root = rootfile



