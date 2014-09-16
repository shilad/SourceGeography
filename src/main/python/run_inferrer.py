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
import logistic_inferrer
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
inf = logistic_inferrer.LogisticInferrer(dao)
f = sg_open(PATH_URL_RESULT, 'w')
counts = collections.defaultdict(int)

for (n, ui) in enumerate(dao.get_urls()):
    if n % 100000 == 0:
        warn('infering result for url %d' % n)
    try:
        (conf, dist) = inf.infer_dist(ui)
        chosen = []
        top = u'null'
        rule = u'null'
        if dist:
            top = sorted(dist.keys(), key=dist.get, reverse=True)[0]
            rule = u'%s-%.2d' % (inf.name , int(max(dist.values()) * 20))
            chosen = [weighted_choice(dist) for i in range(ui.count)]
        tokens = [top, ','.join(chosen), rule, ui.url, ui.lang, ui.whois, ui.tld, ui.wikidata]
        for (i, t) in enumerate(tokens):
            if i > 0: f.write(u'\t')
            f.write(u'null' if t is None else unicode(t))
        f.write(u'\n')
        counts[rule] += ui.count
    except:
        warn('decoding %s failed: ' % ui.url)
        traceback.print_exc()
f.close()

for rule in counts:
    print rule, counts[rule]
