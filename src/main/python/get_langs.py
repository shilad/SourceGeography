"""
Detects the langauge of scraped web resources.

Requires:

pip install langid  (on mac, pip install --pre langid)

"""
import codecs

import geoscrape
import langid
import sys

if len(sys.argv) != 2:
    sys.stdout.write('usage: %s base_scrape_dir\n' % sys.argv[0])
    sys.exit(1)


def process(web_resource):
    text = web_resource.get_text()
    if text:
        (lang, confidence) =  langid.classify(text)
        if confidence >= 0.9:
            return web_resource.url, lang
    return web_resource.url, 'unknown'

def handle_result((url, lang)):
    f.write('%s\t%s\n' % (url, lang))

f = codecs.open('url_langs.tsv', 'w', encoding='utf-8')

geoscrape.process_resources(
    sys.argv[1],
    process,
    handle_result)

f.close()