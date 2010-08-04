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

package org.opensha.sha.cybershake.db;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.ListIterator;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGridCenteredSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

public class CybershakeSiteInfo2DB {

	
	public static double CUT_OFF_DISTANCE = 200;
	private SiteInfo2DBAPI site2db;
	private ERF2DBAPI erf2db = null;
	private BufferedWriter out = null;
	private boolean logging = false;
	private boolean forceAddRuptures = false;
	
	private boolean matchSourceNames = false;
	HashMap<Integer, Integer> sourceMap = null;
	
	public CybershakeSiteInfo2DB(DBAccess db){
		site2db = new SiteInfo2DB(db);
		erf2db = new ERF2DB(db);
	}
	
	public void setMatchSourceNames(boolean match) {
		matchSourceNames = match;
	}
	
	
	
	/**
	 * Puts the Cybershake locations in the database
	 * @param siteName
	 * @param siteShortName
	 * @param siteLat
	 * @param siteLon
	 * @returns the SiteId from the database
	 */
	public int  putCybershakeLocationInDB(String siteName,String siteShortName,double siteLat,double siteLon){
	    return site2db.insertSite(siteName, siteShortName, siteLat, siteLon);
	}
	
	/**
	 * Returns the CyberShake site id for the corresponding Cybershake short site name in the database
	 * @param cybershakeShortSiteName
	 * @return
	 */
	public int getCybershakeSiteId(String cybershakeShortSiteName){
		return site2db.getSiteId(cybershakeShortSiteName);
	}
	
	/**
	 * Returns the Cybershake site id for the corresponding location with given Lat and Lon.
	 * @param lat
	 * @param lon
	 * @return
	 */
	public int getCybershakeSiteId(double lat,double lon){
		return site2db.getSiteId(lat, lon);
	}
	

	/**
	 * Finds all the ruptures that have any location on their surface within Cybershake location
	 * circular regional bounds.
	 * @param erf
	 * @param erfId
	 * @param siteId
	 * @param locLat
	 * @param locLon
	 */
	public ArrayList<int[]> putCyberShakeLocationSrcRupInfo(EqkRupForecastAPI eqkRupForecast,int erfId,
			int siteId,double locLat,double locLon) {
		return putCyberShakeLocationSrcRupInfo(eqkRupForecast, erfId, 
				siteId, locLat, locLon, false);
	}
	
	/**
	 * Finds all the ruptures that have any location on their surface within Cybershake location
	 * circular regional bounds with option to add ruptures that are not already in database.
	 * @param erf
	 * @param erfId
	 * @param siteId
	 * @param locLat
	 * @param locLon
	 * @param checkAddRup make sure rupture is in DB, and if not, add it
	 */
	public ArrayList<int[]> putCyberShakeLocationSrcRupInfo(
			EqkRupForecastAPI eqkRupForecast, int erfId, int siteId,
			double locLat, double locLon, boolean checkAddRup) {
		return putCyberShakeLocationSrcRupInfo(eqkRupForecast, erfId, 
				siteId, locLat, locLon, checkAddRup, "");
	}
	
	private HashMap<Integer, Integer> getSourceMatchMap(EqkRupForecastAPI eqkRupForecast, int erfID) {
		if (sourceMap == null) {
			sourceMap = new HashMap<Integer, Integer>();
			
			for (int sourceID=0; sourceID<eqkRupForecast.getNumSources(); sourceID++) {
				String name = eqkRupForecast.getSource(sourceID).getName();
				
				int csID = this.erf2db.getSourceIDFromName(erfID, name);
				
				if (csID >= 0) {
					sourceMap.put(sourceID, csID);
					System.out.println("Matched source " + sourceID + " with DB source " + csID);
				} else {
//					System.out.println("Source " + name + " not in DB!");
				}
			}
		}
		
		return sourceMap;
	}
	
	private int getCSSourceID(EqkRupForecastAPI eqkRupForecast, int erfID, int erfSourceID) {
		int csSource = erfSourceID;
		
		if (matchSourceNames) {
			HashMap<Integer, Integer> map = this.getSourceMatchMap(eqkRupForecast, erfID);
			if (map == null) {
				System.err.println("WHAT?????????????");
			}
			System.out.print("Matching sourceID " + erfSourceID + "...");
			if (map.containsKey(erfSourceID)) {
				csSource = map.get(erfSourceID);
				System.out.println(csSource);
			} else {
				System.out.println("it's not in there!");
			}
		}
		
		return csSource;
	}
	
