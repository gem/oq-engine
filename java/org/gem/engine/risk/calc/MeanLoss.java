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

import org.gem.engine.risk.data.DiscreteFunction;

/**
 * Computes the mean loss (ML) within a given time span.
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.3.6.
 * 
 * @author Andrea Cerisara
 * @version $Id: MeanLoss.java 564 2010-07-19 10:31:31Z acerisara $
 */
public class MeanLoss
{

    private final DiscreteFunction curve;
    private final ProbabilityOfOccurrence probabilityOfOccurence;

    /**
     * @param curve the loss or loss ratio curve to use
     * @param probabilityOfOccurence the object responsible for computing the PO for each loss.
     */
    public MeanLoss(DiscreteFunction curve, ProbabilityOfOccurrence probabilityOfOccurence)
    {
        this.curve = curve;
        this.probabilityOfOccurence = probabilityOfOccurence;
    }

    /**
     * Computes the mean loss.
     * 
     * @return the mean loss
     */
    public double compute()
    {
        double result = 0;

        for (double loss : curve.getDomain())
        {
            result += loss * probabilityOfOccurence.compute(loss);
        }

        return result;
    }

}
