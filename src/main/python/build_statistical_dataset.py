#!/usr/bin/python -O
import math

import country_info
from sg_utils import *

countries = country_info.read_countries()
newspapers = {}             # iso to num newspapers per capita
journals = {}               # iso to num journals
migration = {}              # iso1 -> iso2 -> num immigrants

def main():
    read_newspapers()
    read_journals()
    read_migration()

    enhance('../../../dat/source-counts.tsv', '../../../dat/source-counts-enhanced.tsv')
    enhance('../../../dat/editor-counts.tsv', '../../../dat/editor-counts-enhanced.tsv')

def enhance(original, enhanced):

    f1 = sg_open_csvr(original)
    f2 = sg_open_csvw(enhanced, f1.fieldnames + [
        # number of people migrating in each direction
        'migration1',
        'migration2',

        # number of newspapers in both countries
        'newspapers1',
        'newspapers2',

        # number of journal articles in both countries
        'journals1',
        'journals2',

        # share of wp language addition accounted for by editor / citation country
        'wplangshare',

        # similarity of distribution of languages in the two countries
        'langsim',

        # the weighted average of people in country 2 who speak languages in country 1
        'countrylangpop',

        # the weighted average of the language share of country 2 for country 1's languages
        'countrylangshare'
    ])
    for row in f1:
        lang = row['project']
        iso1 = row['article_country']
        iso2 = row['other_country']
        c1 = find_country_by_iso(iso1)
        c2 = find_country_by_iso(iso2)
        row['migration1'] = migration.get(iso1, {}).get(iso2, 0)
        row['migration2'] = migration.get(iso2, {}).get(iso1, 0)
        row['newspapers1'] = newspapers.get(iso1, 0)
        row['newspapers2'] = newspapers.get(iso2, 0)
        row['journals1'] = journals.get(iso1, 0)
        row['journals2'] = journals.get(iso2, 0)
        row['wplangshare'] = c2.lang_share2.get(lang, 0)
        row['langsim'] = language_sim(c1, c2)
        row['countrylangshare'] = language_share(c1, c2)
        row['countrylangpop'] = language_pop(c1, c2)

        f2.writerow(row)
    f1.close()
    f2.close()

def language_sim(cx, cy):
    xdotx = sum([x*x for x in cx.lang_speakers2.values()])
    ydoty = sum([y*y for y in cy.lang_speakers2.values()])
    xdoty = 0.0
    for lx in cx.lang_speakers2:
        if lx in cy.lang_speakers2:
            xdoty += cx.lang_speakers2[lx] * cy.lang_speakers2[lx]
    if xdotx == 0 or ydoty == 0:
        return 0.0
    else:
        return xdoty / math.sqrt(xdotx * ydoty)

def language_share(c1, c2):
    # How well c2 covers the set of languages in c1
    total = sum(c1.lang_speakers2.values())  + 0.000001
    result = 0.0
    for l in c1.lang_speakers2:
        result += 1.0 * c1.lang_speakers2[l] / total * c2.lang_share2.get(l, 0.0)
    return result

def language_pop(c1, c2):
    # How well c2 covers the set of languages in c1
    total = sum(c1.lang_speakers2.values())  + 0.000001
    result = 0.0
    for l in c1.lang_speakers2:
        result += 1.0 * c1.lang_speakers2[l] / total * c2.lang_speakers2.get(l, 0)
    return result

