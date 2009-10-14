# Part of Objavi2, which makes pdf versions of FLOSSManuals books.
# This python module contains or encapsulates configuration and
# constant data.
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

"""This module contains constant values used to produce books.
"""
#XXX eventually, read in a real config file.
#XXX Some of these values should be editable via an admin cgi script

#Not really configurable (72 pt per inch / 25.4 mm per inch)
POINT_2_MM = 25.4 / 72.0
MM_2_POINT = 72.0 / 25.4
INCH_2_POINT = 72

KEEP_TEMP_FILES=True
TMPDIR = 'tmp'

EPUB_DIR = 'books'
BOOKI_BOOK_DIR = 'booki-books'

FIREFOX = 'firefox'
WKHTMLTOPDF = '/usr/local/bin/wkhtmltopdf-static'
WKHTMLTOPDF_EXTRA_COMMANDS = []
#WKHTMLTOPDF_EXTRA_COMMANDS = ['--outline',  '-t']
HTML2ODT = './html2odt'


#CGITB_DOMAINS = ('203.97.236.46', '202.78.240.7')
CGITB_DOMAINS = False

#bookland is used to make isbn barcodes
BOOKLAND = 'bookland/bookland'

# how many pages to number in one pdfedit process (which has
# exponential memory leak)
PDFEDIT_MAX_PAGES = 40

#keep book lists around for this time without refetching
BOOK_LIST_CACHE = 3600 * 2
BOOK_LIST_CACHE_DIR = 'cache'

TOC_URL = "http://%s/pub/%s/_index/TOC.txt"
BOOK_URL = "http://%s/bin/view/%s/_all?skin=text"
CHAPTER_URL = "http://%s/bin/view/%s/%s?skin=text"
PUBLISH_URL = "/books/"

TWIKI_GATEWAY_URL = 'http://%s/booki-twiki-gateway.cgi?server=%s&book=%s&mode=zip'
BOOKI_ZIP_URL = 'http://%s/export/%s'

#leave out vowels so as to avoid accidental words, and punctuation for bidi consistency
CHAPTER_COOKIE_CHARS = 'BCDFGHJKLMNPQRSTVWXYZ'

DEFAULT_SERVER = 'en.flossmanuals.net'
BOOKI_SERVER = 'booki.flossmanuals.net'
DEFAULT_SIZE = 'COMICBOOK'
DEFAULT_ENGINE = 'webkit'
#DEFAULT_MODE = None

RTL_SCRIPTS = ['persian', 'arabic', 'hebrew', 'urdu']

USE_CACHED_IMAGES = False

USE_TAGS_FOR_CONTENTS = False

TRY_BOOK_CLEANUP_ON_DEL = False

LOCALHOST = 'localhost'

