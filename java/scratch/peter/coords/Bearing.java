/*
 * $Id: Bearing.java,v 1.24 2006/11/18 19:03:12 dmurray Exp $
 *
 * Copyright  1997-2004 Unidata Program Center/University Corporation for
 * Atmospheric Research, P.O. Box 3000, Boulder, CO 80307,
 * support@unidata.ucar.edu.
 *
 * This library is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2.1 of the License, or (at
 * your option) any later version.
 *
 * This library is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser
 * General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this library; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */


package scratch.peter.coords;



import org.opensha.commons.geo.Location;


/**
 * Computes the distance, azimuth, and back azimuth between
 * two lat-lon positions on the Earth's surface. Reference ellipsoid is the WGS-84.
 *
 * @author Unidata Development Team
 * @version $Id: Bearing.java,v 1.24 2006/11/18 19:03:12 dmurray Exp $
 */
public class Bearing {

    /** the azimuth, degrees, 0 = north, clockwise positive */
    private double azimuth;

    /** the back azimuth, degrees, 0 = north, clockwise positive */
    private double backazimuth;

    /** separation in kilometers */
    private double distance;

    /** Earth radius */
    private static final double A = 6378137.0;  // in meters

    /** Some constant */
    private static final double F = 1.0 / 298.257223563;

    /** epsilon */
    private static final double EPS = 0.5E-13;

    /** constant R */
    private static final double R = 1.0 - F;

    /** conversion for degrees to radians */
    private static final double rad = Math.toRadians(1.0);

    /** conversion for radians to degrees */
    private static final double deg = Math.toDegrees(1.0);

    /**
     * Get the azimuth in degrees, 0 = north, clockwise positive
     *
     * @return azimuth in degrees
     */
    public double getAngle() {
        return azimuth;
    }

    /**
     * Get the back azimuth in degrees, 0 = north, clockwise positive
     * @return back azimuth in degrees
     */
    public double getBackAzimuth() {
        return backazimuth;
    }

    /**
     * Get the distance in kilometers
     * @return distance in km
     */
    public double getDistance() {
        return distance;
    }

    /**
     * Calculate the bearing between the 2 points.
     * See calculateBearing below.
     *
     * @param pt1 Point 1
     * @param pt2 Point 2
     * @param result Object to use if non-null
     *
     * @return The bearing
     */
    public static Bearing calculateBearing(Location pt1, Location pt2,
                                           Bearing result) {
        return calculateBearing(pt1.getLatitude(), pt1.getLongitude(),
                                pt2.getLatitude(), pt2.getLongitude(),
                                result);
    }

