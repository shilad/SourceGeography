#!/usr/bin/python -O

import codecs
import collections
import json

import urlinfo
from sg_utils import *


dao = urlinfo.UrlInfoDao()
title_to_country = {}

# first, build countries.json
data= []
for c in dao.get_countries():
    data.append({
        'iso' : c.iso,
        'name' : c.name,
        'title' : c.title,
        'population' : c.population
    })
    title_to_country[c.title + ' (en)'] = c

f = sg_open('../../../web/countries.json', 'w')
json.dump(data, f)
f.close()

# read in all predicted locations
predictions = {}

for line in sg_open(PATH_URL_RESULT):
    tokens = line.strip().split('\t')
    if len(tokens) >= 4:
        url = tokens[3]
        chosen = tokens[1]
        if chosen:
            predictions[url] = chosen

# next, summarize counts by language and country

url_counts = collections.defaultdict(int)
accumulator = collections.defaultdict(int)
successes = 0
total = 0
missing = collections.Counter()

for line in sg_open(PATH_SOURCE_URLS):
    total += 1
    tokens = line.strip().split('\t')

    if len(tokens) < 13:
        continue

    lang = tokens[0]
    title = tokens[6]
    url = tokens[12]

    if total % 1000000 == 0:
        warn('matched %d of %d records, total %d distinct (lang, containing_country, source_country) entries' %
             (successes, total, len(accumulator)))
    containing_country = title_to_country.get(title)
    if not containing_country:
        missing[title] += 1
        #warn('unknown containing country title: ' + `title`)
        continue

    if not url in predictions:
        continue

    n = url_counts[url]
    url_counts[url] += 1
    choices = predictions[url].split(',')
    iso = choices[n % len(choices)]
    predicted_country = dao.iso_countries.get(iso)
    if not predicted_country:
        warn('unknown predicted country iso code: ' + `iso`)
        continue

    successes += 1

    key = (lang, containing_country, predicted_country)
    accumulator[key] += 1


print('results for missing are ' + `missing`)

data = []
for ((lang, containing_country, predicted_country), n) in accumulator.items():
    data.append((lang, containing_country.iso, predicted_country.iso, n))

f = sg_open('../../../web/counts.json', 'w')
json.dump(data, f)
f.close()