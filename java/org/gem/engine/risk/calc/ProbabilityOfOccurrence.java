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
import java.util.List;

import org.gem.engine.risk.data.DiscreteFunction;

/**
 * Computes the probability of occurrence (PO) for the mean loss (ML).
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.3.7.
 * 
 * @author Andrea Cerisara
 * @version $Id: ProbabilityOfOccurrence.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class ProbabilityOfOccurrence
{

    private List<Double> losses;
    private final Interpolator interpolator;
    private final DiscreteFunction lossCurve;

    /**
     * @param curve the loss or loss ratio curve to use
     * @param interpolator the object used for interpolating values
     */
    public ProbabilityOfOccurrence(Interpolator interpolator, DiscreteFunction curve)
    {
        this.lossCurve = curve;
        this.interpolator = interpolator;
        this.losses = new ArrayList<Double>(curve.getDomain());
    }

    /**
     * Computes the probability of occurrence for the given probability of exceedance (PE).
     * 
     * @param value the probability of exceedance to use 
     * @return the probability of occurrence
     */
    public double compute(double value)
    {
        double L1 = L1(value);
        double L2 = L2(value);

        return PEL1(L1, value) - PEL2(L2, value);
    }

    private double L1(double value)
    {
        return value <= ratioAt(0) ? 0.0 : (value + ratioAt(losses.indexOf(value) - 1)) / 2;
    }

    private double L2(double value)
    {
        return value >= ratioAt(lastElement()) ? 1 : (value + ratioAt(losses.indexOf(value) + 1)) / 2;
    }

    private double PEL1(double L1, double value)
    {
        return value <= ratioAt(0) ? lossCurve.getFor(L1) : interpolator.interpolate(L1);
    }

    private double PEL2(double L2, double value)
    {
        return value >= ratioAt(lastElement()) ? 0.0 : interpolator.interpolate(L2);
    }

    private Double ratioAt(int index)
    {
        return losses.get(index);
    }

    private int lastElement()
    {
        return losses.size() - 1;
    }

}
