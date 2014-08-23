#!/usr/bin/env python

import chardet
import codecs
import httplib
import os
import psycopg2
import random
import re
import shutil
import string
import sys
import tarfile
import tempfile
import time
import traceback
import urlparse
import urllib2

import psycopg2.extensions

PG_CNX = psycopg2.connect(host = sys.argv[1], user = sys.argv[2], password = sys.argv[3], database = sys.argv[4])
PG_CNX.set_client_encoding('UTF-8')
PG_CURSOR = PG_CNX.cursor()
SLEEP_TIME = 0
BATCH_SIZE = 100
END_TIME = time.time() + 40 * 60
BINARY_EXTS = set(['pdf', 'jpg', 'gif', 'xls', 'doc', 'png', 'zip', 'swf', 'tif', 'dot', 'jpeg', 'xlsx'])
BLOCKSIZE = 1048576 # or some other, desired size in bytes
ENCODING_DETECT_BYTES = 10*1024*1024   # 10 MBs
DRY_RUN = False

RETRY_COUNT = {}
RETRY_ERRORS = {}


def main():
    if not os.path.isdir('batches'):
        os.mkdir('batches')

    while time.time() < END_TIME:
        urls = get_batch(BATCH_SIZE)
        batch_id = random_word(8)
        batch_dir = 'batches/' + batch_id
        os.mkdir(batch_dir)

        tar_path = batch_dir + '.tar.bz2'
        dest_dir =  os.path.join(time.strftime("%Y-%m-%d/%H"), batch_id[0])
        dest = os.path.join(dest_dir, batch_id + '.tar.bz2')

        for url in urls:
            if time.time() > END_TIME:
                break
            do_one_url(url, batch_id, dest)

        tar = tarfile.open(tar_path, 'w:bz2', bufsize=BLOCKSIZE)
        tar.add(batch_dir, arcname=batch_id)
        tar.close()


        if DRY_RUN:
            os.system('mkdir -p foo/%s' % dest_dir)
            os.system('cp %s foo/%s' % (tar_path, dest))
        else:
            os.system('aws s3 cp %s s3://sourcegeography/scrape/%s' % (tar_path, dest))

        shutil.rmtree(batch_dir)
        os.unlink(tar_path)

def random_word(length):
    return ''.join(random.choice(string.lowercase + string.digits) for i in range(length))

def get_batch(n):
    global PG_CURSOR, PG_CNX

    PG_CURSOR.execute("""
            lock table urls in SHARE ROW EXCLUSIVE mode;
            UPDATE urls
            SET    started = 'now()'
            WHERE  url in (SELECT url FROM urls WHERE started IS NULL LIMIT %s)
            RETURNING url
        """, (n,))
    PG_CNX.commit()
    return [row[0] for row in PG_CURSOR.fetchall()]

def encoding_works(path, encoding):
    f = None
    try:
        f = codecs.open(path, encoding=encoding)
        while f.read(BLOCKSIZE):
            pass
        return True
    except:
        return False
    finally:
        if f: f.close()

def guess_charset(response, download):
    ctype = response.headers.get('content-type', '').lower()
    if 'charset=' in ctype:
        charset = ctype.split('charset=')[-1]
        if encoding_works(download, charset):
            return charset

    s = codecs.open(download, encoding='ascii', errors='ignore').read(10000).lower()
    mat_meta = re.compile('<meta.*charset=(")?([a-z0-9_-]+)[^a-z0-9_-]').search
    m = mat_meta(s)
    if m:
        charset = m.group(2)
        if encoding_works(download, charset):
            return charset

    s = open(download, 'rb').read(ENCODING_DETECT_BYTES)
    d = chardet.detect(s)
    charset = d['encoding']
    if charset and encoding_works(download, charset):
        return charset

    return 'utf-8'


def is_binary(url):
    lurl = url.lower()
    for ext in BINARY_EXTS:
        if lurl.endswith('.' + ext):
            return True
        elif ('.' + ext + '?') in lurl:
            return True
        elif ('.' + ext + '#') in lurl:
            return True
        elif ('.' + ext + '&') in lurl:
            return True
    return False


