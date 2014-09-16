from sg_utils import *

import urlinfo
import logistic_inferrer

def main():
    dao = urlinfo.UrlInfoDao()
    data = read_data(dao)

    folds = 7
    subsets = list([[] for i in range(folds)])
    for (i, d) in enumerate(data):
        subsets[i % folds].append(d)

    correct = 0
    total = 0
    missed_ps = []
    correct_ps = []
    for i in range(folds):
        test = subsets[i]
        train = sum(subsets[0:i] + subsets[i+1:], [])
        inf = logistic_inferrer.LogisticInferrer(dao)
        inf.train(train)
        for (ui, actual) in test:
            total += 1
            (conf, dist) = inf.infer_dist(ui)
            if not dist:
                warn('no prediction for %s' % (ui,))
                continue
            maxp = max(dist.values())
            bestc = [c for c in dist if dist[c] == maxp][0]
            if bestc == actual:
                correct_ps.append(maxp)
                correct += 1
            else:
                missed_ps.append(maxp)
                print 'missed', ui.url, '- guessed', bestc
    print correct, total, sum(correct_ps) / len(correct_ps), sum(missed_ps) / len(missed_ps)

    print 'final model:'
    inf = logistic_inferrer.LogisticInferrer(dao)
    inf.train(data)

def read_data(dao):
    names = {}
    for line in sg_open(PATH_COUNTRY_NAMES):
        (cc, name) = line.lower().strip().split(' ', 1)
        names[name.strip()] = cc.strip()

    data = []
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
        data.append((ui, names[name]))

    warn('retained %d urls' % len(data))

    return data

if __name__ == '__main__':
    main()

