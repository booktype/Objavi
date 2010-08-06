#!/usr/bin/python
#
# Part of Objavi2, which turns html manuals into books
#
# Copyright (C) 2009 Douglas Bagnall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Make a pdf from the specified book."""
from __future__ import with_statement

import os, sys
os.chdir('..')
sys.path.insert(0, os.path.abspath('.'))

import re, time
#import traceback
from pprint import pformat

from objavi.fmbook import Book, HTTP_HOST, find_archive_urls
from objavi import config
from objavi import twiki_wrapper
from objavi.book_utils import init_log, log, make_book_name
from objavi.cgi_utils import parse_args, optionise, listify, get_server_list
from objavi.cgi_utils import is_utf8, isfloat, isfloat_or_auto, is_isbn, is_url
from objavi.cgi_utils import output_blob_and_exit, output_blob_and_shut_up, output_and_exit
from objavi.cgi_utils import get_size_list, get_default_css, font_links, set_memory_limit


# ARG_VALIDATORS is a mapping between the expected cgi arguments and
# functions to validate their values. (None means no validation).
ARG_VALIDATORS = {
    "book": re.compile(r'^([\w-]+/?)*[\w-]+$').match, # can be: BlahBlah/Blah_Blah
    "css": is_utf8, # an url, empty (for default), or css content
    "title": lambda x: len(x) < 999 and is_utf8(x),
    "isbn": is_isbn,
    "license": config.LICENSES.__contains__,
    "server": config.SERVER_DEFAULTS.__contains__,
    "engine": config.ENGINES.__contains__,
    "booksize": config.PAGE_SIZE_DATA.__contains__,
    "page_width": isfloat,
    "page_height": isfloat,
    "gutter": isfloat_or_auto,
    "top_margin": isfloat_or_auto,
    "side_margin": isfloat_or_auto,
    "bottom_margin": isfloat_or_auto,
    "columns": isfloat_or_auto,
    "column_margin": isfloat_or_auto,
    "cgi-context": lambda x: x.lower() in '1true0false',
    "mode": config.CGI_MODES.__contains__,
    "pdftype": lambda x: config.CGI_MODES.get(x, [False])[0], #for css mode
    "rotate": u"yes".__eq__,
    "grey_scale": u"yes".__eq__,
    "destination": config.CGI_DESTINATIONS.__contains__,
    "toc_header": is_utf8,
    "max-age": isfloat,
    "method": config.CGI_METHODS.__contains__,
    "callback": is_url,
    "html_template": is_utf8,
    "booki-group": is_utf8,
    "booki-user": is_utf8,
}

__doc__ += '\nValid arguments are: %s.\n' % ', '.join(ARG_VALIDATORS.keys())


def get_page_settings(args):
    """Find the size and any optional layout settings.

    args['booksize'] is either a keyword describing a size or
    'custom'.  If it is custom, the form is inspected for specific
    dimensions -- otherwise these are ignored.

    The margins, gutter, number of columns, and column
    margins all set themselves automatically based on the page
    dimensions, but they can be overridden.  Any that are are
    collected here."""
    # get all the values including sizes first
    # the sizes are found as 'page_width' and 'page_height',
    # but the Book class expects them as a 'pointsize' tuple, so
    # they are easily ignored.
    settings = {}
    for k, extrema in config.PAGE_EXTREMA.iteritems():
        try:
            v = float(args.get(k))
        except (ValueError, TypeError):
            #log("don't like %r as a float value for %s!" % (args.get(k), k))
            continue
        min_val, max_val, multiplier = extrema
        if v < min_val or v > max_val:
            log('rejecting %s: outside %s' % (v,) + extrema)
        else:
            log('found %s=%s' % (k, v))
            settings[k] = v * multiplier #convert to points in many cases

    # now if args['size'] is not 'custom', the width and height found
    # above are ignored.
    size = args.get('booksize', config.DEFAULT_SIZE)
    settings.update(config.PAGE_SIZE_DATA[size])

    #if args['mode'] is 'newspaper', then the number of columns is
    #automatically determined unless set -- otherwise default is 1.
    if args.get('mode') == 'newspaper' and settings.get('columns') is None:
        settings['columns'] = 'auto'

    if args.get('grey_scale'):
        settings['grey_scale'] = True

    if size == 'custom':
        #will raise KeyError if width, height aren't set
        settings['pointsize'] = (settings['page_width'], settings['page_height'])
        del settings['page_width']
        del settings['page_height']

    settings['engine'] = args.get('engine', config.DEFAULT_ENGINE)
    return settings

