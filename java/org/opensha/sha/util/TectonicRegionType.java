/**
 * 
 */
package org.opensha.sha.util;

import java.io.IOException;
import java.io.Serializable;

import org.opensha.commons.util.FileUtils;

/**
 * @author field
 * 
 */
public enum TectonicRegionType implements Serializable {

    /** Active shallow crust tectonic region. */
    ACTIVE_SHALLOW("Active Shallow Crust"),

    /** Stable shallow crust tectonic region. */
    STABLE_SHALLOW("Stable Shallow Crust"),

    /** Subduction Interface tectonic region. */
    SUBDUCTION_INTERFACE("Subduction Interface"),

    /** Subduction IntraSlab tectonic region. */
    SUBDUCTION_SLAB("Subduction IntraSlab"),

    /** Volcanic tectonic region. */
    VOLCANIC("Volcanic");

    private String name;

    private TectonicRegionType(String name) {
        this.name = name;
    }

    /**
     * This gets the TectonicRegionType associated with the given string
     * 
     * @param name
     * @return
     */
    public static TectonicRegionType getTypeForName(String name) {
        if (name == null)
            throw new NullPointerException();
        for (TectonicRegionType trt : TectonicRegionType.values()) {
            if (trt.name.equals(name))
                return trt;
        }
        throw new IllegalArgumentException(
                "TectonicRegionType name does not exist");
    }

    /**
     * This check whether given string is a valid tectonic region
     * 
     * @param name
     * @return
     */
    public static boolean isValidType(String name) {
        boolean answer = false;
        for (TectonicRegionType trt : TectonicRegionType.values()) {
            if (trt.name.equals(name))
                answer = true;
        }
        return answer;
    }

    @Override
    public String toString() {
        return name;
    }

    // public
    public static void main(String[] args) throws IOException {
        System.out.println(isValidType("Active Shallow Crust"));
        String fname = "/tmp/trt.obj";
        TectonicRegionType before = TectonicRegionType.ACTIVE_SHALLOW;
        FileUtils.saveObjectInFile(fname, before);
        TectonicRegionType after =
                (TectonicRegionType) FileUtils.loadObject(fname);
        System.out.println("before: " + before);
        System.out.println("after: " + after);
    }

}
