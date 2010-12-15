package org.gem.engine.logictree;

import java.io.Serializable;
import java.util.ArrayList;

/**
 * Class for defining a logic tree branching level. A branching level consists
 * of a set of {@link LogicTreeBranch} objects (each defining an uncertainty
 * model). A branching level is characterized by a branching level number
 * (representing its position in the logic tree), a branching label (a
 * descriptor), and by an appliesTo value indicating to which previous
 * end-branch model the branching level applies to (NOTE: this feature has never
 * been really implemented or used).
 */
public class LogicTreeBranchingLevel implements Serializable {

    private ArrayList<LogicTreeBranch> treeBranchList;
    private int level;
    private String branchingLabel;
    private int appliesTo;

    /**
     * Empty constructor initializing only list of {@link LogicTreeBranch}
     */
    public LogicTreeBranchingLevel() {

        this.treeBranchList = new ArrayList<LogicTreeBranch>();
    }

    /**
     * Creates new logic tree branching level, given the level number (level),
     * descriptor (branchingLabel), and branch index the branching level applies
     * to (appliesTo)
     */
    public LogicTreeBranchingLevel(int level, String branchingLabel,
            int appliesTo) {

        this.treeBranchList = new ArrayList<LogicTreeBranch>();
        this.level = level;
        this.branchingLabel = branchingLabel;
        this.appliesTo = appliesTo;
    }

    /**
     * Adds {@link LogicTreeBranch}
     */
    public void addBranch(LogicTreeBranch treeBranch) {
        this.treeBranchList.add(treeBranch);
    }

    /**
     * Gets {@link LogicTreeBranch} list
     */
    public ArrayList<LogicTreeBranch> getBranchList() {
        return treeBranchList;
    }

    /**
     * Sets {@link LogicTreeBranch} lists
     */
    public void setTreeBranchList(ArrayList<LogicTreeBranch> treeBranchList) {
        this.treeBranchList = treeBranchList;
    }

    /**
     * Gets branching level number
     */
    public int getLevel() {
        return level;
    }

    /**
     * Sets branching level number
     */
    public void setLevel(int level) {
        this.level = level;
    }

    /**
     * Gets branching label
     */
    public String getBranchingLabel() {
        return branchingLabel;
    }

    /**
     * Sets branching label
     */
    public void setBranchingLabel(String branchingLabel) {
        this.branchingLabel = branchingLabel;
    }

    /**
     * Gets applies to
     */
    public int getAppliesTo() {
        return appliesTo;
    }

    /**
     * Sets applies to
     */
    public void setAppliesTo(int appliesTo) {
        // if (appliesTo >= 0){
        this.appliesTo = appliesTo;
        // }
    }

    /**
     * Gets branch with index idx
     */
    public LogicTreeBranch getBranch(int idx) {
        return this.treeBranchList.get(idx);
    }

    @Override
    public boolean equals(Object obj) {
        if (!(obj instanceof LogicTreeBranchingLevel)) {
            return false;
        }

        LogicTreeBranchingLevel other = (LogicTreeBranchingLevel) obj;

        return treeBranchList.equals(other.treeBranchList)
                && level == other.level
                && branchingLabel.equals(other.branchingLabel)
                && appliesTo == other.appliesTo;
    }
}
