# This file is part of Objavi.
# Copyright (c) 2012 Borko Jandras <borko.jandras@sourcefabric.org>
#
# Objavi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Objavi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Objavi.  If not, see <http://www.gnu.org/licenses/>.

import os

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

import tasks
import forms
import form_config
import config
import book_utils
import cgi_utils
import booki_wrapper
import twiki_wrapper


def fetch_booklist(request):
    server    = request.REQUEST.get("server", config.DEFAULT_SERVER)
    book      = request.REQUEST.get("book")
    interface = request.REQUEST.get("interface", "Booki")
    if interface == "Booki":
        books = booki_wrapper.get_book_list(server)
    else:
        books = twiki_wrapper.get_book_list(server)
    context = {
        "books" : books,
        "default" : book,
        }
    return render_to_response("booklist.html", context, context_instance=RequestContext(request))


def fetch_css(request):
    server = request.REQUEST.get("server", config.DEFAULT_SERVER)
    mode   = request.REQUEST.get("pdf_type", form_config.DEFAULT_PDF_TYPE)
    path   = book_utils.get_server_defaults(server)['css-%s' % mode]
    path   = os.path.join(config.STATIC_ROOT, path)
    return HttpResponse(file(path, "r").read())


def show_form(request):
    context = {
        "FORM_INPUTS" : form_config.FORM_INPUTS,
        "form"        : forms.ObjaviForm(auto_id='%s'),
        "font_list"   : cgi_utils.font_list(),
        "font_links"  : cgi_utils.font_links(),
        }
    return render_to_response("form.html", context, context_instance=RequestContext(request))


def default(request):
    mode = request.REQUEST.get("mode")

    if mode == "css":
        return fetch_css(request)
    elif mode == "booklist":
        return fetch_booklist(request)

    book = request.REQUEST.get("book")

    if book and not mode:
        mode = "book"

    def call_task(task):
        #result = task.delay(request.REQUEST)
        #return result.get()
        return task(request.REQUEST)

    if mode in ("book", "newspaper", "web"):
        return call_task(tasks.render_book)
    elif mode == "openoffice":
        return call_task(tasks.render_openoffice)
    elif mode == "bookizip":
        return call_task(tasks.render_bookizip)
    elif mode == "templated_html":
        return call_task(tasks.render_templated_html)
    elif mode == "epub":
        return call_task(tasks.render_epub)
    else:
        return show_form(request)


__all__ = [fetch_booklist, fetch_css, default]
