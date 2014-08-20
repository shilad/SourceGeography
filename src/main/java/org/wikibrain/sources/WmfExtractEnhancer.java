package org.wikibrain.sources;

import com.google.common.net.InternetDomainName;
import com.vividsolutions.jts.geom.*;
import com.vividsolutions.jts.geom.impl.CoordinateArraySequence;
import com.vividsolutions.jts.index.SpatialIndex;
import com.vividsolutions.jts.index.strtree.STRtree;
import org.apache.commons.io.LineIterator;
import org.apache.commons.lang.StringUtils;
import org.apache.http.NameValuePair;
import org.apache.http.client.utils.URLEncodedUtils;
import org.wikibrain.conf.ConfigurationException;
import org.wikibrain.core.cmd.Env;
import org.wikibrain.core.cmd.EnvBuilder;
import org.wikibrain.core.dao.DaoException;
import org.wikibrain.core.dao.LocalPageDao;
import org.wikibrain.core.dao.UniversalPageDao;
import org.wikibrain.core.lang.Language;
import org.wikibrain.core.model.LocalPage;
import org.wikibrain.spatial.core.dao.SpatialDataDao;
import org.wikibrain.utils.ParallelForEach;
import org.wikibrain.utils.Procedure;
import org.wikibrain.utils.WpIOUtils;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Logger;

/**
 * @author Shilad Sen
 */
public class WmfExtractEnhancer {
    //Buffer to consider - in degrees - roughly 500m to 1km depending on exact lat / lng
    private static final double BUFFER_DEGREES = 0.01;

    private static final Logger LOG = Logger.getLogger(SourceExtractor.class.getName());

    private final Language language;
    private final LocalPageDao pageDao;
    private final SpatialDataDao spatialDao;
    private final UniversalPageDao conceptDao;

    private Map<LocalPage, Geometry> countries = new HashMap<LocalPage, Geometry>();

    public WmfExtractEnhancer(Env env, Language language) throws ConfigurationException, DaoException {
        this.language = language;
        this.pageDao = env.getConfigurator().get(LocalPageDao.class);
        this.spatialDao = env.getConfigurator().get(SpatialDataDao.class);
        this.conceptDao = env.getConfigurator().get(UniversalPageDao.class);

        Map<Integer, Geometry> idsToCountries = spatialDao.getAllGeometriesInLayer("country");
        for (int conceptId : idsToCountries.keySet()) {
            LocalPage country = getLocalPage(conceptId);
            if (country != null) {
                countries.put(country, idsToCountries.get(conceptId));
            }
        }
        System.out.println("resolved " + countries.size() + " countries");
    }

    private void createCsv(File inputPath, File outputPath, File invalidUrlPath) throws IOException {
        BufferedReader reader = WpIOUtils.openBufferedReader(inputPath);
        final BufferedWriter writer = WpIOUtils.openWriter(outputPath);
        final BufferedWriter invalidUrlWriter = WpIOUtils.openWriter(invalidUrlPath);

        final AtomicInteger numLines = new AtomicInteger();
        final AtomicInteger numBadCountries = new AtomicInteger();
        final AtomicInteger numBadUrls = new AtomicInteger();

        // Copy header
        writer.write(reader.readLine() +
                "\turl2" +
                "\tdomain2" +
                "\teffectiveDomain2" +
                "\n");

        LineIterator iter = new LineIterator(reader);
        ParallelForEach.iterate(iter, new Procedure<String>() {
            @Override
            public void call(String input) throws Exception {
                try {
                    String output = translate(input);
                    if (output == null) {
                        numBadCountries.incrementAndGet();
                    } else {
                        writer.write(output + "\n");
                    }
                } catch (InvalidUrlException e) {
                    invalidUrlWriter.write(e.getUrl() + "\n");
                    numBadUrls.incrementAndGet();
                }
                if (numLines.incrementAndGet() % 1000 == 0) {
                    System.err.println("Doing line " + numLines.get() +
                            ". Found " + numBadCountries.get() + " bad countries and  " + numBadUrls.get() + " invalid urls.");
                }
            }
        });

    }


