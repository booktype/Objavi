# Part of Objavi2, which turns html manuals into books.
# This contains classes representing books and coordinates their processing.
#
# Copyright (C) 2009 Douglas Bagnall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Library module representing a complete FM book being turned into a
PDF"""

import os, sys
import tempfile
import re, time
import random
import copy
from subprocess import Popen, check_call, PIPE
from cStringIO import StringIO
from urllib2 import urlopen, HTTPError
import zipfile
import traceback
from string import ascii_letters
from pprint import pformat

try:
    import json
except ImportError:
    import simplejson as json

import lxml.html
from lxml import etree

from objavi import config, epub_utils
from objavi.book_utils import log, run, make_book_name, guess_lang, guess_text_dir
from objavi.book_utils import ObjaviError, log_types
from objavi.pdf import PageSettings, count_pdf_pages, concat_pdfs, rotate_pdf, parse_outline, parse_extracted_outline
from objavi.epub import add_guts, _find_tag
from objavi.xhtml_utils import EpubChapter, split_tree, empty_html_tree, utf8_html_parser
from objavi.cgi_utils import url2path, path2url, try_to_kill

from iarchive import epub as ia_epub
from booki.bookizip import get_metadata, add_metadata

TMPDIR = os.path.abspath(config.TMPDIR)
DOC_ROOT = os.environ.get('DOCUMENT_ROOT', config.HTDOCS)
HTTP_HOST = os.environ.get('HTTP_HOST', '')

def find_archive_urls(bookid, bookname):
    s3url = 'http://s3.us.archive.org/booki-%s/%s' % (bookid, bookname)
    detailsurl = 'http://archive.org/details/booki-%s' % (bookid,)
    return (s3url, detailsurl)

def _get_best_title(tocpoint):
    if 'html_title' in tocpoint:
        return tocpoint['html_title']
    if 'title' in tocpoint:
        return tocpoint['title']
    return 'Untitled'

def _add_initial_number(e, n):
    """Put a styled chapter number n at the beginning of element e."""
    initial = e.makeelement("strong", Class="initial")
    e.insert(0, initial)
    initial.tail = ' '
    if e.text is not None:
        initial.tail += e.text
    e.text = ''
    initial.text = "%s." % n

def expand_toc(toc, depth=1, index=0):
    """Reformat toc slightly for convenience"""
    for item in toc:
        url = item.get('url') or ''
        url = url.lstrip('/')
        if url == '':
            log('Item with empty url: %s' %(item,))
        bits = url.split('#', 1)
        filename = bits[0]
        fragment = (bits[1] if len(bits) == 2 else None)
        item['depth'] = depth
        item["filename"] = filename
        item["fragment"] = fragment
        item["index"] = index
        index += 1
        if 'children' in item:
            index = expand_toc(item['children'], depth + 1, index)
    return index

def _serialise(rtoc, stoc, depth):
    for item in rtoc:
        url = item['url'].lstrip('/')
        bits = url.split('#', 1)
        filename = bits[0]
        fragment = (bits[1] if len(bits) == 2 else None)
        stoc.append({"depth": depth,
                     "title": item['title'],
                     "url": url,
                     "filename": filename,
                     "fragment": fragment,
                     "type": item['type']
                     })
        if 'children' in item:
            _serialise(item['children'], stoc, depth + 1)


def serialise_toc(rtoc):
    """Take the recursive TOC structure and turn it into a list of
    serial points.  Reformat some things for convenience."""
    stoc = []
    _serialise(rtoc, stoc, 1)
    for i, x in enumerate(stoc):
        x['position'] = i
    return stoc

def filename_toc_map(rtoc):
    tocmap = {}
    #log(rtoc)
    def traverse(toc):
        for point in toc:
            #log(point.keys())
            tocmap.setdefault(point['filename'], []).append(point)
            if 'children' in point:
                traverse(point['children'])
    traverse(rtoc)
    return tocmap

def save_data(fn, data):
    """Save without tripping up on unicode"""
    if isinstance(data, unicode):
        data = data.encode('utf8', 'ignore')
    f = open(fn, 'w')
    f.write(data)
    f.close()


class Book(object):
    page_numbers = 'latin'
    preamble_page_numbers = 'roman'

    def notify_watcher(self, message=None):
        if self.watchers:
            if  message is None:
                #message is the name of the caller
                message = traceback.extract_stack(None, 2)[0][2]
            log("notify_watcher called with '%s'" % message)
            for w in self.watchers:
                w(message)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.notify_watcher(config.FINISHED_MESSAGE)
        self.cleanup()
        #could deal with exceptions here and return true


    def __init__(self, book, server, bookname,
                 page_settings=None, watchers=None, isbn=None,
                 license=config.DEFAULT_LICENSE, title=None,
                 max_age=0):
        log("*** Starting new book %s ***" % bookname)
        self.watchers = set()
        if watchers is not None:
            self.watchers.update(watchers)
        self.notify_watcher('start')
        self.bookname = bookname
        self.book = book
        self.server = server
        self.cookie = ''.join(random.sample(ascii_letters, 10))
        try:
            blob, self.bookizip_file = fetch_zip(server, book, save=True, max_age=max_age)
        except HTTPError, e:
            traceback.print_exc()
            self.notify_watcher("ERROR:\n Couldn't get %r\n %s %s" % (e.url, e.code, e.msg))
            #not much to do?
            #raise 502 Bad Gateway ?
            sys.exit()
        f = StringIO(blob)
        self.notify_watcher('fetch_zip')
        self.store = zipfile.ZipFile(f, 'r')
        self.info = json.loads(self.store.read('info.json'))
        for k in ('manifest', 'metadata', 'spine', 'TOC'):
            if k not in self.info:
                raise ObjaviError('info.json of %s lacks vital element "%s"' %
                                  (bookname, k))
            #check types also?

        self.metadata = self.info['metadata']
        self.spine = self.info['spine']
        self.manifest = self.info['manifest']

        if server == config.LOCALHOST: # [DEPRECATED]
            server = get_metadata(self.metadata, 'server', ns=config.FM, default=[server])[0]
            book = get_metadata(self.metadata, 'book', ns=config.FM, default=[book])[0]

        log(pformat(self.metadata))
        self.lang = get_metadata(self.metadata, 'language', default=[None])[0]
        if not self.lang:
            self.lang = guess_lang(server, book)
            log('guessed lang as %s' % self.lang)

        self.toc_header = get_metadata(self.metadata, 'toc_header', ns=config.FM, default=[None])[0]
        if not self.toc_header:
            self.toc_header = config.SERVER_DEFAULTS[server]['toc_header']
        if isinstance(self.toc_header, unicode):
            self.toc_header = self.toc_header.encode('utf-8')

        self.dir = str(get_metadata(self.metadata, 'dir', ns=config.FM, default=[None])[0])
        if not self.dir:
            self.dir = guess_text_dir(server, book)

        #Patch in the extra metadata. (lang and dir may be set from config)
        #these should be read from zip -- so should go into zip?
        for var, key, scheme, ns in (
            (isbn, 'id', 'ISBN', config.DC),
            (license, 'rights', 'License', config.DC),
            (title, 'title', '', config.DC),
            (self.lang, 'language', '', config.DC),
            (self.dir, 'dir', '', config.FM),
            ):
            if var is not None:
                current = get_metadata(self.metadata, key, ns=ns, scheme=scheme)
                log("current values %r, proposed %r" % (current, var))
                if var not in current:
                    add_metadata(self.metadata, key, var, scheme=scheme, ns=ns)

        self.isbn = get_metadata(self.metadata, 'id', scheme='ISBN', default=[None])[0]
        self.license = get_metadata(self.metadata, 'rights', scheme='License', default=[None])[0]

        self.toc = self.info['TOC']
        expand_toc(self.toc)

        self.workdir = tempfile.mkdtemp(prefix=bookname, dir=TMPDIR)
        os.chmod(self.workdir, 0755)

        self.body_html_file = self.filepath('body.html')
        self.body_pdf_file = self.filepath('body.pdf')
        self.preamble_html_file = self.filepath('preamble.html')
        self.preamble_pdf_file = self.filepath('preamble.pdf')
        self.tail_html_file = self.filepath('tail.html')
        self.tail_pdf_file = self.filepath('tail.pdf')
        self.isbn_pdf_file = None
        self.pdf_file = self.filepath('final.pdf')
        self.body_odt_file = self.filepath('body.odt')
        self.outline_file = self.filepath('outline.txt')

        self.publish_file = os.path.abspath(os.path.join(config.PUBLISH_DIR, bookname))

        if page_settings is not None:
            self.maker = PageSettings(**page_settings)

        if title is not None:
            self.title = title
        else:
            titles = get_metadata(self.metadata, 'title')
            if titles:
                self.title = titles[0]
            else:
                self.title = 'A Book About ' + self.book
        if isinstance(self.title, unicode):
            self.title = self.title.encode('utf-8')

        self.notify_watcher()


    if config.TRY_BOOK_CLEANUP_ON_DEL:
        #Dont even define __del__ if it is not used.
        _try_cleanup_on_del = True
        def __del__(self):
            if self._try_cleanup_on_del and os.path.exists(self.workdir):
                self._try_cleanup_on_del = False #or else you can get in bad cycles
                self.cleanup()

    def get_tree_by_id(self, id):
        """get an HTML tree from the given manifest ID"""
        name = self.manifest[id]['url']
        mimetype = self.manifest[id]['mimetype']
        s = self.store.read(name)
        f = StringIO(s)
        if mimetype == 'text/html':
            if s == '':
                log('html ID %r is empty! Not parsing' % (id,))
                tree = empty_html_tree()
            else:
                try:
                    tree = lxml.html.parse(f, parser=utf8_html_parser)
                except etree.XMLSyntaxError, e:
                    log('Could not parse html ID %r, filename %r, string %r... exception %s' %
                        (id, name, s[:20], e))
                    tree = empty_html_tree()
        elif 'xml' in mimetype: #XXX or is this just asking for trouble?
            tree = etree.parse(f)
        else:
            tree = f.read()
        f.close()
        return tree

    def filepath(self, fn):
        return os.path.join(self.workdir, fn)

    def save_tempfile(self, fn, data):
        """Save the data in a temporary directory that will be cleaned
        up when all is done.  Return the absolute file path."""
        fn = self.filepath(fn)
        save_data(fn, data)
        return fn

    def make_oo_doc(self):
        """Make an openoffice document, using the html2odt script."""
        self.wait_for_xvfb()
        html_text = etree.tostring(self.tree, method="html", encoding="UTF-8")
        save_data(self.body_html_file, html_text)
        run([config.HTML2ODT, self.workdir, self.body_html_file, self.body_odt_file])
        log("Publishing %r as %r" % (self.body_odt_file, self.publish_file))
        os.rename(self.body_odt_file, self.publish_file)
        self.notify_watcher()

    def extract_pdf_outline(self):
        """Get the outline (table of contents) for the PDF, which
        wkhtmltopdf should have written to a file.  If that file
        doesn't exist (or config says not to use it), fall back to
        using self._extract_pdf_outline_the_old_way, below.
        """
        number_of_pages = None
        if config.USE_DUMP_OUTLINE:
            try:
                self.outline_contents = parse_extracted_outline(self.outline_file)
            except Exception, e:
                traceback.print_exc()
                number_of_pages = self._extract_pdf_outline_the_old_way()
        else:
            number_of_pages = self._extract_pdf_outline_the_old_way()

        if number_of_pages is None:
            number_of_pages = count_pdf_pages(self.body_pdf_file)

        self.notify_watcher()
        return number_of_pages

    def _extract_pdf_outline_the_old_way(self):
        """Try to get the PDF outline using pdftk.  This doesn't work
        well with all scripts."""
        debugf = self.filepath('extracted-outline.txt')
        self.outline_contents, number_of_pages = \
                parse_outline(self.body_pdf_file, 1, debugf)

        if not self.outline_contents:
            #probably problems with international text. need a horrible hack
            log('no outline: trying again with ascii headings')
            import copy
            tree = copy.deepcopy(self.tree)
            titlemap = {}
            for tag in ('h1', 'h2', 'h3', 'h4'):
                for i, e in enumerate(tree.getiterator(tag)):
                    key = "%s_%s" % (tag, i)
                    titlemap[key] = e.text_content().strip(config.WHITESPACE_AND_NULL)
                    del e[:]
                    if tag == 'h1':
                        e = lxml.etree.SubElement(e, "strong", Class="initial")
                    e.text = key
                    log("key: %r, text: %r, value: %r" %(key, e.text, titlemap[key]))

            ascii_html_file = self.filepath('body-ascii-headings.html')
            ascii_pdf_file = self.filepath('body-ascii-headings.pdf')
            html_text = lxml.etree.tostring(tree, method="html", encoding="UTF-8")
            save_data(ascii_html_file, html_text)
            self.maker.make_raw_pdf(ascii_html_file, ascii_pdf_file, outline=True)
            debugf = self.filepath('ascii-extracted-outline.txt')
            ascii_contents, number_of_ascii_pages = \
                parse_outline(ascii_pdf_file, 1, debugf)
            self.outline_contents = []
            log ("number of pages: %s, post ascii: %s" %
                 (number_of_pages, number_of_ascii_pages))
            for ascii_title, depth, pageno in ascii_contents:
                if ascii_title[-4:] == '&#0;': #stupid [something] puts this in
                    ascii_title = ascii_title[:-4]
                if ' ' in ascii_title:
                    ascii_title = ascii_title.rsplit(' ', 1)[1]
                title = titlemap.get(ascii_title, '')
                log((ascii_title, title, depth, pageno))

                self.outline_contents.append((title, depth, pageno))

        return number_of_pages

    def make_body_pdf(self):
        """Make a pdf of the HTML, using webkit"""
        #1. Save the html
        html_text = etree.tostring(self.tree, method="html", encoding="UTF-8")
        save_data(self.body_html_file, html_text)

        #2. Make a pdf of it
        self.maker.make_raw_pdf(self.body_html_file, self.body_pdf_file, outline=True, outline_file=self.outline_file)
        self.notify_watcher('generate_pdf')

        n_pages = self.extract_pdf_outline()

        log ("found %s pages in pdf" % n_pages)
        #4. resize pages, shift gutters, even pages
        self.maker.reshape_pdf(self.body_pdf_file, self.dir, centre_end=True)
        self.notify_watcher('reshape_pdf')

        #5 add page numbers
        self.maker.number_pdf(self.body_pdf_file, n_pages, dir=self.dir,
                              numbers=self.page_numbers)
        self.notify_watcher("number_pdf")
        self.notify_watcher()

    def make_preamble_pdf(self):
        contents = self.make_contents()
        inside_cover_html = self.compose_inside_cover()
        log_types(self.dir, self.css_url, self.title, inside_cover_html,
                  self.toc_header, contents, self.title)

        html = ('<html dir="%s"><head>\n'
                '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'
                '<link rel="stylesheet" href="%s" />\n'
                '</head>\n<body>\n'
                '<h1 class="frontpage">%s</h1>'
                '%s\n'
                '<div class="contents"><h1>%s</h1>\n%s</div>\n'
                '<div style="page-break-after: always; color:#fff" class="unseen">.'
                '<!--%s--></div></body></html>'
                ) % (self.dir, self.css_url, self.title, inside_cover_html,
                     self.toc_header, contents, self.title)
        save_data(self.preamble_html_file, html)

        self.maker.make_raw_pdf(self.preamble_html_file, self.preamble_pdf_file)

        self.maker.reshape_pdf(self.preamble_pdf_file, self.dir, centre_start=True)

        self.maker.number_pdf(self.preamble_pdf_file, None, dir=self.dir,
                            numbers=self.preamble_page_numbers,
                            number_start=-2)

        self.notify_watcher()

    def make_end_matter_pdf(self):
        """Make an inside back cover and a back cover.  If there is an
        isbn number its barcode will be put on the back cover."""
        if self.isbn:
            self.isbn_pdf_file = self.filepath('isbn.pdf')
            self.maker.make_barcode_pdf(self.isbn, self.isbn_pdf_file)
            self.notify_watcher('make_barcode_pdf')

        end_matter = self.compose_end_matter()
        #log(end_matter)
        save_data(self.tail_html_file, end_matter.decode('utf-8'))
        self.maker.make_raw_pdf(self.tail_html_file, self.tail_pdf_file)

        self.maker.reshape_pdf(self.tail_pdf_file, self.dir, centre_start=True,
                               centre_end=True, even_pages=False)
        self.notify_watcher()

    def make_book_pdf(self):
        """A convenient wrapper of a few necessary steps"""
        # now the Xvfb server is needed. make sure it has had long enough to get going
        self.wait_for_xvfb()
        self.make_body_pdf()
        self.make_preamble_pdf()
        self.make_end_matter_pdf()

        concat_pdfs(self.pdf_file, self.preamble_pdf_file,
                    self.body_pdf_file, self.tail_pdf_file,
                    self.isbn_pdf_file)

        self.notify_watcher('concatenated_pdfs')

    def make_templated_html(self, template=None, zip=False, index=config.TEMPLATING_INDEX_FIRST):
        """Make a templated html version of the book."""
        #set up the directory and static files
        self.unpack_static()
        destdir = self.filepath(os.path.basename(self.publish_file))
        os.mkdir(destdir)
        os.rename(self.filepath('static'), os.path.join(destdir, 'static'))

        if not template:
            template_tree = lxml.html.parse(config.TEMPLATING_DEFAULT_TEMPLATE, parser=utf8_html_parser).getroot()
        else:
            template_tree = lxml.html.document_fromstring(template)

        tocmap = filename_toc_map(self.toc)
        contents_name, first_name = config.TEMPLATING_INDEX_MODES[index]

        #build a contents page and a contents menu
        #We can't make this in the same pass because the menu needs to
        #go in every page (i.e., into the template)
        menu = etree.Element('ul', Class=config.TEMPLATING_MENU_ELEMENT)
        contents = etree.Element('div', Class=config.TEMPLATING_REPLACED_ELEMENT)

        booktitle = etree.Element('div', Class=config.TEMPLATING_BOOK_TITLE_ELEMENT)
        log(self.title)
        booktitle.text = self.title.decode('utf-8')

        etree.SubElement(contents, 'h1').text = self.title.decode('utf-8')

        savename = first_name
        for ID in self.spine:
            filename = self.manifest[ID]['url']
            #handle any TOC points in this file.
            for point in tocmap[filename]:
                if point['type'] == 'booki-section':
                    etree.SubElement(contents, 'h2').text = point['title']
                    etree.SubElement(menu, 'li', Class='booki-section').text = point['title']
                else:
                    if savename is None:
                        savename = filename
                    div = etree.SubElement(contents, 'div')
                    etree.SubElement(div, 'a', href=savename).text = point['title']
                    li = etree.SubElement(menu, 'li')
                    li.tail = '\n'
                    etree.SubElement(li, 'a', href=savename).text = point['title']
                    savename = None
        #put the menu and book title into the template (if it wants it)
        for e in template_tree.iterdescendants(config.TEMPLATING_MENU_ELEMENT):
            e.getparent().replace(e, copy.deepcopy(menu))
        for e in template_tree.iterdescendants(config.TEMPLATING_BOOK_TITLE_ELEMENT):
            e.getparent().replace(e, copy.deepcopy(booktitle))

        #function to template content and write to disk
        def save_content(content, title, filename):
            if not isinstance(title, unicode):
                title = title.decode('utf-8')
            content.set('id', config.TEMPLATING_CONTENTS_ID)
            content.tag = 'div'
            dest = copy.deepcopy(template_tree)
            dest.set('dir', self.dir)
            for e in dest.iterdescendants(config.TEMPLATING_REPLACED_ELEMENT):
                #copy only if there are more than 2
                if content.getparent() is not None:
                    content = copy.deepcopy(content)
                e.getparent().replace(e, content)

            chaptertitle = etree.Element('div', Class=config.TEMPLATING_CHAPTER_TITLE_ELEMENT)
            chaptertitle.text = title
            for e in template_tree.iterdescendants(config.TEMPLATING_CHAPTER_TITLE_ELEMENT):
                e.getparent().replace(e, copy.deepcopy(chaptertitle))
            for e in dest.iterdescendants('title'):
                #log(type(title), title)
                e.text = title
            self.save_tempfile(os.path.join(destdir, filename), lxml.html.tostring(dest, encoding="UTF-8"))


        #write the contents to a file. (either index.html or contents.html)
        save_content(contents, self.title, contents_name)

        savename = first_name
        #and now write each chapter to a file
        for ID in self.spine:
            filename = self.manifest[ID]['url']
            try:
                root = self.get_tree_by_id(ID).getroot()
                body = root.find('body')
            except Exception, e:
                log("hit %s when trying book.get_tree_by_id(%s).getroot().find('body')" % (e, ID))
                body = etree.Element('body')

            #handle any TOC points in this file.  There should only be one!
            for point in tocmap[filename]:
                if point['type'] != 'booki-section':
                    title = point['title']
                    break
            else:
                title = self.title

            if savename is None:
                savename = filename
            save_content(body, title, savename)
            savename = None
        if config.TAR_TEMPLATED_HTML:
            tarname = self.filepath('html.tar.gz')
            workdir, tardir = os.path.split(destdir)
            #workdir == self.workdir, and tardir <Book>-<date>.tar.gz
            run(['tar', 'czf', tarname, '-C', workdir, tardir])
            os.rename(tarname, self.publish_file + '.tar.gz')
        log(destdir, self.publish_file)
        os.rename(destdir, self.publish_file)
        self.notify_watcher()


    def make_simple_pdf(self, mode):
        """Make a simple pdf document without contents or separate
        title page.  This is used for multicolumn newspapers and for
        web-destined pdfs."""
        self.wait_for_xvfb()
        #0. Add heading to begining of html
        body = list(self.tree.cssselect('body'))[0]
        e = body.makeelement('h1', {'id': 'book-title'})
        e.text = self.title.decode('utf-8')
        body.insert(0, e)
        intro = lxml.html.fragment_fromstring(self.compose_inside_cover())
        e.addnext(intro)

        #0.5 adjust parameters to suit the particular kind of output
        if mode == 'web':
            self.maker.gutter = 0

        #1. Save the html
        html_text = etree.tostring(self.tree, method="html", encoding="UTF-8")
        save_data(self.body_html_file, html_text)

        #2. Make a pdf of it (direct to to final pdf)
        self.maker.make_raw_pdf(self.body_html_file, self.pdf_file, outline=True, outline_file=self.outline_file)
        self.notify_watcher('generate_pdf')
        n_pages = count_pdf_pages(self.pdf_file)

        if mode != 'web':
            #3. resize pages and shift gutters.
            self.maker.reshape_pdf(self.pdf_file, self.dir, centre_end=True)
            self.notify_watcher('reshape_pdf')

            #4. add page numbers
            self.maker.number_pdf(self.pdf_file, n_pages,
                                  dir=self.dir, numbers=self.page_numbers)
            self.notify_watcher("number_pdf")
        self.notify_watcher()


    def rotate180(self):
        """Rotate the pdf 180 degrees so an RTL book can print on LTR
        presses."""
        rotated = self.filepath('final-rotate.pdf')
        unrotated = self.filepath('final-pre-rotate.pdf')
        #leave the unrotated pdf intact at first, in case of error.
        rotate_pdf(self.pdf_file, rotated)
        os.rename(self.pdf_file, unrotated)
        os.rename(rotated, self.pdf_file)
        self.notify_watcher()

    def publish_pdf(self):
        """Move the finished PDF to its final resting place"""
        log("Publishing %r as %r" % (self.pdf_file, self.publish_file))
        os.rename(self.pdf_file, self.publish_file)
        self.notify_watcher()

    def publish_bookizip(self):
        """Publish the bookizip.  For this, copy rather than move,
        because the bookizip might be used by further processing.  If
        possible, a hard link is created."""
        log("Publishing %r as %r" % (self.bookizip_file, self.publish_file))
        try:
            run(['cp', '-l', self.bookizip_file, self.publish_file])
        except OSError:
            run(['cp', self.bookizip_file, self.publish_file])
        self.notify_watcher()

    def concat_html(self):
        """Join all the chapters together into one tree.  Keep the TOC
        up-to-date along the way."""

        #each manifest item looks like:
        #{'contributors': []
        #'license': [],
        #'mimetype': '',
        #'rightsholders': []
        #'url': ''}
        doc = lxml.html.document_fromstring('<html dir="%s"><body dir="%s"></body></html>'
                                            % (self.dir, self.dir))
        tocmap = filename_toc_map(self.toc)
        for ID in self.spine:
            details = self.manifest[ID]
            #log(ID, pformat(details))
            # ACO MIJENJAO
            try:
                root = self.get_tree_by_id(ID).getroot()
            except Exception, e:
                log("hit %s when trying book.get_tree_by_id(%s).getroot()" % (e, ID))
                continue
            #handle any TOC points in this file
            for point in tocmap[details['url']]:
                #if the url has a #identifier, use it. Otherwise, make
                #one up, using a hidden element at the beginning of
                #the inserted document.
                #XXX this will break if different files use the same ids
                #XXX should either replace all, or replace selectively.
                if point['fragment']:
                    fragment = point['fragment']
                else:
                    body = _find_tag(root, 'body')
                    fragment = '%s_%s' % (self.cookie, point['index'])
                    #reuse first tag if it is suitable.
                    if (len(body) and
                        body[0].tag in ('h1', 'h2', 'h3', 'h4', 'p', 'div')):
                        first = body[0]
                        while (first.tag == 'div' and
                               len(first) and
                               first[0].tag in ('h1', 'h2', 'h3', 'h4', 'p', 'div')):
                            #descend into nested divs, looking for the real beginning
                            first = first[0]

                        if first.get('id') is None:
                            first.set('id', fragment)
                        else:
                            fragment = first.get('id')
                        #the chapter starts with a heading. that heading should be the chapter name.
                        if first.tag in ('h1', 'h2', 'h3'):
                            #log('chapter has title "%s", found html title "%s"' %
                            #    (point['title'], body[0].text_content()))
                            point['html_title'] = first.text_content()
                    else:
                        marker = body.makeelement('div', style="display:none",
                                                  id=fragment)
                        body.insert(0, marker)
                point['html_id'] = fragment

            add_guts(root, doc)
        return doc

    def unpack_static(self):
        """Extract static files from the zip for the html to refer to."""
        static_files = [x['url'] for x in self.manifest.values()
                        if x['url'].startswith('static')]
        if static_files:
            os.mkdir(self.filepath('static'))

        for name in static_files:
            s = self.store.read(name)
            f = open(self.filepath(name), 'w')
            f.write(s)
            f.close()
        self.notify_watcher()

    def load_book(self):
        """"""
        #XXX concatenate the HTML to match how TWiki version worked.
        # This is perhaps foolishly early -- throwing away useful boundaries.
        self.unpack_static()
        self.tree = self.concat_html()
        self.save_tempfile('raw.html', etree.tostring(self.tree, method='html'))

        self.headings = [x for x in self.tree.iter('h1')]
        if self.headings:
            self.headings[0].set('class', "first-heading")
        for h1 in self.headings:
            h1.title = h1.text_content().strip()
        self.notify_watcher()

    def make_contents(self):
        """Generate HTML containing the table of contents.  This can
        only be done after the main PDF has been made, because the
        page numbers are contained in the PDF outline."""
        header = '<table class="toc">\n'
        row_tmpl = ('<tr><td class="chapter">%s</td><td class="title">%s</td>'
                    '<td class="pagenumber">%s</td></tr>\n')
        empty_section_tmpl = ('<tr><td class="empty-section" colspan="3">%s</td></tr>\n')
        section_tmpl = ('<tr><td class="section" colspan="3">%s</td></tr>\n')
        footer = '\n</table>'

        contents = []

        chapter = 1
        page_num = 1
        #log(self.outline_contents)
        outline_contents = iter(self.outline_contents)

        for section in self.toc:
            if not section.get('children'):
                contents.append(empty_section_tmpl % section['title'])
                continue
            contents.append(section_tmpl % section['title'])

            for point in section['children']:
                try:
                    level = 99
                    while level > 1:
                        h1_text, level, page_num = outline_contents.next()
                except StopIteration:
                    log("contents data not found for %s. Stopping" % (point,))
                    break
                contents.append(row_tmpl % (chapter, _get_best_title(point), page_num))
                chapter += 1

        doc = header + '\n'.join(contents) + footer
        if isinstance(doc, unicode):
            doc = doc.encode('utf-8')
        self.notify_watcher()
        return doc

    def add_section_titles(self):
        """Add any section heading pages that the TOC.txt file
        specifies.  These are sub-book, super-chapter groupings.

        Also add initial numbers to chapters.
        """
        chapter = 1
        section = None
        #log(self.toc)
        for t in self.toc:
            #only top level sections get a subsection page,
            #and only if they have children.
            if t.get('children'):
                section = self.tree.makeelement('div', Class="objavi-subsection")
                heading = etree.SubElement(section, 'div', Class="objavi-subsection-heading")
                heading.text = t['title']
                for child in t['children']:
                    item = etree.SubElement(section, 'div', Class="objavi-chapter")
                    if 'html_title' in child:
                        item.text = child['html_title']
                        heading = self.tree.cssselect('#'+ child['html_id'])
                        if heading:
                            _add_initial_number(heading[0], chapter)
                    else:
                        item.text = child['title']
                    _add_initial_number(item, chapter)
                    log(item.text, debug='HTMLGEN')
                    chapter += 1
                log("#%s is %s" % (t['html_id'], self.tree.cssselect('#'+ t['html_id'])))
                location = self.tree.cssselect('#'+ t['html_id'])[0]
                location.addprevious(section)


        self.notify_watcher()


    def add_css(self, css=None, mode='book'):
        """If css looks like a url, use it as a stylesheet link.
        Otherwise it is the CSS itself, which is saved to a temporary file
        and linked to."""
        log("css is %r" % css)
        htmltree = self.tree
        if css is None or not css.strip():
            css_default = config.SERVER_DEFAULTS[self.server]['css-%s' % mode]
            if css_default is None:
                #guess from language -- this should come first
                css_modes = config.LANGUAGE_CSS.get(self.lang,
                                                    config.LANGUAGE_CSS['en'])
                css_default = css_modes.get(mode, css_modes[None])
            url = css_default
        elif not re.match(r'^http://\S+$', css):
            url = path2url(self.save_tempfile('objavi.css', css), full=True)
        else:
            url = css

        #find the head -- it's probably first child but lets not assume.
        for child in htmltree:
            if child.tag == 'head':
                head = child
                break
        else:
            head = htmltree.makeelement('head')
            htmltree.insert(0, head)

        link = etree.SubElement(head, 'link', rel='stylesheet', type='text/css', href=url)
        self.css_url = url
        self.notify_watcher()
        return url


    def _read_localised_template(self, template, fallbacks=['en']):
        """Try to get the template in the approriate language, otherwise in english."""
        for lang in [self.lang] + fallbacks:
            try:
                fn = template % (lang)
                f = open(fn)
                break
            except IOError, e:
                log("couldn't open inside front cover for lang %s (filename %s)" % (lang, fn))
                log(e)
        template = f.read()
        f.close()
        return template

    def compose_inside_cover(self):
        """create the markup for the preamble inside cover."""
        template = self._read_localised_template(config.INSIDE_FRONT_COVER_TEMPLATE)

        if self.isbn:
            isbn_text = '<b>ISBN :</b> %s <br>' % self.isbn
        else:
            isbn_text = ''

        return template % {'date': time.strftime('%Y-%m-%d'),
                           'isbn': isbn_text,
                           'license': self.license,
                           }


    def compose_end_matter(self):
        """create the markup for the end_matter inside cover.  If
        self.isbn is not set, the html will result in a pdf that
        spills onto two pages.
        """
        template = self._read_localised_template(config.END_MATTER_TEMPLATE)

        d = {'css_url': self.css_url,
             'title': self.title
             }

        if self.isbn:
            d['inside_cover_style'] = ''
        else:
            d['inside_cover_style'] = 'page-break-after: always'

        return template % d


    def make_epub(self, use_cache=False):
        """Make an epub version of the book, using Mike McCabe's
        epub module for the Internet Archive."""
        ebook = ia_epub.Book(self.publish_file, content_dir='')
        def add_file(ID, filename, mediatype, content):
            ebook.add_content({'media-type': mediatype.encode('utf-8'),
                               'id': ID.encode('utf-8'),
                               'href': filename.encode('utf-8'),
                               }, content)

        toc = self.info['TOC']

        #manifest
        filemap = {} #map html to corresponding xhtml
        spinemap = {} #map IDs to multi-file chapters
        for ID in self.manifest:
            details = self.manifest[ID]
            #log(ID, pformat(details))
            fn, mediatype = details['url'], details['mimetype']
            content = self.store.read(fn)
            if mediatype == 'text/html':
                #convert to application/xhtml+xml, and perhaps split
                c = EpubChapter(self.server, self.book, ID, content,
                                use_cache=use_cache)
                c.remove_bad_tags()
                if fn[-5:] == '.html':
                    fnbase = fn[:-5]
                else:
                    fnbase = fn
                fnx = fnbase + '.xhtml'
                mediatype = 'application/xhtml+xml'

                fragments = split_html(c.as_xhtml(),
                                       compressed_size=self.store.getinfo(fn).compress_size)

                #add the first one as if it is the whole thing (as it often is)
                add_file(ID, fnx, mediatype, fragments[0])
                filemap[fn] = fnx
                if len(fragments) > 1:
                    spine_ids = [ID]
                    spinemap[ID] = spine_ids
                    #add any extras
                    for i in range(1, len(fragments)):
                        # XXX it is possible for duplicates if another
                        # file happens to have this name. Ignore for now
                        _id = '%s_SONY_WORKAROUND_%s' % (ID, i)
                        spine_ids.append(_id)
                        add_file(_id,
                                 '%s_SONY_WORKAROUND_%s.xhtml' % (fnbase, i),
                                 mediatype, fragments[i])

            else:
                add_file(ID, fn, mediatype, content)

        #toc
        ncx = epub_utils.make_ncx(toc, self.metadata, filemap)
        ebook.add(ebook.content_dir + 'toc.ncx', ncx)

        #spine
        for ID in self.spine:
            if ID in spinemap:
                for x in spinemap[ID]:
                    ebook.add_spine_item({'idref': x})
            else:
                ebook.add_spine_item({'idref': ID})

        #metadata -- no use of attributes (yet)
        # and fm: metadata disappears for now
        DCNS = config.DCNS
        DC = config.DC
        meta_info_items = []
        log(pformat(self.metadata))
        for ns in [DC]:
            for keyword, schemes in self.metadata[ns].items():
                if ns:
                    keyword = '{%s}%s' % (ns, keyword)
                for scheme, values in schemes.items():
                    for value in values:
                        item = {
                            'item': keyword,
                            'text': value,
                            }
                        if scheme:
                            if keyword in (DCNS + 'creator', DCNS + 'contributor'):
                                item['atts'] = {'role': scheme}
                            else:
                                item['atts'] = {'scheme': scheme}
                        meta_info_items.append(item)

        has_authors = 'creator' in self.metadata[DC]
        if not has_authors and config.CLAIM_UNAUTHORED:
            authors = []
            for x in self.metadata[DC]['creator'].values():
                authors.extend(x)

            meta_info_items.append({'item': DCNS + 'creator',
                                    'text': 'The Contributors'})

            meta_info_items.append({'item': DCNS + 'rights',
                                    'text': 'This book is free. Copyright %s' % (', '.join(authors))}
                                   )
        log(meta_info_items)
        tree_str = ia_epub.make_opf(meta_info_items,
                                    ebook.manifest_items,
                                    ebook.spine_items,
                                    ebook.guide_items,
                                    ebook.cover_id)
        ebook.add(ebook.content_dir + 'content.opf', tree_str)
        ebook.z.close()
        self.notify_watcher()


    def publish_s3(self):
        """Push the book's epub to archive.org, using S3."""
        #XXX why only epub?
        secrets = {}
        for x in ('S3_SECRET', 'S3_ACCESSKEY'):
            fn = getattr(config, x)
            f = open(fn)
            secrets[x] = f.read().strip()
            f.close()

        now = time.strftime('%F')
        s3output = self.filepath('s3-output.txt')
        s3url, detailsurl = find_archive_urls(self.book, self.bookname)
        headers = [
            'x-amz-auto-make-bucket:1',
            "authorization: LOW %(S3_ACCESSKEY)s:%(S3_SECRET)s" % secrets,
            'x-archive-meta-mediatype:texts',
            'x-archive-meta-collection:opensource',
            'x-archive-meta-title:%s' % (self.book,),
            'x-archive-meta-date:%s' % (now,),
            'x-archive-meta-creator:FLOSS Manuals Contributors',
            ]

        if self.license in config.LICENSES:
            headers.append('x-archive-meta-licenseurl:%s' % config.LICENSES[self.license])

        argv = ['curl', '--location', '-s', '-o', s3output]
        for h in headers:
            argv.extend(('--header', h))
        argv.extend(('--upload-file', self.publish_file, s3url,))

        log(' '.join(repr(x) for x in argv))
        check_call(argv, stdout=sys.stderr)
        self.notify_watcher()
        return detailsurl, s3url

    def publish_shared(self, group=None, user=None):
        """Make symlinks from the BOOKI_SHARED_DIRECTORY to the
        published file, so that a virtual host can be set up to
        publish the files from a static location.  If group is set, it
        is used as a subdirectory, otherwise a virtual group like
        'lonely-user-XXX' is used."""
        if group is None:
            if user is None:
                return
            group = config.BOOKI_SHARED_LONELY_USER_PREFIX + user
        group = group.replace('..', '+').replace('/', '+')
        group = re.sub("[^\w%.,-]+", "_", group)[:250]
        groupdir = os.path.join(config.BOOKI_SHARED_DIRECTORY, group)

        generic_name = re.sub(r'-\d{4}\.\d\d\.\d\d\-\d\d\.\d\d\.\d\d', '', self.bookname)
        log(self.bookname, generic_name)

        if not os.path.exists(groupdir):
            os.mkdir(groupdir)

        #change directory, for least symlink confusion
        pwd = os.getcwd()
        os.chdir(groupdir)
        if os.path.exists(generic_name):
            os.unlink(generic_name)
        os.symlink(os.path.abspath(self.publish_file), generic_name)
        os.chdir(pwd)


    def spawn_x(self):
        """Start an Xvfb instance, using a new server number.  A
        reference to it is stored in self.xvfb, which is used to kill
        it when the pdf is done.

        Note that Xvfb doesn't interact well with dbus which is
        present on modern desktops.
        """
        #Find an unused server number (in case two cgis are running at once)
        while True:
            servernum = random.randrange(50, 500)
            if not os.path.exists('/tmp/.X%s-lock' % servernum):
                break

        self.xserver_no = ':%s' % servernum

        authfile = self.filepath('Xauthority')
        os.environ['XAUTHORITY'] = authfile

        #mcookie(1) eats into /dev/random, so avoid that
        from hashlib import md5
        m = md5("%r %r %r %r %r" % (self, os.environ, os.getpid(), time.time(), os.urandom(32)))
        mcookie = m.hexdigest()

        check_call(['xauth', 'add', self.xserver_no, '.', mcookie])

        self.xvfb = Popen(['Xvfb', self.xserver_no,
                           '-screen', '0', '1024x768x24',
                           '-pixdepths', '32',
                           #'-blackpixel', '0',
                           #'-whitepixel', str(2 ** 24 -1),
                           #'+extension', 'Composite',
                           '-dpi', '96',
                           #'-kb',
                           '-nolisten', 'tcp',
                           ])

        # We need to wait a bit before the Xvfb is ready.  but the
        # downloads are so slow that that probably doesn't matter

        self.xvfb_ready_time = time.time() + 2

        os.environ['DISPLAY'] = self.xserver_no
        log(self.xserver_no)

    def wait_for_xvfb(self):
        """wait until a previously set time before continuing.  This
        is so Xvfb has time to properly start."""
        if hasattr(self, 'xvfb'):
            d = self.xvfb_ready_time - time.time()
            if d > 0:
                time.sleep(d)
                self.notify_watcher()

    def cleanup_x(self):
        """Try very hard to kill off Xvfb.  In addition to killing
        this instance's xvfb, occasionally (randomly) search for
        escaped Xvfb instances and kill those too."""
        if not hasattr(self, 'xvfb'):
            return
        check_call(['xauth', 'remove', self.xserver_no])
        p = self.xvfb
        log("trying to kill Xvfb %s" % p.pid)
        try_to_kill(p.pid, 15)
        for i in range(10):
            if p.poll() is not None:
                log("%s died with %s" % (p.pid, p.poll()))
                break
            log("%s not dead yet" % p.pid)
            time.sleep(0.2)
        else:
            log("Xvfb would not die! kill -9! kill -9!")
            try:
                try_to_kill(p.pid, 9)
            except OSError, e:
                log(e)

        if random.random() < 0.1:
            # occasionally kill old xvfbs and soffices, if there are any.
            self.kill_old_processes()

    def kill_old_processes(self):
        """Sometimes, despite everything, Xvfb or soffice instances
        hang around well after they are wanted -- for example if the
        cgi process dies particularly badly. So kill them if they have
        been running for a long time."""
        log("running kill_old_processes")
        killable_names = ' '.join(['Xvfb', 'soffice', 'soffice.bin', 'ooffice',
                                   os.path.basename(config.HTML2ODT),
                                   os.path.basename(config.WKHTMLTOPDF),
                                   ])
        p = Popen(['ps', '-C', killable_names,
                   '-o', 'pid,etime', '--no-headers'], stdout=PIPE)
        data = p.communicate()[0].strip()
        if data:
            lines = data.split('\n')
            pids = []
            for line in lines:
                log('dealing with ps output "%s"' % line)
                try:
                    pid, days, hours, minutes, seconds \
                         = re.match(r'^\s*(\d+)\s+(\d+-)?(\d{2})?:?(\d{2}):(\d+)\s*$', line).groups()
                except AttributeError:
                    log("Couldn't parse that line!")
                # 50 minutes should be enough xvfb time for anyone
                if days or hours or int(minutes) > 50:
                    pid = int(pid)
                    try_to_kill(pid, 15)
                    pids.append(pid)

            time.sleep(1.0)
            for pid in pids:
                #try again in case any are lingerers
                try_to_kill(pid, 9)
        self.notify_watcher()

    def cleanup(self):
        self.cleanup_x()
        if not config.KEEP_TEMP_FILES:
            for fn in os.listdir(self.workdir):
                os.remove(os.path.join(self.workdir, fn))
            os.rmdir(self.workdir)
        else:
            log("NOT removing '%s', containing the following files:" % self.workdir)
            log(*os.listdir(self.workdir))

        self.notify_watcher()


