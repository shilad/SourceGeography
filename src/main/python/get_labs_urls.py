#!/usr/bin/python -O

import codecs
import MySQLdb
import os
import sys
import traceback


LANGS = ['en', 'de', 'fr', 'nl', 'it', 'pl', 'es', 'ru', 'ja', 'pt', 'zh', 'sv', 'vi', 'uk', 'ca', 'no', 'fi', 'cs', 'hu', 'ko', 'fa', 'id', 'tr', 'ar', 'ro', 'sk', 'eo', 'da', 'sr', 'lt', 'ms', 'he', 'eu', 'sl', 'bg', 'kk', 'vo', 'hr', 'war', 'hi', 'et', 'gl', 'az', 'nn', 'simple', 'la', 'el', 'th', 'new', 'roa-rup', 'oc', 'sh', 'ka', 'mk', 'tl', 'ht', 'pms', 'te', 'ta', 'be-x-old', 'be', 'br', 'ceb', 'lv', 'sq', 'jv', 'mg', 'cy', 'lb', 'mr', 'is', 'bs', 'yo', 'an', 'lmo', 'hy', 'fy', 'bpy', 'ml', 'pnb', 'sw', 'bn', 'io', 'af', 'gu', 'zh-yue', 'ne', 'nds', 'ur', 'ku', 'uz', 'ast', 'scn', 'su', 'qu', 'diq', 'ba', 'tt', 'my', 'ga', 'cv', 'ia', 'nap', 'bat-smg', 'map-bms', 'wa', 'als', 'kn', 'am', 'gd', 'bug', 'tg', 'zh-min-nan', 'yi', 'vec', 'sco', 'hif', 'roa-tara', 'os', 'arz', 'nah', 'mzn', 'sah', 'ky', 'mn', 'sa', 'pam', 'hsb', 'li', 'mi', 'si', 'co', 'ckb', 'gan', 'glk', 'bo', 'fo', 'bar', 'bcl', 'ilo', 'mrj', 'se', 'fiu-vro', 'nds-nl', 'tk', 'vls', 'ps', 'gv', 'rue', 'dv', 'nrm', 'pag', 'pa', 'koi', 'rm', 'km', 'kv', 'udm', 'csb', 'mhr', 'fur', 'mt', 'zea', 'wuu', 'lij', 'ug', 'lad', 'pi', 'xmf', 'sc', 'bh', 'zh-classical', 'or', 'nov', 'ksh', 'ang', 'so', 'kw', 'stq', 'nv', 'hak', 'frr', 'ay', 'frp', 'ext', 'szl', 'pcd', 'ie', 'gag', 'haw', 'xal', 'ln', 'rw', 'pdc', 'pfl', 'vep', 'krc', 'crh', 'eml', 'gn', 'ace', 'to', 'ce', 'kl', 'arc', 'myv', 'dsb', 'as', 'bjn', 'pap', 'tpi', 'lbe', 'mdf', 'wo', 'jbo', 'kab', 'sn', 'av', 'cbk-zam', 'ty', 'srn', 'kbd', 'lo', 'lez', 'ab', 'mwl', 'ltg', 'na', 'ig', 'kg', 'tet', 'za', 'kaa', 'nso', 'zu', 'rmy', 'cu', 'tn', 'chr', 'chy', 'got', 'sm', 'bi', 'mo', 'bm', 'iu', 'pih', 'ik', 'ss', 'sd', 'pnt', 'cdo', 'ee', 'ha', 'ti', 'bxr', 'ts', 'om', 'ks', 'ki', 've', 'sg', 'rn', 'cr', 'dz', 'lg', 'ak', 'ff', 'tum', 'fj', 'st', 'tw', 'xh', 'ch', 'ny', 'ng', 'ii', 'cho', 'mh', 'aa', 'kj', 'ho', 'mus', 'kr', 'hz']

DB = None

PATH='source_urls.tsv'

WRITER = None


def main():
    global WRITER

    if os.path.isfile(PATH):
        WRITER = codecs.open(PATH, 'wa', encoding='utf-8')
    else:
        WRITER = codecs.open(PATH, 'w', encoding='utf-8')
        write_tokens([
                "language",
                "articleId",
                "articleTitle",
                "articleLat",
                "articleLong",
                "countryId",
                "countryTitle",
                "countryLat",
                "countryLong",
                "url",
                "domain",
                "effectiveDomain"
            ])

    for l in LANGS:
        do_lang(l)

    WRITER.close()


def do_lang(lang):
    warn('processing %s' % lang)
    if not connect(lang):
        return
    geotags = get_geotags()
    warn('found %d geo ids for %s' % (len(geotags), lang))
    for i, (page_id, (lat, lng)) in enumerate(geotags.items()):
        if i % 10000 == 0:
            warn('%s: doing %d of %d' % (lang, i, len(geotags)))
        try:
            process_page(lang, page_id, lat, lng)
        except:
            warn('processing of page %s failed:' % page_id)
            traceback.print_exc()

def get_geotags():
    global DB

    geotags= {}
    c = DB.cursor()
    c.execute('select gt_page_id, gt_lat, gt_lon from geo_tags')
    for row in c.fetchall():
        geotags[row[0]] = (row[1], row[2])
    c.close()
    return geotags
    

def process_page(lang, page_id, lat, lng):
    global DB

    c = DB.cursor()
    try:
        c.execute('select page_namespace, page_title, page_is_redirect from page where page_id = %s', page_id)
        rows = c.fetchall()
        if len(rows) == 0:
            warn('missing page %s' % page_id)
    
        ns = rows[0][0]
        title = rows[0][1]
        redirect = rows[0][2]
    
        if ns != 0 or redirect != 0:
            return

        c.execute('select el_to from externallinks where el_from = %s', page_id)

        for row in c.fetchall():
            url = row[0]
            write_tokens([
                lang,
                str(page_id),
                title,
                str(lat),
                str(lng),
                '-1',
                '-1',
                '-1',
                '-1',
                url,
            ])
    finally:
        c.close()


def connect(lang):
    global DB

    if DB:
        DB.close()
        DB = None
    try:
        name = lang + 'wiki_p'
        host = lang + 'wiki.labsdb'
        DB = MySQLdb.connect(
                db=name,
                read_default_file="~/replica.my.cnf", 
                host=host,
                use_unicode=True,
                charset='utf8'
            )
        return True
    except:
        warn('connection to %s failed' % lang)
        return False


def warn(message):
    sys.stderr.write(message + '\n')


def write_tokens(tokens):
    global WRITER

    for i, t in enumerate(tokens):
        if i > 0:
            WRITER.write('\t')
        WRITER.write(t.decode('utf-8'))
    WRITER.write('\n')
    

if __name__ == '__main__':
    main()
