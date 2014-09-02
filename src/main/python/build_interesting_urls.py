from sg_utils import *

CONTENT_TYPE_KEEPERS = set([
    'text/html',
    'application/pdf',
    'text/xml',
    'application/rss+xml',
    'application/rdf+xml',
    'text/plain',
    'application/msword',
    'application/vnd.ms-excel',
    'application/xml',
    'application/xhtml+xml',
    'application/x-pdf',
    'application/x-httpd-php',
    '"application/pdf"',
    'text/rtf',
    'application/x-msexcel',
    'application/ms-excel',
    'plain/text',
    '.pdf',
    'image/bmp',
    'application/atom+xml',
    'video/x-ms-wvx',
    'text/csv',
    'pdf',

    ])

import geoscrape

f = sg_open('../../../dat/interesting_urls.txt', 'w')
def process(web_resource):
    return web_resource.url, web_resource.get_content_type()

def handle_result((url, content_type)):
    if content_type in CONTENT_TYPE_KEEPERS:
        f.write(url+ '\n')

geoscrape.process_resources(sys.argv[1], process, handle_result)

f.close()