// Console: wk_objavi
// Description: shift margins left and right and add page numbers for wkhtmltopdf PDFs

/* ^^^^ previous lines are pdfedit magic. Let them be!

Part of Objavi2, which makes pdf versions of FLOSSManuals books.

This file is QSAscript for pdfedit. It makes pdfs more book-like,
adding gutters and page numbers.

Copyright (C) 2009 Douglas Bagnall

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation; either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */



run(settings.expand("${OBJAVI_SCRIPT_DIR}/libobjavi.qs"));

run( "pdfoperator.qs" ); // pdfedit stdlib, from /usr/share/pdfedit

function get_page_inverse_transform(page){
    /*This is somewhat inefficient if the only transformation is at
     the beginning of stream 0, which seems invariably to be the case.
     */

    var stream = page.getContentStream(page.getContentStreamCount() - 1);
    var op = stream.getLastOperator();
    //from /usr/share/pdfedit/pdfoperator.qs
    var transform = get_cmToDetransformation(page, op);
    var transform = getDetransformationMatrix(page, op);
    return transform;
}

function number_check(parser, name, default_value){
    return function(s){
        var x = parser(s);
        if (isNaN(x) && name)
            throw(name + ' should be a number! (not "' + s + '")');
        if (default_value != undefined)
            return x || default_value;
        return x;
    };
}


const OPERATIONS = {
    adjust_for_direction: 1,
    resize: 2,
    transform: 4,
    shift: 8,
    page_numbers: 16,
    index: 32,
    even_pages: 64,
    scale: 128,

    dummy: 256,
    all: 0xffff
};

const DEFAULT_OPERATION = 0;

function convert_operation(x){
    if (! x){
        x = 'all';
    }
    var words = x.lower().split(',');
    var ops = 0;
    for (var i = 0; i < words.length; i++){
        var op = OPERATIONS[words[i]];
        if (op)
            ops |= op;
    }
    return ops;
}


function onConsoleStart() {
    print("in wk_objavi");

    var convertors = {
        offset: number_check(parseFloat, 'offset'),
        dir: function(x){return x.upper();},
        number_style: function(x){return x.lower();},
        centre_first: function(x){return x.lower() == 'true';},
        centre_last: function(x){return x.lower() == 'true';},
        number_start: number_check(parseInt, 'number_start', 1),
        number_bottom: number_check(parseFloat, 'number_bottom'),
        number_margin: number_check(parseFloat, 'number_margin'),
        width: number_check(parseFloat, 'width'),
        height: number_check(parseFloat, 'height'),
        operation: convert_operation
    };

    var options = {
        offset: DEFAULT_OFFSET,
        dir:    DEFAULT_DIR,
        number_style: DEFAULT_NUMBER_STYLE,
        number_start: 1,
        number_bottom: 20,
        number_margin: 60,
        filename: '',
        output_filename: undefined,
        width: COMIC_WIDTH,
        height: COMIC_HEIGHT,
        engine: DEFAULT_ENGINE,
        centre_first: 'false',
        centre_last: 'false',
        operation: DEFAULT_OPERATION
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
        newfilename = re.cap(1) + '-PDFEDIT.pdf';
    if (newfilename != options.filename)
        Process.execute("cp " + options.filename + ' ' + newfilename);

    var pdf = this.loadPdf(newfilename, 1);


    function doing_op(op){
        var ret = options.operation & OPERATIONS[op];
        if (ret)
            print("doing " + op);
        return ret;
    }

    if (doing_op('even_pages')){
        even_pages(pdf);
    }

    if (doing_op('adjust_for_direction')){
        adjust_for_direction(pdf, options.offset, options.dir);
    }

    if (doing_op('scale')) {
	process_pdf(pdf, scale_page, {width: options.width,
				      height: options.height,
                                      flip: 0})
    }

    if (doing_op('resize')){
        process_pdf(pdf, shift_page_mediabox, {offset: 0,
                                               width: options.width,
                                               height: options.height,
                                               flip: undefined
                                              });
    }
    if (doing_op('transform')){
        process_pdf(pdf, transform_page, {offset: options.offset,
                                          dir: options.dir,
                                          flip: "offset"
                                         },
                                         (options.centre_first) ? 1 : undefined,
                                         (options.centre_last) ? 1 : undefined
                   );
    }
    if (doing_op('shift')){
        process_pdf(pdf, shift_page_mediabox, {offset: options.offset,
                                               flip: "offset",
                                               width: options.width,
                                               height: options.height
                                              },
                                              (options.centre_first) ? 1 : undefined,
                                              (options.centre_last) ? 1 : undefined
                   );
    }
    if (doing_op('page_numbers') &&
        options.number_style != 'none'){
        number_pdf_pages(pdf, options.dir, options.number_style,
                         options.number_start, options.number_margin, options.number_bottom
                        );
    }
    if (doing_op('index')){
        save_text_index(pdf, newfilename+'.index');
    }

    pdf.save();

    pdf.unloadPdf();
}



