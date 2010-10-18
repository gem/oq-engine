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

import static java.lang.Math.PI;
import static org.opensha.commons.geo.GeoTools.TWOPI;
import static org.opensha.commons.geo.GeoTools.TO_DEG;
import static org.opensha.commons.geo.GeoTools.TO_RAD;
import static org.opensha.commons.geo.GeoTools.EARTH_RADIUS_MEAN;

import org.apache.commons.math.util.MathUtils;

/**
 * This class contains static utility methods to operate on geographic
 * <code>Location</code> data.<br>
 * <br>
 * See: <a href="http://williams.best.vwh.net/avform.htm" target="_blank">
 * Aviation Formulary</a> for formulae implemented in this class as well as <a
 * href="http://www.movable-type.co.uk/scripts/latlong.html"
 * target="_blank">Moveable Type Scripts</a> for other implementations.
 * 
 * @author Peter Powers
 * @author Steven W. Rock
 * @version $Id: LocationUtils.java 6593 2010-04-15 14:41:07Z pmpowers $
 * @see Location
 */
public final class LocationUtils {

    /*
     * Developer Notes: All experimental, exploratory and test methods were
     * moved to the LocationUtilsTest.java. On the basis of various experiments,
     * older methods to calculate distance were replaced with updated versions,
     * many of which leverage spherical geometry to yield more accurate results.
     * Some 'fast' versions were updated as well. All legacy methods, however,
     * are preserved in LocationUtilsTest.java where comparison tests can be
     * rerun. P.Powers 3-6-2010
     * 
     * Most methods take Locations exclusively as arguments. This alleviates any
     * error checking that must otherwise be performed on user supplied lat-lon
     * values. It also alleviates the need for expensive degree-radian
     * conversions by using radians, the native format for Locations,
     * exclusively.
     * 
     * TODO: Add log warnings when 'fast' methods are being used for points that
     * exceed some max separation.
     */

    /* No instantiation allowed */
    private LocationUtils() {
    }

    /**
     * <code>Enum</code> used indicate sidedness of points with respect to a
     * line.
     */
    public enum Side {
        /** Indicates a point is on the right side of a line. */
        RIGHT,
        /** Indicates a point is on the left side of a line. */
        LEFT,
        /** Indicates a point is on the a line. */
        ON;
    }

    /**
     * Calculates the angle between two <code>Location</code>s using the <a
     * href="http://en.wikipedia.org/wiki/Haversine_formula" target="_blank">
     * Haversine</a> formula. This method properly handles values spanning
     * &#177;180&#176;. See <a
     * href="http://williams.best.vwh.net/avform.htm#Dist"> Aviation
     * Formulary</a> for source. Result is returned in radians.
     * 
     * @param p1
     *            the first <code>Location</code> point
     * @param p2
     *            the second <code>Location</code> point
     * @return the angle between the points (in radians)
     */
    public static double angle(Location p1, Location p2) {
        double lat1 = p1.getLatRad();
        double lat2 = p2.getLatRad();
        double sinDlatBy2 = Math.sin((lat2 - lat1) / 2.0);
        double sinDlonBy2 = Math.sin((p2.getLonRad() - p1.getLonRad()) / 2.0);
        // half length of chord connecting points
        double c =
                (sinDlatBy2 * sinDlatBy2)
                        + (Math.cos(lat1) * Math.cos(lat2) * sinDlonBy2 * sinDlonBy2);
        return 2.0 * Math.atan2(Math.sqrt(c), Math.sqrt(1 - c));
    }

    /**
     * Calculates the great circle surface distance between two
     * <code>Location</code>s using the Haversine formula for computing the
     * angle between two points. For a faster, but less accurate implementation
     * at large separations, see {@link #horzDistanceFast(Location, Location)}.
     * 
     * @param p1
     *            the first <code>Location</code> point
     * @param p2
     *            the second <code>Location</code> point
     * @return the distance between the points in km
     * @see #angle(Location, Location)
     * @see #horzDistanceFast(Location, Location)
     */
    public static double horzDistance(Location p1, Location p2) {
        return EARTH_RADIUS_MEAN * angle(p1, p2);
    }

