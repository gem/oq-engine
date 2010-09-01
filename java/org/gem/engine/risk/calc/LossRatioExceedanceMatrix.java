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
import org.gem.engine.risk.data.distribution.DistributionFactory;

/**
 * Computes the loss ratio exceedance matrix (LREM).
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.3.2.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossRatioExceedanceMatrix.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class LossRatioExceedanceMatrix
{

    private final Interval ratios;
    private final DistributionFactory factory;

    /**
     * @param ratios the ratios used to compute the loss ratio exceedance matrix
     * @param factory the distribution factory to use
     */
    public LossRatioExceedanceMatrix(Interval ratios, DistributionFactory factory)
    {
        this.ratios = ratios;
        this.factory = factory;
    }

    /**
     * Computes the loss ratio exceedance matrix.
     * 
     * @param mean the mean discrete vulnerability function to use
     * @param cov the cov discrete vulnerability function to use
     * @return the loss ratio exceedance matrix
     */
    public Double[][] compute(DiscreteVulnerabilityFunction mean, DiscreteVulnerabilityFunction cov)
    {
        int currentColumn = 0;
        Double[][] result = new Double[ratios.size()][mean.getDomain().size()];

        for (Double IML : mean.getDomain())
        {
            Distribution distribution = factory.create(mean.distributionType(), mean.getFor(IML), cov.getFor(IML));

            // build a single column
            for (int row = 0; row < ratios.size(); row++)
            {
                double nextRatio = row < ratios.size() - 1 ? ratios.get(row + 1) : 1;
                result[row][currentColumn] = adjustValue(1 - adjustValue(distribution.cumulativeProbability(nextRatio)));
            }

            currentColumn++;
        }

        return result;
    }

    private double adjustValue(double value)
    {
        return value < 0.00001 ? 0.0 : value;
    }

}
