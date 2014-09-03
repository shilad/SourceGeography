"""
Infers location of web pages based on four signals:
 - Whois lookup on domain
- country TLDs
- Language of web page
- Wikidata country source

"""

import collections
import sqlite3

import country_info

from sg_utils import *


class UrlInfo(object):
    __slots__ = ['url', 'lang', 'whois', 'wikidata', 'domain', 'tld', 'count']

    def __init__(self, url):
        self.url = url
        self.lang = None
        self.whois = None
        self.wikidata = None
        self.count = 1
        self.domain = url2host(self.url)
        self.tld = self.domain.split('.')[-1]

    def __repr__(self):
        return 'UrlInfo{ url=%s n=%s lang=%s whois=%s wikidata=%s domain=%s tld=%s }' % \
               (self.url, self.count, self.lang, self.whois, self.wikidata, self.domain, self.tld)

    def __str__(self):
        return `self`


def read_urls():
    f = sg_open(PATH_URL_INTERESTING)
    for line in f:
        yield line.strip()
    f.close()

class UrlInfoDao:
    def __init__(self):
        self.iso_countries = {}     # ISO country code to country object
        self.tld_countries = {}     # TLD code to country object
        self.country_priors = {}    # country to smoothed prior distribution
        self.url_db = None

        self.lang_countries = collections.defaultdict(list)      # ISO lang code to ISO country codes
        self.read_countries()
        self.analyze_langs()

        self.try_to_open_db()
        if self.url_db:
           warn('sucessfully loaded urls from cache')
           return

        warn('saving urls to cache for future use')
        try:
            self.rebuild_db()
        except:
            try: self.url_db.close()
            except: pass
            silentremove(PATH_DAO_CACHE)
            raise

    def read_countries(self):
        countries = country_info.read_countries()
        for c in countries:
            self.iso_countries[c.iso] = c
            self.tld_countries[c.tld] = c

        # Build raw priors
        hasPrior = len([c for c in self.get_countries() if c.prior is not None]) > 0
        for c in countries:
            if hasPrior:
                self.country_priors[c] = c.prior if c.prior else 0.0
            else:
                self.country_priors[c] = c.population if c.population else 0.0

        # Add equal smoothing constant that sums to 1% of total.
        total = sum(self.country_priors.values()) * 1.01
        smoothing_k = total * 0.01 / len(countries)
        for c in countries:
            self.country_priors[c] = (self.country_priors[c] + smoothing_k) / total

        self.iso_countries['uk'] = self.iso_countries['gb']         # hack - uk is "unofficial" gb

    def analyze_langs(self):
        lang2countries = collections.defaultdict(list)


        for c in self.iso_countries.values():
            for (i, l) in enumerate(c.cleaned_langs):
                p = c.prior if c.prior is None else c.prior
                s = p * 1.0 / ((i+1) ** 2.5)
                lang2countries[l].append((s, c))

        for lang, country_scores in lang2countries.items():
            country_scores.sort()
            country_scores.reverse()
            sum_scores = 1.0 * sum([s for (s, c) in country_scores]) + 0.000001
            self.lang_countries[lang] = [(c, score/sum_scores) for (score, c) in country_scores]
            if len(country_scores) > 2:
                print 'countries for %s are %s' % (lang, [(c.name,s) for (c, s) in self.lang_countries[lang]])

    def read_page_langs(self, urls):
        if not os.path.isfile(PATH_URL_LANGS):
            warn('0 results not available...')
            return

        warn('reading url webpage langs')
        count = 0
        for line in sg_open(PATH_URL_LANGS):
            tokens = line.strip().split('\t')
            if len(tokens) == 2:
                url = tokens[0]
                lang = tokens[1]
                if lang != 'unknown':
                    if not url in urls:
                        urls[url] = UrlInfo(url)
                    urls[url].lang = lang
                    count += 1
            else:
                warn('invalid whois line: %s' % `line`)
        warn('finished reading %d url lang entries' % count)

    def read_whois(self, urls):
        if not  os.path.isfile(PATH_URL_WHOIS):
            warn('whois results not available...')
            return

        warn('reading whois results...')

        num_whois = 0
        for line in sg_open(PATH_URL_WHOIS):
            tokens = line.strip().split('\t')
            if len(tokens) == 2:
                url = tokens[0]
                whois = tokens[1]
                if whois != '??':
                    if not url in urls:
                        urls[url] = UrlInfo(url)
                    urls[url].whois = whois
                    num_whois += 1
            else:
                warn('invalid whois line: %s' % `line`)
        warn('finished reading %d whois entries' % num_whois)

    def read_wikidata(self, urls):
        if not os.path.isfile(PATH_WIKIDATA_URL_LOCATIONS):
            warn('wikidata results not available...')
            return

        warn('reading wikidata results...')
        n = 0
        for line in sg_open(PATH_WIKIDATA_URL_LOCATIONS):
            tokens = line.strip().split('\t')
            if len(tokens) == 2:
                url = tokens[0]
                iso = tokens[1]
                if url not in urls:
                    urls[url] = UrlInfo(url)
                urls[url].wikidata = iso
                n += 1
            else:
                warn('invalid whois line: %s' % `line`)
        warn('finished reading %d wikidata entries' % n)

    def read_counts(self, urls):
        if not os.path.isfile(PATH_URL_COUNTS):
            warn('counts results not available...')
            return

        warn('reading wikidata results...')
        n = 0
        for line in sg_open(PATH_URL_COUNTS):
            tokens = line.strip().split('\t')
            if len(tokens) == 2:
                url = tokens[0]
                url_count = int(tokens[1])
                if url not in urls:
                    urls[url] = UrlInfo(url)
                urls[url].count = url_count
                n += 1
            else:
                warn('invalid url_count line: %s' % `line`)
        warn('finished reading %d url count entries' % n)

    def try_to_open_db(self):
        if not os.path.isfile(PATH_DAO_CACHE):
            return None

        datafiles = [PATH_URL_LANGS, PATH_URL_WHOIS, PATH_WIKIDATA_URL_LOCATIONS, PATH_URL_COUNTS]
        for df in datafiles:
            if not os.path.isfile(df) or os.path.getmtime(PATH_DAO_CACHE) < os.path.getmtime(df):
                return None

        self.url_db = sqlite3.connect(PATH_DAO_CACHE)

    def rebuild_db(self):
        silentremove(PATH_DAO_CACHE)

        infos = {}

        self.read_page_langs(infos)
        self.read_whois(infos)
        self.read_wikidata(infos)
        self.read_counts(infos)

        self.url_db = sqlite3.connect(PATH_DAO_CACHE)

        c = self.url_db.cursor()
        c.execute("""
            CREATE TABLE URL_INFO
            (url TEXT primary key, count INTEGER, lang TEXT, whois TEXT, wikidata TEXT)
        """)
        self.url_db.commit()

        urls = sorted(infos.keys())

        for i in xrange(0, len(infos), 10000):
            if i % 100000 == 0:
                warn('inserting %s' % i)

            batch = [infos[u] for u in urls[i:(i+10000)]]
            c.executemany("INSERT INTO URL_INFO VALUES(?,?,?,?,?)",
                [(u.url, u.count, u.lang, u.whois, u.wikidata) for u in batch])

        self.url_db.commit()

    def get_url(self, url):
        c = self.url_db.cursor()
        try:
            for row in c.execute('SELECT url, count, lang, whois, wikidata FROM URL_INFO WHERE url=?', (url,)):
                ui = UrlInfo(row[0])
                ui.count = row[1]
                ui.lang = row[2]
                ui.whois = row[3]
                ui.wikidata = row[4]
                return ui
            return None
        finally:
            c.close()

    def get_urls(self):
        c = self.url_db.cursor()
        try:
            for row in c.execute('SELECT url, count, lang, whois, wikidata FROM URL_INFO'):
                ui = UrlInfo(row[0])
                ui.count = row[1]
                ui.lang = row[2]
                ui.whois = row[3]
                ui.wikidata = row[4]
                yield ui
        finally:
            c.close()


    def get_countries(self):
        return self.tld_countries.values()

import os, errno

def silentremove(filename):
    """
    Silently remove a file, from http://stackoverflow.com/a/10840586/141245
    :param filename:
    :return:
    """
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured

if __name__ == '__main__':
    dao = UrlInfoDao()

    print dao.get_url('http://google.com')