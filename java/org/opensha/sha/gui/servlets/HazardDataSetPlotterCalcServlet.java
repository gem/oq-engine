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
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.StringTokenizer;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: HazardDataSetPlotterCalcServlet  </p>
 * <p>Description: This class does the calculation for the HazardDataSetPloter.
 * Once the user has selected the lat, lon and gridSpacing, it will do the calculation
 * using the HazardMap dataset and return back list containing the Y values for the
 * selected region.
 * @author : Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class HazardDataSetPlotterCalcServlet  extends HttpServlet {

	public static final String PARENT_DIR = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/HazardMapDatasets/";
	public  static final String SITES_FILE_NAME = "sites.txt";

	/**
	 *
	 *
	 * @param request
	 * @param response
	 * @throws IOException
	 * @throws ServletException
	 * @return the ArrayList after reading the file for the selected lat and lon
	 */
	public void doGet(HttpServletRequest request,  HttpServletResponse response)
	throws IOException, ServletException {
		System.out.println("HazardDataSetPlotterCalcServlet: Handling GET");
		
		//Vectors for computing the lat and lons for the given gridded region
		ArrayList locationVector= new ArrayList();
		try {
			// get all the input stream from the applet
			ObjectInputStream inputFromApplication = new ObjectInputStream(request.getInputStream());
			String selectedDataSet = (String)inputFromApplication.readObject();
			//gets the input for the lat, lon
			double lat = ((Double)inputFromApplication.readObject()).doubleValue();
			double lon = ((Double)inputFromApplication.readObject()).doubleValue();
			//close of the input from the application
			inputFromApplication.close();

			//sending the output in the form of the arrayList back to the calling application.
			ObjectOutputStream output = new ObjectOutputStream(response.getOutputStream());
			output.writeObject(getDataSet(selectedDataSet,lat,lon));
			output.close();
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
	 * @param minLat
	 * @param maxLat
	 * @param minLon
	 * @param maxLon
	 */
	private ArrayList getDataSet(String selectedSet,double selectedLat,double selectedLon){

		//searching the directory for the list of the files.
		File dir = new File(PARENT_DIR+selectedSet+"/");
		String[] fileList=dir.list();
		//formatting of the text double Decimal numbers for 2 places of decimal.
		DecimalFormat d= new DecimalFormat("0.00##");

		String latitude = null;
		String longitude = null;
		//getting the selected dataset
		// READ THE SITES FILE
		try{
			FileReader sitesReader = new FileReader(PARENT_DIR
					+ selectedSet +"/"+SITES_FILE_NAME);
			BufferedReader sitesin = new BufferedReader(sitesReader);
			// first line in the file contains the min lat, max lat, discretization interval
			latitude = sitesin.readLine();
			longitude = sitesin.readLine();
			sitesReader.close();
			sitesin.close();
		}catch(Exception e){
			System.out.println("Error reading the site file");
			e.printStackTrace();
		}
		//reading the latitude files
		StringTokenizer st = new StringTokenizer(latitude);
		double minLat = Double.parseDouble(st.nextToken().trim());
		double maxLat = Double.parseDouble(st.nextToken().trim());
		double gridSpacing = Double.parseDouble(st.nextToken().trim());

		//reading the longitude files
		st = new StringTokenizer(longitude);
		double minLon = Double.parseDouble(st.nextToken().trim());
		double maxLon = Double.parseDouble(st.nextToken().trim());

		boolean latFlag = false;
		boolean lonFlag = false;
		double latForFile =0;
		double lonForFile =0;
		double matchingGridSpacing = gridSpacing/2 + .0001;
		double lat = minLat;
		double lon = minLon;
		//lat and lon to compare with maxLat and maxLon, as double varies in precision
		//so we need different variable for comparison with maximum lat & lons
		//this needs to eb formatted to be compared.
		double latForComparison = Double.parseDouble(d.format(lat));
		double lonForComparison = Double.parseDouble(d.format(lon));
		for(; latForComparison<=maxLat; lat=lat+gridSpacing,latForComparison = Double.parseDouble(d.format(lat))){
			if(Math.abs(selectedLat-lat) <= (matchingGridSpacing)){
				latFlag=true;
				latForFile =lat;
			}
		}
		//it might that sites.txt has different latitude but calculations
		//for the Hazard data set are done for larger region becuase in  our
		//current framework we do calculation for rectangular region.
		if(lat >maxLat && !latFlag){
			latFlag=true;
			latForFile =lat;
		}
		for(; lonForComparison<=maxLon && latFlag; lon=lon+gridSpacing,lonForComparison = Double.parseDouble(d.format(lon))) {
			//iterating over lon's for each lat
			if(((Math.abs(selectedLon - lon)) <= matchingGridSpacing)){
				lonFlag = true;
				lonForFile = lon;
				break;
			}
		}
		//it might that sites.txt has different longitude but calculations
		//for the Hazard data set are done for larger region becuase in  our
		//current framework we do calculation for rectangular region.
		if(lon >maxLon && latFlag && !lonFlag)
			lonForFile = lon;

		try{
			System.out.println("Selected Lat and Lon:"+latForFile+" , "+lonForFile);
			System.out.println("Selected Lat and Lon for comparison:"+latForComparison+" , "+lonForComparison);
			String fileName =  d.format(latForFile)+"_"+d.format(lonForFile)+".txt";
			ArrayList listfiles = FileUtils.loadFile(PARENT_DIR+selectedSet+"/"+fileName);
			return listfiles;
		}catch(Exception e){
			System.out.println("Error reading the lat lon file");
			e.printStackTrace();
		}
		return null;
	}

	/**
	 * This method just calls the doPost method
	 *
	 * @param request : Request Object
	 * @param response : Response Object
	 * @throws IOException : Throws IOException during read-write from connection stream
	 * @throws ServletException
	 */
	public void doPost(HttpServletRequest request, HttpServletResponse response)
	throws IOException, ServletException {
		doGet(request,response);
	}
}
