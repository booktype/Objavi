"""Fetch stuff from remote Booki instances"""

import os, sys

from objavi import config
from objavi.book_utils import log
from urllib2 import urlopen
from urlparse import urlsplit

try:
    import json
except ImportError:
    import simplejson as json


def get_book_list(server):
    """Ask the server for a list of books.  Booki offers this list as
    json at /list-books.json.
    """
    url = 'http://%s/list-books.json' % server
    log('getting booklist: %s' % url)
    f = urlopen(url)
    books = json.load(f)

    items = []
    for book in books:
        url = book['fields']['url_title']
        title = book['fields']['title']
        items.append((url, title))

    f.close()
    return items