    /**
     * Calculates approximate distance between two <code>Location</code>s. This
     * method is about 2 orders of magnitude faster than
     * <code>surfaceDistance()</code>, but is imprecise at large distances.
     * Method uses the latitudinal and longitudinal differences between the
     * points as the sides of a right triangle. The longitudinal distance is
     * scaled by the cosine of the mean latitude.<br/>
     * <br/>
     * <b>Note:</b> This method does <i>NOT</i> support values spanning
     * #177;180&#176; and fails where the numeric angle exceeds 180&#176;. Use
     * {@link #horzDistance(Location, Location)} in such instances.
     * 
     * @param p1
     *            the first <code>Location</code> point
     * @param p2
     *            the second <code>Location</code> point
     * @return the distance between the points in km
     * @see #horzDistance(Location, Location)
     */
    public static double horzDistanceFast(Location p1, Location p2) {
        // modified from J. Zechar:
        // calculates distance between two points, using formula
        // as specifed by P. Shebalin via email 5.8.2004
        double lat1 = p1.getLatRad();
        double lat2 = p2.getLatRad();
        double dLat = lat1 - lat2;
        double dLon =
                (p1.getLonRad() - p2.getLonRad())
                        * Math.cos((lat1 + lat2) * 0.5);
        return EARTH_RADIUS_MEAN * Math.sqrt((dLat * dLat) + (dLon * dLon));
    }

    /**
     * Returns the vertical separation between two <code>Location</code>s. The
     * returned value is not absolute and preserves the sign of the difference
     * between the points.
     * 
     * @param p1
     *            the first <code>Location</code> point
     * @param p2
     *            the first <code>Location</code> point
     * @return the vertical separation between the points
     */
    public static double vertDistance(Location p1, Location p2) {
        return p2.getDepth() - p1.getDepth();
    }

    /**
     * Calculates the distance in three dimensions between two
     * <code>Location</code>s using spherical geometry. Method returns the
     * straight line distance taking into account the depths of the points. For
     * a faster, but less accurate implementation at large separations, see
     * {@link #linearDistanceFast(Location, Location)}.
     * 
     * @param p1
     *            the first <code>Location</code> point
     * @param p2
     *            the second <code>Location</code> point
     * @return the distance in km between the points
     * @see #linearDistanceFast(Location, Location)
     */
    public static double linearDistance(Location p1, Location p2) {
        double alpha = angle(p1, p2);
        double R1 = EARTH_RADIUS_MEAN - p1.getDepth();
        double R2 = EARTH_RADIUS_MEAN - p2.getDepth();
        double B = R1 * Math.sin(alpha);
        double C = R2 - R1 * Math.cos(alpha);
        return Math.sqrt(B * B + C * C);
    }

    /**
     * Calculates the approximate linear distance in three dimensions between
     * two <code>Location</code>s. This simple and speedy implementation uses
     * the Pythagorean theorem, treating horizontal and vertical separations as
     * orthogonal.<br/>
     * <br/>
     * <b>Note:</b> This method is very imprecise at large separations and
     * should not be used for points &gt;200km apart. If an estimate of
     * separation distance is not known in advance use
     * {@link #linearDistance(Location, Location)} for more reliable results.
     * 
     * @param p1
     *            the first <code>Location</code> point
     * @param p2
     *            the second <code>Location</code> point
     * @return the distance in km between the points
     * @see #linearDistance(Location, Location)
     */
    // TODO examine whether all uses of this method are appropriate or
    // if more accurate linearDistance() should be used instead
    public static double linearDistanceFast(Location p1, Location p2) {
        double h = horzDistanceFast(p1, p2);
        double v = vertDistance(p1, p2);
        return Math.sqrt(h * h + v * v);
    }

