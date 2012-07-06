
Introduction
------------

Objavi is a publishing engine primarly intender for exporting Booktype
books to PDF, EPUB or ODF for distribution or printing.  The name comes
from the Croatian word "objavi!" meaning "publish!".

Objavi is primarily written in Python, with a substantial amount of
QSAScript (an ECMAscript variant) and some Javascript, HTML, and CSS.

The development of Objavi was supported by Internews.  It was
extended to produce EPUB documents with support from the Internet
Archive.

Currently Objavi is part of the Booktype project which is being developed
by the Sourcefabric organization (www.sourcefabric.org).


Installation
------------

See the INSTALL.txt file for installation instructions.


More Info
---------

Objavi is part of the Booktype project, so they shared support and
development forums.

Wiki
https://wiki.sourcefabric.org/display/Booktype/Booktype

Support forum
http://forum.sourcefabric.org/categories/booktype-support

Development forum
http://forum.sourcefabric.org/categories/booktype-development

Bug tracker
http://dev.sourcefabric.org/browse/OB



The objavi process
------------------

Objavi starts with a "booki-zip", as defined in the file
"doc/booki-zip-standard.txt".  This might be sourced from a Booktype
instance, or from TWiki via the booki-twiki-gateway script, or perhaps
form an EPUB imported via Espri.

PDF Output
~~~~~~~~~~
If a PDF is required, the HTML is concatenated, various extra bits are
inserted, and the wkhtmltopdf program rederes it using WebKit.

At this point the PDF has no page numbers, no gutters, no table of
contents, and is using a too big paper size.  In order to write a
table of contents, an outline of the PDF is extracted and laid out as
html.  The table of contents thus generated is combined with other
preliminary pages and another PDF is created.

If a book PDF is required, Pdfedit is used to crop the pages down to
size and to shift them alternately left and right, creating a gutter
for the spine of the book.  Then pdfedit is used again to add page
numbers to both PDFs, with lowercase roman numbers being used for the
preliminary pages.

Finally the two PDFs are combined using pdftk and, optionally, spun
180 degrees so they appear upside down.  If a right-to-left book is
printed like this on a left-to-right printer, the binding will be on
the correct side.

Pdfedit and wkhtmltopdf both require an X server to run, for which
Xvfb is used.

For newspaper format, the page size is set to the column width, and
pdfnup is used to arrange the columns on another page.

OpenOffice output
~~~~~~~~~~~~~~~~~
ODF output was introduced with Objavi 2.1.  This uses an Open Office
instance controlled by pyuno.

EPUB output
~~~~~~~~~~~
The html in the booki-zip is manipulated into xhtml using lxml, and
the structural information and metadata is converted into EPUB form.
