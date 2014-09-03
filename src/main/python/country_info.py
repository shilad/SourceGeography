import codecs
import os
from sg_utils import *


class Country:
    def __init__(self, row_tokens):
        self.iso = row_tokens[0].lower()
        self.iso3 = row_tokens[1].lower()
        self.fips = row_tokens[3].lower()
        self.name = row_tokens[4]
        self.population = int(row_tokens[7])
        self.tld = row_tokens[9][1:].lower()  # ".uk" -> "uk"
        self.langs = row_tokens[15].split(',')
        self.cleaned_langs = [l.lower().split('-')[0] for l in self.langs]
        self.prior = None  # Prior probability of the country generating a webpage
        self.title = None  # Article title in English Wikipedia

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            '{Country %s iso=%s, iso3=%s, fips=%s, pop=%s, tld=%s langs=%s prior=%s}' %
            (self.name, self.iso, self.iso3, self.fips, self.population, self.tld, self.cleaned_langs, self.prior)
        )


TITLE_MAPPING = {
    'Myanmar': 'Burma',
    'French Southern Territories': 'French Southern and Antarctic Lands',
    'Saint Helena': 'Saint Helena, Ascension and Tristan da Cunha',
    'Pitcairn': 'Pitcairn Islands',
    'Vatican': 'Vatican City',
    'Micronesia': 'Federated States of Micronesia',
    'Macedonia': 'Republic of Macedonia',
    'Bahamas': 'The Bahamas',
    'Georgia': 'Georgia (country)',
    'Ireland': 'Republic of Ireland',
    'Palestinian Territory': 'Palestine',
    'Macao': 'Macau',
    'U.S. Virgin Islands': 'United States Virgin Islands',
    'Gambia': 'The Gambia'
}


def read_countries():
    countries = []
    iso_countries = {}
    f = codecs.open(PATH_COUNTRY_INFO, 'r', encoding='utf-8')
    for line in f:
        if line.startswith('#'):
            continue
        c = Country(line.strip().split('\t'))
        countries.append(c)
        c.title = TITLE_MAPPING.get(c.name, c.name)

        iso_countries[c.iso] = c

    if os.path.isfile(PATH_COUNTRY_PRIOR):
        # initialize in case they don't appear in our dataset
        for c in countries:
            c.prior = 0.0000001

        for line in open(PATH_COUNTRY_PRIOR):
            tokens = line.strip().split('\t')
            iso = tokens[0]
            prior = float(tokens[1])
            iso_countries[iso].prior = prior

    return countries


if __name__ == '__main__':
    for c in read_countries():
        print `c`