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
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.util.ArrayList;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.OutputFormat;
import org.dom4j.io.SAXReader;
import org.dom4j.io.XMLWriter;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.gridComputing.GridJob;
import org.opensha.commons.gridComputing.GridResources;
import org.opensha.commons.gridComputing.ResourceProvider;
import org.opensha.commons.gridComputing.StorageHost;
import org.opensha.commons.gridComputing.SubmitHost;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupForecast;


public class HazardMapMetadataJobCreator {

	private static final String DEBUG_FOLDER_NAME = "/home/kevin/OpenSHA/condor/jobs/";

	private String restartOriginalDir = "";

	private ArrayList<ProgressListener> progressListeners = new ArrayList<ProgressListener>(); 

	private Document metadata;
	private boolean skipCVMFiles;
	private boolean restart;
	private boolean debug;
	private int startDAG;
	private int endDAG;
	
	private String logDirectory = "";
	
	

	public HazardMapMetadataJobCreator(Document metadata, boolean skipCVMFiles, boolean restart, boolean debug, int startDAG, int endDAG) {
		this.metadata = metadata;
		this.skipCVMFiles = skipCVMFiles;
		this.restart = restart;
		this.debug = debug;
		this.startDAG = startDAG;
		this.endDAG = endDAG;
	}

	public HazardMapMetadataJobCreator(Document metadata, boolean skipCVMFiles, boolean restart) throws InvocationTargetException, IOException {
		this(metadata, skipCVMFiles, restart, false, -1, -1);
	}

	public void createDAG(boolean submit) throws InvocationTargetException, IOException {
		this.setProgressIndeterminate(true);

		// get the root element
		Element root = metadata.getRootElement();
		// load the sites from metadata
		SitesInGriddedRegion sites = this.loadSites(root);
		// load the job params from metadata
		HazardMapJob job = this.loadJob(root, startDAG, endDAG, sites);
		// get and create the output directory (and subdirs)
		String outputDir = this.createDirs(job, restart, debug);
		System.out.println("Loaded " + sites.getRegion().getNodeCount() + " sites!");
		// save the ERF to a file if needed
		if (job.getCalcParams().isSerializeERF()) {
			this.saveERF(root, job, outputDir);
		}
		OrderedSiteDataProviderList siteDataList = null;
		if (job.getCalcParams().isUseCVM()) {
			Element siteDataEl = root.element(OrderedSiteDataProviderList.XML_METADATA_NAME);
			siteDataList = OrderedSiteDataProviderList.fromXMLMetadata(siteDataEl);
		}
		// write out new metadata file
		String metadataFileName = outputDir + job.getConfigFileName();
		this.writeCalcMetadataFile(metadata, metadataFileName);

		// initialize the job creator
		HazardMapJobCreator creator;

		if (startDAG >= 0 && endDAG > startDAG)
			creator = new HazardMapJobCreator(outputDir, sites, startDAG, endDAG, job, siteDataList);
		else
			creator = new HazardMapJobCreator(outputDir, sites, job, siteDataList);
		creator.setLogDirectory(logDirectory);
		creator.logStart();
		creator.addAllProgressListeners(progressListeners);
		
		ResourceProvider rp = job.getResources().getResourceProvider();
		StorageHost storageHost = job.getResources().getStorageHost();
		
		boolean stageOut = true;
		// if it's already being computed on the storage host, don't stage out
		if (rp.getHostName().toLowerCase().contains(storageHost.getSchedulerHostName().toLowerCase())
				|| rp.getHostName().toLowerCase().contains(storageHost.getGridFTPHostName().toLowerCase()))
			stageOut = false;
		creator.setStageOut(stageOut);
		
		// create the actual jobs
		if (restart)
			creator.createRestartJobs(this.restartOriginalDir, stageOut);
		else
			creator.createJobs(stageOut);

		// create all of the DAG elements
		int totalDAG = 7;
		this.updateProgressMessage("Creating DAG");
		this.updateProgress(0, totalDAG);
		if (stageOut)
			creator.createStorageMakeDirJob();
		creator.createMakeDirJob();
		this.updateProgress(1, totalDAG);
		creator.createTestJob();
		this.updateProgress(2, totalDAG);
		creator.createCHModJob();
		this.updateProgress(3, totalDAG);
		creator.createCopyLinkJob();
		this.updateProgress(4, totalDAG);
		creator.createPrePostJob(true);
		creator.createPrePostJob(false);
		this.updateProgress(5, totalDAG);
		creator.createDAG (outputDir, creator.getNumberOfJobs());
		this.updateProgress(6, totalDAG);
		creator.createJarTransferJobFile();
		this.updateProgress(7, totalDAG);
		creator.createJarTransferInputFile(outputDir, rp.getStoragePath());
		
		creator.logCompletion();

		creator.createSubmitDAGScript(submit);
	}
	
