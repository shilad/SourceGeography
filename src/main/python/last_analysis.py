import collections
from sg_utils import *


PROJS = ['fr', 'ar']
ARTICLE_COUNTRIES = ['Overall', 'eg', 'ir', 'iq', 'tn']
TO_COUNT = ['dz', 'eg', 'ir', 'iq', 'sa', 'tn', 'fr', 'be', 'ca', 'gb', 'us', 'Other']

def main():
    rows = [[] for i in range(len(TO_COUNT))]
    for proj in PROJS:
        to_merge = analyze('../../../dat/editor-counts.tsv', proj)
        for i in range(len(to_merge)):
            rows[i].extend(to_merge[i])
    writer=csv.writer(open('../../../dat/editor-final-analysis.csv','wb'))
    for row in rows:
        writer.writerow(row)

    rows = [[] for i in range(len(TO_COUNT))]
    for proj in PROJS:
        to_merge = analyze('../../../dat/source-counts.tsv', proj)
        for i in range(len(to_merge)):
            rows[i].extend(to_merge[i])
    writer=csv.writer(open('../../../dat/publisher-final-analysis.csv','wb'))
    for row in rows:
        writer.writerow(row)



def analyze(path, proj):
    counts = collections.defaultdict(lambda : collections.defaultdict(int))
    for row in sg_open_csvr(path):
        if not row['project'] == proj:
            continue
        count = int(row['count'])
        ac = row['article_country']
        oc = row['other_country']
        if ac in ARTICLE_COUNTRIES:
            if oc in TO_COUNT:
                counts[ac][oc] += count
            else:
                counts[ac]['Other'] += count
        if oc in TO_COUNT:
            counts['Overall'][oc] += count
        else:
            counts['Overall']['Other'] += count

    results = []
    for oc in TO_COUNT:
        row = []
        for ac in ARTICLE_COUNTRIES:
            row.append(1.0 * counts[ac][oc] / sum(counts[ac].values()))
        results.append(row)
    return results

main()