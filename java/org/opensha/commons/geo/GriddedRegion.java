/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.geo;

import java.awt.Shape;
import java.awt.geom.Area;
import java.util.Arrays;
import java.util.Iterator;

import org.apache.commons.math.util.MathUtils;
import org.dom4j.Element;


/**
 * A <code>GriddedRegion</code> is a <code>Region</code> that has been evenly
 * discretized in latitude and longitude. Each node in a gridded region
 * represents a small area that is an equal number of degrees in width and
 * height and is identified by a unique {@link Location} at the geographic
 * (lat-lon) center of the node. <img style="padding: 30px 40px; float: right;" 
 * src="{@docRoot}/img/gridded_regions_border.jpg"/> In the adjacent figure,
 * the heavy black line marks the border of the <code>Region</code> . The 
 * light gray dots mark the <code>Location</code>s of nodes outside the region,
 * and black dots those inside the region. The dashed grey line marks the
 * border, inside which, a <code>Location</code> will be associated with a
 * grid node. See {@link 
 * GriddedRegion#indexForLocation(Location)} 
 * for more details on rules governing whether a grid node is inside a region
 * and whether a <code>Location</code> will be associated with a grid node.<br/>
 * <br/>
 * A <code>GriddedRegion</code> may be initialized several ways (e.g. as a
 * circle, an area of uniform degree-width and -height, or a buffer around
 * a linear feature). See constructor documentation for illustrative examples.
 * The <code>Location</code>s of the grid nodes are indexed
 * internally in order of increasing longitude then latitude starting with
 * the node at the lowest latitude and longitude in the region.
 * <code>GriddedRegion</code>s are iterable as a shorthand for 
 * <code>getNodeList().iterator()</code>.<br/>
 * <br/>
 * To ensure grid nodes fall on specific lat-lon values, all constructors
 * take an anchor <code>Location</code> argument. This location can be
 * anywhere in- or outside the region to be gridded. If the region contains
 * the anchor location, the anchor will coincide with a grid node.  For
 * example, given a grid spacing of 1&deg; and an anchor <code>Location</code>
 * of 22.1&deg;N -134.7&deg;W, grid nodes within any region will fall at
 * whole valued latitudes + 0.1&deg; and longitudes - 0.7&deg;. If an anchor
 * <code>Location</code> is <code>null</code>, it is automatically set as
 * the Location defined by the minimum latitude and longitude of the region's
 * border.<br/>
 * <br/>
 * <a name="note"></a>
 * <b><i>NOTE:</i></b> Due to rounding errors and the use of an {@link Area}
 * internally to define a <code>Region</code>'s border, 
 * {@link Region#contains(Location)} may not always return the expected result
 * near a border. See {@link Region#contains(Location)} for further details.
 * For a <code>GriddedRegion</code>, this results in values returned by calls 
 * {@link #getMinGridLat()} etc. for which there may not be any grid nodes. To
 * guarantee node coverage for a <code>GriddedRegion</code>, say for eventual
 * map output, 'best-practice' dictates expanding a region slightly.
 * 
 * @author Nitin Gupta
 * @author Vipin Gupta 
 * @author Peter Powers
 * @version $Id: GriddedRegion.java 6594 2010-04-15 15:13:06Z pmpowers $
 * @see Region
 */

public class GriddedRegion extends Region implements Iterable<Location> {

	private static final long serialVersionUID = 1L;

	public final static String XML_METADATA_NAME = "evenlyGriddedGeographicRegion";
	public final static String XML_METADATA_GRID_SPACING_NAME = "spacing";
	public final static String XML_METADATA_ANCHOR_NAME = "anchor";
	public final static String XML_METADATA_NUM_POINTS_NAME = "numPoints";

	/** Convenience reference for an anchor at (0&#176;, 0&#176;). */
	public final static Location ANCHOR_0_0 = new Location(0,0);
	
