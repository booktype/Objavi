#!/usr/bin/python

import lxml.html, lxml.html.clean
from lxml.html import html5parser

html ="""<html><body>
<!-- a comment -->
</body></html>
"""

#tree = lxml.html.document_fromstring(html)
tree = html5parser.document_fromstring(html)

cleaner = lxml.html.clean.Cleaner()
cleaner(tree)