	/**
	 * Finds all the ruptures that have any location on their surface within Cybershake location
	 * circular regional bounds with option to add ruptures that are not already in database (with logging).
	 * @param erf
	 * @param erfId
	 * @param siteId
	 * @param locLat
	 * @param locLon
	 * @param checkAddRup make sure rupture is in DB, and if not, add it
	 * @param addLogFileName filename to log to (no logging if empty)
	 */
	public ArrayList<int[]> putCyberShakeLocationSrcRupInfo(
			EqkRupForecastAPI eqkRupForecast, int erfId, int siteId,
			double locLat, double locLon, boolean checkAddRup, String addLogFileName) {
		Location loc = new Location(locLat, locLon);
		Region region = new Region(loc,CUT_OFF_DISTANCE);
		int numSources = eqkRupForecast.getNumSources();
		
		ArrayList<int[]> newRups = new ArrayList<int[]>();

		// Going over each and every source in the forecast
		int count = 0;
		for (int sourceIndex = 0; sourceIndex < numSources; ++sourceIndex) {
			
			if (sourceIndex < this.skipSource)
				continue;
			this.skipSource = -1;
			
			int csSource = getCSSourceID(eqkRupForecast, erfId, sourceIndex);
			
			// get the ith source
			ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);
			int numRuptures = source.getNumRuptures();
			
			ArrayList<Integer> rupsToAdd = new ArrayList<Integer>();

			// going over all the ruptures in the source
			for (int rupIndex = 0; rupIndex < numRuptures; ++rupIndex) {
				
				if (rupIndex < this.skipRup)
					continue;
				this.skipRup = -1;
				
				ProbEqkRupture rupture = source.getRupture(rupIndex);

				EvenlyGriddedSurfaceAPI rupSurface = new EvenlyGridCenteredSurface(
						rupture.getRuptureSurface());

				// getting the iterator for all points on the rupture
				ListIterator it = rupSurface.getAllByRowsIterator();
				// looping over all the rupture pt locations and if any of those
				// lies
				// within the provided distance range then include the rupture
				// in the list.
				long start = 0;
				if (Cybershake_OpenSHA_DBApplication.timer) {
					start = System.currentTimeMillis();
				}
				boolean log = addLogFileName != null && addLogFileName.length() > 0;
				while (it.hasNext()) {
					Location ptLoc = (Location) it.next();
					if (region.contains(ptLoc)) {
						if (Cybershake_OpenSHA_DBApplication.timer) {
							System.out.println("Found one inside at " + (System.currentTimeMillis() - start) + " milliseconds");
						}
						//check if the rupture is there
						if (checkAddRup || this.forceAddRuptures) {
							//check if it's a dup
							if (this.site2db.isSiteRupInDB(erfId, sourceIndex, rupIndex, siteId)) {
								System.out.println("It's a duplicate...skipping!");
								break;
							}
							if (this.forceAddRuptures || !this.site2db.isRupInDB(erfId, sourceIndex, rupIndex)) { //it's not in the database
								if (this.forceAddRuptures) {
									if (count % 100 == 0) {
										System.out.println("Adding rupture " + count);
									}
								} else
									System.out.println("Rupture " + sourceIndex + " " + rupIndex + " not in DB, adding...");
								//log it
								if (log) {
									int newRupToAdd[] = {sourceIndex, rupIndex};
									newRups.add(newRupToAdd);
									try {
										if (out == null) {
											out = new BufferedWriter(new FileWriter(addLogFileName));
											logging = true;
										}
										out.append(sourceIndex + " " + rupIndex + "\n");
										out.flush();
									} catch (IOException e) {
										e.printStackTrace();
									}
								}
								//add it
								erf2db.insertSrcRupInDB(eqkRupForecast, erfId, sourceIndex, rupIndex);
								//flush log in case something bad happens
								if (addLogFileName.length() > 0) {
									try {
										out.flush();
									} catch (IOException e) {
										e.printStackTrace();
									}
								}
							}
						}
						long start2 = 0;
						if (Cybershake_OpenSHA_DBApplication.timer) {
							System.out.println("Done checking at " + (System.currentTimeMillis() - start) + " milliseconds");
							start2 = System.currentTimeMillis();
						}
//						System.out.println("Inserting Rupture " + sourceIndex + ", " + rupIndex + " for site " + siteId);
						rupsToAdd.add(rupIndex);
//						this.site2db.insertSite_RuptureInfo(siteId, erfId,
//								sourceIndex, rupIndex, CUT_OFF_DISTANCE);
						count++;
						if (Cybershake_OpenSHA_DBApplication.timer) {
							long total2 = (System.currentTimeMillis() - start2);
					    	System.out.println("Took " + total2 + " miliseconds to insert site rupture info!");
						}
						break;
					}
				}
				if (Cybershake_OpenSHA_DBApplication.timer) {
					long total = (System.currentTimeMillis() - start);
					System.out.println("Took " + total + " miliseconds to check and insert site rupture info!");
				}
			}
			
			// add the list
			if (rupsToAdd.size() > 0) {
				System.out.println("Inserting " + rupsToAdd.size() + " ruptures for Site=" + siteId + " and source=" + sourceIndex);
				
				this.site2db.insertSite_RuptureInfoList(siteId, erfId, csSource, rupsToAdd, CUT_OFF_DISTANCE);
			}
			
		}
		return newRups;
	}
	
	private int skipSource = -1;
	
	public void setSkipToSource(int source) {
		this.skipSource = source;
	}
	
	private int skipRup = -1;
	
	public void setSkipToRup(int rup) {
		this.skipRup = rup;
	}
	
	public void setForceAddRuptures(boolean force) {
		this.forceAddRuptures = force;
	}
	
	public void closeWriter() {
		if (logging) {
			try {
				out.close();
				logging = false;
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
	}
	
	/**
	 * Computes the regional bounds for the given cybershake and puts in the
	 * database. Also put the ruptureId and sourceId from ERF that dictates the
	 * min/max lat/lon for the region.
	 * 
	 * @param eqkRupForecast
	 * @param erfId
	 * @param siteId
	 * @param locLat
	 * @param locLon
	 * @param update - update bounds, don't reinsert
	 */
	public void putCyberShakeLocationRegionalBounds(EqkRupForecastAPI eqkRupForecast,int erfId, int siteId,
			                                        double locLat,double locLon, boolean update){
		
		Location loc = new Location(locLat,locLon);
		Region region = new Region(loc,CUT_OFF_DISTANCE);
		
	    int numSources = eqkRupForecast.getNumSources();

	    double minLat = Double.POSITIVE_INFINITY;
	    int minLatRupId = -1,minLatSrcId= -1;
	    double maxLat = Double.NEGATIVE_INFINITY;
	    int maxLatRupId =-1,maxLatSrcId=-1;
	    double minLon = Double.POSITIVE_INFINITY;
	    int minLonRupId =-1,minLonSrcId = -1;
	    double maxLon = Double.NEGATIVE_INFINITY;
	    int maxLonRupId = -1, maxLonSrcId =-1;

	    //Going over each and every source in the forecast
	    for (int sourceIndex = 0; sourceIndex < numSources; ++sourceIndex) {
	      // get the ith source
	      ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);
	      int numRuptures = source.getNumRuptures();
	      
	      int csSource = getCSSourceID(eqkRupForecast, erfId, sourceIndex);

	      //going over all the ruptures in the source
	      for (int rupIndex = 0; rupIndex < numRuptures; ++rupIndex) {
	        ProbEqkRupture rupture = source.getRupture(rupIndex);

	        EvenlyGriddedSurfaceAPI rupSurface = new EvenlyGridCenteredSurface(rupture.getRuptureSurface());

	        //getting the iterator for all points on the rupture
	        ListIterator it = rupSurface.getAllByRowsIterator();
	        boolean rupInside = false;
	        //looping over all the rupture pt locations and if any of those lies
	        //within the provided distance range then include the rupture in the list.
	        while (it.hasNext()) {
	          Location ptLoc = (Location) it.next();
	          if (region.contains(ptLoc)) {
	            rupInside = true;
	            break;
	          }
	        }
	        it = rupSurface.getAllByRowsIterator();
	        while (it.hasNext() && rupInside) {
	          Location ptLoc = (Location) it.next();
	          double lat = ptLoc.getLatitude();
	          double lon = ptLoc.getLongitude();
	          if (lat < minLat){
	            minLat = lat;
	            minLatRupId = rupIndex;
	            minLatSrcId = csSource;
	          }
	          if (lat > maxLat){
	            maxLat = lat;
	            maxLatRupId = rupIndex;
	            maxLatSrcId = csSource;
	          }
	          if (lon < minLon){
	            minLon = lon;
	            minLonRupId = rupIndex;
	            minLonSrcId = csSource;
	          }
	          if (lon > maxLon){
	            maxLon = lon;
	            maxLonRupId = rupIndex;
	            maxLonSrcId = csSource;
	          }
	        }
	      }
	    }
	    long start = 0;
	    if (Cybershake_OpenSHA_DBApplication.timer) {
	    	start = System.currentTimeMillis();
	    }
	    if (update) {
	    	site2db.updateSiteRegionalBounds(siteId, erfId,CUT_OFF_DISTANCE,
                    maxLat, maxLatSrcId, maxLatRupId, minLat,
                    minLatSrcId, minLatRupId, maxLon, maxLonSrcId, 
                    maxLonRupId, minLon, minLonSrcId, minLonRupId);
	    } else {
	    	site2db.insertSiteRegionalBounds(siteId, erfId,CUT_OFF_DISTANCE,
                    maxLat, maxLatSrcId, maxLatRupId, minLat,
                    minLatSrcId, minLatRupId, maxLon, maxLonSrcId, 
                    maxLonRupId, minLon, minLonSrcId, minLonRupId);
	    }
	    if (Cybershake_OpenSHA_DBApplication.timer) {
	    	long total = (System.currentTimeMillis() - start);
	    	System.out.println("Took " + total + " miliseconds to insert regional bounds!");
	    }
	}
	
	
	
	/**
	 * 
	 * @returns the list of cybershake sites
	 */
	public ArrayList<String> getCS_SitesList(){
		return site2db.getAllSites();
	}
	
	
	/**
	 * 
	 * @returns the list of all Cybershake Site Locations
	 */
	public LocationList getCS_SitesListLocations(){
		return site2db.getAllSitesLocation();
	}
	
	/**
	 * 
	 * @param siteShortName short site name as in database for Cybershake site
	 * @returns the Earthquake rupture forecast source id's for a given cybershake site.
	 */
	public ArrayList<Integer> getSrcIDsForSite(String csSiteName, int erfID){;
		return site2db.getSrcIdsForSite(csSiteName, erfID);
	}
	
	/**
	 * 
	 * @param siteShortName
	 * @param srcId
	 * @returns the list of rupture ids 
	 */
	public ArrayList<Integer> getRupIDsForSite(String csSiteName, int erfID, int srcID){
		return site2db.getRupIdsForSite(csSiteName, erfID, srcID);
	}
	
	
	/**
	 * 
	 * @param csSiteName
	 * @returns the Geographic locaton for the given Cybershake site
	 */
	public Location getCyberShakeSiteLocation(String csSiteName){
		return site2db.getLocationForSite(csSiteName);
	}
	
	/**
	 * Gets a CybershakeSite from the Database
	 * @param shortName
	 * @return
	 */
	public CybershakeSite getSiteFromDB(String shortName) {
		return site2db.getSiteFromDB(shortName);
	}
	
	/**
	 * Gets a CybershakeSite from the Database
	 * @param shortName
	 * @return
	 */
	public CybershakeSite getSiteFromDB(int siteID) {
		return site2db.getSiteFromDB(siteID);
	}
	
	/**
	 * Gets all CybershakeSite's from the Database
	 * @return
	 */
	public ArrayList<CybershakeSite> getAllSitesFromDB() {
		return site2db.getAllSitesFromDB();
	}
	
	
	public static void main(String args[]) {
		HashMap<Integer, Integer> map = new HashMap<Integer, Integer>();
		
		map.put(3, 5);
		
		System.out.println(map.get(3));
		System.out.println(map.get(new Integer(3)));
		
//		CybershakeSiteInfo2DB site2db = new CybershakeSiteInfo2DB(Cybershake_OpenSHA_DBApplication.db);
		
//		site2db.
	}
	

}
