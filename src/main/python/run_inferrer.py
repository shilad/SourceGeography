"""
Infers location of web pages based on four signals:
 - Whois lookup on domain
- country TLDs
- Language of web page
- Wikidata country source
"""
import codecs
import collections
import sys
import traceback

import urlinfo
import rule_inferrer

from sgconstants import *


dao = urlinfo.UrlInfoDao()
inf = rule_inferrer.Inferrer(dao)
f = codecs.open(PATH_URL_RESULT, 'w', encoding='utf-8')
counts = collections.defaultdict(int)
for ui in dao.get_urls():
    try:
        (country, rule) = inf.infer(ui)
        iso = 'unknown'
        if country: iso = country.iso
        tokens = [rule, iso, ui.url, ui.lang, ui.whois, ui.tld, ui.wikidata]
        for (i, t) in enumerate(tokens):
            if i > 0: f.write('\t')
            f.write('null' if t is None else t)
        f.write('\n')
        counts[rule] += 1
    except:
        sys.stderr.write('decoding %s failed: ' % ui.url)
        traceback.print_exc()
f.close()

for rule in counts:
    print rule, counts[rule]
