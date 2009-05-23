#!/usr/bin/python
"""Make a pdf from the specified book."""
import os, sys
import cgi
import re
import tempfile
from urllib2 import urlopen
from getopt import gnu_getopt
from subprocess import Popen, check_call

import lxml.etree, lxml.html


SERVER_NAME = os.environ.get('SERVER_NAME', 'en.flossmanuals.net')

TOC_URL = "http://%s/pub/%%s/_index/TOC.txt" % SERVER_NAME
BOOK_URL = "http://%s/bin/view/%%s/_all?skin=text" % SERVER_NAME
ADD_TEMPLATE = False


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

_files_to_rm = []

def save_tempfile(data, **kwargs):
    """Save the data in a tempfile and put the filename on the
    clean-up list.  A sensible keyword argument might be
    suffix='.css'."""
    fh, fn = tempfile.mkstemp(**kwargs)
    os.write(fh, data)
    os.close(fh)
    _files_to_rm.append(fn)
    return os.path.abspath(fn)

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
            yield (f.next().strip(), f.next().strip(), f.next().strip())
        except StopIteration:
            break
    f.close()





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


def make_pdf(htmltree, bookid):
    """Make a pdf of the HTML, using webkit"""
    html_file = '/tmp/%s.html' % bookid
    pdf_file = '/tmp/%s.pdf' % bookid
    html_text = lxml.etree.tostring(htmltree, encoding='utf-8', method="html")
    f = open(html_file, 'w')
    f.write(html_text)
    f.close()
    
    check_call(['wkhtmltopdf', '-s', 'B5', html_file, pdf_file])
    
    
    #check_call(['pdfedit', '-s', 'shift_margins', 'shift_margins',
    #           '20', 'original/farsi-wk-narrow-scheherazadehe.pdf', 'COMICBOOK', 'RTL'])





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

    headings = htmltree.cssselect('h1')

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
            ## #XXX this has to go below! in add_section_titles!
            ## initial = h1.makeelement("strong", Class="initial")
            ## h1.insert(0, initial)
            ## initial.tail = h1.text
            ## initial.text = "%s." % chapter
            ## h1.text = ''

            chapter += 1

        elif status == '0':
            contents.append(section_tmpl % text)
            #XXX interstitial pages need to be made with the main PDF

        else:
            log("mystery TOC line: %s %s %s" % (status, chapter_url, text))

    doc = '\n'.join(headers) + '\n'.join(contents) + footer
    #return doc


def add_section_titles(htmltree, toc):
    headings = iter(htmltree.cssselect('h1'))
    chapter = 1
    section = None
    
    
    for status, chapter_url, text in toc:
        if status == '1' and section is not None:
            #  chapter heading
            h1 = headings.next()
            title = h1.text_content()            
            item = h1.makeelement('div', Class='chapter')
            
            item.text = title
            section.append(item)
            if not section.getnext(): #XXX how to tell that the section has not been placed?
                h1.addprevious(section)

            #put a bold number at the beginning of the h1
            initial = h1.makeelement("strong", Class="initial")
            h1.insert(0, initial)
            initial.tail = h1.text
            initial.text = "%s." % chapter
            h1.text = ''
            chapter += 1

                            
        elif status == '0':
            section = htmltree.makeelement('div', Class="subsection")
            # it would be natural to use h1 here, but that would muck
            # up the h1 iterator. (original Pisa Objavi uses <h0>).
            heading = section.makeelement('div', Class="subsection-heading")
            heading.text = text



if __name__ == '__main__':
    args = parse_args()
    web_name = args['webName']

    htmltree = get_book(web_name)
    toc = list(toc_reader(web_name))

    add_section_titles(htmltree, toc)
    
    pdfname = make_pdf(htmltree, web_name)
    
    contents = make_contents(htmltree, toc)


