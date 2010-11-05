package org.gem.engine.logictree;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Random;

public interface LogicTreeAPI<Element> extends Iterable<Element> {

    /**
	 * 
	 */
    public void addBranchingLevel(LogicTreeBranchingLevel branLev);

    public ArrayList<LogicTreeBranchingLevel> getBranchingLevelsList();

    public LogicTreeBranchingLevel getBranchingLevel(int idx);

    public void addEBMapping(String str, Element obj);

    public HashMap<String, Element> getEBMap();

    public void setModelName(String str);

    public String getModelName();

    public double getWeight(String lab);

    public double getTotWeight(String lab);

    public void saveGemLogicTreeModel(String fileName) throws Exception;

    public int sampleBranchingLevel(int branchingLevelIndex, Random rn);

}
