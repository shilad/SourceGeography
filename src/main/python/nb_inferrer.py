import sys
import urlinfo

from sg_utils import *

DEBUG = False

# According to Google (https://support.google.com/webmasters/answer/1347922?hl=en)
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

        best = top[0]
        r = 1 + int(result[best] * 8)    # a number between 1 and 9

        if best not in self.dao.iso_countries:
            warn('unknown country: %s' % best)
            return (None, 'nb-0')

        return (self.dao.iso_countries[best], 'nb-' + str(r))


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
