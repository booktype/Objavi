#!/usr/bin/python
"""Make a pdf from the specified book."""
import os, sys
import cgi
import re
from getopt import gnu_getopt

from fmbook import log, Book, SIZE_MODES, POINT2MM

FORM_TEMPLATE = os.path.abspath('templates/form.html')

# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).
ARG_VALIDATORS = {
    "webName": lambda x: '/' not in x and '..' not in x,
    "css": None, # an url, empty (for default), or css content
    "title": None,
    "header": None,
    "isbn": None,
    "license": None,
    "server": None,
    "booksize": SIZE_MODES.__contains__
}

__doc__ += '\nValid arguments are: %s.\n' % ', '.join(ARG_VALIDATORS.keys())

def parse_args():
    """Read and validate CGI or commandline arguments, putting the
    good ones into the returned dictionary.  Command line arguments
    should be in the form --title='A Book'.
    """
    query = cgi.FieldStorage()
    options, args = gnu_getopt(sys.argv[1:], '', [x + '=' for x in ARG_VALIDATORS])
    print options
    options = dict(options)
    print options
    data = {}
    for key, validator in ARG_VALIDATORS.items():
        value = query.getfirst(key, options.get('--' + key, None))
        print key, value
        if value is not None:
            if validator is not None and not validator(value):
                log("argument '%s' is not valid ('%s')" % (key, value))
                continue
            data[key] = value

    print data
    return data


def get_server_list(default=None):
    #how to get server list?
    pass


def get_book_list(server, default=None):
    #need to go via http to get list
    pass

def get_size_list(server, default=None):
    #order by increasing areal size.
    ordered = [x[1] for x in
               sorted((v.area, v) for v in SIZE_MODES.values())]
    return [v.name, '%s (%dmm x %dmm)' % (v.name, v.mmsize[0], v.mmsize[1])
            for v in ordered]


def show_form(args, server, webname):
    f = open(FORM_TEMPLATE)
    template = f.read()
    f.close()

    server_list = get_server_list(default=server)
    book_options = get_book_list(server, default=webname)
    size_options = get_size_list()

    css = get_default_css()

    print "Content-type: text/css; charset=utf-8\n"
    print template % dict( (x, __dict__[x]) for x in
                           ('css', 'book_options', 'server_options'))



if __name__ == '__main__':
    args = parse_args()
    webname = args['webName']        
    server = args.get('server',
                      os.environ.get('SERVER_NAME', 'en.flossmanuals.net'))
    size = args.get('booksize')

    if not webname or not server:
        show_form(args, server, webname, size)
        show_form(args, server, webname)
        sys.exit()
    
    from fmbook import log, Book

    book = Book(webname, server, size)
    book = Book(webname, server)
    book.load()
    
    book.set_title(args.get('title'))
    book.add_css(args.get('css'))

    book.add_section_titles()

    book.make_pdf()

