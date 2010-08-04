/**
 * 
 */
package org.opensha.sha.faultSurface;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;

/**
 * This class represents an evenly gridded surface composed of four Locations.
 * 
 * @author field
 */
public class FourPointEvenlyGriddedSurface extends EvenlyGriddedSurface {

	// for debugging
	private final static boolean D = false;

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;


	/**
	 * The constructs the surface from the Locations given (counter clockwise 
	 * when looking at surface from positive side).  This computes gridSpacingAlong and 
	 * gridSpacingDown as the average of the two calculable distances for each.
	 * @param upperLeft
	 * @param lowerLeft
	 * @param lowerRight
	 * @param upperRight
	 */
	public FourPointEvenlyGriddedSurface(Location upperLeft,  Location lowerLeft, 
										 Location lowerRight, Location upperRight) {
		setNumRowsAndNumCols(2, 2);
		
		setLocation(0, 0, upperLeft);
		setLocation(0, 1, upperRight);
		setLocation(1, 0, lowerLeft);
		setLocation(1, 1, lowerRight);
		
		gridSpacingAlong = (LocationUtils.linearDistanceFast(getLocation(0, 0), getLocation(0, 1)) +
							LocationUtils.linearDistanceFast(getLocation(1, 0), getLocation(1, 1)))/2;
		gridSpacingDown = (LocationUtils.linearDistanceFast(getLocation(0, 0), getLocation(1, 0))+
						   LocationUtils.linearDistanceFast(getLocation(0, 1), getLocation(1, 1)))/2;

		if(gridSpacingAlong == gridSpacingDown)
			sameGridSpacing = true;
		else
			sameGridSpacing = false;
	}

}
