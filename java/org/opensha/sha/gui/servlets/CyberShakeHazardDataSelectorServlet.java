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

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.StringTokenizer;
import java.util.TreeSet;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.RunScript;

/**
 * <p>Title: CyberShakeHazardDataSelectorServlet</p>
 *
 * <p>Description: This servlet selects the different Sites completed for
 * CyberShake and then collects the hazard dataset for different SA values.</p>
 *
 * @author Nitin Gupta
 * @version 1.0
 */


public class CyberShakeHazardDataSelectorServlet  extends HttpServlet {


	public static final String GET_CYBERSHAKE_INFO_PROB_CURVE =
		"SA Period for Cybershake Sites";
	public static final String GET_CYBERSHAKE_INFO_DETER_CURVE =
		"Deterministic Curve";
	public static final String GET_HAZARD_DATA = "Read the CyberShake Hazard Data";
	public static final String GET_DETERMINISTIC_DATA = "Read the deterministic data";
	private static final String CYBERSHAKE_HAZARD_DATASET = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/CyberShake/";
	private static final String OpenSHA_LIB_PATH = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/WEB-INF/lib/ERF.jar";
	private static final String EXECUTABLE_CLASS_NAME = "CalculateDeterministicHazardCurve";
	private static final String hazardDataFilesStartString = "hazcurve_";
	//private static final String

	//Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		try {
			System.out.println("CyberShakeHazardDataSelectorServlet: Handling GET");

			// get an input stream from the applet
			ObjectInputStream inputFromApplet = new ObjectInputStream(request.getInputStream());

			/**
			 * get the function desired by th user
			 */
			String functionDesired  = (String) inputFromApplet.readObject();

