import codecs
import collections

from sgconstants import *

url_counts = collections.defaultdict(int)

for line in codecs.open(PATH_SOURCE_URLS, 'r', encoding='utf-8'):
    tokens = line.split('\t')
    if len(tokens) >= 13:
        url = tokens[12].strip()
        url_counts[url] += 1


f = codecs.open(PATH_URL_COUNTS, 'w', encoding='utf-8')
for url in sorted(url_counts.keys()):
    f.write(url)
    f.write('\t')
    f.write(str(url_counts[url]))
    f.write('\n')

f.close()