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

package org.opensha.sha.calc.hazardMap.old.cron;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;

import org.apache.log4j.ConsoleAppender;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;
import org.apache.log4j.PatternLayout;
import org.apache.log4j.RollingFileAppender;
import org.dom4j.DocumentException;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.hazardMap.old.HazardMapMetadataJobCreator;
import org.opensha.sha.calc.hazardMap.old.servlet.StatusServlet;

public class HazardMapCronJob {
	
	// *************
	// CONFIGURATION
	// *************
	//
	// conf file
	private String confFile;
	// directories
	private String inDir;
	private String processingDir;
	private String processedDir;
	private String failedDir;
	private String logDir;
	
	// *************
	// LOGGING
	// *************
	private  String logFileName = null;
	private String logPattern = "%-5p [%d] (%F:%L) - %m%n";
	protected static Logger logger = Logger.getLogger(HazardMapCronJob.class);
	private static boolean log = false;
	
	/**
	 * Cron job for processing Hazard Map operations submitted through the servlet
	 * @param confFile - Configuration file
	 * @throws DocumentException
	 * @throws IOException 
	 */
	public HazardMapCronJob(String confFile) throws DocumentException, IOException {
		loadConfFile(confFile);
		setupLogger();
		logger.info("~~~~~~~~~~##### Starting Cron Job #####~~~~~~~~~~");
		logger.debug("Input Dir: " + inDir);
		logger.debug("Processing Dir: " + processingDir);
		logger.debug("Processed Dir: " + processedDir);
		logger.debug("Failed Dir: " + failedDir);
		logger.debug("Log Dir: " + logDir);
	}
	
	private void setupLogger() throws IOException {
		String logFilePath = logDir + getLogFileName();
		boolean append = true;
		
		//try to get the pid, must be specified with the vm argument: -Dpid=$$
		//note that this is the PID of the shell, not this individual java process
		String pattern = logPattern;
		String pid = System.getProperty("pid");
		String id = "";
		if (pid != null && pid.length() != 0) {
			id = pid;
		} else {
			// we generate our own id, epoch seconds
			long timeID = System.currentTimeMillis();
			// we don't care about milis, lets get down to seconds:
			timeID = timeID / 1000l;
			// now lets get down to minutes
			double timeDoub = timeID / 60d;
			long prefix = (long)(Math.floor(timeDoub) + 0.1);
			double fraction = 1d - ((double)(prefix + 1l) - timeDoub);
			fraction *= 10;
			fraction = (int)fraction / 10d;
			String fracStr = fraction + "";
			if (fracStr.contains(".")) {
				fracStr = fracStr.substring(fracStr.indexOf(".") + 1);
			}
			id = prefix + "." + fracStr;
		}
		pattern = id + " " + pattern;
		
		RollingFileAppender fileAppender = new RollingFileAppender(new PatternLayout(pattern), logFilePath, append);
		fileAppender.setMaxFileSize("1MB");
		ConsoleAppender consoleAppender = new ConsoleAppender(new PatternLayout(pattern));
		
		logger.addAppender(fileAppender);
		logger.addAppender(consoleAppender);
		
		logger.setLevel(Level.DEBUG);
		
		log = true;
	}
	
	public String getLogFileName() {
		if (logFileName == null) {
			Date now = new Date();
			SimpleDateFormat format = new SimpleDateFormat("yyyyMMdd");
			
			logFileName = format.format(now) + ".txt";
		}
		return logFileName;
	}
	
	private void loadConfFile(String confFile) throws MalformedURLException, DocumentException {
		this.confFile = confFile;
		CronConfLoader conf = new CronConfLoader(confFile);
		
		inDir = conf.getInDir();
		processingDir = conf.getProcessingDir();
		processedDir = conf.getProcessedDir();
		failedDir = conf.getFailedDir();
		logDir = conf.getLogDir();
	}
	
	public void processOperations() {
		ArrayList<File> files = loadInputFiles();
		
		if (files.size() == 0) {
			logger.info("~~~~~~~~~~##### No input files found...exiting #####~~~~~~~~~~");
			return;
		}
		for (File file : files) {
			logger.info("***** Processing File: " + file.getAbsolutePath());
			if (!file.exists()) {
				logger.error("File doesn't exist, skipping: " + file.getAbsolutePath());
				continue;
			}
			
			CronOperation op = null;
			try {
				op = new CronOperation(file.getAbsolutePath());
			} catch (Exception e) {
				logger.error("Error loading " + file.getAbsolutePath(), e);
				failFile(file);
				continue;
			}
			
			try {
				boolean success = handleOperation(op);
				if (success) {
					logger.info("Done Processing '" + op.getOperation() + "' in " + file.getAbsoluteFile());
				} else {
					logger.error("Unknown operation: " + op.getOperation());
					failFile(file);
					continue;
				}
			} catch (Exception e) {
				logger.error("Error processing operation '" + op.getOperation() + "' in: " + file.getAbsolutePath(), e);
				failFile(file);
				continue;
			}
			
			// we're done, move it to processed
			try {
				moveFile(file, processedDir);
			} catch (IOException e) {
				logger.error("Unable to move to processed dir: " + file.getAbsolutePath(), e);
			}
		}
		logger.info("~~~~~~~~~~##### Done processing " + files.size() + " file(s)...exiting #####~~~~~~~~~~");
//		ArrayList<String> this.loadInputFiles();
	}
	