			if(functionDesired.equalsIgnoreCase(GET_CYBERSHAKE_INFO_PROB_CURVE)) {
				// gets the CyberShake Sites and the SA period associated with it.
				HashMap siteSA_PeriodList =loadDataSets(false,null);
				ObjectOutputStream outputToApplet = new ObjectOutputStream(response.getOutputStream());
				// report to the user whether the operation was successful or not
				// get an ouput stream from the applet
				outputToApplet.writeObject(siteSA_PeriodList);
				outputToApplet.close();

			}
			else if(functionDesired.equalsIgnoreCase(GET_CYBERSHAKE_INFO_DETER_CURVE)) {
				// gets the CyberShake Sites and the SA period associated with it.
				HashMap siteSrcListMap = new HashMap();
				HashMap siteSA_PeriodList =loadDataSets(true,siteSrcListMap);
				ObjectOutputStream outputToApplet = new ObjectOutputStream(response.getOutputStream());
				// report to the user whether the operation was successful or not
				// get an ouput stream from the applet
				outputToApplet.writeObject(siteSA_PeriodList);
				outputToApplet.writeObject(siteSrcListMap);
				outputToApplet.close();

			}
			else if(functionDesired.equalsIgnoreCase(GET_HAZARD_DATA)) {
				String siteName = (String)inputFromApplet.readObject();
				String saPeriod = (String)inputFromApplet.readObject();
				DiscretizedFuncAPI fileData = readHazardDataSet(siteName,saPeriod);
				ObjectOutputStream outputToApplet = new ObjectOutputStream(response.getOutputStream());
				// report to the user whether the operation was successful or not
				// get an ouput stream from the applet
				outputToApplet.writeObject(fileData);
				outputToApplet.close();
			}
			else if(functionDesired.equalsIgnoreCase(GET_DETERMINISTIC_DATA)){
				String siteName = (String)inputFromApplet.readObject();
				String saPeriod = (String)inputFromApplet.readObject();
				String srcIndex = (String)inputFromApplet.readObject();
				Integer rupIndex = (Integer)inputFromApplet.readObject();
				ArrayList imlVals = (ArrayList)inputFromApplet.readObject();
				DiscretizedFuncAPI fileData = readDeterministicDataSet(siteName,saPeriod,srcIndex,rupIndex,imlVals);
				ObjectOutputStream outputToApplet = new ObjectOutputStream(response.getOutputStream());
				// report to the user whether the operation was successful or not
				// get an ouput stream from the applet
				outputToApplet.writeObject(fileData);
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
	 * This method reads the Hazard data file for a given Cybershake Site and Sa Period.
	 * @param siteName String Cybershake site.
	 * @param saPeriod String SA period for which hazard data needs to be read.
	 * @return ArrayList
	 */
	public DiscretizedFuncAPI readHazardDataSet(String siteName,String saPeriod){
		String saPeriodFile = hazardDataFilesStartString+saPeriod;
		String fileToRead = this.CYBERSHAKE_HAZARD_DATASET+siteName+"/"+saPeriodFile;
		ArrayList fileLines = null;
		DiscretizedFuncAPI func = null;
		try {
			fileLines = FileUtils.loadFile(fileToRead);
		}
		catch (FileNotFoundException ex) {
			ex.printStackTrace();
		}
		catch (IOException ex) {
			ex.printStackTrace();
		}
		func = new ArbitrarilyDiscretizedFunc();
		int size = fileLines.size();
		for(int i=0;i<size;++i){
			StringTokenizer st = new StringTokenizer((String)fileLines.get(i));
			func.set(Double.parseDouble(st.nextToken()),Double.parseDouble(st.nextToken()));
		}
		return func;
	}


	/**
	 * This method reads the seismogram files for each rupture with all variations
	 * computed in Cybershake and returns the curve data for it.
	 * @param siteName String Site Name
	 * @param saPeriod String SA Period
	 * @param srcIndex Double Src Index
	 * @param rupIndex Double Rup Index
	 * @param imlVals ArrayList iml values for which deterministic curve needs to
	 * be computed.
	 * @return ArrayList of data read from seismogram file.
	 */

	public DiscretizedFuncAPI readDeterministicDataSet(String siteName,
			String saPeriod,
			String srcIndex, Integer rupIndex,
			ArrayList imlVals) {

		String fileName = CYBERSHAKE_HAZARD_DATASET+siteName+"/iml.txt";
		DiscretizedFuncAPI func = null;
		try{
			FileWriter fw = new FileWriter(fileName);
			int size = imlVals.size();
			for(int i=0;i<size;++i)
				fw.write(((Double)imlVals.get(i)).doubleValue()+"\n");
			fw.close();

			RunScript.runScript(new String[] {"sh", "-c",
					"java -classpath "+
					OpenSHA_LIB_PATH+":"+
					CYBERSHAKE_HAZARD_DATASET+". "+
					EXECUTABLE_CLASS_NAME +"   "+
					srcIndex + "  " + ((Integer)rupIndex).intValue() + "   " + fileName + " " +
					siteName + " " + saPeriod});

			func = new ArbitrarilyDiscretizedFunc();
			ArrayList fileLines = FileUtils.loadFile(CYBERSHAKE_HAZARD_DATASET+siteName+"/"+
					"Deterministic_File_Pd_"+saPeriod);
			size = fileLines.size();
			for(int i=0;i<size;++i){
				String xyVal = (String)fileLines.get(i);
				StringTokenizer st = new StringTokenizer(xyVal);
				double xVal = Double.parseDouble(st.nextToken().trim());
				double yVal = Double.parseDouble(st.nextToken().trim());
				func.set(xVal,yVal);
			}
		}catch(Exception e){
			e.printStackTrace();
		}
		return func;
	}

	/**
	 * Gets the list of SA period associated with the site
	 */
	private HashMap loadDataSets(boolean isDeterministic,HashMap siteSrcListMap) {
		//Hashtable for storing the SA Period for each site
		HashMap siteSA_PeriodHazardDatasetMap = new HashMap();

		try {
			File dirs = new File(CYBERSHAKE_HAZARD_DATASET);
			//getting the list of dirs for sites completed in Cybershake.
			File[] dirList = dirs.listFiles();

			// for each data set, read the meta data and sites info
			for (int i = 0; i < dirList.length; ++i) {
				//getting the hazard data files in each site
				if (dirList[i].isDirectory()) {
					try {

						//listing all the SA values files in a given directory
						File hazFiles = new File(dirList[i].getAbsolutePath());
						//listing the files in Cybershake Site directory
						File[] hazardFiles = hazFiles.listFiles();
						//total number of files in the directory
						int numTotalFiles  = hazardFiles.length;

						//creating the Array of ArrayList, with each Arraylist being the
						//filelines read from the hazard data file.
						ArrayList saPeriodVals = new ArrayList();
						TreeSet srcIndexList = null;
						if(isDeterministic){
							srcIndexList = new TreeSet();
						}
						for (int j = 0; j < numTotalFiles; ++j) {
							String fileName = hazardFiles[j].getName();

							if(fileName.startsWith(hazardDataFilesStartString)){
								String saPeriod = fileName.substring(fileName.indexOf("_")+1);
								saPeriodVals.add(saPeriod);
							}
							if(fileName.endsWith("bsa") && isDeterministic){
								String srcRupfileName = fileName.substring(fileName.indexOf("_")+1);
								//System.out.println("Substring fileName:"+srcRupfileName);
								int firstIndex = srcRupfileName.indexOf("_")+1;
								int lastIndex = srcRupfileName.lastIndexOf("_");
								//System.out.println("FirstIndex = "+firstIndex+" LastIndex = "+lastIndex);
								String srcIndex = srcRupfileName.substring(firstIndex,
										lastIndex);
								srcIndexList.add(new Integer(srcIndex));
							}
						}
						siteSA_PeriodHazardDatasetMap.put(dirList[i].getName(), saPeriodVals);
						if(isDeterministic)
							siteSrcListMap.put(dirList[i].getName(),srcIndexList);
					}
					catch (Exception e) {
						e.printStackTrace();
					}
				}
			}
			return siteSA_PeriodHazardDatasetMap;
		}
		catch (Exception e) {
			e.printStackTrace();
		}
		return null;
	}

}