    /**
     * Computes distance (in km), azimuth (degrees clockwise positive
     * from North, 0 to 360), and back azimuth (degrees clockwise positive
     * from North, 0 to 360), from latitude-longituide point pt1 to
     * latitude-longituide pt2.<p>
     * Algorithm from U.S. National Geodetic Survey, FORTRAN program "inverse,"
     * subroutine "INVER1," by L. PFEIFER and JOHN G. GERGEN.
     * See http://www.ngs.noaa.gov/TOOLS/Inv_Fwd/Inv_Fwd.html
     * <P>Original documentation:
     * <br>SOLUTION OF THE GEODETIC INVERSE PROBLEM AFTER T.VINCENTY
     * <br>MODIFIED RAINSFORD'S METHOD WITH HELMERT'S ELLIPTICAL TERMS
     * <br>EFFECTIVE IN ANY AZIMUTH AND AT ANY DISTANCE SHORT OF ANTIPODAL
     * <br>STANDPOINT/FOREPOINT MUST NOT BE THE GEOGRAPHIC POLE
     * </P>
     * Reference ellipsoid is the WGS-84 ellipsoid.
     * <br>See http://www.colorado.edu/geography/gcraft/notes/datum/elist.html
     *
     * Requires close to 1.4 E-5 seconds wall clock time per call
     * on a 550 MHz Pentium with Linux 7.2.
     *
     * @param lat1 Lat of point 1
     * @param lon1 Lon of point 1
     * @param lat2 Lat of point 2
     * @param lon2 Lon of point 2
     * @param result put result here, or null to allocate
     * @return a Bearing object with distance (in km), azimuth from
     *         pt1 to pt2 (degrees, 0 = north, clockwise positive)
     */
    public static Bearing calculateBearing(double lat1, double lon1,
                                           double lat2, double lon2,
                                           Bearing result) {

        if (result == null) {
            result = new Bearing();
        }

        if ((lat1 == lat2) && (lon1 == lon2)) {
            result.distance    = 0;
            result.azimuth     = 0;
            result.backazimuth = 0;
            return result;
        }
        // Algorithm from National Geodetic Survey, FORTRAN program "inverse,"
        // subroutine "INVER1," by L. PFEIFER and JOHN G. GERGEN.
        // http://www.ngs.noaa.gov/TOOLS/Inv_Fwd/Inv_Fwd.html
        // Conversion to JAVA from FORTRAN was made with as few changes as possible
        // to avoid errors made while recasting form, and to facilitate any future
        // comparisons between the original code and the altered version in Java.
        // Original documentation:
        // SOLUTION OF THE GEODETIC INVERSE PROBLEM AFTER T.VINCENTY
        // MODIFIED RAINSFORD'S METHOD WITH HELMERT'S ELLIPTICAL TERMS
        // EFFECTIVE IN ANY AZIMUTH AND AT ANY DISTANCE SHORT OF ANTIPODAL
        // STANDPOINT/FOREPOINT MUST NOT BE THE GEOGRAPHIC POLE
        // A IS THE SEMI-MAJOR AXIS OF THE REFERENCE ELLIPSOID
        // F IS THE FLATTENING (NOT RECIPROCAL) OF THE REFERNECE ELLIPSOID
        // LATITUDES GLAT1 AND GLAT2
        // AND LONGITUDES GLON1 AND GLON2 ARE IN RADIANS POSITIVE NORTH AND EAST
        // FORWARD AZIMUTHS AT BOTH POINTS RETURNED IN RADIANS FROM NORTH
        //
        // Reference ellipsoid is the WGS-84 ellipsoid.
        // See http://www.colorado.edu/geography/gcraft/notes/datum/elist.html
        // FAZ is forward azimuth in radians from pt1 to pt2;
        // BAZ is backward azimuth from point 2 to 1;
        // S is distance in meters.
        //
        // Conversion to JAVA from FORTRAN was made with as few changes as possible
        // to avoid errors made while recasting form, and to facilitate any future
        // comparisons between the original code and the altered version in Java.
        //
        //IMPLICIT REAL*8 (A-H,O-Z)
        //  COMMON/CONST/PI,RAD
        //  COMMON/ELIPSOID/A,F
        double GLAT1 = rad * lat1;
        double GLAT2 = rad * lat2;
        double TU1   = R * Math.sin(GLAT1) / Math.cos(GLAT1);
        double TU2   = R * Math.sin(GLAT2) / Math.cos(GLAT2);
        double CU1   = 1. / Math.sqrt(TU1 * TU1 + 1.);
        double SU1   = CU1 * TU1;
        double CU2   = 1. / Math.sqrt(TU2 * TU2 + 1.);
        double S     = CU1 * CU2;
        double BAZ   = S * TU2;
        double FAZ   = BAZ * TU1;
        double GLON1 = rad * lon1;
        double GLON2 = rad * lon2;
        double X     = GLON2 - GLON1;
        double D, SX, CX, SY, CY, Y, SA, C2A, CZ, E, C;
        do {
            SX  = Math.sin(X);
            CX  = Math.cos(X);
            TU1 = CU2 * SX;
            TU2 = BAZ - SU1 * CU2 * CX;
            SY  = Math.sqrt(TU1 * TU1 + TU2 * TU2);
            CY  = S * CX + FAZ;
            Y   = Math.atan2(SY, CY);
            SA  = S * SX / SY;
            C2A = -SA * SA + 1.;
            CZ  = FAZ + FAZ;
            if (C2A > 0.) {
                CZ = -CZ / C2A + CY;
            }
            E = CZ * CZ * 2. - 1.;
            C = ((-3. * C2A + 4.) * F + 4.) * C2A * F / 16.;
            D = X;
            X = ((E * CY * C + CZ) * SY * C + Y) * SA;
            X = (1. - C) * X * F + GLON2 - GLON1;
            //IF(DABS(D-X).GT.EPS) GO TO 100
        } while (Math.abs(D - X) > EPS);

        FAZ = Math.atan2(TU1, TU2);
        BAZ = Math.atan2(CU1 * SX, BAZ * CX - SU1 * CU2) + Math.PI;
        X   = Math.sqrt((1. / R / R - 1.) * C2A + 1.) + 1.;
        X   = (X - 2.) / X;
        C   = 1. - X;
        C   = (X * X / 4. + 1.) / C;
        D   = (0.375 * X * X - 1.) * X;
        X   = E * CY;
        S   = 1. - E - E;
        S = ((((SY * SY * 4. - 3.) * S * CZ * D / 6. - X) * D / 4. + CZ) * SY
             * D + Y) * C * A * R;

        result.distance = S / 1000.0;  // meters to km
        result.azimuth  = FAZ * deg;   // radians to degrees

        if (result.azimuth < 0.0) {
            result.azimuth += 360.0;  // reset azs from -180 to 180 to 0 to 360
        }

        result.backazimuth = BAZ * deg;  // radians to degrees; already in 0 to 360 range

        return result;
    }


