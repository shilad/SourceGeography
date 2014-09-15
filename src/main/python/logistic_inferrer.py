import collections
import math

from sg_utils import *

DEBUG = False

# According to Google (https://support.google.com/webmasters/answer/1347922?hl=en)
GENERIC_TLDS = set('ad,as,bz,cc,cd,co,dj,fm,io,la,me,ms,nu,sc,sr,su,tv,tk,ws,int'.split(','))

def logit(p):
    return math.log(p) - math.log(1 - p)

def prob2sigmoid(p, conf):
    conf = conf - 0.0001 # avoid infinities
    return logit(p * conf + (1.0 - conf) / 2)

def logistic(x):
    return 1.0 / (1 + math.exp(-x))

class LogisticInferrer:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'logistic'
        self.features = [
            ParsedWhoisFeature(dao),
            NamedWhoisFeature(dao),
            MilGovFeature(dao),
            WikidataFeature(dao),
            LanguageFeature(dao),
            TldFeature(dao)
        ]

        self.prior = {}
        for (c, dist) in dao.country_priors.items():
            self.prior[c.iso] = dist

        if len(self.prior) == 0:
            raise Exception('no country priors!')

    def infer_dist(self, url_info):
        result = {}

        for (c, p) in self.prior.items():
            result[c] = prob2sigmoid(p, 0.1)
        result['uk'] = result['br']

        for f in self.features:
            (conf, dist) = f.infer_dist(url_info)
            if conf == 0 or not dist:
                continue

            for (c, p) in dist.items():
                result[c] += prob2sigmoid(p, conf)

        if not result:
            return (0.0, {})

        for (c, prob) in result.items():
            result[c] = logistic(prob)
        print 'hgihest is', max(result.values()), sum(result.values())
        total = sum(result.values())
        for (c, prob) in result.items():
            result[c] = result[c] / total

        return (1.0, result)

    def infer(self, url_info):
        _, result = self.infer_dist(url_info)
        if not result:
            return (None, 'nb-0')

        top = sorted(result, key=result.get, reverse=True)
        if DEBUG:
            sys.stderr.write('top for %s:' % url_info.url[:20])
            for c in top[:5]:
                sys.stderr.write(' %s=%.3f' % (c, result[c]))
            sys.stderr.write('\n')

        best = top[0]
        r = 1 + int(result[best] * 8)    # a number between 1 and 9

        if best not in self.dao.iso_countries:
            warn('unknown country: %s' % best)
            return (None, 'nb-0')

        return (self.dao.iso_countries[best], 'nb-' + str(r))


class ParsedWhoisFeature:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'pwhois'

    def infer_dist(self, url_info):
        if not url_info.whois:
            return (0, {})

        pairs = [token.split('|') for token in url_info.whois.split(',')]
        for (country, n) in pairs:
            if n == 'p':    # a structure, parsed entry
                return (0.95, { country : 1.0 })

        return (0, {})


class NamedWhoisFeature:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'nwhois'

    def infer_dist(self, url_info):
        if not url_info.whois:
            return (0, {})

        pairs = [token.split('|') for token in url_info.whois.split(',')]
        dist = {}
        for (country, n) in pairs:
            if n != 'p':    # a structure, parsed entry
                dist[country] = int(n)

        if not dist:
            return (0, {})

        total = sum(dist.values())
        for (lang, n) in dist.items():
            dist[lang] = 1.0 * n / total
        return (0.60, dist)


class WikidataFeature:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'wikidata'

    def infer_dist(self, url_info):
        if not url_info.wikidata:
            return (0, {})
        return (0.99, { url_info.wikidata : 1.0 })


class LanguageFeature:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'language'

    def infer_dist(self, url_info):
        if not url_info.lang or not url_info.lang in self.dao.lang_countries:
            return (0, {})

        candidates = {}
        for (country, prob) in self.dao.lang_countries[url_info.lang]:
            candidates[country.iso] = prob

        return (0.70, candidates)

class MilGovFeature:
    def __init__(self, dao):
        self.name = 'mil'

    def infer_dist(self, url_info):
        if url_info.tld in ('mil', 'gov'):
            return (1.0, { 'us' : 1.0 })
        else:
            return (0, {})

class TldFeature:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'tld'

    def infer_dist(self, url_info):
        tld = url_info.tld
        if tld not in GENERIC_TLDS and tld in self.dao.tld_countries:
            iso = self.dao.tld_countries[tld].iso
            return (0.95, { iso : 1.0 })
        else:
            return (0, {})



if __name__ == '__main__':

    import urlinfo
    import random

    dao = urlinfo.UrlInfoDao()
    tld = TldFeature(dao)
    inf = LogisticInferrer(dao)
    feats = [f for f in inf.features if f.name != 'tld']
    tests = 0

    feat_counts = {}
    feat_correct = {}
    feat_guesses = {}
    for f in feats:
        feat_correct[f] = 0
        feat_counts[f] = 0
        feat_guesses[f] = {}
        for i in range(11):
            feat_guesses[f][i / 10.0] = []
        feat_guesses[f][-1] = []

    for (i, url) in enumerate(sg_open(PATH_URL_INTERESTING)):
        url = url.strip()
        if i % 1000000 == 0:
            print 'doing', i, tests
        if random.random() < 0.005:
            ui  = dao.get_url(url)
            if not ui:
                continue
            guesses = tld.infer_dist(ui)[1]
            if not guesses:
                continue
            tests += 1
            actual = list(guesses.keys())[0]

            for f in feats:
                (conf, d) = f.infer_dist(ui)
                if not d:
                    continue
                feat_counts[f] += 1
                for (c, p) in d.items():
                    bin = int(p * 10) / 10.0
                    feat_guesses[f][bin].append((url, actual, c))
                    if actual == c and p == max(d.values()):    # if its highest
                        feat_correct[f] += 1
                if actual not in d:
                    feat_guesses[f][-1].append((url, actual, ''))


    for f in feats:
        print 'results for', f.name
        n = feat_counts[f] + 1
        print '\tnum-guesses: %d of %d (%.1f%%)' % (n, tests, 100.0 * n / tests)
        print '\tnum-correct: %d of %d (%.1f%%)' % (feat_correct[f], n, 100.0 * feat_correct[f] / n)
        for k in sorted(feat_guesses[f]):
            g = feat_guesses[f][k]
            misses = [
                        (url, actual, guess)
                        for (url, actual, guess) in g
                        if actual != guess
                    ]
            nhits = len(g) - len(misses)
            p = 0 if not g else 100.0 * nhits / len(g)
            print '\tbin %.1f: %d of %d (%.1f%%)' % (k, nhits, len(g), p)






