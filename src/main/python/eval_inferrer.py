# According to Google (https://support.google.com/webmasters/answer/1347922?hl=en)
import sys
import logistic_inferrer
import urlinfo

from sg_utils import *

import nb_inferrer
import rule_inferrer
import baseline_inferrer


TEST_ALG = 'logistic'

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
            top_prob = dist[top[0]]
            if normalize_cc(top[0]) == normalize_cc(actual_cc):
                correct.append((url, actual_cc, top[:3], top_prob))
            else:
                wrong.append((url, actual_cc, top[:3], top_prob))
        else:
            (guess, rule) = feat.infer(ui)
            if not guess:
                num_missing += 1
                continue
            if normalize_cc(guess.iso) == normalize_cc(actual_cc):
                correct.append((url, actual_cc, guess, 0.9))
            else:
                wrong.append((url, actual_cc, guess, 0.5))

    overall_conf = sum([x[-1] for x in correct + wrong]) / len(correct + wrong)
    correct_conf = sum([x[-1] for x in correct]) / len(correct)
    if wrong:
        wrong_conf = sum([x[-1] for x in wrong]) / len(wrong)
    else:
        wrong_conf = 0.0

    print 'Feature %s had %d correct, %d wrong, %d missing, confs c=%.7f, w=%.7f, all=%.3f. Wrong are:' % \
          (feat.name, len(correct), len(wrong), num_missing, correct_conf, wrong_conf, overall_conf)
    for w in correct:
        print '\tcorrect: %s actual=%s pred=%s conf=%.3f' % w
    for w in wrong:
        print '\twrong: %s actual=%s pred=%s conf=%.3f' % w
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

    elif TEST_ALG == 'logistic':
        # test each individual feature
        inf = logistic_inferrer.LogisticInferrer(dao)
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


