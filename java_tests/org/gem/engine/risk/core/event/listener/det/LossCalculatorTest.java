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

package org.gem.engine.risk.core.event.listener.det;

import static org.gem.engine.risk.core.AdditionalPipeKeys.ASSET;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LOSS_RATIO_RESULT;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LOSS_RATIO_STD_DEV_RESULT;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LOSS_RESULT;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LOSS_STD_DEV_RESULT;
import static org.junit.Assert.assertEquals;

import org.gem.engine.risk.core.event.listener.BaseFilterTest;
import org.gem.engine.risk.core.event.listener.det.LossCalculator;
import org.gem.engine.risk.data.asset.Asset;
import org.junit.Before;
import org.junit.Test;

public class LossCalculatorTest extends BaseFilterTest
{

    @Before
    public void setUp()
    {
        filter = new LossCalculator();

        addToPipe(LOSS_RATIO_RESULT, 5.0);
        addToPipe(LOSS_RATIO_STD_DEV_RESULT, 2.0);
        addToPipe(ASSET, Asset.newAsset(2.0, null));
    }

    @Test
    public void shouldComputeTheLoss()
    {
        runOn(anySite());
        assertEquals(5.0 * 2.0, pipeValueAtKey(LOSS_RESULT));
    }

    @Test
    public void shouldComputeTheLossStdDev()
    {
        runOn(anySite());
        assertEquals(2.0 * 2.0, pipeValueAtKey(LOSS_STD_DEV_RESULT));
    }

}