    /**
     * Computes the shortest distance between a point and a line (great-circle).
     * Both the line and point are assumed to be at the earth's surface; the
     * depth component of each <code>Location</code> is ignored. This is the
     * true spherical geometric function for 'off-track distance'; See <a
     * href="http://williams.best.vwh.net/avform.htm#XTE"> Aviation
     * Formulary</a> for source.<br/>
     * <br/>
     * <b>Note:</b> This method, though more accurate over longer distances and
     * line lengths, is up to 20x slower than
     * {@link #distanceToLineFast(Location, Location, Location)}. However, this
     * method does return accurate results for values spanning #177;180&#176;.
     * Moreover, the sign of the result indicates which side of the supplied
     * line <code>p3</code> is on (right:[+] left:[-]).
     * 
     * @param p1
     *            the first <code>Location</code> point on the line
     * @param p2
     *            the second <code>Location</code> point on the line
     * @param p3
     *            the <code>Location</code> point for which distance will be
     *            calculated
     * @return the shortest distance in km between the supplied point and line
     * @see #distanceToLineFast(Location, Location, Location)
     */
    public static double distanceToLine(Location p1, Location p2, Location p3) {
        // angular distance
        double ad13 = angle(p1, p3);
        // delta azimuth p1 to p3 and azimuth p1 to p2
        double Daz13az12 = azimuthRad(p1, p3) - azimuthRad(p1, p2);

        // cross-track distance (in radians)
        double xtdRad = Math.asin(Math.sin(ad13) * Math.sin(Daz13az12));
        // along-track distance (in km)
        double atd =
                Math.acos(Math.cos(ad13) / Math.cos(xtdRad))
                        * EARTH_RADIUS_MEAN;

        // check if beyond p3
        if (atd > horzDistance(p1, p2))
            return horzDistance(p2, p3);
        // check if before p1
        if (Math.cos(Daz13az12) < 0)
            return horzDistance(p1, p3);
        return xtdRad * EARTH_RADIUS_MEAN;
    }

    /**
     * Computes the shortest distance between a point and a line. Both the line
     * and point are assumed to be at the earth's surface; the depth component
     * of each <code>Location</code> is ignored. This is a fast, geometric,
     * cartesion (flat-earth approximation) solution in which longitude is
     * scaled by the cosine of latitude; it is only appropriate for use over
     * short distances (e.g. &lt;200 km).<br/>
     * <br/>
     * <b>Note:</b> This method does <i>NOT</i> support values spanning
     * &#177;180&#176; and results for such input values are not guaranteed.
     * 
     * @param p1
     *            the first <code>Location</code> point on the line
     * @param p2
     *            the second <code>Location</code> point on the line
     * @param p3
     *            the <code>Location</code> point for which distance will be
     *            calculated
     * @return the shortest distance in km between the supplied point and line
     * @see #distanceToLine(Location, Location, Location)
     */
    public static double distanceToLineFast(Location p1, Location p2,
            Location p3) {

        double lat1 = p1.getLatRad();
        double lat2 = p2.getLatRad();
        double lat3 = p3.getLatRad();
        double lon1 = p1.getLonRad();
        double lon2 = p2.getLonRad();
        double lon3 = p3.getLonRad();

        // use average latitude to scale longitude
        double lonScale = Math.cos(0.5 * lat3 + 0.25 * lat1 + 0.25 * lat2);

        // line-point corrdinates w/ loc transformed to the origin
        double x1 = (lon1 - lon3) * lonScale;
        double x2 = (lon2 - lon3) * lonScale;
        double y1 = lat1 - lat3;
        double y2 = lat2 - lat3;

        double dist;

        // check for values very close to zero
        if (Math.abs(x1 - x2) > 1e-6) {
            double m = (y2 - y1) / (x2 - x1); // slope
            double b = y2 - m * x2; // intercept
            double xT = -m * b / (1 + m * m); // x target
            double yT = m * xT + b; // y target

            // make sure the target point is in between the two endpoints
            boolean betweenPts = false;
            if (x2 > x1) {
                if (xT <= x2 && xT >= x1)
                    betweenPts = true;
            } else {
                if (xT <= x1 && xT >= x2)
                    betweenPts = true;
            }

            if (betweenPts)
                dist = Math.sqrt(xT * xT + yT * yT);
            // return Math.sqrt(xT*xT + yT*yT) * EARTH_RADIUS_MEAN;
            else {
                double d1 = Math.sqrt(x1 * x1 + y1 * y1);
                double d2 = Math.sqrt(x2 * x2 + y2 * y2);
                dist = Math.min(d1, d2);
            }
        } else {
            // the x1 = x2 case
            if (y2 > y1) {
                if (y2 <= 0.0) {
                    dist = Math.sqrt(x2 * x2 + y2 * y2);
                } else if (y1 >= 0) {
                    dist = Math.sqrt(x1 * x1 + y1 * y1);
                } else {
                    dist = Math.abs(x1);
                }
            } else {
                // (y1 > y2)
                if (y1 <= 0.0) {
                    dist = Math.sqrt(x1 * x1 + y1 * y1);
                } else if (y2 >= 0) {
                    dist = Math.sqrt(x2 * x2 + y2 * y2);
                } else {
                    dist = Math.abs(x1);
                }
            }
        }
        return dist * EARTH_RADIUS_MEAN;
    }

