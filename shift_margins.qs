// Console: shift_margins
// Description: shift margins left and right
// Parameters: [input file] [margin]

/*
 * Shift pages alternately left or right, and add page numbers in the
 * outer corners.
 *
 * This is a QSA script for pdfedit. QSA is a (deprecated) dialect of
 * ecmascript used for scripting QT applications like pdfedit.
 *
 */

//to get the filename:
//string takeParameter()
//
//also .onLoad()
//
//addText(605,906,605,906,684,438)

const DEFAULT_OFFSET = 25;
const COMIC_WIDTH = (6.625 * 72);
const COMIC_HEIGHT = (10.25 * 72);

const DEFAULT_DIR = 'LTR';


//const DEFAULT_MODE = 'TRANSFORM';
//const DEFAULT_MODE = 'MEDIABOX';
const DEFAULT_MODE = 'COMICBOOK';

function margins_wtf(){
    print("what?");
}


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
        //print("resizing from " + w + ", " + h + " to " + width + ", " + height);
        //print("x, y = " + x + ", " + y + "; dw, dh =  " + (width - w) + ", " + (height - h));
        /*resize each page, so put the mediabox out and up by half of
        the difference */
        x -= 0.5 * (width - w);
        y -= 0.5 * (height - h);
        w = width;
        h = height;
        print("now x, y = " + x + ", " + y);
    }
    page.setMediabox(x - offset, y, x + w - offset, y + h);
}



/*
for (i=1; i<= pages; i++){
 var offset = (i &1) * 50 - 25;
 var page = document.getPage(i);
 var box = page.mediabox();
 page.setMediabox(offset, box[1], box[2] + offset -box[0], box[3]);
}
         */

function process_pdf(pdf, offset, func, width, height){
    var pages = pdf.getPageCount();
    var i;
    for (i = 1; i <= pages; i++){
        func(pdf.getPage(i), offset, width, height);
        offset = -offset;
    }
}


function shift_margins(pdfedit, offset_s, filename, mode, dir){
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
    for (var i = 0; i < p.length; i++){
        print(p[i]);
    }
    shift_margins(this, p[0], p[1], p[2], p[3]);
}
else {
    print("skipping first round");
}



