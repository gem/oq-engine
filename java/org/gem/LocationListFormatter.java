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
