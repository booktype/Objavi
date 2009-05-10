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


//const MODE = 'TRANSFORM';
//const MODE = 'MEDIABOX';
const MODE = 'COMICBOOK';

function margins_wtf(){
    print("what?");
}

function transform_page(page, offset){
    page.setTransformMatrix([1, 0, 0, 1, offset, 0]);
}

function shift_page_mediabox(page, offset, width, height){
    var box = page.mediabox();
    var x = box[0];
    var y = box[1];
    var w = box[2] - box[0];
    var h = box[3] - box[1];

    if (width || height){
        print("resizing from " + w + ", " + h + " to " + width + ", " + height);
        print("x, y = " + x + ", " + y + "; dw, dh =  " + (width - w) + ", " + (height - h));
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


function shift_margins(pdfedit, filename, offset_s){
    var offset = parseFloat(offset_s);
    if (isNaN(offset)){
        print ("offset not set or unreadable ('" + offset_s + "' -> '" + offset +"'), using default of " + DEFAULT_OFFSET);
        offset = DEFAULT_OFFSET;
    }

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
        newfilename = re.cap(1) + '-' + MODE + '.pdf';
    }
    Process.execute("cp " + filename + ' ' + newfilename);


    var pdf = pdfedit.loadPdf(newfilename, 1);

    if (MODE == 'TRANSFORM')
        process_pdf(pdf, offset, transform_page);
    else if (MODE == 'MEDIABOX')
        process_pdf(pdf, offset, shift_page_mediabox);
    else if (MODE == 'COMICBOOK')
        process_pdf(pdf, offset, shift_page_mediabox, COMIC_WIDTH, COMIC_HEIGHT);
    pdf.save();
    pdf.unloadPdf();
}



/* This file gets executed *twice*: once as it gets loaded and again
 as it gets "called". The first time it recieves an extra command line
 parameter -- the name of the "function", which is the name of the
 script (or an abbreviation thereof).

 So to do things only once, we count parameters and only do anything
 if there are 0 or 2.
 */

print("in shift_margins");

var p = parameters();

if (p.length == 2){
    shift_margins(this, p[0], p[1]);
}
else if (p.length == 0){
    //no parameters given -- use the test example.
    shift_margins(this);
}
else {
    print("not processing with " + (p.length) + " parameters");
}

/*debug*/
for (var i = 0; i < p.length; i++){
    print(p[i]);
}


