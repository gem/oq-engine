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

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.commons.lang.SystemUtils;
import org.opensha.commons.mapping.servlet.GMT_MapGeneratorServlet;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.RunScript;
import org.opensha.sha.calc.disaggregation.DisaggregationCalculator;
import org.opensha.sha.calc.disaggregation.DisaggregationPlotData;


/**
 * <p>Title: DisaggregationPlotServlet </p>
 * <p>Description: this servlet runs the GMT script based on the parameters and generates the
 * image file and returns that back to the calling application applet </p>

 * @author :Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class DisaggregationPlotServlet
extends HttpServlet {

	private static final String GMT_URL_PATH = "http://opensha.usc.edu/";
	private final static String FILE_PATH = GMT_MapGeneratorServlet.OPENSHA_FILE_PATH;
	private final static String GMT_DATA_DIR = "gmtData/";
	private final static String GMT_SCRIPT_FILE = "gmtScript.txt";
	private final static String METADATA_FILE_NAME = "metadata.txt";

	//Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws
	ServletException, IOException {
		
		System.out.println("DisaggregationPlotServlet: Handling GET");

		// get an ouput stream from the applet
		ObjectOutputStream outputToApplet = new ObjectOutputStream(response.
				getOutputStream());

		//gets the current time in milliseconds to be the new director for each user
		String currentMilliSec = "";
		currentMilliSec += System.currentTimeMillis();
		//Name of the directory in which we are storing all the gmt data for the user
		String newDir = null;

		try {
			//all the user gmt stuff will be stored in this directory
			File mainDir = new File(FILE_PATH + GMT_DATA_DIR);
			//create the main directory if it does not exist already
			if (!mainDir.isDirectory()) {
				(new File(FILE_PATH + GMT_DATA_DIR)).mkdir();
			}

			// get an input stream from the applet
			ObjectInputStream inputFromApplet = new ObjectInputStream(request.
					getInputStream());

			newDir = FILE_PATH + GMT_DATA_DIR + currentMilliSec;

			//create a gmt directory for each user in which all his gmt files will be stored
			(new File(newDir)).mkdir();
			//reading the gmtScript file that user sent as the attachment and create
			//a new gmt script inside the directory created for the user.
			//The new gmt script file created also has one minor modification
			//at the top of the gmt script file I am adding the "cd ... " command so
			//that it should pick all the gmt related files from the directory cretade for the user.
			//reading the gmt script file sent by user as te attchment

			String gmtScriptFile = newDir + "/" + GMT_SCRIPT_FILE;

			//gets the object for the GMT_MapGenerator script
			DisaggregationPlotData data = (DisaggregationPlotData)inputFromApplet.readObject();
			ArrayList<String> gmtMapScript = DisaggregationCalculator.createGMTScriptForDisaggregationPlot(data, newDir);

			//Metadata content: Map Info
			String metadata = (String) inputFromApplet.readObject();

			//creating a new gmt script for the user and writing it ot the directory created for the user
			FileWriter fw = new FileWriter(gmtScriptFile);
			BufferedWriter bw = new BufferedWriter(fw);
			int size = gmtMapScript.size();
			for (int i = 0; i < size; ++i) {
				bw.write( (String) gmtMapScript.get(i) + "\n");
			}
			bw.close();

			String metadataFile = newDir + "/" + METADATA_FILE_NAME;

			//creating the metadata (map Info) file in the new directory created for user
			fw = new FileWriter(metadataFile);
			bw = new BufferedWriter(fw);
			bw.write(" " + (String) metadata + "\n");
			bw.close();

			//running the gmtScript file
			String[] command = {
					"sh", "-c", "sh " + gmtScriptFile};
			RunScript.runScript(command);

			//create the Zip file for all the files generated
			FileUtils.createZipFile(newDir);
			//URL path to folder where all GMT related files and map data file for this
			//calculations reside.
			String mapImagePath = GMT_URL_PATH + GMT_DATA_DIR +
			currentMilliSec + SystemUtils.FILE_SEPARATOR;
			//returns the URL to the folder where map image resides
			outputToApplet.writeObject(mapImagePath);
			outputToApplet.close();

		}catch (Exception e) {
			//sending the error message back to the application
			outputToApplet.writeObject(new RuntimeException(e.getMessage()));
			outputToApplet.close();
		}
	}

	//Process the HTTP Post request
	public void doPost(HttpServletRequest request, HttpServletResponse response) throws
	ServletException, IOException {
		// call the doPost method
		doGet(request, response);
	}
}
