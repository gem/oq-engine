package org.gem.engine;

import static org.junit.Assert.assertTrue;

import java.util.HashMap;

import org.gem.engine.logictree.LogicTree;
import org.gem.engine.logictree.LogicTreeBranch;
import org.gem.engine.logictree.LogicTreeBranchingLevel;
import org.gem.engine.logictree.LogicTreeRule;
import org.gem.engine.logictree.LogicTreeRuleParam;
import org.junit.Test;
import org.opensha.sha.util.TectonicRegionType;

public class LogicTreeReaderTest {

    @Test
    public void readSourceModelLogicTreeTest() {

        HashMap<String, LogicTree> sourceModelLogicTreeHashMap =
                getSourceModelLogicTree();

        LogicTreeReader sourceModelLogicTreeReader =
                new LogicTreeReader(
                        "java_tests/data/source_model_logic_tree.xml");

        assertTrue(sourceModelLogicTreeHashMap.keySet().size() == sourceModelLogicTreeReader
                .getLogicTreeHashMap().keySet().size());
        for (String key : sourceModelLogicTreeHashMap.keySet())
            assertTrue(sourceModelLogicTreeHashMap.get(key).equals(
                    sourceModelLogicTreeReader.getLogicTreeHashMap().get(key)));

    }

    @Test
    public void readGmpeLogicTreeTest() {
        HashMap<String, LogicTree> gmpeLogicTreeHashMap =
                getGmpeLogicTreeHashMap();

        LogicTreeReader gmpeLogicTreeReader =
                new LogicTreeReader("java_tests/data/gmpe_logic_tree.xml");

        assertTrue(gmpeLogicTreeHashMap.keySet().size() == gmpeLogicTreeReader
                .getLogicTreeHashMap().keySet().size());
        for (String key : gmpeLogicTreeHashMap.keySet())
            assertTrue(gmpeLogicTreeHashMap.get(key).equals(
                    gmpeLogicTreeReader.getLogicTreeHashMap().get(key)));
    }

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
