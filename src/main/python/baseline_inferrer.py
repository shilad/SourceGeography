GENERIC_TLDS = set('ad,as,bz,cc,cd,co,dj,fm,io,la,me,ms,nu,sc,sr,su,tv,tk,ws,int'.split(','))

class BaselineInferrer:
    def __init__(self, dao):
        self.dao = dao
        self.name = 'baseline'

    def infer(self, url_info):
        tld = url_info.tld
        us = self.dao.tld_countries['us']
        if tld in ('mil', 'gov'):
            return (us, 'mil')
        elif tld not in GENERIC_TLDS and tld in self.dao.tld_countries:
            c = self.dao.tld_countries[tld]
            return (c, 'iso')
        else:
            return (us, 'guess')
