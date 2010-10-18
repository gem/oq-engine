/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.commons.geo;

import static org.opensha.commons.geo.GeoTools.TO_DEG;
import static org.opensha.commons.geo.GeoTools.TO_RAD;

import java.io.Serializable;

import org.dom4j.Element;
import org.opensha.commons.metadata.XMLSaveable;

/**
 * A <code>Location</code> represents a point with reference to the earth's
 * ellipsoid. It is expressed in terms of latitude, longitude, and depth. As in
 * seismology, the convention adopted in OpenSHA is for depth to be
 * positive-down, always. All utility methods in this package assume this to be
 * the case.<br/>
 * <br/>
 * For computational cenvenience, latitude and longitude values are converted
 * and stored internally in radians. Special <code>get***Rad()</code> methods
 * are provided to access this native format. <br/>
 * <br/>
 * <code>Location</code> instances are immutable.
 * 
 * @author Peter Powers
 * @author Sid Hellman
 * @author Steven W. Rock
 * @version $Id: Location.java 6593 2010-04-15 14:41:07Z pmpowers $
 */
public class Location implements Serializable, XMLSaveable, Cloneable,
        Comparable<Location> {

    private static final long serialVersionUID = 1L;

    public final static String XML_METADATA_NAME = "Location";
    public final static String XML_METADATA_LONGITUDE = "Longitude";
    public final static String XML_METADATA_LATITUDE = "Latitude";
    public final static String XML_METADATA_DEPTH = "Depth";

    private double lat;
    private double lon;
    private double depth;

    // for internal use by clone()
    private Location() {
    }

    /**
     * Constructs a new <code>Location</code> with the supplied latitude and
     * longitude and sets the depth to 0.
     * 
     * @param lat
     *            latitude in decimal degrees to set
     * @param lon
     *            longitude in decimal degrees to set
     * @throws IllegalArgumentException
     *             if any supplied values are out of range
     * @see GeoTools
     */
    public Location(double lat, double lon) {
        this(lat, lon, 0);
    }

    /**
     * Constructs a new <code>Location</code> with the supplied latitude,
     * longitude, and depth values.
     * 
     * @param lat
     *            latitude in decimal degrees to set
     * @param lon
     *            longitude in decimal degrees to set
     * @param depth
     *            in km to set (positive down)
     * @throws IllegalArgumentException
     *             if any supplied values are out of range
     * @see GeoTools
     */
    public Location(double lat, double lon, double depth) {
        GeoTools.validateLat(lat);
        GeoTools.validateLon(lon);
        GeoTools.validateDepth(depth);
        this.lat = lat * TO_RAD;
        this.lon = lon * TO_RAD;
        this.depth = depth;
    }

    /**
     * Returns the depth of this <code>Location</code>.
     * 
     * @return the <code>Location</code> depth in km
     */
    public double getDepth() {
        return depth;
    }

    /**
     * Returns the latitude of this <code>Location</code>.
     * 
     * @return the <code>Location</code> latitude in decimal degrees
     */
    public double getLatitude() {
        return lat * TO_DEG;
    }

    /**
     * Returns the longitude of this <code>Location</code>.
     * 
     * @return the <code>Location</code> longitude in decimal degrees
     */
    public double getLongitude() {
        return lon * TO_DEG;
    }

    /**
     * Returns the latitude of this <code>Location</code>.
     * 
     * @return the <code>Location</code> latitude in radians
     */
    public double getLatRad() {
        return lat;
    }

    /**
     * Returns the longitude of this <code>Location</code>.
     * 
     * @return the <code>Location</code> longitude in radians
     */
    public double getLonRad() {
        return lon;
    }

    /**
     * Returns this <code>Location</code> formatted as a "lon,lat,depth"
     * <code>String</code> for use in KML documents. This differs from
     * {@link Location#toString()} in that the output lat-lon order are
     * reversed.
     * 
     * @return the location as a <code>String</code> for use with KML markup
     */
    public String toKML() {
        // TODO check that reversed lat-lon order would be ok
        // for toString() and retire this method
        StringBuffer b = new StringBuffer();
        b.append(getLongitude());
        b.append(",");
        b.append(getLatitude());
        b.append(",");
        b.append(getDepth());
        return b.toString();
    }

    @Override
    public String toString() {
        StringBuffer b = new StringBuffer();
        b.append(getLatitude());
        b.append(",");
        b.append(getLongitude());
        b.append(",");
        b.append(getDepth());
        return b.toString();
    }

    @Override
    public Location clone() {
        Location clone = new Location();
        clone.lat = this.lat;
        clone.lon = this.lon;
        clone.depth = this.depth;
        return clone;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (!(obj instanceof Location))
            return false;
        Location loc = (Location) obj;
        // NOTE because rounding errors may give rise to very slight
        // differences in radian values that disappear when converting back
        // to decimal degrees, and because most Locations are initialized
        // with decimal degree values, equals() compares decimal degrees
        // rather than the native radian values. ppowers 4/12/2010
        if (getLatitude() != loc.getLatitude())
            return false;
        if (getLongitude() != loc.getLongitude())
            return false;
        if (getDepth() != loc.getDepth())
            return false;
        return true;
    }

    @Override
    public int hashCode() {
        long latHash = Double.doubleToLongBits(lat);
        long lonHash = Double.doubleToLongBits(lon + 1000);
        long depHash = Double.doubleToLongBits(depth + 2000);
        long v = latHash + lonHash + depHash;
        return (int) (v ^ (v >>> 32));
    }

    /**
     * Compares this <code>Location</code> to another and sorts first by
     * latitude, then by longitude. When sorting a list of randomized but evenly
     * spaced grid of <code>Location</code>s, the resultant ordering will be
     * left to right across rows of uniform latitude, ascending to the leftmost
     * next higher latitude at the end of each row (left-to-right,
     * bottom-to-top).
     * 
     * @param loc
     *            <code>Location</code> to compare <code>this</code> to
     * @return a negative integer, zero, or a positive integer if this
     *         <code>Location</code> is less than, equal to, or greater than the
     *         specified <code>Location</code>.
     */
    @Override
    public int compareTo(Location loc) {
        double d = (lat == loc.lat) ? lon - loc.lon : lat - loc.lat;
        return (d != 0) ? (d < 0) ? -1 : 1 : 0;
    }

    public Element toXMLMetadata(Element root) {
        Element xml = root.addElement(Location.XML_METADATA_NAME);
        xml.addAttribute(Location.XML_METADATA_LATITUDE, getLatitude() + "");
        xml.addAttribute(Location.XML_METADATA_LONGITUDE, getLongitude() + "");
        xml.addAttribute(Location.XML_METADATA_DEPTH, getDepth() + "");
        return root;
    }

    public static Location fromXMLMetadata(Element root) {
        double lat =
                Double.parseDouble(root.attribute(
                        Location.XML_METADATA_LATITUDE).getValue());
        double lon =
                Double.parseDouble(root.attribute(
                        Location.XML_METADATA_LONGITUDE).getValue());
        double depth =
                Double.parseDouble(root.attribute(Location.XML_METADATA_DEPTH)
                        .getValue());
        return new Location(lat, lon, depth);
    }

}
