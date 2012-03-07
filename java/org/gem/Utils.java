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

public class Utils
{
    /**
     * Given a list of 'bins' and a value,
     * figure out which bin the value fits into.
     * 
     * Examples:
     * 
     * Given the bins [0.0, 1.0, 2.0],
     * a value of 0.5 would be in bin 0, since it is
     * >= the 0th element and less then and 1st element.
     * 
     * Given the bins [0.0, 1.0, 2.0],
     * a value of 1.0 would be in bin 1.
     * @param bins
     * @param value
     */
    public static int digitize(Double[] bins, Double value)
    {
        for (int i = 0; i < bins.length - 1; i++)
        {
            if (value >= bins[i] && value < bins[i + 1])
            {
                return i;
            }
        }
        throw new IllegalArgumentException(
                "Value '" + value + "' is outside the expected range");
    }
}
