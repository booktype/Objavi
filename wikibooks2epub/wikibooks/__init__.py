#!/usr/bin/python
# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
# written by j@mailb.org 2009
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from __future__ import division
import re
import os
import shutil
import tempfile
import hashlib
try:
    import xml.etree.ElementTree as ET
except:
    import elementtree.ElementTree as ET

import simplejson as json


from oxlib.cache import readUrlUnicode, saveUrl, readUrl
from urllib import quote, unquote

wikibooks_base = 'http://en.wikibooks.org'
wikibooks_api = wikibooks_base + '/w/api.php'

def wikiApi(**args):
    _default_args = {
        'format': 'json',
        'action': 'query',
    }
    for key in _default_args:
        if key not in args:
            args[key] = _default_args[key]
    url = wikibooks_api
    args = ['%s=%s' % (quote(str(key)), quote(args[key].encode('utf-8'))) for key in args]
    url += '?' + '&'.join(args)
    data = readUrlUnicode(url)
    return json.loads(data)

def normalizeTitle(title):
    title = title.replace('_', ' ').strip()
    if title.endswith('/'): title = title[:-1]
    return title

def pageMarkup(title):
    title = normalizeTitle(title)
    txt = wikiApi(action='query', prop='revisions',
                  rvexpandtemplates='1', titles=title, rvprop='content')
    txt = txt['query']['pages'].values()[0]
    if 'revisions' in txt:
        txt = txt['revisions'][0].values()[0]
    else:
        txt = None
    return txt

def pageHtml(title):
    title = normalizeTitle(title)
    data = wikiApi(action='parse', redirects='1', page=title)
    txt = data['parse']['text']['*']

    #cleanup wiki stuff
    txt = re.sub('\[<a href.*?>.*?edit</a>\]','', txt)

    #expand local image links
    txt = re.sub('src="(/.*?)"','src="%s\\1"'%wikibooks_base, txt)
    return txt

def localImageLink(url):
    url = url.replace('/', '_').replace(' ', '_')
    if len(url) > 255: #removing folders, names can get to long
        e = os.path.splitext(url)
        domain = url.replace('http:__', '').split('_')[0]
        url = '%s_%s'%(domain, hashlib.sha1(url).hexdigest())
        if len(e) == 2:
            url += e[1]
    return 'static/%s'%url

def pageHtmlLocal(title, bookTitle):
    txt = pageHtml(title)

    #remove link from images
    txt = re.sub('<a.*? href="/wiki/File:.*?" .*?>(.*?)</a>','\\1', txt)

    #replace image link with local image
    def img_link(matchobj):
        url = normalizeTitle(matchobj.group(1))
        return 'src="%s"'%localImageLink(url)
    txt = re.sub('src="http://(.*?)"',img_link, txt)

    #txt = re.sub('src="http://(.*?)"','src="static/\\1"', txt)

    def epub_link(matchobj):
        title = normalizeTitle(matchobj.group(1))
        if not title.startswith(bookTitle):
            return 'href="%s"'%(wikibooks_base + '/wiki/' + title)
        return 'href="%s.html"'%title.replace('/', '_')

    #use local links to other chapters
    txt = re.sub('href="/wiki/(.*?)"', epub_link, txt)
    txt = re.sub('href="/w/index.php\?title=(.*?)&amp(.*?)"', epub_link, txt)


    #strip scripts
    script_reg = re.compile('<script type="text\/javascript">.*?<\/script>', re.DOTALL)
    txt = re.sub(script_reg, '', txt)
    
    #remove cruft
    txt = txt.replace('<div class="magnify"><img src="static/en.wikibooks.org_skins-1.5_common_images_magnify-clip.png" width="15" height="11" alt="" /></div>', '')
    txt = re.sub('<a href=".*?&amp;action=edit" class="external text" rel="nofollow"><font class="noprint" style="white-space:nowrap; font-size:smaller;">edit TOC</font></a>','', txt)
    return txt