    /**
     * Tokens are, in order:

         "language",
         "articleId",
         "articleTitle",
         "articleLat",
         "articleLong",
         "countryId",
         "countryTitle",
         "countryLat",
         "countryLong",
         "url",
         "domain",
         "effectiveDomain",
         "url2",
         "domain2",
         "effectiveDomain2"

     * @param input
     * @return
     * @throws InvalidUrlException
     */
    private String translate(String input) throws InvalidUrlException {
        String tokens[] = input.split("\t");
        String output[] = new String[15];

        // Initialize with existing data
        System.arraycopy(tokens, 0, output, 0, tokens.length);

        Geometry articleGeo = makePoint(Double.valueOf(tokens[3]), Double.valueOf(tokens[4]));
        if (tokens[9].startsWith("//")) {
            tokens[9] = "http:" + tokens[9];
        }
        URL url;
        try {
            url = new URL(tokens[9]);
        } catch (MalformedURLException e) {
            throw new InvalidUrlException(tokens[9]);
        }

        LocalPage country = getContainingCountry(articleGeo);

        if (country == null) {
//            LOG.info("No country found for " + input);
            return null;
        }

        Geometry countryGeo = countries.get(country);

        output[5] = "" + country.getLocalId();
        output[6] = "" + country.getTitle();
        output[7] = "" + countryGeo.getCentroid().getX();
        output[8] = "" + countryGeo.getCentroid().getY();

        try {
            InternetDomainName domain = InternetDomainName.fromLenient(url.getHost());
            InternetDomainName topDomain = domain.topPrivateDomain();
            output[9] = url.toExternalForm();
            output[10] = StringUtils.join(domain.parts(), ".");
            output[11] =  StringUtils.join(topDomain.parts(), ".");
        } catch (IllegalArgumentException e) {
            throw  new InvalidUrlException(tokens[9]);
        } catch (IllegalStateException e) {
            throw  new InvalidUrlException(tokens[9]);
        }

        URL url2 = getRealUrl(url);
        if (url2 == null) {
            output[12] = "";
            output[13] = "";
            output[14] = "";
        } else if (url.toExternalForm().equals(url2.toExternalForm())) {
            output[12] = output[9];
            output[13] = output[10];
            output[14] = output[11];
        } else {
            try {
                InternetDomainName domain = InternetDomainName.fromLenient(url2.getHost());
                InternetDomainName topDomain = domain.topPrivateDomain();
                output[12] = url2.toExternalForm();
                output[13] = StringUtils.join(domain.parts(), ".");
                output[14] =  StringUtils.join(topDomain.parts(), ".");
            } catch (IllegalArgumentException e) {
                throw  new InvalidUrlException(tokens[9]);
            } catch (IllegalStateException e) {
                throw  new InvalidUrlException(tokens[9]);
            }
        }

        for (int i = 0; i < output.length; i++) {
            output[i] = output[i].replaceAll("\\s+", " ").trim();
        }

        return StringUtils.join(output, "\t");
    }

    private URL getRealUrl(URL url) throws InvalidUrlException {
        String host = url.getHost().toLowerCase();

        if (host.startsWith("translate.google.")) {
            return getParamAsUrl(url, "u");
        } else if (host.endsWith("babelfish.yahoo.com")) {
            return getParamAsUrl(url, "trurl");
        } else if (host.endsWith("microsofttranslator.com")) {
            return getParamAsUrl(url, "a");
        } else if (host.endsWith("archive.org")) {
            String path = url.getPath();
            int i = path.indexOf("http:");
            if (i < 0) {
                return null;
            }
            try {
                return new URL(path.substring(i));
            } catch (MalformedURLException e) {
                throw new InvalidUrlException(url.toString());
            }
        } else {
            return url;
        }
    }

    private URL getParamAsUrl(URL url, String name) throws InvalidUrlException {
        try {
            for (NameValuePair nv : URLEncodedUtils.parse(url.toURI(), "UTF-8")) {
                if (nv.getName().equalsIgnoreCase(name)) {
                    return new URL(nv.getValue());
                }
            }
            return null;
        } catch (IllegalArgumentException e) {  // incorrect parameter encoding
            return getDirtyParamAsUrl(url, name);
        } catch (URISyntaxException e) {
            return getDirtyParamAsUrl(url, name);
        } catch (MalformedURLException e) {
            throw new InvalidUrlException(url.toString());
        }
    }

    private URL getDirtyParamAsUrl(URL url, String name) throws InvalidUrlException {
        // Make a last-ditch effort for improperly coded urls
        String s = url.toExternalForm();
        int i = s.indexOf("&" + name + "=");
        if (i < 0) {
            i = s.indexOf("?" + name + "=");
        }
        if (i >= 0) {
            try {
                return new URL(s.substring(i + 2 + name.length()));
            } catch (MalformedURLException e) {
                throw new InvalidUrlException(s);
            }
        }
        throw new InvalidUrlException(s);
    }

    private Geometry makePoint(double lat, double lng) {
        Coordinate[] coords = new Coordinate[1];
        coords[0] = new Coordinate(lng, lat);
        CoordinateArraySequence coordArraySeq = new CoordinateArraySequence(coords);
        return new Point(coordArraySeq, new GeometryFactory(new PrecisionModel(), 4326));
    }

    private LocalPage getContainingCountry(Geometry point) {
        // FIXME: This doesn't handle projection correctly.
        LocalPage closestPage = null;
        double closestDistance = 1.0 / 60 * 12; // 12 nautical miles, a territorial border

        for (LocalPage country : countries.keySet()) {
            double d = countries.get(country).distance(point);
            if (d < closestDistance) {
                closestDistance = d;
                closestPage = country;
            }
        }
        return closestPage;
    }

    private LocalPage getLocalPage(int conceptId) throws DaoException {
        int pageId = conceptDao.getLocalId(language, conceptId);
        if (pageId < 0) {
            return null;
        }
        return pageDao.getById(language ,pageId);
    }

    static class InvalidUrlException extends Exception {
        private String url;

        public InvalidUrlException(String url) {
            super("Invalid url: " + url);
            this.url = url;
        }

        public String getUrl() {
            return url;
        }
    }

    public static void main(String args[]) throws Exception {
        Env env = EnvBuilder.envFromArgs(args);
        WmfExtractEnhancer analyzer = new WmfExtractEnhancer(env, Language.EN);
        analyzer.createCsv(new File("wmf_source_urls.tsv.bz2"), new File("source_urls.tsv"), new File("invalid_urls.txt"));
    }
}
