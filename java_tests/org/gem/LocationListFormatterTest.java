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
