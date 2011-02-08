package org.gem.engine;

import static org.junit.Assert.assertEquals;

import java.util.ArrayList;
import java.util.List;

import org.gem.engine.hazard.parsers.SourceModelTestData;
import org.junit.Test;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class SourceModelReaderTest extends SourceModelTestData {

    /**
     * Compares source model as derived by reading nrML file with source model
     * defined by hand with the same data contained in the nrML file
     */
    @Test
    public void readsTheSourceModel() {
        List<GEMSourceData> srcList = new ArrayList<GEMSourceData>();
        srcList.add(simpleFaultSourceData());
        srcList.add(complexSourceData());
        srcList.add(areaSourceData());
        srcList.add(pointSourceData());

        SourceModelReader srcModelReader =
                new SourceModelReader("java_tests/data/source_model.xml", 0.1);

        List<GEMSourceData> srcListRead = srcModelReader.read();

        assertEquals(srcList.size(), srcListRead.size());
        assertSourcesAreEqual(srcListRead, srcList);
    }

}
