#!/usr/bin/python
#
# Part of Objavi2, which turns html manuals into books
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

"""Make a pdf from the specified book."""
from __future__ import with_statement

import os, sys
import cgi
import re, time
from urllib2 import urlopen
from getopt import gnu_getopt

from fmbook import log, Book

import config
from config import SERVER_DEFAULTS, DEFAULT_SERVER

FORM_TEMPLATE = os.path.abspath('templates/form.html')
PROGRESS_TEMPLATE = os.path.abspath('templates/progress.html')

def isfloat(s):
    #spaces?, digits!, dot?, digits?, spaces?
    #return re.compile(r'^\s*[+-]?\d+\.?\d*\s*$').match
    try:
        float(s)
        return True
    except ValueError:
        return False

def isfloat_or_auto(s):
    return isfloat(s) or s.lower() in ('', 'auto')

def is_isbn(s):
    # 10 or 13 digits with any number of hyphens, perhaps with check-digit missing
    s =s.replace('-', '')
    return (re.match(r'^\d+[\dXx*]$', s) and len(s) in (9, 10, 12, 13))


# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).
ARG_VALIDATORS = {
    "book": re.compile(r'^(\w+/?)*\w+$').match, # can be: BlahBlah/Blah_Blah
    "css": None, # an url, empty (for default), or css content
    "title": lambda x: len(x) < 999,
    #"header": None, # header text, UNUSED
    "isbn": is_isbn,
    "license": config.LICENSES.__contains__,
    "server": SERVER_DEFAULTS.__contains__,
    "engine": config.ENGINES.__contains__,
    "booksize": config.PAGE_SIZE_DATA.__contains__,
    "page_width": isfloat,
    "page_height": isfloat,
    "gutter": isfloat_or_auto,
    "top_margin": isfloat_or_auto,
    "side_margin": isfloat_or_auto,
    "bottom_margin": isfloat_or_auto,
    "columns": isfloat_or_auto,
    "column_margin": isfloat_or_auto,
    "cgi-context": lambda x: x.lower() in '1true0false',
    "mode": config.CGI_MODES.__contains__,
    "pdftype": lambda x: config.CGI_MODES.get(x, [False])[0],
    "rotate": u"yes".__eq__,
    "grey_scale": u"yes".__eq__,
}

__doc__ += '\nValid arguments are: %s.\n' % ', '.join(ARG_VALIDATORS.keys())

def parse_args():
    """Read and validate CGI or commandline arguments, putting the
    good ones into the returned dictionary.  Command line arguments
    should be in the form --title='A Book'.
    """
    query = cgi.FieldStorage()
    options, args = gnu_getopt(sys.argv[1:], '', [x + '=' for x in ARG_VALIDATORS])
    options = dict(options)
    data = {}
    for key, validator in ARG_VALIDATORS.items():
        value = query.getfirst(key, options.get('--' + key, None))
        log('%s: %s' % (key, value), debug='STARTUP')
        if value is not None:
            if validator is not None and not validator(value):
                log("argument '%s' is not valid ('%s')" % (key, value))
                continue
            data[key] = value

    log(data, debug='STARTUP')
    return data

def get_server_list():
    return sorted(SERVER_DEFAULTS.keys())

def get_book_list(server):
    """Ask the server for a list of books.  Floss Manual TWikis keep such a list at
    /bin/view/TWiki/WebLeftBarWebsList?skin=text but it needs a bit of processing

    If BOOK_LIST_CACHE is non-zero, the book list won't be re-fetched
    in that many seconds, rather it will be read from disk.
    """
    if config.BOOK_LIST_CACHE:
       cache_name = os.path.join(config.BOOK_LIST_CACHE_DIR, '%s.booklist' % server)
       if (os.path.exists(cache_name) and
           os.stat(cache_name).st_mtime + config.BOOK_LIST_CACHE > time.time()):
           f = open(cache_name)
           s = f.read()
           f.close()
           return s.split()

    url = 'http://%s/bin/view/TWiki/WebLeftBarWebsList?skin=text' % server
    #XXX should use lxml
    log(url)
    f = urlopen(url)
    s = f.read()
    f.close()
    items = sorted(re.findall(r'/bin/view/([\w/]+)/WebHome', s))
    if config.BOOK_LIST_CACHE:
        f = open(cache_name, 'w')
        f.write('\n'.join(items))
        f.close()
    return items

def get_size_list():
    #order by increasing areal size.
    def calc_size(name, pointsize, klass):
        if pointsize:
            mmx = pointsize[0] * config.POINT_2_MM
            mmy = pointsize[1] * config.POINT_2_MM
            return (mmx * mmy, name, klass,
                    '%s (%dmm x %dmm)' % (name, mmx, mmy))

        return (0, name, klass, name) # presumably 'custom'

    return [x[1:] for x in sorted(calc_size(k, v.get('pointsize'), v.get('class', ''))
                                  for k, v in config.PAGE_SIZE_DATA.iteritems())
            ]


