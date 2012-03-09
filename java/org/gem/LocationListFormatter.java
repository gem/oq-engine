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

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class LocationListFormatter
{

    private final LocationList locations;

    public LocationListFormatter(LocationList locations)
    {
        this.locations = locations;
    }

    public String format()
    {
        StringBuilder result = new StringBuilder();

        for (int i = 0; i < locations.size(); i++)
        {
            Location current = locations.get(i);
            result.append(format(current));

            if (notLast(i))
            {
                result.append(", ");
            }
        }

        return result.toString();
    }

    private boolean notLast(int index)
    {
        return !(index == locations.size() - 1);
    }

    private String format(Location location)
    {
        StringBuilder result = new StringBuilder();

        result.append(location.getLongitude()).append(" ");
        result.append(location.getLatitude()).append(" ");
        result.append(location.getDepth());

        return result.toString();
    }

}
