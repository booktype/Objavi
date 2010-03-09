

function objavi_poller(url){
    var index = 0;
    var polling = true;
    var colour_toggle = 0;
    //var counter = 0;

    function poll(msg){
        colour_toggle = ! colour_toggle;
        //counter += 1;
        //$("body").css('background-position', "" + (4 * counter) + "px " + (3 * counter) + "px");
        if (colour_toggle){
            $("h1").css('color', '#f70');
            //$("body").css('background-image', "url(/static/background-2.png)");
        }
        else {
            $("h1").css('color', '#d50');
            //$("body").css('background-image', "url(/static/background-1.png)");
            //$("body").css('background-position', "" + (1 * counter) + "px " + (3 * counter) + "px");
        }

        if (msg){
            var messages = msg.split('\n');
            for (var i = Math.max(0, index - 1); i < messages.length; i++){
                var m = messages[i];
                if (m){
                    objavi_show_progress(m);
                    if (m == 'FINISHED'){
                        polling = false;
                        $("h1").css('color', '#f70');
                    }
                }
            }
            index = messages.length;
        }
        if (polling){
            window.setTimeout(function(){
                                  $.ajax({
                                             type: "GET",
                                             url: url,
                                             cache: false,
                                             success: poll,
                                             beforeSend: function(r){
                                                 r.setRequestHeader('X-hello', 'hi');
                                             }
                                         });
                                  },
                              300);
        }
    }
    return poll;
}

