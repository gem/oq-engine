package org.gem.engine.logictree;

import java.io.Serializable;

/**
 * Class for logic tree branch definition. A logic tree branch is defined in
 * terms of a branch number, a branch value (string describing an uncertainty
 * model), and a weight (representing the likelihood associated to the
 * uncertainty model). A logic tree branch can additionally contain a file name
 * (representing an uncertainty model) or a logic tree rule (representing
 * uncertainty on a particular model parameter)
 */
public class LogicTreeBranch implements Serializable {

    private int relativeID;
    private String branchingValue;
    private double weight;
    private String nameInputFile;
    private LogicTreeRule rule;

    public LogicTreeBranch() {

    }

    /**
     * Creates a new Logic Tree branch, given the branch number (relativeID), an
     * uncertainty model (branchingValue), and a weight. The input file field
     */
    public LogicTreeBranch(int relativeID, String branchingValue, double weight) {
        this.relativeID = relativeID;
        this.branchingValue = branchingValue;
        this.weight = weight;
        nameInputFile = "";
        rule = new LogicTreeRule(LogicTreeRuleParam.NONE, 0.0);
    }

    /**
     * Gets branch number
     */
    public int getRelativeID() {
        return relativeID;
    }

    /**
     * Sets branch number
     */
    public void setRelativeID(int relativeID) {
        this.relativeID = relativeID;
    }

    /**
     * Gets uncertainty model
     */
    public String getBranchingValue() {
        return branchingValue;
    }

    /**
     * Sets uncertainty model
     */
    public void setBranchingValue(String branchingValue) {
        this.branchingValue = branchingValue;
    }

    /**
     * Gets input file
     */
    public String getNameInputFile() {
        return nameInputFile;
    }

    /**
     * Sets input file
     */
    public void setNameInputFile(String nameInputFile) {
        this.nameInputFile = nameInputFile;
    }

    /**
     * Gets branch weight
     */
    public double getWeight() {
        return weight;
    }

    /**
     * Sets branch weight
     */
    public void setWeight(double weight) {
        this.weight = weight;
    }

    /**
     * Gets logic tree rule
     */
    public LogicTreeRule getRule() {
        return rule;
    }

    /**
     * Sets logic tree rule
     */
    public void setRule(LogicTreeRule rule) {
        this.rule = rule;
    }

    @Override
    public boolean equals(Object obj) {
        if (!(obj instanceof LogicTreeBranch)) {
            return false;
        }

        LogicTreeBranch other = (LogicTreeBranch) obj;

        return relativeID == other.relativeID
                && branchingValue.equals(other.branchingValue)
                && weight == other.weight
                && nameInputFile.equals(other.nameInputFile)
                && rule.equals(other.rule);
    }

}
