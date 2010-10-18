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

import static org.opensha.commons.geo.GeoTools.PI_BY_2;
import static org.opensha.commons.geo.GeoTools.TO_RAD;

import java.awt.Shape;
import java.awt.geom.Area;
import java.awt.geom.Path2D;
import java.awt.geom.PathIterator;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.dom4j.Attribute;
import org.dom4j.Element;
import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.metadata.XMLSaveable;

/**
 * A <code>Region</code> is a polygonal area on the surface of the earth. The
 * vertices comprising the border of each <code>Region</code> are stored
 * internally as latitude-longitude coordinate pairs in an
 * {@link java.awt.geom.Area}, facilitating operations such as union, intersect,
 * and contains. Insidedness rules follow those defined in the
 * {@link java.awt.Shape} interface.<br/>
 * <br/>
 * Some constructors require the specification of a {@link BorderType}. If one
 * wishes to define a geographic <code>Region</code> that represents a rectangle
 * in a Mercator projection, {@link BorderType#MERCATOR_LINEAR} should be used,
 * otherwise, the border will follow a {@link BorderType#GREAT_CIRCLE} between
 * two points. Over small distances, great circle paths are approximately the
 * same as linear, Mercator paths. Over longer distances, a great circle is a
 * better representation of a line on a globe. Internally, great circles are
 * approximated by multple straight line segments that have a maximum length of
 * 100km.<br/>
 * <br/>
 * A <code>Region</code> may also have interior (or negative) areas. Any call to
 * {@link Region#contains(Location)} for a <code>Location</code> within or on
 * the border of such an interior area will return <code>false</code>.<br/>
 * <br/>
 * <b><i>NOTE:</i></b> The current implementation does not support regions that
 * are intended to span &#177;180&deg;. Any such regions will wrap the long way
 * around the earth and results are undefined. Regions that encircle either pole
 * are not supported either.<br/>
 * <br/>
 * <b><i>NOTE:</i></b> Due to rounding errors and the use of an {@link Area}
 * internally to define a <code>Region</code>'s border,
 * {@link Region#contains(Location)} may not always return the expected result
 * near a border. See {@link Region#contains(Location)} for further details.<br/>
 * 
 * 
 * @author Peter Powers
 * @version $Id: Region.java 6628 2010-04-27 20:45:42Z kmilner $
 * @see Area
 * @see BorderType
 */
public class Region implements Serializable, XMLSaveable, NamedObjectAPI {

    private static final long serialVersionUID = 1L;

    // although border vertices can be accessed by path-iterating over
    // area, an immutable list is stored for convenience
    private LocationList border;

    // interior region list; may remain null
    private ArrayList<LocationList> interiors;

    // Internal representation of region
    private Area area;

    // Default angle used to subdivide a circular region: 10 deg
    private static final double WEDGE_WIDTH = 10;

    // Default segment length for great circle splitting: 100km
    private static final double GC_SEGMENT = 100;

    public final static String XML_METADATA_NAME = "Region";
    public final static String XML_METADATA_OUTLINE_NAME = "OutlineLocations";

    private String name = "Unnamed Region";

    /* empty constructor for internal use */
    private Region() {
    }

