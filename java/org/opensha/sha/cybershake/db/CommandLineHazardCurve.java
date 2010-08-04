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
import java.io.FileWriter;
import java.io.IOException;
import java.rmi.RemoteException;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2;
import org.opensha.sha.gui.infoTools.ConnectToCVM;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.util.SiteTranslator;


public class CommandLineHazardCurve implements ParameterChangeWarningListener {
	private static String HOSTNAME = "intensity.usc.edu";
	private static String DB_NAME = "CyberShake";
	private static double[] siteCoords = new double[2];

	 // site translator
	SiteTranslator siteTranslator = new SiteTranslator();
	
	private String site;
	private MeanUCERF2 meanUCERF2;
	private ScalarIntensityMeasureRelationshipAPI imr;		
	private ArbitrarilyDiscretizedFunc function;

	private String ERF_NAME = "WGCEP (2007) UCERF2 - Single Branch";
	private static final DBAccess db = new DBAccess(HOSTNAME,DB_NAME); 
	
	public static void main(String[] args) {
		if (args.length<3) {
			System.out.println("Usage:  java CommandLineHazardCurve <site> <sgt_variation_id> <rup_var_scenario_id>");
			System.exit(1);
		}
		String siteName = args[0];
		int sgtVariationID = Integer.parseInt(args[1]);
		int rupVarID = Integer.parseInt(args[2]);
		siteCoords = getSiteCoordinates(siteName);
		System.out.println(siteCoords[0] + " " + siteCoords[1]);
//		siteCoords[0] = 34.0192;
//		siteCoords[1] = -118.286;
		System.out.println("Preparing for curve generation.");
		CommandLineHazardCurve clhc = new CommandLineHazardCurve(siteName);
//		System.out.println("Calculating Attenuation curve.");
//		clhc.calcAttenuationCurve(siteName);
		System.out.println("Calculating CS curve.");
		clhc.calcCyberShakeCurve(siteName, sgtVariationID, rupVarID);
		System.exit(0);
	}
	
	private void calcCyberShakeCurve(String siteName, int sgtVariationID, int rupVarID) {
		HazardCurveComputation hazCurve = new HazardCurveComputation(db);
		ArrayList<Double> imlVals = new ArrayList<Double>();
		for(int i=0; i<function.getNum();++i)
			imlVals.add(function.getX(i));
		CybershakeIM im = new CybershakeIM(21, "spectral acceleration", 3.00003, "cm per sec squared");
		DiscretizedFuncAPI cyberShakeHazardData= hazCurve.computeHazardCurve(imlVals, siteName, ERF_NAME, sgtVariationID, rupVarID, im);
		System.out.println("Writing out CS file.");
		try {
		    FileWriter fr = new FileWriter(siteName + "_cybershake.txt");
		    for(int i=0;i<cyberShakeHazardData.getNum();++i) {
			fr.write(cyberShakeHazardData.getX(i)+" "+cyberShakeHazardData.getY(i)+"\n");
		    }
		    fr.flush();
		    fr.close();
	        } catch(IOException e) {
		    e.printStackTrace();
	        }
	}

	private void calcAttenuationCurve(String siteName) {
		HazardCurveCalculator hazCurveCalc;
		
		try {
			hazCurveCalc = new HazardCurveCalculator();
			setSiteParamsInIMR();
			Site site = new Site(new Location(siteCoords[0], siteCoords[1]), siteName);
			
			Iterator it = imr.getSiteParamsIterator();
			while(it.hasNext())  {
				site.addParameter((ParameterAPI)it.next());
			}

			//log the IML valuesbefore passing to HazardCurveCalculator
			DiscretizedFuncAPI logIML_Func = new ArbitrarilyDiscretizedFunc();
			for(int i=0; i<function.getNum(); ++i)
				logIML_Func.set(Math.log(function.getX(i)), 1);
			
			// calculate the hazard curve
			hazCurveCalc.getHazardCurve(logIML_Func, site, imr, meanUCERF2);
			
			// Unlog the IML values. The Y Values we get from hazardCurveCalculator are unmodified
			DiscretizedFuncAPI hazFunc = new ArbitrarilyDiscretizedFunc();
			for(int i=0; i<function.getNum(); ++i)
				hazFunc.set(function.getX(i), logIML_Func.getY(i));
			
			try {
				FileWriter fr = new FileWriter(site.getName() + ".txt");
				for(int i=0;i<hazFunc.getNum();++i) {
					fr.write(hazFunc.getX(i)+" "+hazFunc.getY(i)+"\n");
				}
				fr.flush();
				fr.close();
	        } catch(IOException e) {
	        	e.printStackTrace();
	        }
	        
		} catch (RemoteException e1) {
			e1.printStackTrace();
		}
		
	}
	
	/**
	   * set the site params in IMR according to basin Depth and vs 30
	   * @param imr
	   * @param lon
	   * @param lat
	   * @param willsClass
	   * @param basinDepth
	   */
	  private void setSiteParamsInIMR() {
		  LocationList locList = new LocationList();
		  locList.add(new Location(siteCoords[0],siteCoords[1]));
		  String willsClass = "NA";
		  double basinDepth = Double.NaN;
		  try{
			  // get the vs 30 and basin depth from cvm
			  willsClass = (String)(ConnectToCVM.getWillsSiteTypeFromCVM(locList)).get(0);
			  basinDepth = ((Double)(ConnectToCVM.getBasinDepthFromCVM(locList)).get(0)).doubleValue();
		  }catch(Exception ee){
			  ee.printStackTrace();
			  return;
		  }

		  Iterator it = imr.getSiteParamsIterator(); // get site params for this IMR
		  while(it.hasNext()) {
			  ParameterAPI tempParam = (ParameterAPI)it.next();
			  System.out.println("Param:"+tempParam.getName());
			  //adding the site Params from the CVM, if site is out the range of CVM then it
			  //sets the site with whatever site Parameter Value user has choosen in the application
			  boolean flag = siteTranslator.setParameterValue(tempParam,willsClass,basinDepth);
			  if( !flag ) {
				  String message = "cannot set the site parameter \""+tempParam.getName()+"\" from Wills class \""+willsClass+"\""+
				  "\n (no known, sanctioned translation - please set by hand)";
				  throw new RuntimeException(message);
			  }
		  }

	  }

