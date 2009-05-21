#!/usr/bin/python
"""Make a pdf from the specified book."""
import os, sys
import cgi
import re
from urllib2 import urlopen
from getopt import gnu_getopt

import lxml


ENV = os.environ()
SERVER_NAME = ENV.get('SERVER_NAME', 'en.flossmanuals.net')

TOC_URL = "http://%s/pub/%%s/_index/TOC.txt" % SERVER_NAME
BOOK_URL = "http://%s/bin/view/%%s/_all?skin=text" % SERVER_NAME

# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).
ARG_VALIDATORS = {
    "webName": lambda x: '/' not in x and '..' not in x,
    "css": None,
    "title": None,
    "header": None,
    "isbn": None,
    "license": None,
}

__doc__ += '\nValid arguments are: %s.\n' % ', '.join(ARG_VALIDATORS.keys())

def log(*messages):
    for m in messages:
        print >> sys.stderr, m

def parse_args():
    """Read and validate CGI or commandline arguments, putting the
    good ones into the returned dictionary.  Command line arguments
    should be in the form --title='A Book'.
    """
    query = cgi.FieldStorage()
    options, args = gnu_getopt(sys.argv[1:], '', [x + '=' for x in ARG_VALIDATORS])
    options = dict(options)

    data = {}
    for key, validator in ARG_VALIDATORS.items():
        value = query.getfirst(key, options.get(key, None))
        if value is not None:
            if validator is not None and not validator(value):
                log("argument '%s' is not valid ('%s')" % (key, value))
                continue
            data[key] = value

    return data


def toc_reader(name):
    """Iterate over the TOC.txt file.  For each chapter yield the
    tuple (<status>, <filename>, <title>).

    <status> is a number, with the following meaning:

          0 - section heading with no chapter
          1 - chapter heading
          2 - book title

    <filename> is twiki name of the chapter.

    <title> is a human readable title for the chapter.  It is likely to
    differ from the title given in the chapter's <h1> heading.
    """
    f = urlopen(TOC_URL % name)
    while True:
        try:
            yield (f.next(), f.next(), f.next())
        except StopIteration:
            break
    f.close()


ADD_TEMPLATE = False

def get_book(name, tidy=True):
    """Fetch and parse the raw html of the book.  If tidy is true
    (default) links in the document will be made absolute."""
    #XXX use lxml
    f = urlopen(BOOK_URL % name)
    html = f.read()
    if ADD_TEMPLATE:
        html = ('<html><head>\n<title>book</title>\n'
                '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" >'
                '</head>\n<body>\n'
                '%s\n</body></html>') % html
    f.close()
    tree = lxml.html.document_fromstring(html)
    tree.make_links_absolute(BOOK_URL % name)

    return tree


def make_pdf(htmltree):
    data = []
    current_heading = 1
    num_heading = 0
    chapters = []

def find_page(element, start=1):
    """Search through the main PDF and retunr the page on which the
    element occurs.  If start is given, the search begins on that
    page."""
    #XXX do it really.
    import random
    return start + random.randrange(1,4)

def make_contents(htmltree, toc):
    header_tmpl = '<h1>%s</h1><table class="toc">\n'
    row_tmpl = ('<tr><td class="chapter">%s</td><td class="title">%s</td>'
                '<td class="page_num">%s</td></tr>\n')
    section_tmpl = ('<tr><td></td><td class="section" colspan="2">%s</td></tr>\n')
    footer = '\n</table><small>TOC ends here</small>'

    contents = []
    headers = []

    chapter = 1
    page_num = 1
    subsections = [] # for the subsection heading pages.

    headings =  htmltree.cssselect('h1')

    for status, chapter_url, text in toc:
        # status is
        #  0 - section heading with no chapter
        #  1 - chapter heading
        #  2 - book title
        #
        # chapter_url is twiki name of the chapter
        # text is a human readable name of the chapter.
        if status == '2':
            headers.append(header_tmpl % text)

        elif status == '1':
            h1 = headings.next()
            title = h1.text_content()
            page_num = find_page(h1, page_num)
            contents.append(row_tmpl % (chapter, title, page_num))
            #put a bold number at the beginning of the h1
            initial = h1.makeelement("strong", Class="initial")
            h1.insert(0, initial)
            initial.tail = h1.text
            initial.text = "%s." % chapter
            h1.text = ''

            chapter += 1

        elif status == '0':
            contents.append(section_tmpl % text)
            #XXX interstitial pages need to be made with the main PDF

        else:
            log("mystery TOC line: %s %s %s" % (status, chapter_url, text))

    doc = '\n'.join(headers) + '\n'.join(contents) + footer
    #return doc



if __name__ == '__main__':
    args = parse_args()
    web_name = args['webHome']
    htmltree = get_book(web_name)
    pdfname = make_pdf(htmltree)
    
    toc = toc_reader(web_name)
    contents = make_contents(htmltree, toc)


