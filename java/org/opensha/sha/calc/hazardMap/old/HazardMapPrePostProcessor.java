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

package org.opensha.sha.calc.hazardMap.old;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.net.MalformedURLException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Calendar;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.MailUtil;
import org.opensha.sha.calc.hazardMap.old.grid.MetadataHazardMapCalculator;


public class HazardMapPrePostProcessor {

	static final String FROM = "OpenSHA";
	static final String HOST = "email.usc.edu";
	public static final String PRE_PROCESS = "PRE";
	public static final String POST_PROCESS = "POST";

	public HazardMapPrePostProcessor(Element root, boolean pre) {
		Element regionElement = root.element(GriddedRegion.XML_METADATA_NAME);
		GriddedRegion region = GriddedRegion.fromXMLMetadata(regionElement);

		HazardMapJob job = HazardMapJob.fromXMLMetadata(root.element(HazardMapJob.XML_METADATA_NAME));

		String emailAddress =  job.getEmail();

		String mailSubject = "";
		String mailMessage = "";

		String name = "'" + job.getJobName() + "'";

		if (!job.getJobID().equals(job.getJobName()))
			name += " (" + job.getJobID() + ")";

		if (pre) {
			mailSubject = "Grid Job " + name + " is Running!";
			mailMessage = getPreProcessMessage(job, region);
		} else {
			mailSubject = "Grid Job " + name + " has Completed!";
			mailMessage = getPostProcessMessage(job, region);
		}
		System.out.println("Sending message...");
		System.out.println("TO: " + emailAddress);
		System.out.println("SUBJECT: " + mailSubject);
		System.out.println("\n");
		System.out.println(mailMessage);
		MailUtil.sendMail(HOST, FROM, emailAddress, mailSubject, mailMessage);
	}

	public static void main(String args[]) {

		if (args.length == 0) {
			System.err.println("RUNNING FROM DEBUG MODE!");
			args = new String[2];
			args[0] = "output.xml";
			args[1] = POST_PROCESS;
		}

		String metadata = args[0];
		SAXReader reader = new SAXReader();

		boolean pre = false;
		if (args.length >= 2)
			pre = args[1].equals(PRE_PROCESS);

		try {
			System.out.println("Reading xml from " + metadata);
			Document document = reader.read(new File(metadata));
			Element root = document.getRootElement();

			System.out.println("Preparing message...");
			new HazardMapPrePostProcessor(root, pre);
			System.out.println("DONE!");
		} catch (MalformedURLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (DocumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}


	}

	private String getPostProcessMessage(HazardMapJob job, GriddedRegion region) {
		File masterDir = new File("curves/");
		File[] dirList=masterDir.listFiles();

		double minLat = Double.MAX_VALUE;
		double minLon = Double.MAX_VALUE;
		double maxLat = Double.MIN_VALUE;
		double maxLon = -9999;

		int actualFiles = 0;

		// for each file in the list
		if (dirList != null) {
			for(File dir : dirList){
				// make sure it's a subdirectory
				if (dir.isDirectory() && !dir.getName().endsWith(".")) {
					File[] subDirList=dir.listFiles();
					for(File file : subDirList) {
						//only taking the files into consideration
						if(file.isFile()){
							String fileName = file.getName();
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


									if (latVal < minLat)
										minLat = latVal;
									else if (latVal > maxLat)
										maxLat = latVal;
									if (lonVal < minLon)
										minLon = lonVal;
									else if (lonVal > maxLon)
										maxLon = lonVal;

								}
							}
						}
						actualFiles++;
					}
				}


			}
		}

		System.out.println("DONE");
		System.out.println("MinLat: " + minLat + " MaxLat: " + maxLat + " MinLon: " + minLon + " MaxLon " + maxLon);

		// get the start time
		long startTime = 0;
		long endTime = System.currentTimeMillis();
		File startTimeFile = new File(MetadataHazardMapCalculator.START_TIME_FILE);
		if (startTimeFile.exists()) {
			try {
				ArrayList<String> startTimeLines = FileUtils.loadFile(MetadataHazardMapCalculator.START_TIME_FILE);
				if (startTimeLines != null) {
					if (startTimeLines.size() > 0) {
						String startTimeString = startTimeLines.get(0);
						startTime = Long.parseLong(startTimeString);
					}
				}
			} catch (FileNotFoundException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}

		String startTimeString = "";
		Calendar startCal = null;
		if (startTime > 0) {
			startCal = Calendar.getInstance();
			startCal.setTimeInMillis(startTime);
			startTimeString = startCal.getTime().toString();
		} else {
			startTimeString = "Start Time Not Available!";
		}

		Calendar endCal = Calendar.getInstance();
		endCal.setTimeInMillis(endTime);
		String endTimeString = endCal.getTime().toString();

		String mailMessage = "THIS IS A AUTOMATED GENERATED EMAIL. PLEASE DO NOT REPLY BACK TO THIS ADDRESS.\n\n\n"+
		"Grid Computation complete\n"+
		"Expected Num of Files="+region.getNodeCount()+"\n"+
		"Files Generated="+actualFiles+"\n"+
		"Dataset Id="+job.getJobID()+"\n"+
		"Simulation Start Time="+startTimeString+"\n"+
		"Simulation End Time="+endTimeString;

		if (startCal == null) {
			mailMessage += "\nPerformance Statistics not Available";
		} else {
			long millis = endCal.getTimeInMillis() - startCal.getTimeInMillis();
			double secs = (double)millis / 1000d;
			double mins = secs / 60d;
			double hours = mins / 60d;

			mailMessage += "\nTotal Run Time (including overhead):\n";
			if (hours > 1)
				mailMessage += new DecimalFormat(	"###.##").format(hours) + " hours = ";
			mailMessage += new DecimalFormat(	"###.##").format(mins) + " minutes";
			double curvesPerHour = (double)actualFiles / hours;
			mailMessage += "\nCurves Per Hour (including overhead): " + curvesPerHour;
		}

		return mailMessage;
	}

	private String getPreProcessMessage(HazardMapJob job, GriddedRegion region) {
		// get the start time
		long startTime = System.currentTimeMillis();

		Calendar startCal = Calendar.getInstance();
		startCal.setTimeInMillis(startTime);
		String startTimeString = startCal.getTime().toString();

		try {
			FileWriter fw = new FileWriter(MetadataHazardMapCalculator.START_TIME_FILE);
			fw.write(System.currentTimeMillis() + "");
			fw.flush();
			fw.close();
		} catch (IOException e) {
			e.printStackTrace();
		}

		String mailMessage = "THIS IS A AUTOMATED GENERATED EMAIL. PLEASE DO NOT REPLY BACK TO THIS ADDRESS.\n\n\n"+
		"Grid Computation has Begun!\n"+
		"Run time will depend on the datasets chosen, number of sites,\n"+
		"and availiability of the selected grid resource: " + job.getResources().getResourceProvider().getName()+"\n\n"+
		"You will get another e-mail when the grid computation has completed.\n\n"+
		"Expected Num of Files="+region.getNodeCount()+"\n"+
		"Dataset Id="+job.getJobID()+"\n"+
		"Simulation Start Time="+startTimeString+"\n";

		return mailMessage;
	}
}