	// the lat-lon arrays of node points. NOTE these are not really needed 
	// after initialization and could be done away with
	private double[] lonNodes;
	private double[] latNodes;
	
	// the lat-lon arrays of node edges
	private double[] lonNodeEdges;
	private double[] latNodeEdges;

	// Location at lower left corner of region bounding rect
	private Location anchor;
	
	// lookup array for grid nodes; has length of master grid spanning
	// region bounding box; all nodes outside region have values of -1;
	// all valid nodes point to position in nodeList; gridIndices increase
	// across and then up
	private int[] gridIndices;
	
	// list of nodes
	private LocationList nodeList;
	
	// grid data
	private double spacing;
	private int nodeCount;
	private int gridSize;

	/**
	 * Initializes a <code>GriddedRegion</code> from a pair of <code>
	 * Location</code>s. When viewed in a Mercator projection, the 
	 * region will be a rectangle. If either both latitude or both longitude
	 * values are the same, an exception is thrown.<br/>
	 * <br/>
	 * <b>Note:</b> In an exception to the rules of insidedness defined
	 * in the {@link Shape} interface, <code>Location</code>s that fall on
	 * northern or eastern borders of this region are considered inside. See 
	 * {@link Region#Region(Location, Location)} for
	 * implementation details.
	 * 
	 * @param loc1 the first <code>Location</code>
	 * @param loc2 the second <code>Location</code>
	 * @param spacing of grid nodes
	 * @param anchor <code>Location</code> for grid; may be <code>null</code>
	 * @throws IllegalArgumentException if the latitude or longitude values
	 * 		in the <code>Location</code>s provided are the same or 
	 * 		<code>spacing</code> is outside the range 0&deg; &lt; <code>spacing
	 * 		</code> &le; 5&deg;
	 * @throws NullPointerException if either <code>Location</code> argument
	 * 		is <code>null</code>
	 * @see Region#Region(Location, Location)
	 */
	public GriddedRegion(
			Location loc1, 
			Location loc2, 
			double spacing, 
			Location anchor) {
		super(loc1, loc2);
		initGrid(spacing, anchor);
	}

	/**
	 * Initializes a <code>GriddedRegion</code> from a list of border locations.
	 * The border type specifies whether lat-lon values are treated as points
	 * in an orthogonal coordinate system or as connecting great circles.
	 * 
	 * @param border Locations
	 * @param type the {@link BorderType} to use when initializing;
	 * 		a <code>null</code> value defaults to 
	 * 		<code>BorderType.MERCATOR_LINEAR</code>
	 * @param spacing of grid nodes
	 * @param anchor <code>Location</code> for grid; may be <code>null</code>
	 * @throws IllegalArgumentException if the <code>border</code> does not 
	 * 		have at least 3 points or <code>spacing</code> is outside the 
	 * 		range 0&deg; &lt; <code>spacing</code> &le; 5&deg;
	 * @throws NullPointerException if the <code>border</code> is 
	 * 		<code>null</code>
	 * @see Region#Region(LocationList, BorderType)
	 */
	public GriddedRegion(
			LocationList border, 
			BorderType type, 
			double spacing, 
			Location anchor) {
		super(border, type);
		initGrid(spacing, anchor);
	}
	
