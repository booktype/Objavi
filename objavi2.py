#!/usr/bin/python
"""Make a pdf from the specified book."""
import os, sys
import cgi
import re
from urllib2 import urlopen
from getopt import gnu_getopt

from fmbook import log, Book, SIZE_MODES, ENGINES, DEFAULT_CSS

FORM_TEMPLATE = os.path.abspath('templates/form.html')
PROGRESS_TEMPLATE = os.path.abspath('templates/progress.html')

# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).

ARG_VALIDATORS = {
    "webName": lambda x: '/' not in x and '..' not in x,
    "css": None, # an url, empty (for default), or css content
    "title": lambda x: len(x) < 999,
    "header": None, # the copyright text?
    "isbn": lambda x: x.isdigit() and len(x) == 13,
    "license": lambda x: len(x) < 999999,
    "server": re.compile(r'^([\w-]+\.?)+$').match,
    "engine": ENGINES.__contains__,
    "booksize": SIZE_MODES.__contains__,
    "cgi-context": lambda x: x.lower() in '1true0false',
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
    #how to get server list?
    return sorted([
        'en.flossmanuals.net',
        'fr.flossmanuals.net',
        'translate.flossmanuals.net',
        'nl.flossmanuals.net',
        'bn.flossmanuals.net',
        'fa.flossmanuals.net',
        #'clean.flossmanuals.net',
        #'42.flossmanuals.net',
        #'trac.flossmanuals.net',
        #'dev.flossmanuals.net',
        #'flossmanuals.net',
        #'irc.flossmanuals.net',
        #'www.flossmanuals.net',
        #'flossmanuals.org',
        #'www.flossmanuals.org',
        #'cal.flossmanuals.net',
        ])


def get_book_list(server):
    #need to go via http to get list
    #http://en.flossmanuals.net/bin/view/TWiki/TWikiWebsTable?skin=text
    #http://en.flossmanuals.net/bin/view/TWiki/WebLeftBarWebsList?skin=text
    items = []
    url = 'http://%s/bin/view/TWiki/WebLeftBarWebsList?skin=text' % server
    #XXX should use lxml
    log(url)
    f = urlopen(url)
    s = f.read()
    f.close()
    return sorted(re.findall(r'/bin/view/(\w+)', s))


def get_size_list():
    #order by increasing areal size.
    ordered = [x[1] for x in
               sorted((v.area, v) for v in SIZE_MODES.values())]
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
    f = open(DEFAULT_CSS[7:])
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
        'css': get_default_css(),
    }
    print template % d


def make_progress_page(webname):
    f = open(PROGRESS_TEMPLATE)
    template = f.read()
    f.close()
    d = {
        'webname': webname,
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


if __name__ == '__main__':
    args = parse_args()
    webname = args.get('webName')
    server = args.get('server', 'en.flossmanuals.net')
    size = args.get('booksize')
    engine = args.get('engine')

    cgi_context = 'SERVER_NAME' in os.environ or args.get('cgi-context', 'NO').lower() in '1true'

    if not webname or not server:
        if cgi_context:
            print "Content-type: text/html; charset=utf-8\n"
            show_form(args, server, webname, size)
        else:
            print __doc__
        sys.exit()

    if cgi_context:
        print "Content-type: text/html; charset=utf-8\n"
        progress_bar = make_progress_page(webname)
    else:
        progress_bar = print_progress

    book = Book(webname, server, pagesize=size, engine=engine,
                watcher=progress_bar
                )
    
    if cgi_context:
        book.spawn_x()
    
    book.load()

    book.set_title(args.get('title'))
    book.add_css(args.get('css'))

    book.add_section_titles()

    book.make_pdf()


    book.cleanup()

    book.notify_watcher('finished')