def optionise(items, default=None):
    """Make a list of strings into an html option string, as would fit
    inside <select> tags."""
    options = []
    for x in items:
        if isinstance(x, str):
            x = (x, x)
        if len(x) == 2:
            # couple: value, name
            if x[0] == default:
                options.append('<option selected="selected" value="%s">%s</option>' % x)
            else:
                options.append('<option value="%s">%s</option>' % x)
        else:
            # triple: value, class, name
            if x[0] == default:
                options.append('<option selected="selected" value="%s" class="%s">%s</option>' % x)
            else:
                options.append('<option value="%s" class="%s">%s</option>' % x)

    return '\n'.join(options)

def listify(items):
    """Make a list of strings into html <li> items, to fit in a <ul>
    or <ol> element."""
    return '\n'.join('<li>%s</li>' % x for x in items)


def get_default_css(server=DEFAULT_SERVER, mode='book'):
    """Get the default CSS text for the selected server"""
    log(server)
    cssfile = SERVER_DEFAULTS[server]['css-%s' % mode]
    log(cssfile)
    f = open(cssfile)
    s = f.read()
    f.close()
    return s

def font_links():
    """Links to various example pdfs."""
    links = []
    for script in os.listdir(config.FONT_EXAMPLE_SCRIPT_DIR):
        if not script.isalnum():
            log("warning: font-sample %s won't work; skipping" % script)
            continue
        links.append('<a href="%s?script=%s">%s</a>' % (config.FONT_LIST_URL, script, script))
    return links


def make_progress_page(book, bookname, mode):
    """Return a function that will notify the user of progress.  In
    CGI context this means making an html page to display the
    messages, which are then sent as javascript snippets on the same
    connection."""
    if not CGI_CONTEXT:
        return lambda message: '******* got message "%s"' %message

    f = open(PROGRESS_TEMPLATE)
    template = f.read()
    f.close()
    progress_list = ''.join('<li id="%s">%s</li>\n' % x[:2] for x in config.PROGRESS_POINTS
                            if mode in x[2])

    d = {
        'book': book,
        'bookname': bookname,
        'progress_list': progress_list,
    }
    print template % d
    def progress_notifier(message):
        print ('<script type="text/javascript">\n'
               'objavi_show_progress("%s");\n'
               '</script>' % message
               )
        if message == 'finished':
            print '</body></html>'
        sys.stdout.flush()
    return progress_notifier

def make_book_name(book, server, suffix='.pdf'):
    lang = SERVER_DEFAULTS.get(server, SERVER_DEFAULTS[DEFAULT_SERVER])['lang']
    book = ''.join(x for x in book if x.isalnum())
    return '%s-%s-%s%s' % (book, lang,
                           time.strftime('%Y.%m.%d-%H.%M.%S'),
                           suffix)


def get_page_settings(args):
    """Find the size and any optional layout settings.

    args['booksize'] is either a keyword describing a size or
    'custom'.  If it is custom, the form is inspected for specific
    dimensions -- otherwise these are ignored.

    The margins, gutter, number of columns, and column
    margins all set themselves automatically based on the page
    dimensions, but they can be overridden.  Any that are are
    collected here."""
    # get all the values including sizes first
    # the sizes are found as 'page_width' and 'page_height',
    # but the Book class expects them as a 'pointsize' tuple, so
    # they are easily ignored.
    settings = {}
    for k, extrema in config.PAGE_EXTREMA.iteritems():
        try:
            v = float(args.get(k))
        except (ValueError, TypeError):
            #log("don't like %r as a float value for %s!" % (args.get(k), k))
            continue
        min_val, max_val, multiplier = extrema
        if v < min_val or v > max_val:
            log('rejecting %s: outside %s' % (v,) + extrema)
        else:
            log('found %s=%s' % (k, v))
            settings[k] = v * multiplier #convert to points in many cases

    # now if args['size'] is not 'custom', the width and height found
    # above are ignored.
    size = args.get('booksize', config.DEFAULT_SIZE)
    settings.update(config.PAGE_SIZE_DATA[size])

    #if args['mode'] is 'newspaper', then the number of columns is
    #automatically determined unless set -- otherwise default is 1.
    if args['mode'] == 'newspaper' and settings.get('columns') is None:
        settings['columns'] = 'auto'

    if args.get('grey_scale'):
        settings['grey_scale'] = True

    if size == 'custom':
        #will raise KeyError if width, height aren't set
        settings['pointsize'] = (settings['page_width'], settings['page_height'])
        del settings['page_width']
        del settings['page_height']

    settings['engine'] = args.get('engine', config.DEFAULT_ENGINE)
    return settings


def output_and_exit(f):
    """Decorator: prefix function output with http headers and exit
    immediately after."""
    def output(args):
        if CGI_CONTEXT:
            print "Content-type: text/html; charset=utf-8\n"
        f(args)
        sys.exit()
    return output

