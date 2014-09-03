# According to Google (https://support.google.com/webmasters/answer/1347922?hl=en)
import sys
import urlinfo

DEBUG = False
GENERIC_TLDS = set('ad,as,bz,cc,cd,co,dj,fm,io,la,me,ms,nu,sc,sr,su,tv,tk,ws,int'.split(','))

class NaiveBayesInferrer:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'naive bayes'
        self.features = [
            WhoisFeature(dao),
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

        for f in self.features:
            (conf, dist) = f.infer_dist(url_info)
            if conf == 0 or not dist:
                continue

            union = set(self.prior.keys()).union(dist.keys())
            for c in union:
                dist[c] = (conf * dist.get(c, 0.0) + (1.0 - conf) * self.prior.get(c, 0.0)) ** conf

            total = sum(dist.values()) + 0.00001
            for c in dist:
                dist[c] /= total

            if DEBUG:
                top = sorted(dist, key=dist.get, reverse=True)
                sys.stderr.write('%s\'s top for %s:' % (f.name, url_info.url[:20]))
                for c in top[:5]:
                    sys.stderr.write(' %s=%.5f' % (c, dist[c]))
                sys.stderr.write('\n')

            if not result:
                result.update(dist)
            else:
                for (c, prob) in dist.items():
                    result[c] = result.get(c, 0.000001) * prob

        if not result:
            return (0.0, {})

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

        r = 1 + int(result[top[0]] * 9)    # a number between 1 and 9

        return (self.dao.iso_countries[top[0]], 'nb-' + str(r))


class WhoisFeature:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'whois'

    def infer_dist(self, url_info):
        if not url_info.whois:
            return (0, {})
        return (0.90, { url_info.whois : 1.0 })


class WikidataFeature:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'wikidata'

    def infer_dist(self, url_info):
        if not url_info.wikidata:
            return (0, {})
        return (0.92, { url_info.wikidata : 1.0 })


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

        return (0.40, candidates)

class TldFeature:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'tld'

    def infer_dist(self, url_info):
        tld = url_info.tld
        if tld in ('mil', 'gov'):
            return (1.0, { 'us' : 1.0 })
        elif tld not in GENERIC_TLDS and tld in self.dao.tld_countries:
            iso = self.dao.tld_countries[tld].iso
            return (0.95, { iso : 1.0 })
        else:
            return (0, {})


def read_test(dao):
    test = {}
    missing = []
    #for line in ['http://rsssf.com/tablesi/ital-intres1970.html nl']:
    for line in open('../../../dat/2012_test.tsv'):
        tokens = line.strip().split()
        url = tokens[0]
        cc = tokens[1]
        ui = dao.get_url(url)
        if not ui:
            missing.append(url)
        else:
            test[url] = (ui, cc.lower())

    print 'missing urls: (%d of %d)' % (len(missing), len(missing) + len(test))
    #for url in missing:
    #    print '\t%s' % (url,)
    print

    return test

def normalize_cc(cc):
    cc = cc.lower()
    if cc == 'uk': cc = 'gb'
    return cc

def test_feature(feat, test):
    num_missing = 0

    correct = []
    wrong = []

    for url in test:
        (ui, actual_cc) = test[url]
        (conf, dist) = feat.infer_dist(ui)
        if not dist:
            num_missing += 1
            continue

        top = sorted(dist, key=dist.get, reverse=True)
        if normalize_cc(top[0]) == normalize_cc(actual_cc):
            correct.append((url, actual_cc, top[:3]))
        else:
            wrong.append((url, actual_cc, top[:3]))

    print 'Feature %s had %d correct, %d wrong, %d missing. Wrong are:' % \
          (feat.name, len(correct), len(wrong), num_missing)
    for w in correct:
        print '\tcorrect: %s actual=%s pred=%s' % w
    for w in wrong:
        print '\twrong: %s actual=%s pred=%s' % w
    print

if __name__ == '__main__':
    dao = urlinfo.UrlInfoDao()
    test = read_test(dao)

    # test each individual feature
    inf = NaiveBayesInferrer(dao)
    for feat in inf.features:
        test_feature(feat, test)


    # test the feature on ourself
    test_feature(inf, test)


