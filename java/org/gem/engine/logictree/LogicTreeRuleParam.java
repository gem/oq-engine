package org.gem.engine.logictree;

public enum LogicTreeRuleParam {

    /** uncertainties on maximum magnitude */
    mMaxGRRelative("mMaxGRRelative"),

    /** uncertainties on GR b value */
    bGRRelative("bGRRelative"),

    /** no uncertainties */
    NONE("noUncertainties");

    private String name;

    private LogicTreeRuleParam(String name) {
        this.name = name;
    }

    /**
     * This gets the GemLogicTreeRule associated with the given string
     * 
     * @param name
     * @return
     */
    public static LogicTreeRuleParam getTypeForName(String name) {
        if (name == null)
            throw new NullPointerException();
        for (LogicTreeRuleParam trt : LogicTreeRuleParam.values()) {
            if (trt.name.equals(name))
                return trt;
        }
        throw new IllegalArgumentException("Rule parameter name: " + name
                + " does not exist");
    }

    /**
     * This check whether given string is a valid GemLogicTreeRule
     * 
     * @param name
     * @return
     */
    public static boolean isValidType(String name) {
        boolean answer = false;
        for (LogicTreeRuleParam trt : LogicTreeRuleParam.values()) {
            if (trt.name.equals(name))
                answer = true;
        }
        return answer;
    }

    @Override
    public String toString() {
        return name;
    }

}
