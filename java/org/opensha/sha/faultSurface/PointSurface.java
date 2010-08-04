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

package org.opensha.sha.faultSurface;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.util.FaultUtils;


/**
 * <b>Title:</b> PointSurface<p>
 *
 * <b>Description:</b> This is a special case of the GriddedSurface
 * that defaults to one point, i.e. there is only one Location, and the
 * grid size is only [1,1], one row and one column. <p>
 *
 * This will be used by point source models of Potential Earthquake.
 * This is the simplist model, with no rupture surface. <p>
 *
 * Note: all the methods of a GriddedSurface are implemented so it behaves
 * just like a surface instead of a point source. Thus this class can
 * be used anywhere a GriddedSurface can. It plugs right into the framework.<p>
 *
 * Since there is only one Location this class extends Location instead of the
 * base implementing GriddedSurface class. There is no need to set up an array,
 * etc. All the list accessor functions can be bypassed and simply return this
 * location everytime. Improves performace over the base class. <p>
 *
 * @author     Steven W. Rock
 * @created    February 26, 2002
 * @version    1.0
 */
// TODO note in docs that class now wraps Location rather tan subclasses
//public class PointSurface extends Location implements EvenlyGriddedSurfaceAPI {
public class PointSurface implements EvenlyGriddedSurfaceAPI {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	private Location location;

	/**
	 * The average strike of this surface on the Earth. Even though this is a
	 * point source, an average strike can be assigned to it to assist with
	 * particular scientific caculations. Initially set to NaN.
	 */
	protected double aveStrike=Double.NaN;

	/**
	 * The average dip of this surface into the Earth. Even though this is a
	 * point source, an average dip can be assigned to it to assist with
	 * particular scientific caculations. Initially set to NaN.
	 */
	protected double aveDip=Double.NaN;

	/** The name of this point source.  */
	protected String name;

	/** Constructor for the PointSurface object - just calls super(). */
	//public PointSurface() { super(); }


	/**
	 *  Constructor for the PointSurface object. Sets all the fields
	 *  for a Location object. Mirrors the Location constructor.
	 *
	 * @param  lat    latitude for the Location of this point source.
	 * @param  lon    longitude for the Location of this point source.
	 * @param  depth  depth below the earth for the Location of this point source.
	 */
	public PointSurface( double lat, double lon, double depth ) {
		//super( lat, lon, depth );
		// init a Locaiton to perform bounds checking of inputs
		this(new Location(lat, lon, depth));
	}

	/**
	 *  Constructor for the PointSurface object. Sets all the fields
	 *  for a Location object.
	 *
	 * @param  loc    the Location object for this point source.
	 */
	public PointSurface( Location loc ) {
		setLocation(loc);
	}


	/**
	 * Sets the average strike of this surface on the Earth. An InvalidRangeException
	 * is thrown if the ave strike is not a valid value, i.e. must be > 0, etc.
	 * Even though this is a point source, an average strike can be assigned to
	 * it to assist with particular scientific caculations.
	 */
	public void setAveStrike( double aveStrike ) throws InvalidRangeException{
		FaultUtils.assertValidStrike( aveStrike );
		this.aveStrike = aveStrike ;
	}


	/**
	 * Sets the average dip of this surface into the Earth. An InvalidRangeException
	 * is thrown if the ave strike is not a valid value, i.e. must be > 0, etc.
	 * Even though this is a point source, an average dip can be assigned to
	 * it to assist with particular scientific caculations.
	 */
	public void setAveDip( double aveDip ) throws InvalidRangeException{
		FaultUtils.assertValidDip( aveDip );
		this.aveDip =  aveDip ;
	}




	/**
	 *  Add a Location to the grid - does the same thing as set except that it
	 *  ensures the object is a Location object. Note that x and y must always
	 *  be 0,0.
	 *
	 * @param  row                                 The row to set this Location at.
	 * @param  column                              The column to set this Location at.
	 * @param  location                            The new location value.
	 * @exception  ArrayIndexOutOfBoundsException  Thrown if the row or column lies beyond the grid space indexes.
	 */
	public void setLocation( int x, int y, Location location ) throws ArrayIndexOutOfBoundsException {
		if ( x == 0 && y == 0 ) {
			this.setLocation( location );
		} else {
			throw new ArrayIndexOutOfBoundsException( "PointSurface can only have one point, i.e. x=0, y=0." );
		}
	}