    /**
     * Initializes a <code>Region</code> from a pair of <code>Location
     * </code>s. When viewed in a Mercator projection, the <code>Region</code>
     * will be a rectangle. If either both latitude or both longitude values in
     * the <code>Location</code>s are the same, an exception is thrown.<br/>
     * <br/>
     * <b>Note:</b> Internally, a very small value (~1m) is added to the maximum
     * latitude and longitude of the locations provided. This ensures that calls
     * to {@link Region#contains(Location)} for any <code>Location</code> on the
     * north or east border of the region will return <code>true</code>. See
     * also the rules governing insidedness in the {@link Shape} interface.
     * 
     * @param loc1
     *            the first <code>Location</code>
     * @param loc2
     *            the second <code>Location</code>
     * @throws IllegalArgumentException
     *             if the latitude or longitude values in the
     *             <code>Location</code>s provided are the same
     * @throws NullPointerException
     *             if either <code>Location</code> argument is <code>null</code>
     */
    public Region(Location loc1, Location loc2) {

        if (loc1 == null || loc2 == null) {
            throw new NullPointerException();
        }

        double lat1 = loc1.getLatitude();
        double lat2 = loc2.getLatitude();
        double lon1 = loc1.getLongitude();
        double lon2 = loc2.getLongitude();

        if (lat1 == lat2 || lon1 == lon2) {
            throw new IllegalArgumentException(
                    "Input lats or lons cannot be the same");
        }

        LocationList ll = new LocationList();
        double minLat = Math.min(lat1, lat2);
        double minLon = Math.min(lon1, lon2);
        double maxLat = Math.max(lat1, lat2);
        double maxLon = Math.max(lon1, lon2);
        double offset = LocationUtils.TOLERANCE;
        // ternaries prevent exceedance of max lat-lon values
        maxLat += (maxLat <= 90.0 - offset) ? offset : 0.0;
        maxLon += (maxLon <= 180.0 - offset) ? offset : 0.0;
        ll.add(new Location(minLat, minLon));
        ll.add(new Location(minLat, maxLon));
        ll.add(new Location(maxLat, maxLon));
        ll.add(new Location(maxLat, minLon));

        initBorderedRegion(ll, BorderType.MERCATOR_LINEAR);
    }

    /**
     * Initializes a <code>Region</code> from a list of border locations. The
     * border type specifies whether lat-lon values are treated as points in an
     * orthogonal coordinate system or as connecting great circles. The border
     * <code>LocationList</code> does not need to repeat the first
     * <code>Location</code> at the end of the list.
     * 
     * @param border
     *            <code>Locations</code>
     * @param type
     *            the {@link BorderType} to use when initializing; a
     *            <code>null</code> value defaults to
     *            <code>BorderType.MERCATOR_LINEAR</code>
     * @throws IllegalArgumentException
     *             if the <code>border</code> defines a <code>Region</code> that
     *             is empty or consists of more than a single closed path.
     * @throws NullPointerException
     *             if the <code>border</code> is <code>null</code>
     * @throws IllegalArgumentException
     *             if the border
     */
    public Region(LocationList border, BorderType type) {
        if (border == null) {
            throw new NullPointerException();
        } else if (border.size() < 3) {
            // quick check for empty; recheck on init
            // because 3 points in a row are also empty
            throw new IllegalArgumentException(
                    "Border must have at least 3 vertices");
        } else if (type == null) {
            type = BorderType.MERCATOR_LINEAR;
        }
        initBorderedRegion(border, type);
    }

    /**
     * Initializes a circular <code>Region</code>. Internally, the centerpoint
     * and radius are used to create a circular region composed of straight line
     * segments that span 10&deg; wedges.
     * 
     * @param center
     *            of the circle
     * @param radius
     *            of the circle
     * @throws IllegalArgumentException
     *             if <code>radius</code> is outside the range 0 km &lt;
     *             <code>radius</code> &le; 1000 km
     * @throws NullPointerException
     *             if <code>center</code> is <code>null</code>
     */
    public Region(Location center, double radius) {
        if (radius <= 0 || radius > 1000) {
            throw new IllegalArgumentException(
                    "Radius is out of [0 1000] km range");
        } else if (center == null) {
            throw new NullPointerException();
        }
        initCircularRegion(center, radius);
    }

