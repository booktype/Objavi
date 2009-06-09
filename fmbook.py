"""Library module representing a complete FM book being turned into a
PDF"""

import os, sys
import tempfile
import re
from urllib2 import urlopen
from subprocess import Popen, check_call

import lxml.etree, lxml.html

import lxml, lxml.html, lxml.etree

POINT_2_MM = 0.35277777777777777

KEEP_TEMP_FILES=True

TOC_URL = "http://%s/pub/%s/_index/TOC.txt"
BOOK_URL = "http://%s/bin/view/%s/_all?skin=text"

DEFAULT_CSS = 'file://' + os.path.abspath('default.css')

def log(*messages):
    for m in messages:
        print >> sys.stderr, m

def _add_initial_number(e, n):
    """Put a styled chapter number n at the beginning of element e."""
    initial = e.makeelement("strong", Class="initial")
    e.insert(0, initial)
    initial.tail = ' '
    if e.text is not None:
        initial.tail += e.text
    e.text = ''
    initial.text = "%s." % n


class TocItem:
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


class PageSettings:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.mmsize = [x * POINT_2_MM for x in self.pointsize]
        self.area = self.pointsize[0] * self.pointsize[1]

    def _webkit_command(self, html, pdf):
        m = [str(x) for x in self.wkmargins]
        cmd = ['wkhtmltopdf', '-s', self.wksize,
               '-T', m[0], '-R', m[1], '-B', m[2], '-L', m[3],
               html, pdf
               ]
        log(' '.join(cmd))
        return cmd

    def pdfcommand(self, html, pdf, engine='webkit'):
        func = getattr(self, '_%s_command' % engine)
        return func(html, pdf)


    def shiftcommand(self, pdf, dir='LTR', numbers='latin', number_start=1,
                     inplace=False, engine='webkit', index=True):
        # XXX everything MUST be sanitised before getting here.
        #numbers should be 'latin', 'roman', or 'arabic'
        if inplace:
            outfile = pdf
        else:
            outfile = self.output_name

        cmd = ['pdfedit', '-s', 'wk_objavi.qs',
               'dir=%s' % dir,
               'filename=%s' % pdf,
               'output_filename=%s' % outfile,
               'mode=%s' % self.name,
               'number_start=%s' % number_start,
               'number_style=%s' % numbers,
               'number_bottom=%s' % self.wknumberpos[1],
               'number_margin=%s' % self.wknumberpos[0],
               'offset=%s' % self.shift,
               'engine=%s' % engine,
               'index=%s' % index,
               #height, width  -- set by 'mode'
               ]
        log(' '.join(cmd))
        return cmd

    def output_name(self, input_name):
        """replicate the name mangling performed by shift_margins.qs
        pdfedit script."""
        #XXX should just pass in name to pdfedit
        if hasattr(self, 'dir'):
            return '%s-%s-%s.pdf' % (input_name[:-4], self.name, self.dir)
        return '%s-%s.pdf' % (input_name[:-4], self.name)


SIZE_MODES = {
    # name      --> should be the same as the key
    # wksize    --> the size name for wkhtml2pdf
    # wkmargins --> margins for wkhtml2pdf (css style, clockwise from top)
    # shift     --> how many points to shift each page left or right.

    'COMICBOOK' : PageSettings(name='COMICBOOK',
                               wksize='B5',
                               wkmargins=[20, 30, 20, 30], #mm
                               wknumberpos=[50, 40], #points, after page resize, from corner
                               shift=20,
                               pointsize=((6.625 * 72), (10.25 * 72)),
                               )
}

ENGINES = {
    'webkit' : [],
}


