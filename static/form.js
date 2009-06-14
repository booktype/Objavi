
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
    var v = $("#css-control").val();

    function on(s){
        $('#css-' + s + '-row').removeClass("css-gone");
        $('#css-' + s + '-data').removeAttr('disabled');
    }
    function off(s){
        $('#css-' + s + '-data').attr('disabled', 'disabled');
        $('#css-' + s + '-row').addClass("css-gone");
    }

    if (v == 'default'){
        off('textarea');
        off('url');
    }
    else {
        var not_v = (v == 'url') ? 'textarea' : 'url';
        on(v);
        off(not_v);
    }
}

function load_booklist(){
    var server = $("#server").val();
    var w = $("#webName");
    var webName = w.val();
    w.attr('disabled', 'disabled');
    w.load("?server=" + server + "&webName=" + webName + "&mode=booklist",
           undefined, function(){w.removeAttr('disabled');}
    );
}



function onload(){
    $(".advanced").addClass("gone");

    if ($("#toggle-advanced").length == 0){
        $("#form").after('<b id="toggle-advanced" >Show advanced options</b>');
    }

    $("#toggle-advanced").click(toggle_advanced);

    $("#server").change(load_booklist);

    $("#css-control").change(css_mode_switch);
    $('#css-textarea-row').addClass("css-gone");
    $('#css-url-row').addClass("css-gone");
    //load the booklist for the selected server
    load_booklist();
}


$(onload);