    /**
     * Initializes a <code>Region</code> as a buffered area around a line.
     * 
     * @param line
     *            at center of buffered <code>Region</code>
     * @param buffer
     *            distance from line
     * @throws NullPointerException
     *             if <code>line</code> is <code>null</code>
     * @throws IllegalArgumentException
     *             if <code>buffer</code> is outside the range 0 km &lt;
     *             <code>buffer</code> &le; 500 km
     */
    public Region(LocationList line, double buffer) {
        if (buffer <= 0 || buffer > 500) {
            throw new IllegalArgumentException(
                    "Buffer is out of [0 500] km range");
        } else if (line == null) {
            throw new NullPointerException();
        } else if (line.size() == 0) {
            throw new IllegalArgumentException("LocationList argument is empty");
        }
        initBufferedRegion(line, buffer);
    }

    /**
     * Initializes a <code>Region</code> with another <code>Region</code>.
     * Creates an exact copy.
     * 
     * @param region
     *            to use as border for new <code>Region</code>
     * @throws NullPointerException
     *             if the supplied <code>Region</code> is null
     */
    public Region(Region region) {
        // don't use validateRegion() b/c we can accept
        // regions with interiors
        if (region == null) {
            throw new NullPointerException("Supplied Region is null");
        }
        this.name = region.name;
        this.border = region.border.clone();
        this.area = (Area) region.area.clone();
        // internal regions
        if (region.interiors != null) {
            interiors = new ArrayList<LocationList>();
            for (LocationList interior : region.interiors) {
                interiors.add(interior.clone());
            }
        }
    }

    /**
     * Returns whether the given <code>Location</code> is inside this
     * <code>Region</code>. The determination follows the rules of insidedness
     * defined in the {@link Shape} interface.<br/>
     * <br/>
     * <b><i>NOTE</i></b>: By using an {@link Area} internally to manage this
     * <code>Region</code>'s geometry, there are instances where rounding errors
     * may cause <code>contains(Location)</code> to yeild unexpected results.
     * For instance, although a <code>Region</code>'s<br/>
     * southernmost point might be initially defined as 40.0&#176;, the internal
     * <code>Area</code> may return 40.0000000000001 on a call to
     * <code>getMinLat()</code> and calls to
     * <code>contains(new Location(40,*))</code> will return false. <br/>
     * 
     * @param loc
     *            the <code>Location</code> to test
     * @return <code>true</code> if the <code>Location</code> is inside the
     *         Region, <code>false</code> otherwise
     * @see java.awt.Shape
     */
    public boolean contains(Location loc) {
        return area.contains(loc.getLongitude(), loc.getLatitude());
    }

    /**
     * Tests whether another <code>Region</code> is entirely contained within
     * this <code>Region</code>.
     * 
     * @param region
     *            to check
     * @return <code>true</code> if this contains the <code>Region</code>;
     *         <code>false</code> otherwise
     */
    public boolean contains(Region region) {
        Area areaUnion = (Area) area.clone();
        areaUnion.add(region.area);
        return area.equals(areaUnion);
    }

    /**
     * Returns whether this <code>Region</code> is rectangular in shape when
     * represented in a Mercator projection.
     * 
     * @return <code>true</code> if rectangular, <code>false</code> otherwise
     */
    public boolean isRectangular() {
        return area.isRectangular();
    }

    /**
     * Adds an interior (donut-hole) to this <code>Region</code>. Any call to
     * {@link Region#contains(Location)} for a <code>Location</code> within this
     * interior area will return <code>false</code>. Any interior
     * <code>Region</code> must lie entirely inside this <code>Region</code>.
     * Moreover, any interior may not overlap or enclose any existing interior
     * region. Internally, the border of the supplied <code>Region</code> is
     * copied and stored as an unmodifiable <code>List</code>. No reference to
     * the supplied <code>Region</code> is retained.
     * 
     * @param region
     *            to use as an interior or negative space
     * @throws NullPointerException
     *             if the supplied <code>Region</code> is <code>null</code>
     * @throws IllegalArgumentException
     *             if the supplied <code>Region</code> is not entirly contained
     *             within this <code>Region</code>
     * @throws IllegalArgumentException
     *             if the supplied <code>Region</code> is not singular (i.e.
     *             already has an interior itself)
     * @throws IllegalArgumentException
     *             if the supplied <code>Region</code> overlaps any existing
     *             interior <code>Region</code>
     * @see Region#getInteriors()
     */
    public void addInterior(Region region) {
        validateRegion(region); // test for non-singularity or null
        if (!contains(region)) {
            throw new IllegalArgumentException(
                    "Region must completely contain supplied interior Region");
        }

        LocationList newInterior = region.border.clone();
        // ensure no overlap with existing interiors
        Area newArea = createArea(newInterior);
        if (interiors != null) {
            for (LocationList interior : interiors) {
                Area existing = createArea(interior);
                existing.intersect(newArea);
                if (!existing.isEmpty()) {
                    throw new IllegalArgumentException(
                            "Supplied interior Region overlaps existing interiors");
                }
            }
        } else {
            interiors = new ArrayList<LocationList>();
        }

        interiors.add(newInterior.unmodifiableList());
        area.subtract(region.area);
    }