@output_and_exit
def mode_booklist(args):
    print optionise(get_book_list(args.get('server', config.DEFAULT_SERVER)),
                    default=args.get('book'))

@output_and_exit
def mode_css(args):
    #XX sending as text/html, but it doesn't really matter
    print get_default_css(args.get('server', config.DEFAULT_SERVER), args.get('pdftype', 'book'))


@output_and_exit
def mode_form(args):
    f = open(FORM_TEMPLATE)
    template = f.read()
    f.close()
    f = open(config.FONT_LIST_INCLUDE)
    font_list = [x.strip() for x in f if x.strip()]
    f.close()
    server = args.get('server', config.DEFAULT_SERVER)
    book = args.get('book')
    size = args.get('booksize', config.DEFAULT_SIZE)
    engine = args.get('engine', config.DEFAULT_ENGINE)
    d = {
        'server_options': optionise(get_server_list(), default=server),
        'book_options': optionise(get_book_list(server), default=book),
        'size_options': optionise(get_size_list(), default=size),
        'engines': optionise(config.ENGINES.keys(), default=engine),
        'pdf_types': optionise(sorted(k for k, v in config.CGI_MODES.iteritems() if v[0])),
        'css': get_default_css(server),
        'font_links': listify(font_links()),
        'font_list': listify(font_list),
        'default_license' : config.DEFAULT_LICENSE,
        'licenses' : optionise(config.LICENSES, default=config.DEFAULT_LICENSE),
        'yes': 'yes',
        None: '',
    }

    form = []
    for id, title, type, source, classes, epilogue in config.FORM_INPUTS:
        val = d.get(source, '')
        e = config.FORM_ELEMENT_TYPES[type] % locals()
        form.append('\n<div id="%(id)s_div" class="form-item %(classes)s">\n'
                    '<div class="input_title">%(title)s</div>\n'
                    '<div class="input_contents"> %(e)s %(epilogue)s\n</div>'
                    '</div>\n' % locals())

    if True:
        _valid_inputs = set(ARG_VALIDATORS)
        _form_inputs = set(x[0] for x in config.FORM_INPUTS if x[2] != 'ul')
        log("valid but not used inputs: %s" % (_valid_inputs - _form_inputs))
        log("invalid form inputs: %s" % (_form_inputs - _valid_inputs))

    print template % {'form': ''.join(form)}


@output_and_exit
def mode_book(args):
    # so we're making a pdf.
    mode = args.get('mode', 'book')
    bookid = args.get('book')
    server = args.get('server', config.DEFAULT_SERVER)
    engine = args.get('engine', config.DEFAULT_ENGINE)
    page_settings = get_page_settings(args)
    bookname = make_book_name(bookid, server)
    progress_bar = make_progress_page(bookid, bookname, mode)

    with Book(bookid, server, bookname, page_settings=page_settings, engine=engine,
              watcher=progress_bar, isbn=args.get('isbn'),
              license=args.get('license')) as book:
        if CGI_CONTEXT:
            book.spawn_x()
        book.load()
        book.set_title(args.get('title'))
        book.add_css(args.get('css'), mode)
        book.add_section_titles()

        if mode == 'book':
            book.make_book_pdf()
        elif mode in ('web', 'newspaper'):
            book.make_simple_pdf(mode)
        if "rotate" in args:
            book.rotate180()

        book.publish_pdf()
        book.notify_watcher('finished')

#These ones are similar enought to be handled by the one function
mode_newspaper = mode_book
mode_web = mode_book


@output_and_exit
def mode_openoffice(args):
    """Make an openoffice document.  A whole lot of the inputs have no
    effect."""
    bookid = args.get('book')
    server = args.get('server', config.DEFAULT_SERVER)
    #page_settings = get_page_settings(args)
    bookname = make_book_name(bookid, server, '.odt')
    progress_bar = make_progress_page(bookid, bookname, 'openoffice')

    with Book(bookid, server, bookname,
              watcher=progress_bar, isbn=args.get('isbn'),
              license=args.get('license')) as book:
        if CGI_CONTEXT:
            book.spawn_x()
        book.load()
        book.set_title(args.get('title'))
        book.add_css(args.get('css'), 'openoffice')
        book.add_section_titles()
        book.make_oo_doc()
        book.notify_watcher('finished')


def main():
    args = parse_args()
    mode = args.get('mode')
    if mode is None and 'book' in args:
        mode = 'book'

    global CGI_CONTEXT
    CGI_CONTEXT = 'SERVER_NAME' in os.environ or args.get('cgi-context', 'no').lower() in '1true'

    if not args and not CGI_CONTEXT:
        print __doc__
        sys.exit()

    output_function = globals().get('mode_%s' % mode, mode_form)
    output_function(args)

if __name__ == '__main__':
    if config.CGITB_DOMAINS and os.environ.get('REMOTE_ADDR') in config.CGITB_DOMAINS:
        import cgitb
        cgitb.enable()
    main()

