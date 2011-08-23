package org.gem.engine.hazard.parsers;

import static org.gem.engine.hazard.parsers.SourceModelTestHelper.areaSourceData;
import static org.gem.engine.hazard.parsers.SourceModelTestHelper.assertSourcesAreEqual;
import static org.gem.engine.hazard.parsers.SourceModelTestHelper.complexSourceData;
import static org.gem.engine.hazard.parsers.SourceModelTestHelper.pointSourceData;
import static org.gem.engine.hazard.parsers.SourceModelTestHelper.simpleFaultSourceData;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.assertNull;

import java.util.ArrayList;
import java.util.List;
import java.io.File;

import org.junit.Test;
import org.junit.Before;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

import org.dom4j.DocumentException;

import org.gem.engine.XMLValidationError;
import org.gem.engine.XMLMismatchError;

public class SourceModelReaderTest {

    public static final String TEST_SOURCE_MODEL_FILE =
        "java_tests/data/source_model.xml";
    public static final String INVALID_TEST_SOURCE_MODEL_FILE =
            "tests/data/invalid/source_model1.xml";
    public static final double MFD_BIN_WIDTH = 0.1;
    public static final String MISMATCHED_FILE =
            "openquake/nrml/schema/examples/logic-tree-gmpe.xml";

    @Before
    public void setUp() {
        System.setProperty("openquake.nrml.schema",
                           new File("openquake/nrml/schema/nrml.xsd").getAbsolutePath());
    }

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
                new SourceModelReader(TEST_SOURCE_MODEL_FILE, MFD_BIN_WIDTH);

        List<GEMSourceData> srcListRead = srcModelReader.read();

        assertEquals(srcList.size(), srcListRead.size());
        assertSourcesAreEqual(srcListRead, srcList);
    }

    /**
     * This test was written to prevent a bug from being reintroduced.
     *
     * Previously, if the read() method was called multiple times, the source data
     * list would simply be appended. This would cause the reader to build a list
     * containing a bunch of duplicates.
     */
    @Test
    public void testSourceListResets() {
        SourceModelReader srcModelReader =
            new SourceModelReader(TEST_SOURCE_MODEL_FILE, MFD_BIN_WIDTH);

        assertEquals(4, srcModelReader.read().size());

        // previously, calling read again would duplicate the sources
        // read from the test file and double the list size
        srcModelReader.read();

        assertEquals(4, srcModelReader.read().size());
    }

    void checkFailsValidation(String path) {
        boolean threw = false;

        try {
            SourceModelReader reader = new SourceModelReader(path, MFD_BIN_WIDTH);

            reader.read();
        }
        catch (XMLValidationError e) {
            threw = true;
            assertEquals(new File(path).getAbsolutePath(), e.getFileName());
            assertTrue("Throws a DocumentException",
                       e.getCause() instanceof DocumentException);
            assertNull(e.getCause().getCause());
        }

        assertTrue("Parsing threw a XMLValidationError", threw);
    }

    /**
     * Checks schema validation for source model logic trees
     */
    @Test
    public void sourceModelSchemaValidationTest() {
        checkFailsValidation(INVALID_TEST_SOURCE_MODEL_FILE);
    }

    /**
     * Test that a document mismatch throws a meaningful error
     */
    @Test
    public void documentMismatchTest() {
        boolean threw = false;

        try {
            SourceModelReader reader = new SourceModelReader(MISMATCHED_FILE, MFD_BIN_WIDTH);

            reader.read();
        }
        catch (XMLMismatchError e) {
            threw = true;
            assertEquals("logicTreeSet", e.getActualTag());
            assertEquals("sourceModel", e.getExpectedTag());
        }

        assertTrue("Parsing threw a XMLMismatchError", threw);
    }
}
