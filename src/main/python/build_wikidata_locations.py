# TODO: run for all languages
import sys

import country_info

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

for line in open(PATH_WIKIDATA_DOMAIN_LOCATIONS):
    tokens = line.split('\t')
    (url, country, domain, top_domain) = tokens
    if country in country_names:
        top_domains[top_domain] = country
        exact_domains[domain] = country
    else:
        warn('unknown country: ' + country)




