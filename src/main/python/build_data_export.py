#!/usr/bin/python -O

import codecs
import collections
import json

import urlinfo
from sg_utils import *


def main():
    dao = urlinfo.UrlInfoDao()
    write_countries(dao)
    write_editors(dao)
    write_sources(dao)

def write_countries(dao):
    title_to_country = {}
    data= []
    for c in dao.get_countries():
        data.append({
            'iso' : c.iso,
            'name' : c.name,
            'title' : c.title,
            'population' : c.population
        })
        title_to_country[c.title + ' (en)'] = c
    f = codecs.open('../../../web/countries.json', 'w', encoding='utf-8')
    json.dump(data, f)
    f.close()
    return title_to_country

def write_editors(dao):
    def clean(s):
        if s[0] == '"' and s[-1] == '"':
            return s[1:-1]
        else:
            return s

    data = []
    for (i, line) in enumerate(open('../../../dat/aggregated_edit_geodata.tsv')):
        if i == 0:
            continue
        tokens = [clean(t) for t in line.strip().split('\t')]
        project = tokens[0]
        if project.endswith('wiki'):
            project = project[:-4]
        article_country = dao.iso_countries.get(tokens[1].lower())
        editor_country = dao.iso_countries.get(tokens[2].lower())
        if not article_country or not editor_country:
            if not article_country: warn('unknown country: %s' % `tokens[1].lower()`)
            if not editor_country: warn('unknown country: %s' % `tokens[2].lower()`)
            continue
        edits = int(tokens[3])
        data.append((project, article_country, editor_country, edits))

    write_data('editor-counts', data)

def write_data(name, counts):

    tsvf = codecs.open('../../../dat/' + name + '.tsv', 'w', encoding='utf-8')
    tsvf.write('\t'.join([
        'project',
        'article_country',
        'article_is_native',
        'other_country',
        'other_is_native',
        'distance',
        'count'
    ]) + '\n')

    data= []
    for (lang, containing_country, predicted_country, n) in counts:
        article_native = containing_country.wp_is_native(lang)
        source_native = predicted_country.wp_is_native(lang)
        dist = containing_country.distances.get(predicted_country, -1)
        if dist < 0: dist = predicted_country.distances.get(containing_country, -1)
        row = (lang, containing_country.iso, article_native, predicted_country.iso, source_native, dist, n)
        tsvf.write(u'\t'.join([str(x) for x in row]) + '\n')
        data.append(row)

    var_name = name.split('-')[0].upper() + '_DATA' # e.g. EDITOR_DATA
    jsonf = codecs.open('../../../web/' + name + '.js', 'w', encoding='utf-8')
    jsonf.write('var ' + var_name + ' = ')
    json.dump(data, jsonf)
    jsonf.close()
    tsvf.close()


def write_sources(dao):
    title_to_country = {}
    for c in dao.get_countries():
        title_to_country[c.title + ' (en)'] = c

    # read in all predicted locations
    predictions = {}
    for line in sg_open(PATH_URL_RESULT):
        tokens = line.strip().split('\t')
        if len(tokens) >= 4:
            url = tokens[3]
            chosen = tokens[1]
            if chosen:
                predictions[url] = tuple(chosen.split(','))

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
        choices = predictions[url]
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
        data.append((lang, containing_country, predicted_country, n))

    write_data('source-counts', data)

if __name__ == '__main__':
    main()