	/**
	 *  Function that must be implemented by all Listeners for
	 *  ParameterChangeWarnEvents.
	 *
	 * @param  event  The Event which triggered this function call
	 */
	public void parameterChangeWarning(ParameterChangeWarningEvent e) {
		String S = " : parameterChangeWarning(): ";
		WarningParameterAPI param = e.getWarningParameter();
		param.setValueIgnoreWarning(e.getNewValue());
	}
	
	private static double[] getSiteCoordinates(String site) {
        try {
			ResultSet result = db.selectData("select CS_Site_Lat, CS_Site_Lon from CyberShake_Sites where CS_Site_Name='" + site + "'");
			result.first();
			if (result.getRow()==0) {
				System.err.println("Error in site query.");
				return null;
			}
			double[] latLon = new double[2];
			latLon[0] = result.getDouble("CS_Site_Lat");
			latLon[1] = result.getDouble("CS_Site_Lon");
			result.close();
			return latLon;
        } catch (SQLException e) {
			e.printStackTrace();
		}
        return null;
	}

	public CommandLineHazardCurve(String s) {
		site = s;
		setupERF();
		setupIMR();		

		// Generate Hazard Curves for SA 3.0s
		imr.setIntensityMeasure("SA");
		imr.getParameter(PeriodParam.NAME).setValue(3.0);
		System.out.println(imr.getParameter(AS_1997_AttenRel.SITE_TYPE_NAME).getValue());
		String imtString = "SA_3.0sec";
		createUSGS_SA_Function();// for SA
	}
	
	  /**
	   * initialises the function with the x and y values if the user has chosen the USGS-PGA X Vals
	   * the y values are modified with the values entered by the user
	   */
	  private void createUSGS_SA_Function(){
	    function= new ArbitrarilyDiscretizedFunc();
	 
	   /* function.set(.0025,1);
	    function.set(.00375,1);
	    function.set(.00563 ,1);
	    function.set(.00844,1);
	    function.set(.0127,1);
	    function.set(.0190,1);
	    function.set(.0285,1);
	    function.set(.0427,1);
	    function.set(.0641,1);
	    function.set(.0961,1);
	    function.set(.144,1);
	    function.set(.216,1);
	    function.set(.324,1);
	    function.set(.487,1);
	    function.set(.730,1);
	    function.set(1.09,1);
	    function.set(1.64,1);
	    function.set(2.46,1);
	    function.set(3.69,1);
	    function.set(5.54,1);*/
	    //new function mirroring the gui app
	    function.set(0.0001,1);
	    function.set(0.00013,1);
		function.set(0.00016,1);
		function.set(0.0002,1);
		function.set(0.00025,1);
		function.set(0.00032,1);
		function.set(0.0004,1);
		function.set(0.0005,1);
		function.set(0.00063,1);
		function.set(0.00079,1);
		function.set(0.001,1);
		function.set(0.00126,1);
		function.set(0.00158,1);
		function.set(0.002,1);
		function.set(0.00251,1);
		function.set(0.00316,1);
		function.set(0.00398,1);
		function.set(0.00501,1);
		function.set(0.00631,1);
		function.set(0.00794,1);
		function.set(0.01,1);
		function.set(0.01259,1);
		function.set(0.01585,1);
		function.set(0.01995,1);
		function.set(0.02512,1);
		function.set(0.03162,1);
		function.set(0.03981,1);
		function.set(0.05012,1);
		function.set(0.0631,1);
		function.set(0.07943,1);
		function.set(0.1,1);
		function.set(0.12589,1);
		function.set(0.15849,1);
		function.set(0.19953,1);
		function.set(0.25119,1);
		function.set(0.31623,1);
		function.set(0.39811,1);
		function.set(0.50119,1);
		function.set(0.63096,1);
		function.set(0.79433,1);
		function.set(1,1);
		function.set(1.25893,1);
		function.set(1.58489,1);
		function.set(1.99526,1);
		function.set(2.51189,1);
		function.set(3.16228,1);
		function.set(3.98107,1);
		function.set(5.01187,1);
		function.set(6.30957,1);
		function.set(7.94328,1);
		function.set(10,1);

	  }

	/**
	 * Parameters here should be same as in opensha.calc.cybershake.db.MeanUCERF2_ToDB class
	 * 
	 * @return
	 */
	private MeanUCERF2 setupERF() {
		meanUCERF2 = new MeanUCERF2();
		meanUCERF2.setParameter(MeanUCERF2.RUP_OFFSET_PARAM_NAME, new Double(5.0));
		meanUCERF2.setParameter(MeanUCERF2.CYBERSHAKE_DDW_CORR_PARAM_NAME, true);
		meanUCERF2.setParameter(UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_POISSON);
		meanUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		meanUCERF2.getTimeSpan().setDuration(1.0);
		meanUCERF2.updateForecast();
		return meanUCERF2;
	}
	
	
	/**
	 * Set up the IMR with default values
	 * @return
	 */
	private ScalarIntensityMeasureRelationshipAPI setupIMR() {
		imr = new AS_1997_AttenRel(this);
		imr.setParamDefaults();
		return imr;
	}
}
