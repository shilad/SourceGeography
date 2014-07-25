package org.wikibrain.sources;

import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.Point;
import com.vividsolutions.jts.geom.PrecisionModel;
import com.vividsolutions.jts.geom.impl.CoordinateArraySequence;
import org.wikibrain.core.lang.Language;
import org.wikibrain.core.model.LocalPage;

import java.net.MalformedURLException;
import java.net.URL;

/**
 * @author Shilad Sen
 */
public class Citation {
    private final LocalPage article;
    private final Point articleLocation;

    private final LocalPage country;
    private final Point countryLocation;

    private final URL url;
    private final String domain;
    private final String effectiveDomain;

    public Citation(String line) {
        if (line.endsWith("\n")) {
            line = line.substring(0, line.length() - 1);
        }
        String tokens[] = line.split("\t");
        if (tokens.length != 12) {
            throw new IllegalArgumentException("Invalid line in extract: " + line);
        }
        this.article = tokensToLocalPage(tokens[0], tokens[1], tokens[2]);
        this.articleLocation = tokensToPoint(tokens[3], tokens[4]);

        this.country = tokensToLocalPage(tokens[0], tokens[5], tokens[6]);
        this.countryLocation = tokensToPoint(tokens[7], tokens[8]);

        try {
            this.url = new URL(tokens[9]);
        } catch (MalformedURLException e) {
            throw new IllegalArgumentException("Invalid URL: " + tokens[9]);
        }

        this.domain = tokens[10];
        this.effectiveDomain = tokens[11];
    }

    private LocalPage tokensToLocalPage(String langToken, String idToken, String titleToken) {
        Language lang = Language.getByLangCode(langToken);
        String suffix = " (" + lang.getLangCode() + ")";
        if (!titleToken.endsWith(suffix)) {
            throw new IllegalArgumentException("Invalid title: " + titleToken);
        }
        String title = titleToken.substring(0, titleToken.length() - suffix.length());
        return new LocalPage(lang, Integer.valueOf(idToken), title);
    }

    private Point tokensToPoint(String tokenX, String tokenY) {
        Coordinate[] coords = new Coordinate[1];
        coords[0] = new Coordinate(Double.valueOf(tokenX), Double.valueOf(tokenY));
        CoordinateArraySequence coordArraySeq = new CoordinateArraySequence(coords);
        return new Point(coordArraySeq, new GeometryFactory(new PrecisionModel(), 4326));
    }

    public LocalPage getArticle() {
        return article;
    }

    public Point getArticleLocation() {
        return articleLocation;
    }

    public LocalPage getCountry() {
        return country;
    }

    public Point getCountryLocation() {
        return countryLocation;
    }

    public URL getUrl() {
        return url;
    }

    public String getDomain() {
        return domain;
    }

    public String getEffectiveDomain() {
        return effectiveDomain;
    }
}
