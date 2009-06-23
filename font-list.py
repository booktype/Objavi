#!/usr/bin/python

import config
import tempfile, os, re, sys
import hashlib
from subprocess import Popen, check_call, PIPE

def get_font_list():
    p = Popen(['fc-list'], stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    fonts = set(re.findall(r"^([^:,]+)", out.strip().replace('\-', '-'), re.M))
    return sorted(fonts, key=str.lower)


def font_div(f):
    return ('<div class="font" style="font-family: \'%s\'">'
            '<big>%s </big> '
            'The quick <b>brown fox</b> jumped over the <i>lazy dog</i>'
            '...,;:"!@#$%%^&*()1234567890</div>' % (f, f))


def font_html(fonts):
    html = ['<html><style>'
            'big {background: #ffc; padding: 0.25em} div{padding:0.6em 0}'
            '</style><body>']
    for f in fonts:
        html.append(font_div(f))
    html.append('</body></html>')
    return '\n'.join(html)

def font_pdf(html, pdfname):
    fh, htmlname = tempfile.mkstemp(suffix='.html', dir=config.TMPDIR)
    os.write(fh, html)
    os.close(fh)
    cmd = ['xvfb-run', config.WKHTMLTOPDF, '-q', '-s', 'A4',
           htmlname, pdfname]

    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    print >>sys.stderr, p.communicate()

def html_font_list(fonts, name):
    f = open(name, 'w')
    for x in fonts:
        f.write(x + '<br/>\n')
    f.close()

#Instead of regenerating the pdf every time, which is expensive, keep
#a cached version indexed by the font list and script version

fonts = get_font_list()
h = hashlib.sha1(str(fonts))
#XXX should h.update(<this file>), so new versions uncache

pdfname = os.path.join(config.BOOK_LIST_CACHE_DIR, 'font-list-' + h.hexdigest() + '.pdf')

if not os.path.exists(pdfname):
    #So this particular font list has not been made before
    html = font_html(fonts)
    font_pdf(html, pdfname)


print "Content-type: application/pdf\n"
f = open(pdfname)
print f.read()
f.close()
sys.exit()

    include_name = os.path.join(config.BOOK_LIST_CACHE_DIR, 'font-list.inc')
    html_font_list(fonts, include_name)


