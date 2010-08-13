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
 * Computes the conditional loss or loss ratio (i.e. for a given probability of exceedance) for loss ratio maps (LRM) or loss maps (LM).
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.3.5.
 * 
 * @author Andrea Cerisara
 * @version $Id: ConditionalLoss.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class ConditionalLoss
{

    private final List<Double> losses;
    private final DiscreteFunction curve;

    /**
     * @param curve the loss or loss ratio curve to use
     */
    public ConditionalLoss(DiscreteFunction curve)
    {
        this.curve = curve;
        this.losses = new ArrayList<Double>(curve.getDomain());
    }

    /**
     * Computes the conditional loss.
     * 
     * @param probability the probability of exceedance to use 
     * @return the conditional loss
     */
    public double compute(double probability)
    {
        if (noValues() || isOutOfRange(probability))
        {
            return 0.0;
        }

        int upperBound = upperBound(probability);
        int lowerBound = upperBound - 1;

        double x = ((PEAt(lowerBound) - probability) * ratioAt(upperBound));
        double y = ((probability - PEAt(upperBound)) * ratioAt(lowerBound));

        return (x + y) / (PEAt(lowerBound) - PEAt(upperBound));
    }

    private boolean noValues()
    {
        return losses.size() == 0;
    }

    private double PEAt(int index)
    {
        return curve.getFor(ratioAt(index));
    }

    private double ratioAt(int index)
    {
        return losses.get(index);
    }

    private int upperBound(double probability)
    {
        int upperBound = 0;

        while (PEAt(upperBound) > probability)
        {
            upperBound++;
        }

        return upperBound;
    }

    private boolean isOutOfRange(double probability)
    {
        return probability >= PEAt(0) || probability <= PEAt(losses.size() - 1);
    }

}
