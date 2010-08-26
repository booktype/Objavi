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
from os import environ as _environ
#XXX eventually, read in a real config file.
#XXX Some of these values should be editable via an admin cgi script

#cgi scripts chdir here to escape htdocs
BASEDIR = ".."

#Not really configurable (72 pt per inch / 25.4 mm per inch)
POINT_2_MM = 25.4 / 72.0
MM_2_POINT = 72.0 / 25.4
INCH_2_POINT = 72

KEEP_TEMP_FILES = True
TMPDIR = 'htdocs/tmp'

LOGDIR = 'log'
REDIRECT_LOG = True
LOG_ROTATE_SIZE = 1000000

SHOW_BOOKI_SERVERS = bool(_environ.get("SHOW_BOOKI_SERVERS", False))

HTDOCS = 'htdocs'
BOOKI_BOOK_DIR = 'htdocs/booki-books'
BOOKI_BOOK_URL = '/booki-books'

BOOKI_SHARED_DIRECTORY = 'htdocs/shared'
BOOKI_SHARED_LONELY_USER_PREFIX = 'lonely-user-'

WKHTMLTOPDF = '/usr/local/bin/wkhtmltopdf-static'
WKHTMLTOPDF_EXTRA_COMMANDS = []

#use hacked version of wkhtmltopdf that writes outline to a file
USE_DUMP_OUTLINE = True
CONTENTS_DEPTH = 1

HTML2ODT = 'bin/html2odt'

#CGITB_DOMAINS = ('203.97.236.46', '202.78.240.7')
CGITB_DOMAINS = False

#bookland is used to make isbn barcodes
BOOKLAND = 'bookland/bookland'

# how many pages to number in one pdfedit process (which has
# exponential memory leak)
PDFEDIT_MAX_PAGES = 20

#maximum memory for objavi.cgi
OBJAVI_CGI_MEMORY_LIMIT = 600 * 1024 * 1024

#keep book lists around for this time without refetching
BOOK_LIST_CACHE = 3600 * 2
CACHE_DIR = 'cache'

#for twiki import
TOC_URL = "http://%s/pub/%s/_index/TOC.txt"
CHAPTER_URL = "http://%s/bin/view/%s/%s?skin=text"

PUBLISH_DIR = 'htdocs/books'

HTML_PUBLISH_DIR = 'htdocs/published'
TEMPLATING_REPLACED_ELEMENT = 'content-goes-here'
TEMPLATING_MENU_ELEMENT = 'menu-goes-here'
TEMPLATING_BOOK_TITLE_ELEMENT = 'book-title-goes-here'
TEMPLATING_CHAPTER_TITLE_ELEMENT = 'chapter-title-goes-here'
TEMPLATING_CONTENTS_ID = 'main-content'
#TEMPLATING_DEFAULT_TEMPLATE = 'templates/templating_template.html'
TEMPLATING_DEFAULT_TEMPLATE = 'templates/templating_template_flossmanuals.html'

TEMPLATING_INDEX_FIRST = 'first'
TEMPLATING_INDEX_CONTENTS = 'contents'
TEMPLATING_INDEX_MODES = {  # contents file, first file
    TEMPLATING_INDEX_FIRST: ('contents.html', 'index.html'),
    TEMPLATING_INDEX_CONTENTS: ('index.html', None),
}

TAR_TEMPLATED_HTML = True

POLL_NOTIFY_PATH = 'htdocs/progress/%s.txt'
#POLL_NOTIFY_URL = 'http://%(HTTP_HOST)s/progress/%(bookname)s.txt'

ZIP_URLS = {
    'TWiki':   'http://%(HTTP_HOST)s/booki-twiki-gateway.cgi?server=%(server)s&book=%(book)s&mode=zip',
    'Booki':   'http://%(server)s/export/%(book)s/export',
    'Archive': 'http://%(HTTP_HOST)s/espri.cgi?mode=zip&book=%(book)s',
}

DEFAULT_DIR = 'LTR'

