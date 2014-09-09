package org.wikibrain.sources;

import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.simplify.TopologyPreservingSimplifier;
import org.h2.engine.Procedure;
import org.wikibrain.conf.ConfigurationException;
import org.wikibrain.core.cmd.Env;
import org.wikibrain.core.cmd.EnvBuilder;
import org.wikibrain.core.dao.DaoException;
import org.wikibrain.core.dao.LocalPageDao;
import org.wikibrain.core.dao.UniversalPageDao;
import org.wikibrain.core.lang.Language;
import org.wikibrain.core.model.LocalPage;
import org.wikibrain.spatial.dao.SpatialDataDao;
import org.wikibrain.spatial.distance.GeodeticDistanceMetric;
import org.wikibrain.utils.ParallelForEach;
import org.wikibrain.utils.WpIOUtils;

import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.util.Map;

/**
 * @author Shilad Sen
 */
public class CountryDistances {
    public static void main(String args[]) throws ConfigurationException, DaoException, IOException {
        final Env env = EnvBuilder.envFromArgs(args);
        final UniversalPageDao conceptDao = env.getConfigurator().get(UniversalPageDao.class);
        final LocalPageDao pageDao = env.getConfigurator().get(LocalPageDao.class);
        final SpatialDataDao spatialDao = env.getConfigurator().get(SpatialDataDao.class);
        final Map<Integer, Geometry> geometries = spatialDao.getAllGeometriesInLayer("country");
        final GeodeticDistanceMetric metric = new GeodeticDistanceMetric(spatialDao);
        System.out.println("cleaning up geometries...");

        for (int conceptId : geometries.keySet()) {
            System.out.println("pre-processing " + conceptId);
            Geometry g = metric.cleanupGeometry(geometries.get(conceptId));
            geometries.put(conceptId, g.getCentroid());
        }
        final BufferedWriter writer = WpIOUtils.openWriter(new File("dat/country_distances.tsv"));

        ParallelForEach.loop(geometries.keySet(), new org.wikibrain.utils.Procedure<Integer>() {
            @Override
            public void call(Integer id1) throws Exception {
                LocalPage page1 = pageDao.getById(Language.EN, conceptDao.getLocalId(Language.EN, id1));
                System.out.println("processing " + page1);
                for (int id2 : geometries.keySet()) {
                    LocalPage page2 = pageDao.getById(Language.EN, conceptDao.getLocalId(Language.EN, id2));
                    Geometry g1 = geometries.get(id1);
                    Geometry g2 = geometries.get(id2);
                    double d;
                    try {
                        d = metric.distance(g1, g2);

                    } catch (ArithmeticException e) {
                        System.err.println("convergence error between " + page1 + " and " + page2);
                        d = g1.distance(g2) * 111;
                    }
                    synchronized (writer) {
                        writer.write(String.format("%s\t%s\t%d\n",
                                page1.getTitle().getCanonicalTitle(),
                                page2.getTitle().getCanonicalTitle(),
                                (int) (d / 1000.0)));
                    }
                }
            }
        });

        writer.close();
    }
}
