# Part of Objavi2, which turns html manuals into books.
# This provides abstractions of texts and virtual printers and manages
# their interactions.
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
from urllib2 import urlopen
from subprocess import Popen, check_call, PIPE

import lxml.etree, lxml.html
import lxml, lxml.html, lxml.etree

import config
from config import SERVER_DEFAULTS, DEFAULT_SERVER, POINT_2_MM, PDFEDIT_MAX_PAGES

TMPDIR = os.path.abspath(config.TMPDIR)
DOC_ROOT = os.environ.get('DOCUMENT_ROOT', '.')
PUBLISH_PATH = "%s/books/" % DOC_ROOT


def log(*messages, **kwargs):
    """Send the messages to the appropriate place (stderr, or syslog).
    If a <debug> keyword is specified, the message is only printed if
    its value ias in the global DEBUG_MODES."""
    if 'debug' not in kwargs or config.DEBUG_ALL or kwargs['debug'] in config.DEBUG_MODES:
        for m in messages:
            try:
                print >> sys.stderr, m
            except Exception:
                print >> sys.stderr, repr(m)

def _add_initial_number(e, n):
    """Put a styled chapter number n at the beginning of element e."""
    initial = e.makeelement("strong", Class="initial")
    e.insert(0, initial)
    initial.tail = ' '
    if e.text is not None:
        initial.tail += e.text
    e.text = ''
    initial.text = "%s." % n

def _add_chapter_cookie(e):
    """add magic hidden text to help with contents generation"""
    cookie = e.makeelement("span", Class="heading-cookie", dir="ltr",
                           style="font-size:6pt; line-height: 6pt; color: #fff; width:0;"
                           " float:left; margin:-2em; z-index: -67; display: block;"
                           )
    cookie.text = ''.join(random.choice(config.CHAPTER_COOKIE_CHARS) for x in range(8))
    e.cookie = cookie.text
    e.addnext(cookie)
    #e.append(cookie)


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

    def __str__(self):
        return '<toc: %s>' %  ', '.join('%s: %s' % x for x in self.__dict__.iteritems())


def run(cmd):
    try:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
    except Exception:
        log("Failed on command: %r" % cmd)
        raise
    log("%s\n%s returned %s and produced\nstdout:%s\nstderr:%s" %
        (' '.join(cmd), cmd[0], p.poll(), out, err))


def find_containing_paper(w, h):
    size = None
    for name, pw, ph in config.PAPER_SIZES:
        if pw >= w and ph >= h:
            mw = (pw - w) * 0.5
            mh = (ph - h) * 0.5
            return (name, mw, mh)

    raise ValueError("page sized %.2fmm x %.2fmm won't fit on any paper!" %
                     (w * POINT_2_MM, h * POINT_2_MM))



