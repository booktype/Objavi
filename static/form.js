
function toggle_advanced(){
    var adv = $(".advanced");
    if (adv.filter(".gone").length){
        $("#toggle-advanced").text('Hide advanced options');
        adv.removeClass("gone");
    }
    else {
        $("#toggle-advanced").text('Show advanced options');
        adv.addClass("gone");
    }
    return false;
}


function css_mode_switch(){


}








function onload(){
    $(".advanced").addClass("gone");

    if ($("#toggle-advanced").length == 0){
        $("#form").before('<b id="toggle-advanced" >Show advanced options</b>');
    }

    $("#toggle-advanced").click(toggle_advanced);
}


$(onload);
