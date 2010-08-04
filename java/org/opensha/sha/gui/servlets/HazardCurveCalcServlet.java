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

package org.opensha.sha.gui.servlets;


import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.rmi.RemoteException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;


/**
 * <p>Title: HazardCurveCalcServlet </p>
 * <p>Description: this servlet generates the data sets based on the parameters
 * set by the user in applet </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class HazardCurveCalcServlet extends HttpServlet {
	public final static boolean D =false;


	//Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws
	ServletException, IOException {
		
		System.out.println("HazardCurveCalcServlet: Handling GET");

		try {

			// get an input stream from the applet
			ObjectInputStream inputFromApplet = new ObjectInputStream(request.
					getInputStream());

			//get the sites for which this needs to be calculated
			Site site = (Site) inputFromApplet.readObject();
			//get the selected IMR
			ScalarIntensityMeasureRelationshipAPI imr = (ScalarIntensityMeasureRelationshipAPI)
			inputFromApplet.readObject();
			//get the selected EqkRupForecast
			Object obj = inputFromApplet.readObject();
			if (D) System.out.println("obj class = "+obj.getClass());
			String  eqkRupForecastLocation = (String) obj;
			// get the serilized Arbitrary discretized func
			ArbitrarilyDiscretizedFunc function = (ArbitrarilyDiscretizedFunc) inputFromApplet.readObject();
			// get the MAX_SOURCE distance
			double maxDistance =  ((Double) inputFromApplet.readObject()).doubleValue();
			System.out.println("ERF Location: "+eqkRupForecastLocation);
			EqkRupForecastAPI eqkRupForecast = (EqkRupForecastAPI)FileUtils.loadObject(eqkRupForecastLocation);
			if(D) System.out.println("ERF URL="+eqkRupForecastLocation);

			//call the HazardCurveCalculator here
			//code to call HazardCurveCalculator

			//checking to see if the EqkRupforecast object is the forecast object or the ERF_List
			//if(eqkRupForecast instanceof ERF_List)  {
			//call the function to handle the ERF_List.

			//}
			//does the Hazard Curve Calculation and return the list of Y-Values
			getHazardCurve(imr,eqkRupForecast,site,function,maxDistance);

			// report to the user whether the operation was successful or not
			// get an output stream from the applet
			ObjectOutputStream outputToApplet = new ObjectOutputStream(response.getOutputStream());
			//here we will be returning the Y-Values for the Hazard Curve.
			outputToApplet.writeObject(function);
			outputToApplet.close();

		}
		catch (Exception e) {
			// report to the user whether the operation was successful or not
			e.printStackTrace();
		}
	}

	/**
	 *
	 * @param imr
	 * @param eqkRupForecast
	 * @param site
	 * @param function
	 * @param maxDistance
	 */
	private void getHazardCurve(ScalarIntensityMeasureRelationshipAPI imr,EqkRupForecastAPI eqkRupForecast,
			Site site,ArbitrarilyDiscretizedFunc function,double maxDistance){
		try{
			HazardCurveCalculator calc = new HazardCurveCalculator();
			calc.setMaxSourceDistance(maxDistance);
			calc.getHazardCurve((DiscretizedFuncAPI)function,site,imr,(EqkRupForecastAPI)eqkRupForecast);
		}catch(RemoteException e){
			e.printStackTrace();
		}
	}


	//Process the HTTP Post request
	public void doPost(HttpServletRequest request, HttpServletResponse response) throws
	ServletException, IOException {
		// call the doPost method
		doGet(request, response);
	}

}
