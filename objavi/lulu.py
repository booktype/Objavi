
import os.path

import json

from urllib2 import urlopen, HTTPError, Request

from config import WKHTMLTOPDF
from constants import POINT_2_MM
from book_utils import log, run

endpoint_template = "https://apps.lulu.com/api/create/v1/getcoversize/?api_key=%(api_key)s"

def calculate_cover_size(api_key, booksize, page_count):
    endpoint = endpoint_template % dict(api_key=api_key)

    paperType = "regular"
    if booksize == "DIGEST":
        paperType = "publisher-grade"

    physical_attributes = {
        "numberOfPages": page_count, # XXX which pages included?
        "color": False,
#        "trimSize": "us_trade",
#        "bindingType": "jacket-hardcover", # XXX softcover?
#        "trimSize": "DIGEST",
        "trimSize": booksize,
        "bindingType": "perfect", # XXX softcover?
        "paperType": paperType,
    }

#    8.5x5.5 perfect bw color cover standard softcover

    req_body = json.dumps(physical_attributes)

    log(endpoint)
    log(req_body)
    request = Request(endpoint, req_body)
    request.add_header("Content-type", "application/json")
    request.add_header("Accept", "application/json")

    try:
        f = urlopen(request)
    except HTTPError, e:
        f = e
    log(f.code)
    log(f.info())
    resp_body = f.read()
    log(resp_body)
    
    resp = json.loads(resp_body)
    spine_width = resp["coverSizeData"]["spineWidth"]["valueInPoints"]
    width = (resp["coverSizeData"]["fullCoverDimension"]["width"]["valueInPoints"]-spine_width)/2
    height = resp["coverSizeData"]["fullCoverDimension"]["height"]["valueInPoints"]

    return (width, height, spine_width)

# XXX the real one is in pdf.py make_cover_pdf
def create_cover_pdf(width, height, spine_width, outputname):
    width = width * POINT_2_MM
    height = height * POINT_2_MM
    spine_width = spine_width * POINT_2_MM

    cmd = [WKHTMLTOPDF,
           "-q",
           "--page-width", str(2 * width + spine_width),
           "--page-height", str(height),
           "--load-error-handling", "ignore",
           "/dev/zero", outputname
    ]
    run(cmd)

def create_project(api_key, user, password, cover, contents, booksize, projectid, title):

    paperType = "regular"
    if booksize == "DIGEST":
        paperType = "publisher-grade"

    import publish.client.client as client
    import publish.common.project as project

    assert os.path.exists(cover), "cover file for test does not exist"
    assert os.path.exists(contents), "contents file for test does not exist"
    pclient = client.Client()

    # This login depends on having user and key set in ~/.lulu_publish_api.conf.
    # Alternatively, credentials can be passed into the login() function.
    log("logging in to lulu.com")
    pclient.login(user, password)

    log("requesting upload token")
    result = pclient.request_upload_token()
    log("uploading the pdf files")
    data = pclient.upload([cover, contents], result['token'])

    cover_fd = project.FileDetails({"mimetype": "application/pdf", "filename": os.path.basename(cover) })
    contents_fd = project.FileDetails({"mimetype": "application/pdf", "filename": os.path.basename(contents) })

    proj = project.Project()
    proj.set("project_type", "softcover")
    proj.set("allow_ratings", True)
    proj.set("bibliography", project.Bibliography())
    proj.get("bibliography").set("title",  title)
    proj.get("bibliography").set("authors", [ {"first_name": "The", "last_name":  "Authors"}, ])
    proj.get("bibliography").set("category",  7)
    proj.get("bibliography").set("description",  "A manual")
    proj.get("bibliography").set("keywords",  [ "Free Software", "Open Source", "manual" ])
    proj.get("bibliography").set("license",  "GNU General Public License")
    proj.get("bibliography").set("copyright_year",  2011)
    proj.get("bibliography").set("copyright_citation",  "by The Authors")
    proj.get("bibliography").set("publisher",  "FLOSS Manuals")
    proj.get("bibliography").set("edition",  "First")
    proj.get("bibliography").set("language",  "EN")
    proj.get("bibliography").set("country_code",  "US")
    proj.set("physical_attributes", project.PhysicalAttributes())
    proj.get("physical_attributes").set("binding_type", "perfect")
    proj.get("physical_attributes").set("trim_size", booksize)
    proj.get("physical_attributes").set("paper_type", paperType)
    proj.get("physical_attributes").set("color", False)
    proj.set("access", "public") # private, direct, public
    proj.set("pricing", [ 
            project.Pricing({"product": "download", "currency_code": "EUR", "total_price": "00.00"}),
            project.Pricing({"product": "print", "currency_code": "EUR", "total_price": "5.00"}),
        ])
    proj.set("file_info", project.FileInfo({ "contents": [ contents_fd ], "cover": [ cover_fd ] }))

    if not projectid:
        log("creating the lulu.com project")
        data = pclient.create(proj)
        log(data)

        assert data.has_key('content_id')
        assert data['content_id'] > 0
        content_id = data['content_id']
    else:
        log("updating the lulu.com project")
        proj.set("content_id", projectid)
        data = pclient.update(proj)
        log(data)

        assert data.has_key('project')
        assert data['project'].has_key('content_id')
        assert data['project']['content_id'] > 0
        content_id = data['project']['content_id']

    log("lulu.com content id: %s" % content_id)

    return content_id
    
if __name__ == "__main__":
    outputname = "lulu-blankcover.pdf"

    api_key = "geukezh5uhfpjcb3j89ysz49"

    page_count = 100
    booksize = "COMIC"

#    width, height, spine_width = 210, 297, 10
    width, height, spine_width = calculate_cover_size(api_key, booksize, page_count)
    print (width, height, spine_width)
    create_cover_pdf(width, height, spine_width, outputname)

#    create_project()