    /**
     * Returns an unmodifiable {@link java.util.List} view of the internal
     * <code>LocationList</code>s (also unmodifiable) of points that decribe the
     * interiors of this <code>Region</code>, if such exist. If no interior is
     * defined, the method returns <code>null</code>.
     * 
     * @return a <code>List</code> the interior <code>LocationList</code>s or
     *         <code>null</code> if no interiors are defined
     */
    public List<LocationList> getInteriors() {
        return (interiors != null) ? Collections.unmodifiableList(interiors)
                : null;
    }

    /**
     * Returns an unmodifiable {@link java.util.List} view of the internal
     * <code>LocationList</code> of points that decribe the border of this
     * <code>Region</code>.
     * 
     * @return the immutable border <code>LocationList</code>
     */
    public LocationList getBorder() {
        return border.unmodifiableList();
    }

    /**
     * Compares the geometry of this <code>Region</code> to another and returns
     * <code>true</code> if they are the same, ignoring any differences in name.
     * Use <code>Region.equals(Object)</code> to include name comparison.
     * 
     * @param r
     *            the <code>Regions</code> to compare
     * @return <code>true</code> if this <code>Region</code> has the same
     *         geometry as the supplied <code>Region</code>, <code>false</code>
     *         otherwise
     * @see Region#equals(Object)
     */
    public boolean equalsRegion(Region r) {
        // note that Area.equals() does not override Object.equals()
        return area.equals(r.area);
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (!(obj instanceof Region))
            return false;
        Region r = (Region) obj;
        if (!getName().equals(r.getName()))
            return false;
        return equalsRegion(r);
    }

    @Override
    public int hashCode() {
        return border.hashCode() ^ name.hashCode();
    }

    /**
     * Returns an exact, independent copy of this <code>Region</code>.
     * 
     * @return a copy of this <code>Region</code>
     */
    @Override
    public Region clone() {
        return new Region(this);
    }

    /**
     * Returns the minimum latitude in this <code>Region</code>'s border.
     * 
     * @return the minimum latitude
     */
    public double getMinLat() {
        return area.getBounds2D().getMinY();
    }

    /**
     * Returns the maximum latitude in this <code>Region</code>'s border.
     * 
     * @return the maximum latitude
     */
    public double getMaxLat() {
        return area.getBounds2D().getMaxY();
    }

    /**
     * Returns the minimum longitude in this <code>Region</code>'s border.
     * 
     * @return the minimum longitude
     */
    public double getMinLon() {
        return area.getBounds2D().getMinX();
    }

    /**
     * Returns the maximum longitude in this <code>Region</code>'s border.
     * 
     * @return the maximum longitude
     */
    public double getMaxLon() {
        return area.getBounds2D().getMaxX();
    }

