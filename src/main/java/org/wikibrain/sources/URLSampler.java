package org.wikibrain.sources;

import com.google.common.net.InternetDomainName;
import org.apache.commons.lang3.StringUtils;
import org.wikibrain.conf.ConfigurationException;
import org.wikibrain.core.WikiBrainException;
import org.wikibrain.core.cmd.Env;
import org.wikibrain.core.cmd.EnvBuilder;
import org.wikibrain.core.dao.DaoException;
import org.wikibrain.core.model.LocalPage;
import org.wikibrain.core.model.NameSpace;
import org.wikibrain.parser.wiki.WikitextRenderer;
import org.wikibrain.utils.WpIOUtils;

import java.io.Closeable;
import java.io.File;
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
public class URLSampler {
    private static final Logger LOG = Logger.getLogger(URLSampler.class.getName());


    public URLSampler() {
    }

    public void sample(File citations, File outputCsv, int n) throws IOException, WikiBrainException {
        StreamSampler<Citation> sampler = new StreamSampler<Citation>(n);
        for (Citation citation : new ExtractReader(citations)) {
            sampler.offer(citation);
        }
        Writer csv = WpIOUtils.openWriter(outputCsv);
        csv.write("url\tdomain\ttop-domain\tarticle\turl\tcountry\tcomments\n");
        for (Citation citation : sampler.getSample()) {
            csv.write(String.format(
                    "%s\t%s\t%s\t%s\t%s\t%s\t%s\n",
                    citation.getUrl(),
                    citation.getDomain(),
                    citation.getEffectiveDomain(),
                    citation.getArticle().getTitle().getCanonicalTitle(),
                    citation.getArticle().getTitle().toUrl(),
                    "",
                    ""
            ));
        }
        csv.close();
    }

    public static void main(String args[]) throws Exception {
        URLSampler sampler = new URLSampler();
        sampler.sample(new File("../wikibrain/source_urls.tsv"), new File("./source_url_sample.tsv"), 450);
    }
}