@output_and_exit
def mode_booklist(args):
    #XXX need to include booki servers
    return optionise(twiki_wrapper.get_book_list(args.get('server', config.DEFAULT_SERVER)),
                     default=args.get('book'))

@output_and_exit
def mode_css(args):
    #XX sending as text/html, but it doesn't really matter
    return get_default_css(args.get('server', config.DEFAULT_SERVER), args.get('pdftype', 'book'))


@output_and_exit
def mode_form(args):
    f = open(config.FORM_TEMPLATE)
    template = f.read()
    f.close()
    f = open(config.FONT_LIST_INCLUDE)
    font_list = [x.strip() for x in f if x.strip()]
    f.close()
    server = args.get('server', config.DEFAULT_SERVER)
    book = args.get('book')
    size = args.get('booksize', config.DEFAULT_SIZE)
    engine = args.get('engine', config.DEFAULT_ENGINE)
    d = {
        'server_options': optionise(get_server_list(), default=server),
        'book_options': optionise(twiki_wrapper.get_book_list(server), default=book),
        'size_options': optionise(get_size_list(), default=size),
        'engines': optionise(config.ENGINES.keys(), default=engine),
        'pdf_types': optionise(sorted(k for k, v in config.CGI_MODES.iteritems() if v[0])),
        'css': get_default_css(server),
        'font_links': listify(font_links()),
        'font_list': listify(font_list),
        'default_license' : config.DEFAULT_LICENSE,
        'licenses' : optionise(config.LICENSES, default=config.DEFAULT_LICENSE),
        'yes': 'yes',
        None: '',
    }

    form = []
    for id, title, type, source, classes, epilogue in config.FORM_INPUTS:
        val = d.get(source, '')
        e = config.FORM_ELEMENT_TYPES[type] % locals()
        form.append('\n<div id="%(id)s_div" class="form-item %(classes)s">\n'
                    '<div class="input_title">%(title)s</div>\n'
                    '<div class="input_contents"> %(e)s %(epilogue)s\n</div>'
                    '</div>\n' % locals())

    if True:
        _valid_inputs = set(ARG_VALIDATORS)
        _form_inputs = set(x[0] for x in config.FORM_INPUTS if x[2] != 'ul')
        log("valid but not used inputs: %s" % (_valid_inputs - _form_inputs))
        log("invalid form inputs: %s" % (_form_inputs - _valid_inputs))

    return template % {'form': ''.join(form)}



