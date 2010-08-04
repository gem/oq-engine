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

package org.opensha.sha.cybershake.openshaAPIs;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.cybershake.db.CybershakeERF;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.ERF2DB;
import org.opensha.sha.cybershake.db.PeakAmplitudesFromDB;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;

public class CyberShakeERF extends EqkRupForecast {
	
	private static final boolean SAVE_OBJECTS = false;

	ArrayList<CyberShakeProbEqkSource> sources = new ArrayList<CyberShakeProbEqkSource>();

	public static final String ERF_ID_SELECTOR_PARAM = "Earthquake Rupture Forecast";

	//SA Period selection param
	private StringParameter erfParam;
	ArrayList<String> erfNames;
	ArrayList<CybershakeERF> erfs;

	DBAccess db = null;
	PeakAmplitudesFromDB ampsDB = null;
	ERF2DB erf2db = null;

	CybershakeERF selectedERF = null;

	boolean updated = false;

	public CyberShakeERF() {
		super();

		this.initParams();
	}
	
	private void checkInitDB() {
		if (db == null) {
			db = Cybershake_OpenSHA_DBApplication.db;
			erf2db = new ERF2DB(db);
			ampsDB = new PeakAmplitudesFromDB(db);
		}
	}
	
	private void checkLoadIDs() {
		if (erfs == null) {
			this.loadERFIDs();
		}
	}

	private void loadERFIDs() {
		checkInitDB();
		
		System.out.println("Loading ERF IDs");
		
		erfs = erf2db.getAllERFs();
		erfNames = new ArrayList<String>();
		for (CybershakeERF erf : erfs) {
			String name = erf.id + ": " + erf.description;
			erfNames.add(name);
		}
		selectedERF = erfs.get(0);
		erfParam = new StringParameter(ERF_ID_SELECTOR_PARAM, erfNames, erfNames.get(0));
		erfParam.addParameterChangeListener(this);
		adjustableParams.addParameter(erfParam);
	}

	private void initParams() {
		// no other params right now
	}

	@Override
	public ParameterList getAdjustableParameterList() {
		checkLoadIDs();
		return super.getAdjustableParameterList();
	}

	@Override
	public ListIterator getAdjustableParamsIterator() {
		checkLoadIDs();
		return super.getAdjustableParamsIterator();
	}

	@Override
	public int getNumSources() {
		return sources.size();
	}

	@Override
	public ProbEqkSource getSource(int source) {
		return sources.get(source);
	}

	@Override
	public ArrayList<CyberShakeProbEqkSource> getSourceList() {
		return sources;
	}

	public String getName() {
		return "CyberShake ERF";
	}

	@Override
	public void parameterChange(ParameterChangeEvent e) {
		super.parameterChange(e);

		String paramName = e.getParameterName();

		if (paramName.equals(ERF_ID_SELECTOR_PARAM)) {
			String val = (String)erfParam.getValue();
			selectedERF = erfs.get(erfNames.indexOf(val));
			System.out.println("New ERF: " + selectedERF);
			updated = false;
		}
	}

	public void updateForecast() {
		if (!updated) {
			checkInitDB();
			
			if (selectedERF == null) {
				loadERFIDs();
			}
			
			String fileName = "cyberShakeERFSources_" + this.selectedERF.id + ".obj";
			File objFile = new File(fileName);
			if (objFile.exists() && SAVE_OBJECTS) {
				sources = (ArrayList<CyberShakeProbEqkSource>)FileUtils.loadObject(fileName);
				updated = true;
			} else {
				long start = System.currentTimeMillis();
				sources = this.erf2db.getSources(this.selectedERF.id);
				double secs = (double)(System.currentTimeMillis() - start) / 1000d;
				System.out.println("Took " + secs + " seconds to update forecast!");
				updated = true;
				if (SAVE_OBJECTS) {
					try {
						FileUtils.saveObjectInFile(fileName, sources);
					} catch (IOException e) {
						// TODO Auto-generated catch block
						e.printStackTrace();
					}
				}
			}
		}
	}

}
