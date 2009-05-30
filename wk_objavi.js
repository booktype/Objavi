// Console: wk_objavi
// Description: shift margins left and right and add page numbers for wkhtmltopdf PDFs

run("libobjavi.qs");

run( "pdfoperator.qs" ); // pdfedit stdlib, from /usr/share/pdfedit

function get_page_inverse_transform(page){
    /*This is somewhat inefficient if the only transformation is at
     the beginning of stream 0, which seems invariably to be the case.
     */

    var stream = page.getContentStream(page.getContentStreamCount() - 1);
    var op = stream.getLastOperator();
    //from /usr/share/pdfedit/pdfoperator.qs
    return get_cmToDetransformation(page, op);
}



function onConsoleStart() {
    print("in wk_objavi");

    var p = parameters();
    var offset = parseFloat(p[0]);
    if (isNaN(offset)){
        print ("offset not set or unreadable ('" + p[0] + "' -> '" + offset +"'), using default of " + DEFAULT_OFFSET);
        offset = DEFAULT_OFFSET;
    }
    var filename = p[1];
    var mode = p[2] || DEFAULT_MODE;
    mode = mode.upper();
    var dir = p[3] || DEFAULT_DIR;
    dir = dir.upper();
    var number_style = p[4] || DEFAULT_NUMBER_STYLE;
    number_style = number_style.lower();
    var number_start = p[5];

    /* Rather than overwrite the file, copy it first to a similar name
    and work on that ("saveas" doesn't work) */
    var re = /^(.+)\.pdf$/i;
    var m = re.search(filename);
    if (m == -1){
        print(filename + " doesn't look like a pdf filename");
        exit(1);
    }
    var newfilename = re.cap(1) + '-' + mode + '.pdf';
    Process.execute("cp " + filename + ' ' + newfilename);

    var pdf = this.loadPdf(newfilename, 1);

    /* for webkit we need to work out the de-transformation matrix
     *
     * it is probably [16.66667, 0, 0, -16.66667, -709.01015, 11344.83908]
     * for all pages.
     */
    var detransform = get_page_inverse_transform(pdf.getFirstPage());
    process_pdf(pdf, add_transformation, detransform);


    adjust_for_direction(pdf, offset, dir);

    flip = function(){
        this.offset = -this.offset;
    };

    if (mode == 'TRANSFORM')
        process_pdf(pdf, transform_page, {offset: offset,
                                          dir: dir,
                                          flip:flip});
    else if (mode == 'MEDIABOX')
        process_pdf(pdf, shift_page_mediabox, {offset: offset,
                                               flip:flip});
    else if (mode == 'COMICBOOK')
    process_pdf(pdf, shift_page_mediabox, {offset: offset,
                                           flip:flip,
                                           width: COMIC_WIDTH,
                                           height: COMIC_HEIGHT});


    /* add on page numbers */
    if (number_style != 'none'){
        number_pdf_pages(pdf, dir, number_style, number_start);
    }

    pdf.save();
    pdf.unloadPdf();
}