    /**
     * Returns the minimum horizonatal distance (in km) between the border of
     * this <code>Region</code> and the <code>Location</code> specified. If the
     * given <code>Location</code> is inside the <code>Region</code>, the method
     * returns 0. The distance algorithm used only works well at short distances
     * (e.g. &lteq; 250 km).
     * 
     * @param loc
     *            the Location to compute a distance to
     * @return the minimum distance between this <code>Region</code> and a point
     * @see LocationUtils#distanceToLineFast(Location, Location, Location)
     */
    public double distanceToLocation(Location loc) {
        if (contains(loc))
            return 0;
        double min = border.minDistToLine(loc);
        // check the segment defined by the last and first points
        double temp =
                LocationUtils.distanceToLineFast(border.get(border.size() - 1),
                        border.get(0), loc);
        return (temp < min) ? temp : min;
    }

    @Override
    public String getName() {
        return name;
    }

    /**
     * Set the name for this <code>Region</code>.
     * 
     * @param name
     *            for the <code>Region</code>
     */
    public void setName(String name) {
        this.name = name;
    }

    @Override
    public String toString() {
        String str =
                "Region\n" + "\tMinimum Lat: " + this.getMinLat() + "\n"
                        + "\tMinimum Lon: " + this.getMinLon() + "\n"
                        + "\tMaximum Lat: " + this.getMaxLat() + "\n"
                        + "\tMaximum Lon: " + this.getMaxLon();
        return str;
    }

    @Override
    public Element toXMLMetadata(Element root) {
        Element xml = root.addElement(Region.XML_METADATA_NAME);
        xml = border.toXMLMetadata(xml);
        String name = this.name;
        if (name == null)
            name = "";
        xml.addAttribute("name", name);
        return root;
    }

    /**
     * Initializes a new <code>Region</code> from stored metadata.
     * 
     * @param e
     *            metadata element
     * @return a <code>Region</code>
     */
    public static Region fromXMLMetadata(Element e) {
        LocationList list =
                LocationList.fromXMLMetadata(e
                        .element(LocationList.XML_METADATA_NAME));
        Region region = new Region(list, BorderType.MERCATOR_LINEAR);
        Attribute nameAtt = e.attribute("name");
        if (nameAtt != null) {
            String name = nameAtt.getValue();
            if (name.length() > 0)
                region.setName(name);
        }
        return region;
    }

    /**
     * Convenience method to return a <code>Region</code> spanning the entire
     * globe.
     * 
     * @return a <code>Region</code> extending from -180&#176; to +180&#176;
     *         longitude and -90&#176; to +90&#176; latitude
     */
    public static Region getGlobalRegion() {
        LocationList gll = new LocationList();
        gll.add(new Location(-90, -180));
        gll.add(new Location(-90, 180));
        gll.add(new Location(90, 180));
        gll.add(new Location(90, -180));
        return new Region(gll, BorderType.MERCATOR_LINEAR);
    }

    /**
     * Returns the intersection of two <code>Region</code>s. If the
     * <code>Region</code>s do not overlap, the method returns <code>null</code>
     * .
     * 
     * @param r1
     *            the first <code>Region</code>
     * @param r2
     *            the second <code>Region</code>
     * @return a new <code>Region</code> defined by the intersection of
     *         <code>r1</code> and <code>r2</code> or <code>null</code> if they
     *         do not overlap
     * @throws IllegalArgumentException
     *             if either supplied <code>Region</code> is not a single closed
     *             <code>Region</code>
     * @thrown NullPointerException if either supplied <code>Region</code> is
     *         <code>null</code>
     */
    public static Region intersect(Region r1, Region r2) {
        validateRegion(r1);
        validateRegion(r2);
        Area newArea = (Area) r1.area.clone();
        newArea.intersect(r2.area);
        if (newArea.isEmpty())
            return null;
        Region newRegion = new Region();
        newRegion.area = newArea;
        newRegion.border = Region.createBorder(newArea, true);
        return newRegion;
    }

