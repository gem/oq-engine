package org.gem.engine;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.assertNull;

import java.util.HashMap;
import java.util.Map;
import java.io.File;

import org.gem.engine.logictree.LogicTree;
import org.gem.engine.logictree.LogicTreeBranch;
import org.gem.engine.logictree.LogicTreeBranchingLevel;
import org.gem.engine.logictree.LogicTreeRule;
import org.gem.engine.logictree.LogicTreeRuleParam;
import org.junit.Test;
import org.junit.Before;
import org.opensha.sha.util.TectonicRegionType;
import org.dom4j.DocumentException;

public class LogicTreeReaderTest {

    /**
     * Logic Tree Source Model test file.
     */
    public static final String LT_SRC_MODEL_TEST_FILE =
            "openquake/nrml/schema/examples/logic-tree-source-model.xml";

    public static final String LT_GMPE_TEST_FILE =
            "openquake/nrml/schema/examples/logic-tree-gmpe.xml";

    public static final String LT_INVALID_SRC_MODEL_TEST_FILE =
            "tests/data/invalid/source_model_logic_tree.xml";

    public static final String LT_INVALID_GMPE_TEST_FILE =
            "tests/data/invalid/gmpe_logic_tree.xml";

    public static final String LT_MISMATCHED_TEST_FILE =
            "openquake/nrml/schema/examples/source-model.xml";

    @Before
    public void setUp() {
        System.setProperty(
            "openquake.nrml.schema",
            new File("openquake/nrml/schema/nrml.xsd").getAbsolutePath());
    }

    /**
     * Compares source model logic tree as derived by reading nrML file with
     * source model logic tree defined by hand with the same data contained in
     * the nrML file
     */
    @Test
    public void readSourceModelLogicTreeTest() {

        HashMap<String, LogicTree> sourceModelLogicTreeHashMap =
                getSourceModelLogicTree();

        LogicTreeReader sourceModelLogicTreeReader =
                new LogicTreeReader(LT_SRC_MODEL_TEST_FILE);
        Map<String, LogicTree> sourceModelLogicTreeHashMapRead =
                sourceModelLogicTreeReader.read();

        assertTrue(sourceModelLogicTreeHashMap.keySet().size() == sourceModelLogicTreeHashMapRead
                .keySet().size());
        for (String key : sourceModelLogicTreeHashMap.keySet()) {
            LogicTree expected = sourceModelLogicTreeHashMap.get(key);
            LogicTree actual = sourceModelLogicTreeHashMapRead.get(key);

            assertEquals(expected, actual);
        }

    }

    /**
     * Compares gmpe logic tree as derived by reading nrML file with gmpe logic
     * tree defined by hand with the same data contained in the nrML file
     */
    @Test
    public void readGmpeLogicTreeTest() {
        HashMap<String, LogicTree> gmpeLogicTreeHashMap =
                getGmpeLogicTreeHashMap();

        LogicTreeReader gmpeLogicTreeReader =
                new LogicTreeReader(LT_GMPE_TEST_FILE);
        Map<String, LogicTree> gmpeLogicTreeHashMapRead =
                gmpeLogicTreeReader.read();

        assertTrue(gmpeLogicTreeHashMap.keySet().size() == gmpeLogicTreeHashMapRead
                .keySet().size());
        for (String key : gmpeLogicTreeHashMap.keySet()) {
            LogicTree expected = gmpeLogicTreeHashMap.get(key);
            LogicTree actual = gmpeLogicTreeHashMapRead.get(key);

            assertEquals(expected, actual);
        }
    }

    /**
     * Defines and gets hash map containing two logic trees for GMPEs, for two
     * different tectonic settings (active shallow crust, subduction interface).
     * The logic tree for active shallow crust contains two GMPEs with equal
     * weight, while the logic tree for subduction interface contains only one
     * gmpe with full weight
     */
    private HashMap<String, LogicTree> getGmpeLogicTreeHashMap() {

        HashMap<String, LogicTree> gmpeLogicTreeHashMap =
                new HashMap<String, LogicTree>();

        LogicTree gmpeLogicTreeActiveShallow = new LogicTree();
        LogicTreeBranchingLevel branchingLevel =
                new LogicTreeBranchingLevel(1, "", 0);
        branchingLevel
                .addBranch(new LogicTreeBranch(1, "BA_2008_AttenRel", 0.5));
        branchingLevel
                .addBranch(new LogicTreeBranch(2, "CB_2008_AttenRel", 0.5));
        gmpeLogicTreeActiveShallow.appendBranchingLevel(branchingLevel);
        gmpeLogicTreeHashMap.put(TectonicRegionType.ACTIVE_SHALLOW.toString(),
                gmpeLogicTreeActiveShallow);

        LogicTree gmpeLogicTreeSubductionInterface = new LogicTree();
        branchingLevel = new LogicTreeBranchingLevel(1, "", 0);
        branchingLevel.addBranch(new LogicTreeBranch(1,
                "McVerryetal_2000_AttenRel", 1.0));
        gmpeLogicTreeSubductionInterface.appendBranchingLevel(branchingLevel);
        gmpeLogicTreeHashMap.put(TectonicRegionType.SUBDUCTION_INTERFACE
                .toString(), gmpeLogicTreeSubductionInterface);

        return gmpeLogicTreeHashMap;
    }

