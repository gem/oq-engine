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

package org.opensha.commons.mapping.servlet;

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
import org.opensha.commons.exceptions.GMT_MapException;
import org.opensha.commons.mapping.gmt.GMT_Map;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.RunScript;



/**
 * <p>Title: GMT_MapGeneratorServlet </p>
 * <p>Description: this servlet runs the GMT script based on the parameters and generates the
 * image file and returns that back to the calling application applet </p>
 * 
 * ****** ORIGINAL VERSION - <b>VERY</b> insecure *******
 * This is the order of operations:
 * Client ==> Server:
 * * directory name (String), or null for auto dirname
 * * GMT script (ArrayList<String>)
 * * XYZ Dataset (XYZ_DatasetAPI)
 * * Filename for XYZ Dataset (String)
 * * Metadata (String)
 * * Metadata filename (String)
 * Server ==> Client:
 * * IMG path **OR** error message
 * 
 * * ****** NEW VERSION - more secure *******
 * This is the order of operations:
 * Client ==> Server:
 * * directory name (String), or null for auto dirname
 * * GMT Map specification (GMT_Map)
 * * Metadata (String)
 * * Metadata filename (String)
 * Server ==> Client:
 * * Directory URL path **OR** error message
 * 
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author :Nitin Gupta, Vipin Gupta, and Kevin Milner
 * @version 1.0
 */

public class GMT_MapGeneratorServlet
extends HttpServlet {

	/*			opensha.usc.edu paths and URLs			*/
	private static final String OPENSHA_GMT_URL_PATH = "http://opensha.usc.edu/";
	public static final String OPENSHA_FILE_PATH = "/scratch/opensha/";
	
	/*			gravity.usc.edu paths and URLs			*/
	private static final String GRAVITY_GMT_URL_PATH = "http://gravity.usc.edu/gmtWS/";
	private static final String GRAVITY_FILE_PATH = "/opt/install/apache-tomcat-5.5.20/webapps/gmtWS/";
	
	private static final String GMT_URL_PATH = OPENSHA_GMT_URL_PATH;
	private final static String FILE_PATH = OPENSHA_FILE_PATH;
	private final static String GMT_DATA_DIR = "gmtData/";
	private final static String GMT_SCRIPT_FILE = "gmtScript.txt";
	
	private GMT_MapGenerator gmt = new GMT_MapGenerator();

	//Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws
	ServletException, IOException {

		// get an ouput stream from the applet
		ObjectOutputStream outputToApplet = new ObjectOutputStream(response.
				getOutputStream());

		//string that decides the name of the output gmt files
		String outFile = null;

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

			//receiving the name of the input directory
			String dirName = (String) inputFromApplet.readObject();

			//gets the object for the GMT_MapGenerator script
			GMT_Map map = (GMT_Map)inputFromApplet.readObject();

			//Metadata content: Map Info
			String metadata = (String) inputFromApplet.readObject();

			//Name of the Metadata file
			String metadataFileName = (String) inputFromApplet.readObject();
			
			String mapImagePath = createMap(gmt, map, dirName, metadata, metadataFileName);
			
			//returns the URL to the folder where map image resides
			outputToApplet.writeObject(mapImagePath);
			outputToApplet.close();

		}catch (Throwable t) {
			//sending the error message back to the application
			outputToApplet.writeObject(new RuntimeException(t));
			outputToApplet.close();
		}
	}
	
	//Process the HTTP Post request
	public void doPost(HttpServletRequest request, HttpServletResponse response) throws
	ServletException, IOException {
		// call the doPost method
		doGet(request, response);
	}
	
	public static String createMap(GMT_MapGenerator gmt, GMT_Map map, String plotDirName, String metadata,
			String metadataFileName) throws IOException, GMT_MapException {
		//Name of the directory in which we are storing all the gmt data for the user
		String newDir = null;
		//gets the current time in milliseconds to be the new director for each user
		String currentMilliSec = "" + System.currentTimeMillis();
		if (plotDirName != null) {
			File f = new File(plotDirName);
			int fileCounter = 1;
			//checking if the directory already exists then add
			while (f.exists()) {
				String tempDirName = plotDirName + fileCounter;
				f = new File(tempDirName);
				++fileCounter;
			}
			newDir = FILE_PATH + GMT_DATA_DIR + f.getName();
		}
		else {
			plotDirName = currentMilliSec;
			newDir = FILE_PATH + GMT_DATA_DIR + currentMilliSec;
		}

		//create a gmt directory for each user in which all his gmt files will be stored
		(new File(newDir)).mkdir();
		//reading the gmtScript file that user sent as the attachment and create
		//a new gmt script inside the directory created for the user.
		//The new gmt script file created also has one minor modification
		//at the top of the gmt script file I am adding the "cd ... " command so
		//that it should pick all the gmt related files from the directory created for the user.
		//reading the gmt script file sent by user as the attachment

		String gmtScriptFile = newDir + "/" + GMT_SCRIPT_FILE;
		
		ArrayList<String> gmtMapScript = gmt.getGMT_ScriptLines(map, newDir);

		//creating a new gmt script for the user and writing it ot the directory created for the user
		FileWriter fw = new FileWriter(gmtScriptFile);
		BufferedWriter bw = new BufferedWriter(fw);
		int size = gmtMapScript.size();
		for (int i = 0; i < size; ++i) {
			bw.write( (String) gmtMapScript.get(i) + "\n");
		}
		bw.close();

		// I use the new File().getName() here to  make sure the filename isn't a relative path
		// that could overwrite something important, like "../../myfile"
		String metadataFile = newDir + "/" + new File(metadataFileName).getName();
		//creating the metadata (map Info) file in the new directory created for user
		fw = new FileWriter(metadataFile);
		bw = new BufferedWriter(fw);
		bw.write(" " + (String) metadata + "\n");
		bw.close();

		//creating the XYZ file from the XYZ file from the XYZ dataSet
		ArrayList<Double> xVals = map.getGriddedData().getX_DataSet();
		ArrayList<Double> yVals = map.getGriddedData().getY_DataSet();
		ArrayList<Double> zVals = map.getGriddedData().getZ_DataSet();
		//file follows the convention lat, lon and Z value
		if (map.getGriddedData().checkXYZ_NumVals()) {
			size = xVals.size();
			fw = new FileWriter(newDir + "/" + new File(map.getXyzFileName()).getName());
			bw = new BufferedWriter(fw);
			for (int i = 0; i < size; ++i) {
				//System.out.println(xVals.get(i)+" "+yVals.get(i)+" "+zVals.get(i)+"\n");
				bw.write(xVals.get(i) + " " + yVals.get(i) + " " + zVals.get(i) +
				"\n");
			}
			bw.close();
		}
		else {
			throw new RuntimeException(
					"X, Y and Z dataset does not have equal size");
		}

		//running the gmtScript file
		String[] command = {
				"sh", "-c", "/bin/bash " + gmtScriptFile};
		RunScript.runScript(command);

		//create the Zip file for all the files generated
		FileUtils.createZipFile(newDir);
		//URL path to folder where all GMT related files and map data file for this
		//calculations reside.
		String mapImagePath = GMT_URL_PATH + GMT_DATA_DIR +
		plotDirName + SystemUtils.FILE_SEPARATOR;
		
		return mapImagePath;
	}

}
