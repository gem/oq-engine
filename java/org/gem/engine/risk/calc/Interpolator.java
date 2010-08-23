/*
 * [COPYRIGHT]
 *
 * [NAME] is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this software; if not, write to the Free
 * Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA, or see the FSF site: http://www.fsf.org.
 */

package org.gem.engine.risk.calc;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.gem.engine.risk.data.DiscreteFunction;

/**
 * Interpolates values for a given function.
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.3.7.
 * 
 * @author Andrea Cerisara
 * @version $Id: Interpolator.java 583 2010-07-21 12:51:07Z acerisara $
 */
public class Interpolator
{

    private List<Double> domain;
    private final DiscreteFunction function;

    /**
     * @param function the function used for interpolation
     */
    public Interpolator(DiscreteFunction function)
    {
        this.function = function;
        this.domain = new ArrayList<Double>(function.getDomain());
    }

    /**
     * Interpolates the given value.
     * 
     * @param value the value to interpolate
     * @return the interpolated value
     */
    public double interpolate(double value)
    {
        if (value <= domain.get(0))
        {
            throw new IllegalArgumentException("It is not possible to interpolate on first value!");
        }

        if (value >= domain.get(domain.size() - 1))
        {
            throw new IllegalArgumentException("It is not possible to interpolate on last value!");
        }

        int index = Arrays.binarySearch(domain.toArray(), value);
        index = index >= 0 ? index : (index * -1) - 2;

        double x = (domain.get(index + 1) - value) * function.getFor(domain.get(index));
        double y = (value - domain.get(index)) * function.getFor(domain.get(index + 1));

        return (x + y) / (domain.get(index + 1) - domain.get(index));
    }

}
