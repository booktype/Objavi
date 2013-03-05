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

import celery

from django.conf import settings
from django.http import HttpResponse

from objavi import form_config
from objavi import constants
from objavi import config
from objavi import fmbook
from objavi import book_utils
from objavi import bookjs

import forms


class RequestError(Exception):
    def __init__(self, errors):
        self.errors = errors
        Exception.__init__(self, errors)

    def __str__(self):
        lines = []
        for param in self.errors:
            msg = "%s: %s" % (param, ", ".join(self.errors[param]))
            lines.append(msg)
        return "; ".join(lines)


class ObjaviRequest(object):
    def __init__(self, args):
        self.bookid = args.get('book')
        self.server = args.get('server')
        self.mode = args.get('mode', form_config.DEFAULT_MODE)
        extension = form_config.CGI_MODES.get(self.mode)[1]
        self.bookname = book_utils.make_book_name(self.bookid, self.server, extension)
        self.destination = args.get('destination')
        self.callback = args.get('callback')
        self.method = args.get('method', form_config.CGI_DESTINATIONS[self.destination]['default'])
        self.template, self.mimetype = form_config.CGI_DESTINATIONS[self.destination][self.method]
        self.bookurl = "%s/%s" % (config.PUBLISH_URL, self.bookname,)

        if args.get('output_format') and args.get('output_profile'):
            self.bookurl = self.bookurl.rsplit(".", 1)[0]+"."+args.get('output_format')

        self.details_url, self.s3url = fmbook.find_archive_urls(self.bookid, self.bookname)
        self.booki_group = args.get('booki_group')
        self.booki_user = args.get('booki_user')

    def finish(self, book):
        #book.publish_shared(self.booki_group, self.booki_user)
        self.publish_file = book.publish_file
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
        args[input] = request.get(input, default)

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
        raise RequestError(form.errors)

    destination = request.get("destination", form_config.DEFAULT_CGI_DESTINATION)
    if destination in form_config.CGI_DESTINATIONS.keys():
        args["destination"] = destination

    engine = request.get("engine", config.DEFAULT_ENGINE)
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
        "page_number_style" : args.get("page_numbers"),
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


def make_response(context):
    if context.destination == "nowhere":
        return HttpResponse(context.bookurl)
    else:
        content_type = form_config.CGI_MODES.get(context.mode)[2]
        response = HttpResponse(content_type = content_type)
        response["Content-Disposition"] = "attachment; filename=%s" % context.bookname
        with open(context.publish_file, "rb") as f:
            response.write(f.read())
        return response



##
# Task functions.
#

def task(func):
    """Default decorator for all task functions.
    """
    @celery.task(name = func.__name__)
    def decorated_func(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return decorated_func


@task
def render_bookjs_pdf(request):
    args = parse_request(request)
    context = ObjaviRequest(args)

    with make_book(context, args) as book:
        book.spawn_x()
        book.load_book()

        page_config = bookjs.make_pagination_config(args)
        custom_css  = args.get("css", "")

        book.add_section_titles()
        book.make_body_html()

        bookjs.render(book.body_html_file, book.pdf_file, custom_css=custom_css, page_config=page_config)

        book.publish_pdf()
        context.finish(book)

    return make_response(context)


@task
def render_bookjs_zip(request):
    args = parse_request(request)
    context = ObjaviRequest(args)

    with make_book(context, args) as book:
        book.load_book()

        custom_css  = bookjs.make_page_settings_css(args)
        custom_css += "\n"
        custom_css += args.get("css", "")

        book.add_section_titles()
        book.make_bookjs_zip(custom_css)

        context.finish(book)

    return make_response(context)


@task
def render_book(request):
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

    return make_response(context)


@task
def render_openoffice(request):
    args = parse_request(request)
    context = ObjaviRequest(args)

    with make_book(context, args) as book:
        book.spawn_x()
        book.load_book()
        book.add_css(args.get('css'), 'openoffice')
        book.add_section_titles()
        book.make_oo_doc()
        context.finish(book)

    return make_response(context)


@task
def render_bookizip(request):
    args = parse_request(request)
    context = ObjaviRequest(args)

    with make_book(context, args) as book:
        book.publish_bookizip()
        context.finish(book)

    return make_response(context)


@task
def render_templated_html(request):
    args = parse_request(request)
    context = ObjaviRequest(args)

    template = args.get('html_template')

    with make_book(context, args) as book:
        book.make_templated_html(template = template)
        context.finish(book)

    return make_response(context)


@task
def render_epub(request):
    args = parse_request(request)
    context = ObjaviRequest(args)

    epub_args = {
        "use_cache"  : config.USE_CACHED_IMAGES,
        "css"        : args.get("css"),
        "cover_url"  : args.get("cover_url"),
        }

    output_format  = args.get("output_format")
    output_profile = args.get("output_profile")

    with make_book(context, args) as book:
        book.make_epub(**epub_args)
        if output_format and output_profile:
            book.convert_with_calibre(output_profile, output_format)
        context.finish(book)

    return make_response(context)


@task
def ingress_epub(request):
    from objavi import espri

    form = forms.EspriForm(request)

    if form.is_valid():
        source = form.cleaned_data["source"]
        book   = form.cleaned_data["book"]
    else:
        raise RequestError(form.errors)

    if source == "url":
        source_function = espri.inet_espri
    elif source == "archive.org":
        source_function = espri.ia_espri
    else:
        raise AssertionError("unknown source identifier")

    file_name = source_function(book)
    file_path = os.path.join(config.BOOKI_BOOK_DIR, file_name)

    response = HttpResponse(content_type = constants.BOOKIZIP_MIMETYPE)
    response["Content-Disposition"] = "attachment; filename=%s" % (file_name, )

    with open(file_path, "rb") as f:
        response.write(f.read())

    return response


__all__ = (
    render_bookjs_pdf, render_bookjs_zip,
    render_book, render_openoffice,
    render_bookizip, render_templated_html,
    render_epub, ingress_epub,
)
