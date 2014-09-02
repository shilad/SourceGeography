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


def warn(message):
    sys.stderr.write(message + '\n')


class Inferrer:
    def __init__(self, url_info_dao):
        self.dao = url_info_dao

    def stats(self):
        field_counts = collections.defaultdict(int)
        for ui in self.dao.get_urls():
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
            return (self.dao.tld_country['us'], 'milgov')

        if url_info.whois and url_info.whois not in self.dao.iso_countries:
            warn("unknown whois entry: %s" % url_info.whois)

        tldc = self.dao.tld_country.get(url_info.tld)
        whoisc = self.dao.iso_countries.get(url_info.whois)
        langcs = self.dao.lang_countries.get(url_info.lang, [])
        wdc = self.dao.iso_countries.get(url_info.wikidata)

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