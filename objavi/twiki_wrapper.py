"""Fetch stuff from remote twiki instances"""

import os, sys, time, re
import tempfile

from objavi import config
from objavi.book_utils import log, guess_lang, guess_text_dir, make_book_name
from urllib2 import urlopen
from urlparse import urlsplit
from booki.bookizip import add_metadata, BookiZip

from objavi.xhtml_utils import BaseChapter, ImageCache

#from pprint import pformat

import lxml.html
from lxml import etree

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
        cache_name = os.path.join(config.CACHE_DIR, '%s.booklist' % server)
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
    credits = None
    metadata = None
    def __init__(self, book, server, bookname=None):
        if bookname is None:
            bookname = make_book_name(book, server, '.zip')
        log("*** Extracting TWiki book %s ***" % bookname)
        self.bookname = bookname
        self.book = book
        self.server = server
        self.workdir = tempfile.mkdtemp(prefix=bookname, dir=config.TMPDIR)
        os.chmod(self.workdir, 0755)
        #probable text direction
        self.dir = guess_text_dir(self.server, self.book)

    def filepath(self, fn):
        return os.path.join(self.workdir, fn)

    def _fetch_metadata(self, force=False):
        """Get information about a twiki book (as much as is easy and
        useful).  If force is False (default) then it will not be
        reloaded if it has already been set.
        """
        if self.metadata is not None and not force:
            log("not reloading metadata")
            return
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
        self.dir = guess_text_dir(self.server, self.book)
        #log(self.server, self.book, lang, self.dir)
        if lang is not None:
            add_metadata(meta, 'language', lang)
        if self.dir is not None:
            add_metadata(meta, 'dir', self.dir, ns=config.FM)

        spine = []
        toc = []
        section = toc
        waiting_for_url = []

        for t in toc_iterator(self.server, self.book):
            #log(t)
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

            elif t.is_section():
                section = item['children']
                toc.append(item)

        self.metadata = {
            'version': 1,
            'metadata': meta,
            'TOC': toc,
            'spine': spine,
            'manifest': {},
        }

        self._parse_credits()
        for c in self.contributors:
            add_metadata(meta, 'contributor', c)



    def make_bookizip(self, filename=None, use_cache=False):
        """Extract all chapters, images, and metadata, and zip it all
        up for conversion to epub.

        If cache is true, images that have been fetched on previous
        runs will be reused.
        """
        self._fetch_metadata()
        if filename is None:
            filename = self.filepath(self.bookname)
        bz = BookiZip(filename, self.metadata)

        all_images = set()
        for chapter in self.metadata['spine']:
            contents = self.get_chapter_html(chapter, wrapped=True)
            c = TWikiChapter(self.server, self.book, chapter, contents,
                             use_cache=use_cache)
            images = c.localise_links()
            c.fix_bad_structure()
            all_images.update(images)
            #log(chapter, self.credits)
            bz.add_to_package(chapter, chapter + '.html',
                              c.as_html(), **self.credits.get(chapter, {}))

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

    def _parse_credits(self, force=False):
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
        if self.credits is not None and not force:
            log("not reloading metadata")
            return

        self.credits = {}
        self.contributors = set()
        self.titles = []

        credits_html = self.get_chapter_html('Credits', wrapped=True)
        try:
            parser = lxml.html.HTMLParser(encoding='utf-8')
            tree = lxml.html.document_fromstring(credits_html, parser=parser)
        except UnicodeDecodeError, e:
            log("book isn't unicode! (%s)" %(e,))
            encoding = config.SERVER_DEFAULTS[self.server]['toc-encoding']
            parser = lxml.html.HTMLParser(encoding=encoding)
            tree = lxml.html.document_fromstring(credits_html, parser=parser)

        name_re = re.compile(r'^\s*(.+?) ((?:\d{4},? ?)+)$')
        spine_iter = iter(self.metadata['spine'])

        try:
            for e in tree.iter('i'):
                if e.tail or e.getnext().tag != 'br':
                    continue
                title = e.text
                chapter = spine_iter.next()
                log("chapter %r title %r" % (chapter, title))
                contributors = []
                rightsholders = []
                while True:
                    e = e.getnext()
                    if not e.tail or e.tag != 'br':
                        break
                    #log(e.tail)
                    if e.tail.startswith(u'\u00a9'): # \u00a9 == copyright symbol
                        m = name_re.match(e.tail[1:])
                        author, dates = m.groups()
                        rightsholders.append(author)
                        contributors.append(author)
                    else:
                        m = name_re.match(e.tail)
                        if m is not None:
                            author, dates = m.groups()
                            contributors.append(author)

                self.credits[chapter] = {
                    "contributors":contributors,
                    "rightsholders": rightsholders,
                    }
                self.titles.append(title)
                self.contributors.update(contributors)

        except StopIteration:
            log('Apparently run out of chapters on title %s!' % title)




class TWikiChapter(BaseChapter):
    image_cache = ImageCache()

    def __init__(self, server, book, chapter_name, html, use_cache=False,
                 cache_dir=None):
        self.server = server
        self.book = book
        self.name = chapter_name
        self.use_cache = use_cache
        if cache_dir:
            self.image_cache = ImageCache(cache_dir)
        self._loadtree(html)

    def localise_links(self):
        """Find image links, convert them to local links, and fetch
        the images from the net so the local links work"""
        images = []
        def localise(oldlink):
            fragments = urlsplit(oldlink)
            if '.' not in fragments.path:
                log('ignoring %s' % oldlink)
                return oldlink
            base, ext = fragments.path.rsplit('.', 1)
            ext = ext.lower()
            if (not fragments.scheme.startswith('http') or
                (fragments.netloc != self.server and 'flossmanuals.net' not in fragments.netloc) or
                ext not in ('png', 'gif', 'jpg', 'jpeg', 'svg', 'css', 'js') or
                '/pub/' not in base
                ):
                log('ignoring %s' % oldlink)
                return oldlink

            newlink = self.image_cache.fetch_if_necessary(oldlink, use_cache=self.use_cache)
            if newlink is not None:
                images.append(newlink)
                return newlink
            log("can't do anything for %s -- why?" % (oldlink,))
            return oldlink

        self.tree.rewrite_links(localise, base_href=('http://%s/bin/view/%s/%s' %
                                                     (self.server, self.book, self.name)))
        return images


#XXX almost certainly broken and out of date!
class Author(object):
    def __init__(self, name, email):
        self.name = name
        self.email = email

class ImportedChapter(TWikiChapter):
    """Used for git import"""
    def __init__(self, lang, book, chapter_name, text, author, email, date, server=None,
                 use_cache=False, cache_dir=None):
        self.lang = lang
        self.book = book
        self.name = chapter_name
        self.author = Author(author, email)
        self.date = date
        if server is None:
            server = '%s.flossmanuals.net' % lang
        self.server = server
        self.use_cache = use_cache
        if cache_dir:
            self.image_cache = ImageCache(cache_dir)
        #XXX is text html-wrapped?
        self._loadtree(text)

    def as_twikitext(self):
        """Get the twiki-style guts of the chapter from the tree"""
        text = etree.tostring(self.tree.find('body'), method='html')
        text = re.sub(r'^.*?<body.*?>\s*', '', text)
        text = re.sub(r'\s*</body>.*$', '\n', text)
        return text
