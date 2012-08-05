# This file is part of Objavi.
# Copyright (c) 2012 Borko Jandras <borko.jandras@sourcefabric.org>
#
# Objavi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Objavi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Objavi.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

from objavi import config
from objavi.pdf import concat_pdfs

import re
import hashlib
import tempfile
from subprocess import Popen, PIPE

from django.conf import settings
from django.http import HttpResponse


FONTS_PER_PAGE = 4


def get_font_list():
    p = Popen(['fc-list'], stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    fonts = set(re.findall(r"^([^:,]+)", out.strip().replace('\-', '-'), re.M))
    return sorted(fonts, key=str.lower)


def font_html(fonts, example_template, dir="LTR"):
    html = ['<html dir="%s"><meta http-equiv="content-type" content="text/html; charset=utf-8"> <style>'
            '.font-name {background: #ffc; padding: 0.25em; font-family: "Dejavu Sans", sans-serif}'
            ' div{padding:0.9em 0}'
            '</style><body>' % dir]
    for f in fonts:
        html.append(example_template % {'font': f})
    html.append('</body></html>')
    return '\n'.join(html)


def font_pdf(html, pdfname):
    fh, htmlname = tempfile.mkstemp(suffix='.html', dir=config.TMP_DIR)
    os.write(fh, html)
    os.close(fh)
    cmd = [#'xvfb-run',
           config.WKHTMLTOPDF, '-q',
           '-s', 'A4',
           htmlname, pdfname]

    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    r = p.communicate()


def font_pdf_multipage(pdfname, fonts, example_template, dir):
    """Make a PDF one page at a time, so as not to use up all
    the computer's memory when using non-latin scripts."""
    pages = []
    i = 0
    tmpdir = tempfile.mkdtemp()
    while i < len(fonts):
        page_file = os.path.join(tmpdir, '%s.pdf' % (i / FONTS_PER_PAGE))
        html = font_html(fonts[i: i + FONTS_PER_PAGE], example_template, dir)
        font_pdf(html, page_file)
        pages.append(page_file)
        i += FONTS_PER_PAGE

    concat_pdfs(pdfname, *pages)
    for x in pages:
        os.remove(x)
    os.rmdir(tmpdir)


def html_font_list(fonts, name):
    f = open(name, 'w')
    for x in fonts:
        f.write(x + '\n')
    f.close()


def create_fontlist(script):
    #Instead of regenerating the pdf every time, which is expensive, keep
    #a cached version indexed by the font list and script version
    fonts = get_font_list()
    h = hashlib.sha1(str(fonts))

    #Any change to this file will effectively clear the cache.
    f = open(os.path.abspath(__file__))
    h.update(f.read())
    f.close()

    if script not in (x for x in os.listdir(config.FONT_EXAMPLE_SCRIPT_DIR) if x.isalnum()):
        script = 'latin'

    f = open(os.path.join(config.FONT_EXAMPLE_SCRIPT_DIR, script))
    example_template = f.read()
    f.close()

    #also hash the script example include
    h.update(example_template)

    pdfname = os.path.join(config.CACHE_DIR, 'font-list-%s-%s.pdf' % (script, h.hexdigest()))

    if not os.path.exists(pdfname):
        #So this particular font list has not been made before
        dir = 'RTL' if script in config.RTL_SCRIPTS else 'LTR'
        font_pdf_multipage(pdfname, fonts, example_template, dir)
        # rewrite the font-list html include
        # this will be done redundantly for each script type
        include_name = os.path.join(config.CACHE_DIR, 'font-list.inc')
        html_font_list(fonts, include_name)

    return pdfname


def view_fontlist(request):
    script = request.REQUEST.get("script", "latin")
    pdfname = create_fontlist(script)
    f = open(pdfname)
    s = f.read()
    f.close()
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=font-list.pdf"
    response.write(s)
    return response

