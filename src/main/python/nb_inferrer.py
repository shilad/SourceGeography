# According to Google (https://support.google.com/webmasters/answer/1347922?hl=en)
GENERIC_TLDS = set('ad,as,bz,cc,cd,co,dj,fm,io,la,me,ms,nu,sc,sr,su,tv,tk,ws'.split(','))

class NaiveBayesInferrer:
    def __init__(self, dao):
        self.dao = dao
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

    def infer(self, url_info):
        result = {}

        for f in self.features:
            (conf, dist) = f.infer(url_info)
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


class WhoisFeature:
    def __init__(self, dao):
        self.dao = dao

    def infer(self, url_info):
        if not url_info.whois:
            return (0, {})
        return (0.85, { url_info.whois : 1.0 })


class WikidataFeature:
    def __init__(self, dao):
        self.dao = dao

    def infer(self, url_info):
        if not url_info.wikidata:
            return (0, {})
        return (0.90, { url_info.wikidata : 1.0 })


class LanguageFeature:
    def __init__(self, dao):
        self.dao = dao

    def infer(self, url_info):
        if not url_info.lang or not url_info.lang in self.dao.lang_countries:
            return (0, {})

        candidates = {}
        for (country, prob) in self.dao.lang_countries[url_info.lang]:
            candidates[country.iso] = prob

        return (0.80, candidates)

class TldFeature:
    def __init__(self, dao):
        self.dao = dao

    def infer(self, url_info):
        tld = url_info.tld
        if tld in ('mil', 'gov'):
            return (1.0, { 'us' : 1.0 })
        elif tld not in GENERIC_TLDS and tld in self.dao.tld_countries:
            iso = self.dao.tld_countries[tld].iso
            return (0.95, { iso : 1.0 })
        else:
            return (0, {})