def make_pdf(html_file, pdf_file, size='COMICBOOK', numbers='latin',
             dir='LTR', number_start=1, inplace=False, engine='webkit',
             index=True):
    """Make a pdf of the named html file, using webkit.  Returns a
    filename for the finished PDF."""
    settings = SIZE_MODES[size]
    check_call(settings.pdfcommand(html_file, pdf_file, engine))
    check_call(settings.shiftcommand(pdf_file, numbers=numbers, dir=dir,
                                     number_start=number_start, inplace=inplace,
                                     engine=engine, index=index))
    if inplace:
        return pdf_file
    return settings.output_name(pdf_file)

def make_pdf_cached(bookid, size='COMICBOOK'):
    #Assume the html is already there
    """Make a pdf of the HTML, using webkit"""
    settings = SIZE_MODES[size]
    html_file = '/tmp/%s.html' % bookid
    pdf_raw = '/tmp/%s.pdf' % bookid
    pdf_shifted = settings.output_name(pdf_raw)
    check_call(settings.pdfcommand(html_file, pdf_raw))
    check_call(settings.shiftcommand(pdf_raw))

def concat_pdfs(name, *args):
    """Join all the named pdfs together into one and save it as <name>"""
    cmd = ['pdftk']
    cmd.extend(args)
    cmd += ['cat', 'output', name]
    check_call(cmd)




