# According to Google (https://support.google.com/webmasters/answer/1347922?hl=en)
GENERIC_TLDS = set('ad,as,bz,cc,cd,co,dj,fm,io,la,me,ms,nu,sc,sr,su,tv,tk,ws'.split(','))

class NaiveBayesInferrer:
    def __init__(self, dao):
        pass


class WhoisFeature:

class TldFeature:
    def __init__(self, dao):
        self.dao = dao

    def infer(self, url_info):
        tld = url_info.tld
        if tld in ('mil', 'gov'):
            return { 'us' : 1.0 }
        elif tld not in GENERIC_TLDS and tld in self.dao.tld_countries:
            return self.dao.tld_countries[tld].iso
        else:
            return None