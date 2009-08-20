

bookland.py - generate EAN-13 bar codes, including ISBN and ISMN

Copyright (C) 1999-2007 Judah Milgram     

This is free software and comes with NO WARRANTY. See file COPYING for
license.

Version 1.1 is a major re-write. New features include:
  - automatic recognition and handling of ISBN-10, ISBN-13, ISMN, and EAN-13.
  - wildcard digits for any digit in product code (not limited to check digit)
  - color may be input as cmyk or rgb. Always generates cmyk for EPS output.

The program is split into two files:
  - productcode.py contains classes for the product codes themselves
  - bookland.py has the symbol classes, generates the Postscript output, and
    contains the actual application.

The program has NOT been tested. You're free to use it but make sure
you can verify the bar codes it produces before you go to press with them.

Bug reports to bookland-bugs@cgpp.com

Usage:

bookland [-h|--help] [-V|--version] [-f|--font=<font>] [-q]
      [-s|--height=<height scale>] [-r --reduction=<points>]
      [-o|outfile=<filename>] [-n|--noquietzone] [-a|--autofile]
      [--cmyk=<c,m,y,k>] [--rgb=<r,g,b>] productCode [priceCode]

Generates an EPS file with the bar code symbol to standard output
(default) or to a named file.

Options:

-h|--help - print the usage message and exit

-q - quiet operation

-V|--version - print version info and exit

-f|--font - font to use for human-readable numbers

-s|--height - bar height scale factor on <0,1>

-r|--reduction - bar width reduction in points. Don't use this
                 unless you know what you're doing.

-o|outfile - write output to named file. Otherwise sends output to stdout.
             If filename is "auto", generates file name from the product
             code number.

-n|--noquietzone - suppress the ">" character to the right of the UPC-5
                   price code. Still sets bounding box for quiet zone.

-a|--autofile - synonym for "-o auto"

--cmyk - cmyk color, comma separated, no spaces. Example:
         --cmyk 0,1,.9,0

--rgb - rgb color, comman separate, no spaces. Example:
        --rgb 1,.9,.1
	Note: color will be converted to cmyk and given as such in output file.

productCode - The product code, with all hyphenation. A single
              asterisk may be used as a wildcard if the check digit
              (or any other digit) is unknown. The program
              automatically recognizes the product code and handles
              accordingly. Examples:

              0-9669553-0-7 - interpreted as an ISBN-10. Converts this
              to an ISBN-13 and generates the EAN-13 bar code symbol with
              "ISBN 978-0-9669553-0-9" above the bars.

              0-9669553-0-* - same as above, but check digit
              calculated automatically.

              0-966*553-0-7 - same as above, but fifth digit
              calculated automatically.

              978-0-9669553-0-9 - interpreted as an ISBN-13. Generates the
              bar code symbol with "ISBN 978-0-9669553-0-9" above the bars.
       
	      978-9-8668553-0-* - same as above but check digit
	      calculated automatically.

              979-1-2345667-9-* - interpreted as an ISBN-13. Check
              digit calculated automatically. Generates bar code
              symbol with "ISBN 979-1-2345667-9-0" above the bars.

              M-123456-78-* - interpreted as ISMN. Check digit
              calculated automatically. Generates bar code symbol with
              "ISMN M-123456-78-5" above the bars.

              123456789012* - interpreted as an EAN-13. Check digit
              calculated automatically. Bar code symbol generated with
              no label above bars. The check digit is calculated as
              "8".

priceCode -   The five digit UPC-5 price code. If not given, then no
              price code bar code symbol drawn. If given with an ISMN
              or EAN-13, generates an error.

NOTE ON WILDCARD DIGITS:

Although the program can compute any single digit represented by an
asterisk, it is still preferable to enter all the digits if
possible. This allows the checksum to be verified, providing slightly
more protection against transcription errors. Remember that if you do
get a checksum error, it's not necessarily the check digit that's
wrong.
