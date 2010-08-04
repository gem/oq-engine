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
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.RunScript;


/**
 * <p>Title: HazusAndGMT_MapsGeneratorServlet </p>
 * <p>Description: this servlet runs the script based on the parameters and generates the
 * hazus shape files and image file and returns the webadress of the output directory
 * that back to the calling application applet </p>
 * @author :Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class HazusAndGMT_MapsGeneratorServlet extends HttpServlet {

	private static final String GMT_URL_PATH="http://gravity.usc.edu/gmtWS/";
	private final static String FILE_PATH="/opt/install/apache-tomcat-5.5.20/webapps/gmtWS/";
	private final static String GMT_DATA_DIR ="gmtData/" ;
	private final static String GMT_SCRIPT_FILE = "gmtScript.txt";


	//Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		
		System.out.println("HazusAndGMT_MapsGeneratorServlet: Handling GET");

		//string that decides the name of the output gmt files
		String outFile = null;
		//gets the current time in milliseconds to be the new director for each user
		String currentMilliSec ="";
		currentMilliSec += System.currentTimeMillis();
		//Name of the directory in which we are storing all the gmt data for the user
		String newDir= null;

		try{
			//all the user gmt stuff will be stored in this directory
			File mainDir = new File(FILE_PATH+GMT_DATA_DIR);
			//create the main directory if it does not exist already
			if(!mainDir.isDirectory()){
				boolean success = (new File(FILE_PATH+GMT_DATA_DIR)).mkdir();
			}



			// get an input stream from the applet
			ObjectInputStream inputFromApplet = new ObjectInputStream(request.getInputStream());

			//receiving the name of the input directory
			String dirName = (String)inputFromApplet.readObject();
			if(dirName != null){
				File f = new File(dirName);
				int fileCounter =1;
				//checking if the directory already exists then add
				while(f.exists()){
					String tempDirName = dirName+fileCounter;
					f = new File(tempDirName);
					++fileCounter;
				}
				newDir = FILE_PATH+GMT_DATA_DIR+f.getName();
			}
			else{
				dirName = currentMilliSec;
				newDir = FILE_PATH+GMT_DATA_DIR+currentMilliSec;
			}



			//create a gmt directory for each user in which all his gmt files will be stored
			boolean success =(new File(newDir)).mkdir();
			//reading the gmtScript file that user sent as the attachment and create
			//a new gmt script inside the directory created for the user.
			//The new gmt script file created also has one minor modification
			//at the top of the gmt script file I am adding the "cd ... " command so
			//that it should pick all the gmt related files from the directory cretade for the user.
			//reading the gmt script file sent by user as te attchment

			String gmtScriptFile = newDir+"/"+this.GMT_SCRIPT_FILE;



			//gets the object for the GMT_MapGenerator script
			ArrayList gmtMapScript = (ArrayList) inputFromApplet.readObject();
			System.out.println("Received GMT Lines");
			//creating a new gmt script for the user and writing it ot the directory created for the user
			FileWriter fw = new FileWriter(gmtScriptFile);
			BufferedWriter bw = new BufferedWriter(fw);
			bw.write("cd "+newDir+"/"+"\n");
			int size= gmtMapScript.size();
			for(int i=0;i<size;++i)
				bw.write((String)gmtMapScript.get(i)+"\n");
			bw.close();
			gmtMapScript = null;

			//XValues recieved from the application from the XYZ dataset
			ArrayList xValues = (ArrayList) inputFromApplet.readObject();
			//YValues recieved from the application from XYZ dataset
			ArrayList yValues = (ArrayList) inputFromApplet.readObject();

			//Prefix String being received to be prefixed before the name of the files
			String sa03 = (String)inputFromApplet.readObject();
			String sa01 = (String)inputFromApplet.readObject();
			String pga = (String)inputFromApplet.readObject();
			String pgv = (String)inputFromApplet.readObject();
			//Name of the XYZ file
			String xyzFileName = (String)inputFromApplet.readObject();
			//Metadata content: Map Info
			String metadata = (String)inputFromApplet.readObject();
			//Name of the Metadata file
			String metadataFileName = (String)inputFromApplet.readObject();
			//write the metadata file
			writeMetadataFile(newDir,metadata,metadataFileName);
			metadata  = null;
			metadataFileName = null;


			//Z dataset for SA-0.3sec being received from the applet
			ArrayList sa03_zDataSet = (ArrayList)inputFromApplet.readObject();
			System.out.println("Received SA-03 object");
			writeXYZ_DataFile(newDir,sa03,xyzFileName,xValues,yValues,sa03_zDataSet);
			sa03_zDataSet = null;

			//Z dataset for SA-1.0sec being received from the applet
			ArrayList sa10_zDataSet = (ArrayList)inputFromApplet.readObject();
			System.out.println("Received SA-10 object");
			writeXYZ_DataFile(newDir,sa01,xyzFileName,xValues,yValues,sa10_zDataSet);
			sa10_zDataSet = null;

			//Z dataset for PGA being received from the applet
			ArrayList pga_zDataSet = (ArrayList)inputFromApplet.readObject();
			System.out.println("Received PGA object");
			writeXYZ_DataFile(newDir,pga,xyzFileName,xValues,yValues,pga_zDataSet);
			pga_zDataSet = null;

			//Z dataset for PGV being received from the applet
			ArrayList pgv_zDataSet = (ArrayList)inputFromApplet.readObject();
			System.out.println("Received PGV object");
			writeXYZ_DataFile(newDir,pgv,xyzFileName,xValues,yValues,pgv_zDataSet);
			pgv_zDataSet = null;

			//running the gmtScript file
			String[] command ={"sh","-c","sh "+gmtScriptFile};
			RunScript.runScript(command);

			//create the Zip file for all the files generated
			FileUtils.createZipFile(newDir);
			// get an ouput stream from the applet
			ObjectOutputStream outputToApplet = new ObjectOutputStream(response.getOutputStream());

			//URL path to folder where all GMT related files and map data file for this
			//calculations reside.
			String mapImagePath = this.GMT_URL_PATH + this.GMT_DATA_DIR +
			dirName + SystemUtils.FILE_SEPARATOR;
			//returns the URL to the folder where map image resides
			outputToApplet.writeObject(mapImagePath);

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



	/**
	 * writes the metdata in the output directory(newDir).
	 * @param newDir
	 * @param metadataVector
	 * @param metadataFileName
	 */
	private void writeMetadataFile(String newDir, String metadata, String metadataFileName){
		String metadataFile = newDir+"/"+metadataFileName;
		try{
			//creating the metadata (map Info) file in the new directory created for user
			FileWriter fw = new FileWriter(metadataFile);
			BufferedWriter bw = new BufferedWriter(fw);
			bw.write(" "+metadata+"\n");
			bw.close();
		}catch(Exception e){
			e.printStackTrace();
		}
	}


	/**
	 * writes the XYZ data file in the output directory and prefix of the file
	 * is based on the selected IMT.
	 * @param dirName
	 * @param imtPrefix
	 * @param xyzFileName
	 * @param xyzDataSet
	 */
	private void writeXYZ_DataFile(String dirName,String imtPrefix,String xyzFileName,
			ArrayList xValues,ArrayList yValues,ArrayList zValues){
		int xSize = xValues.size();
		int ySize = yValues.size();
		int zSize = zValues.size();

		//file follows the convention lat, lon and Z value
		if((xSize==ySize) && (ySize==zSize)){
			try{
				FileWriter fw = new FileWriter(dirName+"/"+imtPrefix+"_"+xyzFileName);
				BufferedWriter bw = new BufferedWriter(fw);
				for(int i=0;i<xSize;++i){
					bw.write(xValues.get(i)+" "+yValues.get(i)+" "+zValues.get(i)+"\n");
				}
				bw.close();
			}catch(Exception e){
				e.printStackTrace();
			}
		}
		else
			throw new RuntimeException("X, Y and Z dataset does not have equal size");
	}


}
