import collections

import urlinfo

from sg_utils import *

urls = set(urlinfo.read_urls())

url_counts = collections.defaultdict(int)

for line in sg_open(PATH_SOURCE_URLS, 'r'):
    tokens = line.split('\t')
    if len(tokens) >= 13:
        url = tokens[12].strip()
        if url in urls:
            url_counts[url] += 1


f = sg_open(PATH_URL_COUNTS, 'w')
for url in sorted(url_counts.keys()):
    f.write(url)
    f.write('\t')
    f.write(str(url_counts[url]))
    f.write('\n')

f.close()