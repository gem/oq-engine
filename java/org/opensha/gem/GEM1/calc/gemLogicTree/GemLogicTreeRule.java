package org.opensha.gem.GEM1.calc.gemLogicTree;

public class GemLogicTreeRule {
	
	private GemLogicTreeRuleParam rule;
	
	private double val;
	
	public GemLogicTreeRule(GemLogicTreeRuleParam rule, double val){
		
		this.rule = rule;
		this.val = val;
		
	}

	public GemLogicTreeRuleParam getRuleName() {
		return rule;
	}

	public double getVal() {
		return val;
	}

}
