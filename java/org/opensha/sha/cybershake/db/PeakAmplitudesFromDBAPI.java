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

import java.sql.SQLException;
import java.util.ArrayList;

public interface PeakAmplitudesFromDBAPI {

	/**
	 * @returns the supported SA Period as list of strings.
	 */
	public ArrayList<CybershakeIM>  getSupportedIMs();
	
	/**
	 * @returns the supported SA Period as list of strings.
	 */
	public ArrayList<CybershakeIM>  getSupportedIMs(int runID);
	
	/**
	 * 
	 * @param erfId
	 * @param srcId
	 * @param rupId
	 * @returns the rupture variation ids for the rupture
	 */
	public ArrayList<Integer> getRupVarationsForRupture(int erfId,int srcId, int rupId);
	
	/**
	 * 
	 * @param siteId
	 * @param erfId
	 * @param srcId
	 * @param rupId
	 * @param rupVarId
	 * @returns the IM Value for the particular IM type
	 */
	public double getIM_Value(int runID, int srcId,int rupId,int rupVarId, CybershakeIM im);
	
	/**
	 * 
	 * @param siteId
	 * @param erfId
	 * @param srcId
	 * @param rupId
	 * @throws SQLException 
	 * @returns the a list of IM Values for the particular IM type
	 */
	public ArrayList<Double> getIM_Values(int runID, int srcId,int rupId, CybershakeIM im) throws SQLException;
	
	/**
	  * @return all possible SGT Variation IDs
	  */
	public ArrayList<Integer> getSGTVarIDs();
	
	/**
	 * @return all possible Rup Var Scenario IDs
	 */
	public ArrayList<Integer> getRupVarScenarioIDs();
	
	/**
	 * delete all peak amplitudes for a given site
	 * @param siteId
	 * @return
	 */
	public int deleteAllAmpsForSite(int siteID);
	
	/**
	 * delete all peak amplitudes for a given run
	 * @param siteId
	 * @return
	 */
	public int deleteAmpsForRun(int runID);
}
