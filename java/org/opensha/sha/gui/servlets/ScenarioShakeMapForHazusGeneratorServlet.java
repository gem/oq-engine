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

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.ServerPrefUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.mapping.GMT_MapGeneratorForShakeMaps;



/**
 * <p>Title: ScenarioShakeMapForHazusGeneratorServlet </p>
 * <p>Description: This servlet creates and runs the GMT script on the server.
 * It creates the script to make map and data for the Hazus.
 *  It returns back the URLs to the generated image files for Hazus.</p>
 * @author :Ned Field , Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class ScenarioShakeMapForHazusGeneratorServlet extends HttpServlet {
	
	public static final String SERVLET_URL = ServerPrefUtils.SERVER_PREFS.getServletBaseURL() + "ScenarioShakeMapForHazusGeneratorServlet";


	//Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {

		System.out.println("ScenarioShakeMapForHazusGeneratorServlet: Handling GET");

		try{
			// get an input stream from the applet
			ObjectInputStream inputFromApplet = new ObjectInputStream(request.getInputStream());

			//gets the GMT_MapGeneratorForShakeMaps object from the application
			GMT_MapGeneratorForShakeMaps gmtMap = (GMT_MapGeneratorForShakeMaps)inputFromApplet.readObject();

			//gets the file name for SA-0.3 XYZ data file for which we want to create the map for
			String sa_03xyzDataFileName = (String)inputFromApplet.readObject();

			//gets the file name for SA-1.0 XYZ data file for which we want to create the map for
			String sa_10xyzDataFileName = (String)inputFromApplet.readObject();

			//gets the file name for pga XYZ data file for which we want to create the map for
			String pga_xyzDataFileName = (String)inputFromApplet.readObject();

			//gets the file name for pgv XYZ data file for which we want to create the map for
			String pgv_xyzDataFileName = (String)inputFromApplet.readObject();

			//gets the Eqkrupture object
			EqkRupture rupture = (EqkRupture)inputFromApplet.readObject();

			//gets the metadata for the map parameters
			String metadata = (String)inputFromApplet.readObject();

			//receiving the name of the input directory
			String dirName = (String)inputFromApplet.readObject();

			//reading the sa-0.3 XYZ dataset from the file
			XYZ_DataSetAPI sa_03xyzData = (XYZ_DataSetAPI)FileUtils.loadObject(sa_03xyzDataFileName);

			//reading the sa-1.0 XYZ dataset from the file
			XYZ_DataSetAPI sa_10xyzData = (XYZ_DataSetAPI)FileUtils.loadObject(sa_10xyzDataFileName);

			//reading the pga XYZ dataset from the file
			XYZ_DataSetAPI pga_xyzData = (XYZ_DataSetAPI)FileUtils.loadObject(pga_xyzDataFileName);

			//reading the pgv XYZ dataset from the file
			XYZ_DataSetAPI pgvxyzData = (XYZ_DataSetAPI)FileUtils.loadObject(pgv_xyzDataFileName);


			//creates and run the GMT Script on the server and return back the URL to all the images
			Object webaddr = gmtMap.makeHazusFileSetUsingServlet(sa_03xyzData,sa_10xyzData,
					pga_xyzData,pgvxyzData,rupture,metadata,dirName);

			//making the XYZ dataset objects to be null.
			sa_03xyzData = null;
			sa_10xyzData = null;
			pga_xyzData = null;
			pgvxyzData = null;

			// get an ouput stream from the applet
			ObjectOutputStream outputToApplet = new ObjectOutputStream(response.getOutputStream());

			//name of the image file as the URL
			outputToApplet.writeObject(webaddr);
			outputToApplet.close();

		} catch (Exception e) {
			// report to the user whether the operation was successful or not
			e.printStackTrace();
		}
	}




	//Process the HTTP Post request
	public void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		// call the doPost method
		doGet(request,response);
	}

}
