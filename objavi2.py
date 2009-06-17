#!/usr/bin/python
"""Make a pdf from the specified book."""
import os, sys
import cgi
import re, time
from urllib2 import urlopen
from getopt import gnu_getopt

from fmbook import log, Book
from fmbook import PAGE_SETTINGS, ENGINES, SERVER_DEFAULTS, DEFAULT_SERVER

from config import BOOK_LIST_CACHE

FORM_TEMPLATE = os.path.abspath('templates/form.html')
PROGRESS_TEMPLATE = os.path.abspath('templates/progress.html')

# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).

ARG_VALIDATORS = {
    "webName": re.compile(r'^(\w+/?)*\w+$').match, # can be: BlahBlah/Blah_Blah
    "css": None, # an url, empty (for default), or css content
    "title": lambda x: len(x) < 999,
    "header": None, # the copyright text?
    "isbn": lambda x: x.isdigit() and len(x) == 13,
    "license": lambda x: len(x) < 999999, #should be a codename?
    "server": SERVER_DEFAULTS.__contains__,
    "engine": ENGINES.__contains__,
    "booksize": PAGE_SETTINGS.__contains__,
    "cgi-context": lambda x: x.lower() in '1true0false',
    "mode": str.isalnum,
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
    log(options)
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
    if BOOK_LIST_CACHE:
       cache_name = os.path.join(BOOK_LIST_CACHE_DIR, '%s.booklist' % server)
       if (os.path.exists(cache_name) and
           os.stat(cache_name).st_mtime + BOOK_LIST_CACHE > time.time()):
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
    if BOOK_LIST_CACHE:
        f = open(cache_name, 'w')
        f.write('\n'.join(items))
        f.close()
    return items

def get_size_list():
    #order by increasing areal size.
    ordered = [x[1] for x in
               sorted((v.area, v) for v in PAGE_SETTINGS.values())]
    return [(v.name, '%s (%dmm x %dmm)' % (v.name, v.mmsize[0], v.mmsize[1]))
            for v in ordered]


def optionise(items, default=None):
    options = []
    for x in items:
        if isinstance(x, str):
            if x == default:
                options.append('<option selected="selected">%s</option>' % x)
            else:
                options.append('<option>%s</option>' % x)
        else:
            # couple: value, name
            if x[0] == default:
                options.append('<option selected="selected" value="%s">%s</option>' % x)
            else:
                options.append('<option value="%s">%s</option>' % x)

    return '\n'.join(options)

def get_default_css(server=None):
    if server not in SERVER_DEFAULTS:
        server == DEFAULT_SERVER
    f = open(SERVER_DEFAULTS[server]['css'])
    s = f.read()
    f.close()
    return s



def show_form(args, server, webname, size='COMICBOOK', engine='webkit'):
    f = open(FORM_TEMPLATE)
    template = f.read()
    f.close()
    d = {
        'server_options': optionise(get_server_list(), default=server),
        'book_options': optionise(get_book_list(server), default=webname),
        'size_options': optionise(get_size_list(), default=size),
        'engines': optionise(ENGINES.keys(), default='webkit'),
        'css': get_default_css(server),
    }
    print template % d


def make_progress_page(webname, bookname):
    f = open(PROGRESS_TEMPLATE)
    template = f.read()
    f.close()
    d = {
        'webname': webname,
        'bookname': bookname,
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

def print_progress(message):
    print '******* got message "%s"' %message

def make_book_name(webname, server):
    lang = SERVER_DEFAULTS.get(server, SERVER_DEFAULTS[DEFAULT_SERVER])['lang']
    webname = ''.join(x for x in webname if x.isalnum())
    return '%s-%s-%s.pdf' % (webname, lang,
                             time.strftime('%Y.%m.%d-%H.%M.%S'))

if __name__ == '__main__':
    args = parse_args()
    webname = args.get('webName')
    server = args.get('server', 'en.flossmanuals.net')
    size = args.get('booksize')
    engine = args.get('engine')
    mode = args.get('mode')


    cgi_context = 'SERVER_NAME' in os.environ or args.get('cgi-context', 'NO').lower() in '1true'
    if cgi_context:
        print "Content-type: text/html; charset=utf-8\n"

    if mode == 'booklist':
        print optionise(get_book_list(server), default=webname)
        sys.exit()

    if not webname or not server:
        if cgi_context:
            show_form(args, server, webname, size)
        else:
            print __doc__
        sys.exit()

    # so we're making a book.
    bookname = make_book_name(webname, server)
    if cgi_context:
        progress_bar = make_progress_page(webname, bookname)
    else:
        progress_bar = print_progress

    book = Book(webname, server, bookname, pagesize=size, engine=engine,
                watcher=progress_bar
                )

    if cgi_context:
        book.spawn_x()

    book.load()

    book.set_title(args.get('title'))
    book.add_css(args.get('css'))

    book.add_section_titles()

    book.make_pdf()

    book.publish_pdf()

    book.cleanup()

    book.notify_watcher('finished')
