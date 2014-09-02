package org.wikibrain.sources;

import gnu.trove.set.TLongSet;
import gnu.trove.set.hash.TLongHashSet;
import org.wikibrain.core.nlp.MurmurHash;
import org.wikibrain.utils.WpIOUtils;

import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 *
 * @author Shilad Sen
 */
public class AllUrls {

    static List<String> IGNORED_DOMAINS = Arrays.asList(
            "wikimedia.org",
            "wikipedia.org",
            "toolserver.org",
            "wmflabs.org"
    );


    static class URLSet {
        private TLongSet set = new TLongHashSet(10000000);
        boolean contains(URL url) { return set.contains(hash(url)); }
        void add(URL url) { set.add(hash(url)); }
        long hash(URL url) { return MurmurHash.hash64(url.toExternalForm()); }
        public int size() { return set.size(); }
    }

    public static void main(String args[]) throws IOException {
        URLSet urls = new URLSet();

        File input = new File("./dat/source_urls.tsv");
        File output = new File("dat/all_urls.txt");
        BufferedWriter writer = WpIOUtils.openWriter(output);

        for (Citation cite : new ExtractReader(input)) {
            URL url = cite.getUrl2();
            if (url != null && !cite.isInternal() && !urls.contains(url)) {
                writer.write(url.toExternalForm() + "\n");
                urls.add(url);
            }
        }
        writer.close();

        System.out.println("wrote " + urls.size() + " urls");
    }
}
