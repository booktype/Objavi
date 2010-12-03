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

"""This module contains form definition and validation data."""
import config
import cgi_utils
from objavi.cgi_utils import is_utf8, is_float, is_float_or_auto, is_isbn, is_url, never_ok

import re

DEFAULT_CGI_DESTINATION = 'html'


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
    'bookizip': (True, '.zip', config.BOOKIZIP_MIMETYPE),
    'templated_html':  (True, '', 'text/html'),
#    'templated_html_zip':  (True, '.zip', 'application/zip'),
}

PUBLIC_CGI_MODES = tuple(k for k, v in CGI_MODES.items() if v[0])


CGI_METHODS = ('sync', 'async', 'poll')

#used by objavi-async
CGI_DESTINATIONS = {
    'archive.org': {'sync': (config.ARCHIVE_TEMPLATE, 'text/plain; charset=utf-8'),
                    'async': (config.ARCHIVE_TEMPLATE, 'text/plain; charset=utf-8'),
                    'poll': (None, None),
                    'default': 'sync',
                    },
    'download': {'sync': (None, None),
                 'async': (config.ASYNC_TEMPLATE, 'text/plain; charset=utf-8'),
                 'poll': (None, None),
                 'default': 'sync',
                 },
    'html': {'sync': (config.PROGRESS_TEMPLATE, 'text/html; charset=utf-8'),
             'async': (config.ASYNC_TEMPLATE, 'text/plain; charset=utf-8'),
             'poll': (config.PROGRESS_ASYNC_TEMPLATE, 'text/html; charset=utf-8'),
             'default': 'sync',
             },
    'nowhere': {'sync': (config.NOWHERE_TEMPLATE, 'text/plain; charset=utf-8'),
                'async': (config.NOWHERE_TEMPLATE, 'text/plain; charset=utf-8'),
                'poll': (config.ASYNC_TEMPLATE, 'text/plain; charset=utf-8'),
                'default': 'sync',
                },
}

DEFAULT_PDF_TYPE = 'book'
DEFAULT_MAX_AGE = -1 #negative number means server default

FORM_INPUTS = (
    # input, name, input type, contents key/input value, CSS classes, extra text, validator, default
    ("server", "FLOSS Manuals server", "select", "server_options", "", "",
     config.SERVER_DEFAULTS.__contains__, config.DEFAULT_SERVER,
     ),
    # book name can be: BlahBlah/Blah_Blah
    ("book", "Manual", "input[type=text]", "book_options", "", "",
     lambda x: len(x) < 999 and is_utf8(x), None,
     ),
    ("title", "Book title", "input[type=text]", None, "", "leave blank for default",
     lambda x: len(x) < 999 and is_utf8(x), None,
     ),
    ("mode", "Document type", "select", "pdf_types", "openoffice", "",
     CGI_MODES.__contains__, None,
     ),

    ("booksize", "Page size", "select", "size_options", "",
     '(Size compatibility: <span class="lulu">Lulu</span>, <span class="newspaper">newspapers</span>, <span class="iso">ISO standards</span>, <span class="us">common in USA</span>)',
     config.PAGE_SIZE_DATA.__contains__, config.DEFAULT_SIZE,
     ),
    ("page_width", "Page width", "input[type=text]", None, "booksize numeric-field", "mm",
     is_float, None,
     ),
    ("page_height", "Page height", "input[type=text]", None, "booksize numeric-field", "mm",
     is_float, None,
     ),
    ("license", "License", "select", "licenses", "advanced", "",
     config.LICENSES.__contains__, None,
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
     config.BOILERPLATE_HTML.__contains__, None,
     ),
    ("embed-fonts", "Embed all fonts", "input[type=checkbox]", 'yes', "advanced",
     'PDFs: force embedding of Adobe fonts (probably unnecessary)',
     u"yes".__eq__, None,
     ),

    ("pdf_type", "", None, '', "", '',             #for css mode
     lambda x: CGI_MODES.get(x, [False])[0], DEFAULT_PDF_TYPE,
     ),
    ("method", '', None, '', "", '',
     CGI_METHODS.__contains__, None,
     ),
    ("callback", '', None, '', "", '',
     is_url, None,
     ),
    ("engine", "", None, "", "", "", config.ENGINES.__contains__, config.DEFAULT_ENGINE,
     ),
    ("destination", "", None, None, "", "",
    CGI_DESTINATIONS.__contains__, DEFAULT_CGI_DESTINATION,
     ),
)


FORM_ELEMENT_TYPES = {
    'input[type=text]' : '<input type="text" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'input[type=text][disabled]' : '<input type="text" disabled="disabled" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'input[type=checkbox]' : '<input type="checkbox" id="%(id)s" name="%(id)s" value="%(val)s" />',
    'textarea' : '<textarea id="%(id)s" name="%(id)s">%(val)s</textarea>',
    'select': '<select id="%(id)s" name="%(id)s">%(val)s</select>',
    'ul': '<ul id="%(id)s">%(val)s</ul>',
    None: None, #don't display the form element
}



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
    (config.FINISHED_MESSAGE, "Finished!", PUBLIC_CGI_MODES),
)

