/*
    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify it
    under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
*/

package org.gem;

import static org.gem.Utils.digitize;
import static org.junit.Assert.*;

import org.junit.Test;

public class UtilsTest
{
    public static final Double[] BIN_LIMS = {5.0, 6.0, 7.0, 8.0, 9.0};

    @Test
    public void testDigitize()
    {
        int expected = 3;

        int actual = digitize(BIN_LIMS, 8.9);

        assertEquals(expected, actual);
    }

    @Test(expected=IllegalArgumentException.class)
    public void testDigitizeOutOfRange()
    {
        digitize(BIN_LIMS, 4.9);
    }

}
