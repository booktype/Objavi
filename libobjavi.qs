/*
Part of Objavi2, which makes pdf versions of FLOSSManuals books.
This is a QSA script library for pdfedit which provides various page
manipulation routines.

Copyright (C) 2009 Douglas Bagnall

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/

/*
 * Shift pages alternately left or right, and add page numbers in the
 * outer corners.
 *
 * This is a QSA script for pdfedit. QSA is a (deprecated) dialect of
 * ecmascript used for scripting QT applications like pdfedit.
 *
 */

const DEFAULT_OFFSET = 25;
/* FLOSS Manuals default book size at lulu: 'Comicbook', 6.625" x 10.25" */
const COMIC_WIDTH = (6.625 * 72);
const COMIC_HEIGHT = (10.25 * 72);

const PAGE_NUMBER_SIZE = 11;

const DEFAULT_DIR = 'LTR';

const DEFAULT_NUMBER_STYLE = 'latin';
const DEFAULT_ENGINE = 'webkit';

function transform_page(page, offset){
    page.setTransformMatrix([1, 0, 0, 1, offset, 0]);
}

function rotate_page180(page){
    /* From the PDF reference:
     *
     * Rotations are produced by
     *  [cos(theta) sin(theta) −sin(theta) cos(theta) 0 0],
     * which has the effect of rotating the coordinate
     * system axes by an angle theta counterclockwise.
     *
     * but the rotation is about the 0,0 axis: ie the top left.
     * So addin the width and height is necessary.
     *
     * There is *also* a Rotate key in the page or document dictionary
     * that can be used to rotate in multiples of 90 degrees. But I did
     * not find that first, and it fails mysteriously in pdfedit.
     *
     *     var d = page.getDictionary();
     *     d.add('Rotate', createInt(180));
     *
     */
    var box = page.mediabox();
    //print("box is " + box);

    angle = Math.PI ;
    var c = Math.cos(angle);
    var s = Math.sin(angle);
    page.setTransformMatrix([c, s, -s, c, box[2], box[3]]);
}

function adjust_for_direction(pdf, dir){
    /* RTL book have gutter on the other side */
    /*rotate the file if RTL*/
    if (dir == 'RTL'){
        //offset = -offset;
        process_pdf(pdf, rotate_page180);
    }
}

function  prepend_content(page, content, prepended_op){
    /* Webkit applies a transformation matrix so it can write the pdf
     * using its native axes.  That means, to use the default grid we
     * need to either insert the page number before the webkit matrix,
     * or apply an inverse.  The inverse looks like:
     *
     * createOperator("cm", iprop_array('nnnnnn', 16.66667, 0, 0, -16.66667, -709.01015, 11344.83908));
     *
     * but it is simpler to jump in first.
     *
     * XXX warning: the order in which these things are applied can matter.
     */
    if (prepended_op == undefined)
        prepended_op = 'cm';

    var stream = page.getContentStream(0);
    var iter = stream.getFirstOperator().iterator();
    var op;
    do {
        op = iter.current();
        if (op.getName() == prepended_op){
            iter.prev();
            op = iter.current();
            break;
        }
    } while (iter.next());

    stream.insertOperator(op, content);
}


function grow_and_shift_page(page, data){
    //get the box size in order to recentre (i.e. add half width & height delta)
    var box = page.mediabox();
    var x = box[0];
    var y = box[1];
    var w = box[2] - box[0];
    var h = box[3] - box[1];

    page.setMediabox(x, y, x + data.width, y + data.height);

    var dx = data.offset + (width - w) * 0.5;
    var dy = (height - h) * 0.5;

    var cm = createOperator("cm", iprop_array('nnnnnn', 1, 0, 0, 1, dx, dy));
    prepend_content(page, cm, 'q');
}



function shift_page_mediabox(page, data){
    var box = page.mediabox();
    var x = box[0];
    var y = box[1];
    var w = box[2] - box[0];
    var h = box[3] - box[1];

    if (data.width || data.height){
        /*resize each page, so put the mediabox out and up by half of
        the difference.
         XXX should the page really be centred vertically? */
        x -= 0.5 * (data.width - w);
        y -= 0.5 * (data.height - h);
        w = data.width;
        h = data.height;
        //print("now x, y = " + x + ", " + y);
    }
    page.setMediabox(x - data.offset, y, x + w - data.offset, y + h);
}

