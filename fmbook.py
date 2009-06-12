"""Library module representing a complete FM book being turned into a
PDF"""

import os, sys
import tempfile
import re, time
from urllib2 import urlopen
from subprocess import Popen, check_call, PIPE

import lxml.etree, lxml.html
import lxml, lxml.html, lxml.etree

from config import PAGE_SIZE_DATA, SERVER_DEFAULTS, DEFAULT_SERVER
from config import POINT_2_MM, KEEP_TEMP_FILES, TMPDIR
from config import ENGINES, DEBUG_MODES, TOC_URL, PUBLISH_URL, BOOK_URL, DEBUG_ALL

TMPDIR = os.path.abspath(TMPDIR)
DOC_ROOT = os.environ.get('DOCUMENT_ROOT', '.')
PUBLISH_PATH = "%s/books/" % DOC_ROOT

def log(*messages, **kwargs):
    """Send the messages to the appropriate place (stderr, or syslog).
    If a <debug> keyword is specified, the message is only printed if
    its value ias in the global DEBUG_MODES."""
    if 'debug' not in kwargs or DEBUG_ALL or kwargs['debug'] in DEBUG_MODES:
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
                     outfile=None, engine='webkit', index=True):
        # XXX everything MUST be sanitised before getting here.
        #numbers should be 'latin', 'roman', or 'arabic'
        if outfile is None:
            outfile = pdf

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


    def make_pdf(self, html_file, pdf_file, size='COMICBOOK', numbers='latin',
                 dir='LTR', number_start=1, engine='webkit',
                 index=True):
        """Make a pdf of the named html file, using webkit.  Returns a
        filename for the finished PDF."""
        p = Popen(self.pdfcommand(html_file, pdf_file, engine), stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if out or err:
            log("pdf generation produced\n", out, err)

        p = Popen(self.shiftcommand(pdf_file, numbers=numbers, dir=dir,
                                    number_start=number_start,
                                    engine=engine, index=index), stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if out or err:
            log("pdf generation produced\n", out, err)


PAGE_SETTINGS = dict((k, PageSettings(**v)) for k, v in PAGE_SIZE_DATA.iteritems())

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
    _try_cleanup_on_del = True

    def notify_watcher(self, message=None):
        if self.watcher:
            if  message is None:
                #message is the name of the caller
                import traceback
                message = traceback.extract_stack(None, 2)[0][2]
                log("notify_watcher called by '%s'" % message)
            self.watcher(message)


    def __init__(self, webname, server, bookname,
                 pagesize=None, engine=None, watcher=None):
        log("*** Starting new book %s ***" % bookname)
        self.webname = webname
        self.server = server
        self.watcher = watcher
        self.workdir = tempfile.mkdtemp(prefix=webname, dir=TMPDIR)
        defaults = SERVER_DEFAULTS.get(server, SERVER_DEFAULTS[DEFAULT_SERVER])
        self.default_css = defaults['css']
        self.lang = defaults['lang']
        self.dir  = defaults['dir']

        self.body_html_file = self.filepath('body.html')
        self.body_pdf_file = self.filepath('body.pdf')
        self.body_index_file = self.filepath('body.pdf.index')
        self.preamble_html_file = self.filepath('preamble.html')
        self.preamble_pdf_file = self.filepath('preamble.pdf')
        self.pdf_file = self.filepath('final.pdf')

        self.publish_name = bookname
        self.publish_file = os.path.join(PUBLISH_PATH, self.publish_name)
        self.publish_url = os.path.join(PUBLISH_URL, self.publish_name)

        self.book_url = BOOK_URL % (self.server, self.webname)
        self.toc_url = TOC_URL % (self.server, self.webname)
        if pagesize is not None:
            self.pagesize = pagesize
        self.maker = PAGE_SETTINGS[self.pagesize]

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

    def make_body_pdf(self):
        """Make a pdf of the HTML, using webkit"""
        html_text = lxml.etree.tostring(self.tree, method="html")
        self.save_data(self.body_html_file, html_text)
        self.maker.make_pdf(self.body_html_file, self.body_pdf_file, dir=self.dir,
                 size=self.pagesize, numbers=self.page_numbers, engine=self.engine)
        self.notify_watcher()

    def make_preamble_pdf(self):
        contents = self.make_contents()
        html = ('<html dir="%s"><head>\n'
                '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'
                '<link rel="stylesheet" href="%s" />\n'
                '</head>\n<body>\n'
                '<h1 class="frontpage">%s</h1>'
                '<div class="copyright">%s</div>\n'
                '<div class="contents">%s</div>\n</body></html>'
                ) % (self.dir, self.css_url, self.title, self.copyright(), contents)
        self.save_data(self.preamble_html_file, html)
        self.maker.make_pdf(self.preamble_html_file, self.preamble_pdf_file, size=self.pagesize, dir=self.dir,
                            numbers=self.preamble_page_numbers, number_start=-2, engine=self.engine, index=False)
        self.notify_watcher()

    def make_pdf(self):
        # now the Xvfb server is needed. make sure it has had long enough to get going
        self.wait_for_xvfb()
        self.make_body_pdf()
        self.make_preamble_pdf()
        concat_pdfs(self.pdf_file, self.preamble_pdf_file, self.body_pdf_file)
        self.notify_watcher('concatenated_pdfs')
        #and move it into place (what place?)

    def publish_pdf(self):
        log(self.filepath('final.pdf'), self.publish_file)
        os.rename(self.filepath('final.pdf'), self.publish_file)
        self.notify_watcher()


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
                '%s\n</body></html>') % (self.dir, self.webname, html)

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
        self.load_book()
        self.load_toc()

    def find_page(self, element, pages, page_initial=False):
        """Search through a page_text_iterator and return the page
        number which the element probably occurs."""
        text = ' '.join(element.text_content().strip().lower().split())
        for p in pages:
            log("looking for '%s' in page %s below:\n%s" % (text, p[0], p[1]), debug='INDEX')
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
            if line == '-=-=- Magic Page Separating Line Not Found In Any Books -=-=-':
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
        self.notify_watcher()
        return doc

    def add_section_titles(self):
        headings = iter(self.headings)
        chapter = 1
        section = None

        for t in self.toc:
            if t.is_chapter() and section is not None:
                h1 = headings.next()
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

        self.notify_watcher()


    def add_css(self, css=None):
        """If css looks like a url, use it as a stylesheet link.
        Otherwise it is the CSS itself, which is saved to a temporary file
        and linked to."""
        htmltree = self.tree
        if css is None:
            url = 'file://' + os.path.abspath(self.default_css)
        elif not re.match(r'^http://\S+$', css):
            fn = self.save_tempfile('objavi.css', css)
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
        self.notify_watcher()
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

    def spawn_x(self):
        #Find an unused server number (in case two cgis are running at once)
        import random
        while True:
            servernum = random.randrange(50, 500)
            if not os.path.exists('/tmp/.X%s-lock' % servernum):
                break

        self.xserver_no = ':%s' % servernum

        authfile = self.filepath('Xauthority')
        os.environ['XAUTHORITY'] = authfile

        #mcookie(1) eats into /dev/random, so avoid that
        from hashlib import md5
        f = open('/dev/urandom')
        m = md5("%r %r %r %r %r" % (self, os.environ, os.getpid(), time.time(), f.read(32)))
        f.close()
        mcookie = m.hexdigest()

        check_call(['xauth', 'add', self.xserver_no, '.', mcookie])

        self.xvfb = Popen(['Xvfb', self.xserver_no,
                           '-screen', '0', '1024x768x24',
                           '-extension', 'Composite',
                           '-kb',
                           '-nolisten', 'tcp',
                           ])


        # We need to wait a bit before the Xvfb is ready.  but the
        # downloads are so slow that that probaby doesn't matter

        self.xvfb_ready_time = time.time() + 2

        os.environ['DISPLAY'] = self.xserver_no
        log(self.xserver_no)

    def wait_for_xvfb(self):
        if hasattr(self, 'xvfb'):
            d = self.xvfb_ready_time - time.time()
            if d > 0:
                sleep(d)
                self.notify_watcher()

    def cleanup_x(self):
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

    def cleanup(self):
        self.cleanup_x()
        if not KEEP_TEMP_FILES:
            for fn in os.listdir(self.workdir):
                os.remove(os.path.join(self.workdir, fn))
            os.rmdir(self.workdir)
        else:
            log("NOT removing '%s', containing the following files:" % self.workdir)
            log(*os.listdir(self.workdir))

        self.notify_watcher()
