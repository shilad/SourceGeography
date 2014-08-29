"""
Requirements:
pip install --pre langid

pdfminer: http://euske.github.io/pdfminer/index.html
"""
import codecs
import langid
import os
import psycopg2
import psycopg2.extensions
import shutil
import sys
import tarfile
import urllib

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
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
        if self.contents_path.endswith('utf8'):
            return codecs.open(self.contents_path, 'r', encoding='utf-8').read(10*1024*1024)
        elif self.is_pdf():
            return pdf_to_text(self.contents_path)

    def is_pdf(self):
        if not self.contents_path.endswith('bin'):
            return False
        return self.url.lower().endswith('pdf') or 'pdf' in self.headers.get('content-type', '')

    def get_lang(self):
        text = self.get_text()
        if text:
            (lang, confidence) =  langid.classify(text)
            if confidence >= 0.9:
                return lang
        return None


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


def get_webpage(url):
    """
        Given a url, return a dictionary containing information about the webpage:
        {
            url : the requested url
            final-url : the url, after following any redirects
            http-code : the numeric http status code of the request (2xx means successfull)
            http-message : the textual http response
            error : any error messsage associated with request
            headers : dictionary containing http response headers
            contents: contents of the http response
            binary: whether the contents is binary (e.g. an image or pdf)
        }
        or None if there is no entry for the URL.
    """
    cur = CONN.cursor()
    tmp_path = None
    try:
        cur.execute('select * from urls where url = %s', url)
        if cur.rowcount == 0:
            return None
        row = cur.fetchone()
        urllib.urlretrieve(S3_PREFIX + row['archive'], 'tmp/tmp.tar.bz2')
        tmp_path = 'tmp/%s' + row['archive']
        os.makedirs(tmp_path)
        archive_path = tmp_path + '/archive.tar.bz'
        tar = tarfile.open(archive_path, "r:bz2")
        tar.extractall(archive_path)

    finally:
        cur.close()
        shutil.rmtree(tmp_path)


def pdf_to_text(data, max_length=10*1024*1024):
    try:
        fp = file(data, 'rb')
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        # Create a PDF interpreter object.
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        # Process each page contained in the document.

        for page in PDFPage.get_pages(fp):
            interpreter.process_page(page)
            data =  retstr.getvalue()
            if len(data) >= max_length:
                break

        return data
    except:
        warn('parsing of pdf %s failed' % data)
        return None

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