def read_newspapers():
    rename = {
        'Brunei Darussalam' : 'Brunei',
        'Congo' : 'Democratic Republic of the Congo',
        "C\xc3\xb4te d'Ivoire" : 'Ivory Coast',
        "Democratic People's Republic of Korea" : 'North Korea',
        'Hong Kong Special Administrative Region of China' : 'Hong Kong',
        'Iran, Islamic Republic of' : 'Iran',
        "Lao People's Democratic Republic" : 'Laos',
        'Libyan Arab Jamahiriya' : 'Libya',
        'Macao Special Administrative Region of China' : 'Macao',
        'Occupied Palestinian Territory' : 'Palestinian Territory',
        'Republic of Korea' : 'South Korea',
        'R\xc3\xa9union' : 'Reunion',
        'Russian Federation' : 'Russia',
        'Syrian Arab Republic' : 'Syria',
        'The former Yugoslav Republic of Macedonia' : 'Macedonia',
        'Timor-Leste' : 'East Timor',
        'Venezuela (Bolivarian Republic of)' : 'Venezuela',
        'United Kingdom of Great Britain and Northern Ireland' : 'United Kingdom',
        'United Republic of Tanzania' : 'Tanzania',
        'United States of America' : 'United States',
        'Viet Nam' : 'Vietnam'
    }
    for row in csv.DictReader(open('../../../dat/country_newspapers.csv')):
        name = row['Reference Area']
        name = rename.get(name, name)
        c = find_country_by_name(name)
        newspapers[c.iso] = int(float(row['Observation Value']) * c.population / 1000000.0)


def read_journals():
    rename = {
        'Russian Federation' : 'Russia',
        'Viet Nam' : 'Vietnam',
        'Syrian Arab Republic' : 'Syria',
        "C\xef\xbf\xbdte d'Ivoire" : 'Ivory Coast',
        'Palestine' : 'Palestinian Territory',
        'Libyan Arab Jamahiriya' : 'Libya',
        'Congo' : 'Democratic Republic of the Congo',
        'Brunei Darussalam' : 'Brunei',
        'Ha\xef\xbf\xbdti' : 'Haiti',
        'Democratic Republic Congo' : 'Democratic Republic of the Congo',
        'Falkland Islands (Malvinas)' : 'Falkland Islands',
        'Virgin Islands (U.S.)' : 'U.S. Virgin Islands',
        'Federated States of Micronesia' : 'Micronesia',
        'Virgin Islands (British)' : 'British Virgin Islands',
        'Timor-Leste' : 'East Timor',
        'Saint Vincent and The Grenadines' : 'Saint Vincent and the Grenadines',
        'Vatican City State' : 'Vatican',
        'Cocos (Keeling) Islands'  : 'Cocos Islands',
        'South Georgia and The South Sandwich Islands' : 'South Georgia and the South Sandwich Islands'
    }
    for row in  csv.DictReader(open('../../../dat/country_journals.csv', 'rU')):
        name = row['Country']
        name = rename.get(name, name)
        c = find_country_by_name(name)
        journals[c.iso] = int(row['Documents'].replace(',', ''))

def read_migration():
    for row in  csv.DictReader(open('../../../dat/country_migration.txt'), delimiter='\t'):
        origin = find_country_by_iso3(row['Country Origin Code'])
        dest = find_country_by_iso3(row['Country Dest Code'])
        if not origin or not dest:
            continue
        if not origin.iso in migration:
            migration[origin.iso] = {}
        if row['Value'] == '..':
            migration[origin.iso][dest.iso] = 0
        else:
            migration[origin.iso][dest.iso] = int(row['Value'])

def find_country_by_name(name):
    for c in countries:
        if c.name == name:
            return c
    warn('unknown country: %s' % `name`)
    return None

def find_country_by_iso(iso):
    iso = iso.lower()
    for c in countries:
        if c.iso == iso:
            return c
    warn('unknown country iso: %s' % `iso`)
    return None


def find_country_by_iso3(iso3):
    iso3 = iso3.lower()
    if not iso3 or iso3 in ('chi', 'zzz' ):
        return None
    rename = {
        'rom' : 'rou',
        'ksv' : 'xkx',
        'imy' : 'imn'
    }
    iso3 = rename.get(iso3, iso3)
    for c in countries:
        if c.iso3 == iso3:
            return c
    warn('unknown country iso3: %s' % `iso3`)
    return None


def enhance_row(row):
    pass

if __name__ == '__main__':
    main()