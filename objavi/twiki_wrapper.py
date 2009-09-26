"""Fetch stuff from remote twiki instances"""

import os, sys, time, re

from objavi import config
from objavi.cgi_utils import log
from urllib2 import urlopen


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

    url = config.CHAPTER_URL % (server, 'TWiki', 'WebLeftBarWebsList')
    #url = 'http://%s/bin/view/TWiki/WebLeftBarWebsList?skin=text' % server
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



def toc_iterator(server, book):
    """TOC.txt has 3 lines per chapter.  Fetch them and yield them in
    triples.
    """
    f = urlopen(config.TOC_URL % (server, book))
    while True:
        try:
            yield (f.next().strip(),
                   f.next().strip(),
                   f.next().strip())
        except StopIteration:
            break
    f.close()


def get_book_html(server, book):
    """Fetch and parse the raw html of the book.  If tidy is true
    (default) links in the document will be made absolute."""
    f = urlopen(config.BOOK_URL % (server, book))
    html = f.read()
    f.close()
    return html


def get_chapter_html(server, book, chapter):
    f = urlopen(config.CHAPTER_URL % (server, book, chapter))
    html = f.read()
    f.close()
    return html