def use_cache():
    return (os.environ.get('HTTP_HOST') in config.USE_ZIP_CACHE_ALWAYS_HOSTS)

def _read_cached_zip(server, book, max_age):
    #find a recent zip if possible
    prefix = '%s/%s' % (config.BOOKI_BOOK_DIR, make_book_name(book, server, '').split('-20', 1)[0])
    from glob import glob
    zips = sorted(glob(prefix + '*.zip'))
    if not zips:
        log("no cached booki-zips matching %s*.zip" % (prefix,))
        return None
    zipname = zips[-1]
    cutoff = time.time() - max_age * 60
    log(repr(zipname))
    try:
        date = time.mktime(time.strptime(zipname, prefix + '-%Y.%m.%d-%H.%M.%S.zip'))
        if date > cutoff:
            f = open(zipname)
            blob = f.read()
            f.close()
            return blob, zipname
        log("%s is too old, must reload" % zipname)
        return None
    except (IOError, IndexError, ValueError), e:
        log('could not make sense of %s: got exception %s' % (zipname, e))
        return None


def fetch_zip(server, book, save=False, max_age=-1, filename=None):
    interface = config.SERVER_DEFAULTS[server].get('interface', 'Booki')
    try:
        url = config.ZIP_URLS[interface] % {'HTTP_HOST': HTTP_HOST,
                                            'server': server, 'book':book}
    except KeyError:
        raise NotImplementedError("Can't handle '%s' interface" % interface)

    if use_cache() and max_age < 0:
        #default to 12 hours cache on objavi.halo.gen.nz
        max_age = 12 * 60

    if max_age:
        log('WARNING: trying to use cached booki-zip',
            'If you are debugging booki-zip creation, you will go CRAZY'
            ' unless you switch this off')
        blob_and_name = _read_cached_zip(server, book, max_age)
        if blob_and_name is not None:
            return blob_and_name

    log('fetching zip from %s'% url)
    f = urlopen(url)
    blob = f.read()
    f.close()
    if save:
        if filename is None:
            filename = '%s/%s' % (config.BOOKI_BOOK_DIR,
                                  make_book_name(book, server, '.zip'))
        f = open(filename, 'w')
        f.write(blob)
        f.close()
    return blob, filename


