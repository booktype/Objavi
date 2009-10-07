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
from subprocess import Popen, check_call, PIPE
from cStringIO import StringIO
import zipfile
try:
    import simplejson as json
except ImportError:
    import json

import lxml, lxml.html, lxml.etree

from objavi import config, twiki_wrapper, epub_utils
from objavi.cgi_utils import log, run
from objavi.pdf import PageSettings, count_pdf_pages, concat_pdfs, rotate_pdf, parse_outline

from iarchive import epub as ia_epub
from booki.xhtml_utils import EpubChapter

TMPDIR = os.path.abspath(config.TMPDIR)
DOC_ROOT = os.environ.get('DOCUMENT_ROOT', '.')
PUBLISH_PATH = "%s/books/" % DOC_ROOT

def make_book_name(book, server, suffix='.pdf'):
    lang = config.SERVER_DEFAULTS.get(server, config.SERVER_DEFAULTS[config.DEFAULT_SERVER])['lang']
    book = ''.join(x for x in book if x.isalnum())
    return '%s-%s-%s%s' % (book, lang,
                           time.strftime('%Y.%m.%d-%H.%M.%S'),
                           suffix)

def _add_initial_number(e, n):
    """Put a styled chapter number n at the beginning of element e."""
    initial = e.makeelement("strong", Class="initial")
    e.insert(0, initial)
    initial.tail = ' '
    if e.text is not None:
        initial.tail += e.text
    e.text = ''
    initial.text = "%s." % n


class TocItem(object):
    """This makes sense of the tuples from TOC.txt files"""
    def __init__(self, status, chapter, title):
        # status is
        #  0 - section heading with no chapter
        #  1 - chapter heading
        #  2 - book title
        #
        # chapter is twiki name of the chapter
        # title is a human readable name of the chapter.
        self.status = status
        self.chapter = chapter
        self.title = title

    def is_chapter(self):
        return self.status == '1'

    def is_section(self):
        return self.status == '0'

    def is_title(self):
        return self.status == '2'

    def __str__(self):
        return '<toc: %s>' %  ', '.join('%s: %s' % x for x in self.__dict__.iteritems())


