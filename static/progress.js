

function objavi_show_progress(task){
    var e =$("#" + task);
    e.css("color", "black");
    e.next().css("color", "red");

    if (task == 'finished'){
        $(".oncomplete").css("display", "box");
        //document.write("</body></html>");
    }
}