	/** Since this is a point source, the single Location can be set without indexes. Does a clone copy. */
	public void setLocation( Location location ) {
		this.location = location;
		//        lat = loc.getLatitude();
		//        lon = loc.getLongitude();
		//        depth = loc.getDepth();
		//        this.setLatitude( location.getLatitude() );
		//        this.setLongitude( location.getLongitude() );
		//        this.setDepth( location.getDepth() );
	}
	//    public double getLatitude() { return lat; }
	//    public void setLatitude(double lat) {
	//    	GeoTools.validateLat(lat);
	//    	this.lat = lat;
	//    }
	//    public double getLongitude() { return lon; }
	//    public void setLongitude(double lon) {
	//    	GeoTools.validateLon(lon);
	//    	this.lon = lon;
	//    }
	public double getDepth() { return location.getDepth(); }
	public void setDepth(double depth) {
		location = new Location(
				location.getLatitude(), 
				location.getLongitude(),
				depth);
	}


	/**
	 *  Set an object in the 2D grid. Ensures the object passed in is a Location.
	 *  Note that x and y must always be 0,0.
	 *
	 * @param  row                                 The row to set the Location. Must be 0.
	 * @param  column                              The row to set the Location. Must be 0.
	 * @param  obj                                 Must be a Location object
	 * @exception  ArrayIndexOutOfBoundsException  Thrown if the row or column lies beyond the grid space indexes.
	 * @exception  ClassCastException              Thrown if the passed in Obejct is not a Location.
	 */
	public void set( int row, int column, Location obj )
	throws
	ArrayIndexOutOfBoundsException,
	ClassCastException {

		if ( row == 0 && column == 0 ) {
			location = obj;
		} else {
			throw new ArrayIndexOutOfBoundsException( "PointSurface can only have one point, i.e. x=0, y=0." );
		}
	}


	/** Returns the average strike of this surface on the Earth.  */
	public double getAveStrike() { return aveStrike; }

	/** Returns the average dip of this surface into the Earth.  */
	public double getAveDip() { return aveDip; }

	/**
	 * Put all the locations of this surface into a location list
	 *
	 * @return
	 */
	public LocationList getLocationList() {
		LocationList locList = new LocationList();
		locList.add(getLocation());
		return locList;
	}



	/** return getLocationsIterator() */
	public ListIterator<Location> getColumnIterator( int row ) throws ArrayIndexOutOfBoundsException {
		return listIterator();
	}

	/** return getLocationsIterator() */
	public ListIterator<Location> getRowIterator( int column ) throws ArrayIndexOutOfBoundsException {
		return listIterator();
	}

	/** return getLocationsIterator() */
	public ListIterator<Location> getAllByColumnsIterator() { return listIterator(); }

	/** return getLocationsIterator() */
	public ListIterator<Location> getAllByRowsIterator() { return listIterator();}


	/** Gets the numRows of the PointSurface. Always returns 1. */
	public int getNumRows() { return 1; }


	/** Gets the numRows of the PointSurface. Always returns 1. */
	public int getNumCols() { return 1; }

	/**
	 * Gets the location for this point source.
	 * 
	 * @return
	 */
	public Location getLocation() {
		return location;
	}


	/**
	 *  Get's the Location of this PointSource.
	 *
	 * @param  row              The row to get this Location from. Must be 0.
	 * @param  column           The column to get this Location from. Must be 0.
	 * @return Value            The Location.
	 *
	 * @exception  ArrayIndexOutOfBoundsException  Thrown if row or column not equal to 0.
	 */
	public Location get( int row, int column )
	throws ArrayIndexOutOfBoundsException {

		if ( row == 0 && column == 0 ) {
			return getLocation();
		} else {
			throw new ArrayIndexOutOfBoundsException( "PointSurface can only have one point, i.e. x=0, y=0." );
		}
	}


	/** Make a clone ( copies all fields ) of the Location. */
	//    protected Location cloneLocation() {
	//
	//        Location location = new Location(
	//                this.getLatitude(),
	//                this.getLongitude(),
	//                this.getDepth()
	//                 );
	//
	//        return location;
	//    }


	/** return getLocationsIterator() */
	public ListIterator<Location> listIterator() {
		ArrayList<Location> v = new ArrayList<Location>();
		v.add(getLocation());
		return v.listIterator();
	}


	/** FIX *** Does nothing - should clear the Location values  */
	public void clear() { }


	/**
	 *  Check if this grid point has data. Will return false for all
	 *  rows and columns != 0.
	 *
	 * @param  row     The row to get this Location from. Must be 0.
	 * @param  column  The column to get this Location from. Must be 0.
	 * @return         Description of the Return Value
	 */
	public boolean exist( int row, int column ) {
		if ( row == 0 || column == 0 ) {
			return true;
		} else {
			return false;
		}
	}