def split_html(html, compressed_size=None, fix_markup=False):
    """Split long html files into pieces that will work nicely on a
    Sony Reader."""
    if compressed_size is None:
        import zlib
        compressed_size = len(zlib.compress(html))

    splits = max(compressed_size // config.EPUB_COMPRESSED_SIZE_MAX,
                 len(html) // config.EPUB_FILE_SIZE_MAX)
    log("uncompressed: %s, compressed: %s, splits: %s" % (len(html), compressed_size, splits))

    if not splits:
        return [html]

    if fix_markup:
        #remove '<' in attributes etc, which makes the marker
        #insertion more reliable
        html = etree.tostring(lxml.html.fromstring(html),
                              encoding='UTF-8',
                              #method='html'
                              )

    target = len(html) // (splits + 1)
    s = 0
    fragments = []
    for i in range(splits):
        e = html.find('<', target * (i + 1))
        fragments.append(html[s:e])
        fragments.append('<hr class="%s" id="split_%s" />' % (config.MARKER_CLASS_SPLIT, i))
        s = e
    fragments.append(html[s:])

    #XXX somehow try to avoid split in silly places (e.g, before inline elements)
    chapters = split_tree(lxml.html.fromstring(''.join(fragments)))
    return [etree.tostring(c.tree, encoding='UTF-8', method='html') for c in chapters]

