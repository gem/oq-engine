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

import java.util.ArrayList;

import org.opensha.sha.earthquake.EqkRupForecast;

public class CybershakeSiteManager {
	
	public static boolean insertCybershakeSite(DBAccess db, CybershakeSite site, EqkRupForecast erf, int erfID, double cutoffDistance, int typeID) {
		SiteInfo2DB site2db = new SiteInfo2DB(db);
		CybershakeSiteInfo2DB csSite2db = new CybershakeSiteInfo2DB(db);
		System.out.println("Inserting site: " + site.getFormattedName());
		
		// CyberShake_Sites table
		System.out.println("Inserting site record");
		csSite2db.putCybershakeLocationInDB(site.name, site.short_name, site.lat, site.lon);
		int siteID = csSite2db.getCybershakeSiteId(site.short_name);
		if (siteID < 0) {
			System.out.println("Error inserting site record!");
			return false;
		}
		System.out.println("Site inserted with ID=" + siteID);
		
		System.out.println("Setting site type to " + typeID);
		site2db.setSiteType(siteID, typeID);
		
		CybershakeSiteInfo2DB.CUT_OFF_DISTANCE = cutoffDistance;
		
		// CyberShake_Site_Regional_Bounds table
		System.out.println("Inserting regional bounds");
		csSite2db.putCyberShakeLocationRegionalBounds(erf, erfID, siteID, site.lat, site.lon, false);
		
		System.out.println("Inserting Source Rupture info");
		csSite2db.putCyberShakeLocationSrcRupInfo(erf, erfID, siteID, site.lat, site.lon, false, null);
		
		System.out.println("DONE inserting site!");
		
		return true;
	}
	
	public static boolean deleteCybershakeSite(DBAccess db, CybershakeSite site) {
		HazardCurve2DB curve2db = new HazardCurve2DB(db);
		PeakAmplitudesFromDB amps2db = new PeakAmplitudesFromDB(db);
		SiteInfo2DB site2db = new SiteInfo2DB(db);
		
		System.out.println("Deleting site: " + site.getFormattedName());
		
		// first delete hazard curves:
		System.out.println("Deleting all hazard curves...");
		ArrayList<CybershakeHazardCurveRecord> curves = curve2db.getHazardCurveRecordsForSite(site.id);
		if (curves != null) {
			for (CybershakeHazardCurveRecord curve: curves) {
				System.out.println("Deleting curve " + curve.getCurveID());
				curve2db.deleteHazardCurve(curve.getCurveID());
			}
		}
		
		System.out.println("Deleting all peak amplitudes...");
		int rows = amps2db.deleteAllAmpsForSite(site.id);
		System.out.println("Deleted " + rows + " amp rows");
		
		System.out.println("Deleting all site ruptures");
		rows = site2db.deleteRupturesForSite(site.id);
		System.out.println("Deleted " + rows + " site rupture rows");
		
		System.out.println("Deleting all site regional bounds");
		rows = site2db.deleteRegionsForSite(site.id);
		System.out.println("Deleted " + rows + " site regional bounds");
		
		System.out.println("Deleting site record");
		rows = site2db.deleteSiteRecord(site.id);
		System.out.println("Deleted " + rows + " site records");
		
		return true;
	}
}