SERVER_DEFAULTS = {
    'booki-dev.flossmanuals.net:8080': {
        'css-book': 'static/en.flossmanuals.net.css',
        'css-web': 'static/en.flossmanuals.net-web.css',
        'css-newspaper': 'static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': 'static/en.flossmanuals.net-openoffice.css',
        'lang': 'en',
        'dir': 'LTR',
        'display': False,
        'interface': 'Booki',
        },
    'booki.flossmanuals.net': {
        'css-book': 'static/en.flossmanuals.net.css',
        'css-web': 'static/en.flossmanuals.net-web.css',
        'css-newspaper': 'static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': 'static/en.flossmanuals.net-openoffice.css',
        'lang': 'en',
        'dir': 'LTR',
        'display': False,
        'interface': 'Booki',
        },
    LOCALHOST: {
        'css-book': 'static/en.flossmanuals.net.css',
        'css-web': 'static/en.flossmanuals.net-web.css',
        'css-newspaper': 'static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': 'static/en.flossmanuals.net-openoffice.css',
        'lang': 'en',
        'dir': 'LTR',
        'display': False,
        'interface': 'local',
        },
    'en.flossmanuals.net': {
        'css-book': 'static/en.flossmanuals.net.css',
        'css-web': 'static/en.flossmanuals.net-web.css',
        'css-newspaper': 'static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': 'static/en.flossmanuals.net-openoffice.css',
        'lang': 'en',
        'dir': 'LTR',
        'display': True,
        'interface': 'TWiki',
        },
    'fr.flossmanuals.net': {
        'css-book': 'static/fr.flossmanuals.net.css',
        'css-web': 'static/fr.flossmanuals.net-web.css',
        'css-newspaper': 'static/fr.flossmanuals.net-newspaper.css',
        'css': 'static/fr.flossmanuals.net.css',
        'css-openoffice': 'static/fr.flossmanuals.net-openoffice.css',
        'lang': 'fr',
        'dir': 'LTR',
        'display': True,
        'interface': 'TWiki',
        },
    'translate.flossmanuals.net': {
        'css-book': 'static/translate.flossmanuals.net.css',
        'css-web': 'static/translate.flossmanuals.net-web.css',
        'css-newspaper': 'static/translate.flossmanuals.net-newspaper.css',
        'css': 'static/translate.flossmanuals.net.css',
        'css-openoffice': 'static/translate.flossmanuals.net-openoffice.css',
        'lang': 'translate',
        'dir': 'LTR',
        'display': True,
        'interface': 'TWiki',
        },
    'nl.flossmanuals.net': {
        'css-book': 'static/nl.flossmanuals.net.css',
        'css-web': 'static/nl.flossmanuals.net-web.css',
        'css-newspaper': 'static/nl.flossmanuals.net-newspaper.css',
        'css': 'static/nl.flossmanuals.net.css',
        'css-openoffice': 'static/nl.flossmanuals.net-openoffice.css',
        'lang': 'nl',
        'dir': 'LTR',
        'display': True,
        'interface': 'TWiki',
        },
    'bn.flossmanuals.net': {
        'css-book': 'static/bn.flossmanuals.net.css',
        'css-web': 'static/bn.flossmanuals.net-web.css',
        'css-newspaper': 'static/bn.flossmanuals.net-newspaper.css',
        'css': 'static/bn.flossmanuals.net.css',
        'css-openoffice': 'static/bn.flossmanuals.net-openoffice.css',
        'lang': 'bn',
        'dir': 'LTR',
        'display': True,
        'interface': 'TWiki',
        },
    'fa.flossmanuals.net': {
        'css-book': 'static/fa.flossmanuals.net.css',
        'css-web': 'static/fa.flossmanuals.net-web.css',
        'css-newspaper': 'static/fa.flossmanuals.net-newspaper.css',
        'css': 'static/fa.flossmanuals.net.css',
        'css-openoffice': 'static/fa.flossmanuals.net-openoffice.css',
        'lang': 'fa',
        'dir': 'RTL',
        'display': True,
        'interface': 'TWiki',
        },
}

# uncomment a debug mode to get messages about that topic.
DEBUG_MODES = (
    #'STARTUP',
    #'INDEX',
    #'PDFEDIT',
    #'PDFGEN',
    #'HTMLGEN',
    )
DEBUG_ALL = False

#convert all sizes to points
PAPER_SIZES = [(s, x * MM_2_POINT, y * MM_2_POINT) for s, x, y in  (
    ("A5", 148, 210),
    #("B5", 176, 250),
    ("A4", 210, 297),
    #("B4", 250, 353),
    ("A3", 297, 420),
    #("B3", 353, 500),
    ("A2", 420, 594),
    #("B2", 500, 707),
    ("A1", 594, 841),
    #("B1", 707, 1000),
    ("A0", 841, 1189),
    ("B0", 1000, 1414),
)]

# margins are BASE_MARGIN + PROPORTIONAL_MARGIN * min(width, height)
BASE_MARGIN = 22
PROPORTIONAL_MARGIN = 0.04
# gutter is BASE_GUTTER + PROPORTIONAL_GUTTER * width
BASE_GUTTER = 15
PROPORTIONAL_GUTTER = 0.011