    /*
     * This method is for same use as calculateBearing, but has much simpler calculations
     * by assuming a spherical earth. It is actually slower than
     * "calculateBearing" code, probably due to having more trig function calls.
     * It is less accurate, too.
     * Errors are on the order of 1/300 or less. This code
     * saved here only as a warning to future programmers thinking of this approach.
     *
     * Requires close to 2.0 E-5 seconds wall clock time per call
     * on a 550 MHz Pentium with Linux 7.2.
     *
     * public static Bearing calculateBearingAlternate
     *   (LatLonPoint pt1, LatLonPoint pt2, Bearing result) {
     *
     * // to convert degrees to radians, multiply by:
     * final double rad = Math.toRadians(1.0);
     * // to convert radians to degrees:
     * final double deg = Math.toDegrees(1.0);
     *
     * if (result == null)
     *   result = new Bearing();
     *
     * double R = 6371008.7;  // mean earth radius in meters; WGS 84 definition
     * double GLAT1 = rad*(pt1.getLatitude());
     * double GLAT2 = rad*(pt2.getLatitude());
     * double GLON1 = rad*(pt1.getLongitude());
     * double GLON2 = rad*(pt2.getLongitude());
     *
     * // great circle angular separation in radians
     * double alpha = Math.acos( Math.sin(GLAT1)*Math.sin(GLAT2)
     *                          +Math.cos(GLAT1)*Math.cos(GLAT2)*Math.cos(GLON1-GLON2) );
     * // great circle distance in meters
     * double gcd = R * alpha;
     *
     * result.distance = gcd / 1000.0;      // meters to km
     *
     * // forward azimuth from point 1 to 2 in radians
     * double s2 = rad*(90.0-pt2.getLatitude());
     * double FAZ = Math.asin(Math.sin(s2)*Math.sin(GLON2-GLON1) / Math.sin(alpha));
     *
     * result.azimuth = FAZ * deg;        // radians to degrees
     * if (result.azimuth < 0.0)
     * result.azimuth += 360.0;       // reset az from -180 to 180 to 0 to 360
     *
     * // back azimuth from point 2 to 1 in radians
     * double s1 = rad*(90.0-pt1.getLatitude());
     * double BAZ = Math.asin(Math.sin(s1)*Math.sin(GLON1-GLON2) / Math.sin(alpha));
     *
     * result.backazimuth = BAZ * deg;
     * if (result.backazimuth < 0.0)
     *     result.backazimuth += 360.0;   // reset backaz from -180 to 180 to 0 to 360
     *
     * return result;
     * }
     */


