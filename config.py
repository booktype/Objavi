"""This module contains constant values used to produce books.
"""
#XXX eventually, read in a real config file.
#XXX Some of these values should be editable via an admin cgi script

#Not really configurable (72 pt per inch / 25.4 mm per inch)
POINT_2_MM = 25.4 / 72.0
MM_2_POINT = 72.0 / 25.4

KEEP_TEMP_FILES=True
TMPDIR = 'tmp'

FIREFOX = 'firefox'
WKHTMLTOPDF = '/usr/local/bin/wkhtmltopdf-static'
WKHTMLTOPDF_EXTRA_COMMANDS = []
#WKHTMLTOPDF_EXTRA_COMMANDS = ['--outline',  '-t']


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
BASE_MARGIN = 18
PROPORTIONAL_MARGIN = 0.032
# gutter is BASE_GUTTER + PROPORTIONAL_GUTTER * width
BASE_GUTTER = 15
PROPORTIONAL_GUTTER = 0.011

PAGE_NUMBER_SIZE = 11 #XXX this is not used by pdfedit! (ie, it is a guess)

PAGE_SIZE_DATA = {
    'COMICBOOK':    {'pointsize': ((6.625 * 72), (10.25 * 72))},
    "A4":           {'pointsize': (210 * MM_2_POINT, 297 * MM_2_POINT)},
    "POCKET":       {'pointsize': (4.25 * 72, 6.875 * 72)},

    "USLETTER":     {'pointsize': (8.5 * 72, 11 * 72)},
    "USTRADE":      {'pointsize': (6 * 72, 9 * 72)},
    "LANDSCAPE9x7": {'pointsize': (9 * 72, 7 * 72)},
    "SQUARE7.5":    {'pointsize': (7.5 * 72, 7.5 * 72)},
    "ROYAL":        {'pointsize': (6.139 * 72, 9.21 * 72)},
    "CROWNQUARTO":  {'pointsize': (7.444 * 72, 9.681 * 72)},
    "SQUARE8.5":    {'pointsize': (8.5 * 72, 8.5 * 72)},
    "A5":           {'pointsize': (148 * MM_2_POINT, 210 * MM_2_POINT)},
}

ENGINES = {
    'webkit' : [],
    'gecko' : [],
}

FONT_LIST_INCLUDE = 'cache/font-list.inc'
FONT_LIST_URL = '/font-list.py'

# for the license field, with a view to making it a drop down.
LISENCES = ('GPL', 'GPLv2', 'GPLv2+', 'GPLv3', 'GPLv3+', 'LGPL', 'LGPLv2.1',
            'BSD', 'public domain', 'MIT', 'Artistic')


if __name__ == '__main__':
    print ', '.join(x for x in globals().keys() if not x.startswith('_'))
