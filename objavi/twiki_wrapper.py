"""Fetch stuff from remote twiki instances"""

import os, sys, time, re
import tempfile

from objavi import config
from objavi.cgi_utils import log
from urllib2 import urlopen

import lxml.html

CHAPTER_TEMPLATE = '''<html>
<head>
<title>%(title)s</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
%(text)s
</body>
</html>
'''

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
    log('getting booklist: %s' % url)
    f = urlopen(url)
    s = f.read()
    f.close()
    items = sorted(x for x in re.findall(r'/bin/view/([\w/]+)/WebHome', s)
                   if x not in config.IGNORABLE_TWIKI_BOOKS)
    if config.BOOK_LIST_CACHE:
        f = open(cache_name, 'w')
        f.write('\n'.join(items))
        f.close()
    return items


def toc_iterator(server, book):
    """TOC.txt has 3 lines per chapter.  Fetch them and yield them in
    triples.
    """
    url = config.TOC_URL % (server, book)
    log('getting TOC: %s' % url)
    f = urlopen(url)
    encoding = config.SERVER_DEFAULTS[server]['toc-encoding']
    while True:
        try:
            if encoding is not None:
                yield TocItem(f.next().decode(encoding).strip().encode('utf-8'),
                              f.next().decode(encoding).strip().encode('utf-8'),
                              f.next().decode(encoding).strip().encode('utf-8'))
            else:
                yield TocItem(f.next().strip(),
                              f.next().strip(),
                              f.next().strip())
        except StopIteration:
            break
    f.close()

def get_book_html(server, book, dir):
    """Fetch and parse the raw html of the book."""
    url = config.BOOK_URL % (server, book)
    log('getting book html: %s' % url)
    f = urlopen(url)
    rawhtml = f.read()
    f.close()
    html = ('<html dir="%s"><head>\n<title>%s</title>\n'
            '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'
            '</head>\n<body>\n'
            '%s\n'
            '<div style="page-break-before: always; color:#fff;" class="unseen">'
            'A FLOSS Manuals book</div>\n</body></html>'
    ) % (dir, book, rawhtml)
    return html


def get_chapter_html(server, book, chapter, wrapped=False):
    url = config.CHAPTER_URL % (server, book, chapter)
    log('getting chapter: %s' % url)
    f = urlopen(url)
    html = f.read()
    f.close()
    if wrapped:
        html = CHAPTER_TEMPLATE % {
            'title': '%s: %s' % (book, chapter),
            'text': html
        }
    return html

def get_book_copyright(server, book, title_map):
    # open the Credits chapter that has a list of authors for each chapter.
    # each chapter is listed thus (linebreaks added):
    #   <i>CHAPTER TITLE</i><br/>&copy; First Author 2007<br/>
    #   Modifications:<br/>Second Author 2007, 2008<br/>
    #   Third Author 2008<br/>Fourth Author 2008<br/><hr/>
    #
    # where "CHAPTER TITLE" is as appears in TOC.txt, and "X
    # Author" are the names TWiki has for authors.  So the thing
    # to do is look for the <i> tags and match them to the toc.
    #
    # the chapter title is not guaranteed unique (but usually is).

    credits_html = get_chapter_html(server, book, 'Credits', wrapped=True)
    tree = lxml.html.document_fromstring(credits_html)
    chapter_copy = {}
    author_copy = {}

    name_re = re.compile(r'^\s*(.+?) ((?:\d{4},? ?)+)$')
    for e in tree.iter('i'):
        log(e.text)
        if e.tail or e.getnext().tag != 'br':
            continue

        chapter = title_map.get(e.text)
        authors = chapter_copy.setdefault(chapter, [])
        while True:
            e = e.getnext()
            if not e.tail or e.tag != 'br':
                break
            log(e.tail)
            if e.tail.startswith(u'\u00a9'): # \u00a9 == copyright symbol
                m = name_re.match(e.tail[1:])
                author, dates = m.groups()
                author_copy.setdefault(author, []).append((chapter, 'primary'))
                authors.append(('primary', author, dates))
                #log(author, dates)
            else:
                m = name_re.match(e.tail)
                if m is not None:
                    author, dates = m.groups()
                    author_copy.setdefault(author, []).append((chapter, 'secondary'))
                    authors.append(('secondary', author, dates))
                    #log(author, dates)

    return author_copy, chapter_copy


class TocItem(object):
    """This makes sense of the tuples from TOC.txt files"""
    def __init__(self, status, chapter, title):
        # status is
        #  0 - section heading with no chapter
        #  1 - chapter heading
        #  2 - book title
        #
        # chapter is twiki name of the chapter
        # title is a human readable name of the chapter.
        self.status = status
        self.chapter = chapter
        self.title = title

    def is_chapter(self):
        return self.status == '1'

    def is_section(self):
        return self.status == '0'

    def is_title(self):
        return self.status == '2'

    def __str__(self):
        return '<toc: %s>' %  ', '.join('%s: %s' % x for x in self.__dict__.iteritems())

    def as_zipitem(self):
        item =  {
            "title": self.title,
            "url": self.chapter + '.html',
            'type': 'chapter'
            }
        if self.is_section:
            item["url"] = None
            item['type'] = 'booki-section'
            item['children'] = []
        return item


class TWikiBook(object):
    def __init__(self, book, server, bookname):
        log("*** Extracting TWiki book %s ***" % bookname)
        self.book = book
        self.server = server
        self.workdir = tempfile.mkdtemp(prefix=bookname, dir=config.TMPDIR)
        os.chmod(self.workdir, 0755)
        defaults = config.SERVER_DEFAULTS[server]
        self.lang = defaults['lang']
        self.dir  = defaults['dir']

        self.publish_name = bookname

    def filepath(self, fn):
        return os.path.join(self.workdir, fn)


    def get_twiki_metadata(self):
        """Get information about a twiki book (as much as is easy and useful)."""
        title_map = {}
        authors = {}
        meta = {
            config.DC: {
                "publisher": {
                    "": ["FLOSS Manuals http://flossmanuals.net"]
                    },
                'language': {
                    "": [self.lang]
                    },
                'identifier': {
                    "": ['http://%s/epub/%s/%s' %
                         (self.server, self.book, time.strftime('%Y.%m.%d-%H.%M.%S'))]
                    },
                'creator': {
                    "": ['The Contributors']
                    },
                'date': {
                    "": [time.strftime('%Y-%m-%d')]
                    },
                'title': {
                    "": [self.book]
                    },
                },
            config.FM: {
                'server': {"": [self.server]},
                'book': {"": [self.book]},
                }
            }
        spine = []
        toc = []
        section = toc

        for t in toc_iterator(self.server, self.book):
            if t.is_chapter():
                spine.append(t.chapter)
                section.append(t.as_zipitem())
                title_map[t.title] = t.chapter
                if toc and toc[-1]['url'] is None:
                    toc[-1]['url'] = section[-1]['url']
            elif t.is_section():
                item = t.as_zipitem()
                section = item['children']
                toc.append(item)
            elif t.is_title():
                meta[config.DC]['title'][''] = [t.title]

        author_copyright, chapter_copyright = get_book_copyright(self.server, self.book, title_map)

        return {
            'metadata': meta,
            'TOC': toc,
            'spine': spine,
            'copyright': author_copyright,
            #'chapter_copyright': chapter_copyright,
        }
