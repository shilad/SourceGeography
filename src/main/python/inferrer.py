"""
Infers location of web pages based on four signals:
 - Whois lookup on domain
- country TLDs
- Language of web page
- Wikidata country source
"""

import codecs
import collections
import os
import country_info
import sys
import urllib2

from sgconstants import *

GENERIC_CC_TLDS = set(['tv'])

class UrlInfo:
    def __init__(self, url):
        self.url = url
        self.lang = None
        self.whois = None
        self.wikidata = None
        self.tld = urllib2.urlparse.urlparse(url).netloc.split('.')[-1]
        self.domain = urllib2.urlparse.urlparse(self.url).netloc

def warn(message):
    sys.stderr.write(message + '\n')


class Inferrer:
    def __init__(self):
        self.iso_countries = {}    # ISO country code to country object
        self.tld_country = {}      # TLD code to country object
        self.urls = {}              # url -> url info
        self.lang_countries = collections.defaultdict(list)      # ISO lang code to ISO country codes
        self.read_countries()
        self.analyze_langs()
        self.read_page_langs()
        self.read_whois()
        self.read_wikidata()

    def read_countries(self):
        for c in country_info.read_countries():
            self.iso_countries[c.iso] = c
            self.tld_country[c.tld] = c

        self.iso_countries['uk'] = self.iso_countries['gb']         # hack - uk is "unofficial" gb

    def analyze_langs(self):
        lang2countries = collections.defaultdict(list)

        for c in self.iso_countries.values():
            for (i, l) in enumerate(c.cleaned_langs):
                p = c.population if c.prior is None else c.prior
                s = p * 1.0 / ((i+1) ** 2.5)
                lang2countries[l].append((s, c))

        for lang, country_scores in lang2countries.items():
            country_scores.sort()
            country_scores.reverse()
            self.lang_countries[lang] = [c for (score, c) in country_scores]
            if len(country_scores) > 2:
                print 'countries for %s are %s' % (lang, [c.name for c in self.lang_countries[lang]])

    def read_page_langs(self):
        if not os.path.isfile(PATH_URL_LANGS):
            warn('0 results not available...')
            return

        warn('reading url webpage langs')
        num_langs = 0
        for line in codecs.open(PATH_URL_LANGS, 'r', encoding='utf-8'):
            tokens = line.strip().split('\t')
            if len(tokens) == 2:
                url = tokens[0]
                lang = tokens[1]
                if lang != 'unknown':
                    if not url in self.urls:
                        self.urls[url] = UrlInfo(url)
                    self.urls[url].lang = lang
                    num_langs += 1
            else:
                warn('invalid whois line: %s' % `line`)
        warn('finished reading %d url lang entries' % num_langs)

    def get_urls(self):
        return self.urls.values()

    def read_whois(self):
        if not os.path.isfile(PATH_URL_WHOIS):
            warn('whois results not available...')
            return

        warn('reading whois results...')
        # f = codecs.open('../../../url_whois_test.tsv', 'w', encoding='utf-8')
        num_whois = 0
        for line in codecs.open(PATH_URL_WHOIS, 'r', encoding='utf-8'):
            tokens = line.strip().split('\t')
            if len(tokens) == 2:
                url = tokens[0]
                #if not url in self.urls: # testing hack...
                #    continue
                # f.write(line)
                whois = tokens[1]
                if whois != '??':
                    if not url in self.urls:
                        self.urls[url] = UrlInfo(url)
                    self.urls[url].whois = whois
                    num_whois += 1
            else:
                warn('invalid whois line: %s' % `line`)
        # f.close()
        warn('finished reading %d whois entries' % num_whois)

    def read_wikidata(self):
        if not os.path.isfile(PATH_WIKIDATA_URL_LOCATIONS):
            warn('wikidata results not available...')
            return

        warn('reading wikidata results...')
        n = 0
        for line in codecs.open(PATH_WIKIDATA_URL_LOCATIONS):
            tokens = line.strip().split('\t')
            if len(tokens) == 2:
                url = tokens[0]
                iso = tokens[1]
                self.urls[url].wikidata = iso
                n += 1
            else:
                warn('invalid whois line: %s' % `line`)
        warn('finished reading %d wikidata entries' % n)

    def stats(self):
        field_counts = collections.defaultdict(int)
        for ui in self.urls.values():
            if ui.tld in ('mil', 'gov'):
                field_counts['milgov'] += 1
                continue
            fields = []
            if ui.lang:
                fields.append('lang')
            if ui.tld:
                fields.append('tld')
            if ui.whois:
                fields.append('whois')
            if ui.wikidata:
                fields.append('wikidata')
            field_counts['-'.join(fields)] += 1

        print('stats on fields:')
        for fields, n in field_counts.items():
            print('\t%s: %d' % (fields, n))

    def infer(self, url_info):
        if url_info.tld in ('mil', 'gov'):
            return (self.tld_country['us'], 'milgov')

        if url_info.whois and url_info.whois not in self.iso_countries:
            warn("unknown whois entry: %s" % url_info.whois)

        tldc = self.tld_country.get(url_info.tld)
        whoisc = self.iso_countries.get(url_info.whois)
        langcs = self.lang_countries.get(url_info.lang, [])
        wdc = self.iso_countries.get(url_info.wikidata)

        if wdc and tldc and wdc != tldc:
            warn("for url %s wdc=%s and tldc=%s disagree" % (url_info.url, wdc, tldc))

        if wdc:
            rule = 'wd'
            if wdc == whoisc:
                rule += '-whois'
            if wdc in langcs:
                rule += '-lang'
            if wdc == tldc:
                rule += '-tld'
            if len(rule.split('-')) >= 2:
                return (wdc, rule)

        if tldc:
            # is it a perfect match?
            if tldc == whoisc and tldc in langcs:
                return (tldc, 'tld-whois-lang')

            # do two out of three match?
            if tldc == whoisc:
                return (tldc, 'tld-whois')
            elif tldc in langcs:
                return (tldc, 'tld-lang')
            elif whoisc and whoisc in langcs:
                return (whoisc, 'whois-lang')

            # all three disagree (or some are missing)
            if wdc and url_info.tld  in GENERIC_CC_TLDS:
                return (wdc, 'wd')
            else:
                return (tldc, 'tld')
        else: # .com, .net, .info, .org, etc
            if whoisc in langcs:
                return (whoisc, 'whois-lang')
            elif wdc:
                return (wdc, 'wd')
            elif whoisc:
                return (whoisc, 'whois')
            elif langcs:
                return (langcs[0], 'lang')
            else:
                return (None, 'unknown')


if __name__ == '__main__':
    i = Inferrer()
    i.stats()