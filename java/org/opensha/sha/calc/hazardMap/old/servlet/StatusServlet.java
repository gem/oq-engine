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

package org.opensha.sha.calc.hazardMap.old.servlet;

import java.io.File;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.MalformedURLException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.gridComputing.StorageHost;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.hazardMap.old.CalculationStatus;
import org.opensha.sha.calc.hazardMap.old.HazardMapJob;
import org.opensha.sha.calc.hazardMap.old.HazardMapJobCreator;

public class StatusServlet extends ConfLoadingServlet {
	
	public static final String NAME = "StatusServlet";
	public static final String WORKFLOW_LOG_DIR = "/home/aftershock/opensha/hazmaps/logs";
	
	public static final String OP_GET_DATASET_LIST = "Get Dataset List";
	public static final String OP_GET_DATASETS_WITH_CURVES_LIST = "Get Completed Dataset List";
	public static final String OP_GET_DATASET_REGION = "Get Dataset Region";
	public static final String OP_GET_STATUS = "Get Status";
	
	public static final String STATUS_WORKFLOW_BEGIN = "Workflow Execution Has Begun";
	public static final String STATUS_CALCULATING = "Calculating Curves";
	public static final String STATUS_RETRIEVING = "Retrieving Curves";
	
	int lineNum = 0;
	
	public StatusServlet() {
		super(NAME);
	}
	
	// Process the HTTP Get request
	public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		
		debug("Handling GET");
		
		// get an input stream from the applet
		ObjectInputStream in = new ObjectInputStream(request.getInputStream());
		ObjectOutputStream out = new ObjectOutputStream(response.getOutputStream());
		