    /**
     * Computes the initial azimuth (bearing) when moving from one
     * <code>Location</code> to another. See <a
     * href="http://williams.best.vwh.net/avform.htm#Crs"> Aviation
     * Formulary</a> for source. For back azimuth, reverse the
     * <code>Location</code> arguments. Result is returned in radians over the
     * interval 0 to 2&pi;.<br/>
     * <br/>
     * <b>Note:</b> It is more efficient to use this method for computation
     * because <code>Location</code>s store lat and lon in radians internally.
     * Use {@link #azimuth(Location, Location)} for presentation.
     * 
     * @param p1
     *            the first <code>Location</code> point
     * @param p2
     *            the second <code>Location</code> point
     * @return the azimuth (bearing) from p1 to p2 in radians
     * @see #azimuth(Location, Location)
     */
    public static double azimuthRad(Location p1, Location p2) {

        double lat1 = p1.getLatRad();
        double lat2 = p2.getLatRad();

        // check the poles using a small number ~ machine precision
        if (isPole(p1)) {
            return ((lat1 > 0) ? PI : 0); // N : S pole
        }

        // for starting points other than the poles:
        double dLon = p2.getLonRad() - p1.getLonRad();
        double cosLat2 = Math.cos(lat2);
        double azRad =
                Math.atan2(Math.sin(dLon) * cosLat2,
                        Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1)
                                * cosLat2 * Math.cos(dLon));

