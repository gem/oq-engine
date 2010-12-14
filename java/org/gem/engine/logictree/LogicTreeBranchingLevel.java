package org.gem.engine.logictree;

import java.io.Serializable;
import java.util.ArrayList;

public class LogicTreeBranchingLevel implements Serializable {

    private ArrayList<LogicTreeBranch> treeBranchList;
    private int level;
    private String branchingLabel;
    private int appliesTo;

    public LogicTreeBranchingLevel() {

        this.treeBranchList = new ArrayList<LogicTreeBranch>();
    }

    public LogicTreeBranchingLevel(int level, String branchingLabel,
            int appliesTo) {

        this.treeBranchList = new ArrayList<LogicTreeBranch>();
        this.level = level;
        this.branchingLabel = branchingLabel;
        this.appliesTo = appliesTo;
    }

    /**
     * 
     * @param treeBranch
     */
    public void addBranch(LogicTreeBranch treeBranch) {
        this.treeBranchList.add(treeBranch);
    }

    /**
     * 
     * @return treeBranchList
     */
    public ArrayList<LogicTreeBranch> getBranchList() {
        return treeBranchList;
    }

    /**
     * 
     * @param treeBranchList
     */
    public void setTreeBranchList(ArrayList<LogicTreeBranch> treeBranchList) {
        this.treeBranchList = treeBranchList;
    }

    /**
     * 
     * @return level
     */
    public int getLevel() {
        return level;
    }

    public void setLevel(int level) {
        this.level = level;
    }

    public String getBranchingLabel() {
        return branchingLabel;
    }

    public void setBranchingLabel(String branchingLabel) {
        this.branchingLabel = branchingLabel;
    }

    public int getAppliesTo() {
        return appliesTo;
    }

    public void setAppliesTo(int appliesTo) {
        // if (appliesTo >= 0){
        this.appliesTo = appliesTo;
        // }
    }

    /**
     * 
     * @param idx
     * @return
     */
    public LogicTreeBranch getBranch(int idx) {
        return this.treeBranchList.get(idx);
    }

    @Override
    public boolean equals(Object obj) {
        if (!(obj instanceof LogicTreeBranchingLevel))
            return false;

        LogicTreeBranchingLevel other = (LogicTreeBranchingLevel) obj;

        return treeBranchList.equals(other.treeBranchList)
                && level == other.level
                && branchingLabel.equals(other.branchingLabel)
                && appliesTo == other.appliesTo;
    }
}
