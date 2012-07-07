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

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

import forms
import form_config
import config
import book_utils
import booki_wrapper
import twiki_wrapper
import settings


def mode_booklist(request):
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


def mode_css(request):
    server = request.REQUEST.get("server", config.DEFAULT_SERVER)
    mode   = request.REQUEST.get("pdf_type", form_config.DEFAULT_PDF_TYPE)
    path   = book_utils.get_server_defaults(server)['css-%s' % mode]
    return HttpResponseRedirect(path)


def mode_form(request):
    context = {
        "FORM_INPUTS" : form_config.FORM_INPUTS,
        "form" : forms.ObjaviForm(auto_id='%s'),
        }
    return render_to_response("form.html", context, context_instance=RequestContext(request))


def mode_pdf(request):
    return HttpResponse("")


def default(request):
    mode = request.REQUEST.get("mode")

    if mode == "css":
        return mode_css(request)
    elif mode == "booklist":
        return mode_booklist(request)

    book = request.REQUEST.get("book")

    if book and not mode:
        mode = "book"

    if mode == "book":
        return mode_pdf(request)
    else:
        return mode_form(request)
