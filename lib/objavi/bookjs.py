
import tempfile

from objavi import book_utils


def render(html_path, pdf_path, **kwargs):
    """Creates a book PDF from the provided HTML document.
    """

    custom_css_file = tempfile.NamedTemporaryFile(prefix="renderer-", suffix=".css", delete=False)

    if kwargs.has_key("custom_css"):
        custom_css_file.write(kwargs.get("custom_css"))

    custom_css_file.flush()

    cmd = [
        "renderer",
        "-platform", "xcb",
        "-custom-css", custom_css_file.name,
        "-output", pdf_path,
        html_path]

    book_utils.run(cmd)


def make_page_settings_css(args):
    """Creates a CSS using page setting arguments.
    """
    page_settings = book_utils.get_page_settings(args)

    page_size     = page_settings.get("pointsize", (420, 595))
    top_margin    = page_settings.get("top_margin",    0.4 * 72)
    bottom_margin = page_settings.get("bottom_margin", 0.4 * 72)
    side_margin   = page_settings.get("side_margin",   0.8 * 72)
    gutter        = page_settings.get("gutter",        1.0 * 72)

    page_width, page_height = page_size

    top            = 0.8 * 72
    bottom         = 0.8 * 72
    contents_width  = page_width - side_margin - gutter
    contents_height = page_height - top - bottom

    css_text = ""

    css_text += """
.page {
    width:  %fpt;
    height: %fpt;
}
""" % (page_width, page_height)

    css_text += """
.contents {
    height: %fpt;  /* page-height - top - bottom */
    top:    %fpt;  /* top-margin + header.height */
    bottom: %fpt;  /* bottom-margin + footer.height */
}
""" % (contents_height, top, bottom)

    css_text += """
.pagenumber {
    bottom: %fpt;  /* bottom-margin */
}

.header {
    top: %fpt;     /* top-margin */
}
""" % (bottom_margin, top_margin)

    css_text += """
.page:nth-child(odd) .contents, .page:nth-child(odd) .pagenumber, .page:nth-child(odd) .header {
    left:  %fpt;   /* gutter */
    right: %fpt;   /* side-margin */
}

.page:nth-child(even) .contents, .page:nth-child(even) .pagenumber, .page:nth-child(even) .header {
    left:  %fpt;   /* side-margin */
    right: %fpt;   /* gutter */
}
""" % (gutter, side_margin, side_margin, gutter)

    css_text += """
img {
    max-width:  %fpt;  /* contents-width  * <0,1] */
    max-height: %fpt;  /* contents-height * <0,1] */
}
""" % (contents_width * 0.9, contents_height * 0.8)

    return css_text
