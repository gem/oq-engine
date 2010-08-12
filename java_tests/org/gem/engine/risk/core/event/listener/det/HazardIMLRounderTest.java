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

import static org.gem.engine.risk.core.AdditionalPipeKeys.MEAN_IML;
import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertThat;

import org.gem.engine.risk.core.event.listener.BaseFilterTest;
import org.gem.engine.risk.core.event.listener.det.HazardIMLRounder;
import org.junit.Before;
import org.junit.Test;

public class HazardIMLRounderTest extends BaseFilterTest
{

    @Before
    public void setUp()
    {
        filter = new HazardIMLRounder();
    }

    @Test
    // 5.2 to 5.5
    public void shouldRoundTheIMLValue1()
    {
        addToPipe(MEAN_IML, 5.2);
        runOn(anySite());

        assertThat((Double) pipeValueAtKey(MEAN_IML), is(5.5));
    }

    @Test
    // 5.5 to 5.5
    public void shouldRoundTheIMLValue2()
    {
        addToPipe(MEAN_IML, 5.5);
        runOn(anySite());

        assertThat((Double) pipeValueAtKey(MEAN_IML), is(5.5));
    }

    @Test
    // 5.6 to 6.0
    public void shouldRoundTheIMLValue3()
    {
        addToPipe(MEAN_IML, 5.6);
        runOn(anySite());

        assertThat((Double) pipeValueAtKey(MEAN_IML), is(6.0));
    }

    @Test
    // 5.0 to 5.0
    public void shouldRoundTheIMLValue4()
    {
        addToPipe(MEAN_IML, 5.0);
        runOn(anySite());

        assertThat((Double) pipeValueAtKey(MEAN_IML), is(5.0));
    }

}