class Book(object):
    pagesize = 'COMICBOOK'
    page_numbers = 'latin'
    preamble_page_numbers = 'roman'
    engine= 'webkit'

    def __init__(self, webname, server,
                 pagesize=None, engine=None):
        self.webname = webname
        self.server = server
        self.workdir = tempfile.mkdtemp(prefix=webname)
        self.body_html_file = self.filepath('body.html')
        self.body_pdf_file = self.filepath('body.pdf')
        self.body_index_file = self.filepath('body.pdf.index')
        self.preamble_html_file = self.filepath('preamble.html')
        self.preamble_pdf_file = self.filepath('preamble.pdf')
        self.pdf_file = self.filepath('final.pdf')

        self.book_url = BOOK_URL % (self.server, self.webname)
        self.toc_url = TOC_URL % (self.server, self.webname)
        if pagesize is not None:
            self.pagesize = pagesize
        if engine is not None:
            self.engine = engine

    def __del__(self):
        if not KEEP_TEMP_FILES:
            for fn in os.listdir(self.workdir):
                os.remove(os.path.join(self.workdir, fn))
            os.rmdir(self.workdir)
        else:
            log("NOT removing '%s', containing the following files:" % self.workdir)
            log(*os.listdir(self.workdir))

    def __getattr__(self, attr):
        """catch unloaded books and load them"""
        log('fetching %s from %s...' % (attr, self.server))
        if attr == 'tree':
            self.load_book()
            return self.tree
        if attr == 'toc':
            self.load_toc()
            return self.toc

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

    def make_body_pdf(self):
        """Make a pdf of the HTML, using webkit"""
        html_text = lxml.etree.tostring(self.tree, method="html")
        self.save_data(self.body_html_file, html_text)
        return make_pdf(self.body_html_file, self.body_pdf_file,
                        size=self.pagesize, numbers=self.page_numbers, inplace=True, engine=self.engine)


    def make_preamble_pdf(self):
        contents = self.make_contents()
        html = ('<html><head>\n'
                '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'
                '<link rel="stylesheet" href="%s" />\n'
                '</head>\n<body>\n'
                '<h1 class="frontpage">%s</h1>'
                '<div class="copyright">%s</div>\n'
                '<div class="contents">%s</div>\n</body></html>'
                ) % (self.css_url, self.title, self.copyright(), contents)
        self.save_data(self.preamble_html_file, html)
        return make_pdf(self.preamble_html_file, self.preamble_pdf_file, size=self.pagesize,
                        numbers=self.preamble_page_numbers, number_start=-2, inplace=True, engine=self.engine, index=False)


    def make_pdf(self):
        self.make_body_pdf()
        self.make_preamble_pdf()
        concat_pdfs(self.pdf_file, self.preamble_pdf_file, self.body_pdf_file)
        #and move it into place (what place?)


    def copyright(self):
        return "copyright goes here"

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


    def load_book(self, tidy=True):
        """Fetch and parse the raw html of the book.  If tidy is true
        (default) links in the document will be made absolute."""
        f = urlopen(self.book_url)
        html = f.read()
        f.close()
        html = ('<html><head>\n<title>%s</title>\n'
                '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'
                '</head>\n<body>\n'
                '%s\n</body></html>') % (self.webname, html)

        self.save_tempfile('raw.html', html)

        tree = lxml.html.document_fromstring(html)
        if tidy:
            tree.make_links_absolute(self.book_url)
        self.tree = tree
        self.headings = [x for x in tree.cssselect('h1')]
        #self.heading_texts = [x.textcontent() for x in self.headings]
        for h1 in self.headings:
            h1.title = h1.text_content().strip()

    def load(self):
        self.load_book()
        self.load_toc()

    def find_page(self, element, pages, page_initial=True):
        """Search through a page_text_iterator and return the page
        number which the element probably occurs."""
        text = ' '.join(element.text_content().strip().lower().split())
        for p in pages:
            print "looking for '%s' in page %s below:\n%s" % (text, p[0], p[1])
            if (not page_initial and text in p[1]) or p[1].startswith(text):
                return p[0]


    def page_text_iterator(self):
        """Return the text found in the pdf, one page at a time,
        transformed to lowercase."""
        f = open(self.body_index_file)
        page = 0
        text = []
        for line in f:
            line = line.strip()
            if line == '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^':
                if page:
                    yield(page, ' '.join(text))
                page = int(f.next())
                text = []
            else:
                text.append(' '.join(line.lower().split()))

        yield(page, ' '.join(text))
        f.close()


    def make_contents(self):
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
        pages = self.page_text_iterator()

        for t in self.toc:
            if t.is_chapter():
                h1 = headings.next()
                page_num = self.find_page(h1, pages)
                contents.append(row_tmpl % (chapter, h1.title, page_num))
                chapter += 1
            elif t.is_section():
                contents.append(section_tmpl % t.title)
            else:
                log("mystery TOC item: %s" % t)

        doc = header + '\n'.join(contents) + footer
        return doc



    def add_section_titles(self):
        headings = iter(self.headings)
        chapter = 1
        section = None

        for t in self.toc:
            if t.is_chapter() and section is not None:
                h1 = headings.next()
                item = h1.makeelement('div', Class='chapter')
                print h1.title
                item.text = h1.title
                _add_initial_number(item, chapter)

                section.append(item)

                if not section_placed:
                    print "placing section"
                    h1.addprevious(section)
                    section_placed = True
                else:
                    print "NOT placing section"

                #put a bold number at the beginning of the h1
                _add_initial_number(h1, chapter)
                chapter += 1


            elif t.is_section():
                section = self.tree.makeelement('div', Class="subsection")
                # section Element complains when you try to ask it whether it
                # has been placed (though it does know)
                section_placed = False
                heading = lxml.etree.SubElement(section, 'div', Class="subsection-heading")
                heading.text = t.title




    def add_css(self, css=None):
        """If css looks like a url, use it as a stylesheet link.
        Otherwise it is the CSS itself, which is saved to a temporary file
        and linked to."""
        htmltree = self.tree
        if css is None:
            url = DEFAULT_CSS
        elif not re.match(r'^http://\S+$', css):
            fn = save_tempfile('objavi.css', css)
            url = 'file://' + fn
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

        link = lxml.etree.SubElement(head, 'link', rel='stylesheet', type='text/css', href=url)
        self.css_url = url
        return url

    def set_title(self, title=None):
        if title:
            self.title = title
        else:
            titles = [x.text_content() for x in self.tree.cssselect('title')]
            if titles and titles[0]:
                self.title = titles[0]
            else:
                #oh well
                self.title = 'A Manual About ' + self.webname
        return self.title