PAGE_EXTREMA = {
    'page_width':  (1, 1000, MM_2_POINT),
    'page_height': (1, 1414, MM_2_POINT), #can't be bigger than biggest PAPER_SIZE
    'gutter': (-1000, 1000, MM_2_POINT),
    'top_margin': (0, 1500, MM_2_POINT),
    'side_margin': (0, 1500, MM_2_POINT),
    'bottom_margin': (0, 1500, MM_2_POINT),
    "columns": (1, 12, 1),
    "column_margin": (0, 1000, MM_2_POINT),
}

PAGE_NUMBER_SIZE = 11 #XXX this is not used by pdfedit! (ie, it is a guess)

PAGE_SIZE_DATA = {
    'COMICBOOK':      {'pointsize': ((6.625 * 72), (10.25 * 72)), 'class': "lulu"},
    "POCKET":         {'pointsize': (4.25 * 72, 6.875 * 72), 'class': "lulu"},

    "USLETTER":       {'pointsize': (8.5 * 72, 11 * 72), 'class': "lulu"},
    "USTRADE":        {'pointsize': (6 * 72, 9 * 72), 'class': "lulu"},
    "LANDSCAPE9x7":   {'pointsize': (9 * 72, 7 * 72), 'class': "lulu"},
    "SQUARE7.5":      {'pointsize': (7.5 * 72, 7.5 * 72), 'class': "lulu"},
    "ROYAL":          {'pointsize': (6.139 * 72, 9.21 * 72), 'class': "lulu"},
    "CROWNQUARTO":    {'pointsize': (7.444 * 72, 9.681 * 72), 'class': "lulu"},
    "SQUARE8.5":      {'pointsize': (8.5 * 72, 8.5 * 72), 'class': "lulu"},

    "A5":             {'pointsize': (148 * MM_2_POINT, 210 * MM_2_POINT), 'class': "lulu iso"},
    "A4":             {'pointsize': (210 * MM_2_POINT, 297 * MM_2_POINT), 'class': "lulu iso"},
    "A3 (NZ Tabloid)": {'pointsize': (297 * MM_2_POINT, 420 * MM_2_POINT), 'class': 'iso newspaper'},
    "A2 (NZ Broadsheet)": {'pointsize': (420 * MM_2_POINT, 594 * MM_2_POINT), 'class': 'iso newspaper'},
    "A1":             {'pointsize': (594 * MM_2_POINT, 841 * MM_2_POINT), 'class': 'iso'},
    "B4":             {'pointsize': (250 * MM_2_POINT, 353 * MM_2_POINT), 'class': 'iso'},
    "B3":             {'pointsize': (353 * MM_2_POINT, 500 * MM_2_POINT), 'class': 'iso'},
    "B2":             {'pointsize': (500 * MM_2_POINT, 707 * MM_2_POINT), 'class': 'iso'},
    "B1":             {'pointsize': (707 * MM_2_POINT, 1000 * MM_2_POINT), 'class': 'iso'},

    "UK Tabloid":     {'pointsize': (11 * INCH_2_POINT, 17 * INCH_2_POINT), 'class': 'newspaper'},
    "UK Broadsheet":  {'pointsize': (18 * INCH_2_POINT, 24 * INCH_2_POINT), 'class': 'newspaper'},
    "US Broadsheet":  {'pointsize': (15 * INCH_2_POINT, 22.75 * INCH_2_POINT), 'class': 'newspaper'},
    "Berliner"     :  {'pointsize': (315 * MM_2_POINT, 470 * MM_2_POINT), 'class': 'newspaper'},
    "Foolscap (F4)":  {'pointsize': (210 * MM_2_POINT, 330 * MM_2_POINT)},

    "Oamaru Broadsheet":{'pointsize': (382 * MM_2_POINT, 540 * MM_2_POINT), 'class': 'newspaper'},
    "Oamaru Tabloid": {'pointsize': (265 * MM_2_POINT, 380 * MM_2_POINT), 'class': 'newspaper'},

    #ODT printable 380x560
    #Aucklander 360x260
    #Dominion 376x540

    "custom":         {'class': "custom"},
}

