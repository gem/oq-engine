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

import org.gem.engine.risk.data.DiscreteVulnerabilityFunction;
import org.gem.engine.risk.data.distribution.Distribution;

/**
 * Computes the mean loss ratio for the deterministic scenario.
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.2.1.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossRatioMean.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class LossRatioMean
{

    private final Distribution distribution;

    /**
     * @param distribution the probabilistic distribution to use
     */
    public LossRatioMean(Distribution distribution)
    {
        this.distribution = distribution;
    }

    /**
     * Computes the loss ratio.
     * 
     * @param function the discrete vulnerability function to use
     * @return the loss ratio
     */
    public double compute(DiscreteVulnerabilityFunction function)
    {
        double result = 0.0;
        Interval IMLs = new Interval(function.getDomain());

        for (double IML : IMLs)
        {
            double lossRatio = function.getFor(IML);
            double probability = distribution.cumulativeProbability(IMLs.lowerBoundFor(IML), IMLs.upperBoundFor(IML));

            result += probability * lossRatio;
        }

        return result;
    }

}
