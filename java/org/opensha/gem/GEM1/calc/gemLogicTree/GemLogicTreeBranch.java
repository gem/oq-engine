package org.opensha.gem.GEM1.calc.gemLogicTree;

import java.io.Serializable;

public class GemLogicTreeBranch implements Serializable{

	private int relativeID;
	private String branchingValue;
	private double weight;
	private String nameInputFile;
	private GemLogicTreeRule rule;
	
	
	public GemLogicTreeBranch(){
		
	}
	
	public GemLogicTreeBranch(int relativeID, String branchingValue, double weight){
		this.relativeID = relativeID;
		this.branchingValue = branchingValue;
		this.weight = weight;
		
	}
	
	public int getRelativeID() {
		return relativeID;
	}
	public void setRelativeID(int relativeID) {
		this.relativeID = relativeID;
	}
	public String getBranchingValue() {
		return branchingValue;
	}
	public void setBranchingValue(String branchingValue) {
		this.branchingValue = branchingValue;
	}
	public String getNameInputFile() {
		return nameInputFile;
	}
	public void setNameInputFile(String nameInputFile) {
		this.nameInputFile = nameInputFile;
	}
	/**
	 * 
	 * @return weight
	 */
	public double getWeight() {
		return weight;
	}
	/**
	 * 
	 * @param weight
	 */
	public void setWeight(double weight) {
		this.weight = weight;
	}

	public GemLogicTreeRule getRule() {
		return rule;
	}

	public void setRule(GemLogicTreeRule rule) {
		this.rule = rule;
	}
	
}
