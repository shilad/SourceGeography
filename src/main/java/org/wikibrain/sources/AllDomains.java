package org.wikibrain.sources;

import org.wikibrain.utils.WpIOUtils;

import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

/**
 * @author Shilad Sen
 */
public class AllDomains {
    public static void main(String args[]) throws IOException {
        File input = new File("./dat/source_urls.tsv");
        File output = new File("./dat/domains.txt");
        BufferedWriter writer = WpIOUtils.openWriter(output);

        Set<String> domains = new HashSet<String>();
        for (Citation cite : new ExtractReader(input)) {
            String d = cite.getEffectiveDomain2();
            if (d != null && !domains.contains(d)) {
                writer.write(d + "\n");
                domains.add(d);
            }
        }
        writer.close();

        System.out.println("wrote " + domains.size() + " domains");
    }
}