class Context(object):
    """Work out what to show the caller.  The method/destination matrix:

    [dest/method]   sync        async       poll
    archive.org     url         id          id
    download        data        .           .
    html            html 1      .           html 2
    nowhere         url         id          id

    'html 1' is dripfed progress reports; 'html 2' polls via
    javascript.  'id' is the book filename.  'url' is a full url
    locating the file on archive.org or the objavi server.  '.'  means
    unimplemented.
    """

    pollfile = None
    def __init__(self, args):
        self.bookid = args.get('book')
        self.server = args.get('server', config.DEFAULT_SERVER)
        self.mode = args.get('mode', 'book')
        extension = config.CGI_MODES.get(self.mode)[1]
        self.bookname = make_book_name(self.bookid, self.server, extension)
        self.destination = args.get('destination', config.DEFAULT_CGI_DESTINATION)
        self.callback = args.get('callback', None)
        self.method = args.get('method', config.CGI_DESTINATIONS[self.destination]['default'])
        self.template, self.mimetype = config.CGI_DESTINATIONS[self.destination][self.method]
        if HTTP_HOST:
            self.bookurl = "http://%s/books/%s" % (HTTP_HOST, self.bookname,)
        else:
            self.bookurl = "books/%s" % (self.bookname,)

        self.details_url, self.s3url = find_archive_urls(self.bookid, self.bookname)
        self.booki_group = args.get('booki-group')
        self.booki_user = args.get('booki-user')
        self.start()

    def start(self):
        """Begin (and in many cases, finish) http output.

        In asynchronous modes, fork and close down stdout.
        """
        log(self.template, self.mimetype, self.destination, self.method)
        if self.template is not None:
            progress_list = ''.join('<li id="%s">%s</li>\n' % x[:2] for x in config.PROGRESS_POINTS
                                    if self.mode in x[2])
            d = {
                'book': self.bookid,
                'bookname': self.bookname,
                'progress_list': progress_list,
                'details_url': self.details_url,
                's3url': self.s3url,
                'bookurl': self.bookurl,
                }
            f = open(self.template)
            content = f.read() % d
            f.close()
        else:
            content = ''

        if self.method == 'sync':
            print 'Content-type: %s\n\n%s' %(self.mimetype, content)
        else:
            output_blob_and_shut_up(content, self.mimetype)
            log(sys.stdout, sys.stderr, sys.stdin)
            if os.fork():
                os._exit(0)
            sys.stdout.close()
            sys.stdin.close()
            log(sys.stdout, sys.stderr, sys.stdin)


    def finish(self, book):
        """Print any final http content."""
        book.publish_shared(self.booki_group, self.booki_user)
        if self.destination == 'archive.org':
            book.publish_s3()
        elif (self.destination == 'download' and
              self.method == 'sync' and
              self.mode != 'templated_html'):
            f = open(book.publish_file)
            data = f.read()
            f.close()
            output_blob_and_exit(data, config.CGI_MODES[self.mode][2], self.bookname)


    def log_notifier(self, message):
        """Send messages to the log only."""
        log('******* got message "%s"' %message)

    def callback_notifier(self, message):
        """Call the callback url with each message."""
        log('in callback_notifier')
        pid = os.fork()
        if pid:
            log('child %s is doing callback with message %r' % (pid, message, ))
            return
        from urllib2 import urlopen, URLError
        from urllib import urlencode
        data = urlencode({'message': message})
        try:
            f = urlopen(self.callback, data)
            time.sleep(2)
            f.close()
        except URLError, e:
            #traceback.print_exc()
            log("ERROR in callback:\n %r\n %s %s" % (e.url, e.code, e.msg))
        os._exit(0)

    def javascript_notifier(self, message):
        """Print little bits of javascript which will be appended to
        an unfinished html page."""
        try:
            if message.startswith('ERROR:'):
                log('got an error! %r' % message)
                print ('<b class="error-message">'
                       '%s\n'
                       '</b></body></html>' % message
                       )
            else:
                print ('<script type="text/javascript">\n'
                       'objavi_show_progress("%s");\n'
                       '</script>' % message
                       )
                if message == config.FINISHED_MESSAGE:
                    print '</body></html>'

            sys.stdout.flush()
        except (ValueError, IOError), e:
            log("failed to send message %r, got exception %r" % (message, e))

    def pollee_notifier(self, message):
        """Append the message to a file that the remote server can poll"""
        if self.pollfile is None or self.pollfile.closed:
            self.pollfile = open(config.POLL_NOTIFY_PATH % self.bookname, 'a')
        self.pollfile.write('%s\n' % message)
        self.pollfile.flush()
        #self.pollfile.close()
        #if message == config.FINISHED_MESSAGE:
        #    self.pollfile.close()

    def get_watchers(self):
        """Based on the CGI arguments, return a likely set of notifier
        methods."""
        log('in get_watchers. method %r, callback %r, destination %r' %
            (self.method, self.callback, self.destination))
        watchers = set()
        if self.method == 'poll':
            watchers.add(self.pollee_notifier)
        if self.method == 'async' and self.callback:
            watchers.add(self.callback_notifier)
        if self.method == 'sync' and  self.destination == 'html':
            watchers.add(self.javascript_notifier)
        watchers.add(self.log_notifier)
        log('watchers are %s' % watchers)
        return watchers

