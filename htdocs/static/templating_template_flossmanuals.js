function addLoadEvent(func) {
    var oldonload = window.onload;
    if (typeof window.onload != 'function') {
        window.onload = func;
    } else {
        window.onload = function() {
            oldonload();
            func();
        };
    }
}

function insertAfter(newElement, targetElement) {
    var parent = targetElement.parentNode;
    if (parent.lastChild == targetElement) {
        parent.appendChild(newElement);
    } else {
        parent.insertBefore(newElement, targetElement.nextSibling);
    }
}

function captionizeImages() {
    if (!document.getElementsByTagName ||
        !document.createElement) {
        return false;
    }
    var images = document.getElementsByTagName("img");
    for (var i=0; i<images.length; i++) {
        if (images[i].className != "non") {
            var title = images[i].getAttribute("title");
            var width = images[i].width;
            var divCaption = document.createElement("div");
            divCaption.className="caption";
            divCaption.style.width=width+'px';
            if (title){
                divCaption.style.padding='2px 0px 3px 0px';
            }
            divCaption.style.display='block';
            var divCaption_text = document.createTextNode(title);
            divCaption.appendChild(divCaption_text);
            var divContainer = document.createElement("div");
            divContainer.className="imgcontainer";
            if (title){
                divContainer.style.padding='0px 0px 10px 0px';
            }
            images[i].parentNode.insertBefore(divContainer,images[i]);
            divContainer.appendChild(images[i]);
            insertAfter(divCaption,images[i]);
        }
    }
}
//addLoadEvent(captionizeImages);

function next () {
    var onode, otarget;
    onode=document.getElementById("%TOPIC%");
    if (onode.id=="Credits") die;
    //alert (onode.id);
    onode=onode.nextSibling;
    if (onode.id=="heading") onode=onode.nextSibling;
    while (onode) {
        //onode=onode.nextSibling;
        if (onode.nodeType==1) {
	    //alert (onode.id);
            otarget=onode;
            break;
        }
        onode=onode.nextSibling;
    }
    if (otarget) {
        //you actually have found one, and do something here
        //alert(otarget.id + "\n" + otarget.tagName);    //just to verify
        top.location = "/" + otarget.id;
    } else {
        //you don't find one
        //alert("nada" + otarget.id);
    }
}

function previous () {
    var onode, otarget;
    onode=document.getElementById("/");
    if (onode.id=="Introduction") die;
    //alert (onode.id);
    onode=onode.previousSibling;
    if (onode.id=="heading") onode=onode.previousSibling;
    if (onode.id=="title") die;
    while (onode) {
        //onode=onode.previousSibling;
        if (onode.nodeType==1) {
	    //alert (onode.id);
            otarget=onode;
            break;
        }
        onode=onode.previousSibling;
    }
    if (otarget) {
        //you actually have found one, and do something here
        //alert(otarget.id + "\n" + otarget.tagName);    //just to verify
        top.location =  otarget.id;
    } else {
        //you don't find one
        //alert("nada" + otarget.id);
    }
}