	/**
	 * Initializes a circular <code>GriddedRegion</code>. Internally,
	 * the centerpoint and radius are used to create a circular region
	 * composed of straight line segments that span 10&deg; wedges. 
	 * <img style="padding: 30px 40px; float: right;" 
	 * src="{@docRoot}/img/gridded_regions_circle.jpg"/> In 
	 * the adjacent figure, the heavy black line marks the border of the 
	 * <code>Region</code>. The light gray dots mark the <code>Location</code>s
	 * of nodes outside the region, and black dots those inside the region.
	 * The dashed grey line marks the border, inside which, a 
	 * <code>Location</code> will be associated with a grid node. See {@link 
	 * GriddedRegion#indexForLocation(Location)} 
	 * for more details on rules governing whether a grid node is inside
	 * a region and whether a <code>Location</code> will be associated 
	 * with a grid node.<br/>
	 * <br/>
	 * 
	 * @param center of the circle
	 * @param radius of the circle
	 * @param spacing of grid nodes
	 * @param anchor <code>Location</code> for grid; may be <code>null</code>
	 * @throws IllegalArgumentException if <code>radius</code> is outside the
	 * 		range 0 km &lt; <code>radius</code> &le; 1000 km or <code>spacing
	 * 		</code> is outside the range 0&deg; &lt; <code>spacing</code> 
	 * 		&le; 5&deg;
	 * @throws NullPointerException if <code>center</code> is null
	 * @see Region#Region(Location, double)
	 */
	public GriddedRegion(
			Location center, 
			double radius, 
			double spacing, 
			Location anchor) {
		super(center, radius);
		initGrid(spacing, anchor);
	}

	/**
	 * Initializes a <code>GriddedRegion</code> as a buffered area around a
	 * line. In the adjacent figure, the heavy black line marks the border of 
	 * the <code>Region</code>. <img style="padding: 30px 40px; float: right;" 
	 * src="{@docRoot}/img/gridded_regions_buffer.jpg"/> The light gray 
	 * dots mark the <code>Location</code>s of nodes
	 * outside the region, and black dots those inside the region.
	 * The dashed grey line marks the border, inside which, a 
	 * <code>Location</code> will be associated with a grid node. See {@link 
	 * GriddedRegion#indexForLocation(Location)} 
	 * for more details on rules governing whether a grid node is inside
	 * a region and whether a <code>Location</code> will be associated 
	 * with a grid node.<br/><br/>
	 * <br/>
	 * 
	 * @param line at center of buffered region
	 * @param buffer distance from line
	 * @param spacing of grid nodes
	 * @param anchor <code>Location</code> for grid; may be <code>null</code>
	 * @throws NullPointerException if <code>line</code> is null
	 * @throws IllegalArgumentException if <code>buffer</code> is outside the
	 * 		range 0 km &lt; <code>buffer</code> &le; 500 km or <code>spacing
	 * 		</code> is outside the range 0&deg; &lt; <code>spacing</code> 
	 * 		&le; 5&deg;
	 * @see Region#Region(LocationList, double)
	 */
	public GriddedRegion(
			LocationList line, 
			double buffer, 
			double spacing, 
			Location anchor) {
		super(line, buffer);
		initGrid(spacing, anchor);
	}
	
	/**
	 * Initializes a <code>GriddedRegion</code> with a <code>Region</code>.
	 * 
	 * @param region to use as border for new <code>GriddedRegion</code>
	 * @param spacing of grid nodes
	 * @param anchor <code>Location</code> for grid; may be <code>null</code>
	 * @throws IllegalArgumentException if <code>spacing
	 * 		</code> is outside the range 0&deg; &lt; <code>spacing</code> 
	 * 		&le; 5&deg;
	 * @throws NullPointerException if <code>region</code> is <code>null</code>
	 * @see Region#Region(Region)
	 */
	public GriddedRegion(
			Region region, 
			double spacing,
			Location anchor) {
		super(region);
		initGrid(spacing, anchor);
	}
	
	/**
	 * Returns the grid node spacing for this region.
	 * @return the grid node spacing (in degrees)
	 */
	public double getSpacing() {
		return spacing;
	}

	/**
	 * Returns the total number of grid nodes in this region.
	 * @return the number of grid nodes
	 */
	public int getNodeCount() {
		return nodeCount;
	}

	/**
	 * Returns whether this region contains any grid nodes. If a regions
	 * dimensions are smaller than the grid spacing, it may be empty.
	 * @return <code>true</code> if region has no grid nodes; 
	 * 		<code>false</code> otherwise
	 */
	public boolean isEmpty() {
		return nodeCount == 0;
	}
	
