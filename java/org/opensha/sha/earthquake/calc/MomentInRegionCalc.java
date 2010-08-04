/**
 * 
 */
package org.opensha.sha.earthquake.calc;

import java.util.Iterator;

import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;

/**
 * It calculates scalar moment in a region for a given ERF
 * @author vipingupta
 *
 */
public class MomentInRegionCalc {
	
	
	/**
	 * It calculates moment in Newton-meters in a region given an ERF.
	 * 
	 * @param erf EqkRupForecast to be used for calculating moment 
	 * @param region Polygon in which Moment  needs to be calculated
	 */
	public static double getMoment(EqkRupForecast erf, Region region) {
		int numSources = erf.getNumSources();
		double totMoment = 0, rupMoment=0;
		int numRups, totRupLocs, rupLocsInside;
		for(int srcIndex=0; srcIndex<numSources; ++srcIndex) {
			numRups = erf.getNumRuptures(srcIndex);
			for(int rupIndex=0; rupIndex<numRups; ++rupIndex) {
				ProbEqkRupture rupture = erf.getRupture(srcIndex, rupIndex);
				rupMoment = MomentMagCalc.getMoment(rupture.getMag());
				Iterator it = rupture.getRuptureSurface().getLocationsIterator();
				totRupLocs=0;
				rupLocsInside=0;
				// find the fraction of rupture within the polygon
				while(it.hasNext()) {
					Location loc = (Location)it.next();
					++totRupLocs;
					if(region.contains(loc)) ++rupLocsInside;
				}
				totMoment = totMoment + rupMoment*((double)rupLocsInside)/totRupLocs;
			}
		}
		return totMoment;
	}

	
	
	public static void main(String args[]) {
		// all six regions for which moment needs to be calculated
		
		//REGION 1
		LocationList locList1 = new LocationList();
		locList1.add(new Location(40.5, -127));
		locList1.add(new Location(45, -122));
		locList1.add(new Location(41.75, -119.025));
		locList1.add(new Location(37.25, -124.025));
		Region region1 = new Region(locList1, BorderType.MERCATOR_LINEAR);
		
//		REGION 2
		LocationList locList2 = new LocationList();
		locList2.add(new Location(37.25, -124.025));
		locList2.add(new Location(41.75, -119.025));
		locList2.add(new Location(41, -118.35));
		locList2.add(new Location(36.5, -123.35));
		Region region2 = new Region(locList2, BorderType.MERCATOR_LINEAR);

//		REGION 3
		LocationList locList3 = new LocationList();
		locList3.add(new Location(36.5, -123.35));
		locList3.add(new Location(41, -118.35));
		locList3.add(new Location(39.5, -117));
		locList3.add(new Location(35, -122));
		Region region3 = new Region(locList3, BorderType.MERCATOR_LINEAR);

//		REGION 4
		LocationList locList4 = new LocationList();
		locList4.add(new Location(35, -122));
		locList4.add(new Location(39.5, -117));
		locList4.add(new Location(37.5, -115.2));
		locList4.add(new Location(33, -120.2));
		Region region4 = new Region(locList4, BorderType.MERCATOR_LINEAR);

//		REGION 5
		LocationList locList5 = new LocationList();
		locList5.add(new Location(33, -120.2));
		locList5.add(new Location(37.5, -115.2));
		locList5.add(new Location(36.75, -114.525));
		locList5.add(new Location(32.25, -119.525));
		Region region5 = new Region(locList5, BorderType.MERCATOR_LINEAR);

//		REGION 6
		LocationList locList6 = new LocationList();
		locList6.add(new Location(32.25, -119.525));
		locList6.add(new Location(36.75, -114.525));
		locList6.add(new Location(34, -112));
		locList6.add(new Location(29.5, -117));
		Region region6 = new Region(locList6, BorderType.MERCATOR_LINEAR);

		
		// ERF
		UCERF2 ucerf2 = new UCERF2();
		ucerf2.updateForecast();
		
		System.out.println(MomentInRegionCalc.getMoment(ucerf2, region1));
		System.out.println(MomentInRegionCalc.getMoment(ucerf2, region2));
		System.out.println(MomentInRegionCalc.getMoment(ucerf2, region3));
		System.out.println(MomentInRegionCalc.getMoment(ucerf2, region4));
		System.out.println(MomentInRegionCalc.getMoment(ucerf2, region5));
		System.out.println(MomentInRegionCalc.getMoment(ucerf2, region6));
	}
	
}
