"""
Requirements:

    install pdftotext (on Mac, brew install xpdf)
    install antiword (on Mac, brew install antiword)


And three python modules (if you don't have sudo, use "pip install --user")

    pip install xlrd
    pip install beautifulsoup4
    pip install psycopg2

TODO: handle google books other isbns
"""
import codecs
import subprocess
import tempfile
import traceback
import types
import os
import psycopg2
import psycopg2.extensions
import shutil
import sys
import tarfile
import xlrd
from bs4 import BeautifulSoup

from cStringIO import StringIO


from multiprocessing import Lock, Pool



S3_PREFIX = 'http://s3.amazonaws.com/sourcegeography/scrape/'
CONN = None


class WebResource:
    def __init__(self, meta_path, contents_path):
        self.headers = {}
        f = codecs.open(meta_path, 'r', encoding='utf-8')
        self.url = f.readline().strip()
        for line in f:
            tokens = line.strip().lower().split(':', 1)
            if len(tokens) == 2:
                self.headers[tokens[0]] = tokens[1]
            else:
                warn('invalid header in %s: %s' % (meta_path, `line`))
        self.contents_path = contents_path

    def __repr__(self):
        return self.url

    def __str__(self):
        return self.url

    def get_text(self):
        if not os.path.isfile(self.contents_path):
            return None

        content_type = self.get_content_type()
        try:
            if 'html' in content_type:
                return html_to_text(self.open_contents())
            elif 'pdf' in content_type:
                return pdf_to_text(self.contents_path)
            elif 'xml' in content_type:
                return xml_to_text(self.open_contents())
            elif 'msword' in content_type:
                return word_to_text(self.contents_path)
            elif 'excel' in content_type:
                return xls_to_text(self.contents_path)
            elif 'text/plain' in content_type:
                return text_to_text(self.open_contents())
            elif self.is_binary():
                return None
            else:
                return text_to_text(self.open_contents())
        except:
            warn('getting text for %s with content-type %s failed' % (self.url, content_type))
            traceback.print_exc()

    def is_binary(self):
        return self.contents_path.endswith('bin')

    def get_content_type(self):
        return self.headers.get('content-type', '').split(';')[0].strip()

    def open_contents(self):
        if not os.path.isfile(self.contents_path):
            return None
        if self.contents_path.endswith('.bin'):
            return open(self.contents_path, 'rb')
        elif self.contents_path.endswith('.utf8'):
            return codecs.open(self.contents_path, 'r', encoding='utf-8')
        else:
            raise AssertionError()


def worker(archive, process_callback, result_callback):
    results = []
    for resource in archive_generator(archive):
        try:
            results.append((result_callback, process_callback(resource)))
        except:
            warn('worker failed:')
            traceback.print_exc()
    return results

def worker_result(results):
    for (cb, r) in results:
        cb(r)

def process_resources(base_dir, process_callback, result_callback):
    """
    :param base_dir:
    :param resource_callback:
    :param result_callback:
    :return:
    """

    pool = Pool()
    archives = list(archive_dirs(base_dir))
    for a in archives:
        r = pool.apply_async(worker, (a, process_callback, result_callback), callback=worker_result)
    pool.close()
    pool.join()

def warn(message):
    sys.stderr.write(message + '\n')


def archive_dirs(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            p = root + '/' + f
            if f.endswith('.tar.bz2'):
                yield p

def archive_generator(path):
        tmp_path = 'tmp/' + os.path.basename(path)
        if not os.path.isdir(tmp_path): os.makedirs(tmp_path)
        tar = tarfile.open(path, "r:bz2")
        print('extracting', path)
        tar.extractall(tmp_path)
        try:
            for root2, dirs2, files2 in os.walk(tmp_path):
                for f2 in files2:
                    p2 = root2 + '/' + f2
                    if f2.endswith('.meta'):
                        for cp in (p2[:-4] + 'utf8', p2[:-4] + 'bin'):
                            if os.path.isfile(cp):
                                yield WebResource(p2, cp)
                                break
                        else:
                            warn('unknown file: ' + p2)
        finally:
            shutil.rmtree(tmp_path, True)

def pdf_to_text(pdf_path):
    fd, txt_path = tempfile.mkstemp()
    os.close(fd)
    os.unlink(txt_path)
    r = subprocess.call(['pdftotext', '-enc', 'UTF-8', '-q', '-f', '0', '-l', '50', pdf_path, txt_path])
    if not os.path.isfile(txt_path) or os.path.getsize(txt_path) == 0:
        return None
    f = codecs.open(txt_path, 'r', encoding='utf-8')
    s = f.read()
    f.close()
    return s

def word_to_text(doc_path):
    return subprocess.check_output(['antiword', doc_path])

def xls_to_text(doc_path):
    buffer = StringIO()
    wb = xlrd.open_workbook(doc_path)
    for i in xrange(wb.nsheets):
        sh = wb.sheet_by_index(i)
        for r in xrange(sh.nrows):
            for v in sh.row_values(r):
                if type(v) is types.StringType:
                    buffer.write(v)
                    buffer.write(' ')
                elif type(v) is types.UnicodeType:
                    buffer.write(v.encode('utf-8'))
                    buffer.write(' ')
            buffer.write('\n')

    s = buffer.getvalue()
    buffer.close()
    return s

def html_to_text(f):
    html = f.read()
    f.close()
    soup = BeautifulSoup(html.encode('utf-8'))
    return  soup.get_text(' ')

def text_to_text(f):
    txt = f.read()
    f.close()
    return txt

def xml_to_text(f):
    xml = f.read()
    f.close()
    soup = BeautifulSoup(xml.encode('utf-8'), 'xml')
    return  soup.get_text(' ')

def init(host='localhost', user='shilad', password=None, db='whois'):
    global CONN

    CONN = psycopg2.connect(host=host, user=user, password=password, database=db)
    CONN.set_client_encoding('UTF-8')
    if not os.path.isdir('tmp'):
        os.mkdir('tmp')

def process_archive(f):
    results = []
    for resource in archive_generator(f):
        lang = resource.get_lang()
        if not lang: lang = 'unknown'
        results.append((resource.url, lang))
    return results


if __name__ == '__main__':
    lock = Lock()
    pool = Pool()
    f = codecs.open('url_langs.tsv', 'w', encoding='utf-8')
    archives = list(archive_dirs('/Users/shilad/Documents/IntelliJ/SourceGeography/scrape/'))
    def handler(results):
        lock.acquire()
        try:
            for (url, lang) in results:
                f.write('%s\t%s\n' % (url, lang))
        finally:
            lock.release()

    for a in archives:
        r = pool.apply_async(process_archive, (a,), callback=handler)
    pool.close()
    pool.join()
    f.close()