	/**
	 * Compares this <code>GriddedRegion</code> to another and returns
	 * <code>true</code> if they are the same with respect to aerial extent
	 * (both exterior and interior borders), grid node spacing, and location.
	 * This method ignores the names of the <code>GriddedRegion</code>s.
	 * Use <code>GriddedRegion.equals(Object)</code> to include name comparison.
	 * 
	 * @param gr the <code>Regions</code> to compare
	 * @return <code>true</code> if this <code>Region</code> has the same 
	 *         geometry as the supplied <code>Region</code>, <code>false</code>
	 *         otherwise
	 * @see GriddedRegion#equals(Object)
	 */
	public boolean equalsRegion(GriddedRegion gr) {
		if (!super.equalsRegion(gr)) return false;
		if (!gr.anchor.equals(anchor)) return false;
		if (gr.spacing != spacing) return false;
		return true;
	}
	
	@Override
	public boolean equals(Object obj) {
		if (this == obj) return true;
		if (!(obj instanceof GriddedRegion)) return false;
		GriddedRegion gr = (GriddedRegion) obj;
		if (!getName().equals(gr.getName())) return false;
		return equalsRegion(gr);
	}
	
	@Override
	public int hashCode() {
		return super.hashCode() ^ 
				anchor.hashCode() ^ 
				Double.valueOf(spacing).hashCode();
	}
	
	/**
	 * Returns an exact, independent copy of this <code>GriddedRegion</code>.
	 * @return a copy of this <code>Region</code>
	 */
	@Override
	public GriddedRegion clone() {
		return new GriddedRegion(this, spacing, anchor);
	}
	
	/**
	 * Creates a new <code>GriddedRegion</code> from this (the parent) and 
	 * another <code>Region</code>. The border of the new region is the 
	 * intersection of the borders of the parent and the passed-in region.
	 * <img style="padding: 30px 40px; float: right;" 
	 * src="{@docRoot}/img/gridded_regions_sub.jpg"/>
	 * The new region also inherits the grid spacing and node-alignment of 
	 * the parent. The method returns <code>null</code> if the two regions do  
	 * not overlap.<br/>
	 * <br/>
	 * Note that the returned <code>GriddedRegion</code> may be
	 * devoid of grid nodes, e.g. in cases where the sub-region is too small to 
	 * contain any nodes of the parent grid. Sucha asituation may arise if the
	 * sub-region represents the area of influence of a small magnitude
	 * earthquake or aftershock. If the closest point to the sub-region in 
	 * the parent grid is desired, then compute the subRegionCentroid and use:
	 * <pre>
	 * 		if (newGriddedRegion.isEmpty()) {
	 * 			int idx = indexForLocation(subRegionCentroid);
	 * 			if (idx != -1) {
	 * 				Location loc = locationForIndex(idx);
	 * 			}
	 * 		}
	 * </pre>
	 * <br/>
	 * @param region to use as border for sub-region
	 * @return a new GriddedRegion or <code>null</code> if the the sub-region
	 *         does not intersect its parent (<code>this</code>)
	 * @see GriddedRegion#isEmpty()
	 */
	public GriddedRegion subRegion(Region region) {
		Region newRegion = Region.intersect(this, region);
		if (newRegion == null) return null;
		return new GriddedRegion(newRegion, spacing, anchor);
	}
	
	/**
	 * Overridden to throw an <code>UnsupportedOperationException</code> 
	 * when called. The border of a <code>GriddedRegion</code> may
	 * only be set on initialization. To create a <code>GriddedRegion</code>
	 * that has interiors (donut-holes), first create a <code>Region</code>
	 * with the required border and interiors using 
	 * {@link Region#addInterior(Region)} and then use it to initialize a 
	 * <code>GriddedRegion</code>.
	 * 
	 * @throws UnsupportedOperationException
	 * @see Region#addInterior(Region)
	 */
	@Override
	public void addInterior(Region region) {
		throw new UnsupportedOperationException(
				"A GriddedRegion may not have an interior Region set");
	}
	
