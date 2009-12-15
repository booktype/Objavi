Notes regarding Objavi's interaction with TWiki
===============================================

These were once part of the main README, but are less relevant now
that Booki is becoming established.  However, they might still be of
use to someone. so here they are.

Which Objavi should I use?
==========================

Short answer
~~~~~~~~~~~~
Try both and see which you like, unless the book in question has
right-to-left text, in which case you want Objavi2.

Details
~~~~~~~
Objavi beta (written in 2008 by Aleksandar Erkalovic and Luka Frelih)
is a TWiki extension that uses Pisa to make PDFs.  Pisa lets you use
CSS rules to avoid widowed or orphaned text and to adjust margins.  In
other regards, its CSS support is variable.  This means Objavi beta
makes well laid-out books, but people writing style rules need to be
aware of its quirks and use peculiar workarounds to achieve certain
effects.  It only works with left-to-right scripts and possibly
mis-renders some of those (due to not understanding combining
characters).

Objavi2 uses Webkit to make PDFs.  Webkit is a common web browser
engine, so it interprets CSS in a fairly predictable fashion but also
has almost no concept of paged media.  It does not recognise CSS rules
for setting page sizes or margins and has limited support for
controlling page breaks.  (There are actually ways in which margins
can be customised with Webkit but Objavi2 does not yet expose them).
Webkit has very well tested Unicode support and it handles
bidirectional text.

The page-break CSS properties supported by Webkit are
page-break-before and page-break-after, which is sufficient to have
each chapter start on a new page, but not to avoid breaking up
paragraphs in unfortunate ways.

Objavi2 is somewhat faster than Objavi beta.


The FLOSS Manuals Book Format
=============================

FLOSS Manuals source HTML
~~~~~~~~~~~~~~~~~~~~~~~~~
The subset of HTML used in FLOSS Manuals books has been pragmatically
determined rather than specified.  The constraints that have shaped it
are that the source must be:

 1. easily producible and editable using the Xinha editor and by hand,
 2. printable using Objavi beta,
 3. organised into chapters, and
 4. conformant to the instincts and habits of the authors.

This has led to simplified HTML that has the following properties:

 * Each chapter starts with an <h1> heading and contains no other <h1>
   elements.

 * Each chapter is in a separate file.

 * Fixed width elements such as images are generally no bigger than
   600 pixels wide.

 * Inline style, class and id attributes are avoided.

 * Many uncommon or irrelevant tags are avoided.

 * <pre> blocks use less than about 80 columns, though this is
   commonly broken.

 * Spurious &nbsp; entities and the like are despised but are left
   unmolested in practice unless they cause obvious problems.

 * All of these guidelines are regularly broken if the printed page
   looks OK.

TOC.txt file
~~~~~~~~~~~~
In addition to the HTML chapters, the source of a FLOSS Manuals book
contains a file named TOC.txt which orders the chapters and groups
them into sections.

The TOC.txt format is quite simple but fiddly to describe and thus
undocumented.  An example can be seen here:

http://en.flossmanuals.net/pub/Audacity/_index/TOC.txt

and decoding methods can be found in the Objavi2 source.  Much of the
information encoded in the TOC.txt file is useless to Objavi.

