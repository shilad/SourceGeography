package org.wikibrain.sources;

import com.google.common.net.InternetDomainName;
import org.apache.commons.lang3.StringUtils;
import org.wikibrain.conf.ConfigurationException;
import org.wikibrain.core.WikiBrainException;
import org.wikibrain.core.cmd.Env;
import org.wikibrain.core.cmd.EnvBuilder;
import org.wikibrain.core.dao.DaoException;
import org.wikibrain.core.dao.LocalPageDao;
import org.wikibrain.core.dao.RawPageDao;
import org.wikibrain.core.dao.UniversalPageDao;
import org.wikibrain.core.lang.Language;
import org.wikibrain.core.model.LocalPage;
import org.wikibrain.core.model.NameSpace;
import org.wikibrain.parser.wiki.WikitextRenderer;
import org.wikibrain.spatial.core.dao.SpatialDataDao;
import org.wikibrain.utils.WpIOUtils;

import java.io.Closeable;
import java.io.IOException;
import java.io.Writer;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.logging.Logger;

/**
 * @author Shilad Sen
 */
public class URLSampler implements Closeable {
    private static final Logger LOG = Logger.getLogger(URLSampler.class.getName());

    private final Language language;
    private final LocalPageDao pageDao;
    private final SpatialDataDao spatialDao;
    private final UniversalPageDao conceptDao;
    private final RawPageDao rawPageDao;
    private final Writer csv;
    private final List<Integer> geoConcepts;

    public URLSampler(Env env, Language language) throws ConfigurationException, DaoException, IOException {
        this.language = language;
        this.pageDao = env.getConfigurator().get(LocalPageDao.class);
        this.spatialDao = env.getConfigurator().get(SpatialDataDao.class);
        this.conceptDao = env.getConfigurator().get(UniversalPageDao.class);
        this.rawPageDao = env.getConfigurator().get(RawPageDao.class);

        this.csv = WpIOUtils.openWriter("url_samples.csv");
        csv.write("url\tdomain\ttop-domain\tarticle\turl\tcountry\tcomments\n");

        this.geoConcepts = new ArrayList<Integer>(spatialDao.getAllGeometriesInLayer("wikidata").keySet());
    }

    public void sampleOne() throws DaoException, WikiBrainException, IOException {
        WikitextRenderer renderer = new WikitextRenderer();

        Random random = new Random();
        LocalPage page = null;
        while (page == null) {
            int conceptId = geoConcepts.get(random.nextInt(geoConcepts.size()));
            int pageId = conceptDao.getLocalId(language, conceptId);
            page = pageDao.getById(language, pageId);
            if (page.getNameSpace() != NameSpace.ARTICLE || page.getTitle().getCanonicalTitle().contains("/")) {
                page = null;
            }
        }

        List<URL> links = new ArrayList<URL>();
        for (String link : renderer.extractExternalLinks(language, page.getTitle().getCanonicalTitle())) {
            try {
                URL url = new URL(link);
                if (url.getProtocol().startsWith("http")) {
                    links.add(url);
                } else {
                    LOG.warning("Ignoring link protocol: " + link);
                }
            } catch (MalformedURLException e) {
                LOG.warning("Invalid URL found: " + link);
            }
        }
        if (links.isEmpty()) {
            sampleOne();
            return;
        }
        URL url = links.get(random.nextInt(links.size()));
        InternetDomainName domain = InternetDomainName.fromLenient(url.getHost());
        InternetDomainName topDomain = domain.topPrivateDomain();
        csv.write(String.format(
                "%s\t%s\t%s\t%s\t%s\t%s\t%s\n",
                url.toExternalForm().replaceAll("\\s+", " "),
                StringUtils.join(domain.parts(), "."),
                StringUtils.join(topDomain.parts(), "."),
                page.getTitle().getCanonicalTitle(),
                page.getTitle().toUrl(),
                "",
                ""
        ));
    }

    public void close() throws IOException {
        csv.close();
    }

    public static void main(String args[]) throws ConfigurationException, DaoException, WikiBrainException, IOException {
        Env env = EnvBuilder.envFromArgs(args);
        URLSampler sampler = new URLSampler(env, env.getLanguages().getDefaultLanguage());
        for (int i = 0; i < 100; i++) {
            sampler.sampleOne();
        }
    }
}
