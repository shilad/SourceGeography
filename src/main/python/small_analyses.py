import collections
from sg_utils import *

# A collection of simple analyses for the paper.


EDITOR_COUNTS = '../../../dat/editor-counts.tsv'
SOURCE_COUNTS = '../../../dat/source-counts.tsv'

def top_us_projs():
    for path in EDITOR_COUNTS, SOURCE_COUNTS:
        counts = collections.defaultdict(lambda: [0, 0])
        for row in sg_open_csvr(path):
            c = int(row['count'])
            proj = row['project']
            if row['other_country'] == 'us': counts[proj][0] += c
            counts[proj][1] += c

        results = []
        for (proj, (us, total)) in counts.items():
            results.append((1.0 * us / total, proj))

        results.sort()
        results.reverse()

        print 'results for', path
        for (proj, fraction_us) in results[:10]:
            print proj, fraction_us

def smallest_us_localness():
    counts = collections.defaultdict(lambda: [0, 0])
    for row in sg_open_csvr(SOURCE_COUNTS):
        if row['article_country'] == 'us':
            c = int(row['count'])
            proj = row['project']
            if row['other_country'] == 'us': counts[proj][0] += c
            counts[proj][1] += c

    results = []
    for (proj, (us, total)) in counts.items():
        results.append((1.0 * us / total, total, proj))

    results.sort()

    for (proj, total, fraction_us) in results[:20]:
        print proj, total, fraction_us

#top_us_projs()
smallest_us_localness()

