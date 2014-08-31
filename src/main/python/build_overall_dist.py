"""
Builds the background distribution of popularity for all countries.
"""

import collections

import inferrer
from sgconstants import *

inf = inferrer.Inferrer()
counts = collections.defaultdict(int)
for ui in inf.get_urls():
    (country, rule) = inf.infer(ui)
    if len(rule.split('-')) >= 2:
        counts[country] += 1

f = open(PATH_COUNTRY_PRIOR, 'w')
total = sum(counts.values())
for (country, n) in counts.items():
    f.write('%s\t%.5f\n' % (country.iso, 1.0 * n / total))
f.close()