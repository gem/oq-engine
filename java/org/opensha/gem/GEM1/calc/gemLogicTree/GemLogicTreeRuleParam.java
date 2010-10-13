package org.opensha.gem.GEM1.calc.gemLogicTree;

public enum GemLogicTreeRuleParam {

    /** uncertainties on maximum magnitude */
    mMaxGRRelative("mMaxGRRelative"),

    /** uncertainties on GR b value */
    bGRRelative("bGRRelative");

    private String name;

    private GemLogicTreeRuleParam(String name) {
        this.name = name;
    }

    /**
     * This gets the GemLogicTreeRule associated with the given string
     * 
     * @param name
     * @return
     */
    public static GemLogicTreeRuleParam getTypeForName(String name) {
        if (name == null)
            throw new NullPointerException();
        for (GemLogicTreeRuleParam trt : GemLogicTreeRuleParam.values()) {
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
        for (GemLogicTreeRuleParam trt : GemLogicTreeRuleParam.values()) {
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
