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

package org.gem.engine.core.event.listener.det;

import static org.gem.engine.core.AdditionalPipeKeys.ASSET;
import static org.gem.engine.core.AdditionalPipeKeys.LOSS_RATIO_RESULT;
import static org.gem.engine.core.AdditionalPipeKeys.LOSS_RATIO_STD_DEV_RESULT;
import static org.gem.engine.core.AdditionalPipeKeys.LOSS_RESULT;
import static org.gem.engine.core.AdditionalPipeKeys.LOSS_STD_DEV_RESULT;

import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.cache.Pipe;
import org.gem.engine.core.event.Filter;
import org.gem.engine.data.asset.Asset;

/**
 * Computes the loss and loss standard deviation for the deterministic scenario.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossCalculator.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class LossCalculator extends Filter
{

    @Override
    protected void filter(Cache buffer, Pipe pipe)
    {
        Asset asset = pipe.get(ASSET);
        Double lossRatio = pipe.get(LOSS_RATIO_RESULT);
        Double lossRatioStdDev = pipe.get(LOSS_RATIO_STD_DEV_RESULT);

        pipe.put(LOSS_RESULT, lossRatio * asset.getValue());
        pipe.put(LOSS_STD_DEV_RESULT, lossRatioStdDev * asset.getValue());
    }

}