PAGE_MIN_SIZE = (1.0, 1.0)
PAGE_MAX_SIZE = (3000.0, 3000.0)

MIN_COLUMN_WIDTH = (110 * MM_2_POINT)

ENGINES = {
    'webkit' : [],
    #'gecko' : [],
}

INSIDE_FRONT_COVER_TEMPLATE = 'templates/inside-front-cover.%s.html'
END_MATTER_TEMPLATE = 'templates/end_matter.%s.html'

FONT_LIST_INCLUDE = 'cache/font-list.inc'
FONT_LIST_URL = '/font-list.cgi.pdf'
FONT_EXAMPLE_SCRIPT_DIR = 'templates/font-list'

# for the license field, with a view to making it a drop down.
LICENSES = {
    'GPL': 'http://www.gnu.org/licenses/gpl.txt',
    'GPLv2': 'http://www.gnu.org/licenses/gpl-2.0.txt',
    'GPLv2+': 'http://www.gnu.org/licenses/gpl-2.0.txt',
    'GPLv3': 'http://www.gnu.org/licenses/gpl-3.0.txt',
    'GPLv3+': 'http://www.gnu.org/licenses/gpl-3.0.txt',
    'LGPL': 'http://www.gnu.org/licenses/lgpl.txt',
    'LGPLv2.1': 'http://www.gnu.org/licenses/lgpl-2.1.txt',
    'LGPLv3': 'http://www.gnu.org/licenses/lgpl-3.0.txt',
    'BSD': 'http://www.debian.org/misc/bsd.license',
    'public domain': None,
    'MIT': 'http://www.opensource.org/licenses/mit-license.html',
    'Artistic': 'http://dev.perl.org/licenses/artistic.html',
    'CC-BY': 'http://creativecommons.org/licenses/by/3.0/',
    'CC-BY-SA': 'http://creativecommons.org/licenses/by-sa/3.0/',
}

DEFAULT_LICENSE = 'GPLv2+'

CGI_MODES = { # arguments are: (publication, )
    'book': (True,),
    'newspaper': (True,),
    'web': (True,),
    'openoffice': (True,),
    'booklist': (False,),
    'css': (False,),
    'form': (False,),
    'epub':(True,),
}
DEFAULT_MODE = 'book'

EPUB_DESTINATIONS = {
    'archive.org': None,
    'download': None,
    'html': None,
}
DEFAULT_EPUB_DESTINATION = 'html'


