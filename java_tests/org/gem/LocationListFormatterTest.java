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

import static org.junit.Assert.assertEquals;

import org.junit.Test;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class LocationListFormatterTest
{

    @Test
    public void withNoLocationsAnEmptyStringIsReturned()
    {
        assertEquals("", new LocationListFormatter(new LocationList()).format());
    }

    @Test
    public void singleLocationRepresentation()
    {
        LocationList locations = new LocationList();
        locations.add(new Location(1.0, 2.0, 0.5));

        assertEquals("2.0 1.0 0.5", new LocationListFormatter(locations).format());
    }

    @Test
    public void multipleLocationsRepresentation()
    {
        LocationList locations = new LocationList();
        locations.add(new Location(1.0, 2.0, 0.5));
        locations.add(new Location(3.5, 2.5, 4.5));
        locations.add(new Location(4.5, 0.5, 7.5));

        assertEquals("2.0 1.0 0.5, 2.5 3.5 4.5, 0.5 4.5 7.5", new LocationListFormatter(locations).format());
    }

}