	public void setLogDirectory(String logDirectory) {
		this.logDirectory = logDirectory;
	}

	public void addProgressListener(ProgressListener listener) {
		progressListeners.add(listener);
	}

	public boolean removeProgressListener(ProgressListener listener) {
		return progressListeners.remove(listener);
	}

	public void removeAllProgressListeners() {
		progressListeners.clear();
	}

	private void updateProgress(int current, int total) {
		for (ProgressListener listener : progressListeners) {
			listener.updateProgress(current, total);
		}
	}

	private void updateProgressMessage(String message) {
		for (ProgressListener listener : progressListeners) {
			listener.setMessage(message);
		}
	}

	private void setProgressIndeterminate(boolean indeterminate) {
		for (ProgressListener listener : progressListeners) {
			listener.setIndeterminate(indeterminate);
		}
	}

	/**
	 * Loads the Job Params from metadata
	 * @param jobElem
	 * @return
	 */
	private HazardMapJob loadJob(Element root, int start, int end, SitesInGriddedRegion sites) {

		this.updateProgressMessage("Loading Job");

		// extract element for job
		Element jobElem = root.element(GridJob.XML_METADATA_NAME);

		// load job from metadata
		HazardMapJob job = HazardMapJob.fromXMLMetadata(jobElem);
		
		GridResources resources = job.getResources();
		StorageHost storageHost = resources.getStorageHost();
		ResourceProvider rp = resources.getResourceProvider();
		SubmitHost submitHost = resources.getSubmitHost();

		if (start >= 0 && end > start) { // this is a partial DAG
			// create suffix for job name with indices
			int nameLength = HazardMapJobCreator.calcNameLength(sites);
			String suffix = "_" + HazardMapJobCreator.addLeadingZeros(start, nameLength)
			+ "_" + HazardMapJobCreator.addLeadingZeros(end, nameLength);

			// add the suffix to the job name
			job.setJobID(job.getJobID() + suffix);

			// rename the metadata file name
			job.setConfigFileName(job.getJobID() + ".xml");

			// delete and reattach the job to the xml document
			jobElem.detach();
			root = job.toXMLMetadata(root);
		}

		System.out.println(job.toString());

		return job;
	}

	private String createDirs(HazardMapJob job, boolean restart, boolean debug) {
		this.updateProgressMessage("Creating Directories");

		String outputDir = "";

		// if we're just debugging
		if (debug)
			outputDir = DEBUG_FOLDER_NAME;
		else
			outputDir = job.getResources().getSubmitHost().getPath();

		if (!outputDir.endsWith("/"))
			outputDir = outputDir + "/";

		outputDir = outputDir + job.getJobID();

		if (restart) {
			restartOriginalDir = outputDir + "/";
			outputDir = outputDir + "_RESTART/";
		} else
			outputDir = outputDir + "/";

		// create job dir
		File outputDirFile = new File(outputDir);
		if (!outputDirFile.exists())
			outputDirFile.mkdir();

		// create out, err, and log dirs
		File outFile = new File(outputDir + "out/");
		if (!outFile.exists())
			outFile.mkdir();
		File errFile = new File(outputDir + "err/");
		if (!errFile.exists())
			errFile.mkdir();
		File logFile = new File(outputDir + "log/");
		if (!logFile.exists())
			logFile.mkdir();
		File logSHFile = new File(outputDir + HazardMapJobCreator.LOG_SCRIPT_DIR_NAME + "/");
		if (!logSHFile.exists())
			logSHFile.mkdir();

		return outputDir;
	}

