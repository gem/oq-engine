package org.gem.engine.logictree;

import java.io.Serializable;

public class LogicTreeRule implements Serializable {

    private final LogicTreeRuleParam rule;

    private final double val;

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

    @Override
    public boolean equals(Object obj) {
        if (!(obj instanceof LogicTreeRule))
            return false;

        LogicTreeRule other = (LogicTreeRule) obj;

        return val == other.val
                && rule.toString().equals(other.rule.toString());
    }

}
