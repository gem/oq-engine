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

package org.gem.engine.core;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class SiteTest
{

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrowAnExceptionIfLongitudeIsOutOfRange1()
    {
        new Site(-360.1, 1.0);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrowAnExceptionIfLongitudeIsOutOfRange2()
    {
        new Site(360.1, 1.0);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrowAnExceptionIfLatitudeIsOutOfRange1()
    {
        new Site(1.0, -90.1);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrowAnExceptionIfLatitudeIsOutOfRange2()
    {
        new Site(1.0, 90.1);
    }

    @Test
    public void testEquals()
    {
        assertTrue(new Site(1.12345678901, 1.12345678901).equals(new Site(1.12345678901, 1.12345678901)));
        assertTrue(new Site(1.12345678901, 1.123456789011).equals(new Site(1.12345678901, 1.123456789012)));
        assertTrue(new Site(1.123456789011, 1.12345678901).equals(new Site(1.123456789012, 1.12345678901)));

        assertFalse(new Site(1.12345679901, 1.12345678901).equals(new Site(1.12345678901, 1.12345678901)));
        assertFalse(new Site(1.12345678901, 1.12345679901).equals(new Site(1.12345678901, 1.12345678901)));
        assertFalse(new Site(1.12345678901, 1.12345678901).equals(new Site(1.12345678901, 1.12345679901)));
    }

}
