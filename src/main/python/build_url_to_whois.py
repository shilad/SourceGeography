"""
Builds the mapping from urls to whois countries.
"""

from sg_utils import *

import urlinfo


domain_countries = {}
for line in sg_open(PATH_WHOIS_RAW):
    tokens = line.strip().split('\t')
    if tokens[1] != '??':
        domain_countries[tokens[0]] = tokens[1]

interesting = set(urlinfo.read_urls())

num_invalid = 0
num_total = 0
num_matches = 0
prev_urls = {}
f = sg_open(PATH_URL_WHOIS, 'w')
for line in sg_open(PATH_SOURCE_URLS):
    tokens = line.strip().split('\t')
    if len(tokens) != 15:
        num_invalid += 1
        continue
    url = tokens[9].strip()
    if not url in interesting:
        continue
    num_total += 1
    if num_total % 100000 == 0:
        warn('matched %d of %d (%d are invalid)' % (num_matches, num_total, num_invalid))
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



