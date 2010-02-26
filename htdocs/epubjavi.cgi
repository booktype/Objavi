#!/usr/bin/python
import os, sys
os.chdir('..')

import cgi
from getopt import gnu_getopt

from objavi.fmbook import log, ZipBook, make_book_name
from objavi.cgi_utils import shift_file, parse_args, optionise, print_template_and_exit
from objavi import config

USE_CACHED_IMAGES = True #avoid network -- will make out of date books in production!

BOOKS = [x[:-4] for x in os.listdir(config.BOOKI_BOOK_DIR) if x.endswith('.zip')]

def print_form(booklink):
    print_template_and_exit('templates/epubjavi.html',
                            {'booklink': booklink,
                             'booklist': optionise(sorted(BOOKS))}
                            )

def epubjavi(book, use_cached_images=USE_CACHED_IMAGES):
    book = ZipBook(config.LOCALHOST, book)
    book.make_epub(use_cache=use_cached_images)
    return shift_file(book.epubfile, config.EPUB_DIR)


# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).
ARG_VALIDATORS = {
    "book": BOOKS.__contains__,
}

if __name__ == '__main__':
    args = parse_args(ARG_VALIDATORS)
    if 'book' in args:
        url = epubjavi(args['book'])
        book_link = '<p>Download <a href="%s">%s epub</a>.</p>' %(url, args['book'])
    else:
        book_link = ''
    print_form(book_link)



