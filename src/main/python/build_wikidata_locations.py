# TODO: run for all languages
import codecs
import sys

import country_info
import rule_inferrer

from sgconstants import *

def warn(message):
    sys.stderr.write(message + '\n')

country_names = {}

for c in country_info.read_countries():
    country_names[c.name] = c

country_names['Republic of Macedonia'] = country_names['Macedonia']
country_names['The Bahamas'] = country_names['Bahamas']
country_names['Georgia (country)'] = country_names['Georgia']
country_names['Republic of Ireland'] = country_names['Ireland']
country_names['Palestine'] = country_names['Palestinian Territory']
country_names['Macau'] = country_names['Macao']
country_names['United States Virgin Islands'] = country_names['U.S. Virgin Islands']
country_names['Burma'] = country_names['Macao']
country_names['The Gambia'] = country_names['Gambia']

exact_domains = {}
top_domains = {}

for line in codecs.open(PATH_WIKIDATA_DOMAIN_LOCATIONS, 'r', encoding='utf-8'):
    tokens = line.split('\t')
    (url, country, domain, top_domain) = tokens
    if country in country_names:
        top_domains[top_domain] = country_names[country]
        exact_domains[domain] = country_names[country]
    else:
        warn('unknown country: ' + country)

total = 0
matches = 0

f = codecs.open(PATH_WIKIDATA_URL_LOCATIONS, 'w', encoding='utf-8')
inf = rule_inferrer.Inferrer()
for ui in inf.get_urls():
    domain_parts = ui.domain.split('.')

    subdomains = []
    for i in range(len(domain_parts) - 1):
        subdomains.append('.'.join(domain_parts[i:]))

    country = None
    for d in subdomains:
        if d in exact_domains:
            country = exact_domains[d]
            break

    if not country:
        for d in subdomains:
            if d in top_domains:
                country = top_domains[d]
                break

    if country:
        matches += 1
        f.write(ui.url)
        f.write('\t')
        f.write(country.iso)
        f.write('\n')

    if total % 10000 == 0:
        print('matched %d of %d' % (matches, total))

    total += 1

print('matched %d of %d' % (matches, total))

f.close()