class PageSettings(object):
    """Calculates and wraps commands for the generation and processing
    of PDFs"""
    def __init__(self, pointsize, **kwargs):
        # the formulas for default gutters, margins and column margins
        # are quite ad-hoc and certainly improvable.

        self.width, self.height = pointsize
        self.papersize, clipx, clipy = find_containing_paper(self.width, self.height)

        self.gutter = kwargs.get('gutter', (config.BASE_GUTTER +
                                            config.PROPORTIONAL_GUTTER * self.width))

        default_margin = (config.BASE_MARGIN + config.PROPORTIONAL_MARGIN * min(pointsize))
        self.top_margin = kwargs.get('top_margin', default_margin)
        self.side_margin = kwargs.get('top_margin', default_margin)
        self.bottom_margin = kwargs.get('top_margin', default_margin)
        self.moz_printer = kwargs.get('moz_printer', ('objavi_' + self.papersize))
        self.columns = kwargs.get('columns', 1)

        self.column_margin = kwargs.get('column_margin', default_margin * 2 / (4.0 + self.columns))

        self.number_bottom = self.bottom_margin - 0.6 * config.PAGE_NUMBER_SIZE
        self.number_margin = self.side_margin

        # calculate margins in mm for browsers
        self.margins = []
        for m, clip in ((self.top_margin, clipy),
                        (self.side_margin, clipx + 0.5 * self.gutter),
                        (self.bottom_margin, clipy + 0.5 * config.PAGE_NUMBER_SIZE),
                        (self.side_margin, clipx + 0.5 * self.gutter),
                        ):
            if m is None:
                m = default_margin
            self.margins.append((m + clip) * POINT_2_MM)

        for x in locals().iteritems():
            log("%s: %s" % x, debug='PDFGEN')
        for x in dir(self):
            log("%s: %s" % (x, getattr(self, x)), debug='PDFGEN')



    def _webkit_command(self, html, pdf):
        m = [str(x) for x in self.margins]
        cmd = [config.WKHTMLTOPDF, '-q', '-s', self.papersize,
               '-T', m[0], '-R', m[1], '-B', m[2], '-L', m[3],
               ] + config.WKHTMLTOPDF_EXTRA_COMMANDS + [
               html, pdf]
        log(' '.join(cmd))
        return cmd

    def _gecko_command(self, html, pdf):
        m = [str(x) for x in self.margins]
        #firefox -P pdfprint -print URL -printprinter "printer_settings"
        cmd = [FIREFOX, '-P', 'pdfprint', '-print',
               html, '-printprinter', self.moz_printer]
        log(' '.join(cmd))
        return cmd

    def make_raw_pdf(self, html, pdf, engine='webkit'):
        func = getattr(self, '_%s_command' % engine)
        if self.columns == 1:
            cmd = func(html, pdf)
            run(cmd)
        else:
            printable_width = self.width - 2.0 * self.side_margin - self.gutter
            column_width = (printable_width - (self.columns - 1) * self.column_margin) / self.columns
            page_width = column_width + self.column_margin

            columnmaker = PageSettings((page_width, self.height), moz_printer=self.moz_printer,
                                       gutter=0, top_margin=self.top_margin,
                                       side_margin=self.column_margin * 0.5,
                                       bottom_margin=self.bottom_margin)

            column_pdf = pdf[:-4] + '-single-column.pdf'
            columnmaker.make_raw_pdf(html, column_pdf, engine=engine)
            columnmaker.reshape_pdf(column_pdf)

            cmd = ['pdfnup',
                   '--nup', '%sx1' % int(self.columns),
                   '--paper', self.papersize.lower() + 'paper',
                   '--outfile', pdf,
                   '--offset', '0 0', #'%scm 0' % (self.margins[1] * 0.1),
                   '--noautoscale', 'true',
                   '--orient', 'portrait',
                   #'--tidy', 'false',
                   column_pdf
                   ]
            run(cmd)



    def reshape_pdf(self, pdf, dir='LTR', centre_start=False, centre_end=False,
                    even_pages=True):
        """Spin the pdf for RTL text, resize it to the right size, and
        shift the gutter left and right"""
        ops = 'resize'
        if self.gutter:
            ops += ',shift'
        if even_pages:
            ops += ',even_pages'
        gutter = self.gutter
        if dir == 'RTL':
            gutter = -gutter
        cmd = ['pdfedit', '-s', 'wk_objavi.qs',
               'dir=%s' % dir,
               'filename=%s' % pdf,
               'output_filename=%s' % pdf,
               'operation=%s' % ops,
               'width=%s' % self.width,
               'height=%s' % self.height,
               'offset=%s' % gutter,
               'centre_start=%s' % centre_start,
               'centre_end=%s' % centre_end,
               ]
        run(cmd)

    def _number_pdf(self, pdf, numbers='latin', dir='LTR',
                    number_start=1):
        cmd = ['pdfedit', '-s', 'wk_objavi.qs',
               'operation=page_numbers',
               'dir=%s' % dir,
               'filename=%s' % pdf,
               'output_filename=%s' % pdf,
               'number_start=%s' % number_start,
               'number_style=%s' % numbers,
               'number_bottom=%s' % self.number_bottom,
               'number_margin=%s' % self.number_margin,
               ]
        run(cmd)

    def number_pdf(self, pdf, pages, **kwargs):
        # if there are too many pages for pdfedit to handle in one go,
        # split the job into bits.  <pages> may not be exact
        if pages is None or pages <= PDFEDIT_MAX_PAGES:
            self._number_pdf(pdf, **kwargs)
        else:
            # section_size must be even
            sections = pages // PDFEDIT_MAX_PAGES + 1
            section_size = (pages // sections + 2) & ~1

            pdf_sections = []
            s = kwargs.pop('number_start', 1)
            while s < pages:
                e = s + section_size - 1
                pdf_section = '%s-%s-%s.pdf' % (pdf[:-4], s, e)
                if e < pages - 1:
                    page_range = '%s-%s' % (s, e)
                else:
                    page_range = '%s-end' % s
                run(['pdftk',
                     pdf,
                     'cat',
                     page_range,
                     'output',
                     pdf_section,
                     ])
                self._number_pdf(pdf_section, number_start=s, **kwargs)
                pdf_sections.append(pdf_section)
                s = e + 1

            concat_pdfs(pdf, *pdf_sections)



def concat_pdfs(name, *args):
    """Join all the named pdfs together into one and save it as <name>"""
    cmd = ['pdftk']
    cmd.extend(args)
    cmd += ['cat', 'output', name]
    run(cmd)

def index_pdf(pdf, text=None):
    """Use pdftotext to extract utf-8 text from a pdf, using ^L to
    separate pages."""
    if text is None:
        text = pdf + '.index.txt'
    cmd = ['pdftotext',
           #'-layout', #keeps more original formatting
           pdf,
           text]
    run(cmd)
    return text

def rotate_pdf(pdfin, pdfout):
    """Turn the PDF on its head"""
    cmd = ['pdftk', pdfin,
           'cat',
           '1-endD',
           'output',
           pdfout
           ]
    run(cmd)


class Book(object):
    page_numbers = 'latin'
    preamble_page_numbers = 'roman'
    engine= 'webkit'
    _try_cleanup_on_del = True

    def notify_watcher(self, message=None):
        if self.watcher:
            if  message is None:
                #message is the name of the caller
                #XXX look at using inspect module
                import traceback
                message = traceback.extract_stack(None, 2)[0][2]
                log("notify_watcher called by '%s'" % message)
            self.watcher(message)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()
        #could deal with exceptions here and return true

    def __init__(self, book, server, bookname,
                 page_settings=None, engine=None, watcher=None):
        log("*** Starting new book %s ***" % bookname)
        self.book = book
        self.server = server
        self.watcher = watcher
        self.workdir = tempfile.mkdtemp(prefix=bookname, dir=TMPDIR)
        os.chmod(self.workdir, 0755)
        defaults = SERVER_DEFAULTS.get(server, SERVER_DEFAULTS[DEFAULT_SERVER])
        self.default_css = defaults['css']
        self.lang = defaults['lang']
        self.dir  = defaults['dir']

        self.body_html_file = self.filepath('body.html')
        self.body_pdf_file = self.filepath('body.pdf')
        self.body_index_file = self.filepath('body.txt')
        self.preamble_html_file = self.filepath('preamble.html')
        self.preamble_pdf_file = self.filepath('preamble.pdf')
        self.pdf_file = self.filepath('final.pdf')

        self.publish_name = bookname
        self.publish_file = os.path.join(PUBLISH_PATH, self.publish_name)
        self.publish_url = os.path.join(config.PUBLISH_URL, self.publish_name)

        self.book_url = config.BOOK_URL % (self.server, self.book)
        self.toc_url = config.TOC_URL % (self.server, self.book)

        self.set_page_dimensions(page_settings)

        if engine is not None:
            self.engine = engine
        self.notify_watcher()

    def __del__(self):
        if os.path.exists(self.workdir) and self._try_cleanup_on_del:
            self._try_cleanup_on_del = False #or else you can get in bad cycles
            self.cleanup()

    def __getattr__(self, attr):
        """catch unloaded books and load them"""
        #log('looking for missing attribute "%s"' % (attr))
        if attr == 'tree':
            self.load_book()
            return self.tree
        if attr == 'toc':
            self.load_toc()
            return self.toc
        raise AttributeError("no such member: '%s'" % attr)


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

    def set_page_dimensions(self, dimensions):
        self.maker = PageSettings(**dimensions)


    def extract_pdf_text(self):
        """Extract the text from the body pdf, split into pages, so
        that the correct page can be found to generate the table of
        contents."""
        index_pdf(self.body_pdf_file, self.body_index_file)
        f = open(self.body_index_file)
        s = unicode(f.read(), 'utf8')
        f.close()
        #pages are spearated by formfeed character "^L", "\f" or chr(12)
        self.text_pages = s.split("\f")
        #there is sometimes (probably always) an unwanted ^L at the end
        return len(self.text_pages)

    def make_body_pdf(self):
        """Make a pdf of the HTML, using webkit"""
        #1. Save the html
        html_text = lxml.etree.tostring(self.tree, method="html")
        self.save_data(self.body_html_file, html_text)

        #2. Make a pdf of it
        self.maker.make_raw_pdf(self.body_html_file, self.body_pdf_file,
                                engine=self.engine)
        self.notify_watcher('generate_pdf')

        #3. extract the text for finding contents.
        n_pages = self.extract_pdf_text()
        log ("found %s pages in pdf" % n_pages)
        #4. resize pages, shift gutters, and rotate 180 degrees for RTL
        self.maker.reshape_pdf(self.body_pdf_file, self.dir, centre_end=True)
        self.notify_watcher('reshape_pdf')

        #5 add page numbers
        self.maker.number_pdf(self.body_pdf_file, n_pages, dir=self.dir,
                              numbers=self.page_numbers)
        self.notify_watcher("number_pdf")
        self.notify_watcher()

    def make_preamble_pdf(self):
        contents = self.make_contents()
        html = ('<html dir="%s"><head>\n'
                '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'
                '<link rel="stylesheet" href="%s" />\n'
                '</head>\n<body>\n'
                '<h1 class="frontpage">%s</h1>'
                '%s\n'
                '<div class="contents">%s</div>\n'
                '<div style="page-break-after: always; color:#fff" class="unseen">.'
                '<!--%s--></div></body></html>'
                ) % (self.dir, self.css_url, self.title, self.inside_cover_html,
                     contents, self.title)
        self.save_data(self.preamble_html_file, html)

        self.maker.make_raw_pdf(self.preamble_html_file, self.preamble_pdf_file,
                                engine=self.engine)

        self.maker.reshape_pdf(self.preamble_pdf_file, self.dir, centre_start=True)

        self.maker.number_pdf(self.preamble_pdf_file, None, dir=self.dir,
                            numbers=self.preamble_page_numbers,
                            number_start=-2)

        self.notify_watcher()

    def make_pdf(self):
        """A convenient wrapper of a few necessary steps"""
        # now the Xvfb server is needed. make sure it has had long enough to get going
        self.wait_for_xvfb()
        self.make_body_pdf()
        self.make_preamble_pdf()
        concat_pdfs(self.pdf_file, self.preamble_pdf_file, self.body_pdf_file)
        self.notify_watcher('concatenated_pdfs')
        #and move it into place (what place?)

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
        f = urlopen(self.toc_url)
        self.toc = []
        while True:
            try:
                self.toc.append(TocItem(f.next().strip(),
                                        f.next().strip(),
                                        f.next().strip()))
            except StopIteration:
                break
        f.close()
        self.notify_watcher()

    def load_book(self, tidy=True):
        """Fetch and parse the raw html of the book.  If tidy is true
        (default) links in the document will be made absolute."""
        f = urlopen(self.book_url)
        html = f.read()
        f.close()
        html = ('<html dir="%s"><head>\n<title>%s</title>\n'
                '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'
                '</head>\n<body>\n'
                '%s\n'
                '<div style="page-break-before: always; color:#fff;" class="unseen">'
                'A FLOSSManuals book</div>\n</body></html>'
                ) % (self.dir, self.book, html)

        self.save_tempfile('raw.html', html)

        tree = lxml.html.document_fromstring(html)
        if tidy:
            tree.make_links_absolute(self.book_url)
        self.tree = tree
        self.headings = [x for x in tree.cssselect('h1')]
        if self.headings:
            self.headings[0].set('class', "first-heading")
        #self.heading_texts = [x.textcontent() for x in self.headings]
        for h1 in self.headings:
            h1.title = h1.text_content().strip()
        self.notify_watcher()


    def load(self):
        """Wrapper around all necessary load methods."""
        self.load_book()
        self.load_toc()

    def find_page(self, element, start_page=1):
        """Search through a page iterator and return the page
        number which the element probably occurs."""
        text = element.cookie
        for i, content in enumerate(self.text_pages[start_page - 1:]):
            log("looking for '%s' in page %s below:\n%s[...]" %
                (text, i + start_page, content[:160]), debug='INDEX')
            #remove spaces: they can appear spuriously
            content = ''.join(content.split())
            if text in content:
                return i + start_page, True
        #If it isn't found, return the start page so the next chapter has a chance
        return start_page, False

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

        headings = iter(self.headings)

        for t in self.toc:
            if t.is_chapter():
                try:
                    h1 = headings.next()
                except StopIteration:
                    log("heading not found for %s (previous h1 missing?). Stopping" % t)
                    break
                page_num, found = self.find_page(h1, page_num)
                # sometimes the heading isn't found, which is shown as a frown
                if found:
                    contents.append(row_tmpl % (chapter, h1.title, page_num))
                else:
                    contents.append(row_tmpl % (chapter, h1.title, ':-('))
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
        log(self.headings)
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

                #put a bold number at the beginning of the h1, and a hidden cookie at the end.
                _add_initial_number(h1, chapter)
                _add_chapter_cookie(h1)
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


    def add_css(self, css=None):
        """If css looks like a url, use it as a stylesheet link.
        Otherwise it is the CSS itself, which is saved to a temporary file
        and linked to."""
        log("css is %r" % css)
        htmltree = self.tree
        if css is None or not css.strip():
            url = 'file://' + os.path.abspath(self.default_css)
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

    def compose_inside_cover(self, license=config.DEFAULT_LICENSE, isbn=None):
        """create the markup for the preamble inside cover, storing it
        in self.inside_cover_html."""
        #XXX this should go in make_preamble_pdf, but that needs to be extracted from make_pdf

        if isbn:
            isbn_text = '<b>ISBN :</b> %s <br>' % isbn
            #XXX make a barcode
        else:
            isbn_text = ''

        for lang in (self.lang, 'en'):
            try:
                fn = INSIDE_FRONT_COVER_TEMPLATE % (lang)
                f = open(fn)
            except IOError, e:
                log("couldn't open inside front cover for lang %s (filename %s)" % (lang, fn))
                log(e)

        template = f.read()
        f.close()

        self.inside_cover_html = template % {'date': time.strftime('%Y-%m-%d'),
                                             'isbn': isbn_text,
                                             'license': license,
                                             }


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

        if random.random() < 0.05:
            #kill old xvfbs occasionally, if there are any.
            self.kill_old_xvfbs()

    def kill_old_xvfbs(self):
        """Sometimes, despite everything, Xvfb instances hang around
        well after they are wanted -- for example if the cgi process
        dies particularly badly. So kill them if they have been
        running for a long time."""
        log("running kill_old_xvfbs")
        p = Popen(['ps', '-C' 'Xvfb', '-o', 'pid,etime', '--no-headers'], stdout=PIPE)
        data = p.communicate()[0].strip()
        if data:
            lines = data.split('\n')
            for line in lines:
                log('dealing with ps output "%s"' % line)
                try:
                    pid, days_, hours, minutes, seconds = re.match(r'^(\d+)\s+(\d+-)?(\d{2})?:?(\d{2}):(\d+)\s*$').groups()
                except AttributeError:
                    log("Couldn't parse that line!")
                # 50 minutes should be enough xvfb time for anyone
                if days or hours or int(minutes) > 50:
                    log("going to kill pid %s" % pid)
                    os.kill(int(pid), 15)
                    time.sleep(0.5)
                    os.kill(int(pid), 9)
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


