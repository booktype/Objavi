# Part of Objavi2, which turns html manuals into books.
# This deals with PDF and page specific concepts.
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

"""Fiddly stuff to do with pages and PDFs."""

import os, sys
import re
from subprocess import Popen, PIPE
import urllib

from objavi import config
from objavi.book_utils import log, run
from objavi.cgi_utils import path2url

def find_containing_paper(w, h):
    for name, pw, ph in config.PAPER_SIZES:
        if pw >= w and ph >= h:
            mw = (pw - w) * 0.5
            mh = (ph - h) * 0.5
            return (name, mw, mh)

    raise ValueError("page sized %.2fmm x %.2fmm won't fit on any paper!" %
                     (w * config.POINT_2_MM, h * config.POINT_2_MM))

class PageSettings(object):
    """Calculates and wraps commands for the generation and processing
    of PDFs"""
    def __init__(self, pointsize, **kwargs):
        # the formulas for default gutters, margins and column margins
        # are quite ad-hoc and certainly improvable.
        self.width, self.height = pointsize
        self.papersize, clipx, clipy = find_containing_paper(self.width, self.height)
        self.grey_scale = 'grey_scale' in kwargs

        self.engine = kwargs.get('engine', config.DEFAULT_ENGINE)
        # All measurements in points unless otherwise stated
        # user interaction is in *mm*, but is converted in objavi2.py
        default_margin = (config.BASE_MARGIN + config.PROPORTIONAL_MARGIN * min(pointsize))
        default_gutter = (config.BASE_GUTTER + config.PROPORTIONAL_GUTTER * self.width)

        self.top_margin = kwargs.get('top_margin', default_margin)
        self.side_margin = kwargs.get('side_margin', default_margin)
        self.bottom_margin = kwargs.get('bottom_margin', default_margin)
        self.gutter = kwargs.get('gutter', default_gutter)

        self.columns = kwargs.get('columns', 1)
        if self.columns == 'auto': #default for newspapers is to work out columns
            self.columns = int(self.width // config.MIN_COLUMN_WIDTH)

        self.column_margin = kwargs.get('column_margin',
                                        default_margin * 2 / (5.0 + self.columns))

        self.number_bottom = self.bottom_margin - 0.6 * config.PAGE_NUMBER_SIZE
        self.number_margin = self.side_margin

        # calculate margins in mm for browsers
        self.margins = []
        for m, clip in ((self.top_margin, clipy),
                        (self.side_margin, clipx + 0.5 * self.gutter),
                        (self.bottom_margin, clipy + 0.5 * config.PAGE_NUMBER_SIZE),
                        (self.side_margin, clipx + 0.5 * self.gutter),
                        ):
            self.margins.append((m + clip) * config.POINT_2_MM)

        self.moz_printer = kwargs.get('moz_printer', ('objavi_' + self.papersize))

        if 'PDFGEN' in config.DEBUG_MODES:
            log("making PageSettings with:")
            for x in locals().iteritems():
                log("%s: %s" % x, debug='PDFGEN')
            for x in dir(self):
                if not x.startswith('__'):
                    log("self.%s: %s" % (x, getattr(self, x)), debug='PDFGEN')



    def _webkit_command(self, html, pdf, outline=False, outline_file=None):
        m = [str(x) for x in self.margins]
        outline_args = ['--outline',  '--outline-depth', '2'] * outline
        if outline_file is not None:
            outline_args += ['--dump-outline', outline_file]

        greyscale_args = ['-g'] * self.grey_scale
        quiet_args = ['-q']
        cmd = ([config.WKHTMLTOPDF] +
               quiet_args +
               ['-s', self.papersize,
               '-T', m[0], '-R', m[1], '-B', m[2], '-L', m[3],
               '-d', '100'] +
               outline_args +
               greyscale_args +
               config.WKHTMLTOPDF_EXTRA_COMMANDS +
               [html, pdf])
        log(' '.join(cmd))
        return cmd


    def make_raw_pdf(self, html, pdf, outline=False, outline_file=None):
        html_url = path2url(html, full=True)
        func = getattr(self, '_%s_command' % self.engine)
        if self.columns == 1:
            cmd = func(html_url, pdf, outline=outline, outline_file=outline_file)
            run(cmd)
        else:
            printable_width = self.width - 2.0 * self.side_margin - self.gutter
            column_width = (printable_width - (self.columns - 1) * self.column_margin) / self.columns
            page_width = column_width + self.column_margin
            side_margin = self.column_margin * 0.5
            if 'PDFGEN' in config.DEBUG_MODES:
                log("making columns with:")
                for k, v in locals().iteritems():
                    log("%s: %r" % (k, v))
                for k in ('width', 'side_margin', 'gutter', 'column_margin', 'columns', 'height'):
                    log("self.%s: %r" % (k, getattr(self, k)))

            columnmaker = PageSettings((page_width, self.height), moz_printer=self.moz_printer,
                                       gutter=0, top_margin=self.top_margin,
                                       side_margin=side_margin,
                                       bottom_margin=self.bottom_margin,
                                       grey_scale=self.grey_scale,
                                       engine=self.engine
                                       )

            column_pdf = pdf[:-4] + '-single-column.pdf'
            columnmaker.make_raw_pdf(html, column_pdf, outline=outline, outline_file=outline_file)
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
        if pages is None or pages <= config.PDFEDIT_MAX_PAGES:
            self._number_pdf(pdf, **kwargs)
        else:
            # section_size must be even
            sections = pages // config.PDFEDIT_MAX_PAGES + 1
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

        position = '%s,%s,%s,%s,%s' % (corner, self.width, self.height, self.side_margin, self.bottom_margin)
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
    m = re.search(r'^\s*Pages:\s*(\d+)\s*$', out, re.MULTILINE)
    return int(m.group(1))


def concat_pdfs(destination, *pdfs):
    """Join all the named pdfs together into one and save it as <name>"""
    cmd = ['pdftk']
    cmd.extend(x for x in pdfs if x is not None)
    cmd += ['cat', 'output', destination]
    run(cmd)

def rotate_pdf(pdfin, pdfout):
    """Turn the PDF on its head"""
    cmd = ['pdftk', pdfin,
           'cat',
           '1-endD',
           'output',
           pdfout
           ]
    run(cmd)

def parse_extracted_outline(outline_file, depth=config.CONTENTS_DEPTH):
    """Extract outline data from a file structured as follows:

    The first line contains the text "Pages: ", followed by the total
    number of pages in the PDF (all numbers are in ascii decimal
    digits).

    Each following line looks like this

    "Level: " <level> "  Page: "  <page number> "  Title: " <title> "\n"

    where <level> is an integer indicating the significance of the
    heading, <page number> is self-explanatory, and <title> is the
    title encoded as utf-8 text that has been escaped as in a URI:
    non-alphanumeric characters are replaced by "%" followed by two
    hexadecimal digits giving their value (This escaping system is
    variously called "url-encoding" or "percent-encoding" and is
    described in section 2.1 of RFC 3986).
    """
    f = open(outline_file, 'r')
    page_line = f.next()
    log(page_line)
    page_count = int(re.match('^Pages: (\d+)', page_line).group(1))

    contents = []
    for line in f:
        m = re.match('Level: (\d+)\s+Page: (\d+)\s+Title: (\S*)', line)
        level = int(m.group(1))
        if level > depth:
            continue
        pagenum = int(m.group(2))
        title = urllib.unquote(m.group(3)).strip()#.decode('utf-8')
        if not title:
            log("WARNING: heading level %s on page %s is empty string" % (level, pagenum))
        contents.append((title, level, pagenum))

    return contents, page_count



def parse_outline(pdf, level_threshold, debug_filename=None):
    """Create a structure reflecting the outline of a PDF.
    A chapter heading looks like this:

    BookmarkTitle: 2. What is sound?
    BookmarkLevel: 1
    BookmarkPageNumber: 3
    """
    cmd = ('pdftk', pdf, 'dump_data')
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    outline, err = p.communicate()
    #log("OUTLINE:", outline)
    if debug_filename is not None:
        try:
            f = open(debug_filename, 'w')
            f.write(outline)
            f.close()
        except IOError:
            log("could not write to %s!" % debug_filename)

    lines = (x.strip() for x in outline.split('\n') if x.strip())
    contents = []

    def _strip(s):
        return s.strip(config.WHITESPACE_AND_NULL)

    def extract(expected, conv=_strip):
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

    return contents, page_count
