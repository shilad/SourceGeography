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

import inferrer

from sgconstants import *


inf = inferrer.Inferrer()
f = codecs.open(PATH_URL_RESULT, 'w', encoding='utf-8')
counts = collections.defaultdict(int)
for ui in inf.get_urls():
    (country, rule) = inf.infer(ui)
    iso = 'unknown'
    if country: iso = country.iso
    tokens = [rule, iso, ui.url, ui.lang, ui.whois, ui.tld, ui.wikidata]
    for (i, t) in enumerate(tokens):
        if i > 0: f.write('\t')
        f.write('null' if t == None else t)
    f.write('\n')
    counts[rule] += 1
f.close()

for rule in counts:
    print rule, counts[rule]
