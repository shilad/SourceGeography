package org.wikibrain.sources;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * A class to sample uniformly from a stream of unknown size.
 *
 * @author Shilad Sen
 */
public class StreamSampler<K> {

    private final int n;
    private Random random = new Random();
    private final List<K> sample;
    private int numObservations = 0;

    public StreamSampler(int n) {
        this.n = n;
        this.sample = new ArrayList<K>();
    }

    public void offer(K elem) {
        numObservations++;
        if (sample.size() < n) {
            sample.add(elem);
        } else if (random.nextInt(numObservations) < n) {
            sample.set(random.nextInt(n), elem);
        }
    }

    public List<K> getSample() {
        return new ArrayList<K>(sample);
    }
}
