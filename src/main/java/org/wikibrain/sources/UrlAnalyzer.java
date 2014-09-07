package org.wikibrain.sources;

import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.http.client.utils.URIBuilder;
import org.wikibrain.utils.WpIOUtils;

import java.io.*;
import java.net.MalformedURLException;
import java.net.URISyntaxException;
import java.net.URL;
import java.net.URLDecoder;
import java.util.*;

/**
 * @author Shilad Sen
 */
public class UrlAnalyzer {
    static final class ParsedUrl {
        String url;
        String host;
        String path;
        String fragment;
        String sortedQuery;

        public ParsedUrl(String surl) throws MalformedURLException, UnsupportedEncodingException, URISyntaxException {
            URIBuilder b = new URIBuilder(surl).setScheme("http");
            URL u = b.build().toURL();
            url = u.toExternalForm();
            host = b.getHost();
            path = b.getPath();
            fragment = b.getFragment();
            Map<String, List<String>> parsed = splitQuery(u);
            List<String> keys = new ArrayList<String>(parsed.keySet());
            sortedQuery = "?";
            Collections.sort(keys);
            for (String key : keys) {
                Collections.sort(parsed.get(key));
                sortedQuery += "&" + key + "="  + StringUtils.join(parsed.get(key), ",");
            }
        }

        public double similarity(ParsedUrl that) {
            if (ObjectUtils.equals(this.url, that.url)) {
                return 0;
            }
            if (!ObjectUtils.equals(this.host, that.host)) {
                return 1000000;
            }
            String p1 = getFullPath();
            String p2 = that.getFullPath();
            return 1.0 * lcs(p1, p2) / (1.0 + Math.max(p1.length(), p2.length()));
        }

        public String getFullPath() {
            return (path == null ? "" : path) + sortedQuery + (fragment == null ? "#" : fragment);
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;

            ParsedUrl parsedUrl = (ParsedUrl) o;

            if (!url.equals(parsedUrl.url)) return false;

            return true;
        }

        @Override
        public int hashCode() {
            return url.hashCode();
        }
    }

    public void analyze(List<String> urls) throws IOException {
        Map<String, List<ParsedUrl>> parsed = new HashMap<String, List<ParsedUrl>>();
        int i = 0;
        for (String s : urls) {
            try {
                ParsedUrl pu = new ParsedUrl(s);
                if (!parsed.containsKey(pu.host)) {
                    parsed.put(pu.host, new ArrayList<ParsedUrl>());
                }
                parsed.get(pu.host).add(pu);
                i++;
            } catch (Exception e) {
            }
        }

        System.err.format("%d of %d urls were valid\n", i, urls.size());
        BufferedWriter writer = WpIOUtils.openWriter(new File("dat/common_url_patterns.txt"));
        while (true) {
            ParsedUrl best = null;
            Set<ParsedUrl> bestNeighbors = null;

            for (String host : parsed.keySet()) {
                List<ParsedUrl> hostUrls = parsed.get(host);
                if (bestNeighbors != null && hostUrls.size() < bestNeighbors.size()) {
                    continue;
                }
                for (ParsedUrl url1 : hostUrls) {
                    Set<ParsedUrl> neighbors = new HashSet<ParsedUrl>();
                    for (ParsedUrl url2 : hostUrls) {
                        if (url1.similarity(url2) >= 0.25) {
                            neighbors.add(url2);
                        }
                    }
                    if (best == null || bestNeighbors.size() < neighbors.size()) {
                        best = url1;
                        bestNeighbors = neighbors;
                    }
                }
            }

            tee(writer, "\nBest url was %s with %d neighbors:", best.url, bestNeighbors.size());
            i = 0;
            for (ParsedUrl u : bestNeighbors) {
                tee(writer, "\t%s", u.url);
                if (i ++ > 10) {
                    break;
                }
            }
            if (bestNeighbors.size() < 3) {
                break;
            }

            parsed.get(best.host).removeAll(bestNeighbors);
        }
    }

    static void tee(BufferedWriter writer, String format, Object ... args) throws IOException {
        String message = String.format(format, args);
        System.err.println(message);
        writer.write(message + "\n");
    }

    /**
     * From http://stackoverflow.com/questions/13592236/parse-the-uri-string-into-name-value-collection-in-java
     * @param url
     * @return
     * @throws UnsupportedEncodingException
     */
    public static Map<String, List<String>> splitQuery(URL url) throws UnsupportedEncodingException {
        final Map<String, List<String>> query_pairs = new LinkedHashMap<String, List<String>>();
        if (url.getQuery() == null || url.getQuery().isEmpty()) {
            return query_pairs;
        }
        final String[] pairs = url.getQuery().split("&");
        for (String pair : pairs) {
            final int idx = pair.indexOf("=");
            final String key = idx > 0 ? URLDecoder.decode(pair.substring(0, idx), "UTF-8") : pair;
            if (!query_pairs.containsKey(key)) {
                query_pairs.put(key, new LinkedList<String>());
            }
            final String value = idx > 0 && pair.length() > idx + 1 ? URLDecoder.decode(pair.substring(idx + 1), "UTF-8") : null;
            query_pairs.get(key).add(value);
        }
        return query_pairs;
    }

    public static int lcs(String x, String y) {
        int M = x.length();
        int N = y.length();

        // opt[i][j] = length of LCS of x[i..M] and y[j..N]
        int[][] opt = new int[M+1][N+1];

        // compute length of LCS and all subproblems via dynamic programming
        for (int i = M-1; i >= 0; i--) {
            for (int j = N-1; j >= 0; j--) {
                if (x.charAt(i) == y.charAt(j))
                    opt[i][j] = opt[i+1][j+1] + 1;
                else
                    opt[i][j] = Math.max(opt[i+1][j], opt[i][j+1]);
            }
        }
        return opt[0][0];
    }

    public static void main(String args[]) throws IOException {
        StreamSampler<String> sampler = new StreamSampler<String>(5000);
        BufferedReader reader = WpIOUtils.openBufferedReader(new File("dat/source_urls.tsv"));
        int i = 0;
        while (true) {
            if (++i % 1000000 == 0) {
                System.err.println("analyzing citation " + i);
                break;
            }
            String line = reader.readLine();
            if (line == null) {
                break;
            }
            String tokens[] = line.split("\t");
            if (tokens.length >= 13) {
                sampler.offer(tokens[12].trim());
            }
        }
        reader.close();
        UrlAnalyzer analyzer = new UrlAnalyzer();
        analyzer.analyze(sampler.getSample());
    }
}
