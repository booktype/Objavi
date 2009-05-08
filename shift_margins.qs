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

//also .onLoad()

//addText(605,906,605,906,684,438)


function margins_wtf(){
    print("what?");

}



function process_page(page, dir){
    page.setTransformMatrix([1, 0, 0, 1, dir * 30, 0]);
}

function process_pdf(pdf){
    //var pdf = this.document();
    var dir = 1;
    var pages = pdf.getPageCount();

    var i;
    for (i = 1; i <= pages; i++){
        process_page(pdf.getPage(i), dir);
        dir = -dir;
    }

    pdf.saveAs('/tmp/test.pdf');
}


function margins_init(pdfedit){
    //var filename = pdfedit.takeParameter();
    var filename = "farsi-wk-homa.pdf";
    pdfedit.onLoadUser = function () {
        process_pdf(pdfedit.document);
    };
    var pdf = pdfedit.loadPdf(filename);
    process_pdf(pdf);
    pdf.unLoadPdf();
}


function shift_margins(){
    process_pdf(this.document);
}


function margins_help() {
    print("Usage: shift_margins FILENAME AMOUNT");
    exit(1);
}

function margins_fail(err) {
    print("shift_margins didn't work");
    print(err);
    margins_help();
}

var p = parameters();
if (p.length != 2) {
    print("got " +  " parameters" + parameters);
    //margins_help();
}
//var pdffile = p[0];
//var amount = p[1];
//if (! exists(pdffile))
//    margins_fail(pdffile + " does not exist");


//shift_margins();
margins_init(this);


