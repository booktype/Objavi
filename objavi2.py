#!/usr/bin/python
"""Make a pdf from the specified book."""
import os, sys
import cgi
import re
import urllib
from getopt import gnu_getopt

ENV = os.environ()
SERVER_NAME = ENV.get('SERVER_NAME', 'en.flossmanuals.net')

ARG_VALIDATORS = {
    "webName": lambda x: '/' not in x and '..' not in x,
    "css": None,
    "title": None,
    "header": None,
    "isbn": None,
    "license": None,
}

__doc__ += 'Valid arguments are: ' + ', '.join(ARG_VALIDATORS.keys())

def log(*messages):
    for m in messages:
        print >> sys.stderr, m

def parse_args():
    """Read and validate CGI or commandline arguments, putting the
    good ones into the returned dictionary.  Command line arguments
    should be in the form --title='A Book'.
    """    
    query = cgi.FieldStorage
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


TOC_PATH="/var/www/write/pub/%s/_index/TOC.txt"

def toc_reader(name):
    f = open(TOC_PATH % name)
    while True:
        try:
            yield (f.next(), f.next(), f.next())
        except StopIteration:
            break
    f.close()

def get_book(name):
    stream = urlopen("http://%s/bin/view/%s/_all?skin=basic" % (SERVER_NAME, name))
    html = stream.read()



def make_pdf(html, name):
    data = []
    current_heading = 1
    num_heading = 0
    chapters = []

def make_toc(html, name):
    toc = []

    for status, chapter_url, desc in toc_reader(name):
        # status is
        #  0 - section heading with no chapter
        #  1 - chapter heading
        #  2 - book title
        #
        # chapter_url is twiki name of the chapter
        # desc is the human readable name of the chapter.
        # XXX it may differ from the H1
        if status == '0':
            if current_heading + num_heading != 1:
	        data.append(_showHeading(web, current_heading, chapters))
	        chapters = []
            current_heading += num_heading
            num_heading = 0
            data.append('<h0>%s</h0>\n<div class="fmtoc">' % desc)

        elif status == '1':
            chapters.append(chapter_url)
            data.append('%s%s<br />\n' % (current_heading + num_heading, description))
            num_heading += 1


    data.append(_showHeading(web, current_heading, chapters))



#XXX need to do this differently
# 1. get whole html
# 2. fix headings, remove META (in python or javascript)


def _showHeading(web, num_heading, chapters):
    html = []

    html.append("</div></fmsection><p></p>\n")

    n = 0
    for chapter in chapters:
        topicData = readTopicText(web, chapter)
        topicData = expandCommonVariables(topicData, "neki topic", web)
        topicData = renderText(topicData, web)
        for line in topicData.split('/n'):
            if '<h1>' in line:
                html.append(line.replace('<h1>', '<h1><span class="fminitial">%s</span>' % num_heading + n))
                n += 1
            else :
                html.append(re.sub('/%META:\w+{.*?}%/', '/', line))

   return ''.join(html)






if __name__ == '__main__':
    args = parse_args()
    web_name = args['webHome']
    html = get_book(web_name)

    pdfname = make_pdf(html, manual)
