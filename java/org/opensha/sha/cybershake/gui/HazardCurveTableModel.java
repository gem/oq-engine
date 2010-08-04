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
import java.util.HashMap;

import javax.swing.table.AbstractTableModel;

import org.opensha.sha.cybershake.db.CybershakeHazardCurveRecord;
import org.opensha.sha.cybershake.db.CybershakeIM;
import org.opensha.sha.cybershake.db.CybershakeRun;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.HazardCurve2DB;
import org.opensha.sha.cybershake.db.Runs2DB;
import org.opensha.sha.cybershake.db.SiteInfo2DB;

public class HazardCurveTableModel extends AbstractTableModel {
	
	public static int NUM_COLUMNS = 10;
	
	private HazardCurve2DB curve2db;
	private SiteInfo2DB site2db;
	private Runs2DB runs2db;
	
	private ArrayList<CybershakeHazardCurveRecord> curves = new ArrayList<CybershakeHazardCurveRecord>();
	private ArrayList<CybershakeRun> runs = new ArrayList<CybershakeRun>();
	
	private HashMap<Integer, CybershakeSite> siteID_NameMap = new HashMap<Integer, CybershakeSite>();
	private HashMap<Integer, CybershakeIM> imTypeMap = new HashMap<Integer, CybershakeIM>();
	
	public HazardCurveTableModel(DBAccess db) {
		this.curve2db = new HazardCurve2DB(db);
		this.site2db = new SiteInfo2DB(db);
		this.runs2db = new Runs2DB(db);
		
		this.reloadCurves();
	}
	
	public CybershakeRun getRunForCurve(CybershakeHazardCurveRecord curve) {
		for (CybershakeRun run : runs) {
			if (run.getRunID() == curve.getRunID())
				return run;
		}
		return null;
	}
	
	public void reloadCurves() {
		curves = curve2db.getAllHazardCurveRecords();
		runs = runs2db.getRuns();
		for (CybershakeHazardCurveRecord curve : curves) {
			CybershakeRun run = getRunForCurve(curve);
			CybershakeSite site = siteID_NameMap.get(run.getSiteID());
			if (site == null) {
				site = site2db.getSiteFromDB(run.getSiteID());
				siteID_NameMap.put(site.id, site);
			}
			CybershakeIM im = imTypeMap.get(curve.getImTypeID());
			if (im == null) {
				im = curve2db.getIMFromID(curve.getImTypeID());
				imTypeMap.put(im.getID(), im);
			}
		}
		this.fireTableDataChanged();
	}

	public int getColumnCount() {
		return NUM_COLUMNS;
	}

	public int getRowCount() {
		return curves.size();
	}
	
	// columns:
	// 0: CurveID | 1: Site_ID | 2: Site Short Name | 3: Site Long Name | 4: Date | 5: ERF_ID | 6: IM_Type_ID |
	//		 7: SA Period | 8: Rup_Var_Scen_ID | 9: SGT_Var_ID 

	public String getColumnName(int col) {
		if (col == 0) {
			return "Curve ID";
		} else if (col == 1) {
			return "Site ID";
		} else if (col == 2) {
			return "Site Name";
		} else if (col == 3) {
			return "Site Long Name";
		} else if (col == 4) {
			return "Date";
		} else if (col == 5) {
			return "ERF ID";
		} else if (col == 6) {
			return "IM Type ID";
		} else if (col == 7) {
			return "SA Period";
		} else if (col == 8) {
			return "Rup Var Scen ID";
		} else if (col == 9) {
			return "SGT Var ID";
		}
		
		return "";
	}
	
	public CybershakeHazardCurveRecord getCurveAtRow(int row) {
		row = this.getRowCount() - row - 1;
		return curves.get(row);
	}

	public Object getValueAt(int row, int col) {
		CybershakeHazardCurveRecord curve = getCurveAtRow(row);
		CybershakeRun run = getRunForCurve(curve);
		
		if (col == 0) {
			return curve.getCurveID();
		} else if (col == 1) {
			return run.getSiteID();
		} else if (col == 2) {
			CybershakeSite site = siteID_NameMap.get(run.getSiteID());
			return site.short_name;
		} else if (col == 3) {
			CybershakeSite site = siteID_NameMap.get(run.getSiteID());
			return site.name;
		} else if (col == 4) {
			return curve.getDate();
		} else if (col == 5) {
			return run.getERFID();
		} else if (col == 6) {
			return curve.getImTypeID();
		} else if (col == 7) {
			CybershakeIM im = imTypeMap.get(curve.getImTypeID());
			return im.getVal();
		} else if (col == 8) {
			return run.getRupVarScenID();
		} else if (col == 9) {
			return run.getSgtVarID();
		}
		
		return null;
	}

}
