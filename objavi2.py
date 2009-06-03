#!/usr/bin/python
"""Make a pdf from the specified book."""
import os, sys
import cgi
import re
from getopt import gnu_getopt

import lxml.etree, lxml.html

from fmbook import log, Book


# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).
ARG_VALIDATORS = {
    "webName": lambda x: '/' not in x and '..' not in x,
    "css": None,
    "title": None,
    "header": None,
    "isbn": None,
    "license": None,
    "server": None,
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


if __name__ == '__main__':
    args = parse_args()
    webname = args['webName']        
    server = args.get('server',
                      os.environ.get('SERVER_NAME', 'en.flossmanuals.net'))
    
    book = Book(webname, server)
    book.load()
    
    book.set_title(args.get('title'))
    book.add_css(args.get('css'))

    book.add_section_titles()

    book.make_pdf()