DEFAULT_SERVER = 'en.flossmanuals.net'
DEFAULT_BOOKI_SERVER = 'www.booki.cc'
DEFAULT_SIZE = 'COMICBOOK'
DEFAULT_ENGINE = 'webkit'

BOOKIZIP_MIMETYPE = "application/x-booki+zip"

RTL_SCRIPTS = ['persian', 'arabic', 'hebrew', 'urdu']

USE_CACHED_IMAGES = False

#Normally, Book objects try to shutdown subprocesses and clean up temp
#files when they __exit__.  This flag makes them try when they __del__
#too (i.e. when they are garbage collected).
TRY_BOOK_CLEANUP_ON_DEL = False

LOCALHOST = 'localhost'

LANGUAGE_CSS = {
    'en': {None: '/static/en.flossmanuals.net.css',
           'web': '/static/en.flossmanuals.net-web.css',
           'newspaper': '/static/en.flossmanuals.net-newspaper.css',
           'openoffice': '/static/en.flossmanuals.net-openoffice.css',
           },
    'my': {None: '/static/my.flossmanuals.net.css',}
}

SERVER_DEFAULTS = {
    'booki.flossmanuals.net': {
        'css-book': '/static/en.flossmanuals.net.css',
        'css-web': '/static/en.flossmanuals.net-web.css',
        'css-newspaper': '/static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': '/static/en.flossmanuals.net-openoffice.css',
        'lang': 'en',
        'dir': 'LTR',
        'toc-encoding': None,
        'display': False,
        'interface': 'Booki',
        'toc_header': 'Table of Contents',
        },
    'www.booki.cc': {
        'css-book': '/static/en.flossmanuals.net.css',
        'css-web': '/static/en.flossmanuals.net-web.css',
        'css-newspaper': '/static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': '/static/en.flossmanuals.net-openoffice.css',
        'lang': 'en',
        'dir': 'LTR',
        'toc-encoding': None,
        'display': True,
        'interface': 'Booki',
        'toc_header': 'Table of Contents',
        },
    'booki.halo.gen.nz': {
        'css-book': '/static/en.flossmanuals.net.css',
        'css-web': '/static/en.flossmanuals.net-web.css',
        'css-newspaper': '/static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': '/static/en.flossmanuals.net-openoffice.css',
        'lang': 'en',
        'dir': 'LTR',
        'toc-encoding': None,
        'display': SHOW_BOOKI_SERVERS,
        'interface': 'Booki',
        'toc_header': 'Table of Contents',
        },
    'archive.org': {
        'css-book': '/static/en.flossmanuals.net.css',
        'css-web': '/static/en.flossmanuals.net-web.css',
        'css-newspaper': '/static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': '/static/en.flossmanuals.net-openoffice.css',
        'lang': 'en',
        'dir': 'LTR',
        'toc-encoding': None,
        'display': False,
        'interface': 'Archive',
        'toc_header': 'Table of Contents',
        },
    LOCALHOST: {
        'css-book': '/static/en.flossmanuals.net.css',
        'css-web': '/static/en.flossmanuals.net-web.css',
        'css-newspaper': '/static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': '/static/en.flossmanuals.net-openoffice.css',
        'lang': 'en',
        'dir': 'LTR',
        'toc-encoding': 'iso-8859-1',
        'display': False,
        'interface': 'local',
        'toc_header': 'Table of Contents',
        },
    'en.flossmanuals.net': {
        'css-book': '/static/en.flossmanuals.net.css',
        'css-web': '/static/en.flossmanuals.net-web.css',
        'css-newspaper': '/static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': '/static/en.flossmanuals.net-openoffice.css',
        'lang': 'en',
        'dir': 'LTR',
        'toc-encoding': None,
        'display': True,
        'interface': 'TWiki',
        'toc_header': 'Table of Contents',
        },
    'fi.flossmanuals.net': {
        'css-book': '/static/en.flossmanuals.net.css',
        'css-web': '/static/en.flossmanuals.net-web.css',
        'css-newspaper': '/static/en.flossmanuals.net-newspaper.css',
        'css-openoffice': '/static/en.flossmanuals.net-openoffice.css',
        'lang': 'fi',
        'dir': 'LTR',
        'toc-encoding': None,
        'display': True,
        'interface': 'TWiki',
        'toc_header': 'Table of Contents',
        },
    'fr.flossmanuals.net': {
        'css-book': '/static/fr.flossmanuals.net.css',
        'css-web': '/static/fr.flossmanuals.net-web.css',
        'css-newspaper': '/static/fr.flossmanuals.net-newspaper.css',
        'css': '/static/fr.flossmanuals.net.css',
        'css-openoffice': '/static/fr.flossmanuals.net-openoffice.css',
        'lang': 'fr',
        'dir': 'LTR',
        'toc-encoding': 'iso-8859-1',
        'display': True,
        'interface': 'TWiki',
        'toc_header': 'Table of Contents',
        },
    'translate.flossmanuals.net': {
        'css-book': None, #'/static/translate.flossmanuals.net.css',
        'css-web': None, #'/static/translate.flossmanuals.net-web.css',
        'css-newspaper': None, #'/static/translate.flossmanuals.net-newspaper.css',
        'css': None, #'/static/translate.flossmanuals.net.css',
        'css-openoffice': None, #'/static/translate.flossmanuals.net-openoffice.css',
        'lang': None,
        'dir': 'auto',
        'toc-encoding': 'iso-8859-1',
        'display': True,
        'interface': 'TWiki',
        'toc_header': 'Table of Contents',
        },
    'nl.flossmanuals.net': {
        'css-book': '/static/nl.flossmanuals.net.css',
        'css-web': '/static/nl.flossmanuals.net-web.css',
        'css-newspaper': '/static/nl.flossmanuals.net-newspaper.css',
        'css': '/static/nl.flossmanuals.net.css',
        'css-openoffice': '/static/nl.flossmanuals.net-openoffice.css',
        'lang': 'nl',
        'dir': 'LTR',
        'toc-encoding': 'iso-8859-1',
        'display': True,
        'interface': 'TWiki',
        'toc_header': 'Table of Contents',
        },
    'bn.flossmanuals.net': {
        'css-book': '/static/bn.flossmanuals.net.css',
        'css-web': '/static/bn.flossmanuals.net-web.css',
        'css-newspaper': '/static/bn.flossmanuals.net-newspaper.css',
        'css': '/static/bn.flossmanuals.net.css',
        'css-openoffice': '/static/bn.flossmanuals.net-openoffice.css',
        'lang': 'bn',
        'dir': 'LTR',
        'toc-encoding': 'iso-8859-1',
        'display': True,
        'interface': 'TWiki',
        'toc_header': 'Table of Contents',
        },
    'fa.flossmanuals.net': {
        'css-book': '/static/fa.flossmanuals.net.css',
        'css-web': '/static/fa.flossmanuals.net-web.css',
        'css-newspaper': '/static/fa.flossmanuals.net-newspaper.css',
        'css': '/static/fa.flossmanuals.net.css',
        'css-openoffice': '/static/fa.flossmanuals.net-openoffice.css',
        'lang': 'fa',
        'dir': 'RTL',
        'toc-encoding': 'iso-8859-1',
        'display': True,
        'interface': 'TWiki',
        'toc_header': 'Table of Contents',
        },
}

