package scratch.marco;

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

public class SiteRuptureDistanceCalculator {
	
	private Site site;
	private EqkRupture rupture;

	/**
	 * 
	 * @param site
	 * @param rupture
	 */
	public SiteRuptureDistanceCalculator(Site site, EqkRupture rupture){
		this.site = site;
		this.rupture = rupture;
	}
	
	/**
	 * This method computes the shortest distance from the surface rupture 
	 * @return minDis
	 */
	public double getRRupDistance(){
		EvenlyGriddedSurfaceAPI rupSurf =  this.rupture.getRuptureSurface();
		Location loc = site.getLocation();
		double minDis = 1e100; 
		for (int i=0; i < rupSurf.getNumRows(); i++){
			for (int j=0; j < rupSurf.getNumCols(); j++){
				double dst = LocationUtils.linearDistance(loc, rupSurf.getLocation(i,j));
				if (dst < minDis) minDis = dst;
			}
		}
		return minDis;
	}
	
	/**
	 * This method computes the shortest distance from the surface projection of rupture as 
	 * originally proposed by Joyner and Boore  
	 * @return minDis
	 */
	public double getJBDistance(){
		 EvenlyGriddedSurfaceAPI rupSurf =  this.rupture.getRuptureSurface();
		 Location loc = site.getLocation();
		 double minDis = 1e100;
		 // Loop over the left side of the rupture
		 for (int i=0; i < rupSurf.getNumRows(); i++){
			 double dis = LocationUtils.horzDistance(loc,rupSurf.getLocation(i,0));
			 if (minDis>dis)minDis=dis;
		 }	 
		// Loop over the bottom side of the rupture
		 for (int i=0; i < rupSurf.getNumCols(); i++){
			 double dis = LocationUtils.horzDistance(loc,rupSurf.getLocation(rupSurf.getNumRows()-1,i));
			 if (minDis>dis)minDis=dis;
		 } 
		// Loop over the right side of the rupture
		 for (int i=0; i < rupSurf.getNumRows(); i++){
			 double dis = LocationUtils.horzDistance(loc,rupSurf.getLocation(i,rupSurf.getNumCols()-1));
			 if (minDis>dis) minDis=dis;
		 }
		// Loop over the top side of the rupture
		 for (int i=0; i < rupSurf.getNumCols(); i++){
			 double dis = LocationUtils.horzDistance(loc,rupSurf.getLocation(0,i));
			 if (minDis>dis) minDis=dis;
		 }
		 return minDis;
	}
}
