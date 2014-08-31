"""
Builds the mapping from urls to whois countries.
"""

import codecs
import sys
from sgconstants import *


domain_countries = {}
for line in codecs.open(PATH_WHOIS_RAW, 'r', encoding='utf-8'):
    tokens = line.strip().split('\t')
    if tokens[1] != '??':
        domain_countries[tokens[0]] = tokens[1]


num_invalid = 0
num_total = 0
num_matches = 0
prev_urls = {}
f = codecs.open(PATH_URL_WHOIS, 'w', encoding='utf-8')
for line in codecs.open(PATH_SOURCE_URLS, 'r', encoding='utf-8'):
    num_total += 1
    if num_total % 100000 == 0:
        print 'matched %d of %d (%d are invalid)' % (num_matches, num_total, num_invalid)
    tokens = line.strip().split('\t')
    if len(tokens) != 15:
        num_invalid += 1
        #sys.stderr.write('invalid line: %s\n' % `line`)
        continue
    url = tokens[9].strip()
    if url in prev_urls:
        num_matches += prev_urls[url]
        continue
    prev_urls[url] = 0
    domain = tokens[-1].strip()
    if not domain in domain_countries:
        continue
    prev_urls[url] += 1
    num_matches += 1
    f.write(url)
    f.write('\t')
    f.write(domain_countries[domain])
    f.write('\n')
f.close()



