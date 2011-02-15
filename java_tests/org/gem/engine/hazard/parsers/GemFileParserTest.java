package org.gem.engine.hazard.parsers;

import static org.gem.engine.hazard.parsers.SourceModelTestHelper.areaSourceData;
import static org.gem.engine.hazard.parsers.SourceModelTestHelper.assertSourcesAreEqual;
import static org.gem.engine.hazard.parsers.SourceModelTestHelper.complexSourceData;
import static org.gem.engine.hazard.parsers.SourceModelTestHelper.pointSourceData;
import static org.gem.engine.hazard.parsers.SourceModelTestHelper.simpleFaultSourceData;
import static org.junit.Assert.assertEquals;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

import org.gem.engine.hazard.models.nshmp.us.NshmpCaliforniaFaultData;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class GemFileParserTest
{

    private static final String OUTPUT_FILE = "output.txt";
    private static final String FILENAME = "california-fault.dat";

    @Before
    public void setUp()
    {
        new File(FILENAME).delete();
        new File(OUTPUT_FILE).delete();
    }

    @After
    public void tearDown()
    {
        new File(FILENAME).delete();
        // new File(OUTPUT_FILE).delete();
    }

    @Test
    public void serializesSimpleSourceData()
    {
        ArrayList<GEMSourceData> sources = new ArrayList<GEMSourceData>();
        sources.add(simpleFaultSourceData());

        writeSources(sources);
        assertReadedSourcesAreEqualTo(sources);
    }

    @Test
    public void serializesComplexSourceData()
    {
        ArrayList<GEMSourceData> sources = new ArrayList<GEMSourceData>();
        sources.add(complexSourceData());

        writeSources(sources);
        assertReadedSourcesAreEqualTo(sources);
    }

    @Test
    public void serializesAreaSourceData()
    {
        ArrayList<GEMSourceData> sources = new ArrayList<GEMSourceData>();
        sources.add(areaSourceData());

        writeSources(sources);
        assertReadedSourcesAreEqualTo(sources);
    }

    @Test
    public void serializesPointSourceData()
    {
        ArrayList<GEMSourceData> sources = new ArrayList<GEMSourceData>();
        sources.add(pointSourceData());

        writeSources(sources);
        assertReadedSourcesAreEqualTo(sources);
    }

    private void writeSources(ArrayList<GEMSourceData> sources)
    {
        GemFileParser writer = new GemFileParser();

        writer.setList(sources);
        writer.writeSource2NrmlFormat(new File(OUTPUT_FILE));
    }

    private void assertReadedSourcesAreEqualTo(ArrayList<GEMSourceData> sources)
    {
        SourceModelReader reader = new SourceModelReader(OUTPUT_FILE, 0.1);
        List<GEMSourceData> readedSources = reader.read();

        assertEquals(sources.size(), readedSources.size());
        assertSourcesAreEqual(sources, readedSources);
    }

    /**
     * Compares source model data (for California faults) as derived from the parser that reads the original ASCII files
     * and the source model data read from NRML file generated with the writeSource2NrmlFormat method.
     */
    @Test
    public void serializeCaliforniaFaultData2Nrml()
    {
        NshmpCaliforniaFaultData faults = new NshmpCaliforniaFaultData("java_tests/data/nshmp/CA/");

        faults.read(-90.0, +90.0, -180.0, +180.0);

        File file = new File("california_fault_model.xml");
        faults.writeSource2NrmlFormat(file);

        SourceModelReader modelReader = new SourceModelReader(file.getAbsolutePath(), 0.1);

        ArrayList<GEMSourceData> sources = new ArrayList<GEMSourceData>(modelReader.read());

        assertEquals(faults.getList().size(), sources.size());
        assertSourcesAreEqual(faults.getList(), sources);
    }

}
