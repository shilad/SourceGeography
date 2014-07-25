package org.wikibrain.sources;

import org.apache.commons.io.IOUtils;
import org.apache.commons.io.LineIterator;
import org.wikibrain.utils.WpIOUtils;

import java.io.File;
import java.io.IOException;
import java.util.Iterator;
import java.util.logging.Logger;

/**
 * @author Shilad Sen
 */
public class ExtractReader implements Iterable<Citation> {
    private static final Logger LOG = Logger.getLogger(ExtractReader.class.getName());

    private final File file;

    public ExtractReader(File file) {
        this.file = file;
    }

    @Override
    public Iterator<Citation> iterator() {
        final LineIterator iter;
        try {
            iter = new LineIterator(WpIOUtils.openBufferedReader(file));
        } catch (IOException e) {
            throw new IllegalArgumentException("Invalid file: " + file);
        }
        // Skip; header
        if (iter.hasNext()) {
            iter.next();
        }

        return new Iterator<Citation>() {
            Citation buffer = null;
            @Override
            public boolean hasNext() {
                fillBuffer();
                return (buffer != null);
            }

            @Override
            public Citation next() {
                fillBuffer();
                Citation result = buffer;
                buffer = null;
                return result;
            }

            @Override
            public void remove() {
                throw new UnsupportedOperationException();
            }

            private Citation fillBuffer() {
                while (buffer == null && iter.hasNext()) {
                    String line = iter.nextLine();
                    if (!line.trim().endsWith("NULL")) {
                        try {
                            buffer = new Citation(line);
                        } catch (IllegalArgumentException e) {
                            LOG.info("Invalid line in " + file + ": " + line);
                        }
                    }
                    if (!iter.hasNext()) {
                        ((LineIterator) iter).close();
                    }
                }
                return buffer;
            }
        };
    }

    public static void main(String args[]) {
        int i = 0;
        for (Citation citation : new ExtractReader(new File("../wikibrain/source_urls.tsv"))) {
            i++;
        }
        System.err.println("i is " + i);
    }
}
