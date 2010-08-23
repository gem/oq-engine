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

import java.util.Set;

import org.gem.engine.risk.data.DiscreteFunction;
import org.gem.engine.risk.data.FixedDiscreteFunction;

/**
 * Computes the loss curve (LC).
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.3.4.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossCurve.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class LossCurve
{

    private final DiscreteFunction lossRatioCurve;

    /**
     * @param lossRatioCurve the loss ratio curve to use
     */
    public LossCurve(DiscreteFunction lossRatioCurve)
    {
        this.lossRatioCurve = lossRatioCurve;
    }

    /**
     * Computes the loss curve.
     * 
     * @param assetValue the asset value to use
     * @return the loss curve
     */
    public DiscreteFunction compute(double assetValue)
    {
        Set<Double> lossRatios = lossRatioCurve.getDomain();
        FixedDiscreteFunction result = new FixedDiscreteFunction();

        for (double lossRatio : lossRatios)
        {
            result.addPair(lossRatio * assetValue, lossRatioCurve.getFor(lossRatio));
        }

        return result;
    }

}
