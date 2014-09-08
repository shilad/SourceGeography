package org.wikibrain.sources;

import com.google.common.net.InternetDomainName;
import com.vividsolutions.jts.geom.Geometry;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang.StringUtils;
import org.wikibrain.conf.ConfigurationException;
import org.wikibrain.core.cmd.Env;
import org.wikibrain.core.cmd.EnvBuilder;
import org.wikibrain.core.dao.DaoException;
import org.wikibrain.core.dao.LocalPageDao;
import org.wikibrain.core.dao.RawPageDao;
import org.wikibrain.core.dao.UniversalPageDao;
import org.wikibrain.core.lang.Language;
import org.wikibrain.core.model.LocalPage;
import org.wikibrain.parser.wiki.WikitextRenderer;
import org.wikibrain.spatial.dao.SpatialDataDao;
import org.wikibrain.utils.ParallelForEach;
import org.wikibrain.utils.Procedure;
import org.wikibrain.utils.WpIOUtils;

import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Logger;

/**
 * @author Shilad Sen
 */
public class SourceExtractor {
    private static final Logger LOG = Logger.getLogger(SourceExtractor.class.getName());

    private final Language language;
    private final LocalPageDao pageDao;
    private final SpatialDataDao spatialDao;
    private final UniversalPageDao conceptDao;
    private final RawPageDao rawPageDao;
    private Map<LocalPage, Geometry> countries = new HashMap<LocalPage, Geometry>();
    private AtomicInteger invalidUrls = new AtomicInteger();

    public SourceExtractor(Env env, Language language) throws ConfigurationException, DaoException {
        this.language = language;
        this.pageDao = env.getConfigurator().get(LocalPageDao.class);
        this.spatialDao = env.getConfigurator().get(SpatialDataDao.class);
        this.conceptDao = env.getConfigurator().get(UniversalPageDao.class);
        this.rawPageDao = env.getConfigurator().get(RawPageDao.class);

        Map<Integer, Geometry> idsToCountries = spatialDao.getAllGeometriesInLayer("country");
        for (int conceptId : idsToCountries.keySet()) {
            LocalPage country = getLocalPage(conceptId);
            if (country != null) {
                countries.put(country, idsToCountries.get(conceptId));
            }
        }
        System.out.println("resolved " + countries.size() + " countries");
    }

    public void createCsv(File csv, File invalidFile, final File completedFile) throws DaoException, IOException {
        Set<Integer> completed = new HashSet<Integer>();
        for (String line : FileUtils.readLines(completedFile)) {
            completed.add(Integer.valueOf(line.trim()));
        }
        final Map<Integer, Geometry> geotags = spatialDao.getAllGeometriesInLayer("wikidata");
        boolean exists = csv.exists();
        final BufferedWriter writer = WpIOUtils.openWriterForAppend(csv);
        final BufferedWriter invalid = WpIOUtils.openWriterForAppend(invalidFile);
        List<String> fields = Arrays.asList(
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
                "effectiveDomain"
        );
        if (!exists) {
            writer.write(StringUtils.join(fields, "\t") + "\n");
        }
        List<Integer> geoConcepts = new ArrayList<Integer>(geotags.keySet());
        geoConcepts.removeAll(completed);
        Collections.shuffle(geoConcepts);

        ParallelForEach.loop(
//                geotags.keySet(), WpThreadUtils.getMaxThreads(),
                geoConcepts, 1,
                new Procedure<Integer>() {
                    @Override
                    public void call(Integer conceptId) throws Exception {
                        writeOneConcept(completedFile, writer, invalid, conceptId, geotags.get(conceptId));

                    }
                },
                100);
        writer.close();
    }

    private void writeOneConcept(File completed, BufferedWriter writer, BufferedWriter invalid, int conceptId, Geometry articleGeo) throws DaoException, IOException {
        FileUtils.write(completed, "" + conceptId + "\n", true);

        LocalPage article = getLocalPage(conceptId);
        LocalPage country = getContainingCountry(articleGeo);
        Geometry countryGeo = countries.get(country);

        if (country == null || article == null) {
            return;
        }
        List<String> row = Arrays.asList(
                language.getLangCode(),
                "" + article.getLocalId(),
                "" + article.getTitle(),
                "" + articleGeo.getCentroid().getX(),
                "" + articleGeo.getCentroid().getY(),
                "" + country.getLocalId(),
                "" + country.getTitle(),
                "" + countryGeo.getCentroid().getX(),
                "" + countryGeo.getCentroid().getY(),
                "NULL",
                "NULL",
                "NULL"
        );
        writer.write(StringUtils.join(row, "\t") + "\n");
        for (URL url : extractUrls(invalid, article)) {
            try {
                InternetDomainName domain = InternetDomainName.fromLenient(url.getHost());
                InternetDomainName topDomain = domain.topPrivateDomain();
                row.set(row.size() - 3, url.toExternalForm());
                row.set(row.size() - 2, StringUtils.join(domain.parts(), "."));
                row.set(row.size() - 1, StringUtils.join(topDomain.parts(), "."));
                for (int i = 0; i < row.size(); i++) {
                    row.set(i, row.get(i).replaceAll("\\s+", " ").trim());
                }
                writer.write(StringUtils.join(row, "\t") + "\n");
            } catch (IllegalArgumentException e) {
                invalid.write(url.toString() + "\n");
            } catch (IllegalStateException e) {
                invalid.write(url.toString() + "\n");
            }
        };
    }

    private LocalPage getContainingCountry(Geometry point) {
        for (LocalPage country : countries.keySet()) {
            if (countries.get(country).contains(point)) {
                return country;
            }
        }
        return null;
    }

    /**
     *
     * @param invalid
     * @param page
     * @return
     */
    public List<URL> extractUrls(BufferedWriter invalid, LocalPage page) throws DaoException, IOException {
        WikitextRenderer renderer = new WikitextRenderer();
        List<URL> links = new ArrayList<URL>();
        for (String link : renderer.extractExternalLinks(page.getLanguage(), page.getTitle().getCanonicalTitle())) {
            try {
                URL url = new URL(link);
                if (url.getProtocol().startsWith("http")) {
                    links.add(url);
                } else {
                    invalid.write(link + "\n");
                }
            } catch (MalformedURLException e) {
                invalid.write(link + "\n");
            }
        }
        return links;
    }

    private LocalPage getLocalPage(int conceptId) throws DaoException {
        int pageId = conceptDao.getLocalId(language, conceptId);
        if (pageId < 0) {
            return null;
        }
        return pageDao.getById(language ,pageId);
    }

    public static void main(String args[]) throws Exception {
        Env env = EnvBuilder.envFromArgs(args);
        SourceExtractor analyzer = new SourceExtractor(env, Language.EN);
        analyzer.createCsv(new File("source_urls.tsv"), new File("invalid_urls.txt"), new File("completed_concepts.txt"));
    }
}
