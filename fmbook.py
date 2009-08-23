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



    def _webkit_command(self, html, pdf, outline=False):
        m = [str(x) for x in self.margins]
        outline_args = ['--outline'] * outline
        cmd = ([config.WKHTMLTOPDF, '-q', '-s', self.papersize,
               '-T', m[0], '-R', m[1], '-B', m[2], '-L', m[3],
               ] + outline_args +
               config.WKHTMLTOPDF_EXTRA_COMMANDS + [html, pdf])
        log(' '.join(cmd))
        return cmd

    def _gecko_command(self, html, pdf, outline=False):
        m = [str(x) for x in self.margins]
        #firefox -P pdfprint -print URL -printprinter "printer_settings"
        cmd = [config.FIREFOX, '-P', 'pdfprint', '-print',
               html, '-printprinter', self.moz_printer]
        log(' '.join(cmd))
        return cmd

    def make_raw_pdf(self, html, pdf, engine='webkit', outline=False):
        func = getattr(self, '_%s_command' % engine)
        if self.columns == 1:
            cmd = func(html, pdf, outline=outline)
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
            columnmaker.make_raw_pdf(html, column_pdf, engine=engine, outline=outline)
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

    def make_barcode_pdf(self, isbn, pdf, corner='br'):
        """Put an ISBN barcode in a corner of a single blank page."""

        position = '%s,%s,%s,%s,%s' %(corner, self.width, self.height, self.side_margin, self.bottom_margin)
        cmd1 = [config.BOOKLAND,
                '--position', position,
                str(isbn)]
        cmd2 = ['ps2pdf',
                '-dFIXEDMEDIA',
                '-dDEVICEWIDTHPOINTS=%s' % self.width,
                '-dDEVICEHEIGHTPOINTS=%s' % self.height,
                '-', pdf]

        p1 = Popen(cmd1, stdout=PIPE)
        p2 = Popen(cmd2, stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
        out, err = p2.communicate()

        log('ran:\n%s | %s' % (' '.join(cmd1), ' '.join(cmd2)))
        log("return: %s and %s \nstdout:%s \nstderr:%s" % (p1.poll(), p2.poll(), out, err))


def count_pdf_pages(pdf):
    """How many pages in the PDF?"""
    #XXX could also use python-pypdf or python-poppler
    cmd = ('pdfinfo', pdf)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    m = re.search(r'^\s*Pages:\s*(\d+)\s*$', re.MULTILINE)
    return int(m.group(1))


def concat_pdfs(destination, *pdfs):
    """Join all the named pdfs together into one and save it as <name>"""
    cmd = ['pdftk']
    cmd.extend(x for x in pdfs if x is not None)
    cmd += ['cat', 'output', destination]
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

def parse_outline(pdf, level_threshold):
    """Create a structure reflecting the outline of a PDF.
    A chapter heading looks like this:

    BookmarkTitle: 2. What is sound?
    BookmarkLevel: 1
    BookmarkPageNumber: 3
    """
    cmd = ('pdftk', pdf, 'dump_data')
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    outline, err = p.communicate()
    lines = (x.strip() for x in outline.split('\n') if x.strip())
    contents = []

    def extract(expected, conv=str.strip):
        line = lines.next()
        try:
            k, v = line.split(':', 1)
            if k == expected:
                return conv(v)
        except ValueError:
            log("trouble with line %r" %line)

    #There are a few useless variables, then the pagecount, then the contents.
    #The pagecount is useful, so pick it up first.
    page_count = None
    while page_count == None:
        page_count = extract('NumberOfPages', int)

    try:
        while True:
            title = extract('BookmarkTitle')
            if title is not None:
                level = extract('BookmarkLevel', int)
                pagenum = extract('BookmarkPageNumber', int)
                if level <= level_threshold and None not in (level, pagenum):
                    contents.append((title, level, pagenum))
    except StopIteration:
        pass

    return contents, outline, page_count


class Book(object):
    page_numbers = 'latin'
    preamble_page_numbers = 'roman'
    engine= 'webkit'
    _try_cleanup_on_del = config.TRY_BOOK_CLEANUP_ON_DEL

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
                 page_settings=None, engine=None, watcher=None, isbn=None,
                 license=config.DEFAULT_LICENSE):
        log("*** Starting new book %s ***" % bookname)
        self.book = book
        self.server = server
        self.watcher = watcher
        self.isbn = isbn
        self.license = license
        self.workdir = tempfile.mkdtemp(prefix=bookname, dir=TMPDIR)
        os.chmod(self.workdir, 0755)
        defaults = SERVER_DEFAULTS[server]
        self.lang = defaults['lang']
        self.dir  = defaults['dir']

        self.body_html_file = self.filepath('body.html')
        self.body_pdf_file = self.filepath('body.pdf')
        self.body_index_file = self.filepath('body.txt')
        self.preamble_html_file = self.filepath('preamble.html')
        self.preamble_pdf_file = self.filepath('preamble.pdf')
        self.tail_html_file = self.filepath('tail.html')
        self.tail_pdf_file = self.filepath('tail.pdf')
        self.isbn_pdf_file = None
        self.pdf_file = self.filepath('final.pdf')

        self.publish_name = bookname
        self.publish_file = os.path.join(PUBLISH_PATH, self.publish_name)
        self.publish_url = os.path.join(config.PUBLISH_URL, self.publish_name)

        self.book_url = config.BOOK_URL % (self.server, self.book)
        self.toc_url = config.TOC_URL % (self.server, self.book)

        self.maker = PageSettings(**page_settings)

        if engine is not None:
            self.engine = engine
        self.notify_watcher()

    def __del__(self):
        if self._try_cleanup_on_del and os.path.exists(self.workdir):
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

    def extract_pdf_outline(self):
        self.outline_contents, self.outline_text, number_of_pages = parse_outline(self.body_pdf_file, 1)
        for x in self.outline_contents:
            log(x)
        return number_of_pages

    def make_body_pdf(self):
        """Make a pdf of the HTML, using webkit"""
        #1. Save the html
        html_text = lxml.etree.tostring(self.tree, method="html")
        self.save_data(self.body_html_file, html_text)

        #2. Make a pdf of it
        self.maker.make_raw_pdf(self.body_html_file, self.body_pdf_file,
                                engine=self.engine, outline=True)
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

        self.maker.make_raw_pdf(self.preamble_html_file, self.preamble_pdf_file,
                                engine=self.engine)

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
        self.maker.make_raw_pdf(self.tail_html_file, self.tail_pdf_file,
                                engine=self.engine)

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
        self.maker.make_raw_pdf(self.body_html_file, self.pdf_file,
                                engine=self.engine, outline=True)
        self.notify_watcher('generate_pdf')
        n_pages = self.extract_pdf_outline()

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
            defaults = SERVER_DEFAULTS[self.server]
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