		// get the function desired by the user
		String functionDesired = null;
		try {
			debug("Reading Operation");
			functionDesired  = (String) in.readObject();
			
			if (confLoader == null) {
				fail(out, "Failed to load server configuration file.");
				return;
			}
			
			if (functionDesired.equals(OP_GET_STATUS)) {
				debug("Handling STATUS Operation");
				handleStatus(in, out);
			} else if (functionDesired.equals(OP_GET_DATASET_LIST)) {
				debug("Handling LIST Operation");
				handleList(in, out);
			} else if (functionDesired.equals(OP_GET_DATASETS_WITH_CURVES_LIST)) {
				debug("Handling curves LIST Operation");
				handleCompletedList(in, out);
			} else if (functionDesired.equals(OP_GET_DATASET_REGION)) {
				debug("Handling curves LIST Operation");
				handleGetRegion(in, out);
			} else {
				fail(out, "Unknown request: " + functionDesired);
				return;
			}
		} catch (ClassNotFoundException e) {
			fail(out, "ClassNotFoundException: " + e.getMessage());
			return;
		}
		
	}
	
	private void handleList(ObjectInputStream in, ObjectOutputStream out) throws IOException, ClassNotFoundException {
		StorageHost storage = this.confLoader.getPresets().getStorageHosts().get(0);
		
		String dirName = storage.getPath();
		
		debug("Loading IDs for directory: " + dirName);
		
		File dirFile = new File(dirName);
		
		File dirList[] = dirFile.listFiles();
		
		ArrayList<DatasetID> datasets = new ArrayList<DatasetID>();
		
		ArrayList<String> foundLogFiles = new ArrayList<String>();
		
		for (File mapDir : dirList) {
			if (!mapDir.isDirectory())
				continue;
			String datasetID = mapDir.getName();
			if (datasetID.equals("."))
				continue;
			if (datasetID.equals(".."))
				continue;
			
			String xmlFileName = mapDir.getAbsolutePath() + File.separator + datasetID + ".xml";
			File xmlFile = new File(xmlFileName);
			
			if (!xmlFile.exists())
				continue;
			
			debug("Loading id/name from: " + xmlFileName);
			String id[] = null;
			try {
				id = loadJobIDFromXML(xmlFileName);
			} catch (Exception e) {
				e.printStackTrace();
				continue;
			}
			
			if (!id[0].equals(datasetID)) {
				System.out.println("Dataset ID's don't match!!!!");
				System.out.println("From DirName: " + datasetID);
				System.out.println("From XML: " + id[0]);
				continue;
			}
			
			boolean hasLogFile = false;
			File logFile = new File(WORKFLOW_LOG_DIR + "/" + id[0] + ".log");
			if (logFile.exists()) {
				hasLogFile = true;
				debug("This has a log file also: "+ logFile.getAbsolutePath());
				foundLogFiles.add(logFile.getAbsolutePath());
			}
			
			debug("Found dataset: " + datasetID);
			datasets.add(new DatasetID(id[0], id[1], hasLogFile, true));
		}
		
		// now the log dir
		dirFile = new File(WORKFLOW_LOG_DIR);
		dirList = dirFile.listFiles();
		
		for (File logFile : dirList) {
			if (!logFile.isFile())
				continue;
			if (!logFile.getName().trim().endsWith(".log"))
				continue;
			boolean skip = false;
			for (String path : foundLogFiles) {
				if (logFile.getAbsolutePath().equals(path)) {
					skip = true;
					break;
				}
			}
			if (skip)
				continue;
			
			debug("Proccessing log: " + logFile.getAbsolutePath());
			
			ArrayList<String> lines = FileUtils.loadFile(logFile.getAbsolutePath());
			
			String name = null;
			String id = null;
			
			for (int i=0; i<lines.size(); i++) {
				if (i > 4)
					break;
				
				String line = lines.get(i).trim();
				
				if (line.startsWith(HazardMapJobCreator.LOG_COMMENT_ID_PREFIX)) {
					id = line.replace(HazardMapJobCreator.LOG_COMMENT_ID_PREFIX, "").trim();
					debug("Found id: " + id);
					if (name != null)
						break;
					continue;
				}
				if (line.startsWith(HazardMapJobCreator.LOG_COMMENT_NAME_PREFIX)) {
					name = line.replace(HazardMapJobCreator.LOG_COMMENT_NAME_PREFIX, "").trim();
					debug("Found name: " + name);
					if (id != null)
						break;
					continue;
				}
			}
			if (name != null && id != null) {
				boolean matched = false;
				debug("Picked up log for " + name + " (id)");
				for (DatasetID dataset : datasets) {
					if (dataset.getID().equals(id)) {
						matched = true;
						dataset.setIsLogFile(true);
						debug("Matched it!");
						break;
					}
				}
				if (!matched) {
					datasets.add(new DatasetID(id, name, true, false));
				}
			} else {
				debug("Bad log file!");
			}
		}
		
		
		debug("Sorting dataset IDs...");
		Collections.sort(datasets);
		
		debug("Sending dataset IDs...");
		out.writeObject(datasets);
		
		out.flush();
		out.close();
		
		debug("Done handling dataset list");
	}
	
	private void handleCompletedList(ObjectInputStream in, ObjectOutputStream out) throws IOException, ClassNotFoundException {
		StorageHost storage = this.confLoader.getPresets().getStorageHosts().get(0);
		
		String dirName = storage.getPath();
		
		debug("Loading IDs for directory: " + dirName);
		
		File dirFile = new File(dirName);
		
		File dirList[] = dirFile.listFiles();
		
		ArrayList<DatasetID> datasets = new ArrayList<DatasetID>();
		
		for (File mapDir : dirList) {
			if (!mapDir.isDirectory())
				continue;
			String datasetID = mapDir.getName();
			if (datasetID.equals("."))
				continue;
			if (datasetID.equals(".."))
				continue;
			
			String xmlFileName = mapDir.getAbsolutePath() + File.separator + datasetID + ".xml";
			File xmlFile = new File(xmlFileName);
			
			if (!xmlFile.exists())
				continue;
			
			debug("Loading id/name from: " + xmlFileName);
			String id[] = null;
			try {
				id = loadJobIDFromXML(xmlFileName);
			} catch (Exception e) {
				e.printStackTrace();
				continue;
			}
			
			if (!id[0].equals(datasetID)) {
				debug("Dataset ID's don't match!!!!");
				debug("From DirName: " + datasetID);
				debug("From XML: " + id[0]);
				continue;
			}
			
			// now check for curves
			try {
				File curvesDir = new File(mapDir.getAbsolutePath() + File.separator + "curves");
				if (!curvesDir.exists())
					continue;
				boolean checkHasSubdirs = false;
				
				if (checkHasSubdirs) {
					File subDirs[] = curvesDir.listFiles();
					boolean good = false;
					// this checks to make sure that it has at least 1 curve by checking that the
					// curves dir has a subdirectory that's not '.' or '..' (thus the longer than 2
					// check)
					for (File curveSubDir : subDirs) {
						if (curveSubDir.length() > 2) {
							good = true;
							break;
						}
					}
					if (!good)
						continue;
				}
			} catch (Exception e) {
				continue;
			}
			
			debug("Found dataset: " + datasetID);
			datasets.add(new DatasetID(id[0], id[1], true, true));
		}
		
		debug("Sorting dataset IDs...");
		Collections.sort(datasets);
		
		debug("Sending dataset IDs...");
		out.writeObject(datasets);
		
		out.flush();
		out.close();
		
		debug("Done handling datasets with curves list");
	}	
	
	private String[] loadJobIDFromXML(String file) throws MalformedURLException, DocumentException {
		Document document = XMLUtils.loadDocument(file);
		
		Element root = document.getRootElement();
		
		Element jobEl = root.element(HazardMapJob.XML_METADATA_NAME);
		
		String id = jobEl.attributeValue("jobID");
		String name = jobEl.attributeValue("jobName");
		
		String ret[] = {id, name};
		
		return ret;
	}
	
	private void handleGetRegion(ObjectInputStream in, ObjectOutputStream out) throws IOException, ClassNotFoundException {
		StorageHost storage = this.confLoader.getPresets().getStorageHosts().get(0);
		
		String dirName = storage.getPath();
		
		// read the dataset id
		String id = (String)in.readObject();
		
		String datasetPath = dirName + File.separator + id + File.separator;
		String xmlPath = datasetPath + id + ".xml";
		
		File xmlFile = new File(xmlPath);
		if (!xmlFile.exists())
			fail(out, "Dataset XML file doesn't exist!");
		
		GriddedRegion region = null;
		
		try {
			Document doc = XMLUtils.loadDocument(xmlPath);
			Element root = doc.getRootElement();
			Element regionEl = root.element(GriddedRegion.XML_METADATA_NAME);
			region = GriddedRegion.fromXMLMetadata(regionEl);
		} catch (Exception e) {
			fail(out, "Error parsing dataset XML!");
		}
		
		debug("Sending region...");
		out.writeObject(region);
		
		out.flush();
		out.close();
	}
	
	private void handleStatus(ObjectInputStream in, ObjectOutputStream out) throws IOException, ClassNotFoundException {
		String id = (String)in.readObject();
		
		int totalCurves = 0;
		int ip = 0;
		int done = 0;
		int trans = -1;
		
		boolean remote = false;
		
		String status = HazardMapJobCreator.STATUS_NONE;
		
		debug("Detecting Status...");
		
		try {
			String logFile = getLogFileName(id);
			
			ArrayList<String> lines = FileUtils.loadFile(logFile);
			
			String lastLine = null;
			
			lineNum = 0;
			
			for (String line : lines) {
				lineNum++;
				line = line.trim();
				if (line.length() == 0)
					continue;
				if (line.startsWith("#"))
					continue;
				try {
					String tmpStatus = getStatus(line);
					
//				debug("Status: " + tmpStatus);
					
					if (match(tmpStatus, HazardMapJobCreator.STATUS_TEST_JOB))
						remote = false;
					else if (match(tmpStatus, HazardMapJobCreator.STATUS_TEST_JOB_REMOTE)) {
						remote = true;
						trans = 0;
					}
					
					if (tmpStatus.startsWith(HazardMapJobCreator.STATUS_WORKFLOW_BEGIN)) {
						totalCurves = getNumberFromStatus(tmpStatus, lineNum);
						tmpStatus = STATUS_WORKFLOW_BEGIN;
					} else if (tmpStatus.startsWith(HazardMapJobCreator.STATUS_CURVE_CALCULATION_START)) {
						ip += getNumberFromStatus(tmpStatus, lineNum);
						tmpStatus = STATUS_CALCULATING;
					} else if (tmpStatus.startsWith(HazardMapJobCreator.STATUS_CURVE_CALCULATION_END)) {
						done += getNumberFromStatus(tmpStatus, lineNum);
						tmpStatus = STATUS_CALCULATING;
					} else if (remote && tmpStatus.startsWith(HazardMapJobCreator.STATUS_CURVE_RETRIEVED)) {
						trans += getNumberFromStatus(tmpStatus, lineNum);
						tmpStatus = STATUS_RETRIEVING;
					}
					
					lastLine = line;
					status = tmpStatus;
				} catch (Exception e) {
					debug("Bad status line: " + line);
					debug(e.getMessage());
				}
			}
			
			debug("Final Status: " + status);
			
			Date date = null;
			if (lastLine != null)
				date = this.getDate(lastLine);
			
			CalculationStatus stat = new CalculationStatus(status, date, totalCurves, ip, done, trans);
			
			debug("Sending status...");
			out.writeObject(stat);
		} catch (Exception e) {
			fail(out, e.getMessage());
		}
		
		out.flush();
		out.close();
		
		debug("Done handling status");
	}
	
	private boolean match(String message, String status) {
		message = message.trim();
		status = status.trim();
		
		return message.equals(status);
	}
	
	private String stripNumberFromStatus(String status) {
		int strEnd = status.indexOf(":");
		if (strEnd < 0)
			throw new RuntimeException("Bad line parse! (line " + lineNum + ")");
		
		return status.substring(0, strEnd);
	}
	
	public static int getNumberFromStatus(String status, int lineNum) {
		status = status.trim();
//		System.out.println("Getting number status from: " + status);
		int strEnd = status.lastIndexOf(" ");
		if (strEnd < 0)
			throw new RuntimeException("Bad number line parse! (line " + lineNum + ")");
		
		String numStr = status.substring(strEnd + 1).trim();
		
		return Integer.parseInt(numStr);
	}
	
	private String getStatus(String line) {
		int dateEnd = line.indexOf("]");
		if (dateEnd < 0)
			throw new RuntimeException("Bad line parse! (line " + lineNum + ")");
		line = line.substring(dateEnd + 1);
		
		line = line.trim();
		
		return line;
	}
	
	public static Date getDate(String line) throws ParseException {
		int dateStart = line.indexOf("[");
		if (dateStart < 0)
			throw new RuntimeException("Bad date parse!");
		int dateEnd = line.indexOf("]");
		if (dateEnd < 0)
			throw new RuntimeException("Bad date parse!");
		
		line = line.substring(dateStart + 1, dateEnd);
		
		SimpleDateFormat format = HazardMapJobCreator.LINUX_DATE_FORMAT;
		
		return format.parse(line);
	}
	
	public static String getLogFileName(String id) {
		return WORKFLOW_LOG_DIR + "/" + id + ".log";
	}
	
	public static String getIDFromLogFileName(String logFileName) {
		logFileName = logFileName.trim();
		return logFileName.replace(".log", "");
	}

}
