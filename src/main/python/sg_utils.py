# CONSTANTS

# path to raw soure urls file, created by running WmfExtractEnhancer on
# the urls extracted by running get_labs_urls on tool labs
import codecs
import urllib2
import sys


PATH_SOURCE_URLS = '../../../dat/source_urls.tsv'

# path to result of running get_langs on the scraped sources
PATH_URL_LANGS = '../../../dat/url_langs.tsv'

# Path to raw whois file, from dave
PATH_WHOIS_RAW = '../../../dat/whois_results3.txt'

# Path to file generated by running build_url_to_whois.py
PATH_URL_WHOIS = '../../../dat/url_whois.tsv'
PATH_URL_WHOIS_TEST = '../../../dat/url_whois_test.tsv'

# Path to interesting urls (those we use in our analysis)
PATH_URL_INTERESTING = '../../../dat/interesting_urls.txt'

# Number of times each url is referenced
# Generated by running build_url_counts.py
PATH_URL_COUNTS = '../../../dat/url_counts.tsv'

# Country info from geonames
PATH_COUNTRY_INFO = '../../../dat/countryInfo.txt'

# Path for prior distribution of countries, built by running build_overall_dists.py
PATH_COUNTRY_PRIOR = '../../../dat/country_priors.txt'

# Wikidata domain locations, built by running WikidataLocator.java
PATH_WIKIDATA_DOMAIN_LOCATIONS = '../../../dat/domain_wikidata_locations.tsv'

# Wikidata url locations, built by running build_wikidata_locations.py
PATH_WIKIDATA_URL_LOCATIONS = '../../../dat/url_wikidata_locations.tsv'

# Final result file
PATH_URL_RESULT = '../../../dat/url_locations.tsv'

# Binary versions of large data structures cached for efficiency
PATH_DAO_CACHE = '../../../dat/dao-cache.bin'

# Path to the 2012 data
PATH_2012 = '../../../dat/2012_test.tsv'

def warn(message):
    sys.stderr.write(message + '\n')

def sg_open(path, mode='r'):
    return codecs.open(path, mode, encoding='utf-8')

def url2host(url):
    return urllib2.urlparse.urlparse(url).netloc