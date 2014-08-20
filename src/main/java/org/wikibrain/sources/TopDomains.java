package org.wikibrain.sources;

import gnu.trove.map.TIntIntMap;
import gnu.trove.map.hash.TIntIntHashMap;
import org.wikibrain.utils.WpCollectionUtils;

import java.io.File;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * @author Shilad Sen
 */
public class TopDomains {
    private final File file;

    private int totalCount;
    private TIntIntMap citationsPerArticle;
    private Map<String, Double> domainCounts;
    private List<String> topDomains;

    public TopDomains(File file) {
        this.file = file;
        prepare();
    }

    public void prepare() {
        citationsPerArticle = new TIntIntHashMap();
        for (Citation citation : new ExtractReader(file)) {
            citationsPerArticle.adjustOrPutValue(citation.getArticle().getLocalId(), 1, 1);
            totalCount++;
        }

        domainCounts = new HashMap<String, Double>();
        for (Citation citation : new ExtractReader(file)) {
            String d = citation.getEffectiveDomain();
            if (d == null) {
                continue;
            }
            int n = citationsPerArticle.get(citation.getArticle().getLocalId());
            if (domainCounts.containsKey(d)) {
                domainCounts.put(d, domainCounts.get(d) + 1.0 / n);
            } else {
                domainCounts.put(d, 1.0 / n);
            }
        }

        topDomains = WpCollectionUtils.sortMapKeys(domainCounts, true);
        topDomains = topDomains.subList(0, 1000);
    }

    public void printTopDomains() {
        System.out.println("Most cited domains:");
        for (int i = 0; i < 100; i++) {
            String domain = topDomains.get(i);
            System.out.println(
                    String.format("%d. %s (%.2f%%)", (i+1), domain,
                            100.0 * domainCounts.get(domain) / citationsPerArticle.size()
                    ));
        }
    }

    public static void main(String args[]) {
        TopDomains td = new TopDomains(new File("./source_urls.tsv"));
        td.printTopDomains();
    }
}
