
import urlparse


def make_cover_html(page_width, page_height, image_url):
   """Creates the HTML for the cover image.

   Page width and height are in points (pt).
   """

   html_text = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Cover</title>
  <style type="text/css">
body {
  padding: 0;
  margin: 0;
}

#cover-image {
  top: 0;
  left: 0;
  position: absolute;
  width: %(page_width)spt;
  height: %(page_height)spt;
  display: table;
  overflow: hidden;
}

#cover-image p {
  display: table-cell;
  vertical-align: middle;
}

#cover-image p img {
  width: %(width)s;
  height: %(height)s;
  max-width: %(page_width)spt;
  max-height: %(page_height)spt;
  display: block;
  margin-left: auto;
  margin-right: auto;
}
  </style>
</head>
<body>
  <div id="cover-image">
    <p>
      <img src="%(image_url)s" alt="Cover image" />
    </p>
  </div>
</body>
</html>
"""

   image_url_parts = urlparse.urlparse(image_url)

   if image_url_parts.fragment:
      image_width, image_height = image_url_parts.fragment.split(",", 2)
      image_url = urlparse.urldefrag(image_url_parts.geturl())[0]
   else:
      image_width, image_height = page_width, page_height


   sx = float(page_width) / float(image_width)
   sy = float(page_height) / float(image_height)

   if sx < sy:
      width, height = ("100%", "auto")
   else:
      width, height = ("auto", "100%")

   params = {
      "width"       : width,
      "height"      : height,
      "page_width"  : str(page_width),
      "page_height" : str(page_height),
      "image_url"   : str(image_url),
   }

   return html_text % params