	@Override
	public Iterator<Location> iterator() {
		return nodeList.iterator();
	}

	/**
	 * Returns the locations of all the nodes in the region as a
	 * <code>LocationList</code>.
	 * @return a list of all the node locations in the region.
	 */
	public LocationList getNodeList() {
		return nodeList;
	}
	
	/**
	 * Returns the <code>Location</code> at a given grid index. This  
	 * method is intended for random access of nodes in this gridded
	 * region; to cycle over all nodes, iterate over the region.
	 * 
	 * @param index of location to retrieve
	 * @return the <code>Location</code> or <code>null</code> if index is
	 * 		out of range
	 */
	public Location locationForIndex(int index) {
		try {
			return nodeList.get(index);
		} catch (IndexOutOfBoundsException e) {
			return null;
		}
	}

	/**
	 * Returns the index of the grid node associated with a given
	 * <code>Location</code> or -1 if the <code>Location</code> is 
	 * ouside this gridded region. For a <code>Location</code> to be 
	 * associated with a node it must fall within the square region 
	 * represented by the node on which the node is centered. Note that 
	 * this allows for some <code>Location</code>s that are outside the 
	 * region border to still be associated with a node.
	 * <br/><br/>
	 * The figure and table below indicate the results produced 
	 * by calling <code>contains()</code> or <code>indexForLocation()</code>.
	 * The arrows in the figure point towards the interior of the 
	 * <code>Region</code>. The dots mark the centered <code>Location</code> 
	 * of each grid node and the numbers indicate the index value of each.
	 * Remember that both methods test for insidedness according to the
	 * rules defined in the {@link Shape} interface.
	 * <br/>
	 * <img style="padding: 20px; display: block; margin-left:auto; 
	 * margin-right:auto;" src="{@docRoot}/img/node_association.jpg"/>
	 * <br/>
	 * <table id="table-a">
	 *   <thead>
	 *     <tr>
	 *       <th>Location</th>
	 *       <th><code>contains(Location)</code></th>
	 *       <th><code>indexForLocation(Location)</code></th>
	 *     </tr>
	 *   <thead>
	 *   <tbody>
	 *     <tr><td><b>A</b></td><td><code>true</code></td><td>-1</td></tr>
	 *     <tr><td><b>B</b></td><td><code>false</code></td><td>3</td></tr>
	 *     <tr><td><b>C</b></td><td><code>false</code></td><td>3</td></tr>
	 *     <tr><td><b>D</b></td><td><code>false</code></td><td>-1</td></tr>
	 *     <tr><td><b>E</b></td><td><code>true</code></td><td>3</td></tr>
	 *     <tr><td><b>F</b></td><td><code>true</code></td><td>3</td></tr>
	 *     <tr><td><b>G</b></td><td><code>true</code></td><td>4</td></tr>
	 *   </tbody>
	 * </table>
	 * 
	 * @param loc the <code>Location</code> to match to a grid node index
	 * @return the index of the associated node or -1 if no such node exists
	 */
	public int indexForLocation(Location loc) {
		int lonIndex = getNodeIndex(lonNodeEdges, loc.getLongitude());
		if (lonIndex == -1) return -1;
		int latIndex = getNodeIndex(latNodeEdges, loc.getLatitude());
		if (latIndex == -1) return -1;
		int gridIndex = ((latIndex) * lonNodes.length) + lonIndex;
		return gridIndices[gridIndex];
	}

	/**
	 * Returns the minimum grid latitude. Note that there may not actually be
	 * any nodes at this latitude. See class <a href="#note">note</a>.
	 * 
	 * @return the minimum grid latitude
	 * @see Region#contains(Location)
	 */
	public double getMinGridLat() {
		return latNodes[0];
	}

	/**
	 * Returns the maximum grid latitude. Note that there may not actually be
	 * any nodes at this latitude. See class <a href="#note">note</a>.
	 * 
	 * @return the maximum grid latitude
	 * @see Region#contains(Location)
	 */
	public double getMaxGridLat() {
		return latNodes[latNodes.length-1];
	}

