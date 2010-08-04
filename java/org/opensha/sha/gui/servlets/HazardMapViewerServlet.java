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


import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Hashtable;
import java.util.StringTokenizer;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.commons.data.ArbDiscretizedXYZ_DataSet;
import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.gui.beans.IMLorProbSelectorGuiBean;

//import unusedArchive.HazardMapCalcServlet;

/**
 * <p>Title: HazardMapViewerServlet</p>
 * <p>Description: This servlet is hosted on web server gravity.usc.edu.
 * This servlet allows application to give all the datasets ids that contains
 * Hazard curves dataset.
 * When user has selected the dataset using which he wants to compute Hazard Map,
 * it is sent back to this servlet which then uses GMT script to create the map image.</p>
 * @author :Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class HazardMapViewerServlet  extends HttpServlet {


	public static final String PARENT_DIR = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/HazardMapDatasets/";
	public  static final String METADATA_FILE_NAME = "metadata.txt";
	public  static final String SITES_FILE_NAME = "sites.txt";

	// directory where all the hazard map data sets will be saved
	public static final String GET_DATA = "Get Data";
	public static final String MAKE_MAP = "Make Map";

	//Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		try {
			
			System.out.println("HazardMapViewerServlet: Handling GET");

			// get an input stream from the applet
			ObjectInputStream inputFromApplet = new ObjectInputStream(request.getInputStream());

			/**
			 * get the function desired by th user
			 */
			String functionDesired  = (String) inputFromApplet.readObject();

			if(functionDesired.equalsIgnoreCase(GET_DATA)) {
				// if USER WANTS TO LOAD EXISTING DATA SETS
				loadDataSets(new ObjectOutputStream(response.getOutputStream()));
			}else if(functionDesired.equalsIgnoreCase(MAKE_MAP)){ // IF USER WANTS TO MAKE MAP
				// get the set selected by the user
				String selectedSet = (String)inputFromApplet.readObject();
				// map generator object
				GMT_MapGenerator map = (GMT_MapGenerator)inputFromApplet.readObject();
				// whether IML@prob is selected or Prob@IML
				String optionSelected = (String)inputFromApplet.readObject();
				// get the value
				double val = ((Double)inputFromApplet.readObject()).doubleValue();
				// get the metadata
				String metadata = (String)inputFromApplet.readObject();

				boolean isProbAt_IML = true;
				if(optionSelected.equalsIgnoreCase(IMLorProbSelectorGuiBean.IML_AT_PROB))
					isProbAt_IML = false;
				// create the XYZ data set
				XYZ_DataSetAPI xyzData = getXYZ_DataSet(selectedSet, isProbAt_IML, val, map);
				String metadataFileName = PARENT_DIR+
				selectedSet+"/"+"map_info.txt";
				FileWriter fw = new FileWriter(metadataFileName);
				fw.write(metadata);
				fw.close();
				// jpg file name
				map.setMetatdataFileName(metadataFileName);
				//get the map scale label
				String mapLabel = getMapLabel(isProbAt_IML);

				String jpgFileName  = map.makeMapUsingServlet(xyzData,mapLabel,metadata,null);
				ObjectOutputStream outputToApplet =new ObjectOutputStream(response.getOutputStream());
				outputToApplet.writeObject(jpgFileName);
				outputToApplet.close();
			}

		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	//Process the HTTP Post request
	public void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		// call the doPost method
		doGet(request,response);
	}


	/**
	 *
	 * @returns the Map label based on the selected Map Type( Prob@IML or IML@Prob)
	 */
	private String getMapLabel(boolean isProbAtIML){
		//making the map
		String label;

		if(isProbAtIML)
			label="Prob";
		else
			label="IML";
		return label;
	}

	/**
	 * Read the data sets, their names, their params needed to generate map
	 * and site range
	 * @param metaDataHash : Hashtable to save metadata
	 * @param lonHash : hashtable to save longitude range
	 * @param latHash : hashtable to save latitude range
	 */
	private void loadDataSets(ObjectOutputStream outputToApplet) {
		//HashTables for storing the metadata for each dataset
		Hashtable metaDataHash = new Hashtable();
		//Hashtable for storing the lons from each dataSet
		Hashtable lonHash= new Hashtable();
		//Hashtable for storing the lats from each dataSet
		Hashtable latHash= new Hashtable();
		try {
			File dirs =new File(PARENT_DIR);
			File[] dirList=dirs.listFiles(); // get the list of all the data in the parent directory

			// for each data set, read the meta data and sites info
			for(int i=0;i<dirList.length;++i){
				if(dirList[i].isDirectory()){

					// READ THE METADATA FILE
					String dataSetDescription= new String();
					try {
						File f = new File(PARENT_DIR+
								dirList[i].getName()+"/"+METADATA_FILE_NAME);
						if (!f.exists()) continue;
						FileReader dataReader = new FileReader(f);
						BufferedReader in = new BufferedReader(dataReader);
						dataSetDescription = "";
						String str=in.readLine();
						while(str!=null) {
							dataSetDescription += str+"\n";
							str=in.readLine();
						}
						metaDataHash.put(dirList[i].getName(),dataSetDescription);
						in.close();

						// READ THE SITES FILE
						FileReader sitesReader = new FileReader(PARENT_DIR
								+ dirList[i].getName() +
								"/"+SITES_FILE_NAME);
						BufferedReader sitesin = new BufferedReader(sitesReader);
						// first line in the file contains the min lat, max lat, discretization interval
						String latitude = sitesin.readLine();
						latHash.put(dirList[i].getName(),latitude);
						// Second line in the file contains the min lon, max lon, discretization interval
						String longitude = sitesin.readLine();
						lonHash.put(dirList[i].getName(),longitude);

					}catch(Exception e) {
						e.printStackTrace();
					}
				}
			}

			// report to the user whether the operation was successful or not
			// get an ouput stream from the applet
			outputToApplet.writeObject(metaDataHash);
			outputToApplet.writeObject(lonHash);
			outputToApplet.writeObject(latHash);
			outputToApplet.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * This method reads the file and generates the final outputfile
	 * for the range of the lat and lon selected by the user . The final output is
	 * generated based on the selcetion made by the user either for the iml@prob or
	 * prob@iml. The data is appended to the end of the until all the list of the
	 * files have been searched for thr input iml or prob value. The final output
	 * file is given as the input to generate the grd file.
	 * @param selectedSet : Selected Hazard dataset
	 * @param isProbAt_IML : what to plot IML@Prob or Prob@IML
	 * @param val : Depending on the above parameter it is either prob val if IML@Prob
	 * or iml val if Prob@IML
	 * @param map : GMT object
	 * @return
	 */
	private XYZ_DataSetAPI getXYZ_DataSet(String selectedSet,
			boolean isProbAt_IML,
			double val, GMT_MapGenerator map ){

		// get the min lat, max lat, min lon ,max lon, gridspacing
		ParameterList paramList = map.getAdjustableParamsList();
		String minLat = paramList.getValue(GMT_MapGenerator.MIN_LAT_PARAM_NAME).toString();
		String maxLat = paramList.getValue(GMT_MapGenerator.MAX_LAT_PARAM_NAME).toString();
		String minLon = paramList.getValue(GMT_MapGenerator.MIN_LON_PARAM_NAME).toString();
		String maxLon = paramList.getValue(GMT_MapGenerator.MAX_LON_PARAM_NAME).toString();

		double gridSpacing =((Double) paramList.getValue(GMT_MapGenerator.GRID_SPACING_PARAM_NAME)).doubleValue();

		//adding the xyz data set to the object of XYZ_DataSetAPI
		XYZ_DataSetAPI xyzData;
		ArrayList xVals= new ArrayList();
		ArrayList yVals= new ArrayList();
		ArrayList zVals= new ArrayList();

		//searching the directory for the list of the files.
		File dir = new File(PARENT_DIR+selectedSet+"/");
		File[] fileList=dir.listFiles();

		//number of files in selected dataset
		int numFiles = fileList.length;
		//creating the arraylist to get the all lats and lons in this dataset
		ArrayList latList = new ArrayList();
		ArrayList lonList = new ArrayList();

		/*
		 *Reading all the Hazard files in the dataset to get their Lat and Lons
		 *Iterating over all hazard curve files to in the selected dataset to get
		 *the exact file names , which are combination of "Lat Value"+"_"+"Lon Value"
		 */
		for(int i=0;i<numFiles;++i){
			//only taking the files into consideration
			if(fileList[i].isFile()){
				String fileName = fileList[i].getName();
				//files that ends with ".txt"
				if(fileName.endsWith(".txt")){
					int index = fileName.indexOf("_");
					int firstIndex = fileName.indexOf(".");
					int lastIndex = fileName.lastIndexOf(".");
					// Hazard data files have 3 "." in their names
					//And leaving the rest of the files which contains only 1"." in their names
					if(firstIndex != lastIndex){

						//getting the lat and Lon values from file names
						Double latVal = new Double(fileName.substring(0,index).trim());
						Double lonVal = new Double(fileName.substring(index+1,lastIndex).trim());
						//Adding the Latitude from the file name to the list if not already there
						if(!latList.contains(latVal))
							latList.add(latVal);
						//Adding the longitude from the file name to the list if not already there
						if(!lonList.contains(lonVal))
							lonList.add(lonVal);
					}
				}
			}
		}

		//Sorting Latitude and Longitude list which are both collection of Doubles
		//As it sorting the contents of the list as String, so goes from minLat to MaxLat
		//and same for longitudes
		Collections.sort(latList);
		Collections.sort(lonList);

		//getting the indexes of the lat and lon( filled by the user)
		// from the list of Lat and Lons( for which we computed the dataset).
		int latListSize = latList.size();
		int lonListSize = lonList.size();


		int minLatIndex =0;
		int maxLatIndex =0;
		//min Lat and max Lat as selected by user
		double minLatVal = Double.parseDouble(minLat);
		double maxLatVal = Double.parseDouble(maxLat);

		//using it to find the nearest Latitude to the min and max Latitude,
		//if they don't match perfectly from the list,
		//double gridSpacingForCloseValue = gridSpacing/2;

		//System.out.println("Close grid spacing ="+gridSpacingForCloseValue);
		//finding the nearest min and max lat. from the list of all lats in this dataset
		int i=0;
		//finding nearest Latitude to minLat
		for(;i<latListSize;++i){
			if(Math.abs(minLatVal - ((Double)latList.get(i)).doubleValue()) < gridSpacing){
				minLatIndex = i;
				break;
			}
		}

		//finding nearest latitude to maxLat
		for(;i<latListSize;++i){
			if(Math.abs(maxLatVal - ((Double)latList.get(i)).doubleValue()) < gridSpacing){
				maxLatIndex = i;
				break;
			}
		}


		int minLonIndex =0;
		int maxLonIndex =0;
		//min Lon and max Lon as selected by user
		double minLonVal = Double.parseDouble(minLon);
		double maxLonVal = Double.parseDouble(maxLon);

		//finding the nearest min and max Lon. from the list of all lats in this dataset
		i=0;
		//finding nearest longitude to minLon
		for(;i<lonListSize;++i){
			if(Math.abs(minLonVal - ((Double)lonList.get(i)).doubleValue()) < gridSpacing){
				minLonIndex = i;
				break;
			}
		}

		//finding nearest longitude to maxLon
		for(;i<lonListSize;++i){
			if(Math.abs(maxLonVal - ((Double)lonList.get(i)).doubleValue()) < gridSpacing){
				maxLonIndex = i;
				break;
			}
		}


		//Decimal format that establishes format of doubl vaule( to read the hazard
		//data files) which are at least upto 2 decimal places
		DecimalFormat d = new DecimalFormat("0.00##");

		//iterating over all the Lat and Lon Value to read the files for the IML or Prob
		//values depending on user choice (IML@Prob or Prob@IML).
		for(int k=minLatIndex;k<=maxLatIndex;++k){
			double interpolatedVal=0;
			ArrayList fileLines;
			for(int j=minLonIndex;j<=maxLonIndex;++j) {
				//getting Lat and Lons
				String lat = d.format(((Double)latList.get(k)).doubleValue());
				String lon = d.format(((Double)lonList.get(j)).doubleValue());

				try {
					//reading the hazard Curve to find interpolate the iml or Prob value
					String fileToRead = lat+"_"+ lon+".txt";
					fileLines = FileUtils.loadFile(PARENT_DIR+selectedSet+"/"+fileToRead);
					String dataLine;
					StringTokenizer st;
					ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();

					if(fileLines.size() ==0)
						System.out.println("File to read but could not found:"+fileToRead);

					for(i=0;i<fileLines.size();++i) {
						dataLine=(String)fileLines.get(i);
						st=new StringTokenizer(dataLine);
						//using the currentIML and currentProb we interpolate the iml or prob
						//value entered by the user.
						double currentIML = Double.parseDouble(st.nextToken());
						double currentProb= Double.parseDouble(st.nextToken());
						func.set(currentIML, currentProb);
					}

					if (isProbAt_IML)
						//final iml value returned after interpolation in log space
						interpolatedVal = func.getInterpolatedY_inLogXLogYDomain(val);
					// for  IML_AT_PROB
					else //interpolating the iml value in log space entered by the user to get the final iml for the
						//corresponding prob.
						interpolatedVal = func.getFirstInterpolatedX_inLogXLogYDomain(val);

				}catch(Exception e) {
					//e.printStackTrace();
				} // catch invalid range exception etc.
				xVals.add(new Double(lat));
				yVals.add(new Double(lon));
				zVals.add(new Double(interpolatedVal));
			}
		}

		// return the XYZ Data set
		xyzData = new ArbDiscretizedXYZ_DataSet(xVals,yVals,zVals);
		return xyzData;
	}
}