def do_one_url(url, batch_id, dest_file):
    global RETRY_COUNT
    global RETRY_ERRORS

    host = ''
    response = None
    try:
        sys.stderr.write('doing %s\n' % url)
        urlinfo = urlparse.urlparse(url)
        host = urlinfo.hostname

        if host in RETRY_COUNT:
            if try_again(RETRY_COUNT[host]):
                sys.stderr.write('retrying %s after %d attempts\n' % (host, RETRY_COUNT[host]))
            else:
                sys.stderr.write('host %s in penalty box for attempt %d\n' % (host, RETRY_COUNT[host]))
                time.sleep(1.0)
                raise urllib2.URLError('Penalty box error: ' + RETRY_ERRORS[host])

        request = urllib2.Request(url)
        handler1 = urllib2.HTTPRedirectHandler()
        handler2 = urllib2.HTTPCookieProcessor()
        opener3 = urllib2.build_opener(handler1, handler2)
        opener3.addheaders = [
            ('User-agent' , 'Mozilla/5.0'),
            ('Host' , urlinfo.netloc)
        ]
        response = opener3.open(request, timeout=20.0)

        url_id = random_word(8)

        # write a temporary file in the original encoding
        tmp = tempfile.mktemp()
        f = open(tmp, 'wb')
        try:
            shutil.copyfileobj(response, f, BLOCKSIZE)
        finally:
            response.close()
            f.close()

        # write the metadata file
        f = codecs.open('batches/%s/%s.meta' % (batch_id, url_id), 'w', encoding='UTF-8')
        try:
            f.write(url)
            f.write('\n')
            for (key, val) in response.headers.items():
                f.write(key)
                f.write(':')
                f.write(val)
                f.write('\n')
        finally:
            f.close()

        if is_binary(url):
            shutil.move(tmp, 'batches/%s/%s.bin' % (batch_id, url_id))
        else:
            charset = guess_charset(response, tmp)
            reencode(tmp, charset, 'batches/%s/%s.utf8' % (batch_id, url_id), 'utf-8')

        PG_CURSOR.execute("""
            UPDATE urls
            SET completed = 'now()', final_url = %s, status_code = %s, archive = %s, file = %s
            WHERE url = %s
        """, (response.geturl(), response.getcode(), dest_file, url_id, url))

        if host in RETRY_COUNT:
            del(RETRY_ERRORS[host])
            del(RETRY_COUNT[host])

    except urllib2.HTTPError as e:
        reason = str(e)
        sys.stderr.write('doing %s failed (%s %s)\n' % (url, e.code, reason))
        PG_CURSOR.execute("""
            UPDATE urls
            SET completed = 'now()', error = %s, status_code = %s, status_message = %s
            WHERE url = %s
        """, ('http', e.code, reason, url))
    except httplib.BadStatusLine as e:
        sys.stderr.write('doing %s failed (bad status %s)\n' % (url, `e.line`))
        PG_CURSOR.execute("""
            UPDATE urls
            SET completed = 'now()', error = %s, status_code = -1, status_message = %s
            WHERE url = %s
        """, ('http', e.line, url))
    except:
        e = traceback.format_exc(1)

        if not 'Penalty box' in e:
            traceback.print_exc(1)
            RETRY_ERRORS[host] = e
        RETRY_COUNT[host] = RETRY_COUNT.get(host, 0) + 1

        PG_CURSOR.execute("""
            UPDATE urls
            SET completed = 'now()', error = %s, status_code = -2
            WHERE url = %s
        """, (e, url))

    PG_CNX.commit()

    time.sleep(SLEEP_TIME)

def try_again(retry_num):
    # num is greater than 0 and a power of two
    # http://code.activestate.com/recipes/577514-chek-if-a-number-is-a-power-of-two/
    return retry_num > 1 and ((retry_num & (retry_num - 1)) == 0)

def reencode(src_path, src_encoding, dest_path, dest_encoding):
    src_file = codecs.open(src_path, "r", src_encoding)
    dest_file = codecs.open(dest_path, "w", dest_encoding)
    shutil.copyfileobj(src_file, dest_file, BLOCKSIZE)
    src_file.close()
    dest_file.close()

if __name__ == '__main__':
    main()

#    while True:
#        do_one_url('http://nrhp.focus.nps.gov/natregadvancedsearch.do?searchType=natregadvanced&selectedCollections=NPS%20Digital%20Library&referenceNumber=9800147asdfa3&natregadvancedsearch=Search', 'z', 'foo')