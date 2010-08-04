/**
 * 
 */
package junk.deformationModel;

import java.awt.geom.Line2D;
import java.awt.geom.Point2D;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 * Given a line and a FaultTrace, this class finds the point of intersection 
 * of the line with the FaultTrace. If there are multiple points, then the point closest
 * to the east point of line is returned. If there is no point of intersection, then
 * null is returned
 *  
 * @author vipingupta
 *
 */
public class LineIntersection {
	private double minDistance;
	private double strike;
	
	/**
	 * Get the intersection point between a line and a fault Trace. 
	 * If there are multiple points, then the point closest
	 * to the east point of line is returned. If there is no point of intersection, then
	 * null is returned
	 * 
	 * @param eastLocation
	 * @param westLocation
	 * @param faultTrace
	 * @return
	 */
	public Location getIntersectionPoint(Location eastLocation, Location westLocation, 
			FaultTrace faultTrace) {
		if(eastLocation.getLongitude()>westLocation.getLongitude())
			throw new RuntimeException("East Location should be first Locqtion");
		Line2D line = this.getLine2DFromLocations(eastLocation, westLocation);
		return getIntersectionPoint(line,faultTrace, LocationUtils.azimuth(eastLocation,westLocation));
	}
	
	/**
	 * 
	 * @param line
	 * @param faultTrace
	 * @return
	 */
	private  Location getIntersectionPoint(Line2D line, FaultTrace faultTrace, double crossSectionStrike) {
		Location closestLoc = null;
		minDistance = Double.MAX_VALUE;
		strike = Double.NaN;
		Location eastLoc = new Location(line.getY1(), line.getX1());
		double distance;
		for(int i=1; i<faultTrace.getNumLocations(); ++i) {
			Location loc = calculateIntersect(line, getLine2DFromLocations(faultTrace.get(i-1),faultTrace.get(i) ));
			if(loc==null) continue;
			distance = LocationUtils.horzDistanceFast(loc, eastLoc);
			if(distance<minDistance) {
				closestLoc = loc;
				minDistance = distance;
				strike = crossSectionStrike+90-LocationUtils.azimuth(faultTrace.get(i),faultTrace.get(i-1));
			}
		}
		return closestLoc;
	}
	
	public double getStrike() {
		return this.strike;
	}
	
	public double getDistance() {
		return this.minDistance;
	}
	
	/**
	 * Make Line2D object from 2 locations
	 * @param loc1
	 * @param loc2
	 * @return
	 */
	private Line2D.Double getLine2DFromLocations(Location loc1, Location loc2) {
		return new  Line2D.Double(loc1.getLongitude(), loc1.getLatitude(), 
				loc2.getLongitude(), loc2.getLatitude());
	}
	
	/**
	 * Calculate intersection point of 2 line segments
	 * @param line1
	 * @param line2
	 * @return
	 */
	private Location calculateIntersect(Line2D line1, Line2D line2){
		double minLon = line1.getX1();
		double maxLon = line1.getX2();
		double minLat = line1.getY1();
		double maxLat = line1.getY2();
		if(minLat>maxLat) {
			minLat = line1.getY2();
			maxLat = line1.getY1();
		}
		
	    double line1gradient = calculateGradient(line1);
	    double line2gradient = calculateGradient(line2);
	    double line1c = calculateC(line1.getP1(), line1gradient);
	    double line2c = calculateC(line2.getP1(), line2gradient);
	    double x = (line2c - line1c) / (line1gradient - line2gradient);
	    double y = line1gradient * x + line1c;
	    if(x>=minLon && x<=maxLon && y>=minLat && y<=maxLat)
	    	return new Location(y, x);
	    else return null;
	}
	    
	private double calculateGradient(Line2D line){
	    return ( (line.getP2().getY() - line.getP1().getY()) / (line.getP2().getX() - line.getP1().getX()) );
	}
	    
	private double calculateC(Point2D point, double gradient){
	    return ( point.getY() - ( point.getX() * gradient ) );
	}
	
}
