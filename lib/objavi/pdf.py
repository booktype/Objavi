# Part of Objavi2, which turns html manuals into books.
# This deals with PDF and page specific concepts.
#
# Copyright (C) 2009 Douglas Bagnall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
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
from constants import POINT_2_MM


class PageSettings(object):
    """Calculates and wraps commands for the generation and processing
    of PDFs"""
    def __init__(self, workdir, pointsize, **kwargs):
        # the formulas for default gutters, margins and column margins
        # are quite ad-hoc and certainly improvable.
        self.workdir = workdir # must be relative to DATA_ROOT
        self.width, self.height = pointsize
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
            self.columns = self.width // config.MIN_COLUMN_WIDTH
        self.columns = int(self.columns)

        self.column_margin = kwargs.get('column_margin',
                                        default_margin * 2 / (5.0 + self.columns))


        # calculate margins in mm for browsers
        self.margins = []
        for m, clip in ((self.top_margin, 0),
                        (self.side_margin, 0.5 * self.gutter),
                        (self.bottom_margin, 0),
                        (self.side_margin, 0.5 * self.gutter),
                        ):
            self.margins.append((m + clip) * POINT_2_MM)

        if 'PDFGEN' in config.DEBUG_MODES:
            log("making PageSettings with:")
            for x in locals().iteritems():
                log("%s: %s" % x, debug='PDFGEN')
            for x in dir(self):
                if not x.startswith('__'):
                    log("self.%s: %s" % (x, getattr(self, x)), debug='PDFGEN')


    def get_boilerplate(self, requested):
        """Return (footer url, header url)"""
        footer_tmpl, header_tmpl = config.BOILERPLATE_HTML.get(requested, config.DEFAULT_BOILERPLATE_HTML)
        html = []
        for templ_path in (footer_tmpl, header_tmpl):
            if templ_path is not None:
                f = open(os.path.join(config.TEMPLATE_ROOT, templ_path))
                template_text = f.read()
                f.close()

                #XXX can manipulate footer here, for CSS etc

                out_path = os.path.join(self.workdir, os.path.basename(templ_path))
                f = open(out_path, 'w')
                f.write(template_text)
                f.close()

                html.append(path2url(out_path))
            else:
                html.append(None)

        return html


    def _webkit_command(self, html_url, pdf, outline=False, outline_file=None, page_num=None):
        m = [str(x) for x in self.margins]
        outline_args = ['--outline',  '--outline-depth', '2'] * outline
        if outline_file is not None:
            outline_args += ['--dump-outline', outline_file]

        page_num_args = []
        if page_num:
            footer_url, header_url = self.get_boilerplate(page_num)
            if footer_url is not None:
                page_num_args += ['--footer-html', footer_url]
            if header_url is not None:
                page_num_args += ['--header-html', header_url]

        greyscale_args = ['-g'] * self.grey_scale
        quiet_args = ['-q']
        cmd = ([config.WKHTMLTOPDF] +
               quiet_args +
               ['--page-width', str(self.width * POINT_2_MM),
                '--page-height', str(self.height * POINT_2_MM),
                '-T', m[0], '-R', m[1], '-B', m[2], '-L', m[3],
                #'--disable-smart-shrinking',
                '-d', '100',
                #'--zoom', '1.2',
                '--encoding', 'UTF-8',
                '--javascript-delay', '2000',
                ] +
               page_num_args +
               outline_args +
               greyscale_args +
               config.WKHTMLTOPDF_EXTRA_COMMANDS +
               [html_url, pdf])
        log(' '.join(cmd))
        return cmd


    def make_raw_pdf(self, html, pdf, outline=False, outline_file=None, page_num=None):
        if self.columns == 1:
            html_url = path2url(html)
            func = getattr(self, '_%s_command' % self.engine)
            cmd = func(html_url, pdf, outline=outline, outline_file=outline_file, page_num=page_num)
            run(cmd)
        else:
            #For multiple columns, generate a narrower single column pdf, and
            #paste it into columns using pdfnup.
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

            columnmaker = PageSettings(self.workdir, (page_width, self.height),
                                       gutter=0, top_margin=self.top_margin,
                                       side_margin=side_margin,
                                       bottom_margin=self.bottom_margin,
                                       grey_scale=self.grey_scale,
                                       engine=self.engine
                                       )

            column_pdf = pdf[:-4] + '-single-column.pdf'
            columnmaker.make_raw_pdf(html, column_pdf, outline=outline,
                                     outline_file=outline_file, page_num=None)
            columnmaker.reshape_pdf(column_pdf)

            # pdfnup seems to round down to an even number of output
            # pages.  For example, if a book fills 13 pages, it will
            # clip it to 12.  So it is necessary to add blank pages to
            # round it up to an even number of output pages, which is
            # to say a multiple of (self.columns * 2) input pages.

            column_pages = count_pdf_pages(column_pdf)
            overflow_pages = column_pages % (self.columns * 2)
            if overflow_pages:
                extra_pages = self.columns * 2 - overflow_pages
            else:
                extra_pages = 0

            cmd = [config.PDFNUP,
                   '--nup', '%sx1' % int(self.columns),
                   #'--paper', papersize.lower() + 'paper',
                   '--outfile', pdf,
                   '--noautoscale', 'true',
                   '--orient', 'portrait',
                   '--paperwidth', '%smm' % int(self.width * POINT_2_MM),
                   '--paperheight', '%smm' % int(self.height * POINT_2_MM),
                   #'--tidy', 'false',
                   '--pages', '1-last%s' % (',{}' * extra_pages,),
                   #'--columnstrict', 'true',
                   #'--column', 'true',
                   column_pdf
                   ]

            run(cmd)



    def reshape_pdf(self, pdf, dir=config.DEFAULT_DIR, centre_start=False,
                    centre_end=False, even_pages=True):
        """Spin the pdf for RTL text, resize it to the right size, and
        shift the gutter left and right"""
        ops = []
        if self.gutter:
            ops.append('shift')
        if even_pages:
            ops.append('even_pages')
        gutter = self.gutter
        if dir == 'RTL':
            gutter = -gutter
        if not ops:
            return

        os.putenv("OBJAVI_SCRIPT_DIR", config.SCRIPT_DIR)

        cmd = ['pdfedit', '-s', '%s/wk_objavi.qs' % config.SCRIPT_DIR,
               'dir=%s' % dir,
               'filename=%s' % pdf,
               'output_filename=%s' % pdf,
               'operation=%s' % ','.join(ops),
               'width=%s' % self.width,
               'height=%s' % self.height,
               'offset=%s' % gutter,
               'centre_start=%s' % centre_start,
               'centre_end=%s' % centre_end,
               ]
        run(cmd)


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

    def calculate_cover_size(self, api_key, booksize, page_count):
        import lulu
        return lulu.calculate_cover_size(api_key, booksize, page_count)

    def make_cover_pdf(self, html_path, pdf_path):
        width = self.width * POINT_2_MM
        height = self.height * POINT_2_MM
        args = [
            "-T", "0",
            "-B", "0",
            "-L", "0",
            "-R", "0",
            "--page-width",  repr(width),
            "--page-height", repr(height),
        ]
        cmd = [config.WKHTMLTOPDF] + args + [html_path, pdf_path]
        run(cmd)


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