def mode_book(args):
    # so we're making a pdf.
    context = Context(args)
    page_settings = get_page_settings(args)

    with Book(context.bookid, context.server, context.bookname,
              page_settings=page_settings,
              watchers=context.get_watchers(), isbn=args.get('isbn'),
              license=args.get('license'), title=args.get('title'),
              max_age=float(args.get('max-age', -1))) as book:

        book.spawn_x()

        if 'toc_header' in args:
            book.toc_header = args['toc_header']
        book.load_book()
        book.add_css(args.get('css'), context.mode)
        book.add_section_titles()

        if context.mode == 'book':
            book.make_book_pdf()
        elif context.mode in ('web', 'newspaper'):
            book.make_simple_pdf(context.mode)
        if "rotate" in args:
            book.rotate180()

        book.publish_pdf()
        context.finish(book)

#These ones are similar enough to be handled by the one function
mode_newspaper = mode_book
mode_web = mode_book


def mode_openoffice(args):
    """Make an openoffice document.  A whole lot of the inputs have no
    effect."""
    context = Context(args)
    with Book(context.bookid, context.server, context.bookname,
              watchers=context.get_watchers(), isbn=args.get('isbn'),
              license=args.get('license'), title=args.get('title'),
              max_age=float(args.get('max-age', -1))) as book:

        book.spawn_x()
        book.load_book()
        book.add_css(args.get('css'), 'openoffice')
        book.add_section_titles()
        book.make_oo_doc()
        context.finish(book)

def mode_epub(args):
    log('making epub with\n%s' % pformat(args))
    #XXX need to catch and process lack of necessary arguments.
    context = Context(args)

    with Book(context.bookid, context.server, context.bookname,
              watchers=context.get_watchers(), title=args.get('title'),
              max_age=float(args.get('max-age', -1))) as book:

        book.make_epub(use_cache=config.USE_CACHED_IMAGES)
        context.finish(book)


def mode_bookizip(args):
    log('making bookizip with\n%s' % pformat(args))
    context = Context(args)

    with Book(context.bookid, context.server, context.bookname,
              watchers=context.get_watchers(), title=args.get('title'),
              max_age=float(args.get('max-age', -1))) as book:
        book.publish_bookizip()
        context.finish(book)

def mode_templated_html(args):
    log('making templated html with\n%s' % pformat(args))
    context = Context(args)
    template = args.get('html_template')
    log(template)
    with Book(context.bookid, context.server, context.bookname,
              watchers=context.get_watchers(), title=args.get('title'),
              max_age=float(args.get('max-age', -1))) as book:

        book.make_templated_html(template=template)
        context.finish(book)

def mode_templated_html_zip(args):
    pass

def main():
    set_memory_limit(config.OBJAVI_CGI_MEMORY_LIMIT)
    args = parse_args(ARG_VALIDATORS)
    mode = args.get('mode')
    if mode is None and 'book' in args:
        mode = 'book'

    global CGI_CONTEXT
    CGI_CONTEXT = 'SERVER_NAME' in os.environ or args.get('cgi-context', 'no').lower() in '1true'

    if not args and not CGI_CONTEXT:
        print __doc__
        sys.exit()

    output_function = globals().get('mode_%s' % mode, mode_form)
    output_function(args)

if __name__ == '__main__':
    if config.CGITB_DOMAINS and os.environ.get('REMOTE_ADDR') in config.CGITB_DOMAINS:
        import cgitb
        cgitb.enable()
    init_log()
    main()