    /**
     * Defines and gets hash map containing one source model logic tree. The
     * source model logic tree containes three branching levels, the first
     * describing two alternative source models, the second branching level
     * defines uncertainties on the Gutenberg-Richter maximum magnitude, while
     * the third uncertainties on Gutenberg-Richter b value
     */
    private HashMap<String, LogicTree> getSourceModelLogicTree() {

        LogicTree sourceModelLogicTree = new LogicTree();

        LogicTreeBranchingLevel branchingLevel =
                new LogicTreeBranchingLevel(1, "", 0);
        LogicTreeBranch branch =
                new LogicTreeBranch(1, "source_model_1.xml", 0.5);
        branch.setNameInputFile("source_model_1.xml");
        branchingLevel.addBranch(branch);
        branch = new LogicTreeBranch(2, "source_model_2.xml", 0.5);
        branch.setNameInputFile("source_model_2.xml");
        branchingLevel.addBranch(branch);
        sourceModelLogicTree.appendBranchingLevel(branchingLevel);

        branchingLevel = new LogicTreeBranchingLevel(2, "", 0);
        branch = new LogicTreeBranch(1, "0.2", 0.2);
        branch.setRule(new LogicTreeRule(LogicTreeRuleParam.mMaxGRRelative,
                +0.2));
        branchingLevel.addBranch(branch);
        branch = new LogicTreeBranch(2, "0.0", 0.6);
        branch.setRule(new LogicTreeRule(LogicTreeRuleParam.mMaxGRRelative,
                +0.0));
        branchingLevel.addBranch(branch);
        branch = new LogicTreeBranch(3, "-0.2", 0.2);
        branch.setRule(new LogicTreeRule(LogicTreeRuleParam.mMaxGRRelative,
                -0.2));
        branchingLevel.addBranch(branch);
        sourceModelLogicTree.appendBranchingLevel(branchingLevel);

        branchingLevel = new LogicTreeBranchingLevel(3, "", 0);
        branch = new LogicTreeBranch(1, "0.1", 0.2);
        branch.setRule(new LogicTreeRule(LogicTreeRuleParam.bGRRelative, +0.1));
        branchingLevel.addBranch(branch);
        branch = new LogicTreeBranch(2, "0.0", 0.6);
        branch.setRule(new LogicTreeRule(LogicTreeRuleParam.bGRRelative, 0.0));
        branchingLevel.addBranch(branch);
        branch = new LogicTreeBranch(3, "-0.1", 0.2);
        branch.setRule(new LogicTreeRule(LogicTreeRuleParam.bGRRelative, -0.1));
        branchingLevel.addBranch(branch);
        sourceModelLogicTree.appendBranchingLevel(branchingLevel);

        HashMap<String, LogicTree> sourceModelLogicTreeHashMap =
                new HashMap<String, LogicTree>();
        sourceModelLogicTreeHashMap.put("1", sourceModelLogicTree);
        return sourceModelLogicTreeHashMap;
    }

    void checkFailsValidation(String path) {
        boolean threw = false;

        try {
            LogicTreeReader reader = new LogicTreeReader(path);

            reader.read();
        }
        catch (RuntimeException e) {
            threw = true;
            assertTrue("Throws a DocumentException",
                       e.getCause() instanceof DocumentException);
            assertNull(e.getCause().getCause());
        }

        assertTrue("Parsing threw an exception", threw);
    }

    /**
     * Checks schema validation for source model logic trees
     */
    @Test
    public void sourceModelSchemaValidationTest() {
        checkFailsValidation(LT_INVALID_SRC_MODEL_TEST_FILE);
    }

    /**
     * Checks schema validation for GMPE logic trees
     */
    @Test
    public void gmpeSchemaValidationTest() {
        checkFailsValidation(LT_INVALID_GMPE_TEST_FILE);
    }

    /**
     * Test that a document mismatch throws a meaningful error
     */
    @Test
    public void documentMismatchTest() {
        boolean threw = false;

        try {
            LogicTreeReader reader = new LogicTreeReader(LT_MISMATCHED_TEST_FILE);

            reader.read();
        }
        catch (XMLMismatchError e) {
            threw = true;
            assertEquals("sourceModel", e.getActualTag());
            assertEquals("logicTreeSet", e.getExpectedTag());
        }

        assertTrue("Parsing threw a XMLMismatchError", threw);
    }
}
