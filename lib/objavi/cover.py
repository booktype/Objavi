
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

   params = {
      "page_width"  : str(page_width),
      "page_height" : str(page_height),
      "image_url"   : str(image_url),
   }

   return html_text % params
