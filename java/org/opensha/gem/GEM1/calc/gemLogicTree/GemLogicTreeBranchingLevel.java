package org.opensha.gem.GEM1.calc.gemLogicTree;

import java.io.Serializable;
import java.util.ArrayList;

public class GemLogicTreeBranchingLevel implements Serializable {

    private ArrayList<GemLogicTreeBranch> treeBranchList;
    private int level;
    private String branchingLabel;
    private int appliesTo;

    public GemLogicTreeBranchingLevel() {

        this.treeBranchList = new ArrayList<GemLogicTreeBranch>();
    }

    public GemLogicTreeBranchingLevel(int level, String branchingLabel,
            int appliesTo) {

        this.treeBranchList = new ArrayList<GemLogicTreeBranch>();
        this.level = level;
        this.branchingLabel = branchingLabel;
        this.appliesTo = appliesTo;
    }

    /**
     * 
     * @param treeBranch
     */
    public void addBranch(GemLogicTreeBranch treeBranch) {
        this.treeBranchList.add(treeBranch);
    }

    /**
     * 
     * @return treeBranchList
     */
    public ArrayList<GemLogicTreeBranch> getBranchList() {
        return treeBranchList;
    }

    /**
     * 
     * @param treeBranchList
     */
    public void setTreeBranchList(ArrayList<GemLogicTreeBranch> treeBranchList) {
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
    public GemLogicTreeBranch getBranch(int idx) {
        return this.treeBranchList.get(idx);
    }

}