	/**
	 * Returns the grid centered location on each grid surface.
	 * @return GriddedSurfaceAPI returns a Surface that has one less
	 * row and col then the original surface. It averages the 4 corner location
	 * on each grid surface to get the grid centered location.
	 */
	public EvenlyGriddedSurfaceAPI getGridCenteredSurface() {
		return this;
	}


	/** returns number of elements in array. Returns 1.  */
	public long size() {
		return 1L;
	}

	/** Sets the name of this PointSource. Uesful for lookup in a list */
	public void setName(String name) { this.name = name; }
	/** Gets the name of this PointSource. Uesful for lookup in a list */
	public String getName() { return name; }

	/**
	 *  this sets the lat, lon, and depth to be NaN
	 *
	 * @param  row            The row to get this Location from. Must be 0.
	 * @param  column         The column to get this Location from. Must be 0.
	 * @exception  ArrayIndexOutOfBoundsException  Thrown if row or column is not zero.
	 */
	/* implementation */
	//    public void delete( int row, int column )
	//             throws ArrayIndexOutOfBoundsException {
	//        if ( row == 0 && column == 0 ) {
	//
	//        	setLatitude(0);
	//        	setLongitude(0);
	//        	setDepth(0);
	////            this.latitude = Double.NaN;
	////            this.longitude = Double.NaN;
	////            this.depth = Double.NaN;
	//        	
	//        } else {
	//            throw new ArrayIndexOutOfBoundsException( "PointSurface can only have one point, i.e. x=0, y=0." );
	//        }
	//    }

	/**
	 * This returns the total length of the surface
	 * @return double
	 */
	public double getSurfaceLength() {

		return 0;
	}


	/**
	 * This returns the surface width (down dip)
	 * @return double
	 */
	public double getSurfaceWidth() {
		return 0;
	}

	/**
	 * This returns the surface area
	 * @return double
	 */
	public double getSurfaceArea() {
		return 0;
	}


	/**
	 * Returns the Surface Metadata with the following info:
	 * <ul>
	 * <li>AveDip
	 * <li>Surface length
	 * <li>Surface DownDipWidth
	 * <li>GridSpacing
	 * <li>NumRows
	 * <li>NumCols
	 * <li>Number of locations on surface
	 * <p>Each of these elements are represented in Single line with tab("\t") delimitation.
	 * <br>Then follows the location of each point on the surface with the comment String
	 * defining how locations are represented.</p>
	 * <li>#Surface locations (Lat Lon Depth)
	 * <p>Then until surface locations are done each line is the point location on the surface.
	 *
	 * </ul>
	 * @return String
	 */
	public String getSurfaceMetadata() {
		String surfaceMetadata;
		surfaceMetadata = (float)aveDip + "\t";
		surfaceMetadata += (float)getSurfaceLength() + "\t";
		surfaceMetadata += (float)getSurfaceWidth() + "\t";
		surfaceMetadata += (float)Double.NaN + "\t";
		surfaceMetadata += "1" + "\t";
		surfaceMetadata += "1" + "\t";
		surfaceMetadata += "1" + "\n";
		surfaceMetadata += "#Surface locations (Lat Lon Depth) \n";
		surfaceMetadata += (float) location.getLatitude() + "\t";
		surfaceMetadata += (float) location.getLongitude() + "\t";
		surfaceMetadata += (float) location.getDepth();

		return surfaceMetadata;
	}


	/** get a list of locations that constitutes the perimeter (forst row, last col, last row, and first col) */
	public LocationList getSurfacePerimeterLocsList() {
		LocationList locList = new LocationList();
		locList.add(this.getLocation());
		return locList;
	}




	/**
	 * returns the grid spacing
	 *
	 * @return
	 */
	public double getGridSpacingAlongStrike() {
		return Double.NaN;
	}
	/**
	 * returns the grid spacing
	 *
	 * @return
	 */
	public double getGridSpacingDownDip() {
		return Double.NaN;
	}
	/**
	 * returns the grid spacing
	 *
	 * @return
	 */
	public Boolean isGridSpacingSame() {
		return null;
	}

	@Override
	public Location getLocation(int row, int column) {
		return get(row, column);
	}

	@Override
	public ListIterator<Location> getLocationsIterator() {
		return listIterator();
	}

	@Override
	public Iterator<Location> iterator() {
		return listIterator();
	}



}