def concat_pdfs_gs(destination, *pdfs):
    """Concatenate all the named PDFs."""
    cmd  = ['gs']
    cmd += ['-dBATCH', '-dNOPAUSE', '-sDEVICE=pdfwrite']
    cmd += ['-sOutputFile=%s' % destination, '-f']
    cmd.extend(x for x in pdfs if x is not None)
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
    '''Extract outline data from an XML file structured as follows:

      <?xml version="1.0" encoding="UTF-8"?>
      <outline xmlns="http://code.google.com/p/wkhtmltopdf/outline">
        <item title="" page="0" link="__WKANCHOR_0" backLink="__WKANCHOR_1">
          <item title="1. ANONYMOUS" page="2" link="__WKANCHOR_2" backLink="__WKANCHOR_3"/>
          <item title="2. HOW THIS BOOK IS WRITTEN" page="4" link="__WKANCHOR_4" backLink="__WKANCHOR_5">
            <item title="WHAT IS A BOOK SPRINT?" page="4" link="__WKANCHOR_6" backLink="__WKANCHOR_7"/>
            <item title="HOW TO WRITE THIS BOOK" page="11" link="__WKANCHOR_c" backLink="__WKANCHOR_d">
              <item title="1. Register" page="11" link="__WKANCHOR_e" backLink="__WKANCHOR_f"/>
              <item title="2. Contribute!" page="11" link="__WKANCHOR_g" backLink="__WKANCHOR_h"/>
            </item>
          </item>
          <item title="3. ASSUMPTIONS" page="13" link="__WKANCHOR_i" backLink="__WKANCHOR_j">
            <item title="WHAT THIS BOOK IS NOT..." page="13" link="__WKANCHOR_k" backLink="__WKANCHOR_l"/>
          </item>
        </item>
      </outline>

     In other words:

     <!ELEMENT outline (item*)>
     <!ELEMENT item (item*)>
     and item has the following attributes:
       title:    url-escaped string
       page:     page number
       link:     link to here from the TOC
       backLink: link back to the TOC

    Title is encoded as utf-8 text that has been "percent-encoding" as
    described in section 2.1 of RFC 3986.
    '''
    from lxml import etree
    f = open(outline_file, 'r')
    tree = etree.parse(f)
    f.close()

    contents = []

    def parse_item(e, depth):
        title = urllib.unquote(e.get('title')).strip()
        pageno = int(e.get('page'))
        if depth:
            contents.append((title, depth, pageno))
        for x in e.iterchildren(config.WKTOCNS + 'item'):
            parse_item(x, depth + 1)

    for x in tree.getroot().iterchildren(config.WKTOCNS + 'item'):
        parse_item(x, 0)

    log(contents)
    return contents



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

def embed_all_fonts(pdf_file):
    tmp_file = pdf_file + '.pre-embed.pdf'
    os.rename(pdf_file, tmp_file)
    cmd = ['gs', '-q',                  # no messages to stdout
           '-dSAFER',                   # read-only
           '-dNOPLATFONTS',             # no platform fonts
           '-dNOPAUSE',                 # don't prompt user
           '-dBATCH',                   # ? undocumented
           '-sDEVICE=pdfwrite',
           #'-sPAPERSIZE=letter',
           '-dCompatibilityLevel=1.4',  # pdf v4
           '-dPDFSETTINGS=/printer',    # "printer optimised" pdf
           '-dMaxSubsetPct=100',        # Always use a subset font
           '-dSubsetFonts=false',       # never use a subset font (overrides above)
           '-dEmbedAllFonts=true',      # As it says
           #'-sOutputFile=-',           # write to stdout
           '-sOutputFile=%s' %(pdf_file), # write to file
           #could also use -dPDFX to make PDF/X3
           #'-f',                        # ?
           '--',
           ] + [tmp_file]
    run(cmd)

def resize_pdf(pdf, width, height):
    ops = ["resize"]

    cmd = ["pdfedit",
           "-s", "scripts/wk_objavi.qs",
           'filename=%s' % pdf,
           'output_filename=%s' % pdf,
           'operation=%s' % ','.join(ops),
           'width=%s' % width,
           'height=%s' % height,
    ]

    run(cmd)
    
