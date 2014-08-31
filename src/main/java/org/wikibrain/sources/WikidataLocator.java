package org.wikibrain.sources;

import com.google.common.net.InternetDomainName;
import com.vividsolutions.jts.geom.Geometry;
import org.apache.commons.lang.StringUtils;
import org.wikibrain.conf.ConfigurationException;
import org.wikibrain.core.cmd.Env;
import org.wikibrain.core.cmd.EnvBuilder;
import org.wikibrain.core.dao.DaoException;
import org.wikibrain.core.dao.LocalPageDao;
import org.wikibrain.core.dao.UniversalPageDao;
import org.wikibrain.core.lang.Language;
import org.wikibrain.core.model.LocalPage;
import org.wikibrain.spatial.core.dao.SpatialDataDao;
import org.wikibrain.utils.WpIOUtils;
import org.wikibrain.wikidata.WikidataDao;
import org.wikibrain.wikidata.WikidataEntity;
import org.wikibrain.wikidata.WikidataFilter;
import org.wikibrain.wikidata.WikidataStatement;

import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;

/**
 * @author Shilad Sen
 */
public class WikidataLocator {
    private final Language language;
    private final LocalPageDao pageDao;
    private final SpatialDataDao spatialDao;
    private final UniversalPageDao conceptDao;
    private final WikidataDao wikidataDao;
    private Map<LocalPage, Geometry> countries = new HashMap<LocalPage, Geometry>();

    public WikidataLocator(Env env) throws ConfigurationException, DaoException {
        this.pageDao = env.getConfigurator().get(LocalPageDao.class);
        this.spatialDao = env.getConfigurator().get(SpatialDataDao.class);
        this.conceptDao = env.getConfigurator().get(UniversalPageDao.class);
        this.wikidataDao = env.getConfigurator().get(WikidataDao.class);
        language = env.getDefaultLanguage();


        Map<Integer, Geometry> idsToCountries = spatialDao.getAllGeometriesInLayer("country");
        for (int conceptId : idsToCountries.keySet()) {
            LocalPage country = getLocalPage(conceptId);
            if (country != null) {
                countries.put(country, idsToCountries.get(conceptId));
            }
        }
        System.out.println("resolved " + countries.size() + " countries");
    }

    public void write(File file) throws DaoException, IOException {
        Map<Integer, Geometry> articlePoints = spatialDao.getAllGeometriesInLayer("wikidata");
        BufferedWriter writer = WpIOUtils.openWriter(file);

        int n = 0;
        WikidataFilter filter = new WikidataFilter.Builder().withPropertyId(856).build();
        for (WikidataStatement stm : wikidataDao.get(filter)) {
            if (!articlePoints.containsKey(stm.getItem().getId())) {
                continue;
            }
            Geometry location = articlePoints.get(stm.getItem().getId());
            LocalPage country = getContainingCountry(location);
            if (country == null) {
                continue;
            }
            n++;

            String surl = stm.getValue().getStringValue();
            while (surl.endsWith("/")) {
                surl = surl.substring(0, surl.length() -1);
            }
            URL url = new URL(surl);
            InternetDomainName domain;
            InternetDomainName topDomain;
            try {
                domain = InternetDomainName.fromLenient(url.getHost());
                topDomain = domain.topPrivateDomain();
            } catch (IllegalArgumentException e) {
                System.err.println("Invalid url: " + url.toString());
                continue;
            } catch (IllegalStateException e) {
                System.err.println("Invalid url: " + url.toString());
                continue;
            }

            writer.write(stm.getValue().getStringValue());
            writer.write("\t");
            writer.write(country.getTitle().getCanonicalTitle());
            writer.write("\t");
            writer.write(StringUtils.join(domain.parts(), "."));
            writer.write("\t");
            writer.write(StringUtils.join(topDomain.parts(), "."));
            writer.write("\n");
        }
        writer.close();

        System.out.println("found " + n);
    }


    private LocalPage getContainingCountry(Geometry point) {
        for (LocalPage country : countries.keySet()) {
            if (countries.get(country).contains(point)) {
                return country;
            }
        }
        return null;
    }

    private LocalPage getLocalPage(int conceptId) throws DaoException {
        int pageId = conceptDao.getLocalId(language, conceptId);
        if (pageId < 0) {
            return null;
        }
        return pageDao.getById(language ,pageId);
    }


    public static void main(String args[]) throws ConfigurationException, DaoException, IOException {
        Env env = EnvBuilder.envFromArgs(args);
        WikidataLocator wdl = new WikidataLocator(env);
        wdl.write(new File("dat/domain_wikidata_locations.tsv"));

    }
}
