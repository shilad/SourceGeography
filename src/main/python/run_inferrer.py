"""
Infers location of web pages based on four signals:
 - Whois lookup on domain
- country TLDs
- Language of web page
- Wikidata country source
"""
import collections
import random
import traceback

import urlinfo
import nb_inferrer
from sg_utils import *

# From http://stackoverflow.com/a/3679747/141245
#
def weighted_choice(choices):
    total = sum(w for c, w in choices.items())
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices.items():
        if upto + w >= r:
            return c
        upto += w
    assert False, "Shouldn't get here"

dao = urlinfo.UrlInfoDao()
inf = nb_inferrer.NaiveBayesInferrer(dao)
f = sg_open(PATH_URL_RESULT, 'w')
counts = collections.defaultdict(int)
for ui in dao.get_urls():
    try:
        (conf, dist) = inf.infer_dist(ui)
        for i in range(ui.count):
            chosen = 'null'
            top = 'null'
            rule = 'null'
            if dist:
                top = sorted(dist.keys(), key=dist.get, reverse=True)[0]
                chosen = weighted_choice(dist)
                rule = '%s-%.2d' % (inf.name , int(max(dist.values()) * 20) / 20.0)
            tokens = [chosen, top, rule, ui.url, ui.lang, ui.whois, ui.tld, ui.wikidata]
            for (i, t) in enumerate(tokens):
                if i > 0: f.write('\t')
                f.write('null' if t is None else t)
            f.write('\n')
            counts[rule] += 1
    except:
        warn('decoding %s failed: ' % ui.url)
        traceback.print_exc()
f.close()

for rule in counts:
    print rule, counts[rule]
