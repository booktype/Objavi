
WK=wkhtmltopdf-static
#WK=wkhtmltopdf-static-beta

HERE=`dirname $0`
cd $HERE

for HTML in arabic*.html; do
    PDF=$HTML.pdf
    echo "outline only:"
    $WK -s A4 -T 30.5 -R 25.0 -B 32.4402777778 -L 25.0 -d 100 --outline -g $HTML $PDF
    pdftk $PDF dumpdata
    PDF2=$HTML-toc.pdf
    echo "toc + outline:"
    $WK -s A4 -T 30.5 -R 25.0 -B 32.4402777778 -L 25.0 -d 100 -t --outline -g $HTML $PDF2
    pdftk $PDF2 dumpdata
done

