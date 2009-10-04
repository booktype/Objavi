"""Module for dealing with epub -> booki conversions."""

import os, sys
from pprint import pprint
import zipfile
from cStringIO import StringIO

from booki.xhtml_utils import new_html_doc()

try:
    from json import dumps
except ImportError:
    from simplejson import dumps

import lxml, lxml.html, lxml.cssselect
from lxml import etree

XMLNS = '{http://www.w3.org/XML/1998/namespace}'
DAISYNS = '{http://www.daisy.org/z3986/2005/ncx/}'
OPFNS = '{http://www.idpf.org/2007/opf}'
CONTAINERNS = '{urn:oasis:names:tc:opendocument:xmlns:container}'
XHTMLNS = '{http://www.w3.org/1999/xhtml}'

XHTML = 'http://www.w3.org/1999/xhtml'
DC = "http://purl.org/dc/elements/1.1/"

def log(*messages, **kwargs):
    for m in messages:
        try:
            print >> sys.stderr, m
        except Exception:
            print >> sys.stderr, repr(m)



def new_doc(guts="", version="1.1", lang=None):
    xmldec = '<?xml version="1.0" encoding="UTF-8"?>'
    doctypes = {
        '1.1': ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"'
                '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">'),
        '1.0': ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"'
                '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
    }

    if lang in (None, 'und', 'UND'):
        langdec = ''
    else:
        langdec = 'xml:lang="%s" lang="%s"' % (lang, lang)

    doc = ('<html xmlns="%s" version="XHTML %s" %s>'
           '<head></head><body>%s</body></html>'
           % (XHTML, version, langdec, guts))

    f = StringIO(xmldec + doctypes.get(version, '') + doc)
    tree = lxml.html.parse(f)
    f.close()
    return tree


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
        self.origin = src

    def gettree(self, name=None, id=None, parse=etree.parse):
        """get an etree from the given zip filename or manifest ID"""
        if name is None:
            name, mimetype = self.manifest[id]
        #Note: python 2.6 (not 2.5) has zipfile.open
        s = self.zip.read(name)
        f = StringIO(s)
        tree = parse(f)
        f.close()
        return tree

    def parse_meta(self):
        '''META-INF/container.xml contains one or more <rootfile>
        nodes.  We want the "application/oepbs-package+xml" one.

        <rootfile full-path="OEBPS/Great Expectations.opf" media-type="application/oebps-package+xml" />
        <rootfile full-path="PDF/Great Expectations.pdf" media-type="application/pdf" />

        Other files are allowed in META-INF, but none of them are much
        use.  They are manifest.xml, metadata.xml, signatures.xml,
        encryption.xml, and rights.xml.
        '''
        tree = self.gettree('META-INF/container.xml')
        for r in tree.getiterator(CONTAINERNS + 'rootfile'):
            if r.get('media-type') == "application/oebps-package+xml":
                rootfile = r.get('full-path')
                break
        else:
            raise EpubError("No OPF rootfile found")

        self.opf_file = rootfile

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
        pwd = os.path.dirname(self.opf_file) #needed for mainfest parsing
        tree = self.gettree(self.opf_file)
        root = tree.getroot()
        metadata = root.find(OPFNS + 'metadata')
        manifest = root.find(OPFNS + 'manifest')
        spine = root.find(OPFNS + 'spine')
        #there is also an optional guide section, which we ignore

        self.metadata = parse_metadata(metadata)
        self.manifest = parse_manifest(manifest, pwd)
        ncxid, self.spine = parse_spine(spine)
        self.ncxfile = self.manifest[ncxid][0]

    def parse_ncx(self):
        ncx = self.gettree(self.ncxfile)
        self.ncxdata = parse_ncx(ncx)

    def raw_json(self):
        """get all the known metadata and nav data as json."""
        data = {
            'metadata': self.metadata,
            'manifest': self.manifest,
            'spine': self.spine,
            'ncx': self.ncxdata
            }
        return dumps(data, indent=2)

    def find_language(self):
        opflang = [x[0].lower() for x in
                   self.metadata.get(DC, {}).get('language', ())]

        # XXX Should the ncx language enter into it? Being xml:lang,
        # it is in theory just the language of the ncx document
        # itself.  But if the metadata lacks language, should it be
        # used instead? At present, NO.
        #ncxlang = self.ncxdata['headers'].get('lang', ())

        # XXX also, for now, ignoring case of badly formed language
        # codes, conflicting or supplementary languages, etc.
        opflang = [x for x in opflang if x not in ('und', '')]
        if not opflang:
            return None
        if len(set(opflang)) > 1:
            log('%s metadata has more than one language: %s -- using first one'
                % (self.origin, opflang))
        return opflang[0]

    def find_probable_chapters(self):
        """Try to find the real chapters from the NCX file.  The
        problem is that different epubs all use their own level of
        nesting."""
        # the Black Arrow has (book 1 (c1, c2, c3), book2 (c4, c5, c6..))
        # and FM books have (section 1 (c1, c2,..),..)
        # i.e super-chapter blocks
        # some have (((c1, c2, c3))) -- deeply nested chapters
        # some have no real chapters, but stupid structure
        points = self.ncxdata['navmap']['points']
        chapter_depth, serial_points, splits = get_chapter_breaks(points)
        return chapter_depth, serial_points, splits

    def concat_document(self):
        """Join all the xhtml files together, putting in markers
        indicating where the splits should be.
        """
        lang = self.find_language()
        points = self.ncxdata['navmap']['points']
        chapter_depth, serial_points, chapter_markers = get_chapter_breaks(points)
        doc = new_doc(lang=lang)
        for ID in self.spine:
            fn, mimetype = self.manifest[ID]
            if mimetype.startswith('image'):
                tree = new_doc(guts='<img src="%s" alt="" />' % fn)
            else:
                tree = self.gettree(fn, parse=_html_parse)

            #add_marker(doc, 'espri-new-file-%s' % ID, fn)

            for depth, fragment, point in chapter_markers.get(fn, ()):
                if fragment:
                    start = tree.xpath("//*[@id='%s']" % fragment)[0]
                else:
                    start = body
                labels = point['labels']
                add_marker(start, 'espri-chapter-%(id)s' % point,
                           title=labels.get(lang, '\n'.join(labels.values())),
                           subsections=str(bool(point['points'])))

                add_marker(body, 'espri-new-file-%s' % ID, title=fn)
            add_guts(tree, doc)
        return doc




