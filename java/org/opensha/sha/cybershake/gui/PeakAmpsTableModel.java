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

import javax.swing.JOptionPane;
import javax.swing.table.AbstractTableModel;

import org.opensha.sha.cybershake.db.CybershakeRun;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.PeakAmplitudesFromDB;
import org.opensha.sha.cybershake.db.SiteInfo2DB;

public class PeakAmpsTableModel extends AbstractTableModel {
	
	public static int NUM_COLUMNS = 8;
	
	PeakAmplitudesFromDB amps2db;
	SiteInfo2DB site2db;
	
	ArrayList<CybershakeRun> ampsRuns = new ArrayList<CybershakeRun>();
	
	HashMap<Integer, CybershakeSite> siteID_NameMap = new HashMap<Integer, CybershakeSite>();
	HashMap<String, Integer> countMap = new HashMap<String, Integer>();
	
	public PeakAmpsTableModel(DBAccess db) {
		this.amps2db = new PeakAmplitudesFromDB(db);
		this.site2db = new SiteInfo2DB(db);
		
		this.reloadAmps();
	}
	
	public void reloadAmps() {
		ampsRuns = amps2db.getPeakAmpRuns();
		
		for (CybershakeRun amp : ampsRuns) {
			int siteID = amp.getSiteID();
			
			CybershakeSite site = siteID_NameMap.get(siteID);
			
			if (site == null) {
				site = site2db.getSiteFromDB(siteID);
				siteID_NameMap.put(siteID, site);
			}
		}
		
		this.fireTableDataChanged();
	}

	public int getColumnCount() {
		return NUM_COLUMNS;
	}

	public int getRowCount() {
		return ampsRuns.size();
	}
	
	public void loadCount(int row) {
		CybershakeRun run = this.getAmpsAtRow(row);
		
		int count = this.amps2db.countAmps(run.getRunID(), null);
		
		countMap.put(run.toString(), new Integer(count));
	}
	
	public int deleteAmps(CybershakeRun record) {
		// if it's not a test site, prompt the user
		CybershakeSite site = getSiteForRecord(record);
		if (site.type_id != CybershakeSite.TYPE_TEST_SITE) {
			String title = "Really delete Peak Amplitudes?";
			String message = "Site '" + site.getFormattedName() + "' is not a test site!\n\n" +
					"Are you sure you want to delete the Amplitudes?";
			int response = JOptionPane.showConfirmDialog(null, message, title, JOptionPane.YES_NO_OPTION);
			
			if (response != JOptionPane.YES_OPTION)
				return -1;
		}
		
		int num = this.amps2db.deleteAmpsForRun(record.getRunID());
		
		return num;
	}
	
	// columns:
	// 0: Site_ID | 1: Site Short Name | 2: Site Long Name | 3: Run_ID | 4: ERF_ID |
	//		5: Rup_Var_Scen_ID | 6: SGT_Var_ID | 7: Count

	public String getColumnName(int col) {
		if (col == 0) {
			return "Site ID";
		} else if (col == 1) {
			return "Site Name";
		} else if (col == 2) {
			return "Site Long Name";
		} else if (col == 3) {
			return "Run ID";
		} else if (col == 4) {
			return "ERF ID";
		} else if (col == 5) {
			return "Rup Var Scen ID";
		} else if (col == 6) {
			return "SGT Var ID";
		} else if (col == 7) {
			return "Count";
		}
		
		return "";
	}
	
	public CybershakeRun getAmpsAtRow(int row) {
		row = this.getRowCount() - row - 1;
		return ampsRuns.get(row);
	}
	
	private CybershakeSite getSiteForRecord(CybershakeRun record) {
		return siteID_NameMap.get(record.getSiteID());
	}

	public Object getValueAt(int row, int col) {
		CybershakeRun amps = getAmpsAtRow(row);
		
		if (col == 0) {
			return amps.getSiteID();
		} else if (col == 1) {
			CybershakeSite site = getSiteForRecord(amps);
			return site.short_name;
		} else if (col == 2) {
			CybershakeSite site = getSiteForRecord(amps);
			return site.name;
		} else if (col == 3) {
			return amps.getRunID();
		} else if (col == 4) {
			return amps.getERFID();
		} else if (col == 5) {
			return amps.getRupVarScenID();
		} else if (col == 6) {
			return amps.getSgtVarID();
		} else if (col == 7) {
			Integer count = countMap.get(amps.toString());
			if (count == null) {
				return "(not counted)";
			} else {
				return count;
			}
		}
		
		return null;
	}

}
