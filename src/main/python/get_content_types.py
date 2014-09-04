import collections
import geoscrape
import sys

def process(web_resource):
    return web_resource.get_content_type()

counts = collections.defaultdict(int)
def handle_result(content_type):
    counts[content_type] += 1

geoscrape.process_resources(sys.argv[1], process, handle_result)

f = open('dat/content_types.txt', 'w')
for t in counts:
    f.write('%s\t%d\n' % (t, counts[t]))
f.close()
