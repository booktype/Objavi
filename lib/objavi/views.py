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
import fmbook
import book_utils
import booki_wrapper
import twiki_wrapper
import settings

from objavi.pdf import resize_pdf, count_pdf_pages


class ObjaviRequest(object):
    def __init__(self, args):
        self.bookid = args.get('book')
        self.server = args.get('server')
        self.mode = args.get('mode', 'book') #XXX default should be configured?
        extension = form_config.CGI_MODES.get(self.mode)[1]
        self.bookname = book_utils.make_book_name(self.bookid, self.server, extension)
        self.destination = args.get('destination')
        self.callback = args.get('callback')
        self.method = args.get('method', form_config.CGI_DESTINATIONS[self.destination]['default'])
        self.template, self.mimetype = form_config.CGI_DESTINATIONS[self.destination][self.method]
        self.bookurl = "%s/books/%s" % (config.OBJAVI_URL, self.bookname,)

        if args.get('output_format') and args.get('output_profile'):
            self.bookurl = self.bookurl.rsplit(".", 1)[0]+"."+args.get('output_format')

        self.details_url, self.s3url = fmbook.find_archive_urls(self.bookid, self.bookname)
        self.booki_group = args.get('booki_group')
        self.booki_user = args.get('booki_user')

    def finish(self, book):
        book.publish_shared(self.booki_group, self.booki_user)
        if self.destination == 'archive.org':
            book.publish_s3()

    def log_notifier(self, message):
        print('*** MESSAGE: "%s"' % message)

    def get_watchers(self):
        return set([self.log_notifier])


def parse_request(request):
    """Extracts arguments from the HTTP request.
    """
    # copy argument values from the request, using defaults when missing
    #
    args = {}
    for input, _, _, _, _, _, _, default in form_config.FORM_INPUTS:
        args[input] = request.REQUEST.get(input, default)

    # rename some arguments to a canonical form
    #
    MAPPINGS = {
        "booki-user"   : "booki_user",
        "booki-group"  : "booki_group",
        "page-numbers" : "page_numbers",
        "max-age"      : "max_age",
        "embed-fonts"  : "embed_fonts",
        "allow-breaks" : "allow_breaks",
        }
    for old_key, new_key in MAPPINGS.items():
        if args.has_key(old_key):
            args[new_key] = args[old_key]
            del args[old_key]

    # validate input
    #
    form = forms.ObjaviForm(args)
    if form.is_valid():
        args = form.cleaned_data
    else:
        return None

    destination = request.REQUEST.get("destination", form_config.DEFAULT_CGI_DESTINATION)
    if destination in form_config.CGI_DESTINATIONS.keys():
        args["destination"] = destination

    engine = request.REQUEST.get("engine", config.DEFAULT_ENGINE)
    if engine in config.ENGINES.keys():
        args["engine"] = engine

    return args


def make_book(context, args):
    """Creates a Book instance for the specified request context and request arguments.
    """
    book_args = {
        "page_settings"     : book_utils.get_page_settings(args),
        "watchers"          : context.get_watchers(),
        "license"           : args.get("license"),
        "max_age"           : float(args.get("max_age")),
        "page_number_style" : args.get("page-numbers"),
        }

    if args.get("isbn"):
        book_args["isbn"] = args.get("isbn")
    if args.get("title"):
        book_args["title"] = args.get("title")

    book = fmbook.Book(context.bookid, context.server, context.bookname, **book_args)

    toc_header = args.get("toc_header")
    if toc_header:
        book.toc_header = toc_header

    return book


def mode_book(request):
    args = parse_request(request)
    context = ObjaviRequest(args)

    with make_book(context, args) as book:
        book.spawn_x()
        book.load_book()

        if not args.get('allow-breaks'):
            book.fake_no_break_after()

        book.add_css(args.get('css'), context.mode)
        book.add_section_titles()

        if context.mode == 'book':
            book.make_book_pdf()
        elif context.mode in ('web', 'newspaper'):
            book.make_simple_pdf(context.mode)

        if args.get("rotate"):
            book.rotate180()

        if args.get('embed-fonts'):
            log("embedding fonts!")
            book.embed_fonts()

        book.publish_pdf()
        context.finish(book)

    return HttpResponse(context.bookurl)


def mode_openoffice(request):
    args = parse_request(request)
    context = ObjaviRequest(args)

    with make_book(context, args) as book:
        book.spawn_x()
        book.load_book()
        book.add_css(args.get('css'), 'openoffice')
        book.add_section_titles()
        book.make_oo_doc()
        context.finish(book)

    return HttpResponse(context.bookurl)


def mode_bookizip(request):
    args = parse_request(request)
    context = ObjaviRequest(args)

    with make_book(context, args) as book:
        book.publish_bookizip()
        context.finish(book)

    return HttpResponse(context.bookurl)


def mode_templated_html(request):
    args = parse_request(request)
    context = ObjaviRequest(args)

    template = args.get('html_template')

    with make_book(context, args) as book:
        book.make_templated_html(template = template)
        context.finish(book)

    return HttpResponse(context.bookurl)


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


def default(request):
    mode = request.REQUEST.get("mode")

    if mode == "css":
        return mode_css(request)
    elif mode == "booklist":
        return mode_booklist(request)

    book = request.REQUEST.get("book")

    if book and not mode:
        mode = "book"

    if mode in ("book", "newspaper", "web"):
        return mode_book(request)
    elif mode == "openoffice":
        return mode_openoffice(request)
    elif mode == "bookizip":
        return mode_bookizip(request)
    elif mode == "templated_html":
        return mode_templated_html(request)
    else:
        return mode_form(request)
