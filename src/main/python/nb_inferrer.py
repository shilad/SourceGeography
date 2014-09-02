# According to Google (https://support.google.com/webmasters/answer/1347922?hl=en)
import sys
import urlinfo

GENERIC_TLDS = set('ad,as,bz,cc,cd,co,dj,fm,io,la,me,ms,nu,sc,sr,su,tv,tk,ws'.split(','))

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
        for c in dao.get_countries():
            if c.prior:
                self.prior[c.iso] = c.prior
        if len(self.prior) == 0:
            raise Exception('no country priors!')

    def infer_dist(self, url_info):
        result = {}

        for f in self.features:
            (conf, dist) = f.infer_dist(url_info)
            if conf == 0:
                dist = dict(self.prior)
            else:
                union = set(self.prior.keys()).union(dist.keys())
                for c in union:
                    dist[c] = conf * dist.get(c, 0.0) + (1.0 - conf) * self.prior.get(c)

            if not result:
                result = dist
            else:
                for (c, prob) in dist.items():
                    result[c] *= prob

        if not result:
            return None

        total = sum(result.values())
        for (c, prob) in result.items():
            result[c] = result[c] / total

        return result

    def infer(self, url_info):
        result = self.infer_dist(url_info)
        if not result:
            return None

        top = sorted(result, key=result.get, reverse=True)
        sys.stderr.write('top for %s:' % url_info.url[:20])
        for c in top[:5]:
            sys.stderr.write(' %s=%.3f' % (c, result[c]))
        sys.stderr.write('\n')

        return (self.dao.iso_countries[top[0]], 'nb')


class WhoisFeature:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'whois'

    def infer_dist(self, url_info):
        if not url_info.whois:
            return (0, {})
        return (0.85, { url_info.whois : 1.0 })


class WikidataFeature:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'wikidata'

    def infer_dist(self, url_info):
        if not url_info.wikidata:
            return (0, {})
        return (0.90, { url_info.wikidata : 1.0 })


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

        return (0.80, candidates)

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
    for line in open('../../../dat/2012_test.tsv'):
        tokens = line.strip().split()
        url = tokens[0]
        cc = tokens[1]
        ui = dao.get_url(url)
        if ui:
            missing.append(ui)
        else:
            test[url] = (ui, cc.lower())

    print 'missing urls: (%d of %d)' % (len(missing), len(missing) + len(test))
    for url in missing:
        print '\t%s' % (url,)
    print

    return test

def test_feature(feat, test):
    num_missing = 0
    num_correct = 0

    wrong = []

    for url in test:
        (ui, actual_cc) = test[url]
        (conf, dist) = feat.infer_dist(ui)
        if not dist:
            num_missing += 1
            continue

        top = sorted(dist, key=dist.get, reverse=True)
        if top[0] == actual_cc:
            num_correct += 1
        else:
            wrong.append((url, actual_cc, top[:3]))

    print 'Feature %s had %d correct, %d wrong, %d missing. Wrong are:' % \
          (feat.name, num_correct, len(wrong), num_missing)
    for w in wrong:
        print '\t%s actual=%s pred=%s' % w
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


