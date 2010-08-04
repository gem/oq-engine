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

package org.gem.engine.data;

import static org.gem.engine.data.builder.HazardCurveBuilder.aCurve;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Before;
import org.junit.Test;

public class HazardCurveTest
{

    private HazardCurve curve;

    @Before
    public void setUp()
    {
        curve = aCurve().withPair(6.0, 0.1).withPair(7.0, 0.2).withPair(8.0, 0.3).withPair(9.0, 0.4).build();
    }

    @Test
    public void shouldGiveTheProbabilityOfOccurrenceForAGivenIml()
    {
        assertEquals(0.1, curve.getFor(6.0), 0.0);
        assertEquals(0.2, curve.getFor(7.0), 0.0);
        assertEquals(0.3, curve.getFor(8.0), 0.0);
        assertEquals(0.4, curve.getFor(9.0), 0.0);
    }

    @Test
    public void computableWhenHasSomeValues1()
    {
        assertFalse(aCurve().build().isComputable());
    }

    @Test
    public void computableWhenHasSomeValues2()
    {
        assertTrue(curve.isComputable());
    }

}
