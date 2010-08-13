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

package org.gem.engine.risk.core.event.listener.prob;

import static org.gem.engine.risk.core.AdditionalPipeKeys.ASSET;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LOSS_CURVE_RESULT;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LOSS_RATIO_CURVE_RESULT;
import static org.junit.Assert.assertEquals;

import org.gem.engine.risk.core.event.listener.BaseFilterTest;
import org.gem.engine.risk.core.event.listener.prob.LossCurveCalculator;
import org.gem.engine.risk.data.DiscreteFunction;
import org.gem.engine.risk.data.FixedDiscreteFunction;
import org.gem.engine.risk.data.asset.Asset;
import org.junit.Before;
import org.junit.Test;

public class LossCurveCalculatorTest extends BaseFilterTest
{

    @Before
    public void setUp()
    {
        FixedDiscreteFunction lossRatioCurve = new FixedDiscreteFunction();
        lossRatioCurve.addPair(0.1, 1.0);
        lossRatioCurve.addPair(0.2, 2.0);

        filter = new LossCurveCalculator();
        addToPipe(ASSET, Asset.newAsset(2.0, null));
        addToPipe(LOSS_RATIO_CURVE_RESULT, lossRatioCurve);
    }

    @Test
    public void shouldComputeAndSaveTheLossCurve()
    {
        runOn(anySite());
        assertEquals(1.0, ((DiscreteFunction) pipeValueAtKey(LOSS_CURVE_RESULT)).getFor(0.1 * 2.0), 0.0);
        assertEquals(2.0, ((DiscreteFunction) pipeValueAtKey(LOSS_CURVE_RESULT)).getFor(0.2 * 2.0), 0.0);
    }

}
