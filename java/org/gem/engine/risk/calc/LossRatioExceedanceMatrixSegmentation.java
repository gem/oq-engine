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

import org.gem.engine.risk.data.DiscreteVulnerabilityFunction;

/**
 * Computes the loss ratios used in the computation of a loss ratio exceedance matrix (LREM).
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.3.3.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossRatioExceedanceMatrixSegmentation.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class LossRatioExceedanceMatrixSegmentation
{

    private static final int INTERMEDIATE_STEPS = 5;

    /**
     * Computes the loss ratios used in the computation of a loss ratio exceedance matrix.
     * 
     * @param function the discrete vulnerability function to use
     * @return the loss ratios used in the computation of a loss ratio exceedance matrix
     */
    public Interval compute(DiscreteVulnerabilityFunction function)
    {
        List<Double> lossRatios = new ArrayList<Double>(function.getCodomain());
        lossRatios.add(0, 0.0); // add 0.0 as first interval
        return new Interval(lossRatios).split(INTERMEDIATE_STEPS);
    }

}