	/**
	 * Returns the minimum grid longitude. Note that there may not actually be
	 * any nodes at this longitude. See class <a href="#note">note</a>.
	 * 
	 * @return the minimum grid longitude
	 * @see Region#contains(Location)
	 */
	public double getMinGridLon() {
		return lonNodes[0];
	}

	/**
	 * Returns the maximum grid longitude. Note that there may not actually be
	 * any nodes at this longitude. See class <a href="#note">note</a>.
	 * 
	 * @return the maximum grid longitude
	 * @see Region#contains(Location)
	 */
	public double getMaxGridLon() {
		return lonNodes[lonNodes.length-1];
	}
	
	@Override
	public Element toXMLMetadata(Element root) {
		Element xml = root.addElement(GriddedRegion.XML_METADATA_NAME);
		xml.addAttribute(
				GriddedRegion.XML_METADATA_GRID_SPACING_NAME, 
				this.getSpacing()+"");
		Element xml_anchor = root.addElement(
				GriddedRegion.XML_METADATA_ANCHOR_NAME);
		xml = anchor.toXMLMetadata(xml_anchor);
		xml.addAttribute(
				GriddedRegion.XML_METADATA_NUM_POINTS_NAME, 
				this.getNodeCount()+"");
		xml = super.toXMLMetadata(xml);

		return root;
	}

	/**
	 * Initializes a new <code>Region</code> from stored metadata.
	 * @param root metadata element
	 * @return a <code>GriddedRegion</code>
	 */
	public static GriddedRegion fromXMLMetadata(Element root) {
		double gridSpacing = Double.parseDouble(root.attribute(
				GriddedRegion.XML_METADATA_GRID_SPACING_NAME).getValue());
		Region geoRegion = Region.fromXMLMetadata(root.element(
				Region.XML_METADATA_NAME));
		LocationList outline = geoRegion.getBorder();
		Location xml_anchor = Location.fromXMLMetadata(root.element(
				XML_METADATA_ANCHOR_NAME).element(Location.XML_METADATA_NAME));
		return new GriddedRegion(
				outline,BorderType.MERCATOR_LINEAR, gridSpacing, xml_anchor);
	}

	/*
	 * Returns the node index of the value or -1 if the value is 
	 * out of range. Expects the array of edge values.
	 */
	private static int getNodeIndex(double[] edgeVals, double value) {
		// If a value exists in an array, binary search returns the index
		// of the value. If the value is less than the lowest array value,
		// binary search returns -1. If the value is within range or 
		// greater than the highest array value, binary search returns
		// (-insert_point-1). The SHA rule of thumb follows the java rules
		// of insidedness, so any exact node edge value is associated with 
		// the node above. Therefore, the negative within range values are 
		// adjusted to the correct node index with (-idx-2). Below range
		// values are already -1; above range values are corrected to -1.
		int idx = Arrays.binarySearch(edgeVals, value);
		return (idx < -1) ? (-idx - 2) : (idx == edgeVals.length-1) ? -1 : idx;
	}

	/* grid setup */
	private void initGrid(double spacing, Location anchor) {
		setSpacing(spacing);
		setAnchor(anchor);
		initLatLonArrays();
		initNodes();
	}

	/* Sets the gid node spacing. */
	private void setSpacing(double spacing) {
		if (spacing <= 0 || spacing > 5) {
			throw new IllegalArgumentException(
					"Grid spacing must be 0\u00B0 \u003E S \u2265 5\u00B0");
		}
		this.spacing = spacing;
	}