        return (azRad + TWOPI) % TWOPI;
    }

    /**
     * Computes the initial azimuth (bearing) when moving from one
     * {@link Location} to another in degrees. See <a
     * href="http://williams.best.vwh.net/avform.htm#Crs"> Aviation
     * Formulary</a> for source. For back azimuth, reverse the
     * <code>Location</code> arguments. Result is returned in decimal degrees
     * over the interval 0&#176; to 360&#176;.
     * 
     * @param p1
     *            the first <code>Location</code> point
     * @param p2
     *            the second <code>Location</code> point
     * @return the azimuth (bearing) from p1 to p2 in decimal degrees
     * @see #azimuthRad(Location, Location)
     */
    public static double azimuth(Location p1, Location p2) {
        return azimuthRad(p1, p2) * TO_DEG;
    }

    /**
     * Computes a <code>Location</code> given an origin point, bearing, and
     * distance. See <a href="http://williams.best.vwh.net/avform.htm#LL">
     * Aviation Formulary</a> for source. Note that <code>azimuth</code> is
     * expected in <i>radians</i>.
     * 
     * @param p
     *            starting location point
     * @param azimuth
     *            (bearing) in <i>radians</i> away from origin
     * @param distance
     *            (horizontal) along bearing in km
     * @return the end location
     */
    public static Location
            location(Location p, double azimuth, double distance) {
        return location(p.getLatRad(), p.getLonRad(), p.getDepth(), azimuth,
                distance, 0);
    }

    /**
     * Computes a <code>Location</code> given an origin point and a
     * <code>LocationVector</code>. See <a
     * href="http://williams.best.vwh.net/avform.htm#LL"> Aviation Formulary</a>
     * for source.
     * 
     * @param p
     *            starting location point
     * @param d
     *            distance along bearing
     * @return the end location
     */
    public static Location location(Location p, LocationVector d) {
        return location(p.getLatRad(), p.getLonRad(), p.getDepth(),
                d.getAzimuth() * TO_RAD, d.getHorzDistance(),
                d.getVertDistance());
    }

    /*
     * Internal helper; assumes lat, lon, and azimuth in radians, and depth and
     * dist in km
     */
    private static Location location(double lat, double lon, double depth,
            double az, double dH, double dV) {

        double sinLat1 = Math.sin(lat);
        double cosLat1 = Math.cos(lat);
        double ad = dH / EARTH_RADIUS_MEAN; // angular distance
        double sinD = Math.sin(ad);
        double cosD = Math.cos(ad);

        double lat2 = Math.asin(sinLat1 * cosD + cosLat1 * sinD * Math.cos(az));

        double lon2 =
                lon
                        + Math.atan2(Math.sin(az) * sinD * cosLat1, cosD
                                - sinLat1 * Math.sin(lat2));

        return new Location(lat2 * TO_DEG, lon2 * TO_DEG, depth + dV);
    }

    /**
     * Returns the <code>LocationVector</code> describing the move from one
     * <code>Location</code> to another.
     * 
     * @param p1
     *            the first <code>Location</code> point
     * @param p2
     *            the second <code>Location</code> point
     * @return the <code>LocationVector</code> from <code>p1</code> to
     *         <code>p2</code>
     */
    public static LocationVector vector(Location p1, Location p2) {

        // NOTE A 'fast' implementation of this method was tested
        // but no performance gain was realized P.Powers 3-5-2010

        LocationVector v =
                new LocationVector(azimuth(p1, p2), horzDistance(p1, p2),
                        vertDistance(p1, p2));

        return v;
    }

    /**
     * Tolerance used for location comparisons; 0.000000000001 which in
     * decimal-degrees, radians, and km is comparable to micron-scale precision.
     */
    public static final double TOLERANCE = 0.000000000001;

    /**
     * Returns whether the supplied <code>Location</code> coincides with one of
     * the poles. Any supplied <code>Location</code>s that are very close (less
     * than a mm) will return <code>true</code>.
     * 
     * @param p
     *            <code>Location</code> to check
     * @return <code>true</code> if <code>loc</code> coincides with one of the
     *         earth's poles, <code>false</code> otherwise.
     */
    public static boolean isPole(Location p) {
        return Math.cos(p.getLatRad()) < TOLERANCE;
    }

    /**
     * Returns <code>true</code> if the supplied <code>Location</code>s are
     * very, very close to one another. Internally, lat, lon, and depth values
     * must be within <1mm of each other.
     * 
     * @param p1
     *            the first <code>Location</code> to compare
     * @param p2
     *            the second <code>Location</code> to compare
     * @return <code>true</code> if the supplied <code>Location</code>s are very
     *         close, <code>false</code> otherwise.
     */
    public static boolean areSimilar(Location p1, Location p2) {
        if (!MathUtils.equals(p1.getLatRad(), p2.getLatRad(), TOLERANCE)) {
            return false;
        }
        if (!MathUtils.equals(p1.getLonRad(), p2.getLonRad(), TOLERANCE)) {
            return false;
        }
        if (!MathUtils.equals(p1.getDepth(), p2.getDepth(), TOLERANCE)) {
            return false;
        }
        return true;
    }

}