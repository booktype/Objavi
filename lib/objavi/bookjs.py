
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
    page_settings = book_utils.get_page_settings(args)

    css_text = ""

    css_text += """
.page {
    width:  %spt;
    height: %spt;
}
""" % page_settings["pointsize"]

    return css_text
