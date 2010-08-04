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

import static org.gem.engine.core.AdditionalPipeKeys.COV_IML;
import static org.gem.engine.core.AdditionalPipeKeys.MEAN_IML;
import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertThat;

import org.gem.engine.core.Site;
import org.gem.engine.core.event.listener.BaseFilterTest;
import org.gem.engine.core.reader.HazardReader;
import org.junit.Before;
import org.junit.Test;

public class HazardIMLLoaderTest extends BaseFilterTest implements HazardReader<Double>
{

    private Double value;

    @Before
    public void setUp()
    {
        filter = new HazardIMLLoader(this, this);
    }

    @Test
    public void shouldLoadTheMeanIMLIntoThePipe()
    {
        value = 5.0;

        runOn(anySite());
        assertThat((Double) pipeValueAtKey(MEAN_IML), is(5.0));
    }

    @Test
    public void shouldLoadTheCovIMLIntoThePipe()
    {
        value = 0.1;

        runOn(anySite());
        assertThat((Double) pipeValueAtKey(COV_IML), is(0.1));
    }

    @Override
    public Double readAt(Site site)
    {
        return value;
    }

}
