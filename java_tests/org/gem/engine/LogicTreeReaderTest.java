package org.gem.engine;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.util.HashMap;
import java.util.Map;

import org.gem.engine.logictree.LogicTree;
import org.gem.engine.logictree.LogicTreeBranch;
import org.gem.engine.logictree.LogicTreeBranchingLevel;
import org.gem.engine.logictree.LogicTreeRule;
import org.gem.engine.logictree.LogicTreeRuleParam;
import org.junit.Test;
import org.opensha.sha.util.TectonicRegionType;

public class LogicTreeReaderTest {

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
                new LogicTreeReader(
                        "java_tests/data/source_model_logic_tree.xml");
        Map<String, LogicTree> sourceModelLogicTreeHashMapRead =
                sourceModelLogicTreeReader.read();

        assertTrue(sourceModelLogicTreeHashMap.keySet().size() == sourceModelLogicTreeHashMapRead
                .keySet().size());
        for (String key : sourceModelLogicTreeHashMap.keySet())
            assertEquals(sourceModelLogicTreeHashMap.get(key),
                    sourceModelLogicTreeHashMapRead.get(key));

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
                new LogicTreeReader("java_tests/data/gmpe_logic_tree.xml");
        Map<String, LogicTree> gmpeLogicTreeHashMapRead =
                gmpeLogicTreeReader.read();

        assertTrue(gmpeLogicTreeHashMap.keySet().size() == gmpeLogicTreeHashMapRead
                .keySet().size());
        for (String key : gmpeLogicTreeHashMap.keySet())
            assertEquals(gmpeLogicTreeHashMap.get(key),
                    gmpeLogicTreeHashMapRead.get(key));
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
        gmpeLogicTreeActiveShallow.addBranchingLevel(branchingLevel);
        gmpeLogicTreeHashMap.put(TectonicRegionType.ACTIVE_SHALLOW.toString(),
                gmpeLogicTreeActiveShallow);

        LogicTree gmpeLogicTreeSubductionInterface = new LogicTree();
        branchingLevel = new LogicTreeBranchingLevel(1, "", 0);
        branchingLevel.addBranch(new LogicTreeBranch(1,
                "McVerryetal_2000_AttenRel", 1.0));
        gmpeLogicTreeSubductionInterface.addBranchingLevel(branchingLevel);
        gmpeLogicTreeHashMap.put(
                TectonicRegionType.SUBDUCTION_INTERFACE.toString(),
                gmpeLogicTreeSubductionInterface);

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
        sourceModelLogicTree.addBranchingLevel(branchingLevel);

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
        sourceModelLogicTree.addBranchingLevel(branchingLevel);

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
        sourceModelLogicTree.addBranchingLevel(branchingLevel);

        HashMap<String, LogicTree> sourceModelLogicTreeHashMap =
                new HashMap<String, LogicTree>();
        sourceModelLogicTreeHashMap.put("1", sourceModelLogicTree);
        return sourceModelLogicTreeHashMap;
    }
}
