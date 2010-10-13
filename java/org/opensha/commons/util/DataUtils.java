/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.commons.util;

/**
 * This class provides various data processing utilities.
 * 
 * @author Peter Powers
 * @version $Id:$
 */
public class DataUtils {

    // no instantiation
    private DataUtils() {
    }

    /**
     * Validates the domain of a <code>double</code> data set. Method verifies
     * that data values all fall within a specified minimum and maximum range
     * (inclusive).
     * 
     * @param data
     *            to validate
     * @param min
     *            minimum range value
     * @param max
     *            maximum range value
     * @throws IllegalArgumentException
     *             if a data value is out of range
     */
    public final static void validate(double[] data, double min, double max)
            throws IllegalArgumentException {
        double value;
        for (int i = 0; i < data.length; i++) {
            value = data[i];
            if (value > max || value < min) {
                throw new IllegalArgumentException("Data value (" + value
                        + ") at position " + (i + 1) + " is out of range.");
            }
        }
    }

    /**
     * Verifies that a <code>double</code> data value falls within a specified
     * minimum and maximum range (inclusive).
     * 
     * @param value
     *            to check
     * @param min
     *            minimum range value
     * @param max
     *            minimum range value
     * @throws IllegalArgumentException
     *             if value is out of range
     */
    public final static void validate(double value, double min, double max) {
        if (value > max || value < min) {
            throw new IllegalArgumentException("Value (" + value
                    + ") is out of range.");
        }
    }

    /**
     * Returns the percent difference between two values.
     * 
     */
    public static double getPercentDiff(double testVal, double targetVal) {
        double result = 0;
        if (targetVal != 0)
            result = (StrictMath.abs(testVal - targetVal) / targetVal) * 100d;

        return result;
    }

}