	/*
	 * Sets the grid anchor value. If null, the anchor is the min lat and lon 
	 * of the region. If not null, the Location provided is adjusted to be the
	 * lower left corner (min lat-lon) of the region bounding grid. If the
	 * region grid extended infinitely, both the input and adjusted anchor
	 * Locations would coincide with grid nodes.
	 */
	private void setAnchor(Location anchor) {
		if (anchor == null) {
			this.anchor = new Location(getMinLat(), getMinLon());
		} else {
			double newLat = computeAnchor(
					getMinLat(), anchor.getLatitude(), spacing);
			double newLon = computeAnchor(
					getMinLon(), anchor.getLongitude(), spacing);
			this.anchor = new Location(newLat, newLon);
		}
	}

	/* Computes adjusted anchor values. */
	private static double computeAnchor(
			double min, double anchor, double spacing) {
		double delta = anchor - min;
		double num_div = Math.floor(delta/spacing);
		double offset = delta - num_div*spacing;
		double newAnchor = min + offset;
		newAnchor = (newAnchor < min) ? newAnchor + spacing : newAnchor;
		// round to cleaner values: e.g. 1.0 vs. 0.999999999997
		return MathUtils.round(newAnchor, 8);
	}

	/* Initilize the grid index and Location arrays */
	private void initNodes() {
		gridSize = lonNodes.length * latNodes.length;
		gridIndices = new int[gridSize];
		nodeList = new LocationList();
		int node_idx = 0;
		int grid_idx = 0;
		Location loc;
		for (double lat:latNodes) {
			for (double lon:lonNodes) {
				loc = new Location(lat, lon);
				if (contains(loc)) {
					
					nodeList.add(loc);
					gridIndices[grid_idx] = node_idx++;
				} else {
					gridIndices[grid_idx] = -1;
				}
				grid_idx++;
			}
		}
		nodeCount = node_idx;
	}
	
	/* Initialize internal grid node center and edge arrays */
	private void initLatLonArrays() {
		lonNodes = initNodeCenters(
				anchor.getLongitude(), getMaxLon(), spacing);
		latNodes = initNodeCenters(
				anchor.getLatitude(), getMaxLat(), spacing);
		lonNodeEdges = initNodeEdges(
				anchor.getLongitude(), getMaxLon(), spacing);
		latNodeEdges = initNodeEdges(
				anchor.getLatitude(), getMaxLat(), spacing);
		
		// System.out.println(anchor);
		// ToStringBuilder tsb = new ToStringBuilder(lonNodes);
		// System.out.println(tsb.append(lonNodes).toString());
		// tsb = new ToStringBuilder(latNodes);
		// System.out.println(tsb.append(latNodes).toString());
		// tsb = new ToStringBuilder(lonNodeEdges);
		// System.out.println(tsb.append(lonNodeEdges).toString());
		// tsb = new ToStringBuilder(latNodeEdges);
		// System.out.println(tsb.append(latNodeEdges).toString());
	}

	/*
	 * Initializes an array of node centers. The first (lowest) bin is 
	 * centered on the min value.
	 */
	private static double[] initNodeCenters(
			double min, double max, double width) {
		// nodeCount is num intervals between min and max + 1
		int nodeCount = (int) Math.floor((max - min) / width) + 1;
		double firstCenterVal = min;
		return buildArray(firstCenterVal, nodeCount, width);
	}
	
	/* 
	 * Initializes an array of node edges which can be used to associate
	 * a value with a particular node using binary search.
	 */
	private static double[] initNodeEdges(
			double min, double max, double width) {
		// edges is binCount + 1
		int edgeCount = (int) Math.floor((max - min) / width) + 2;
		// offset first bin edge half a binWidth
		double firstEdgeVal = min - (width / 2);
		return buildArray(firstEdgeVal, edgeCount, width);
	}
	
	/* Node edge and center array builder. */
	private static double[] buildArray(
			double startVal, int count, double interval) {
		 
		double[] values = new double[count];
		double val = startVal;
		for (int i=0; i<count; i++) {
			// round to cleaner values: e.g. 1.0 vs. 0.999999999997
			values[i] = MathUtils.round(val, 8);
			val += interval;
		}
		return values;
	}
	
}
