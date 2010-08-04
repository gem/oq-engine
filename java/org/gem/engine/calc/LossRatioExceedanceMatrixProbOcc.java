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
import org.gem.engine.data.HazardCurve;

/**
 * Computes the loss ratio exceedance matrix (LREM) * the probability of occurrence (PO) of an hazard curve.
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.3.4.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossRatioExceedanceMatrixProbOcc.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class LossRatioExceedanceMatrixProbOcc
{

    private final Double[][] LREM;
    private final HazardCurve hazardCurve;

    /**
     * @param LREM the loss ratio exceedance matrix to use
     * @param hazardCurve the hazard curve to use
     */
    public LossRatioExceedanceMatrixProbOcc(Double[][] LREM, HazardCurve hazardCurve)
    {
        this.LREM = LREM;
        this.hazardCurve = hazardCurve;
    }

    /**
     * Computes the LREM * PO matrix.
     * 
     * @param function the discrete vulnerability function to use
     * @return the LREM * PO matrix
     */
    public Double[][] compute(DiscreteVulnerabilityFunction function)
    {
        int currentColumn = 0;
        Double[][] result = new Double[LREM.length][function.getDomain().size()];

        for (Double IML : function.getDomain())
        {
            double PO = hazardCurve.getFor(IML);

            for (int row = 0; row < LREM.length; row++)
            {
                result[row][currentColumn] = LREM[row][currentColumn] * PO;
            }

            currentColumn++;
        }

        return result;
    }

}
