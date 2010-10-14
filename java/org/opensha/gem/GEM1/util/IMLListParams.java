package org.opensha.gem.GEM1.util;

public enum IMLListParams {

    /** Intensity measure level list */
    IML_LIST("Intensity measure level list");

    private String name;

    private IMLListParams(String name) {
        this.name = name;
    }

    /**
     * This gets the GemSourceType associated with the given string
     * 
     * @param name
     * @return
     */
    public static IMLListParams getTypeForName(String name) {
        if (name == null)
            throw new NullPointerException();
        for (IMLListParams trt : IMLListParams.values()) {
            if (trt.name.equals(name))
                return trt;
        }
        throw new IllegalArgumentException(
                "Area source parameter name does not exist");
    }

    /**
     * This check whether given string is a valid Gem source type
     * 
     * @param name
     * @return
     */
    public static boolean isValidType(String name) {
        boolean answer = false;
        for (IMLListParams trt : IMLListParams.values()) {
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
