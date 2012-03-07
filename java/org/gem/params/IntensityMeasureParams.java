/*
    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify it
    under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
*/

package org.gem.params;

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