    /**
     * Returns the union of two <code>Region</code>s. If the <code>Region</code>
     * s do not overlap, the method returns <code>null</code>.
     * 
     * @param r1
     *            the first <code>Region</code>
     * @param r2
     *            the second <code>Region</code>
     * @return a new <code>Region</code> defined by the union of <code>r1</code>
     *         and <code>r2</code> or <code>null</code> if they do not overlap
     * @throws IllegalArgumentException
     *             if either supplied <code>Region</code> is not a single closed
     *             <code>Region</code>
     * @thrown NullPointerException if either supplied <code>Region</code> is
     *         <code>null</code>
     */
    public static Region union(Region r1, Region r2) {
        validateRegion(r1);
        validateRegion(r2);
        Area newArea = (Area) r1.area.clone();
        newArea.add(r2.area);
        if (!newArea.isSingular())
            return null;
        Region newRegion = new Region();
        newRegion.area = newArea;
        newRegion.border = Region.createBorder(newArea, true);
        return newRegion;
    }

    /* Validator for geometry operations */
    private static void validateRegion(Region r) {
        if (r == null) {
            throw new NullPointerException("Supplied Region is null");
        } else if (!r.area.isSingular()) {
            throw new IllegalArgumentException("Region must be singular");
        }
    }

    /*
     * Creates a java.awt.geom.Area from a LocationList border. This method
     * throw exceptions if the generated Area is empty or not singular
     */
    private static Area createArea(LocationList border) {

        Path2D path = new Path2D.Double(Path2D.WIND_EVEN_ODD, border.size());

        boolean starting = true;
        for (Location loc : border) {
            double lat = loc.getLatitude();
            double lon = loc.getLongitude();
            // if just starting, then moveTo
            if (starting) {
                path.moveTo(lon, lat);
                starting = false;
                continue;
            }
            path.lineTo(lon, lat);
        }
        path.closePath();
        Area area = new Area(path);
        // final checks on area generated, this is redundant for some
        // constructors that perform other checks on inputs
        if (area.isEmpty()) {
            throw new IllegalArgumentException("Area is empty");
        } else if (!area.isSingular()) {
            throw new IllegalArgumentException(
                    "Area is not a single closed path");
        }

        return area;
    }

    /*
     * Initialize a region from a list of border locations. Internal
     * java.awt.geom.Area is generated from the border.
     */
    private void initBorderedRegion(LocationList border, BorderType type) {

        // first remove last point in list if it is the same as
        // the first point
        int lastIndex = border.size() - 1;
        if (border.get(lastIndex).equals(border.get(0))) {
            border.remove(lastIndex);
        }

        if (type.equals(BorderType.GREAT_CIRCLE)) {
            LocationList gcBorder = new LocationList();
            // process each border pair [start end]; so that the entire
            // border is traversed, set the first 'start' Location as the
            // last point in the gcBorder
            Location start = border.get(border.size() - 1);
            for (int i = 0; i < border.size(); i++) {
                gcBorder.add(start);
                Location end = border.get(i);
                double distance = LocationUtils.horzDistance(start, end);
                // subdivide as necessary
                while (distance > GC_SEGMENT) {
                    // find new Location, GC_SEGMENT km away from start
                    double azRad = LocationUtils.azimuthRad(start, end);
                    Location segLoc =
                            LocationUtils.location(start, azRad, GC_SEGMENT);
                    gcBorder.add(segLoc);
                    start = segLoc;
                    distance = LocationUtils.horzDistance(start, end);
                }
                start = end;
            }
            this.border = gcBorder.clone();
        } else {
            this.border = border.clone();
        }
        area = createArea(this.border);
    }

    /*
     * Initialize a circular region by creating an circular border of shorter
     * straight line segments. Internal java.awt.geom.Area is generated from the
     * border.
     */
    private void initCircularRegion(Location center, double radius) {
        border = createLocationCircle(center, radius);
        area = createArea(border);
    }

