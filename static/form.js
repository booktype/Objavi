/* Part of Objavi2, which turns html manuals into books. This file
 * provides javascript to help people select the book and options they 
 * want.
 *
 * Copyright (C) 2009 Douglas Bagnall
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */

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

function load_css(){
    var server = $("#server").val();
    var textarea = $('#css-textarea-data');

    $.get("?server=" + server + "&mode=css",
          undefined, function(data){textarea.val(data);}
        );
}



function onload(){
    $(".advanced").addClass("gone");

    if ($("#toggle-advanced").length == 0){
        $("#form").after('<b id="toggle-advanced">Show advanced options</b>');
    }

    $("#toggle-advanced").click(toggle_advanced);

    $("#server").change(load_booklist);

    $("#css-control").change(css_mode_switch);
    css_mode_switch();
    //load the booklist for the selected server
    load_booklist();
}


$(onload);
