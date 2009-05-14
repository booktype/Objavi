// Console: shift_margins
// Description: shift margins left and right
/**** The preceding lines are pdfedit magic! do not remove them! ***/

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

const DEFAULT_DIR = 'LTR';

//const DEFAULT_MODE = 'TRANSFORM';
//const DEFAULT_MODE = 'MEDIABOX';
const DEFAULT_MODE = 'COMICBOOK';


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
     */
    var box = page.mediabox();
    print("box is " + box);

    angle = Math.PI ;
    var c = Math.cos(angle);
    var s = Math.sin(angle);
    //page.setTransformMatrix([1, 0, 0, 1, box[2], -box[3]]);
    page.setTransformMatrix([c, s, -s, c, box[2], box[3]]);
}


function shift_page_mediabox(page, offset, width, height){
    var box = page.mediabox();
    var x = box[0];
    var y = box[1];
    var w = box[2] - box[0];
    var h = box[3] - box[1];

    if (width || height){
        /*resize each page, so put the mediabox out and up by half of
        the difference.
         XXX should the page really be centred vertically? */
        x -= 0.5 * (width - w);
        y -= 0.5 * (height - h);
        w = width;
        h = height;
        print("now x, y = " + x + ", " + y);
    }
    page.setMediabox(x - offset, y, x + w - offset, y + h);
}


/** Add text line */
function puttext (op,txt) {
	var operands = createIPropertyArray ();
	operands.append (createString(txt));
	op.pushBack (createOperator("Tj",operands),op.getLastOperator());
}
/** End text */
function putendtext (op) {
	var operands = createIPropertyArray ();
	op.pushBack (createOperator("ET",operands),op.getLastOperator());
}

/** Restore graphical state. */
function putendq (op) {
	var operands = createIPropertyArray ();
	op.pushBack( createOperator("Q",operands), op.getLastOperator());
}


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
    s: createString
};


function iprop_array(pattern){
    var array = createIPropertyArray();
    for (i = 1; i < arguments.length; i++){
        var s = pattern.charAt(i - 1);
        var arg = arguments[i];
        var op = convertors[s](arg);
        array.append(op);
    }
    return array;
}



function add_page_number(page, number, dir){
    var box = page.mediabox();
    var y = box[1] + 20;
    var x;

    if ((number & 1) == (dir == 'RTL')){
        x = box[0] + 20;
    }
    else {
        x = box[2] - 40;
    }

    var q = createCompositeOperator("q","Q");
    var BT = createCompositeOperator("BT","ET");

    q.pushBack(BT, q);

    var fonts = page.getFontIdsAndNames();
    /* how do we know which is the right one?!
     * oh well... */

    var Tf_ops = iprop_array('Nn', fonts[0], 12);
    BT.pushBack(createOperator("Tf", Tf_ops), BT.getLastOperator());

    var ops = iprop_array('nn', x, y);
    op.pushBack(createOperator("Td", ops), op.getLastOperator());

    puttext(BT,text);
    putendtext(BT);
    putendq(q);

    var ops = createPdfOperatorStack();
    ops.append(q);
    page.prependContentStream(ops);
}


function number_pdf_pages(pdf, dir){
    var pages = pdf.getPageCount();
    var i;
    for (i = 1; i <= pages; i++){
        add_page_number(pdf.getPage(i), i);
    }
}


//addText(605,906,605,906,684,438)



function process_pdf(pdf, offset, func, width, height){
    var pages = pdf.getPageCount();
    var i;
    for (i = 1; i <= pages; i++){
        func(pdf.getPage(i), offset, width, height);
        offset = -offset;
    }
}


function shift_margins(pdfedit, offset_s, filename, mode, dir){
    print("got " + arguments.length + " arguments: ");
    for (var i = 0; i < arguments.length; i++){
        print(arguments[i]);
    }

    var offset = parseFloat(offset_s);
    if (isNaN(offset)){
        print ("offset not set or unreadable ('" + offset_s + "' -> '" + offset +"'), using default of " + DEFAULT_OFFSET);
        offset = DEFAULT_OFFSET;
    }

    mode = mode || DEFAULT_MODE;
    mode = mode.upper();
    dir = dir || DEFAULT_DIR;
    dir = dir.upper();

    /* Rather than overwrite the file, copy it first to a similar name
    and work on that ("saveas" doesn't work) */
    var newfilename;
    if (filename == undefined){
        newfilename = '/tmp/test-src.pdf';
        filename = '/home/douglas/fm-data/pdf-tests/original/farsi-wk-homa.pdf';
        print("using default filenamer of " + newfilename);
    }
    else {
        var re = /^(.+)\.pdf$/i;
        var m = re.search(filename);
        if (m == -1){
            print(filename + " doesn't look like a pdf filename");
            exit(1);
        }
        newfilename = re.cap(1) + '-' + mode + '.pdf';
    }
    Process.execute("cp " + filename + ' ' + newfilename);

    var pdf = pdfedit.loadPdf(newfilename, 1);

    /* add on page numbers */
    number_pdf_pages(pdf, dir);


    /* RTL book have gutter on the other side */
    /*rotate the file if RTL*/
    if (dir == 'RTL'){
        //offset = -offset;
        process_pdf(pdf, offset, rotate_page180);
    }


    if (mode == 'TRANSFORM')
        process_pdf(pdf, offset, transform_page);
    else if (mode == 'MEDIABOX')
        process_pdf(pdf, offset, shift_page_mediabox);
    else if (mode == 'COMICBOOK')
        process_pdf(pdf, offset, shift_page_mediabox, COMIC_WIDTH, COMIC_HEIGHT);


    pdf.save();
    pdf.unloadPdf();
}



/* This file gets executed *twice*: once as it gets loaded and again
 as it gets "called". The first time it recieves an extra command line
 parameter -- the name of the "function", which is the name of the
 script (or an abbreviation thereof).

 The first real parameter is the offset (a number), so it is easy to
 detect the spurious "function" parameter and do nothing in that case.

*/

print("in shift_margins");

var p = parameters();

if (p.length == 0 || ! p[0].startsWith("shi")){
    var i;
    for (i = 0; i < p.length; i++){
        print(p[i]);
    }

    /* There is no _apply_ method for functions in QSA !!  and
     * indexing past the end of an array is an error.  So fill it out
     * with some undefineds to fake variadic calling.
     */
    for (i = 0; i < 5; i++){
        p.push(undefined);
    }
    shift_margins(this, p[0], p[1], p[2], p[3], p[4]);
}
else {
    print("skipping first round");
}



