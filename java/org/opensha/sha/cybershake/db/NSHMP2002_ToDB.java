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



import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;


/**
 * This Class creates an instances of Frankel02/NHSMP02 ERF to insert into the database
 * @author vipingupta
 *
 */
public class NSHMP2002_ToDB extends ERF2DB {
	
	public NSHMP2002_ToDB(DBAccess db){
		super(db);
		createFrankel02ERF();
	}
	
	 /**
	  * Create NSHMP 02 ERF instance
	  *
	  */
	  private void createFrankel02ERF() {

	    
		eqkRupForecast = new Frankel02_AdjustableEqkRupForecast();
		
		// exclude Background seismicity
	    eqkRupForecast.getAdjustableParameterList().getParameter(
	        Frankel02_AdjustableEqkRupForecast.
	        BACK_SEIS_NAME).setValue(Frankel02_AdjustableEqkRupForecast.
	                                 BACK_SEIS_EXCLUDE);
	    // Stirling's representation
	    eqkRupForecast.getAdjustableParameterList().getParameter(
	      Frankel02_AdjustableEqkRupForecast.FAULT_MODEL_NAME).setValue(
	    		  Frankel02_AdjustableEqkRupForecast.FAULT_MODEL_STIRLING);
	    // Rup offset
	    eqkRupForecast.getAdjustableParameterList().getParameter(
	      Frankel02_AdjustableEqkRupForecast.RUP_OFFSET_PARAM_NAME).setValue(
	        new Double(5.0));
	    // duration
	    eqkRupForecast.getTimeSpan().setDuration(1.0);
	    eqkRupForecast.updateForecast();
	  }
}
