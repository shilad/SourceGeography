"""
Builds the background distribution of popularity for all countries.
"""

import collections
import os

import nb_inferrer
import urlinfo

from sg_utils import *

if os.path.isfile(PATH_COUNTRY_PRIOR): os.unlink(PATH_COUNTRY_PRIOR)

dao = urlinfo.UrlInfoDao()
inf = nb_inferrer.NaiveBayesInferrer(dao)
counts = collections.defaultdict(int)
total = 0
matched = 0
for ui in dao.get_urls():
    total += 1
    (country, rule) = inf.infer(ui)
    if rule >= 'nb-8':
        counts[country] += 1
        matched += 1
    if total % 100000 == 0:
        warn('identified %d of %d with high enough confidence for inclusion of prior' % (matched, total))

f = open(PATH_COUNTRY_PRIOR, 'w')
total = sum(counts.values())
for (country, n) in counts.items():
    f.write('%s\t%.5f\n' % (country.iso, 1.0 * n / total))
f.close()