FORM_INPUTS = (
    # input, name, input type, contents key, CSS classes, extra text
    ("server", "FLOSS Manuals server", "select", "server_options", "", ""),
    ("book", "Manual", "select", "book_options", "", ""),
    ("title", "Book title", "input[type=text]", None, "", ""),
    ("license", "License", "select", "licenses", "", ""),

    ("mode", "Document type", "select", "pdf_types", "advanced openoffice", ""),
    ("isbn", "ISBN", "input[type=text]", None, "advanced", "(13 digits)"),

    ("booksize", "Page size", "select", "size_options", "advanced", '(Size compatibility: <span class="lulu">Lulu</span>, <span class="newspaper">newspapers</span>, <span class="iso">ISO standards</span>)'),
    ("page_width", "Page width", "input[type=text]", None, "advanced booksize numeric-field", ""),
    ("page_height", "Page height", "input[type=text]", None, "advanced booksize numeric-field", ""),

    ("top_margin", "Top margin", "input[type=text]", None, "advanced margins numeric-field", ""),
    ("side_margin", "Side margin", "input[type=text]", None, "advanced margins numeric-field", ""),
    ("bottom_margin", "Bottom margin", "input[type=text]", None, "advanced margins numeric-field", ""),
    ("gutter", "Gutter", "input[type=text]", None, "advanced margins numeric-field", ""),

    ("columns", "Columns", "input[type=text]", None, "advanced columns numeric-field", ""),
    ("column_margin", "Column margin", "input[type=text]", None, "advanced columns numeric-field", ""),

    ("grey_scale", "Grey-scale", "input[type=checkbox]", 'yes', "advanced", "(for black and white printing)"),

    #("css_customise", "Customise CSS", "input[type=checkbox]", None, "advanced", "Enter a URL or "),
    ("css-url", "CSS URL", "input[type=text][disabled]", "css_url", "advanced css-url openoffice", ""),
    ("font_list", "Available fonts", "ul", "font_list", "advanced css-custom openoffice", ""),
    ("font_links", "Font examples", "ul", "font_links", "advanced css-custom openoffice", ""),
    ("css", "CSS", "textarea", "css", "advanced css-custom openoffice", ""),

    ("rotate", "Rotate pages for binding", "input[type=checkbox]", 'yes', "advanced", "(for RTL books on LTR printing presses, and vice versa)."),
    #("engine", "Layout engine", "select", "engines", "advanced", ""),
    #("header", "Header Text", "input[type=text]", None, "advanced", ""),
)

FORM_ELEMENT_TYPES = {
    'input[type=text]' : '<input type="text" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'input[type=text][disabled]' : '<input type="text" disabled="disabled" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'input[type=checkbox]' : '<input type="checkbox" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'textarea' : '<textarea id="%(id)s" name="%(id)s">%(val)s</textarea>',
    'select': '<select id="%(id)s" name="%(id)s">%(val)s</select>',
    'ul': '<ul id="%(id)s">%(val)s</ul>',
}

PROGRESS_POINTS = (
    ("__init__", "Initialise the book", ('book', 'newspaper', 'web', 'openoffice', 'epub')),
    ("load_book", "Fetch the book", ('book', 'newspaper', 'web', 'openoffice')),
    ("load_toc", "Fetch TOC metadata", ('book', 'newspaper', 'web', 'openoffice')),
    ("add_css", "Add css", ('book', 'newspaper', 'web', 'openoffice')),
    ("add_section_titles", "Add section titles", ('book', 'newspaper', 'web', 'openoffice')),
    ("make_epub", "Make the epub file", ('epub',)),
    ("make_oo_doc", "Make the OpenOffice document", ('openoffice',)),
    ("generate_pdf", "Generate the main pdf", ('book', 'newspaper', 'web')),
    ("extract_pdf_outline", "Find page numbers", ('book',)),
    ("reshape_pdf", "Cut pages to size", ('book', 'newspaper',)),
    #('make_body_pdf', "Generate the main pdf", ('book', 'newspaper', 'web')),
    ("number_pdf", "Number pages", ('book', 'newspaper',)),
    ("make_contents", "Calculate Table of Contents", ('book',)),
    ("make_preamble_pdf", "Generate preamble pdf", ('book',)),
    ('make_end_matter_pdf', "Generate end matter pdf", ('book',)),
    ("concatenated_pdfs", "concatenate the pdfs", ('book',)),
    #("publish_pdf", "Publish the pdf", ('book', 'newspaper', 'web')),
    ("finished", "Finished!", ('book', 'newspaper', 'web', 'openoffice', 'epub')),
)

#XML namespace stuff
DCNS = "{http://purl.org/dc/elements/1.1/}"
DC = "http://purl.org/dc/elements/1.1/"
XHTMLNS = '{http://www.w3.org/1999/xhtml}'
XHTML = 'http://www.w3.org/1999/xhtml'










if __name__ == '__main__':
    print ', '.join(x for x in globals().keys() if not x.startswith('_'))
