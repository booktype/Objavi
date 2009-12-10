#!/usr/bin/python

import os

# Preliminary bit to get cgi scripts working

def guess_http_host():
    hostnames = {
        'cloudy': 'objavi.halo.gen.nz',
        'vps504': 'objavi.flossmanuals.net',
    }
    f = open('/etc/hostname')
    host = f.read().strip()
    f.close()
    try:
        os.environ['HTTP_HOST'] = hostnames[host]
    except KeyError:
        raise RuntimeError("making epubs requires a HTTP_HOST environment variable which "
                           "shows where to find a working booki-twiki-gateway.cgi")

if 'HTTP_HOST' not in os.environ:
    guess_http_host()

#-------------------------------------------------------------#

import traceback
from objavi.fmbook import log, ZipBook, make_book_name
from objavi import config
from objavi.twiki_wrapper import get_book_list


def make_epub(server, bookid):
    log('making epub for %s %s' % (server, bookid))
    bookname = make_book_name(bookid, server, '.epub')
    book = ZipBook(server, bookid, bookname=bookname, project='FM')
    book.make_epub(use_cache=True)


for server, settings in config.SERVER_DEFAULTS.items():
    if settings['interface'] == 'Booki':
        continue
    books = get_book_list(server)

    for book in books:
        try:
            make_epub(server, book)
            log('SUCCEEDED: %s %s' % (server, book))
        except Exception, e:
            log('FAILED: %s %s' % (server, book))
            traceback.print_exc()


