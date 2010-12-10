package org.gem.engine;

import org.junit.Test;

public class SourceModelReaderTest {

    @Test
    public void readSourceModel() {

        SourceModelReader srcModelReader =
                new SourceModelReader("java_tests/data/source_model.xml", 0.1);
    }
}
