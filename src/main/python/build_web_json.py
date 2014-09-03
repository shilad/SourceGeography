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
    tokens = line.strip.split('\t')
    if len(tokens) >= 4:
        url = tokens[3]
        chosen = tokens[1]
        if chosen:
            predictions[url] = chosen

# next, summarize counts by language and country

url_counts = collections.defaultdict(int)
accumulator = {}
successes = 0
total = 0

for line in sg_open(PATH_SOURCE_URLS):
    total += 1
    tokens = line.strip().split('\t')
    lang = tokens[0]
    title = tokens[6]
    url = tokens[12]
    country = title_to_country.get(title)
    if not country:
        warn('unknown country title: ' + `title`)
        continue

    if not url in predictions:
        continue

    successes += 1
    n = url_counts[url]
    url_counts[url] += 1
    choices = predictions[url].split(',')
    iso = choices[n % len(choices)]
    predicted = dao.iso_countries[]




    key = (lang, country, )
    if not lang in accumulator:
        accumulator[lang] =


