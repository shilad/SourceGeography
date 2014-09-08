"""
Builds the mapping from urls to whois countries.
"""

from sg_utils import *

import urlinfo


domain_countries = {}
for line in sg_open(PATH_WHOIS_RAW):
    if line.strip().endswith('??'):
        continue
    tokens = line.strip().split('\t', 2)
    if len(tokens) != 3:
        raise Exception("invalid whois line: " + `line`)
    url = tokens[0]
    parse_type = tokens[1]
    whois = tokens[2]
    if parse_type in ('parsed', 'de_parsed'):
        if not whois.endswith('|1'):
            raise Exception("unexpected parsed record: " + `line`)
        whois = whois[:-1] + 'p'    # the code p indicates parsed
    elif parse_type != 'geonames':
        raise Exception("unexpected parse type: " + `line`)
    whois = whois.replace('\t', ',')
    domain_countries[url] = whois
    if len(domain_countries) % 100000 == 0:
        warn('doing domain ' + str(len(domain_countries)))

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
    f.write(u'\t')
    f.write(domain_countries[domain])
    f.write(u'\n')
f.close()



