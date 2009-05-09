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


function margins_wtf(){
    print("what?");
}


function transform_page(page, offset){
    page.setTransformMatrix([1, 0, 0, 1, offset, 0]);
}

function shift_page_mediabox(page, offset){
    var box = page.mediabox();
    page.setMediabox(offset, box[1], box[2] -box[0] + offset, box[3]);

}


/*
for (i=1; i<= pages; i++){
    var offset = (i &1) * 50 - 25;
    var page = document.getPage(i);
    var box = page.mediabox();
    page.setMediabox(offset, box[1], box[2] + offset -box[0], box[3]);
}
*/

function process_pdf(pdf, offset){
    var pages = pdf.getPageCount();
    var i;
    for (i = 1; i <= pages; i++){
        shift_page_mediabox(pdf.getPage(i), offset);
        offset = -offset;
    }
    //pdf.saveAs('/tmp/test.pdf');
}


function shift_margins(pdfedit, filename, offset){
    if (filename == undefined){
        filename = '/tmp/test-src.pdf';
        Process.execute("cp original/farsi-wk-homa.pdf " + filename);
    }
    if (offset == undefined){
        offset = 25;
    }
    var pdf = pdfedit.loadPdf(filename, 1);
    process_pdf(pdf, offset);
    //pdf.saveAs('/tmp/test2.pdf');
    pdf.save();
    pdf.unloadPdf();
}


print("in shift_margins");
var p = parameters();

if (p.length == 2){
    shift_margins(this, p[0], p[1]);
}
else if (p.length == 0){
    //no parameters given
    shift_margins(this);
}
else {
    print("not processing with " + (p.length) + " parameters");
}


/* if 1 or 3 parameters, one of them is the name of the 'function' and
 this will wheel around again.*/

for (var i = 0; i < p.length; i++){
    print(p[i]);
}


