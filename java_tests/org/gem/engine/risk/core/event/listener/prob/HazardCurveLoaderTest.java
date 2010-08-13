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

import static org.gem.engine.risk.core.AdditionalPipeKeys.HAZARD_CURVE;
import static org.gem.engine.risk.data.builder.HazardCurveBuilder.aCurve;
import static org.junit.Assert.assertEquals;

import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.event.listener.BaseFilterTest;
import org.gem.engine.risk.core.event.listener.prob.HazardCurveLoader;
import org.gem.engine.risk.core.reader.HazardReader;
import org.gem.engine.risk.data.HazardCurve;
import org.junit.Before;
import org.junit.Test;

public class HazardCurveLoaderTest extends BaseFilterTest implements HazardReader<HazardCurve>
{

    private HazardCurve curve;

    @Before
    public void setUp()
    {
        curve = aCurve().build();
        filter = new HazardCurveLoader(this);
    }

    @Test
    public void shouldLoadACurveIntoThePipe()
    {
        runOn(anySite());
        assertEquals(curve, pipeValueAtKey(HAZARD_CURVE));
    }

    @Override
    public HazardCurve readAt(Site site)
    {
        return curve;
    }

}
