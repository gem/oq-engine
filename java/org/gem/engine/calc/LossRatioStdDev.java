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

package org.gem.engine.calc;

import org.gem.engine.data.DiscreteVulnerabilityFunction;
import org.gem.engine.data.distribution.Distribution;

/**
 * Computes the loss ratio standard deviation for the deterministic scenario.
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.2.2.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossRatioStdDev.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class LossRatioStdDev
{

    private final Distribution distribution;

    /**
     * @param distribution the probabilistic distribution to use
     */
    public LossRatioStdDev(Distribution distribution)
    {
        this.distribution = distribution;
    }

    /**
     * Computes the loss ratio standard deviation.
     * 
     * @param cov the cov discrete vulnerability function to use
     * @param mean the mean discrete vulnerability function to use
     * @return the loss ratio standard deviation
     */
    public double compute(DiscreteVulnerabilityFunction mean, DiscreteVulnerabilityFunction cov)
    {
        double y = probTimesStdDevLossRatio(mean, cov);
        double x = Math.pow(probTimesMeanLossRatio(mean), 2);

        return Math.sqrt(y - x);
    }

    private double probTimesMeanLossRatio(DiscreteVulnerabilityFunction mean)
    {
        double result = 0.0;
        Interval IMLs = new Interval(mean.getDomain());

        for (double IML : IMLs)
        {
            double probability = cumulativeProbabilityFor(IMLs, IML);
            result += Math.pow(mean.getFor(IML) * probability, 2);
        }

        return result;
    }

    private double probTimesStdDevLossRatio(DiscreteVulnerabilityFunction mean, DiscreteVulnerabilityFunction cov)
    {
        double result = 0.0;
        Interval IMLs = new Interval(mean.getDomain());

        for (double IML : IMLs)
        {
            double stdDev = mean.getFor(IML) * cov.getFor(IML);
            double probability = cumulativeProbabilityFor(IMLs, IML);
            result += (Math.pow(stdDev, 2) + Math.pow(mean.getFor(IML), 2)) * probability;
        }

        return result;
    }

    private double cumulativeProbabilityFor(Interval IMLs, double IML)
    {
        return distribution.cumulativeProbability(IMLs.lowerBoundFor(IML), IMLs.upperBoundFor(IML));
    }

}
