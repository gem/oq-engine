package org.gem.engine.hazard.parsers;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.List;

import org.gem.engine.InputModelData;
import org.gem.engine.SourceModelReader;
import org.gem.engine.hazard.models.nshmp.us.NshmpCaliforniaFaultData;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class GemFileParserTest {

    private static final String FILENAME = "california-fault.dat";

    @Before
    public void setUp() {
        new File(FILENAME).delete();
    }

    @After
    public void tearDown() {
        // new File(FILENAME).delete();
    }

    @Test
    public void serializesCaliforniaFaultData() throws Exception {
        NshmpCaliforniaFaultData faults =
                new NshmpCaliforniaFaultData("java_tests/data/nshmp/CA/");

        faults.read(-90.0, +90.0, -180.0, +180.0);

        faults.writeSource2CLformat(new FileWriter(FILENAME));
        ArrayList<GEMSourceData> sources =
                new InputModelData(FILENAME, 0.1).getSourceList();

        assertEquals(faults.getList().size(), sources.size());
        assertSourcesAreEqual(faults.getList(), sources);
    }

    /**
     * Compares source model data (for California faults) as derived from the
     * parser that reads the original ASCII files and the source model data read
     * from nrml file generated with the writeSource2NrmlFormat method.
     */
    @Test
    public void serializeCaliforniaFaultData2Nrml() {
        NshmpCaliforniaFaultData faults =
                new NshmpCaliforniaFaultData("java_tests/data/nshmp/CA/");
        faults.read(-90.0, +90.0, -180.0, +180.0);

        File file = new File("california_fault_model.xml");

        faults.writeSource2NrmlFormat(file);
        SourceModelReader modelReader =
                new SourceModelReader(file.getAbsolutePath(), 0.1);
        ArrayList<GEMSourceData> sources = new ArrayList(modelReader.read());
        assertEquals(faults.getList().size(), sources.size());
        assertSourcesAreEqual(faults.getList(), sources);
    }

    private void assertSourcesAreEqual(List<GEMSourceData> list1,
            List<GEMSourceData> list2) {

        for (int i = 0; i < list1.size(); i++) {
            assertTrue(list1.get(i).equals(list2.get(i)));
        }
    }

}