def add_guts(src, dest):
    """Append the contents of the <body> of one tree onto that of
    another.  The source tree will be emptied."""
    #print  lxml.etree.tostring(src)
    sbody = _find_tag(src, 'body')
    dbody = _find_tag(dest, 'body')
    if len(dbody):
        dbody[-1].tail = ((dbody[-1].tail or '') +
                          (sbody.text or '')) or None
    else:
        dbody.text = sbody.text

    for x in sbody:
        dbody.append(x)

    dbody.tail = ((dbody.tail or '') +
                  (sbody.tail or '')) or None


def _xhtml_parse(*args, **kwargs):
    kwargs['parser'] = lxml.html.XHTMLParser(encoding="utf-8")
    return lxml.html.parse(*args, **kwargs)

def _html_parse(*args, **kwargs):
    kwargs['parser'] = lxml.etree.HTMLParser(encoding="utf-8")
    return lxml.html.parse(*args, **kwargs)


def _find_tag(doc, tag):
    #log(lxml.etree.tostring(doc, encoding='utf-8', method='html').replace('&#13;', ''))
    try:
        return doc.iter(XHTMLNS + tag).next()
    except StopIteration:
        return doc.iter(tag).next()

def add_marker(el, ID, title=None, klass="espri-marker"):
    marker = el.makeelement('hr')
    marker.set('id', ID)
    marker.set('class', klass)
    if title is not None:
        marker.set('title', title)
    parent = el.getparent()
    index = parent.index(el)
    parent.insert(index, marker)



def get_chapter_breaks(points):
    #
    # first go is quite naive: go to deepest level that is in
    # every branch, not counting top level divisions (which may be
    # cover, prologue, etc).
    serial_points = []
    #pprint(points)
    #lcb == lowest common depth (> 1)
    def serialise(p, depth):
        serial_points.append((depth, p))
        #if p['class']:
        #    log("found class=='%s' at depth %s" % (p['class'], depth))
        if not p.get('points'):
            return depth
        lcd = 1e999
        for child in p['points']:
            bottom = serialise(child, depth + 1)
            lcd = min(bottom, lcd)
        return lcd

    lcd = 999
    depths = []
    for p in points:
        depth = serialise(p, 1)
        depths.append(depth)
        if 1 < depth < lcd:
            lcd = depth
    if lcd == 999:
        lcd = 1
    #log(depths)

    # The book should now be split on all the points at chapter depth
    # (lcd), and all higher points butnot if the higher point is at
    # the same location as the chapter.  If the chapter start url has
    # a fragment id (e.g. "something.html#chapter-6"), then the split
    # is internal to the chapter.  What the book serialiser needs is a
    # mapping from file names to the split-ids in that chapter, so
    # construct that.

    splits = {}
    for depth, p in serial_points:
        if depth > lcd:
            continue #ignore the sub-sections
        url, ID = p['content_src'], None
        if '#' in url:
            log("GOT a fragment! %s" % url)
            url, ID = url.split('#', 1)
        s = splits.setdefault(url, [])
        s.append((depth, ID, p))

    return lcd, serial_points, splits






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
    """get text content from an <xx><text>...</text></xx> construct,
    as is common in NCX files."""
    # there will only be one <text>, but for...iter is still easiest
    for t in e.iter(DAISYNS + 'text'):
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
    for meta in head.findall(DAISYNS + 'meta'):
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

    ret = {
        'headers':  headers,
        'navmap':   parse_navmap(root.find(DAISYNS + 'navMap')),
    }

    #Try adding these bits, even though no-one has them and they are no use.
    pagelist = ncx.find(DAISYNS + 'pageList')
    navlist = ncx.find(DAISYNS + 'navList')
    if pagelist is not None:
        ret['pagelist'] = parse_pagelist(pagelist)
    if navlist is not None:
        ret['navlist'] = parse_navlist(navlist)

    return ret


def parse_navmap(e):
    #<!ELEMENT navMap (navInfo*, navLabel*, navPoint+)>
    #XXX move info and labels out of navmap, and into headers?
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
        'class': e.get('class'),
        'play_order': int(e.get('playOrder')),
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
        'targets': tuple(parse_pagetarget(x) for x in e.findall(DAISYNS + 'pageTarget')),
        }

def parse_pagetarget(e):
    #<!ELEMENT pageTarget (navLabel+, content)>
    labels = get_labels(e)
    c = e.find(DAISYNS + 'content')
    ret = {
        'id': e.get('id'),
        'type': e.get('type'),
        'play_order': int(e.get('playOrder')),
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
        'targets': tuple(parse_pagetarget(x) for x in e.findall(DAISYNS + 'navTarget')),
        }

def parse_navtarget(e):
    #<!ELEMENT navTarget (navLabel+, content)>
    labels = get_labels(e)
    c = e.find(DAISYNS + 'content')
    ret = {
        'id': e.get('id'),
        'play_order': int(e.get('playOrder')),
        'content_src': c.get('src'),
        'labels': get_labels(e),
    }
    value = e.get('value')
    if value is not None:
        ret['value'] = value
    return ret