	private boolean handleOperation(CronOperation op) throws InvocationTargetException, IOException {
		if (op.getOperation().equals(CronOperation.OP_SUBMIT)) {
			logger.info("Processing Submit Operation!");
			handleSubmitOperation(op);
		} else if (op.getOperation().equals(CronOperation.OP_CANCEL)) {
			// TODO: implement Cancel operation
			logger.info("Processing Cancel Operation!");
		} else if (op.getOperation().equals(CronOperation.OP_RESTART)) {
			// TODO: implement restart operation
			logger.info("Processing Restart Operation!");
		} else if (op.getOperation().equals(CronOperation.OP_DELETE)) {
			// TODO: implement delete operation
			logger.info("Processing Delete Operation!");
		} else {
			return false;
		}
		return true;
	}
	
	private void handleSubmitOperation(CronOperation op) throws InvocationTargetException, IOException {
		HazardMapMetadataJobCreator creator = new HazardMapMetadataJobCreator(op.getDocument(), false, false, false, -1, -1);
		creator.setLogDirectory(StatusServlet.WORKFLOW_LOG_DIR);
		creator.createDAG(true);
	}
	
	private void handleCancelOperation(CronOperation op) {
		
	}
	
	private ArrayList<File> loadInputFiles(){
		logger.info("Loading Input Files");
		File dir = new File(inDir);
		
		File files[] = dir.listFiles();
		
		ArrayList<File> opFiles = new ArrayList<File>();
		
		for (File file : files) {
			if (file.isDirectory())
				continue;
			logger.info("Found File: " + file.getAbsolutePath());
			try {
				File outFile = moveFile(file, processingDir);
				opFiles.add(outFile);
			} catch (IOException e) {
				// TODO Auto-generated catch block
				logger.error("Error moving " + file.getAbsolutePath() + ", skipping!", e);
			}
		}
		
		return opFiles;
	}
	
	private void failFile(File file) {
		try {
			moveFile(file, failedDir);
		} catch (IOException e) {
			logger.error("Error moving file to 'failed' dir: " + file.getAbsolutePath(), e);
		}
	}
	
	private static File moveFile(File in, String outDir) throws IOException {
		File out = copyFile(in, outDir);
		if (!in.delete() && log)
			logger.warn("Unable to delete " + out.getAbsolutePath());
		return out;
	}
	
	private static File copyFile(File in, String outDir) throws IOException {
		File out = new File(outDir + in.getName());
		
		String message = "Moving file " + in.getAbsolutePath() + " to " + out.getAbsolutePath();
		if (log)
			logger.info(message);
		else
			System.out.println(message);
		
		FileWriter fw = new FileWriter(out);
		
		ArrayList<String> lines = FileUtils.loadFile(in.getAbsolutePath());
		
		for (String line : lines) {
			fw.write(line + "\n");
		}
		
		fw.close();
		
		return out;
	}

	/**
	 * Main class for cron job
	 * @param args - CONFIG_FILE_NAME
	 */
	public static void main(String[] args) {
		if (args.length == 0) {
			// this is a debug run
			System.err.println("WARNING: Running from debug mode!");
			args = new String[1];
			char sep = File.separatorChar;
			String testDir = "org"+sep+"opensha"+sep+"sha"+sep+"calc"+sep+"hazardMap"+sep+"cron"+sep+"test"+sep;
			String testInsDir = testDir + "testInputs";
			String insDir = testDir + "in" + sep;
			for (File file : new File(testInsDir).listFiles()) {
				System.out.println(file.getAbsolutePath());
				if (!file.isFile())
					continue;
				try {
					HazardMapCronJob.copyFile(file, insDir);
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}
			args[0] = testDir+"testConfig.xml";
		}
		if (args.length != 1) {
			System.err.println("USAGE: HazardMapCronJob CONFIG_FILE");
			System.exit(1);
		}
		String confFile = args[0];
		try {
			HazardMapCronJob cron = new HazardMapCronJob(confFile);
			cron.processOperations();
		} catch (DocumentException e) {
			e.printStackTrace();
			System.exit(1);
		} catch (IOException e) {
			e.printStackTrace();
			System.exit(1);
		}
		System.exit(0);
	}

}
