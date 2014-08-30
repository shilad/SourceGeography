"""
Detects the langauge of scraped web resources.

Requires:

pip install --pre langid

"""

import geoscrape
import langid


def process(web_resource):
    text = web_resource.get_text()
    if text:
        (lang, confidence) =  langid.classify(text)
        if confidence >= 0.9:
            return web_resource.url, lang
    return web_resource.url, 'unknown'

def handle_result((url, lang)):
    f.write('%s\t%s\n' % (url, lang))

f = open('url_langs.tsv', 'w')

geoscrape.process_resources(
    '/Users/shilad/Documents/IntelliJ/SourceGeography/scrape/',
    process,
    handle_result)

f.close()