class Book(object):
    page_numbers = 'latin'
    preamble_page_numbers = 'roman'

    def notify_watcher(self, message=None):
        if self.watcher:
            if  message is None:
                #message is the name of the caller
                #XXX look at using inspect module
                import traceback
                message = traceback.extract_stack(None, 2)[0][2]
            log("notify_watcher called with '%s'" % message)
            self.watcher(message)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()
        #could deal with exceptions here and return true

    def __init__(self, book, server, bookname,
                 page_settings=None, watcher=None, isbn=None,
                 license=config.DEFAULT_LICENSE):
        log("*** Starting new book %s ***" % bookname)
        self.book = book
        self.server = server
        self.watcher = watcher
        self.isbn = isbn
        self.license = license
        self.workdir = tempfile.mkdtemp(prefix=bookname, dir=TMPDIR)
        os.chmod(self.workdir, 0755)
        defaults = config.SERVER_DEFAULTS[server]
        self.lang = defaults['lang']
        self.dir  = defaults['dir']

        self.body_html_file = self.filepath('body.html')
        self.body_pdf_file = self.filepath('body.pdf')
        self.preamble_html_file = self.filepath('preamble.html')
        self.preamble_pdf_file = self.filepath('preamble.pdf')
        self.tail_html_file = self.filepath('tail.html')
        self.tail_pdf_file = self.filepath('tail.pdf')
        self.isbn_pdf_file = None
        self.pdf_file = self.filepath('final.pdf')
        self.body_odt_file = self.filepath('body.odt')

        self.publish_name = bookname
        self.publish_file = os.path.join(PUBLISH_PATH, self.publish_name)
        self.publish_url = os.path.join(config.PUBLISH_URL, self.publish_name)

        if page_settings is not None:
            self.maker = PageSettings(**page_settings)

        self.notify_watcher()

    if config.TRY_BOOK_CLEANUP_ON_DEL:
        #Dont even define __del__ if it is not used.
        _try_cleanup_on_del = True
        def __del__(self):
            if self._try_cleanup_on_del and os.path.exists(self.workdir):
                self._try_cleanup_on_del = False #or else you can get in bad cycles
                self.cleanup()

    def filepath(self, fn):
        return os.path.join(self.workdir, fn)

    def save_data(self, fn, data):
        """Save without tripping up on unicode"""
        if isinstance(data, unicode):
            data = data.encode('utf8', 'ignore')
        f = open(fn, 'w')
        f.write(data)
        f.close()

    def save_tempfile(self, fn, data):
        """Save the data in a temporary directory that will be cleaned
        up when all is done.  Return the absolute file path."""
        fn = self.filepath(fn)
        self.save_data(fn, data)
        return fn

    def make_oo_doc(self):
        """Make an openoffice document, using the html2odt script."""
        self.wait_for_xvfb()
        html_text = lxml.etree.tostring(self.tree, method="html")
        self.save_data(self.body_html_file, html_text)
        run([config.HTML2ODT, self.workdir, self.body_html_file, self.body_odt_file])
        log("Publishing %r as %r" % (self.body_odt_file, self.publish_file))
        os.rename(self.body_odt_file, self.publish_file)
        self.notify_watcher()

    def extract_pdf_outline(self):
        self.outline_contents, self.outline_text, number_of_pages = parse_outline(self.body_pdf_file, 1)
        for x in self.outline_contents:
            log(x)
        self.notify_watcher()
        return number_of_pages

    def make_body_pdf(self):
        """Make a pdf of the HTML, using webkit"""
        #1. Save the html
        html_text = lxml.etree.tostring(self.tree, method="html")
        self.save_data(self.body_html_file, html_text)

        #2. Make a pdf of it
        self.maker.make_raw_pdf(self.body_html_file, self.body_pdf_file, outline=True)
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
        html = ('<html dir="%s"><head>\n'
                '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'
                '<link rel="stylesheet" href="%s" />\n'
                '</head>\n<body>\n'
                '<h1 class="frontpage">%s</h1>'
                '%s\n'
                '<div class="contents">%s</div>\n'
                '<div style="page-break-after: always; color:#fff" class="unseen">.'
                '<!--%s--></div></body></html>'
                ) % (self.dir, self.css_url, self.title, inside_cover_html,
                     contents, self.title)
        self.save_data(self.preamble_html_file, html)

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

        self.save_data(self.tail_html_file, self.compose_end_matter())
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


    def make_simple_pdf(self, mode):
        """Make a simple pdf document without contents or separate
        title page.  This is used for multicolumn newspapers and for
        web-destined pdfs."""
        self.wait_for_xvfb()
        #0. Add heading to begining of html
        body = list(self.tree.cssselect('body'))[0]
        e = body.makeelement('h1', {'id': 'book-title'})
        e.text = self.title
        body.insert(0, e)
        intro = lxml.html.fragment_fromstring(self.compose_inside_cover())
        e.addnext(intro)

        #0.5 adjust parameters to suit the particular kind of output
        if mode == 'web':
            self.maker.gutter = 0

        #1. Save the html
        html_text = lxml.etree.tostring(self.tree, method="html")
        self.save_data(self.body_html_file, html_text)

        #2. Make a pdf of it (direct to to final pdf)
        self.maker.make_raw_pdf(self.body_html_file, self.pdf_file, outline=True)
        self.notify_watcher('generate_pdf')
        #n_pages = self.extract_pdf_outline()
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

    def get_twiki_metadata(self):
        """Get information about a twiki book (as much as is easy and useful)."""
        if not hasattr(self, 'toc'):
            self.load_toc()

        title_map = {}
        authors = {}
        meta = {
            'language': self.lang,
            'identifier': 'http://%s/epub/%s/%s' %(self.server, self.book, time.strftime('%Y.%m.%d-%H.%M.%S')),
            'publisher': 'FLOSS Manuals http://flossmanuals.net',
            'date': time.strftime('%Y-%m-%d'),
            'fm:server': self.server,
            'fm:book': self.book,
            'title': self.book,
            }
        spine = []
        toc = []
        section = toc
        for t in self.toc:
            if t.is_chapter():
                spine.append(t.chapter)
                section.append((t.title, t.chapter))
                title_map[t.title] = t.chapter
            elif t.is_section():
                section = []
                toc.append([[t.title, None], section])
            elif t.is_title():
                meta['title'] = t.title

        author_copyright, chapter_copyright = twiki_wrapper.get_book_copyright(self.server, self.book, title_map)

        return {
            'metadata': meta,
            'TOC': toc,
            'spine': spine,
            'copyright': author_copyright,
            #'chapter_copyright': chapter_copyright,
        }

    def load_toc(self):
        """From the TOC.txt file create a list of TocItems with
        the attributes <status>, <chapter>, and <title>.

        <status> is a number, with the following meaning:

              0 - section heading with no chapter
              1 - chapter heading
              2 - book title

        The TocItem object has convenience functions <is_chapter> and
        <is_section>.

        <chapter> is twiki name of the chapter.

        <title> is a human readable title for the chapter.  It is likely to
        differ from the title given in the chapter's <h1> heading.
        """
        self.toc = []
        for status, chapter, title in twiki_wrapper.toc_iterator(self.server, self.book):
            self.toc.append(TocItem(status, chapter, title))
        self.notify_watcher()

    def load_book(self):
        """Fetch and parse the raw html of the book.  Links in the
        document will be made absolute."""
        html = twiki_wrapper.get_book_html(self.server, self.book, self.dir)
        self.save_tempfile('raw.html', html)

        self.tree = lxml.html.document_fromstring(html)
        self.tree.make_links_absolute(config.BOOK_URL % (self.server, self.book))
        self.headings = [x for x in self.tree.cssselect('h1')]
        if self.headings:
            self.headings[0].set('class', "first-heading")
        for h1 in self.headings:
            h1.title = h1.text_content().strip()
        self.notify_watcher()

    def load(self):
        """Wrapper around all necessary load methods."""
        self.load_book()
        self.load_toc()

    def make_contents(self):
        """Generate HTML containing the table of contents.  This can
        only be done after the main PDF has been made."""
        header = '<h1>Table of Contents</h1><table class="toc">\n'
        row_tmpl = ('<tr><td class="chapter">%s</td><td class="title">%s</td>'
                    '<td class="pagenumber">%s</td></tr>\n')
        section_tmpl = ('<tr><td class="section" colspan="3">%s</td></tr>\n')
        footer = '\n</table>'

        contents = []

        chapter = 1
        page_num = 1
        subsections = [] # for the subsection heading pages.

        outline_contents = iter(self.outline_contents)
        headings = iter(self.headings)

        for t in self.toc:
            if t.is_chapter():
                try:
                    h1 = headings.next()
                except StopIteration:
                    log("heading not found for %s (previous h1 missing?). Stopping" % t)
                    break
                h1_text, level, page_num = outline_contents.next()
                log("%r %r" % (h1.title, h1_text))
                contents.append(row_tmpl % (chapter, h1.title, page_num))
                chapter += 1
            elif t.is_section():
                contents.append(section_tmpl % t.title)
            else:
                log("mystery TOC item: %s" % t)

        doc = header + '\n'.join(contents) + footer
        self.notify_watcher()
        return doc

    def add_section_titles(self):
        """Add any section heading pages that the TOC.txt file
        specifies.  These are sub-book, super-chapter groupings.

        Also add initial numbers to chapters.
        """
        headings = iter(self.headings)
        chapter = 1
        section = None

        for t in self.toc:
            if t.is_chapter() and section is not None:
                try:
                    h1 = headings.next()
                except StopIteration:
                    log("heading not found for %s (previous h1 missing?)" % t)
                    break
                item = h1.makeelement('div', Class='chapter')
                log(h1.title, debug='HTMLGEN')
                item.text = h1.title
                _add_initial_number(item, chapter)

                section.append(item)

                if not section_placed:
                    log("placing section", debug='HTMLGEN')
                    h1.addprevious(section)
                    section_placed = True
                else:
                    log("NOT placing section", debug='HTMLGEN')

                #put a bold number at the beginning of the h1.
                _add_initial_number(h1, chapter)
                chapter += 1

            elif t.is_section():
                section = self.tree.makeelement('div', Class="subsection")
                # section Element complains when you try to ask it whether it
                # has been placed (though it does know)
                section_placed = False
                heading = lxml.html.fragment_fromstring(t.title, create_parent='div')
                heading.set("Class", "subsection-heading")
                section.append(heading)

        self.notify_watcher()


    def add_css(self, css=None, mode='book'):
        """If css looks like a url, use it as a stylesheet link.
        Otherwise it is the CSS itself, which is saved to a temporary file
        and linked to."""
        log("css is %r" % css)
        htmltree = self.tree
        if css is None or not css.strip():
            defaults = config.SERVER_DEFAULTS[self.server]
            url = 'file://' + os.path.abspath(defaults['css-%s' % mode])
        elif not re.match(r'^http://\S+$', css):
            fn = self.save_tempfile('objavi.css', css)
            url = 'file://' + fn
        else:
            url = css
        #XXX for debugging and perhaps sensible anyway
        #url = url.replace('file:///home/douglas/objavi2', '')


        #find the head -- it's probably first child but lets not assume.
        for child in htmltree:
            if child.tag == 'head':
                head = child
                break
        else:
            head = htmltree.makeelement('head')
            htmltree.insert(0, head)

        link = lxml.etree.SubElement(head, 'link', rel='stylesheet', type='text/css', href=url)
        self.css_url = url
        self.notify_watcher()
        return url

    def set_title(self, title=None):
        """If a string is supplied, it becomes the book's title.
        Otherwise a guess is made."""
        if title:
            self.title = title
        else:
            titles = [x.text_content() for x in self.tree.cssselect('title')]
            if titles and titles[0]:
                self.title = titles[0]
            else:
                #oh well
                self.title = 'A Manual About ' + self.book
        return self.title

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
                           '-kb',
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
        os.kill(p.pid, 15)
        for i in range(10):
            if p.poll() is not None:
                log("%s died with %s" % (p.pid, p.poll()))
                break
            log("%s not dead yet" % p.pid)
            time.sleep(0.2)
        else:
            log("Xvfb would not die! kill -9! kill -9!")
            os.kill(p.pid, 9)

        if random.random() < 0.1:
            # occasionally kill old xvfbs and soffices, if there are any.
            self.kill_old_processes()

    def kill_old_processes(self):
        """Sometimes, despite everything, Xvfb or soffice instances
        hang around well after they are wanted -- for example if the
        cgi process dies particularly badly. So kill them if they have
        been running for a long time."""
        log("running kill_old_processes")
        p = Popen(['ps', '-C' 'Xvfb soffice soffice.bin html2odt ooffice wkhtmltopdf',
                   '-o', 'pid,etime', '--no-headers'], stdout=PIPE)
        data = p.communicate()[0].strip()
        if data:
            lines = data.split('\n')
            for line in lines:
                log('dealing with ps output "%s"' % line)
                try:
                    pid, days, hours, minutes, seconds \
                         = re.match(r'^(\d+)\s+(\d+-)?(\d{2})?:?(\d{2}):(\d+)\s*$', line).groups()
                except AttributeError:
                    log("Couldn't parse that line!")
                # 50 minutes should be enough xvfb time for anyone
                if days or hours or int(minutes) > 50:
                    log("going to kill pid %s" % pid)
                    os.kill(int(pid), 15)
                    time.sleep(0.5)
                    try:
                        os.kill(int(pid), 9)
                        log('killing %s with -9')
                    except OSError, e:
                        pass
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