def pageImages(title):
    html = pageHtml(title)
    images = re.compile('<img.*?src="(.*?)"', re.DOTALL).findall(html)
    return images

def pageLinks(title):
    '''
        return all wiki links of a page in a list
    '''
    links = []
    title = normalizeTitle(title)
    data = wikiApi(action='parse', redirects='1', page=title, prop='links')
    for l in data['parse']['links']:
        links.append(l['*'])
    return links

def bookLinks(title, bookTitle=None, recursive=False, _links=[]):
    '''
        return all wiki links of a book with given title
    '''
    title = normalizeTitle(title)
    if not bookTitle:
        bookTitle = title

    links = pageLinks(title)
    links = [l.startswith('/') and title + l or l for l in links]
    links = filter(lambda link: link.startswith(bookTitle), links)
    links = filter(lambda link: link not in _links, links)
    if recursive:
        __links = _links + links
        for l in links:
            new_links = bookLinks(l, bookTitle=bookTitle, recursive=True, _links=__links)
            new_links = filter(lambda link: link not in __links, new_links)
            links = links + new_links
    links = sorted(list(set(links)))
    return links

def savePage(title, base='/tmp/book', bookTitle=''):
    title = normalizeTitle(title)
    html = pageHtmlLocal(title, bookTitle)
    filetitle = "%s.html" % title.replace('/', '_')
    filename = os.path.join(base, filetitle)
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    f = open(filename, 'w')
    f.write('<?xml version="1.0" encoding="utf-8"?>\n')
    f.write('<html xmlns="http://www.w3.org/1999/xhtml"><head>')
    f.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />')
    f.write('<link rel="stylesheet" href="stylesheet.css" type="text/css" />')
    f.write('</head><body>\n');
    f.write(html.encode('utf-8'))
    f.write('\n</body></html>');
    f.close()
    return filetitle

def saveImages(title, base='/tmp/book'):
    #use cache for now
    #from oxlib.net import saveUrl
    images = pageImages(title)
    _images = []
    for image in images:
        f = os.path.join(base, unquote(localImageLink(image).replace('http:__', '')))
        _images.append(f.replace(base+'/', ''))
        if not os.path.exists(f.encode('utf-8')):
            saveUrl(image, f)
    return _images

