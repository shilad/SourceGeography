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

def compare_localness_lenses():
    localness = collections.defaultdict(lambda: [(0, 0), (0, 0)])

    for (i, path) in enumerate([EDITOR_COUNTS, SOURCE_COUNTS]):
        totals = collections.defaultdict(int)
        locals = collections.defaultdict(int)
        for row in sg_open_csvr(path):
            c = int(row['count'])
            key = (row['project'], row['article_country'])
            totals[key] += c
            if row['article_country'] == row['other_country']:
                locals[key] += c

        for key in locals:
            localness[key][i] = (1.0 * locals[key] / totals[key], totals[key])

    X = []
    Y = []
    for ((editor_p, editor_n), (source_p, source_n)) in localness.values():
        if editor_n > 100 and source_n > 100:
            X.append(editor_p)
            Y.append(source_p)

    from scipy.stats.stats import pearsonr, spearmanr

    print 'n = ', len(X)
    print 'spearman', spearmanr(X, Y)
    print 'pearson', pearsonr(X, Y)
    print 'num where source locality is higher: ', len([1 for (x, y) in zip(X, Y )if y > x])



#top_us_projs()
#smallest_us_localness()
compare_localness_lenses()