class ZipBook(Book):
    """A Book based on a booki-zip file.  Depending how out-of-date
    this docstring is, some of the parent's methods will not work.
    """
    def __init__(self, zipstring, **kwargs):
        f = StringIO(zipstring)
        self.store = zipfile.ZipFile(f, 'r')
        self.info = json.loads(self.store.read('info.json'))

        metadata = self.info['metadata']
        book = metadata['fm:book']
        server = metadata['fm:server']
        bookname = make_book_name(book, server)

        Book.__init__(self, book, server, bookname, **kwargs)
        self.set_title(metadata['title'])

    def make_epub(self, use_cache=False):
        """Make an epub version of the book, using Mike McCabe's
        epub module for the Internet Archive."""
        self.epubfile = self.filepath('%s.epub' % self.book)
        ebook = ia_epub.Book(self.epubfile, content_dir='')
        manifest = self.info['manifest']
        metadata = self.info['metadata']
        toc = self.info['TOC']
        spine = self.info['spine']

        #manifest
        filemap = {} #reformualted manifest for NCX
        for ID in manifest:
            fn, mediatype = manifest[ID]
            content = self.store.read(fn)
            if mediatype == 'text/html':
                #convert to application/xhtml+xml
                c = EpubChapter(self.server, self.book, ID, content,
                                use_cache=use_cache)
                c.remove_bad_tags()
                c.prepare_for_epub()
                content = c.as_xhtml()
                fn = fn[:-5] + '.xhtml'
                mediatype = 'application/xhtml+xml'
            if mediatype == 'application/xhtml+xml':
                filemap[ID] = fn

            info = {'id': ID, 'href': fn, 'media-type': mediatype}
            ebook.add_content(info, content)

        #toc
        ncx = epub_utils.make_ncx(toc, metadata, filemap)
        ebook.add(ebook.content_dir + 'toc.ncx', ncx)

        #spine
        for ID in spine:
            ebook.add_spine_item({'idref': ID})

        #metadata -- no use of attributes (yet)
        # and fm: metadata disappears for now
        dcns = config.DCNS
        meta_info_items = []
        for k, v in metadata.iteritems():
            if k.startswith('fm:'):
                continue
            meta_info_items.append({'item': dcns + k,
                                    'text': v}
                                   )

        #copyright
        authors = sorted(self.info['copyright'])
        for a in authors:
            meta_info_items.append({'item': dcns + 'creator',
                                    'text': a}
                                   )
        meta_info_items.append({'item': dcns + 'rights',
                                'text': 'This book is free. Copyright %s' % (', '.join(authors))}
                               )

        tree_str = ia_epub.make_opf(meta_info_items,
                                    ebook.manifest_items,
                                    ebook.spine_items,
                                    ebook.guide_items,
                                    ebook.cover_id)
        ebook.add(ebook.content_dir + 'content.opf', tree_str)
        ebook.z.close()