function add_transformation(page, data){
    var t = data.transform;
    var cm = createOperator("cm", iprop_array('nnnnnn', t[0], t[1], t[2], t[3], t[4], t[5], t[6]));
}



/*
 * Helper functions for creating pdf operators. You can create an
 * IPropertyArray or a PdfOperator like this:
 *
 * var array = iprop_array("Nnns", "Name", 1, 1.2, "string"); var rg =
 * operator('rg', "nnn", 0, 1, 0);
 *
 * where the first argument to operator and the second to iprop_array
 * is a template (ala Python's C interface) that determines the
 * interpretation of subsequent parameters. Common keys are 'n' for
 * (floaing point) number, 's' for string, 'N' for name, 'i' for
 * integer. See the convertors object below.
 *
 */

var convertors = {
    a: createArray,
    b: createBool,
    //c: createCompositeOperator,
    d: createDict,
    o: createEmptyOperator,
    i: createInt,
    N: createName,
    O: createOperator,
    n: createReal,
    r: createRef,
    s: createString,
    z: function(x){ return x; } //for pre-existing object, no processing.
};

function iprop_array(pattern){
    //print("doing " + arguments);
    var array = createIPropertyArray();
    for (i = 1; i < arguments.length; i++){
        var s = pattern.charAt(i - 1);
        var arg = arguments[i];
        var op = convertors[s](arg);
        array.append(op);
    }
    return array;
}


/* roman_number(number) -> lowercase roman number + approximate width */
function roman_number(number){
    var data = [
        'm', 1000,
        'd', 500,
        'c', 100,
        'l', 50,
        'x', 10,
        'v', 5,
        'i', 1
    ];

    var i;
    var s = '';
    for (i = 0; i < data.length; i += 2){
        var value = data[i + 1];
        var letter = data[i];
        while (number >= value){
            s += letter;
            number -= value;
        }
    }

    var subs = [
        'dcccc', 'cm',
        'cccc', 'cd',
        'lxxxx', 'xc',
        'xxxx', 'xl',
        'viiii', 'ix',
        'iiii', 'iv'
    ];
    for (i = 0; i < subs.length; i+= 2){
        s = s.replace(subs[i], subs[i + 1]);
    }

    /* Try to take into account variable widths.
     * XXX these numbers are made up, and font-specific.
     */
    var widths = {
        m: 0.9,
        d: 0.6,
        c: 0.6,
        l: 0.3,
        x: 0.6,
        v: 0.6,
        i: 0.3
    };

    var w = 0;
    for (i = 0; i < s.length; i++){
        w += widths[s.charAt(i)];
    }

    return {
        text: s,
        width: w
    };
}


/* change_number_charset(number, charset) -> unicode numeral + approx. width
 farsi =  '۰۱۲۳۴۵۶۷۸۹';
 arabic = '٠١٢٣٤٥٦٧٨٩';
 */
function change_number_charset(number, charset){
    var charsets = {
        arabic: ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'],
        farsi:  ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
    };
    if (charset == undefined)
        charset = 'arabic';
    var numerals = charsets[charset];
    var west = number.toString();
    var i;
    var s = '';
    for (i = 0; i < west.length; i++){
        var c = west.charAt(i);
        s += numerals[parseInt(c)];
    }
    //lazy guess at width
    var w = 0.6 * s.length;
    return {
        text: s,
        width: w
    };
}

function latin_number(number){
    var text = number.toString();
    /* It would be nice to know the bounding box of the page number,
     but it is not rendered during this process, so we have to guess.
     All Helvetica numerals are the same width (approximately N shape)
     so I'll assume 0.6ish.
     */
    return {
        text: text,
        width: text.length * 0.6
    };
}

var stringifiers = {
    roman:  roman_number,
    arabic: change_number_charset,
    farsi:  change_number_charset,
    latin:  latin_number
};