    /**
     * Nice format.
     *
     * @return  return a nice format of this Bearing
     */
    public String toString() {
        StringBuffer buf = new StringBuffer();
        buf.append("Azimuth: ");
        buf.append(azimuth);
        buf.append(" Back azimuth: ");
        buf.append(backazimuth);
        buf.append(" Distance: ");
        buf.append(distance);
        return buf.toString();
    }


    /**
     * Test the calculations - forward and back
     *
     * @param args non used
     */
    public static void main(String[] args) {
        Bearing         workBearing = new Bearing();
        Location pt1         = new Location(40, -105);
        Location pt2         = new Location(37.4, -118.4);
        Bearing         b           = new Bearing();
        b.calculateBearing(pt1, pt2, b);
        System.out.println("Bearing from " + pt1 + " to " + pt2 + " = \n\t"
                           + b);
        Location pt3 = new Location(0,0,0);
        pt3 = b.findPoint(pt1, b.getAngle(), b.getDistance(), pt3);
        System.out.println(
            "using first point, angle and distance, found second point at "
            + pt3);
        pt3 = b.findPoint(pt2, b.getBackAzimuth(), b.getDistance(), pt3);
        System.out.println(
            "using second point, backazimuth and distance, found first point at "
            + pt3);
        /*  uncomment for timing tests
        for(int j=0;j<10;j++) {
            long t1 = System.currentTimeMillis();
            for(int i=0;i<30000;i++) {
                workBearing = Bearing.calculateBearing(42.5,-93.0,
                                                       48.9,-117.09,workBearing);
            }
            long t2 = System.currentTimeMillis();
            System.err.println ("time:" + (t2-t1));
        }
        */
    }


    /**
     * Calculate a position given an azimuth and distance from
     * another point.
     * @see #findPoint(double, double, double, double, LatLonPointImpl)
     *
     * @param pt1 Point 1
     * @param az  azimuth (degrees)
     * @param dist distance from the point (km)
     * @param result Object to use if non-null
     *
     * @return The LatLonPoint
     */
    public static Location findPoint(Location pt1, double az,
                                            double dist,
                                            Location result) {
        return findPoint(pt1.getLatitude(), pt1.getLongitude(), az, dist);
    }

