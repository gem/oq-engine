package org.gem.engine.hazard.parsers;

import static org.junit.Assert.assertEquals;

import java.io.File;
import java.util.ArrayList;

import org.gem.engine.SourceModelReader;
import org.gem.engine.hazard.models.nshmp.us.NshmpCaliforniaFaultData;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class GemFileParserTest extends SourceModelTestData {

    private static final String OUTPUT_FILE = "output.txt";
    private static final String FILENAME = "california-fault.dat";

    @Before
    public void setUp() {
        new File(FILENAME).delete();
        new File(OUTPUT_FILE).delete();
    }

    @After
    public void tearDown() {
        new File(FILENAME).delete();
        // new File(OUTPUT_FILE).delete();
    }

    // TODO (ac): Add equals on object after the implementation of
    // truncatedGutenbergRichter
    @Test
    public void serializesSimpleSourceData() {
        GemFileParser writer = new GemFileParser();

        ArrayList<GEMSourceData> sources = new ArrayList<GEMSourceData>();
        sources.add(simpleFaultSourceData());

        writer.setList(sources);
        writer.writeSource2NrmlFormat(new File(OUTPUT_FILE));

        SourceModelReader reader = new SourceModelReader(OUTPUT_FILE, 0.1);
        assertEquals(sources.size(), reader.read().size());
    }

    // TODO (ac): Add equals on object after the implementation of
    // truncatedGutenbergRichter
    @Test
    public void serializesComplexSourceData() {
        GemFileParser writer = new GemFileParser();

        ArrayList<GEMSourceData> sources = new ArrayList<GEMSourceData>();
        sources.add(complexSourceData());

        writer.setList(sources);
        writer.writeSource2NrmlFormat(new File(OUTPUT_FILE));

        SourceModelReader reader = new SourceModelReader(OUTPUT_FILE, 0.1);
        assertEquals(sources.size(), reader.read().size());
    }

    // TODO (ac): Add equals on object after the implementation of
    // truncatedGutenbergRichter
    @Test
    public void serializesAreaSourceData() {
        GemFileParser writer = new GemFileParser();

        ArrayList<GEMSourceData> sources = new ArrayList<GEMSourceData>();
        sources.add(areaSourceData());

        writer.setList(sources);
        writer.writeSource2NrmlFormat(new File(OUTPUT_FILE));

        SourceModelReader reader = new SourceModelReader(OUTPUT_FILE, 0.1);
        assertEquals(sources.size(), reader.read().size());
    }

    // TODO (ac): Add equals on object after the implementation of
    // truncatedGutenbergRichter
    @Test
    public void serializesPointSourceData() {
        GemFileParser writer = new GemFileParser();

        ArrayList<GEMSourceData> sources = new ArrayList<GEMSourceData>();
        sources.add(pointSourceData());

        writer.setList(sources);
        writer.writeSource2NrmlFormat(new File(OUTPUT_FILE));

        SourceModelReader reader = new SourceModelReader(OUTPUT_FILE, 0.1);
        assertEquals(sources.size(), reader.read().size());
    }

    /**
     * Compares source model data (for California faults) as derived from the
     * parser that reads the original ASCII files and the source model data read
     * from NRML file generated with the writeSource2NrmlFormat method.
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

        ArrayList<GEMSourceData> sources =
                new ArrayList<GEMSourceData>(modelReader.read());

        assertEquals(faults.getList().size(), sources.size());
        assertSourcesAreEqual(faults.getList(), sources);
    }

}
