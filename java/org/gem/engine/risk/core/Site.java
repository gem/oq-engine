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

package org.gem.engine.risk.core;

import lombok.ToString;

/**
 * Describes a site.
 * <p>
 * A site is a location where the computation is triggered.
 * 
 * @author Andrea Cerisara
 * @version $Id: Site.java 549 2010-07-12 07:52:04Z acerisara $
 */
@ToString
public class Site
{

    /**
     * The epsilon used to test if two sizes are equal.
     */
    public static final double EPSILON = 0.00000000001;

    private final double latitude;
    private final double longitude;

    /**
     * @param longitude the longitude of this site
     * @param latitude the latitude of this site
     */
    public Site(Double longitude, Double latitude)
    {
        checkLatitudeBoundaries(latitude);
        checkLongitudeBoundaries(longitude);

        this.latitude = latitude;
        this.longitude = longitude;
    }

    private void checkLatitudeBoundaries(Double latitude)
    {
        if (latitude < -90.0 || latitude > 90.0)
        {
            throw new IllegalArgumentException("Latitude must be between -90.0 and 90.0, but was " + latitude);
        }
    }

    private void checkLongitudeBoundaries(Double longitude)
    {
        if (longitude < -360.0 || longitude > 360.0)
        {
            throw new IllegalArgumentException("Longitude must be between -360.0 and 360.0, but was " + longitude);
        }
    }

    /**
     * Returns the longitude of this point.
     * 
     * @return the longitude of this point
     */
    public double getLongitude()
    {
        return longitude;
    }

    /**
     * Returns the latitude of this point.
     * 
     * @return the latitude of this point
     */
    public double getLatitude()
    {
        return latitude;
    }

    @Override
    public int hashCode()
    {
        return (int) (longitude * latitude * 1000000);
    }

    /**
     * Two sites are equal when the longitude and latitude are equal.
     */
    @Override
    public boolean equals(Object obj)
    {
        if (!(obj instanceof Site))
        {
            return false;
        }

        Site other = (Site) obj;
        return doubleEquals(longitude, other.longitude) && doubleEquals(latitude, other.latitude);
    }

    private boolean doubleEquals(double expected, double value)
    {
        return Math.abs(expected - value) < EPSILON;
    }

    /**
     * Returns a new site with the same latitude and with a longitude increased by the given size.
     * 
     * @param size the size used to increase the longitude
     * @return a new site with the same latitude and with a longitude increased by the given size
     */
    public Site shiftLongitude(Double size)
    {
        return new Site(longitude + size, latitude);
    }

    /**
     * Returns a new site with the same longitude and with a latitude increased by the given size.
     * 
     * @param size the size used to increase the longitude
     * @return a new site with the same longitude and with a latitude increased by the given size
     */
    public Site shiftLatitude(Double size)
    {
        return new Site(longitude, latitude + size);
    }

}
