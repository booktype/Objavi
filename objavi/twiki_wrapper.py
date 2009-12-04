"""Fetch stuff from remote twiki instances"""

import os, sys, time, re
import tempfile

from objavi import config
from objavi.cgi_utils import log, guess_lang, guess_text_dir, make_book_name
from urllib2 import urlopen
from booki.bookizip import add_metadata, BookiZip
from booki.xhtml_utils import EpubChapter

from pprint import pformat

import lxml.html

CHAPTER_TEMPLATE = '''<html dir="%(dir)s">
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
        if self.is_section():
            item["url"] = None
            item['type'] = 'booki-section'
            item['children'] = []
        return item


class TWikiBook(object):
    def __init__(self, book, server, bookname=None):
        if bookname is None:
            bookname = make_book_name(book, server, '.zip')
        log("*** Extracting TWiki book %s ***" % bookname)
        self.book = book
        self.server = server
        self.workdir = tempfile.mkdtemp(prefix=bookname, dir=config.TMPDIR)
        os.chmod(self.workdir, 0755)

        #probable text direction
        self.dir = guess_text_dir(self.server, self.book)

    def filepath(self, fn):
        return os.path.join(self.workdir, fn)

    def get_twiki_metadata(self):
        """Get information about a twiki book (as much as is easy and useful)."""
        meta = {
            config.DC: {
                "publisher": {
                    "": ["FLOSS Manuals http://flossmanuals.net"]
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

        lang = guess_lang(self.server, self.book)
        dir = guess_text_dir(self.server, self.book)
        log(self.server, self.book, lang, dir)
        if lang is not None:
            add_metadata(meta, 'language', lang)
        if dir is not None:
            add_metadata(meta, 'dir', dir, ns=config.FM)

        spine = []
        toc = []
        section = toc
        waiting_for_url = []
        title_map = {}

        for t in toc_iterator(self.server, self.book):
            log(t)
            if t.is_title():
                meta[config.DC]['title'][''] = [t.title]
                continue

            item = t.as_zipitem()
            if item['url'] is None:
                waiting_for_url.append(item)
            elif waiting_for_url:
                for wt in waiting_for_url:
                    wt['url'] = item['url']
                waiting_for_url = []

            if t.is_chapter():
                spine.append(t.chapter)
                section.append(item)
                title_map.setdefault(t.title, []).append(t.chapter)

            elif t.is_section():
                section = item['children']
                toc.append(item)

        credits, contributors = self.get_book_copyright(title_map)
        for c in contributors:
            add_metadata(meta, 'contributor', c)

        return {
            'version': 1,
            'metadata': meta,
            'TOC': toc,
            'spine': spine,
            'manifest': {},
        }, credits



    def make_bookizip(self, filename=None, use_cache=False):
        """Extract all chapters, images, and metadata, and zip it all
        up for conversion to epub.

        If cache is true, images that have been fetched on previous
        runs will be reused.
        """
        if filename is None:
            filename = self.filepath('booki.zip')
        metadata, credits = self.get_twiki_metadata()
        #log(pformat(metadata))
        bz = BookiZip(filename, metadata)

        all_images = set()
        for chapter in metadata['spine']:
            contents = self.get_chapter_html(chapter, wrapped=True)
            c = EpubChapter(self.server, self.book, chapter, contents,
                            use_cache=use_cache)
            images = c.localise_links()
            all_images.update(images)
            bz.add_to_package(chapter, chapter + '.html',
                              c.as_html(), **credits[chapter])

        # Add images afterwards, to sift out duplicates
        for image in all_images:
            imgdata = c.image_cache.read_local_url(image)
            bz.add_to_package(image, image, imgdata) #XXX img ownership: where is it?

        bz.finish()
        return bz.filename

    def get_chapter_html(self, chapter, wrapped=False):
        url = config.CHAPTER_URL % (self.server, self.book, chapter)
        log('getting chapter: %s' % url)
        f = urlopen(url)
        html = f.read()
        f.close()
        if wrapped:
            html = CHAPTER_TEMPLATE % {
                'title': '%s: %s' % (self.book, chapter),
                'text': html,
                'dir': self.dir
            }
        return html

    def get_book_copyright(self, title_map):
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

        credits_html = self.get_chapter_html('Credits', wrapped=True)
        tree = lxml.html.document_fromstring(credits_html)
        credits = {}
        authors = set()

        name_re = re.compile(r'^\s*(.+?) ((?:\d{4},? ?)+)$')
        for e in tree.iter('i'):
            log(e.text)
            if e.tail or e.getnext().tag != 'br':
                continue
            try:
                chapter = title_map.get(e.text, []).pop(0)
            except IndexError:
                log("no remaining chapters matching %s" % e.text)
                continue
            log(chapter)
            details = credits.setdefault(chapter, {
                "contributors": [],
                "rightsholders": [],
                })
            while True:
                e = e.getnext()
                if not e.tail or e.tag != 'br':
                    break
                log(e.tail)
                if e.tail.startswith(u'\u00a9'): # \u00a9 == copyright symbol
                    m = name_re.match(e.tail[1:])
                    author, dates = m.groups()
                    details['rightsholders'].append(author)
                    details['contributors'].append(author)
                else:
                    m = name_re.match(e.tail)
                    if m is not None:
                        author, dates = m.groups()
                        details['contributors'].append(author)

            authors.update(details['contributors'])
        return credits, authors
