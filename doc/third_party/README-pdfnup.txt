WHENCE PDFNUP?
==============

The file bin/pdfnup is a slightly modified variant of version 1.20 of
David Firth's pdfnup program from the PDFjam package.

It is copyright David Firth, and licensed under the GPL version 2 (see
COPYING).  This license is slightly different from most other parts of
Objavi which are available under GPL version 2 or greater.  If you
decide to use GPLv3, you have to leave out bin/pdfnup.

The PDFjam homepage is http://www.warwick.ac.uk/go/pdfjam

CHANGES
=======

The script was modified to allow arbitrary output page sizes using the
following options:

 --paperwidth    <n><units>
 --paperheight   <n><units>

For example, --paperwidth 500mm --paperheight 707mm would specify B2
paper.

The file pdfnup.diff contains the changes (not counting the accidental
deletion of trailing whitespace).

POSSIBLY OBSOLETE.
==================

According to http://www.warwick.ac.uk/go/pdfjam, version 2 of pdfnup
offers a way of specifying arbitrary paper sizes.
