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

import org.gem.engine.data.DiscreteFunction;
import org.gem.engine.data.DiscreteVulnerabilityFunction;
import org.gem.engine.data.FixedDiscreteFunction;
import org.gem.engine.data.HazardCurve;

/**
 * Computes the loss ratio curve (LRC).
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.3.4.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossRatioCurve.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class LossRatioCurve
{

    private final Interval ratios;
    private final Double[][] LREM;
    private final HazardCurve hazardCurve;

    /**
     * @param ratios the ratios used to compute the loss ratio exceedance matrix
     * @param LREM the loss ratio exceedance matrix to use
     * @param hazardCurve the hazard curve to use
     */
    public LossRatioCurve(Interval ratios, Double[][] LREM, HazardCurve hazardCurve)
    {
        this.LREM = LREM;
        this.ratios = ratios;
        this.hazardCurve = hazardCurve;
    }

    /**
     * Computes the loss ratio curve.
     * 
     * @param function the discrete vulnerability function to use
     * @return the computed loss ratio curve
     */
    public DiscreteFunction compute(DiscreteVulnerabilityFunction function)
    {
        FixedDiscreteFunction lossRatioCurve = new FixedDiscreteFunction();
        Double[][] LREMXPO = new LossRatioExceedanceMatrixProbOcc(LREM, hazardCurve).compute(function);

        for (int row = 0; row < LREMXPO.length; row++)
        {
            double currentSum = 0;

            for (int column = 0; column < LREMXPO[row].length; column++)
            {
                currentSum += LREMXPO[row][column];
            }

            lossRatioCurve.addPair(ratios.get(row), currentSum);
        }

        return lossRatioCurve;
    }

}
