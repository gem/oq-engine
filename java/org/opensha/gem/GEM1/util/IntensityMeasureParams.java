package org.opensha.gem.GEM1.util;

import org.opensha.commons.param.StringParameter;

public enum IntensityMeasureParams {

    /** Intensity measure type */
    INTENSITY_MEAS_TYPE("Intensity measure type");

    private String name;

    private IntensityMeasureParams(String name) {
        this.name = name;
    }

    /**
     * This gets the GemSourceType associated with the given string
     * 
     * @param name
     * @return
     */
    public static IntensityMeasureParams getTypeForName(String name) {
        if (name == null)
            throw new NullPointerException();
        for (IntensityMeasureParams trt : IntensityMeasureParams.values()) {
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
        for (IntensityMeasureParams trt : IntensityMeasureParams.values()) {
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
