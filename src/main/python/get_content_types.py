import geoscrape

f = open('content_types.txt', 'w')
def process(web_resource):
    return web_resource.get_content_type()

def handle_result(content_type):
    f.write(content_type + '\n')

geoscrape.process_resources('/Users/shilad/Documents/IntelliJ/SourceGeography/scrape/', process, handle_result)

f.close()