	private SitesInGriddedRegion loadSites(Element root) {
		this.updateProgressMessage("Loading Sites");
		Element regionElement = root.element(GriddedRegion.XML_METADATA_NAME);
		GriddedRegion region = GriddedRegion.fromXMLMetadata(regionElement);
		SitesInGriddedRegion sites = new SitesInGriddedRegion(region);
//		if (region.isRectangular()) {
//			try {
//				sites = new SitesInGriddedRegion(region, region.getGridSpacing());
//			} catch (RegionConstraintException e) {
//				sites = new SitesInGriddedRegion(region.getRegionOutline(), region.getGridSpacing());
//			}
//		} else {
//			sites = new SitesInGriddedRegion(region.getRegionOutline(), region.getGridSpacing());
//		}

		return sites;
	}

	private void saveERF(Element root, HazardMapJob job, String outputDir) throws InvocationTargetException, IOException {
		this.updateProgressMessage("Loading ERF");
		// load the erf element from metadata
		Element erfElement = root.element(EqkRupForecast.XML_METADATA_NAME);

		// rename the old erf to ERF_REF so that the params are preserved, but it is not used for calculation
		root.add(erfElement.createCopy("ERF_REF"));
		erfElement.detach();

		// load the erf from metadata
		System.out.println("Creating ERF...");
		EqkRupForecast erf = EqkRupForecast.fromXMLMetadata(erfElement);

		// update it's forecast
		this.updateProgressMessage( "Updating ERF Forecast");
		System.out.println("Updating Forecast...");
		erf.updateForecast();

		// save ERF to file
		String erfFileName = job.getJobID() + "_ERF.obj";
		System.out.println("Saving ERF to " + erfFileName + "...");
		FileUtils.saveObjectInFile(outputDir + erfFileName, erf);

		// create new ERF element and add to root
		Element newERFElement = root.addElement(EqkRupForecast.XML_METADATA_NAME);
		newERFElement.addAttribute("fileName", erfFileName);

		System.out.println("Done with ERF");
	}

	public void writeCalcMetadataFile(Document document, String fileName) throws IOException {
		this.updateProgressMessage("Writing Metadata File");
		OutputFormat format = OutputFormat.createPrettyPrint();
		XMLWriter writer = new XMLWriter(new FileWriter(fileName), format);
		writer.write(document);
		writer.close();
	}

	/**
	 * Main class for creating and (optionally) starting hazard map work flows
	 * 
	 * args: matadata_file [submit]
	 * @param args
	 */
	public static void main(String args[]) {
		boolean skipCVMFiles = false;
		boolean restart = false;
		boolean debug = false;
		if (args.length == 0) {
			System.err.println("RUNNING FROM DEBUG MODE!");
			args = new String[1];
			args[0] = "output.xml";
			debug = true;
		}
		
		boolean submit = false;
		
		if (args.length > 1)
			submit = Boolean.parseBoolean(args[1]);

		try {
			String metadata = args[0];
			SAXReader reader = new SAXReader();
			Document document = reader.read(new File(metadata));

			HazardMapMetadataJobCreator creator = new HazardMapMetadataJobCreator(document, skipCVMFiles, restart, debug, -1, -1);
			creator.createDAG(submit);
		} catch (MalformedURLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (DocumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (InvocationTargetException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}
