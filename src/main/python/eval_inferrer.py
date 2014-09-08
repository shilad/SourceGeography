# According to Google (https://support.google.com/webmasters/answer/1347922?hl=en)
import sys
import urlinfo

from sg_utils import *

import nb_inferrer
import rule_inferrer
import baseline_inferrer


TEST_ALG = 'nb'

def read_test(dao, path):
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
        if hasattr(feat, 'infer_dist'):
            (conf, dist) = feat.infer_dist(ui)
            if not dist:
                num_missing += 1
                continue

            top = sorted(dist, key=dist.get, reverse=True)
            if normalize_cc(top[0]) == normalize_cc(actual_cc):
                correct.append((url, actual_cc, top[:3]))
            else:
                wrong.append((url, actual_cc, top[:3]))
        else:
            (guess, rule) = feat.infer(ui)
            if not guess:
                num_missing += 1
                continue
            if normalize_cc(guess.iso) == normalize_cc(actual_cc):
                correct.append((url, actual_cc, guess))
            else:
                wrong.append((url, actual_cc, guess))

    print 'Feature %s had %d correct, %d wrong, %d missing. Wrong are:' % \
          (feat.name, len(correct), len(wrong), num_missing)
    for w in correct:
        print '\tcorrect: %s actual=%s pred=%s' % w
    for w in wrong:
        print '\twrong: %s actual=%s pred=%s' % w
    print

if __name__ == '__main__':
    dao = urlinfo.UrlInfoDao()
    test = read_test(dao, PATH_2012)

    if TEST_ALG == 'nb':
        # test each individual feature
        inf = nb_inferrer.NaiveBayesInferrer(dao)
        for feat in inf.features:
            test_feature(feat, test)


        # test the feature on ourself
        test_feature(inf, test)
    elif TEST_ALG == 'rule':
        # test each individual feature
        inf = rule_inferrer.Inferrer(dao)
        test_feature(inf, test)
    elif TEST_ALG == 'baseline':
        inf = baseline_inferrer.BaselineInferrer(dao)
        test_feature(inf, test)
    else:
        raise Exception('unknown algorithm: ' + TEST_ALG)


