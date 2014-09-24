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

    names = {}
    for line in sg_open(PATH_COUNTRY_NAMES):
        (cc, name) = line.lower().strip().split(' ', 1)
        names[name.strip()] = cc.strip()

    data = {}
    for line in sg_open(PATH_CODED_URL_COUNTRIES):
        tokens = line.strip().split('\t', 1)
        if len(tokens) != 2:
            continue
        (url, name) = tokens
        name = name.lower()
        if name not in names:
            warn('unknown name: %s' % (`name`, ))
            continue
        ui = dao.get_url(url)
        if not ui:
            warn('unknown url: %s' % (`url`, ))
            continue
        data[url] = (ui, names[name].lower())

    warn('retained %d urls' % len(data))

    return data

def normalize_cc(cc):
    cc = cc.lower()
    if cc == 'uk': cc = 'gb'
    return cc

def is_hard(dao, ui):
    if ui.tld in ('mil', 'gov'):
        return False
    elif ui.tld not in GENERIC_TLDS and ui.tld in dao.tld_countries:
        return False
    else:
        return True

def test_feature(feat, test):
    num_missing = 0

    hard_correct = []
    hard_wrong = []
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
            k = (url, actual_cc, top[:3], top_prob)
            if normalize_cc(top[0]) == normalize_cc(actual_cc):
                correct.append(k)
                if is_hard(dao, ui): hard_correct.append(k)
            else:
                wrong.append(k)
                if is_hard(dao, ui): hard_wrong.append(k)
        else:
            (guess, rule) = feat.infer(ui)
            if not guess:
                num_missing += 1
                continue
            if normalize_cc(guess.iso) == normalize_cc(actual_cc):
                k = (url, actual_cc, guess, 0.9)
                correct.append(k)
                if is_hard(dao, ui): hard_correct.append(k)
            else:
                k = (url, actual_cc, guess, 0.5)
                wrong.append(k)
                if is_hard(dao, ui): hard_wrong.append(k)

    overall_conf = sum([x[-1] for x in correct + wrong]) / len(correct + wrong)
    correct_conf = sum([x[-1] for x in correct]) / len(correct)
    if wrong:
        wrong_conf = sum([x[-1] for x in wrong]) / len(wrong)
    else:
        wrong_conf = 0.0

    total = len(test)
    print 'Feature %s had %d correct, %d wrong (%.1f%%), %d missing, coverage=%.1f%% confs c=%.7f, w=%.7f, all=%.3f. Wrong are:' % \
          (feat.name, len(correct), len(wrong), 100.0 * len(correct) / len(correct + wrong),
           num_missing, 100.0 * (total - num_missing) / total, correct_conf, wrong_conf, overall_conf)
    if hard_correct or hard_wrong:
        print 'Hard domains: %d correct, %d wrong (%.1f%%)' % (len(hard_correct), len(hard_wrong), 100.0 * len(hard_correct) / len(hard_wrong + hard_correct))
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


