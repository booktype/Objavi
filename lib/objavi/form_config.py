# Part of Objavi2, which makes pdf versions of FLOSSManuals books.
# This python module contains or encapsulates configuration and
# constant data.
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

"""This module contains form definition and validation data."""
import config
import cgi_utils
from objavi.cgi_utils import is_utf8, is_float, is_float_or_auto
from objavi.cgi_utils import is_int_or_auto, is_isbn, is_url, never_ok
from objavi.book_utils import get_server_defaults

import re


DESTINATIONS = ('download', 'nowhere')
DEFAULT_DESTINATION = 'download'

CGI_MODES = { # arguments are: (publication, extension, mimetype)
    'bookjs/pdf': (True, '.pdf', "application/pdf"),
    'bookjs/zip': (False, '.zip', "application/zip"),
    'book': (True, '.pdf', "application/pdf"),
    'newspaper': (True, '.pdf', "application/pdf"),
    'web': (True, '.pdf', "application/pdf"),
    #XX stop openoffice for now: it doesn't work anyway
    'openoffice': (True, '.odt', "application/vnd.oasis.opendocument.text"),
    'booklist': (False, None, None),
    'css': (False, None, None),
    'form': (False, None, None),
    'epub': (True, '.epub', "application/epub+zip"),
    'bookizip': (True, '.zip', config.BOOKIZIP_MIMETYPE),
    'templated_html':  (True, '.tar.gz', 'application/x-gzip'),
}

DEFAULT_MODE = 'book'
DEFAULT_MAX_AGE = -1 #negative number means server default


FORM_INPUTS = (
    # input, name, input type, contents key/input value, CSS classes, extra text, validator, default
    ("server", "Booktype server", "select", "server_options", "", "",
     lambda x: get_server_defaults(x) is not None, config.DEFAULT_SERVER,
     ),
    # book name can be: BlahBlah/Blah_Blah
    ("book", "Book", "input[type=text]", "book_options", "", "",
     lambda x: len(x) < 999 and is_utf8(x), None,
     ),
    ("title", "Book title", "input[type=text]", None, "", "leave blank for default",
     lambda x: len(x) < 999 and is_utf8(x), None,
     ),
    ("mode", "Document type", "select", "pdf_types", "openoffice", "",
     CGI_MODES.__contains__, DEFAULT_MODE,
     ),

    ("booksize", "Page size", "select", "size_options", "", "",
     config.PAGE_SIZE_DATA.__contains__, config.DEFAULT_SIZE,
     ),
    ("page_width", "Page width", "input[type=text]", None, "booksize numeric-field", "mm",
     is_float, None,
     ),
    ("page_height", "Page height", "input[type=text]", None, "booksize numeric-field", "mm",
     is_float, None,
     ),
    ("cover_url", "URL for cover image", "input[type=text]", None, "", "", 
     lambda x: len(x) < 999 and is_utf8(x), None),
    ("output_profile", "Output profile for Calibre", "input[type=text]", None, "", "", 
     lambda x: len(x) < 999 and is_utf8(x), None),
    ("output_format", "Output format for Calibre", "input[type=text]", None, "", "", 
     lambda x: len(x) < 7 and is_utf8(x) and "/" not in x and "." not in x, "mobi"),
    ("license", "License", "select", "licenses", "advanced", "",
     config.LICENSES.__contains__, config.DEFAULT_LICENSE,
     ),
    ("toc_header", "Table of Contents header", "input[type=text]", None, "advanced", "",
     is_utf8, None,
     ),
    ("isbn", "ISBN", "input[type=text]", None, "advanced", "(13 digits)",
     is_isbn, None,
     ),
    ("top_margin", "Top margin", "input[type=text]", None, "advanced margins numeric-field", "mm",
     is_float_or_auto, None,
     ),
    ("side_margin", "Side margin", "input[type=text]", None, "advanced margins numeric-field", "mm",
     is_float_or_auto, None,
     ),
    ("bottom_margin", "Bottom margin", "input[type=text]", None, "advanced margins numeric-field", "mm",
     is_float_or_auto, None,
     ),
    ("gutter", "Gutter", "input[type=text]", None, "advanced margins numeric-field", "mm",
     is_float_or_auto, None,
     ),

    ("columns", "Columns", "input[type=text]", None, "advanced columns numeric-field", "",
     is_int_or_auto, None,
     ),
    ("column_margin", "Column margin", "input[type=text]", None, "advanced columns numeric-field", "mm",
     is_float_or_auto, None,
     ),

    ("grey_scale", "Grey-scale", "input[type=checkbox]", 'yes', "advanced", "(for black and white printing)",
     u"yes".__eq__, None,
     ),

    ("css-url", "CSS URL", "input[type=text][disabled]", "css_url", "advanced css-url openoffice", "",
     never_ok, None,
     ),
    ("font_list", "Available fonts", "ul", "font_list", "advanced css-custom openoffice", "",
     never_ok, None,
     ),
    ("font_links", "Font examples", "ul", "font_links", "advanced css-custom openoffice", "",
     never_ok, None,
     ),
    ("css", "CSS", "textarea", "css", "advanced css-custom openoffice", "",
     is_utf8, None,
     ),

    ("rotate", "Rotate pages for binding", "input[type=checkbox]", 'yes', "advanced",
     "(for RTL books on LTR printing presses, and vice versa).",
     u"yes".__eq__, None,
     ),
    ("html_template", "HTML Template", "textarea", None, "advanced html-template",
     'for "templated html" output',
     is_utf8, None,
     ),
    ("max-age", "Use cached data", "input[type=text]", None, "advanced numeric-field",
     "(younger than this many minutes).",
     is_float, DEFAULT_MAX_AGE,
     ),
    ("booki-group", "Booki group", "input[type=text]", None, "advanced booki",
     "Pretend the book belongs to this Booki group",
     is_utf8, None,
     ),
    ("booki-user", "Booki user", "input[type=text]", None, "advanced booki",
     "Pretend the book belongs to this Booki user",
     is_utf8, None,
     ),
    ("page-numbers", "Page numbering style", "select", "page_numbers", "advanced",
     'if in doubt, choose "auto"',
     config.PAGE_NUMBER_OPTIONS.__contains__, config.DEFAULT_PAGE_NUMBER_OPTION,
     ),
    ("embed-fonts", "Embed all fonts", "input[type=checkbox]", 'yes', "advanced",
     'PDFs: force embedding of Adobe fonts (probably unnecessary)',
     u"yes".__eq__, None,
     ),
    ("allow-breaks", "no page break control",
     "input[type=checkbox]", 'yes', "advanced", "Let page breaks occur immediately after headings",
     u"yes".__eq__, None,
     ),
)
