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

    var convertors = {
        offset: function(x){
            x = parseFloat(x);
            if (isNaN(x))
                throw('offset should be a number!');
            return x;
        },
        mode: function(x){return x.upper();},
        dir: function(x){return x.upper();},
        number_style: function(x){return x.lower();},
        number_start: function(x){
            x = parseInt(x);
            if (isNaN(x))
                throw('number_start should be an integer!');
            return x || 1;
        }
    };
    var options = {
        offset: DEFAULT_OFFSET,
        mode:   DEFAULT_MODE,
        dir:    DEFAULT_DIR,
        number_style: DEFAULT_NUMBER_STYLE,
        number_start: '1',
        filename: '',
        output_filename: undefined,
        width: COMIC_WIDTH,
        height: COMIC_HEIGHT
    };

    options = parse_options(parameters(), options, convertors);

    /* Rather than overwrite the file, copy it first to a similar name
    and work on that ("saveas" doesn't work) */
    var re = /^(.+)\.pdf$/i;
    var m = re.search(options.filename);
    if (m == -1){
        throw(options.filename + " doesn't look like a pdf filename");
    }
    var newfilename = options.output_filename;
    if (newfilename == undefined)
        newfilename = re.cap(1) + '-' + options.mode + '.pdf';

    Process.execute("cp " + options.filename + ' ' + newfilename);

    var pdf = this.loadPdf(newfilename, 1);

    /* for webkit we need to work out the de-transformation matrix
     *
     * it is probably [16.66667, 0, 0, -16.66667, -709.01015, 11344.83908]
     * for all pages.
     */
    var detransform = get_page_inverse_transform(pdf.getFirstPage());
    process_pdf(pdf, add_transformation, detransform);


    adjust_for_direction(pdf, options.offset, options.dir);

    flip = function(){
        this.offset = -this.offset;
    };

    if (mode == 'TRANSFORM'){
        /* resize first */
        process_pdf(pdf, shift_page_mediabox, {offset: 0,
                                               width: options.width,
                                               height: options.height
                                              });
        process_pdf(pdf, transform_page, {offset: options.offset,
                                          dir: options.dir,
                                          flip: "offset"
                                         });
    }
    else if (options.mode == 'COMICBOOK'){
        process_pdf(pdf, shift_page_mediabox, {offset: options.offset,
                                               flip: "offset",
                                               width: options.width,
                                               height: options.height
                                              });

    }

    /* add on page numbers */
    if (options.number_style != 'none'){
        number_pdf_pages(pdf, options.dir,
                         options.number_style, options.number_start);
    }

    pdf.save();
    pdf.unloadPdf();
}