#if 'www.booki.cc' in SERVER_DEFAULTS:
#    SERVER_DEFAULTS['booki.cc'] = SERVER_DEFAULTS['www.booki.cc']


LANGUAGE_DIR = {
    "ar": 'RTL',  # arabic (many variants)
    "dv": 'RTL',  # dhivehi, maldives islands
    "fa": 'RTL',  # farsi
    #"ha": 'RTL',  # hausa, west africa, particularly niger and nigeria
    "he": 'RTL',  # hebrew
    "ps": 'RTL',  # pashto
    "ur": 'RTL',  # urdu, pakistan
    "yi": 'RTL',  # yiddish, israel
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

# margins are BASE_MARGIN + PROPORTIONAL_MARGIN * min(width, height)
BASE_MARGIN = 22
PROPORTIONAL_MARGIN = 0.04
# gutter is BASE_GUTTER + PROPORTIONAL_GUTTER * width
BASE_GUTTER = 15
PROPORTIONAL_GUTTER = 0.011

PAGE_EXTREMA = {
    #Maximum sizes based on B0 paper.  There was once a good reason
    #for that, and there is no pressing need to change now (enough for
    #anyone, etc).
    'page_width':  (1, 1000, MM_2_POINT),
    'page_height': (1, 1414, MM_2_POINT),
    'gutter': (-1000, 1000, MM_2_POINT),
    'top_margin': (0, 1500, MM_2_POINT),
    'side_margin': (0, 1500, MM_2_POINT),
    'bottom_margin': (0, 1500, MM_2_POINT),
    "columns": (1, 12, 1),
    "column_margin": (0, 1000, MM_2_POINT),
}

PAGE_SIZE_DATA = {
    'COMICBOOK':      {'pointsize': ((6.625 * 72), (10.25 * 72)), 'class': "lulu"},
    "POCKET":         {'pointsize': (4.25 * 72, 6.875 * 72), 'class': "lulu"},

    "USLETTER":       {'pointsize': (8.5 * 72, 11 * 72), 'class': "lulu us"},
    "USTRADE6x9":     {'pointsize': (6 * 72, 9 * 72), 'class': "lulu us"},
    "LANDSCAPE9x7":   {'pointsize': (9 * 72, 7 * 72), 'class': "lulu us"},
    "SQUARE7.5":      {'pointsize': (7.5 * 72, 7.5 * 72), 'class': "lulu"},
    "ROYAL":          {'pointsize': (6.139 * 72, 9.21 * 72), 'class': "lulu us"},
    "CROWNQUARTO":    {'pointsize': (7.444 * 72, 9.681 * 72), 'class': "lulu us"},
    "SQUARE8.5":      {'pointsize': (8.5 * 72, 8.5 * 72), 'class': "lulu"},
    "US5.5x8.5":      {'pointsize': (5.5 * 72, 8.5 * 72), 'class': "us"},
    "US5x8":          {'pointsize': (5 * 72, 8 * 72), 'class': "us"},
    "US7x10":         {'pointsize': (7 * 72, 10 * 72), 'class': "us"},

    "A5":             {'pointsize': (148 * MM_2_POINT, 210 * MM_2_POINT), 'class': "lulu iso"},
    "A4":             {'pointsize': (210 * MM_2_POINT, 297 * MM_2_POINT), 'class': "lulu iso"},
    "A3 (NZ Tabloid)": {'pointsize': (297 * MM_2_POINT, 420 * MM_2_POINT), 'class': 'iso newspaper'},
    "A2 (NZ Broadsheet)": {'pointsize': (420 * MM_2_POINT, 594 * MM_2_POINT), 'class': 'iso newspaper'},
    "A1":             {'pointsize': (594 * MM_2_POINT, 841 * MM_2_POINT), 'class': 'iso'},
    "B5":             {'pointsize': (176 * MM_2_POINT, 250 * MM_2_POINT), 'class': 'iso'},
    "B4":             {'pointsize': (250 * MM_2_POINT, 353 * MM_2_POINT), 'class': 'iso'},
    "B3":             {'pointsize': (353 * MM_2_POINT, 500 * MM_2_POINT), 'class': 'iso'},
    "B2":             {'pointsize': (500 * MM_2_POINT, 707 * MM_2_POINT), 'class': 'iso'},
    "B1":             {'pointsize': (707 * MM_2_POINT, 1000 * MM_2_POINT), 'class': 'iso'},

    "UK Tabloid":     {'pointsize': (11 * INCH_2_POINT, 17 * INCH_2_POINT), 'class': 'newspaper'},
    "UK Broadsheet":  {'pointsize': (18 * INCH_2_POINT, 24 * INCH_2_POINT), 'class': 'newspaper'},
    "US Broadsheet":  {'pointsize': (15 * INCH_2_POINT, 22.75 * INCH_2_POINT), 'class': 'newspaper us'},
    "Berliner"     :  {'pointsize': (315 * MM_2_POINT, 470 * MM_2_POINT), 'class': 'newspaper'},
    "Foolscap (F4)":  {'pointsize': (210 * MM_2_POINT, 330 * MM_2_POINT)},

    "Oamaru Broadsheet":{'pointsize': (382 * MM_2_POINT, 540 * MM_2_POINT), 'class': 'newspaper'},
    "Oamaru Tabloid": {'pointsize': (265 * MM_2_POINT, 380 * MM_2_POINT), 'class': 'newspaper'},

    #ODT printable 380x560
    #Aucklander 360x260
    #Dominion 376x540

    "custom":         {'class': "custom"},
}

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

CGI_MODES = { # arguments are: (publication, extension, mimetype)
    'book': (True, '.pdf', "application/pdf"),
    'newspaper': (True, '.pdf', "application/pdf"),
    'web': (True, '.pdf', "application/pdf"),
    #XX stop openoffice for now: it doesn't work anyway
    #'openoffice': (True, '.odt', "application/vnd.oasis.opendocument.text"),
    'booklist': (False, None, None),
    'css': (False, None, None),
    'form': (False, None, None),
    'epub': (True, '.epub', "application/epub+zip"),
    'bookizip': (True, '.zip', BOOKIZIP_MIMETYPE),
    'templated_html':  (True, '', 'text/html'),
#    'templated_html_zip':  (True, '.zip', 'application/zip'),
}

PUBLIC_CGI_MODES = tuple(k for k, v in CGI_MODES.items() if v[0])

FORM_TEMPLATE = 'templates/form.html'
PROGRESS_ASYNC_TEMPLATE = 'templates/progress-async.html'
PROGRESS_TEMPLATE = 'templates/progress.html'
ASYNC_TEMPLATE = 'templates/async.txt'
ARCHIVE_TEMPLATE = 'templates/archive.txt'
NOWHERE_TEMPLATE = 'templates/nowhere.txt'

CGI_METHODS = ('sync', 'async', 'poll')

#used by objavi-async
CGI_DESTINATIONS = {
    'archive.org': {'sync': (ARCHIVE_TEMPLATE, 'text/plain; charset=utf-8'),
                    'async': (ARCHIVE_TEMPLATE, 'text/plain; charset=utf-8'),
                    'poll': (None, None),
                    'default': 'sync',
                    },
    'download': {'sync': (None, None),
                 'async': (ASYNC_TEMPLATE, 'text/plain; charset=utf-8'),
                 'poll': (None, None),
                 'default': 'sync',
                 },
    'html': {'sync': (PROGRESS_TEMPLATE, 'text/html; charset=utf-8'),
             'async': (ASYNC_TEMPLATE, 'text/plain; charset=utf-8'),
             'poll': (PROGRESS_ASYNC_TEMPLATE, 'text/html; charset=utf-8'),
             'default': 'sync',
             },
    'nowhere': {'sync': (NOWHERE_TEMPLATE, 'text/plain; charset=utf-8'),
                'async': (NOWHERE_TEMPLATE, 'text/plain; charset=utf-8'),
                'poll': (ASYNC_TEMPLATE, 'text/plain; charset=utf-8'),
                'default': 'sync',
                },
}

DEFAULT_CGI_DESTINATION = 'html'


FORM_INPUTS = (
    # input, name, input type, contents key, CSS classes, extra text
    ("server", "FLOSS Manuals server", "select", "server_options", "", ""),
    ("book", "Manual", "input[type=text]", "book_options", "", ""),
    ("title", "Book title", "input[type=text]", None, "", "leave blank for default"),
    ("mode", "Document type", "select", "pdf_types", "openoffice", ""),

    ("booksize", "Page size", "select", "size_options", "", '(Size compatibility: <span class="lulu">Lulu</span>, <span class="newspaper">newspapers</span>, <span class="iso">ISO standards</span>, <span class="us">common in USA</span>)'),
    ("page_width", "Page width", "input[type=text]", None, "booksize numeric-field", "mm"),
    ("page_height", "Page height", "input[type=text]", None, "booksize numeric-field", "mm"),

    ("license", "License", "select", "licenses", "advanced", ""),
    ("toc_header", "Table of Contents header", "input[type=text]", None, "advanced", ""),
    ("isbn", "ISBN", "input[type=text]", None, "advanced", "(13 digits)"),

    ("top_margin", "Top margin", "input[type=text]", None, "advanced margins numeric-field", "mm"),
    ("side_margin", "Side margin", "input[type=text]", None, "advanced margins numeric-field", "mm"),
    ("bottom_margin", "Bottom margin", "input[type=text]", None, "advanced margins numeric-field", "mm"),
    ("gutter", "Gutter", "input[type=text]", None, "advanced margins numeric-field", "mm"),

    ("columns", "Columns", "input[type=text]", None, "advanced columns numeric-field", ""),
    ("column_margin", "Column margin", "input[type=text]", None, "advanced columns numeric-field", "mm"),

    ("grey_scale", "Grey-scale", "input[type=checkbox]", 'yes', "advanced", "(for black and white printing)"),

    #("css_customise", "Customise CSS", "input[type=checkbox]", None, "advanced", "Enter a URL or "),
    ("css-url", "CSS URL", "input[type=text][disabled]", "css_url", "advanced css-url openoffice", ""),
    ("font_list", "Available fonts", "ul", "font_list", "advanced css-custom openoffice", ""),
    ("font_links", "Font examples", "ul", "font_links", "advanced css-custom openoffice", ""),
    ("css", "CSS", "textarea", "css", "advanced css-custom openoffice", ""),

    ("rotate", "Rotate pages for binding", "input[type=checkbox]", 'yes', "advanced", "(for RTL books on LTR printing presses, and vice versa)."),

    ("html_template", "HTML Template", "textarea", None, "advanced html-template", 'for "templated html" output'),

    #("engine", "Layout engine", "select", "engines", "advanced", ""),
    #("header", "Header Text", "input[type=text]", None, "advanced", ""),
    ("max-age", "Use cached data", "input[type=text]", None, "advanced numeric-field", "(younger than this many minutes)."),
    ("booki-group", "Booki group", "input[type=text]", None, "advanced booki", "Pretend the book belongs to this Booki group"),
    ("booki-user", "Booki user", "input[type=text]", None, "advanced booki", "Pretend the book belongs to this Booki user"),
    #("destination", "Use cached data", "input[type=text]", None, "advanced", ""),
    ("page-numbers", "Page numbering style", "select", "page_numbers", "advanced", 'if in doubt, choose "auto"'),
)

FORM_ELEMENT_TYPES = {
    'input[type=text]' : '<input type="text" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'input[type=text][disabled]' : '<input type="text" disabled="disabled" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'input[type=checkbox]' : '<input type="checkbox" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'textarea' : '<textarea id="%(id)s" name="%(id)s">%(val)s</textarea>',
    'select': '<select id="%(id)s" name="%(id)s">%(val)s</select>',
    'ul': '<ul id="%(id)s">%(val)s</ul>',
}

FINISHED_MESSAGE = 'FINISHED'

PROGRESS_POINTS = (
    ("start", "wake up", PUBLIC_CGI_MODES),
    ("fetch_zip", "Load data", PUBLIC_CGI_MODES),
    ("__init__", "Initialise the book", PUBLIC_CGI_MODES),
    ("load_book", "Fetch the book", ('book', 'newspaper', 'web', 'openoffice')),
    ("add_css", "Add css", ('book', 'newspaper', 'web', 'openoffice')),
    ("add_section_titles", "Add section titles", ('book', 'newspaper', 'web', 'openoffice')),
    ("make_epub", "Make the epub file", ('epub',)),
    ("make_oo_doc", "Make the OpenOffice document", ('openoffice',)),
    ("generate_pdf", "Generate the main pdf", ('book', 'newspaper', 'web')),
    ("extract_pdf_outline", "Find page numbers", ('book',)),
    ("reshape_pdf", "Add gutters", ('book', 'newspaper',)),
    ("make_contents", "Calculate Table of Contents", ('book',)),
    ("make_preamble_pdf", "Generate preamble pdf", ('book',)),
    ('make_end_matter_pdf', "Generate end matter pdf", ('book',)),
    ("concatenated_pdfs", "concatenate the pdfs", ('book',)),
    ("make_templated_html", "Make templated HTML", ('templated_html',)),
    #("publish_pdf", "Publish the pdf", ('book', 'newspaper', 'web')),
    (FINISHED_MESSAGE, "Finished!", PUBLIC_CGI_MODES),
)

#XML namespace stuff
DCNS = "{http://purl.org/dc/elements/1.1/}"
DC = "http://purl.org/dc/elements/1.1/"
FM = "http://booki.cc/"
XHTMLNS = '{http://www.w3.org/1999/xhtml}'
XHTML = 'http://www.w3.org/1999/xhtml'
WKTOCNS = "{http://code.google.com/p/wkhtmltopdf/outline}"

S3_SECRET = '/home/douglas/s3.archive.org-secret'
S3_ACCESSKEY = '/home/douglas/s3.archive.org-accesskey'

#When it is necessary to creat a navpoint ID, use this string.
NAVPOINT_ID_TEMPLATE = 'chapter%s'

CLAIM_UNAUTHORED = False

IMG_CACHE = 'cache/images/'

USE_IMG_CACHE_ALWAYS_HOSTS = ['objavi.halo.gen.nz']
USE_ZIP_CACHE_ALWAYS_HOSTS = ['objavi.halo.gen.nz']

IGNORABLE_TWIKI_BOOKS = ('Main', 'TWiki', 'PR', 'Trash', 'Sandbox',
                         'Floss', 'Publish', 'Remix', 'Snippets')

WHITESPACE_AND_NULL = ''.join(chr(_x) for _x in range(33))

#how big to let epub chapters get before splitting?
#sony reader has 100k compressed/300k uncompressed limit, but lets leave room to move.
EPUB_COMPRESSED_SIZE_MAX = 70000
EPUB_FILE_SIZE_MAX = 200000

#used to identify marker tags in html
MARKER_CLASS_SPLIT = "espri-marker-name-clash-with-no-one--split"
MARKER_CLASS_INFO = "espri-marker-name-clash-with-no-one--info"

BOILERPLATE_HTML = { #(footer, header)
    'LTR': ('htdocs/static/boilerplate/footer-LTR.html', None),
    'RTL': ('htdocs/static/boilerplate/footer-RTL.html', None),
    'fa': ('htdocs/static/boilerplate/footer-fa.html', None),
    'ar': ('htdocs/static/boilerplate/footer-ar.html', None),
    'my': ('htdocs/static/boilerplate/footer-my.html', None),
    'hi': ('htdocs/static/boilerplate/footer-hi.html', None),
    'none': (None, None),
}

#default to western-arabic in default text dir
DEFAULT_BOILERPLATE_HTML = BOILERPLATE_HTML[DEFAULT_DIR]

#offset to the zero from ascii zero. 1-9 are added to this.
LOCALISED_DIGITS = {
    'fa': 0x6f0 - 48,
    'ar': 0x660 - 48,
    'hi': 0x966 - 48,
    'my': 0x1040 - 48,
}

PAGE_NUMBER_OPTIONS = BOILERPLATE_HTML.keys() + ['auto']
DEFAULT_PAGE_NUMBER_OPTION = 'auto'


if __name__ == '__main__':
    print ', '.join(x for x in globals().keys() if not x.startswith('_'))
