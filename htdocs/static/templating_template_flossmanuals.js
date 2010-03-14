
function get_chapter_list() {
    var chapters = [];
    var here = document.location;
    $(".menu-goes-here a").each(function (i) {
                                    if (this.href == here){
                                        $(this).parent().css('background', '#f99b1c');
                                    }
                                    chapters.push(this.href);
                                });
    var  prev, next;   
    for (var i = 0; i < chapters.length; i++){
        if (chapters[i] == here){
            if (i > 0){
                $('.left.arrow a').each(function() {
                                            this.href = chapters[i-1];
                                        });
            }
            else{
                $('.left.arrow a').each(function() {
                                            this.style.visibility = 'hidden';
                                        });                
            }
            if (i + 1 < chapters.length){
                $('.right.arrow a').each(function() {
                                             this.href = chapters[i+1];
                                         });
                }
            else{
                $('.right.arrow a').each(function() {
                                             this.style.visibility = 'hidden';
                                         });              
            }
        }
    }
    return chapters;
}    

var all_book_chapters = $(get_chapter_list);

function previous(){
    return true;
}

function next(){
    return true;
}
