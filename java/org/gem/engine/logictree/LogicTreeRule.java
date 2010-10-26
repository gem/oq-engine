package org.gem.engine.logictree;

import java.io.Serializable;

public class LogicTreeRule implements Serializable {

    private LogicTreeRuleParam rule;

    private double val;

    public LogicTreeRule(LogicTreeRuleParam rule, double val) {

        this.rule = rule;
        this.val = val;

    }

    public LogicTreeRuleParam getRuleName() {
        return rule;
    }

    public double getVal() {
        return val;
    }

}