def epub_files(title, items):
    n = 0
    def mime(item):
        extension = os.path.splitext(item)[-1]
        return {
            '.css': 'text/css',
            '.html': 'application/xhtml+xml',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.jpg': 'image/jpg',
        }.get(extension, 'application/octet-stream')

    content = ET.Element('package')
    content.attrib['xmlns:dc'] = "http://purl.org/dc/elements/1.1/"
    content.attrib['xmlns'] = "http://www.idpf.org/2007/opf"
    content.attrib['version'] = "2.0"
    content.attrib['unique-identifier'] = "bookid"
    metadata = ET.SubElement(content, "metadata")
    e = ET.SubElement(metadata, "dc:type")
    e.text = 'Text'
    e = ET.SubElement(metadata, "dc:title")
    e.text = title
    e = ET.SubElement(metadata, "dc:creator")
    e.text = 'Wikibooks.org'
    e = ET.SubElement(metadata, "dc:publisher")
    e.text = 'Wikibooks.org'
    e = ET.SubElement(metadata, "dc:language")
    e.text = 'en'
    e = ET.SubElement(metadata, "dc:source")
    e.text = 'http://en.wikiboooks.org/wiki/%s' % title
    e = ET.SubElement(metadata, "dc:identifier")
    e.attrib['id'] = 'bookid'
    e.text = 'http://en.wikiboooks.org/wiki/%s' % title

    manifest = ET.SubElement(content, "manifest")
    spine = ET.SubElement(content, "spine")
    spine.attrib['toc'] = 'ncx'

    def manifest_item(href, id, type):
        item = ET.SubElement(manifest, 'item')
        item.attrib['href'] = href
        item.attrib['id'] = id
        item.attrib['media-type'] = type

    def spine_item(idref):
        item = ET.SubElement(spine, 'itemref')
        item.attrib['idref'] = idref

    #toc.ncx
    toc = ET.Element('ncx')
    toc.attrib['xmlns'] = "http://www.daisy.org/z3986/2005/ncx/"
    toc.attrib['version'] = "2005-1"
    head = ET.SubElement(toc, "head")
    e = ET.SubElement(head, "meta")
    e.attrib['name'] = 'dtb:uid'
    e.attrib['content'] = title
    e = ET.SubElement(head, "meta")
    e.attrib['name'] = 'dtb:depth'
    e.attrib['content'] = '1'
    e = ET.SubElement(head, "meta")
    e.attrib['name'] = 'dtb:totalPageCount'
    e.attrib['content'] = '0'
    e = ET.SubElement(head, "meta")
    e.attrib['name'] = 'dtb:maxPageNumber'
    e.attrib['content'] = '0'

    docTitle = ET.SubElement(toc, "docTitle")
    text = ET.SubElement(docTitle, "text")
    text.text = title
    navMap = ET.SubElement(toc, "navMap")

    def navPoint(n, label, content):
        nav = ET.SubElement(navMap, "navPoint")
        nav.attrib['id'] = "chapter%d" % n
        nav.attrib['playOrder'] = "%d" % n
        e = ET.SubElement(nav, "navLabel")
        e = ET.SubElement(e, "text")
        e.text = label
        e = ET.SubElement(nav, "content")
        e.attrib['src'] = content

    #default manifest items
    manifest_item('toc.ncx', 'ncx', 'application/x-dtbncx+xml')
    manifest_item('stylesheet.css', 'css', 'text/css')

    items = sorted(list(set(items)))
    for item in items:
        n += 1
        manifest_item(item, 'item%d' % n, mime(item))
        if mime(item) == 'application/xhtml+xml':
            spine_item('item%d' % n)
            label = item.replace('_', ' ')[:-5]
            navPoint(n, label, item)

    content_xml = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(content, 'utf-8')
    toc_ncx = '<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">\n' + ET.tostring(toc, 'utf-8')

    return content_xml, toc_ncx

def container(base):
    xml = '''<?xml version='1.0' encoding='utf-8'?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile media-type="application/oebps-package+xml" full-path="content.opf"/>
  </rootfiles>
</container>'''
    if not os.path.exists(base+'/META-INF'):
        os.makedirs(base+'/META-INF')
    f = open(base+'/META-INF/container.xml', 'w')
    f.write(xml)
    f.close()
    f = open(base+'/mimetype', 'w')
    f.write('application/epub+zip')
    f.close()

def createEpub(title, output=None):
    pages = bookLinks(title, recursive=True)
    tmptree = tempfile.mkdtemp(prefix="epub.")
    base = os.path.join(tmptree, title)

    #FIXME: other css might be better suited
    url = 'http://en.wikibooks.org/skins-1.5/common/commonPrint.css'
    saveUrl(url, base+'/stylesheet.css')

    #write html pages and related images
    items = []
    for page in pages:
        items.append(savePage(page, base, bookTitle=title))
        items += saveImages(page, base)

    #write basic epub info and create epub
    content_opf, toc_ncx = epub_files(title, items)
    f = open(base+'/content.opf', 'w')
    f.write(content_opf)
    f.close()
    f = open(base+'/toc.ncx', 'w')
    f.write(toc_ncx)
    f.close()
    container(base)
    tmp_output=os.path.join(tmptree, '%s.epub'%title)
    cmd = u'cd "%s";zip -q0X  "%s" mimetype;zip -qXr9D  "%s" *'%(base, tmp_output, tmp_output)
    os.system(cmd.encode('utf-8'))
    if output:
        shutil.copyfile(tmp_output, output)
        shutil.rmtree(tmptree)

def getTitle(url):
    data = readUrlUnicode(url)
    return re.compile('wgTitle="(.*?)",').findall(data)[0]

if __name__ == '__main__':
    import sys
    title = getTitle(sys.argv[1])
    createEpub(title)

