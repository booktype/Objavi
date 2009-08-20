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

FIREFOX = 'firefox'
WKHTMLTOPDF = '/usr/local/bin/wkhtmltopdf-static'
WKHTMLTOPDF_EXTRA_COMMANDS = []
#WKHTMLTOPDF_EXTRA_COMMANDS = ['--outline',  '-t']

# how many pages to number in one pdfedit process (which has
# exponential memory leak)
PDFEDIT_MAX_PAGES = 40

#keep book lists around for this time without refetching
BOOK_LIST_CACHE = 3600 * 2
BOOK_LIST_CACHE_DIR = 'cache'

TOC_URL = "http://%s/pub/%s/_index/TOC.txt"
BOOK_URL = "http://%s/bin/view/%s/_all?skin=text"
PUBLISH_URL = "/books/"

#leave out vowels so as to avoid accidental words, and punctuation for bidi consistency
CHAPTER_COOKIE_CHARS = 'BCDFGHJKLMNPQRSTVWXYZ'

DEFAULT_SERVER = 'en.flossmanuals.net'
DEFAULT_SIZE = 'COMICBOOK'
DEFAULT_ENGINE = 'webkit'
#DEFAULT_MODE = None

RTL_SCRIPTS = ['persian', 'arabic', 'hebrew', 'urdu']

#DEFAULT_CSS = 'file://' + os.path.abspath('static/default.css')
SERVER_DEFAULTS = {
    'en.flossmanuals.net': {
        'css': 'static/en.flossmanuals.net.css',
        'lang': 'en',
        'dir': 'LTR',
        },
    'fr.flossmanuals.net': {
        'css': 'static/fr.flossmanuals.net.css',
        'lang': 'fr',
        'dir': 'LTR',
        },
    'translate.flossmanuals.net': {
        'css': 'static/translate.flossmanuals.net.css',
        'lang': 'translate',
        'dir': 'LTR',
        },
    'nl.flossmanuals.net': {
        'css': 'static/nl.flossmanuals.net.css',
        'lang': 'nl',
        'dir': 'LTR',
        },
    'bn.flossmanuals.net': {
        'css': 'static/bn.flossmanuals.net.css',
        'lang': 'bn',
        'dir': 'LTR',
        },
    'fa.flossmanuals.net': {
        'css': 'static/fa.flossmanuals.net.css',
        'lang': 'fa',
        'dir': 'RTL',
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
    'page_width':  (1, 3000, MM_2_POINT),
    'page_height': (1, 3000, MM_2_POINT),
    'gutter': (-1000, 1000, MM_2_POINT),
    'top_margin': (0, 1500, MM_2_POINT),
    'side_margin': (0, 1500, MM_2_POINT),
    'bottom_margin': (0, 1500, MM_2_POINT),
    "columns": (1, 20, 1),
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
    #"Foolscap Folio": {'pointsize': (8.5 * INCH_2_POINT, 13.5 * INCH_2_POINT)},

    "custom":         {'class': "custom"},
}

PAGE_MIN_SIZE = (1.0, 1.0)
PAGE_MAX_SIZE = (3000.0, 3000.0)

ENGINES = {
    'webkit' : [],
    #'gecko' : [],
}

FONT_LIST_INCLUDE = 'cache/font-list.inc'
FONT_LIST_URL = '/font-list.cgi.pdf'
FONT_EXAMPLE_SCRIPT_DIR = 'templates/font-list'

# for the license field, with a view to making it a drop down.
LICENSES = ('GPL', 'GPLv2', 'GPLv2+', 'GPLv3', 'GPLv3+', 'LGPL', 'LGPLv2.1',
            'BSD', 'public domain', 'MIT', 'Artistic', 'CC-BY', 'CC-BY-SA')

DEFAULT_LICENSE = 'GPLv2+'

FORM_INPUTS = (
    ("server", "FLOSS Manuals server", "select", "server_options", "", ""),
    ("webName", "Manual", "select", "book_options", "", ""),
    ("title", "Book title", "input[type=text]", None, "", ""),
    ("license", "License", "select", "licenses", "", ""),

    ("isbn", "ISBN", "input[type=text]", None, "advanced", "(13 digits)"),
    ("rotate", "Rotate pages for binding", "input[type=checkbox]", None, "advanced", "(for RTL books on LTR printing presses, and vice versa)."),
    ("engine", "Layout engine", "select", "engines", "advanced", ""),    
    #("header", "Header Text", "input[type=text]", None, "advanced", ""),
    
    ("booksize", "Page size", "select", "size_options", "advanced", ""),
    ("page_width", "Page width", "input[type=text]", None, "advanced booksize numeric-field", ""),
    ("page_height", "Page height", "input[type=text]", None, "advanced booksize numeric-field", ""),

    ("top_margin", "Top margin", "input[type=text]", None, "advanced margins numeric-field", ""),
    ("side_margin", "Side margin", "input[type=text]", None, "advanced margins numeric-field", ""),
    ("bottom_margin", "Bottom margin", "input[type=text]", None, "advanced margins numeric-field", ""),
    ("gutter", "Gutter", "input[type=text]", None, "advanced margins numeric-field", ""),

    ("columns", "Columns", "input[type=text]", None, "advanced columns numeric-field", ""),
    ("column_margin", "Column margin", "input[type=text]", None, "advanced columns numeric-field", ""),

    #("css_customise", "Customise CSS", "input[type=checkbox]", None, "advanced", "Enter a URL or "),
    ("css-url", "CSS URL", "input[type=text][disabled]", "css_url", "advanced css-url", ""),
    ("font_list", "Available fonts", "ul", "font_list", "advanced css-custom", ""),
    ("font_links", "Font examples", "ul", "font_links", "advanced css-custom", ""),
    ("css", "CSS", "textarea", "css", "advanced css-custom", ""),
)

FORM_ELEMENT_TYPES = {
    'input[type=text]' : '<input type="text" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'input[type=text][disabled]' : '<input type="text" disabled="disabled" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'input[type=checkbox]' : '<input type="checkbox" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'textarea' : '<textarea id="%(id)s" name="%(id)s">%(val)s</textarea>',
    'select': '<select id="%(id)s" name="%(id)s">%(val)s</select>',
    'ul': '<ul id="%(id)s" name="%(id)s">%(val)s</ul>',
}



if __name__ == '__main__':
    print ', '.join(x for x in globals().keys() if not x.startswith('_'))
