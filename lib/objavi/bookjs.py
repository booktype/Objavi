
from objavi import book_utils


def render(html_path, pdf_path):
    """Creates a book PDF from the provided HTML document.
    """
    cmd = [
        "renderer",
        "-platform", "xcb",
        "-output", pdf_path,
        html_path]
    book_utils.run(cmd)
