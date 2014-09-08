package org.wikibrain.sources;

import org.apache.commons.io.FileUtils;
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
import org.wikibrain.spatial.dao.SpatialDataDao;
import org.wikibrain.utils.WpIOUtils;

import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/**
 * @author Shilad Sen
 */
public class ArticleSourceSampler {
    private final Language language;
    private final LocalPageDao pageDao;
    private final SpatialDataDao spatialDao;
    private final UniversalPageDao conceptDao;
    private final RawPageDao rawPageDao;
    private final File dir;
    private final List<Integer> geoConcepts;

    public ArticleSourceSampler(Env env, Language language) throws ConfigurationException, DaoException {
        this.language = language;
        this.pageDao = env.getConfigurator().get(LocalPageDao.class);
        this.spatialDao = env.getConfigurator().get(SpatialDataDao.class);
        this.conceptDao = env.getConfigurator().get(UniversalPageDao.class);
        this.rawPageDao = env.getConfigurator().get(RawPageDao.class);

        this.dir = new File("citation_samples");
        FileUtils.deleteQuietly(dir);
        this.dir.mkdirs();

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

        BufferedWriter writer = WpIOUtils.openWriter(new File(dir, page.getTitle().getTitleStringWithoutNamespace() + ".html"));

        String href = "<a href=\"" + page.getTitle().toUrl() + "\">" + page.getTitle().getCanonicalTitle() + "</a>";

        writer.write("<html><body>\n");
        writer.write("<h1>Coding for " + href + "<h1>\n");
        writer.write("<h3>Instructions:</h3>\n");
        writer.write("<ol>\n");
        writer.write("</ol>\n");
        writer.write("<ol>\n" +
                "<li> Visit the page at " + href + "\n" +
                "<li> Enter your initials in the 'coder' section\n" +
                "<li> Look at the list of extracted links below in the 'Correct sources' section\n" +
                "<li> Add a short description of each missed source to the 'Missed sources' section\n" +
                "</ol>\n");

        writer.write("<h3>Initials of person who coded this:</h3>\n");
        writer.write("<h3>Correct sources</h3>\n");
        List<String> links = renderer.extractExternalLinks(language, page.getTitle().getCanonicalTitle());
        Collections.sort(links);
        writer.write("<ul>\n");
        for (String link : links) {
            if (link.startsWith("http://") || link.startsWith("https://")) {
                writer.write("<li><a href=\"" + link + "\">" + link + "</a>\n");
            }
        }
        writer.write("</ul>\n");
        writer.write("<h3>Missing sources</h3>\n");
        writer.close();
    }

    public static void main(String args[]) throws ConfigurationException, DaoException, WikiBrainException, IOException {
        Env env = EnvBuilder.envFromArgs(args);
        ArticleSourceSampler sampler = new ArticleSourceSampler(env, env.getLanguages().getDefaultLanguage());
        for (int i = 0; i < 50; i++) {
            sampler.sampleOne();
        }
    }
}
