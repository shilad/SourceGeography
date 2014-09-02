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
import marshal
import country_info
import sys
import urllib2

from sgconstants import *


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


class UrlInfoDao:
    def __init__(self):
        self.iso_countries = {}    # ISO country code to country object
        self.tld_country = {}      # TLD code to country object
        self.urls = {}              # url -> url info
        self.lang_countries = collections.defaultdict(list)      # ISO lang code to ISO country codes
        self.read_countries()
        self.analyze_langs()

        datafiles = [PATH_URL_LANGS, PATH_URL_WHOIS, PATH_WIKIDATA_URL_LOCATIONS]
        self.urls = self.get_cached_datastructure(datafiles)
        if self.urls:
            warn('sucessfully loaded urls from cache')
            return

        self.urls = {}              # url -> url info
        self.read_page_langs()
        self.read_whois()
        self.read_wikidata()

        warn('saving urls to cache for future use')
        #self.put_cached_datastructure(datafiles, self.urls)

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
            sum_scores = 1.0 * sum([s for (s, c) in country_scores]) + 0.000001
            self.lang_countries[lang] = [(c, score/sum_scores) for (score, c) in country_scores]
            if len(country_scores) > 2:
                print 'countries for %s are %s' % (lang, [(c.name,s) for (c, s) in self.lang_countries[lang]])

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

    def get_countries(self):
        return self.tld_country.values()

    def read_whois(self):
        if not   os.path.isfile(PATH_URL_WHOIS):
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
                if url not in self.urls:
                    self.urls[url] = UrlInfo(url)
                self.urls[url].wikidata = iso
                n += 1
            else:
                warn('invalid whois line: %s' % `line`)
        warn('finished reading %d wikidata entries' % n)

    def get_cached_datastructure(self, data_files):
        p = PATH_DAO_CACHE + '/' + self.get_cache_key(data_files)
        if not os.path.isfile(p):
            return None
        for df in data_files:
            if not os.path.isfile(df) or os.path.getmtime(p) < os.path.getmtime(df):
                return None
        f = open(p, 'rb')
        r = marshal.load(f)
        f.close()
        return r

    def get_cache_key(self, data_files):
        return str(abs(hash(','.join(data_files))))

    def put_cached_datastructure(self, data_files, obj):
        if not os.path.isdir(PATH_DAO_CACHE):
            os.makedirs(PATH_DAO_CACHE)
        p = PATH_DAO_CACHE + '/' + self.get_cache_key(data_files)
        warn('reading cached entry for %s' % data_files)
        f = open(p, 'wb')
        marshal.dump(obj, f)
        f.close()
