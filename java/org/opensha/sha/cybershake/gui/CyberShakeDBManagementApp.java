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

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.util.FileUtils;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;

public class CyberShakeDBManagementApp {
	
	private DBAccess db;
	
	private HazardCurveGUI curves = null;
	private PeakAmpsGUI amps = null;
	private SitesGUI sites = null;
	
	private ChooserDialog choose;
	
	private boolean readOnly = false;
	
	public CyberShakeDBManagementApp(DBAccess db) {
		this.db = db;
		
		this.readOnly = db.isReadOnly();
		
		choose = new ChooserDialog(this);
		
		choose.setVisible(true);
	}
	
	public void showCurvesGUI() {
		if (curves == null) {
			curves = new HazardCurveGUI(db);
		}
		curves.setVisible(true);
	}
	
	public void showAmpsGUI() {
		if (amps == null) {
			amps = new PeakAmpsGUI(db);
		}
		amps.setVisible(true);
	}
	
	public void showSitesGUI() {
		if (sites == null) {
			sites = new SitesGUI(db);
		}
		sites.setVisible(true);
	}
	
	public boolean isReadOnly() {
		return readOnly;
	}
	
	public static String[] loadPassFile(String fileName) throws FileNotFoundException, IOException {
		String user = "";
		String pass = "";
		for (String line : (ArrayList<String>)FileUtils.loadFile(fileName)) {
			line = line.trim();
			if (line.startsWith("#"))
				continue;
			if (line.contains(":")) {
				String split[] = line.split(":");
				user = split[0];
				pass = split[1];
				break;
			}
		}
		String ret[] = { user, pass };
		return ret;
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		DBAccess db = null;
		
		String usage = "CyberShakeDBManagementApp [db_pass_file]";
		
		if (args.length == 1) {
			// if password file doesn't exist, ignore it
			if (!(new File(args[0])).exists()) {
				System.err.println("WARNING: Password file doesn't exist, ignoring: " + args[0]);
				args = new String[0];
			}
		}
		
		if (args.length == 0) {
			// prompt for pass
			while (db == null) {
				try {
					db = Cybershake_OpenSHA_DBApplication.getAuthenticatedDBAccess(true, true);
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}
		} else if (args.length == 1) {
			String dbPassFile = args[0];
			try {
				String user_pass[] = loadPassFile(dbPassFile);
				db = new DBAccess(Cybershake_OpenSHA_DBApplication.HOST_NAME, Cybershake_OpenSHA_DBApplication.DATABASE_NAME, 
						user_pass[0], user_pass[1]);
			} catch (FileNotFoundException e) {
				System.err.println("Password file doesn't exist!");
				System.exit(1);
			} catch (IOException e) {
				System.err.println("Error reading password file!");
				System.exit(1);
			}
		} else {
			System.out.println(usage);
			System.exit(-1);
		}
		
		new CyberShakeDBManagementApp(db);
	}

}
