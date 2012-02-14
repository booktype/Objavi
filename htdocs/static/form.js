/* Part of Objavi2, which turns html manuals into books. This file
 * provides javascript to help people select the book and options they
 * want.
 *
 * Copyright (C) 2009 Douglas Bagnall
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License along
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
        $('.css-' + s).removeClass("hidden-css");
        $('.css-' + s + ' input').removeAttr('disabled');
        $('.css-' + s + ' textarea').removeAttr('disabled');
    }
    function off(s){
        $('.css-' + s + ' input').attr('disabled', 'disabled');
        $('.css-' + s + ' textarea').attr('disabled', 'disabled');
        $('.css-' + s).addClass("hidden-css");
    }

    if (v == 'default'){
        off('custom');
        off('url');
    }
    else {
        var not_v = (v == 'url') ? 'custom' : 'url';
        on(v);
        off(not_v);
    }
}

function mode_switch(){
    /*For openoffice mode, hide the irrelevant inputs */
    var mode = $("#mode").val();
    if (mode == 'openoffice'){
        $('.advanced').not($('.openoffice')).addClass('hidden-mode');
    }
    else {
        $('div.advanced').removeClass('hidden-mode');
    }
}

function load_booklist(){
    var server = $("#server").val();
    //if it is still a text input, replace with a select
    $("input#book").replaceWith('<select id="book" name="book"></select>');
    var w = $("#book");
    var book = w.val();
    w.attr('disabled', 'disabled');
    w.load("?server=" + server + "&book=" + book + "&mode=booklist",
           undefined, function(){w.removeAttr('disabled');}
    );
}

function load_css(){
    var server = $("#server").val();
    var textarea = $('#css');

    //Try to get CSS to suit current mode
    $.get("?server=" + server + "&mode=css&pdftype=" + $("#mode").val(),
          undefined, function(data){textarea.val(data);}
    );
}


function toggle_custom_size(){
    var v = $("#booksize").val();
    if (v == 'custom'){
        $('.booksize').removeClass("hidden");
    }
    else {
        $('.booksize').addClass("hidden");
    }
}

function onload(){
    //add the "advanced options" toggle buton before first advanced option.
    while ($("#toggle-advanced").length == 0){
        $("div.advanced").eq(0).before(
            '<button id="toggle-advanced">Show advanced options</button>');
        $("#toggle-advanced").click(toggle_advanced);
    }

    $("#booksize").change(toggle_custom_size);
    toggle_custom_size();

    $("#server").change(load_booklist);

    if ($("#css-control").length == 0){
        $(".css-url").before('<div id="css-control_div" class="advanced form-item openoffice">' +
                             '<div class="input_title">CSS mode</div>' +
                             '<div><select id="css-control">' +
                             '<option value="default" selected="selected">Server default</option>' +
                             '<option value="url">URL</option>' +
                             '<option value="custom">Custom</option>' +
                             '</select></div></div>'
                            ).attr("name", 'css');
        $('#css_div .input_title').after('<a href="#" onclick="load_css(); return false;">' +
                                         'Load default CSS for this server and mode ' +
                                         '(lose changes)</a>');
    }

    $("#mode").change(mode_switch);
    $("#css-control").change(css_mode_switch);
    css_mode_switch();

    //make sure the advanced bits are still hidden after css-controls are added
    $(".advanced").addClass("gone");

    //load the booklist for the selected server
    load_booklist();
}

/* hide advanced options before page is loaded, rather than after. */
$(".advanced").load(function(event){
                        event.target.addClass("gone");
                    });

$(onload);