    /*
     * Initialize a buffered region by creating box areas of 2x buffer width
     * around each line segment and circle areas around each vertex and union
     * all of them. The border is then be derived from the Area.
     */
    private void initBufferedRegion(LocationList line, double buffer) {
        // init an empty Area
        area = new Area();
        // for each point segment, create a circle area
        Location prevLoc = null;
        for (Location loc : line) {
            // starting out only want to create circle area for first point
            if (area.isEmpty()) {
                area.add(createArea(createLocationCircle(loc, buffer)));
                prevLoc = loc;
                continue;
            }
            area.add(createArea(createLocationBox(prevLoc, loc, buffer)));
            area.add(createArea(createLocationCircle(loc, buffer)));
            prevLoc = loc;
        }
        border = createBorder(area, true);
    }

    /*
     * Creates a LocationList border from a java.awt.geom.Area. The clean flag
     * is used to post-process list to remove repeated identical locations,
     * which are common after intersect and union operations.
     */
    private static LocationList createBorder(Area area, boolean clean) {
        PathIterator pi = area.getPathIterator(null);
        LocationList ll = new LocationList();
        // placeholder vertex for path iteration
        double[] vertex = new double[6];
        while (!pi.isDone()) {
            int type = pi.currentSegment(vertex);
            double lon = vertex[0];
            double lat = vertex[1];
            // skip the final closing segment which just repeats
            // the previous vertex but indicates SEG_CLOSE
            if (type != PathIterator.SEG_CLOSE) {
                ll.add(new Location(lat, lon));
            }
            pi.next();
        }

        if (clean) {
            LocationList llClean = new LocationList();
            Location prev = ll.get(ll.size() - 1);
            for (Location loc : ll) {
                if (loc.equals(prev))
                    continue;
                llClean.add(loc);
                prev = loc;
            }
            ll = llClean;
        }
        return ll;
    }

    /*
     * Utility method returns a LocationList that approximates the circle
     * represented by the center location and radius provided.
     */
    private static LocationList createLocationCircle(Location center,
            double radius) {

        LocationList ll = new LocationList();
        for (double angle = 0; angle < 360; angle += WEDGE_WIDTH) {
            ll.add(LocationUtils.location(center, angle * TO_RAD, radius));
        }
        return ll;
    }

    /*
     * Utility method returns a LocationList representing a box that is as long
     * as the line between p1 and p2 and extends on either side of that line
     * some 'distance'.
     */
    private static LocationList createLocationBox(Location p1, Location p2,
            double distance) {

        // get the azimuth and back-azimuth between the points
        double az12 = LocationUtils.azimuthRad(p1, p2);
        double az21 = LocationUtils.azimuthRad(p2, p1); // back azimuth

        // add the four corners
        LocationList ll = new LocationList();
        // corner 1 is azimuth p1 to p2 - 90 from p1
        ll.add(LocationUtils.location(p1, az12 - PI_BY_2, distance));
        // corner 2 is azimuth p1 to p2 + 90 from p1
        ll.add(LocationUtils.location(p1, az12 + PI_BY_2, distance));
        // corner 3 is azimuth p2 to p1 - 90 from p2
        ll.add(LocationUtils.location(p2, az21 - PI_BY_2, distance));
        // corner 4 is azimuth p2 to p1 + 90 from p2
        ll.add(LocationUtils.location(p2, az21 + PI_BY_2, distance));

        return ll;
    }

    // Serialization methods required for non-serializable Area
    private void writeObject(ObjectOutputStream os) throws IOException {
        os.writeObject(name);
        os.writeObject(border);
        os.writeObject(interiors);
    }

    @SuppressWarnings("unchecked")
    private void readObject(ObjectInputStream is) throws IOException,
            ClassNotFoundException {
        name = (String) is.readObject();
        border = (LocationList) is.readObject();
        interiors = (ArrayList<LocationList>) is.readObject();
        area = createArea(border);
        if (interiors != null) {
            for (LocationList interior : interiors) {
                Area intArea = createArea(interior);
                area.subtract(intArea);
            }
        }
    }

}
