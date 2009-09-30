#!/usr/bin/python
import os, sys
import zipfile
from cStringIO import StringIO
import cgi
from getopt import gnu_getopt

try:
    import simplejson as json
except ImportError:
    import json

from objavi.fmbook import log, Book, make_book_name
from objavi.cgi_utils import shift_file, parse_args, optionise
from objavi.config import EPUB_DIR
from iarchive import epub as ia_epub
from booki.xhtml_utils import EpubChapter
from objavi import epub_utils

DCNS = "{http://purl.org/dc/elements/1.1/}"

USE_CACHED_IMAGES = True #avoid network -- will make out of date books in production!

BOOKI_BOOK_DIR = 'booki-books'
BOOKS = [x[:-4] for x in os.listdir(BOOKI_BOOK_DIR) if x.endswith('.zip')]


class ZipBook(Book):

    def __init__(self, zipstring, **kwargs):
        f = StringIO(zipstring)
        self.store = zipfile.ZipFile(f, 'r')
        self.info = json.loads(self.store.read('info.json'))

        metadata = self.info['metadata']
        book = metadata['fm:book']
        server = metadata['fm:server']
        bookname = make_book_name(book, server)

        Book.__init__(self, book, server, bookname, **kwargs)
        self.set_title(metadata['title'])

    def make_epub(self):
        self.epubfile = self.filepath('%s.epub' % self.book)
        ebook = ia_epub.Book(self.epubfile, content_dir='')
        manifest = self.info['manifest']
        metadata = self.info['metadata']
        toc = self.info['TOC']
        spine = self.info['spine']

        #manifest
        filemap = {} #reformualted manifest for NCX
        for ID in manifest:
            fn, mediatype = manifest[ID]
            content = self.store.read(fn)
            if mediatype == 'text/html':
                #convert to application/xhtml+xml
                c = EpubChapter(self.server, self.book, ID, content,
                                use_cache=USE_CACHED_IMAGES)
                c.remove_bad_tags()
                content = c.as_xhtml()
                fn = fn[:-5] + '.xhtml'
                mediatype = 'application/xhtml+xml'
            if mediatype == 'application/xhtml+xml':
                filemap[ID] = fn

            #XXX fix up text/html
            info = {'id': ID, 'href': fn, 'media-type': mediatype}
            ebook.add_content(info, content)

        #spine
        for ID in spine:
            ebook.add_spine_item({'idref': ID})

        #toc
        ncx = epub_utils.make_ncx(toc, metadata, filemap)
        ebook.add(ebook.content_dir + 'toc.ncx', ncx)


        #metadata -- no use of attributes (yet)
        # and fm: metadata disappears for now
        meta_info_items = []
        for k, v in metadata.iteritems():
            if k.startswith('fm:'):
                continue
            meta_info_items.append({'item': DCNS + k,
                                    'text': v}
                                   )

        #copyright
        authors = sorted(self.info['copyright'])
        for a in authors:
            meta_info_items.append({'item': DCNS + 'creator',
                                    'text': a}
                                   )
        meta_info_items.append({'item': DCNS + 'rights',
                                'text': 'This book is free. Copyright %s' % (', '.join(authors))}
                               )

        tree_str = ia_epub.make_opf(meta_info_items,
                                    ebook.manifest_items,
                                    ebook.spine_items,
                                    ebook.guide_items,
                                    ebook.cover_id)
        ebook.add(ebook.content_dir + 'content.opf', tree_str)
        ebook.z.close()

def print_form(booklink):
    print "Content-type: text/html; charset=utf-8\n"
    f = open('templates/epubjavi.html')
    template = f.read()
    f.close()

    print template % {'booklink': booklink,
                      'booklist': optionise(sorted(BOOKS))}



def epubjavi(book):
    f = open('%s/%s.zip' % (BOOKI_BOOK_DIR, book))
    zipstring = f.read()
    f.close()
    book = ZipBook(zipstring)
    book.make_epub()
    return shift_file(book.epubfile, EPUB_DIR)



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