function add_page_number(page, number, dir, style, margin, bottom,
                         preceding_operators){
    //print(' ' + number + ' ' +  dir + ' ' + style);
    if (! style in stringifiers || style == undefined){
        style = 'latin';
    }
    var box = page.mediabox();
    var h = PAGE_NUMBER_SIZE;
    var n = stringifiers[style](number, style);
    var text = n.text;
    var w = n.width * h;

    var y = box[1] + bottom;
    var x = box[0] + margin;

    if ((number & 1) == (dir != 'RTL')){
        x = box[2] - margin - w;
    }

    var q = createCompositeOperator("q", "Q");
    var BT = createCompositeOperator("BT", "ET");

    /* it would be nice to use the book's font, but it seems not to
    work for unknown reasons.  */
    page.addSystemType1Font("Helvetica");
    var font = page.getFontId("Helvetica"); // probably 'PDFEDIT_F1'

    var rg = createOperator("rg", iprop_array('nnn', 0, 0, 0));
    var tf = createOperator("Tf", iprop_array('Nn', font, h));
    var td = createOperator("Td", iprop_array('nn', x, y));
    var tj = createOperator("Tj", iprop_array('s', text));
    var et = createOperator("ET", iprop_array());
    var end_q = createOperator("Q", iprop_array());

    BT.pushBack(rg, BT);
    BT.pushBack(tf, rg);
    BT.pushBack(td, tf);
    BT.pushBack(tj, td);
    BT.pushBack(et, tj);

    /*If given extra operators, push them in first */
    if (0 && preceding_operators != undefined){
        print('' + preceding_operators[0]);
        var i;
        for (i = 0; i < preceding_operators.length; i++){
            q.pushBack(preceding_operators[i], q);
        }
    }

    q.pushBack(BT, q);
    q.pushBack(end_q, BT);

    var ops = createPdfOperatorStack();
    ops.append(q);
    page.appendContentStream(ops);
}



function number_pdf_pages(pdf, dir, number_style, start,
                          margin, bottom,
                          preceding_operators){
    var pages = pdf.getPageCount();
    var i;
    var offset = 0;
    print("numbers start at " + start + "; offset is " + offset + "sum = " + (start + offset));
    start = parseInt(start) || 1;
    if (start < 0){
        /*count down (-start) pages before beginning */
        offset = -start;
        start = 1;
    }
    else {
        /* start numbering at (start) */
        offset = 1 - start;
    }
    for (i = start; i <= pages - offset; i++){
        add_page_number(pdf.getPage(i + offset), i, dir, number_style,
                        margin, bottom, preceding_operators);
    }
}


function process_pdf(pdf, func, data, skip_start, skip_end){
    var pages = pdf.getPageCount();
    var i = 1;
    if (! isNaN(skip_start)){
        print ("skipping " + skip_start + "pages");
        i += skip_start;
        if (skip_start & 1)
            data[data.flip] = -data[data.flip];
        print (data.flip + " is  now " + data[data.flip]);
    }
    if (! isNaN(skip_end)){
        pages -= skip_end;
    }
    for (; i <= pages; i++){
        func(pdf.getPage(i), data);
        if (data != undefined && data.flip)
            data[data.flip] = -data[data.flip];
    }
}

function even_pages(pdf){
    /* if the pdf has an odd number of pages, cut one off the end.
     * The pdf generator should have made an extra page in case this is necessary.
     */

    var pages = pdf.getPageCount();
    if (pages & 1){
        pdf.removePage(pages); //one-based numbering
    }
}


function save_text_index(pdf, filename){
    //create an index file for finding chapter page numbers
    var pages = pdf.getPageCount();
    //open file
    var outfile = new File(filename);
    outfile.open(File.WriteOnly);

    var write = function(x){
        outfile.write(x + '\n');
    };

    for (var i = 1; i <= pages; i++){
        write('\n-=-=- Magic Page Separating Line Not Found In Any Books -=-=-');
        write(i);
        write((pdf.getPage(i).getText()));
    }

    outfile.close();
}





function parse_options(parameters, options, convertors){
    /* split parameters on the first '=' and return a mapping object.
     * a mapping of default options can be passed in. */
    if (options == undefined)
        options = {};
    if (convertors == undefined)
        convertors = {};

    print(parameters + '');
    var i;
    for (i = 0; i < parameters.length; i++){
        var p = parameters[i];
        if (p == 'h' || p == 'help')
            commandline_help(options);

        var split = p.indexOf('=');
        var key = p.substring(0, split);
        var value = p.substring(split + 1);
        if (key in convertors)
            options[key] = convertors[key](value);
        else
            options[key] = value;
    }
    return options;
}

function commandline_help(options){
    print("options are:");
    var padding = "                   ";
    for (var o in options){
        print(o + padding.substring(0, padding.length - o.length) + '[' + options[o] + ']');
    }
    exit(0);
}
