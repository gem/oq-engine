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

package org.opensha.sha.cybershake.gui;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;

import javax.swing.table.AbstractTableModel;

import org.opensha.sha.cybershake.db.CybershakeHazardCurveRecord;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.CybershakeSiteType;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.HazardCurve2DB;
import org.opensha.sha.cybershake.db.SiteInfo2DB;

public class SitesTableModel extends AbstractTableModel {
	
	public static int NUM_COLUMNS = 8;
	
	DBAccess db;
	
	SiteInfo2DB site2db;
	HazardCurve2DB curve2db;
	
	ArrayList<CybershakeSite> sites;
	ArrayList<CybershakeSiteType> types;
	
	HashMap<String, Double> cutoffMap = new HashMap<String, Double>();
	HashMap<String, String> erfMap = new HashMap<String, String>();
	HashMap<String, CybershakeSiteType> typeMap = new HashMap<String, CybershakeSiteType>();
	HashMap<String, String> periodMap = new HashMap<String, String>();
	
	public SitesTableModel(DBAccess db) {
		this.db = db;
		
		this.site2db = new SiteInfo2DB(db);
		this.curve2db = new HazardCurve2DB(db);
		
		this.reloadSites();
	}
	
	public void reloadSites() {
		sites = site2db.getAllSitesFromDB();
		types = site2db.getSiteTypes();
		
		// load the cutoff distances
		for (CybershakeSite site : sites) {
			Double cutoff = cutoffMap.get(site.toString());
			
			if (cutoff == null) {
				cutoff = site2db.getSiteCutoffDistance(site.id);
				cutoffMap.put(site.toString(), cutoff);
			}
			
			CybershakeSiteType type = typeMap.get(sites.toString());
			
			if (type == null) {
				for (CybershakeSiteType newType : types) {
					if (newType.getID() == site.type_id) {
						typeMap.put(site.toString(), newType);
						break;
					}
				}
			}
			
			String erfs = erfMap.get(site.toString());
			
			if (erfs == null) {
				erfs = "";
				
				for (int erf : site2db.getERFsForSite(site.id)) {
					if (erfs.length() > 0)
						erfs += ",";
					erfs += erf;
				}
				if (erfs.length() == 0)
					erfs = "<None>";
				erfMap.put(site.toString(), erfs);
			}
			
			String periods = periodMap.get(site.toString());
			
			if (periods == null) {
				periods = "";
				
				ArrayList<CybershakeHazardCurveRecord> curves = curve2db.getHazardCurveRecordsForSite(site.id);
				
				if (curves != null) {
					Collections.sort(curves);
					for (CybershakeHazardCurveRecord curve : curves) {
						if (periods.length() > 0)
							periods += ",";
						double period = curve2db.getIMForCurve(curve.getCurveID()).getVal();
						period = (double)((int)(period * 100 + 0.5)) / 100d;
						periods += period;
					}
				}
				if (periods.length() == 0)
					periods = "<None>";
				periodMap.put(site.toString(), periods);
			}
		}
		
		this.fireTableDataChanged();
	}

	public int getColumnCount() {
		return NUM_COLUMNS;
	}

	public int getRowCount() {
		return sites.size();
	}
	
	// columns:
	// 0: Site_ID | 1: Site Short Name | 2: Site Long Name | 3: Location | 4: Type | 5: Cutoff Distance | 6: ERF(s) | 7: curves

	public String getColumnName(int col) {
		if (col == 0) {
			return "ID";
		} else if (col == 1) {
			return "Name";
		} else if (col == 2) {
			return "Long Name";
		} else if (col == 3) {
			return "Location";
		} else if (col == 4) {
			return "Type";
		} else if (col == 5) {
			return "Cutoff Distance";
		} else if (col == 6) {
			return "ERF(s)";
		} else if (col == 7) {
			return "Curve Period(s)";
		}
		
		return "";
	}

	public Object getValueAt(int row, int col) {
		CybershakeSite site = getSiteAtRow(row);
		
		if (col == 0) {
			return site.id;
		} else if (col == 1) {
			return site.short_name;
		} else if (col == 2) {
			return site.name;
		} else if (col == 3) {
			String loc = "(" + site.lat + ", " + site.lon + ")";
			return loc;
		} else if (col == 4) {
			CybershakeSiteType type = typeMap.get(site.toString());
			if (type == null)
				return "<None>";
			return type.getName();
		} else if (col == 5) {
			double dist = cutoffMap.get(site.toString());
			return dist;
		} else if (col == 6) {
			String erfs = erfMap.get(site.toString());
			return erfs;
		} else if (col == 7) {
			String periods = periodMap.get(site.toString());
			return periods;
		}
		
		return null;
	}
	
	public CybershakeSite getSiteAtRow(int row) {
		row = this.getRowCount() - row - 1;
		return sites.get(row);
	}

}