    /**
     * Calculate a position given an azimuth and distance from
     * another point.
     *
     * <p>
     * Algorithm from National Geodetic Survey, FORTRAN program "forward,"
     * subroutine "DIRCT1," by stephen j. frakes.
     * http://www.ngs.noaa.gov/TOOLS/Inv_Fwd/Inv_Fwd.html
     * <p>Original documentation:
     *  <pre>
     *    SOLUTION OF THE GEODETIC DIRECT PROBLEM AFTER T.VINCENTY
     *    MODIFIED RAINSFORD'S METHOD WITH HELMERT'S ELLIPTICAL TERMS
     *    EFFECTIVE IN ANY AZIMUTH AND AT ANY DISTANCE SHORT OF ANTIPODAL
     *  </pre>
     *
     * @param lat1 latitude of starting point
     * @param lon1 longitude of starting point
     * @param az  forward azimuth (degrees)
     * @param dist distance from the point (km)
     * @param result Object to use if non-null
     *
     * @return the position as a LatLonPointImpl
     */
    public static Location findPoint(double lat1, double lon1,
                                            double az, double dist) {
//        if (result == null) {
//            result = new Location();
//        }

        if ((dist == 0)) {
            return new Location(lat1, lon1);

//            result.setLatitude(lat1);
//            result.setLongitude(lon1);
//            return result;
        }
        
        // Algorithm from National Geodetic Survey, FORTRAN program "forward,"
        // subroutine "DIRCT1," by stephen j. frakes.
        // http://www.ngs.noaa.gov/TOOLS/Inv_Fwd/Inv_Fwd.html
        // Conversion to JAVA from FORTRAN was made with as few changes as 
        // possible to avoid errors made while recasting form, and 
        // to facilitate any future comparisons between the original 
        // code and the altered version in Java.
        // Original documentation:
        //   SUBROUTINE DIRCT1(GLAT1,GLON1,GLAT2,GLON2,FAZ,BAZ,S)
        //
        //   SOLUTION OF THE GEODETIC DIRECT PROBLEM AFTER T.VINCENTY
        //   MODIFIED RAINSFORD'S METHOD WITH HELMERT'S ELLIPTICAL TERMS
        //   EFFECTIVE IN ANY AZIMUTH AND AT ANY DISTANCE SHORT OF ANTIPODAL
        //
        //   A IS THE SEMI-MAJOR AXIS OF THE REFERENCE ELLIPSOID
        //   F IS THE FLATTENING OF THE REFERENCE ELLIPSOID
        //   LATITUDES AND LONGITUDES IN RADIANS POSITIVE NORTH AND EAST
        //   AZIMUTHS IN RADIANS CLOCKWISE FROM NORTH
        //   GEODESIC DISTANCE S ASSUMED IN UNITS OF SEMI-MAJOR AXIS A
        //
        //   PROGRAMMED FOR CDC-6600 BY LCDR L.PFEIFER NGS ROCKVILLE MD 20FEB75
        //   MODIFIED FOR SYSTEM 360 BY JOHN G GERGEN NGS ROCKVILLE MD 750608
        // 

        if (az < 0.0) {
            az += 360.0;  // reset azs from -180 to 180 to 0 to 360
        }
        double FAZ   = az * rad;
        double GLAT1 = lat1 * rad;
        double GLON1 = lon1 * rad;
        double S     = dist * 1000.;  // convert to meters
        double TU    = R * Math.sin(GLAT1) / Math.cos(GLAT1);
        double SF    = Math.sin(FAZ);
        double CF    = Math.cos(FAZ);
        double BAZ   = 0.;
        if (CF != 0) {
            BAZ = Math.atan2(TU, CF) * 2;
        }
        double CU  = 1. / Math.sqrt(TU * TU + 1.);
        double SU  = TU * CU;
        double SA  = CU * SF;
        double C2A = -SA * SA + 1.;
        double X   = Math.sqrt((1. / R / R - 1.) * C2A + 1.) + 1.;
        X = (X - 2.) / X;
        double C = 1. - X;
        C = (X * X / 4. + 1) / C;
        double D = (0.375 * X * X - 1.) * X;
        TU = S / R / A / C;
        double Y = TU;
        double SY, CY, CZ, E, GLAT2, GLON2;
        do {
            SY = Math.sin(Y);
            CY = Math.cos(Y);
            CZ = Math.cos(BAZ + Y);
            E  = CZ * CZ * 2. - 1.;
            C  = Y;
            X  = E * CY;
            Y  = E + E - 1.;
            Y = (((SY * SY * 4. - 3.) * Y * CZ * D / 6. + X) * D / 4. - CZ)
                * SY * D + TU;
        } while (Math.abs(Y - C) > EPS);
        BAZ   = CU * CY * CF - SU * SY;
        C     = R * Math.sqrt(SA * SA + BAZ * BAZ);
        D     = SU * CY + CU * SY * CF;
        GLAT2 = Math.atan2(D, C);
        C     = CU * CY - SU * SY * CF;
        X     = Math.atan2(SY * SF, C);
        C     = ((-3. * C2A + 4.) * F + 4.) * C2A * F / 16.;
        D     = ((E * CY * C + CZ) * SY * C + Y) * SA;
        GLON2 = GLON1 + X - (1. - C) * D * F;
        BAZ   = (Math.atan2(SA, BAZ) + Math.PI) * deg;
        return new Location(GLAT2 * deg, GLON2 * deg);
//        result.setLatitude(GLAT2 * deg);
//        result.setLongitude(GLON2 * deg);
//        return result;
    }

}

