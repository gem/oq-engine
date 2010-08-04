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

import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Date;
import java.util.StringTokenizer;

import org.dom4j.Document;
import org.dom4j.Element;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.SiteDataValueList;
import org.opensha.commons.data.siteData.SiteDataValueListList;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.gridComputing.ResourceProvider;
import org.opensha.commons.gridComputing.StorageHost;
import org.opensha.commons.gridComputing.SubmitHost;
import org.opensha.commons.util.FileNameComparator;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.RunScript;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.hazardMap.old.grid.MetadataHazardMapCalculator;


public class HazardMapJobCreator {

	private String outputDir = "";

	public static final String OUTPUT_FILES_DIR_NAME = "outfiles";
	public static final String SUBMIT_FILES_DIR_NAME = "submitfiles";
	public static final String SCRIPT_FILES_DIR_NAME = "scriptfiles";
	
	public static final boolean APPEND_DOT_COMMAND = true;
	public static final boolean DOT_UPDATE = true;

	public static final String LOG_SCRIPT_DIR_NAME = "log_sh";

	private String logDir = "";
	private String logFileName = "log.txt";

	public static SimpleDateFormat LINUX_DATE_FORMAT = new SimpleDateFormat("EEE MMM dd HH:mm:ss z yyyy");

	// status messages
	// No status
	public static final String STATUS_NONE = "Not started or no status available";
	// In cron inbox
	public static final String STATUS_CRON_IN = "Waiting to be prepared";
	// DAG creation begins
	public static final String STATUS_CREATE_BEGIN = "Creating DAG";
	// DAG has been created
	public static final String STATUS_CREATE_END = "DAG Created Successfully";
	// DAG submitted
	public static final String STATUS_SUBMIT_DAG = "Submitting DAG";
	// DAG submit success
	public static final String STATUS_SUBMIT_DAG_SUCCESS = "DAG Submitted Successfully!";
	// DAG submit fail
	public static final String STATUS_SUBMIT_DAG_FAIL = "DAG Submission Error";
	// workflow beginning
	public static final String STATUS_WORKFLOW_BEGIN = "Workflow Execution Has Begun: ";
	// transfer input files
	public static final String STATUS_TRANSFER_INPUTS = "Transferring Files To Compute Resource";
	// test job
	public static final String STATUS_TEST_JOB = "Running Quick Test";
	// test job for stage out transfers
	public static final String STATUS_TEST_JOB_REMOTE = "Running Quick Remote Test";
	// curve calculation
	public static final String STATUS_CURVE_CALCULATION_START = "Calculating Curves: ";
	public static final String STATUS_CURVE_CALCULATION_END = "Curve Calculation Done: ";
	public static final String STATUS_CURVE_RETRIEVED = "Curves Retrieved: ";
	// post process
	public static final String STATUS_POST_PROCESS = "Curve Calculation Complete, Post Processing";
	// done
	public static final String STATUS_DONE = "Done";
	
	public static final String WRAPPER_SCRIPT_NAME = "launch.sh";
	public static final String RET_VAL_SCRIPT_NAME = "ret_val.sh";
	
	public static final String LOG_COMMENT_NAME_PREFIX = "#name: ";
	public static final String LOG_COMMENT_ID_PREFIX = "#id: ";
	
	public static int NUM_JOB_RETRIES = 3;
	public static double TAR_WALL_TIME_PER_CURVE = 0.05;
	public static int TAR_WALL_TIME_MIN = 5;
	
	public static int DAGMAN_MAX_IDLE = 50;
	public static int DAGMAN_MAX_PRE = 3;
	public static int DAGMAN_MAX_POST = 5;

	private DecimalFormat decimalFormat=new DecimalFormat("0.00##");

	HazardMapJob job;
	ResourceProvider rp;
	StorageHost storageHost;
	SubmitHost submitHost;
	HazardMapCalculationParameters calcParams;

	SitesInGriddedRegion sites;

	int startIndex;
	int endIndex;

	boolean cvmFromFile = true;
	boolean skipCVMFiles = false;
	boolean divertFromSCECToMain = false;

	boolean stageOut = false;

//	String willsFileName = "/" + WillsSiteClass.WILLS_FILE;
//	String basinFileName = "/data/siteType/CVM2/basindepth_OpenSHA.txt";

	boolean gravityLink = false;

	ArrayList<String> regionNames = new ArrayList<String>();
	ArrayList<String> cvmNames = new ArrayList<String>();
	
	private String wrapperScript;
	private String rpWrapperScript;
	private String storageWrapperScript;
	private String retValScript;

	public int nameLength = 7;

	private ArrayList<ProgressListener> progressListeners = new ArrayList<ProgressListener>(); 
	
	private OrderedSiteDataProviderList siteDataList;

	public HazardMapJobCreator(String outputDir, SitesInGriddedRegion sites,
				HazardMapJob job, OrderedSiteDataProviderList siteDataList) {
		this(outputDir, sites, 0, sites.getRegion().getNodeCount() - 1, job, siteDataList);
	}

	public HazardMapJobCreator(String outputDir, SitesInGriddedRegion sites, int startIndex, int endIndex,
				HazardMapJob job, OrderedSiteDataProviderList siteDataList) {
		this.job = job;
		this.siteDataList = siteDataList;
		this.sites = sites;
		this.startIndex = startIndex;
		this.endIndex = endIndex;
		this.outputDir = outputDir;
		
		this.submitHost = job.getResources().getSubmitHost();
		this.storageHost = job.getResources().getStorageHost();
		this.rp = job.getResources().getResourceProvider();
		this.calcParams = job.getCalcParams();
		
		wrapperScript = writeWrapperScript();
		retValScript = writeRetValScript();
		
		nameLength = calcNameLength(sites);
		
		logFileName = job.getJobID() + ".log";
		
//		this.executable = rp_javaPath;
//		this.globusscheduler = rp_host + "/" + rp_batchScheduler;
	}
	
	public static int calcNameLength(SitesInGriddedRegion sites) {
		String maxSite = (sites.getRegion().getNodeCount() - 1) + "";
		return maxSite.length();
	}

	public static String getCurrentDateString() {
		Date date = new Date(System.currentTimeMillis());
		String dateStr = LINUX_DATE_FORMAT.format(date);
		return dateStr;
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

	public boolean addAllProgressListeners(Collection<ProgressListener> listeners) {
		return progressListeners.addAll(listeners);
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

	public void createJob(int start, int end) throws IOException {
		boolean testJob = false;
		if (end < 0) {// this is the initial test job, just do one curve
			testJob = true;
			end = start;
		}

		String regionName = addLeadingZeros(start, nameLength) + "_" + addLeadingZeros(end, nameLength);
		String jobFilePrefix = "Job_" + regionName;
		if (testJob)
			jobFilePrefix = "testJob";
		String cvmFileName = "";
		if (calcParams.isUseCVM()) {
			cvmFileName = createCVMJobFile(regionName, start, end);
			cvmNames.add(cvmFileName);
		}

		String globusscheduler = rp.getHostName() + "/" + rp.getBatchScheduler();

		String globusrsl = "";
		if (testJob) {
			int oldWall = rp.getGlobusRSL().getMaxWallTime();
			int wallTime = 15;
			if (wallTime < oldWall) {
				rp.getGlobusRSL().setMaxWallTime(wallTime);
				globusrsl = rp.getGlobusRSL().getRSLString();
				rp.getGlobusRSL().setMaxWallTime(oldWall);
			} else
				globusrsl = rp.getGlobusRSL().getRSLString();
		} else {
			globusrsl = rp.getGlobusRSL().getRSLString();
		}
//		if (divertFromSCECToMain) {
//		if (job.rp.rp_host.toLowerCase().contains("hpc.usc.edu")) {
//		if (globusrsl.toLowerCase().contains("(queue=scec)")) {
//		if (jobs % 20 == 0) {
//		globusrsl = globusrsl.replace("(queue=scec)", "");
//		}
//		}
//		}
//		}
		
		String endStr;
		if (testJob)
			endStr = "TEST";
		else
			endStr = end + "";
		
		String executable;
		String arguments;
		
		String javaArgs = "-cp " + rp.getStoragePath() + "/" + job.getJobID()
				+ "/opensha_gridHazMapGenerator.jar " + MetadataHazardMapCalculator.class.getName()+ " "
				+ start + " " + endStr + " " + job.getConfigFileName() + " " + cvmFileName;
		
		if (rp.isGridUniverse()) {
			executable = "/bin/sh";
			arguments = rpWrapperScript + " " + rp.getJavaPath() + " " + javaArgs;
		} else {
			executable = rp.getJavaPath();
			arguments = javaArgs;
		}

		String jobFileName = jobFilePrefix + ".sub";
		if (!testJob)
			regionNames.add(regionName);
		System.out.println("Creating " + jobFileName);
		FileWriter fr = new FileWriter(outputDir + jobFileName);

		fr.write("universe = " + rp.getUniverse() + "\n");
		if (rp.isGridUniverse()) {
			fr.write("globusrsl = " + globusrsl + "\n");
			fr.write("globusscheduler = " + globusscheduler + "\n");
		}
		String requirements = rp.getRequirements();
		if (requirements.length() > 0)
			fr.write("requirements = " + requirements + "\n");
		fr.write("should_transfer_files = yes" + "\n");
		fr.write("WhenToTransferOutput = ON_EXIT" + "\n");
		fr.write("executable = " + executable + "\n");
//		fr.write("arguments = -cp " + job.rp.rp_storagePath + "/" + job.jobName + "/opensha_gridHazMapGenerator.jar org.opensha.sha.calc.GridMetadataHazardMapCalculator " + start + " " + endStr + " " + job.getConfigFileName() + " " + cvmFileName + " " + job.threadsPerJob + " " + "\n");
		fr.write("arguments = " + arguments + "\n");
		fr.write("copy_to_spool = false" + "\n");
		if (testJob) {
			fr.write("output = " + jobFilePrefix + ".out" + "\n");
			fr.write("error = " + jobFilePrefix + ".err" + "\n");
			fr.write("log = " + jobFilePrefix + ".log" + "\n");
		} else {
			fr.write("output = out/" + jobFilePrefix + ".out" + "\n");
			fr.write("error = err/" + jobFilePrefix + ".err" + "\n");
			fr.write("log = log/" + jobFilePrefix + ".log" + "\n");
		}
		fr.write("transfer_executable = false" + "\n");
		fr.write("transfer_error = true" + "\n");
		fr.write("transfer_output = true" + "\n");
		fr.write("notification = never" + "\n");
		fr.write("remote_initialdir = " + rp.getStoragePath() + "/" + job.getJobID() + "\n");
		fr.write("queue" + "\n\n");

		fr.close();

//		// create the expected files
//		if (!testJob) {
//		int curveJobEndIndex = end-1;
//		if (curveJobEndIndex > this.endIndex)
//		curveJobEndIndex = this.endIndex;
//		fr = new FileWriter(outputDir + jobFilePrefix + ".txt");
//		fr.write("# globusscheduler = " + globusscheduler + "\n");
//		fr.write("# remote_initialdir = " + rp.getStoragePath() + "/" + job.getJobID() + "\n");
//		for (int j=start; j<=curveJobEndIndex; j++) {
//		try {
//		Location loc = sites.getSite(j).getLocation();
//		String lat = decimalFormat.format(loc.getLatitude());
//		String lon = decimalFormat.format(loc.getLongitude());
//		String jobDir = lat + "/";
//		fr.write(jobDir + lat + "_" + lon + ".txt\n");
//		} catch (RegionConstraintException e) {
//		e.printStackTrace();
//		}
//		}
//		fr.close();
//		}

		// create the expected files
		if (!testJob && stageOut) {
			int curveJobEndIndex = end-1;
			if (curveJobEndIndex > this.endIndex)
				curveJobEndIndex = this.endIndex;
			ArrayList<String> outfiles = new ArrayList<String>();
			for (int j=start; j<=curveJobEndIndex; j++) {
				try {
					Location loc = sites.getSite(j).getLocation();
					String lat = decimalFormat.format(loc.getLatitude());
					String lon = decimalFormat.format(loc.getLongitude());
					String jobDir = "curves/" + lat + "/";
					String name = jobDir + lat + "_" + lon + ".txt";
					outfiles.add(name);
				} catch (RegionConstraintException e) {
					e.printStackTrace();
				}
			}
			String tarFileName = this.createStageOutZipJobFile(regionName, outfiles);
			this.createStageOutPostJobFiles(regionName, tarFileName);
		}
	}

	public void createJobs(boolean stageOut) throws IOException {
		System.out.println("Creating jobs for " + sites.getRegion().getNodeCount() + " sites!");

		File outDir = new File(outputDir);
		if (!outDir.exists())
			outDir.mkdir();
		int jobs = 0;
		long start = System.currentTimeMillis();

		// find out how many we're making
		int expectedJobs = 0;
		for (int i=startIndex; i<=endIndex; i+=calcParams.getSitesPerJob()) {
			expectedJobs++;
		}

		int updateInterval = 1;
		if (expectedJobs > 100) {
			updateInterval = expectedJobs / 100;
		}

		this.setProgressIndeterminate(false);

		for (int i=startIndex; i<=endIndex; i+=calcParams.getSitesPerJob()) {
			if (jobs % updateInterval == 0)
				this.updateProgress(jobs, expectedJobs);
			createJob(i, i + calcParams.getSitesPerJob());
			jobs++;
		}
		System.out.println("Tobal Jobs Created: " + jobs);
		long duration = System.currentTimeMillis() - start;
		//double estimate = average * (double)numSites + (double)overhead * (numSites / curvesPerJob);
		double mins = duration / 60000d;
		String minsStr = new DecimalFormat(	"###.##").format(mins);
		String seconds = new DecimalFormat(	"###.##").format(duration / 1000d);
		System.out.println("Total Job Time: " + seconds + " seconds = " + minsStr + " mins");
		System.out.println("Time Per Job: " + new DecimalFormat(	"###.##").format(duration / (double)jobs / 1000d) + " seconds");

		double estimatedMins = (mins / (double)jobs) * (double)sites.getRegion().getNodeCount() / (double)calcParams.getSitesPerJob();
		System.out.println("Estimated time (based on current, " + sites.getRegion().getNodeCount() + " curves): " + new DecimalFormat(	"###.##").format(estimatedMins) + " mins");
		estimatedMins = (mins / (double)jobs) * 200000d / (double)calcParams.getSitesPerJob();
		System.out.println("Estimated time (based on 200,000 curves): " + new DecimalFormat(	"###.##").format(estimatedMins) + " mins");
	}

	public void createTestJob() throws IOException {
		this.createJob(this.startIndex, -1);
	}

	public void createRestartJobs(String originalDir, boolean stageOut) throws IOException {

		this.setProgressIndeterminate(true);
		this.updateProgressMessage("Finding jobs to be restarted");

		File outDir = new File(originalDir);
		File dirList[] = outDir.listFiles();

		Arrays.sort(dirList, new FileNameComparator());

		ArrayList<int[]> badJobs = new ArrayList<int[]>(); 

		for (File file : dirList) {
			if (file.getName().endsWith(".sub") && file.getName().startsWith("Job_")) {
				String outFileDir = file.getParentFile().getAbsolutePath() + "/out/";
				String outFileName = file.getName().replace(".sub", ".out");
				String outFilePath = outFileDir + outFileName;
				File outFile = new File(outFilePath);
				boolean good = false;
				System.out.println("Checking " + file.getName());
				if (outFile.exists()) {
					try {
						ArrayList<String> lines = FileUtils.loadFile(outFilePath);
						for (String line : lines) {
							if (line.contains("DONE")) {
								good = true;
								break;
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

				if (!good) {
					StringTokenizer tok = new StringTokenizer(file.getName(), "_.");

					// "Job"
					tok.nextToken();
					int start = Integer.parseInt(tok.nextToken());
					int end = Integer.parseInt(tok.nextToken());

					System.out.println("Start: " + start + " End: " + end);

					int indices[] = {start, end};
					badJobs.add(indices);
				}
			}
		}

		int cur = 0;
		int num = badJobs.size();
		this.setProgressIndeterminate(false);
		this.updateProgressMessage("Creating Restart Jobs");
		for (int[] badJob : badJobs) {
			this.updateProgress(cur++, num);
			createJob(badJob[0], badJob[1]);
		}

	}

	private String createCVMJobFile(String jobName, int startIndex, int endIndex) {
		String fileName = jobName + ".cvm";

		if (skipCVMFiles) {// we're skipping creation of the CVM files
			return fileName;
		}

		LocationList locs = new LocationList();

		if (endIndex > this.endIndex)
			endIndex = this.endIndex;

		System.out.println("Writing CVM info for sites " + startIndex + " to " + endIndex + " into " + fileName);

		for (int i=startIndex; i<=endIndex; i++) {
			try {
				locs.add(sites.getSite(i).getLocation());
			} catch (RegionConstraintException e) {
				e.printStackTrace();
			}
		}
//		System.out.println("Locations: " + locs.size());
		
		ArrayList<SiteDataValueList<?>> datas = new ArrayList<SiteDataValueList<?>>(); 
		
		for (int i=0; i<this.siteDataList.size(); i++) {
			SiteDataAPI<?> provider = siteDataList.getProvider(i);
			if (siteDataList.isEnabled(i)) {
				try {
					SiteDataValueList<?> data = provider.getAnnotatedValues(locs);
					datas.add(data);
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		}
		
		SiteDataValueListList lists = new SiteDataValueListList(datas);
		
		Document doc = XMLUtils.createDocumentWithRoot();
		Element root = doc.getRootElement();
		
		lists.toXMLMetadata(root);
		
		try {
			XMLUtils.writeDocumentToFile(outputDir + fileName, doc);
		} catch (IOException e) {
			e.printStackTrace();
		}
		
		return fileName;
	}

	public void createSubmitScripts(int jobsPerScript) throws IOException {
		int i = 0;
		int scripts = 0;
		FileWriter fr = null;
		FileWriter all = new FileWriter(outputDir + "submit_all.sh");
		while (i < regionNames.size()) {
			if (i % jobsPerScript == 0) {
				if (fr != null)
					fr.close();
				String fileName = outputDir + "submit_" + addLeadingZeros(scripts, nameLength) + ".sh";
				System.out.println("Creating " + fileName);
				fr = new FileWriter(fileName);
				scripts++;
			}
			fr.write("condor_submit Job_" + regionNames.get(i) + ".sub" + "\n");
			all.write("condor_submit Job_" + regionNames.get(i) + ".sub" + "\n");
			fr.write("sleep 2\n");
			all.write("sleep 1\n");
			i++;
		}
		if (fr != null)
			fr.close();
		all.close();
	}

	public static String addLeadingZeros(int num, int length) {
		String str = num + "";
		if (str.length() > length)
			return str;

		while (str.length() < length)
			str = "0" + str;

		return str;
	}

	public void createMakeDirJob() throws IOException {
		FileWriter fr = new FileWriter(outputDir + "mkdir.sub");

		String mainDir = rp.getStoragePath() + "/" + job.getJobID();
		String tarDir = mainDir + "/tgz";
		String tarInDir = mainDir + "/tgz_in";

		fr.write("universe = grid" + "\n");
		fr.write("executable = /bin/mkdir" + "\n");
		fr.write("arguments = -v -p " + mainDir + " " + tarDir + " " + tarInDir + "\n");
		fr.write("notification = NEVER" + "\n");
		fr.write("globusrsl = (jobtype=single)" + "\n");
		fr.write("globusscheduler = " + rp.getHostName() + "/" + rp.getForkScheduler() + "\n");
		fr.write("copy_to_spool = false" + "\n");
		fr.write("error = mkdir.err" + "\n");
		fr.write("log = mkdir.log" + "\n");
		fr.write("output = mkdir.out" + "\n");
		fr.write("transfer_executable = false" + "\n");
		fr.write("transfer_error = true" + "\n");
		fr.write("transfer_output = true" + "\n");
		fr.write("periodic_release = (NumSystemHolds <= 3)" + "\n");
		fr.write("periodic_remove = (NumSystemHolds > 3)" + "\n");
		fr.write("remote_initialdir = /tmp" + "\n");
		fr.write("queue" + "\n");
		fr.write("" + "\n");

		fr.flush();
		fr.close();
	}

	public void createStorageMakeDirJob() throws IOException {
		FileWriter fr = new FileWriter(outputDir + "mkdirStorage.sub");

		String mainDir = storageHost.getPath() + "/" + job.getJobID();
		String tgzDir = mainDir + "/tgz";

		fr.write("universe = grid" + "\n");
		fr.write("executable = /bin/mkdir" + "\n");
		fr.write("arguments = -v -p " + mainDir + " " + tgzDir + "\n");
		fr.write("notification = NEVER" + "\n");
		fr.write("globusrsl = (jobtype=single)" + "\n");
		fr.write("globusscheduler = " + storageHost.getSchedulerHostName() + "/" + storageHost.getForkScheduler() + "\n");
		fr.write("copy_to_spool = false" + "\n");
		fr.write("error = mkdirStorage.err" + "\n");
		fr.write("log = mkdirStorage.log" + "\n");
		fr.write("output = mkdirStorage.out" + "\n");
		fr.write("transfer_executable = false" + "\n");
		fr.write("transfer_error = true" + "\n");
		fr.write("transfer_output = true" + "\n");
		fr.write("periodic_release = (NumSystemHolds <= 3)" + "\n");
		fr.write("periodic_remove = (NumSystemHolds > 3)" + "\n");
		fr.write("remote_initialdir = /tmp" + "\n");
		fr.write("queue" + "\n");
		fr.write("" + "\n");

		fr.flush();
		fr.close();
	}

	public void createCHModJob() throws IOException {
		FileWriter fw = new FileWriter(outputDir + "chmod.sh");
		fw.write("/bin/chmod +r * \n");
		fw.write("/bin/chmod -R +rx curves \n");
		fw.flush();
		fw.close();

		FileWriter fr = new FileWriter(outputDir + "chmod.sub");

		fr.write("universe = grid" + "\n");
		fr.write("executable = /bin/sh" + "\n");
		if (stageOut)
			fr.write("arguments = " + storageHost.getPath() + "/" + job.getJobID() + "/chmod.sh" + "\n");
		else
			fr.write("arguments = " + rp.getStoragePath() + "/" + job.getJobID() + "/chmod.sh" + "\n");
		fr.write("notification = NEVER" + "\n");
		fr.write("globusrsl = (jobtype=single)" + "\n");
		if (stageOut)
			fr.write("globusscheduler = " + storageHost.getSchedulerHostName() + "/" + storageHost.getForkScheduler() + "\n");
		else
			fr.write("globusscheduler = " + rp.getHostName() + "/" + rp.getForkScheduler() + "\n");
		fr.write("copy_to_spool = false" + "\n");
		fr.write("error = chmod.err" + "\n");
		fr.write("log = chmod.log" + "\n");
		fr.write("output = chmod.out" + "\n");
		fr.write("transfer_executable = false" + "\n");
		fr.write("transfer_error = true" + "\n");
		fr.write("transfer_output = true" + "\n");
		fr.write("periodic_release = (NumSystemHolds <= 3)" + "\n");
		fr.write("periodic_remove = (NumSystemHolds > 3)" + "\n");
		if (stageOut)
			fr.write("remote_initialdir = " + storageHost.getPath() + "/" + job.getJobID() + "\n");
		else
			fr.write("remote_initialdir = " + rp.getStoragePath() + "/" + job.getJobID() + "\n");
		fr.write("queue" + "\n");
		fr.write("" + "\n");

		fr.flush();
		fr.close();
	}

	public void createCopyLinkJob() throws IOException {
		FileWriter fr = new FileWriter(outputDir + "copy_link.sub");

		fr.write("universe = grid" + "\n");
		fr.write("executable = /opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/HazardMapXMLDatasets/copy_link.pl" + "\n");
		fr.write("arguments = " + job.getJobID() + "\n");
		fr.write("notification = NEVER" + "\n");
		fr.write("globusrsl = (jobtype=single)" + "\n");
		fr.write("globusscheduler = gravity.usc.edu/jobmanager-fork" + "\n");
		fr.write("copy_to_spool = false" + "\n");
		fr.write("error = copy_link.err" + "\n");
		fr.write("log = copy_link.log" + "\n");
		fr.write("output = copy_link.out" + "\n");
		fr.write("transfer_executable = false" + "\n");
		fr.write("transfer_error = true" + "\n");
		fr.write("transfer_output = true" + "\n");
		fr.write("periodic_release = (NumSystemHolds <= 3)" + "\n");
		fr.write("periodic_remove = (NumSystemHolds > 3)" + "\n");
		fr.write("remote_initialdir = " + "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/HazardMapXMLDatasets/" + "\n");
		fr.write("queue" + "\n");
		fr.write("" + "\n");

		fr.flush();
		fr.close();
	}
	
	private boolean hostNamesMatch(String host1, String host2) {
		host1 = host1.trim();
		host2 = host2.trim();
		
		host1 = host1.toLowerCase();
		host2 = host2.toLowerCase();
		
		if (host1.equals(host2))
			return true;
		
		return false;
	}

	public void createPrePostJob(boolean pre) throws IOException {
		String jobName = "";
		if (pre)
			jobName = "pre";
		else
			jobName = "post";
		FileWriter fr = new FileWriter(outputDir + jobName + ".sub");
		
		String prePostStr = "";
		if (pre)
			prePostStr = HazardMapPrePostProcessor.PRE_PROCESS;
		else
			prePostStr = HazardMapPrePostProcessor.POST_PROCESS;
		
		String javaPath;
		String javaArgs;
		String executable;
		String arguments;
		
		// we want to use the resource provider if:
		// * it's a 'pre' run
		boolean useRP = !stageOut || hostNamesMatch(rp.getHostName(), storageHost.getSchedulerHostName());
		
		if (!useRP) {
			javaPath = storageHost.getJavaPath();
			javaArgs = "-cp " + storageHost.getJarPath() + " org.opensha.sha.calc.hazardMap.HazardMapPrePostProcessor " + job.getConfigFileName() + " " + prePostStr;
		} else {
			javaPath = rp.getJavaPath();
			javaArgs = "-cp " + rp.getStoragePath() + "/" + job.getJobID() + "/" + "opensha_gridHazMapGenerator.jar" + " org.opensha.sha.calc.hazardMap.HazardMapPrePostProcessor " + job.getConfigFileName() + " " + prePostStr;
		}
		
//		if (rp.isGridUniverse() && useRP) {
//			executable = "/bin/sh";
//			arguments = wrapperScript + " " + javaPath + " " + javaArgs;
//		} else {
		executable = javaPath;
		arguments = javaArgs;
//		}

		if (useRP)
			fr.write("universe = " + rp.getUniverse() + "\n");
		else
			fr.write("universe = grid" + "\n");
		
		fr.write("executable = " + executable + "\n");
		fr.write("arguments = " + arguments + "\n");

		fr.write("notification = NEVER" + "\n");
		fr.write("globusrsl = (jobtype=single)" + "\n");
		if (!useRP)
			fr.write("globusscheduler = " + storageHost.getSchedulerHostName() + "/" + storageHost.getForkScheduler() + "\n");
		else
			fr.write("globusscheduler = " + rp.getHostName() + "/" + rp.getForkScheduler() + "\n");
		fr.write("copy_to_spool = false" + "\n");
		fr.write("error = " + jobName + ".err" + "\n");
		fr.write("log = " + jobName + ".log" + "\n");
		fr.write("output = " + jobName + ".out" + "\n");
		fr.write("transfer_executable = false" + "\n");
		fr.write("transfer_error = true" + "\n");
		fr.write("transfer_output = true" + "\n");
		fr.write("periodic_release = (NumSystemHolds <= 3)" + "\n");
		fr.write("periodic_remove = (NumSystemHolds > 3)" + "\n");
		if (!useRP)
			fr.write("remote_initialdir = " + storageHost.getPath() + "/" + job.getJobID() + "\n");
		else
			fr.write("remote_initialdir = " + rp.getStoragePath() + "/" + job.getJobID() + "\n");
		fr.write("queue" + "\n");
		fr.write("" + "\n");

		fr.flush();
		fr.close();
	}

	public void createJarTransferInputFile (String outputDir, String remoteJobDir) {
		
		ArrayList<String> sources = new ArrayList<String>();
		ArrayList<String> dests = new ArrayList<String>();

		String gridFTPPath = rp.getGridFTPHost() + rp.getStoragePath() + "/" + job.getJobID();
		
		// the jar file
		sources.add("gsiftp://"+ submitHost.getHostName() + submitHost.getDependencyPath() +"/opensha_gridHazMapGenerator.jar");
		dests.add("gsiftp://"+gridFTPPath+"/"+"opensha_gridHazMapGenerator.jar");
		
		if (rp.isGridUniverse()) {
			// if it's the grid/globus universe, we need to capture send the launcher script
			sources.add("gsiftp://"+ submitHost.getHostName() + this.wrapperScript + "\n");
			dests.add("gsiftp://"+gridFTPPath+"/"+WRAPPER_SCRIPT_NAME);
		}
		
		if (calcParams.isSerializeERF()) {
			// serialized ERF
			sources.add("gsiftp://"+ submitHost.getHostName() + submitHost.getPath() +"/" +job.getJobID() +"/" + job.getJobID() + "_ERF.obj");
			dests.add("gsiftp://"+gridFTPPath+"/"+ job.getJobID() + "_ERF.obj");
		}
		
		// conf file
		sources.add("gsiftp://"+ submitHost.getHostName() + submitHost.getPath() + "/"+job.getJobID() +"/" + job.getConfigFileName());
		dests.add("gsiftp://" + gridFTPPath+"/" + job.getConfigFileName());
		
		// chmod script
		sources.add("gsiftp://"+ submitHost.getHostName() + submitHost.getPath() + "/"+job.getJobID() +"/chmod.sh");
		if (stageOut)
			dests.add("gsiftp://" + storageHost.getGridFTPHostName() + storageHost.getPath() + "/" + job.getJobID() +"/" + "chmod.sh");
		else
			dests.add("gsiftp://" + gridFTPPath +"/" + "chmod.sh");
		
		if (stageOut) {
			// send the conf file to the storage host
			sources.add("gsiftp://"+ submitHost.getHostName() + submitHost.getPath() + "/"+job.getJobID() +"/" + job.getConfigFileName());
			dests.add("gsiftp://" + storageHost.getGridFTPHostName() + storageHost.getPath() + "/" + job.getJobID() +"/" + job.getConfigFileName());
			
			// send the launcher
			sources.add("gsiftp://"+ submitHost.getHostName() + this.wrapperScript);
			dests.add("gsiftp://"+ storageHost.getGridFTPHostName() + storageHost.getPath() + "/" + job.getJobID() +"/"+ WRAPPER_SCRIPT_NAME);
			
			// send the tar/zip input files
			for (String name : tarInFiles) {
				sources.add("gsiftp://"+ submitHost.getHostName() + submitHost.getPath() +"/" +job.getJobID() +"/"+name);
				dests.add("gsiftp://" + gridFTPPath+"/" + name);
			}
		}
		
		for (String name : cvmNames) {
			// cvm files
			sources.add("gsiftp://"+ submitHost.getHostName() + submitHost.getPath() +"/" +job.getJobID() +"/"+name);
			dests.add("gsiftp://"+gridFTPPath+"/"+name);
		}
		
		try {
			FileWriter fw = new FileWriter(outputDir + "/test.in");
			
			boolean first = true;
			
			for (int i=0; i<sources.size(); i++) {
				if (first)
					first = false;
				else
					fw.write("\n\n");
				
				fw.write(sources.get(i) + "\n");
				fw.write(dests.get(i) + "\n");
			}

			fw.close();
		} catch (Exception e) {
			System.out.println (e);
		}		
	}

	public void createDAG (String outputDir, int numberOfJobs) {

		boolean onHPC = rp.getHostName().toLowerCase().contains("hpc.usc.edu") || 
		(stageOut && (storageHost.getSchedulerHostName().toLowerCase().contains("hpc.usc.edu")
				|| storageHost.getGridFTPHostName().toLowerCase().contains("hpc.usc.edu")));

		String jobName = "curves_";
		String tarJobName = "tar_";
		String untarJobName = "untar_";
		
		boolean isGridUniverse = rp.isGridUniverse();

		try {
			BufferedOutputStream fos = new BufferedOutputStream (new FileOutputStream(outputDir+"/main.dag"));
			StringBuffer str = new StringBuffer ();

			// code for create directory job
			str.append("# Hazard Map DAG\n");
			str.append("# This is a DAG to create an OpenSHA Hazard Map\n");
			str.append("# It was generated by " + this.getClass().getPackage().toString() + "." + this.getClass().getName() + " \n");
			str.append("\n");
			str.append("\n");
			str.append("# This Job creates the direcory on the compute resource where all input files\n");
			str.append("# and curves will be stored\n");
			str.append("Job create_dir mkdir.sub\n");
			str.append("Script PRE create_dir " + createLogShellScript("mkdir", STATUS_WORKFLOW_BEGIN + this.sites.getRegion().getNodeCount()) + "\n");
			str.append("RETRY create_dir " + NUM_JOB_RETRIES + "\n");
			str.append("\n");
			str.append("\n");
			if (stageOut) {
				str.append("# This Job creates the direcory on the compute resource where all input files\n");
				str.append("# and curves will be stored\n");
				str.append("Job create_storage_dir mkdirStorage.sub" + "\n");
				str.append("RETRY create_storage_dir " + NUM_JOB_RETRIES + "\n");
				str.append("\n");
				str.append("\n");
			}
//			str.append("Job ");
//			str.append("create_dir ");
//			str.append ("HPC_cdir.sub");			
//			str.append("\n");
//			str.append("\n");			
			// main job
			str.append("# This job transfers the ERF obj file (if necessary), the jar file,\n");
			str.append("# and all CVM files (if necessary)\n");
			str.append("Job ");
			str.append("transfer_input_files ");
			str.append ("transfer_input_files.sub\n");
			str.append("Script PRE transfer_input_files " + createLogShellScript("transfer_input_files", STATUS_TRANSFER_INPUTS) + "\n");
			str.append("RETRY transfer_input_files " + NUM_JOB_RETRIES + "\n");
			str.append("\n");
			str.append("\n");
			str.append("# This is a simple test job which just computes one curve before all of the regular\n");
			str.append("# compute jobs are submitted\n");
			str.append("Job test testJob.sub" + "\n");
			String testMessage;
			if (stageOut)
				testMessage = STATUS_TEST_JOB_REMOTE;
			else
				testMessage = STATUS_TEST_JOB;
			str.append("Script PRE test " + createLogShellScript("test", testMessage) + "\n");
			if (isGridUniverse) {
				str.append("Script POST test " + retValScript + " " + outputDir + "testJob.out" + "\n");
			}
			str.append("RETRY test " + NUM_JOB_RETRIES + "\n");
			str.append("\n");
			str.append("\n");
			str.append("# This job chmod's all of the curves to become globally readable after computation\n");
			str.append("Job chmod chmod.sub" + "\n");
			str.append("Script PRE chmod " + createLogShellScript("post", STATUS_POST_PROCESS) + "\n");
			str.append("RETRY chmod " + NUM_JOB_RETRIES + "\n");
			str.append("\n");
			str.append("\n");
			if (onHPC || stageOut) {
				str.append("# This is the pre processing job that sends an e-mail to the submitter at the beginning\n");
				str.append("# of the computation\n");
				str.append("Job preProcess pre.sub" + "\n");
				str.append("RETRY preProcess " + NUM_JOB_RETRIES + "\n");
				str.append("\n");
				str.append("\n");
				str.append("# This is the post processing job that sends an e-mail to the submitter at the end\n");
				str.append("# of the computation\n");
				str.append("Job postProcess post.sub" + "\n");
				str.append("Script POST postProcess " + createLogShellScript("done", STATUS_DONE) + "\n");
				str.append("RETRY postProcess " + NUM_JOB_RETRIES + "\n");
				str.append("\n");
				str.append("\n");
			}

			if (onHPC && gravityLink) {
				str.append("# This job is run on gravity.usc.edu and sets up links so that maps can be plotted\n");
				str.append("# directly from HPC (over nfs)\n");
				str.append("Job copy_link copy_link.sub" + "\n");
				str.append("RETRY copy_link " + NUM_JOB_RETRIES + "\n");
				str.append("\n");
				str.append("\n");
			}
			// child jobs

			str.append("# These are the actual hazard curve calculation jobs\n");
			str.append("# and any stage out jobs if needed\n");
			int num = 1;
			String curvePreScript = createLogShellScript("curve_pre", STATUS_CURVE_CALCULATION_START + this.calcParams.getSitesPerJob());
			String curvePostScript = createLogShellScript("curve_post", STATUS_CURVE_CALCULATION_END + this.calcParams.getSitesPerJob());
			String curveStageOutPostScript = null;
			ArrayList<String> curveJobNames = new ArrayList<String>();
			if (stageOut)
				curveStageOutPostScript = createLogShellScript("curve_stage", STATUS_CURVE_RETRIEVED + this.calcParams.getSitesPerJob());
			for (String region : regionNames) {
				String thisJobName = jobName + num;
				curveJobNames.add(thisJobName);
				str.append("Job " + thisJobName + " " + "Job_" + region + ".sub" + "\n");
				str.append("Script PRE " + thisJobName + " " + curvePreScript + "\n");
				String jobOut = "";
				if (isGridUniverse)
					jobOut = submitHost.getPath() + "/" + job.getJobID() + "/out/Job_" + region + ".out";
				str.append("Script POST " + thisJobName + " " + curvePostScript + " " + jobOut + "\n");
				str.append("RETRY " + thisJobName + " " + NUM_JOB_RETRIES + "\n");

				if (stageOut) {
					String thisTarName = tarJobName + thisJobName;
					String thisUntarName = untarJobName + thisJobName;
					str.append("Job " + thisTarName + " " + submitHost.getPath() + "/" + job.getJobID() + "/" + tgzSubDir + "/Tar_" + region + ".sub" + "\n");
					String tarOut = "";
					if (isGridUniverse)
						tarOut = submitHost.getPath() + "/" + job.getJobID() + "/" + tgzSubDir + "/out/" + region + ".out";
					str.append("Script POST " + thisTarName + " " + submitHost.getPath() + "/" + job.getJobID() + "/" + stageOutScriptDir + "/StageOut_" + region + ".sh" + " " + tarOut + "\n");
					str.append("RETRY " + thisTarName + " " + NUM_JOB_RETRIES + "\n");
					str.append("Job " + thisUntarName + " " + submitHost.getPath() + "/" + job.getJobID() + "/" + tgzUnzipDir + "/UnTar_" + region + ".sub" + "\n");
					String unTarOut = submitHost.getPath() + "/" + job.getJobID() + "/" + tgzUnzipDir + "/out/" + region + ".out";
					str.append("Script POST " + thisUntarName + " " + curveStageOutPostScript + " " + unTarOut + "\n");
					str.append("RETRY " + thisUntarName + " " + NUM_JOB_RETRIES + "\n");
				}
				num++;
				str.append("\n");
			}
			
			str.append("### PARENT CHILD RELATIONSHIPS ###\n");
			str.append("\n");

			// parent child relationship
			
			str.append("# This states that the transfers should only happen after the directory is created\n");
			str.append("PARENT ");
			str.append("create_dir ");
			str.append("CHILD ");
			str.append("transfer_input_files" + "\n");
			str.append("\n");
			
			if (stageOut) {
				str.append("# This makes sure that the storage dir is created\n");
				str.append("PARENT ");
				str.append("create_storage_dir ");
				str.append("CHILD ");
				str.append("transfer_input_files" + "\n");
				str.append("\n");
			}
			
			if (onHPC || stageOut) {
				str.append("# This sends the pre processing e-mail\n");
				str.append("PARENT ");
				str.append("transfer_input_files ");
				str.append("CHILD ");
				str.append("preProcess" + "\n");
				str.append("\n");
			}
			
			str.append("# This states that the test job should happen once everything has been transfered\n");
			str.append("PARENT ");
			str.append("transfer_input_files ");
			str.append("CHILD ");
			str.append("test" + "\n");
			str.append("\n");

			str.append("# These are the parent/child relationships that make all hazard curve jobs execute in\n");
			str.append("# parallel after the test job executes to completion without error\n");
			for (String curveJobName : curveJobNames) {
				str.append("PARENT ");
				str.append("test ");
				str.append("CHILD ");
				str.append(curveJobName + "\n");
			}

			str.append("\n");
			str.append("# These are the parent/child relationships that make the chmod job run only once all\n");
			str.append("# hazard curve jobs have completed and data stage out (if applicable) has completed\n");
			for (String curveJobName : curveJobNames) {
				if (stageOut) {
					String thisTarName = tarJobName + curveJobName;
					String thisUntarName = untarJobName + curveJobName;
					str.append("PARENT ");
					str.append(curveJobName + " ");
					str.append("CHILD ");
					str.append(thisTarName + "\n");

					str.append("PARENT ");
					str.append(thisTarName + " ");
					str.append("CHILD ");
					str.append(thisUntarName + "\n");

					str.append("PARENT ");
					str.append(thisUntarName + " ");
					str.append("CHILD ");
					str.append("chmod" + "\n");
				} else {
					str.append("PARENT ");
					str.append(curveJobName + " ");
					str.append("CHILD ");
					str.append("chmod" + "\n");
				}
			}

			if (onHPC && gravityLink) { // set up gravity for automatic plotting
				str.append("\n");
				str.append("# chmod job should be run before the files are linked to from gravity\n");
				str.append("PARENT ");
				str.append("chmod ");
				str.append("CHILD ");
				str.append("copy_link" + "\n");

				str.append("\n");
				str.append("# Once everything is done, run the post process job to e-mail the user\n");
				str.append("PARENT ");
				str.append("copy_link ");
				str.append("CHILD ");
				str.append("postProcess" + "\n");
			}

			if (onHPC || stageOut) {
				str.append("\n");
				str.append("# Once everything is done, run the post process job to e-mail the user\n");
				str.append("PARENT ");
				str.append("chmod ");
				str.append("CHILD ");
				str.append("postProcess" + "\n");
			}
			
			if (APPEND_DOT_COMMAND) {
				str.append("\n");
				str.append("# This will create a file that can be used to visualize the DAG\n");
				str.append("DOT dag.dot");
				if (DOT_UPDATE) {
					str.append(" UPDATE");
				}
				str.append("\n");
			}

			fos.write(str.toString().getBytes());
			fos.close();
		} catch (Exception e) {
			System.out.println (e);
		}		
	}	

	public void createJarTransferJobFile () {
		String jobFilePrefix = "test";
		String jobName = "transfer_input_files";

		try {
			FileWriter fr = new FileWriter(outputDir + jobName+".sub");
			fr.write ("\n\n");
			fr.write("environment = " + submitHost.getTransferEnvironment() + "\n");
			fr.write("arguments = " + submitHost.getTransferArguments() + "\n");
			fr.write("copy_to_spool = false" + "\n");
			fr.write("error = " + jobName + ".err" + "\n");
			fr.write("executable = " + submitHost.getTransferExecutable() + "\n");

			fr.write("input = " + jobFilePrefix + ".in" + "\n");
			fr.write("log = " + jobFilePrefix + ".log" + "\n");
			fr.write("output = " + jobName + ".out" + "\n");

			fr.write ("periodic_release = (NumSystemHolds <= 3)" + "\n");
			fr.write ("periodic_remove = (NumSystemHolds > 3)" + "\n");			
			fr.write("remote_initialdir = " + rp.getStoragePath() + "/" + job.getJobID() + "\n");

			fr.write("notification = NEVER" + "\n");
			fr.write("transfer_error = true" + "\n");
			fr.write("transfer_executable = false" + "\n");
			fr.write("transfer_output = true" + "\n");
			fr.write("universe = scheduler" + "\n");
			fr.write("queue" + "\n\n");
			fr.close();	
		} catch (Exception e) {
			System.out.println (e);
		}			
	}

	public int getNumberOfJobs () {
		return regionNames.size();
	}

	String tgzInDir = "tgz_in";
	String tgzSubDir = "tgz_sub";
	String stageOutScriptDir = "stage_out_sh";
	String tgzUnzipDir = "tgz_un";

	ArrayList<String> tarInFiles = new ArrayList<String>();

	boolean firstStageOut = true;
	
	public static int getTarWallTime(int sitesPerJob) {
		double wt = (double)sitesPerJob * TAR_WALL_TIME_PER_CURVE + 2d;
		
		int wtInt = (int)(wt + 0.5);
		
		if (wtInt < TAR_WALL_TIME_MIN)
			return TAR_WALL_TIME_MIN;
		return wtInt;
	}

	public String createStageOutZipJobFile(String regionName, ArrayList<String> outFiles) {

		String tarFileName = "tgz/" + regionName + ".tgz";

		String tarInputName = tgzInDir + "/Tar_" + regionName + ".in";
		String tarScriptName = tgzSubDir + "/Tar_" + regionName + ".sub";

		File tgz_in = new File(outputDir + "/" + tgzInDir);

		if (!tgz_in.exists()) {
			tgz_in.mkdir();

			File tgz_sub = new File(outputDir + "/" + tgzSubDir);
			tgz_sub.mkdir();

			File tgz_sub_out = new File(outputDir + "/" + tgzSubDir + "/out");
			tgz_sub_out.mkdir();

			File tgz_sub_log = new File(outputDir + "/" + tgzSubDir + "/log");
			tgz_sub_log.mkdir();

			File tgz_sub_err = new File(outputDir + "/" + tgzSubDir + "/err");
			tgz_sub_err.mkdir();
		}

		try {
			FileWriter fw = new FileWriter(outputDir + "/" + tarInputName);
			for (String file : outFiles)
				fw.write(file + "\n");
			fw.close();

			FileWriter fr = new FileWriter(outputDir + "/" + tarScriptName);
			
			String progExec = "/bin/tar";
			String progArgs = "-czv --files-from " + tarInputName + " --file " + tarFileName;
			String executable = "";
			String arguments = "";
			if (rp.isGridUniverse()) {
				executable = "/bin/sh";
				arguments = this.rpWrapperScript + " " + progExec + " " + progArgs;
			} else {
				executable = progExec;
				arguments = progArgs;
			}

			fr.write("universe = " + rp.getUniverse() + "\n");
			String requirements = rp.getRequirements();
			if (requirements.length() > 0)
				fr.write("requirements = " + requirements + "\n");
			fr.write("should_transfer_files = yes" + "\n");
			fr.write("WhenToTransferOutput = ON_EXIT" + "\n");
			fr.write("executable = " + executable + "\n");
			fr.write("arguments = " + arguments + "\n");
			fr.write("notification = NEVER" + "\n");
			if (rp.isGridUniverse()) {
				fr.write("globusrsl = (jobtype=single)(maxwalltime=" + getTarWallTime(job.getCalcParams().getSitesPerJob()) + ")" + "\n");
				fr.write("globusscheduler = " + rp.getHostName() + "/" + rp.getBatchScheduler() + "\n");
			}
			fr.write("copy_to_spool = false" + "\n");
			fr.write("error = " + outputDir + "/" + tgzSubDir + "/err/" + regionName + ".err" + "\n");
			fr.write("log = " + outputDir + "/" + tgzSubDir + "/log/" + regionName + ".log" + "\n");
			fr.write("output = " + outputDir + "/" + tgzSubDir + "/out/" + regionName + ".out" + "\n");
			fr.write("transfer_executable = false" + "\n");
			fr.write("transfer_error = true" + "\n");
			fr.write("transfer_output = true" + "\n");
			fr.write("periodic_release = (NumSystemHolds <= 3)" + "\n");
			fr.write("periodic_remove = (NumSystemHolds > 3)" + "\n");
			fr.write("remote_initialdir = " + rp.getStoragePath() + "/" + job.getJobID() + "\n");
			fr.write("queue" + "\n");
			fr.write("" + "\n");

			fr.flush();
			fr.close();

			tarInFiles.add(tarInputName);

			// now make the submit file
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

		return tarFileName;
	}

	public void createStageOutPostJobFiles(String regionName, String tarFileName) {

		File stageOutDir = new File(outputDir + "/" + stageOutScriptDir);

		if (!stageOutDir.exists()) {
			stageOutDir.mkdir();

			File tgz_sub = new File(outputDir + "/" + tgzUnzipDir);
			tgz_sub.mkdir();

			File tgz_sub_out = new File(outputDir + "/" + tgzUnzipDir + "/out");
			tgz_sub_out.mkdir();

			File tgz_sub_log = new File(outputDir + "/" + tgzUnzipDir + "/log");
			tgz_sub_log.mkdir();

			File tgz_sub_err = new File(outputDir + "/" + tgzUnzipDir + "/err");
			tgz_sub_err.mkdir();
		}

		// make the transfer script file

		String stageOutFile = outputDir + "/" + stageOutScriptDir + "/StageOut_" + regionName + ".sh";

		String source = rp.getGridFTPHost() + rp.getStoragePath() + "/" + job.getJobID() + "/" + tarFileName;
		String destFilePath = storageHost.getPath() + "/" + job.getJobID() + "/" + tarFileName;
		String dest = storageHost.getGridFTPHostName() + destFilePath;

		int streams = 1;

		try {
			FileWriter fw = new FileWriter(stageOutFile);

			fw.write("#!/bin/sh" + "\n");
			fw.write("" + "\n");
			addFirstArgRetValCheck(fw);
			fw.write("globus-url-copy -vb -tcp-bs 2097152 -p " + streams + " gsiftp://" + source + " gsiftp://" + dest + "\n");

			if (firstStageOut) {
				source = rp.getGridFTPHost() + rp.getStoragePath() + "/" + job.getJobID() + "/" + job.getConfigFileName();
				dest = storageHost.getGridFTPHostName() + storageHost.getPath() + "/" + job.getJobID() + "/" + job.getConfigFileName();
				fw.write("globus-url-copy -vb -tcp-bs 2097152 -p " + streams + " gsiftp://" + source + " gsiftp://" + dest + "\n");
				firstStageOut = false;
			}

			fw.close();

			// now make the untar job

			String unTarScriptName = tgzUnzipDir + "/UnTar_" + regionName + ".sub";

			FileWriter fr = new FileWriter(outputDir + "/" + unTarScriptName);

			String executable = "/bin/sh";
			String arguments = this.storageWrapperScript + " /bin/tar -xzvf " + destFilePath;

			fr.write("universe = grid" + "\n");
			fr.write("executable = " + executable + "\n");
			fr.write("arguments = " + arguments + "\n");
			fr.write("notification = NEVER" + "\n");
			fr.write("globusrsl = (jobtype=single)(maxwalltime=" + getTarWallTime(job.getCalcParams().getSitesPerJob()) + ")" + "\n");
			fr.write("globusscheduler = " + storageHost.getSchedulerHostName() + "/" + storageHost.getBatchScheduler() + "\n");
			fr.write("copy_to_spool = false" + "\n");
			fr.write("error = " + outputDir + "/" + tgzUnzipDir + "/err/" + regionName + ".err" + "\n");
			fr.write("log = " + outputDir + "/" + tgzUnzipDir + "/log/" + regionName + ".log" + "\n");
			fr.write("output = " + outputDir + "/" + tgzUnzipDir + "/out/" + regionName + ".out" + "\n");
			fr.write("transfer_executable = false" + "\n");
			fr.write("transfer_error = true" + "\n");
			fr.write("transfer_output = true" + "\n");
			fr.write("periodic_release = (NumSystemHolds <= 3)" + "\n");
			fr.write("periodic_remove = (NumSystemHolds > 3)" + "\n");
			fr.write("remote_initialdir = " + storageHost.getPath() + "/" + job.getJobID() + "\n");
			fr.write("queue" + "\n");
			fr.write("" + "\n");

			fr.flush();
			fr.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public void setStageOut(boolean stageOut) {
		this.stageOut = stageOut;
	}

	// creates a shell script that will submit the DAG
	public void createSubmitDAGScript(boolean run) {
		try {
			String scriptFileName = submitHost.getPath() + "/" + job.getJobID() + "/submit_DAG.sh";
			FileWriter fw = new FileWriter(scriptFileName);
			fw.write("#!/bin/bash\n");
			fw.write("" + "\n");
			fw.write("if [ -f ~/.bash_profile ]; then" + "\n");
			fw.write("\t. ~/.bash_profile" + "\n");
			fw.write("fi" + "\n");
			fw.write("" + "\n");
			fw.write("cd "+outputDir+"\n");
			// make the stage out transfer scripts executable
			if (stageOut) {
				fw.write("/bin/chmod -R +x " + outputDir + "/" + stageOutScriptDir + "\n");
			}
			// make the log scripts executable
			fw.write("/bin/chmod +x " + outputDir + LOG_SCRIPT_DIR_NAME + "/" + "*.sh" + "\n");
			// make the return value checker script executable
			fw.write("/bin/chmod +x " + retValScript + "\n");
			// let the command wrapper script executable
			fw.write("/bin/chmod +x " + wrapperScript + "\n");
			// make this submit script executable for easy manual resubmits later
			fw.write("/bin/chmod +x " + scriptFileName + "\n");
			fw.write("\n");
			String binPath = this.submitHost.getCondorPath();
			if (!binPath.endsWith(File.separator))
				binPath += File.separator;
			String dagArgs = "-maxidle " + DAGMAN_MAX_IDLE + " -MaxPre " + DAGMAN_MAX_PRE + 
							" -MaxPost " + DAGMAN_MAX_POST + 
							" -OldRescue 0 -AutoRescue 1";
			fw.write(binPath + "condor_submit_dag " + dagArgs + " main.dag" + "\n");
			fw.close();
			if (run) {
				this.logMessage(STATUS_SUBMIT_DAG);
				String outFile = this.logDir + this.logFileName + ".subout";
				String errFile = this.logDir + this.logFileName + ".suberr";
				int retVal = RunScript.runScript(new String[]{"sh", "-c", "sh "+scriptFileName}, outFile, errFile);
				if (retVal == 0)
					this.logMessage(STATUS_SUBMIT_DAG_SUCCESS);
				else
					this.logMessage(STATUS_SUBMIT_DAG_FAIL + ": " + retVal);
				System.out.println("Command executed with status " + retVal);
			}
		}
		catch (Exception e) {
			e.printStackTrace();
		}
	}

	public void logStart() {
		try {
			writeToLogFile(logDir + logFileName, LOG_COMMENT_NAME_PREFIX + job.getJobName());
			writeToLogFile(logDir + logFileName, LOG_COMMENT_ID_PREFIX + job.getJobID());
			this.logMessage(STATUS_CREATE_BEGIN);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public void logCompletion() {
		try {
			this.logMessage(STATUS_CREATE_END);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	public void setLogDirectory(String logDir) {
		if (logDir.length() > 0 && !logDir.endsWith(File.separator))
			logDir += File.separator;
		System.out.println("Log directory: " + logDir);
		this.logDir = logDir;
	}
	
	public static void writeToLogFile(String logFileName, String message) throws IOException {
		File logFile = new File(logFileName);
		if (!logFile.exists())
			logFile.createNewFile();
		FileOutputStream stream = new FileOutputStream(logFile, true);
		message += "\n";
		stream.write(message.getBytes());
		stream.flush();
		stream.close();
	}
	
	public static void logMessage(String logFileName, String message) throws IOException {
		message = "[" + getCurrentDateString() + "] " + message;
		writeToLogFile(logFileName, message);
	}

	public synchronized void logMessage(String message) throws IOException {
		logMessage(logDir + logFileName, message);
	}

	private String createLogShellScript(String dagStage, String message) {
		String fileName = this.outputDir + LOG_SCRIPT_DIR_NAME + File.separator + "log_" + dagStage + ".sh";
		try {
			FileWriter fw = new FileWriter(fileName);
			
//			#!/bin/sh
//			
//			
//			echo [`date`] message >> logFile
//			
//			
//			

			fw.write("#!/bin/sh" + "\n");
			fw.write("" + "\n");
			addFirstArgRetValCheck(fw);
			fw.write("echo [`date`] " + message + " >> " + logDir + logFileName + "\n");

			fw.close();
		} catch (IOException e) {
			e.printStackTrace();
		}

		return fileName;
	}
	
	private void addFirstArgRetValCheck(FileWriter fw) throws IOException {
//		errFile=$1
//		
//		if [ $errFile ];then
//			retVal.sh $errFile
//			rv=$?
//			if [ $rv -gt 0 ];then
//				exit $rv
//			fi
//		fi
		fw.write("errFile=$1" + "\n");
		fw.write("" + "\n");
		fw.write("if [ $errFile ];then" + "\n");
		fw.write("\t" + this.outputDir + RET_VAL_SCRIPT_NAME + " $errFile" + "\n");
		fw.write("\t" + "rv=$?" + "\n");
		fw.write("\t" + "if [ $rv -gt 0 ];then" + "\n");
		fw.write("\t" + "\t" + "exit $rv" + "\n");
		fw.write("\t" + "fi" + "\n");
		fw.write("fi" + "\n");
		fw.write("" + "\n");
	}
	
	public String writeWrapperScript() {
		String fileName = this.outputDir + WRAPPER_SCRIPT_NAME;
		
		rpWrapperScript = this.rp.getStoragePath()  + "/" + this.job.getJobID() + "/" + WRAPPER_SCRIPT_NAME;
		storageWrapperScript = this.storageHost.getPath()  + "/" + this.job.getJobID() + "/" + WRAPPER_SCRIPT_NAME;
		
		try {
			FileWriter fw = new FileWriter(fileName);
			
//			#!/bin/sh
//
//			/bin/echo SHELL: $SHELL
//			/bin/echo DATE: `date`
//			/bin/echo ARCH: `uname -a`
//			com=""
//
//			for arg in $*;do
//			com="${com} ${arg}"
//			done
//
//			/bin/echo COMMAND: $com
//			/bin/echo ***RUNNING COMMAND***
//			$com
//			rv=$?
//			/bin/echo ***COMMAND TERMINATED***
//			/bin/echo RETURN_VAL: $rv
//			
//			exit $rv

			fw.write("#!/bin/sh" + "\n");
			fw.write("" + "\n");
			fw.write("umask u=rwx,g=rx,o=rx" + "\n");
			fw.write("" + "\n");
			fw.write("/bin/echo SHELL: $SHELL" + "\n");
			fw.write("/bin/echo DATE: `date`" + "\n");
			fw.write("/bin/echo ARCH: `uname -a`" + "\n");
			fw.write("com=\"\"" + "\n");
			fw.write("for arg in $*;do" + "\n");
			fw.write("\tcom=\"${com} ${arg}\"" + "\n");
			fw.write("done" + "\n");
			fw.write("" + "\n");
			fw.write("/bin/echo COMMAND: $com" + "\n");
			fw.write("/bin/echo ***RUNNING COMMAND***" + "\n");
			fw.write("$com" + "\n");
			fw.write("rv=$?" + "\n");
			fw.write("/bin/echo ***COMMAND TERMINATED***" + "\n");
			fw.write("/bin/echo RETURN_VAL: $rv" + "\n");
			fw.write("" + "\n");
			fw.write("exit $rv" + "\n");
			
			fw.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		return fileName;
	}
	
	public String writeRetValScript() {
		String fileName = this.outputDir + RET_VAL_SCRIPT_NAME;
		
		try {
			FileWriter fw = new FileWriter(fileName);
			
//			#!/bin/sh
//
//			file=$1
//			rv=3
//
//			echo "Parsing $file"
//			use=0
//
//			for val in `/bin/grep RETURN_VAL $file`;do
//				
//				if [ $use -eq 1 ];then
//					echo "Found an RV: $val"
//					rv=$val
//				fi
//				
//				echo $val | /bin/grep RETURN_VAL > /dev/null
//				grep_rv=$?
//				if [ $grep_rv -eq 0 ];then
//					echo the next one is what we want...
//					use=1
//				else
//					use=0
//				fi
//			done
//
//			/bin/echo FINAL_RETURN_VAL: $rv
//
//			exit $rv
			
			fw.write("#!/bin/sh" + "\n");
			fw.write("" + "\n");
			fw.write("file=$1" + "\n");
			fw.write("rv=3" + "\n");
			fw.write("" + "\n");
			fw.write("echo \"Parsing $file\"" + "\n");
			fw.write("use=0" + "\n");
			fw.write("" + "\n");
			fw.write("for val in `/bin/grep RETURN_VAL $file`;do" + "\n");
			fw.write("\t" + "\n");
			fw.write("\t" + "if [ $use -eq 1 ];then" + "\n");
			fw.write("\t\t" + "echo \"Found an RV: $val\"" + "\n");
			fw.write("\t\t" + "rv=$val" + "\n");
			fw.write("\t" + "fi" + "\n");
			fw.write("\t" + "" + "\n");
			fw.write("\t" + "echo $val | /bin/grep RETURN_VAL > /dev/null" + "\n");
			fw.write("\t" + "grep_rv=$?" + "\n");
			fw.write("\t" + "if [ $grep_rv -eq 0 ];then" + "\n");
			fw.write("\t\t" + "echo the next one is what we want..." + "\n");
			fw.write("\t\t" + "use=1" + "\n");
			fw.write("\t" + "else" + "\n");
			fw.write("\t\t" + "use=0" + "\n");
			fw.write("\t" + "fi" + "\n");
			fw.write("\t" + "\n");
			fw.write("" + "\n");
			fw.write("done" + "\n");
			fw.write("" + "\n");
			fw.write("/bin/echo FINAL_RETURN_VAL: $rv" + "\n");
			fw.write("" + "\n");
			fw.write("exit $rv" + "\n");
			
			fw.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		return fileName;
	}

//	public void createJarTransferToHostInputFile (String outputDir, String remoteJobDir) {
//	File dir = new File(outputDir);
//	String[] children = dir.list();

//	FilenameFilter filter = new FilenameFilter() {
//	public boolean accept(File dir, String name) {
//	return name.endsWith(".txt");
//	}
//	};
//	children = dir.list(filter);

//	ArrayList arr = new ArrayList ();
//	for (int i = 0; i < children.length; i++) {
//	arr.add(children[i]);
//	}

//	Collections.sort(arr);

//	String line = null;
//	BufferedReader fr = null;
//	BufferedWriter fw = null;
//	try {
//	for (int i = 0; i < arr.size(); i++) {
//	fw = new BufferedWriter (new FileWriter (outputDir+"/tx_jars_2HOST_"+(i+1)+".in"));
//	fr = new BufferedReader (new FileReader (outputDir+"/"+(String)arr.get(i)));
//	line = fr.readLine();line = fr.readLine();
//	while ((line = fr.readLine()) != null) {
//	fw.write("gsiftp://"+ rp.rp_host +rp.rp_storagePath + "/" + job.getJobID()+"/");
//	fw.write(line);
//	fw.write("\n");
//	fw.write("gsiftp://"+ job.repo_host + job.repo_storagePath + "/" + job.getJobID() +"/"+line);
//	fw.write("\n\n");
//	}
//	fr.close();
//	fw.close();
//	}


//	} catch (Exception e) {
//	System.out.println (e);
//	}		
//	}

//	public void createTransferOutputJobFiles (int numberOfJobs) {
//	String jobName = "tx_jars_2HOST_";
//	String exefile = "/usr/local/vds-1.4.7/bin/kickstart";
//	FileWriter fr = null;
//	String name = null;

//	try {
//	for (int i = 0; i < numberOfJobs; i++) {
//	name = jobName+(i+1);
//	fr = new FileWriter(outputDir + name+".sub");		

//	fr.write ("\n\n");
//	fr.write("environment = GLOBUS_LOCATION=/usr/local/vdt/globus;LD_LIBRARY_PATH=/usr/local/vdt/globus/lib;" + "\n");
//	fr.write("arguments = -n transfer -N VDS::transfer:1.0 -i - -R local /usr/local/vds-1.4.7/bin/transfer  -f  base-uri se-mount-point" + "\n");
//	fr.write("copy_to_spool = false" + "\n");
//	fr.write("error = " + name + ".err" + "\n");
//	fr.write("executable = " + exefile + "\n");
//	fr.write("globusrsl ="+ rp.rp_globusrsl +"\n");
//	fr.write ("globusscheduler = "+rp.rp_host+"/"+rp.rp_getBatchScheduler()+"\n");		
//	fr.write("input = " + name + ".in" + "\n");
//	fr.write("log = " + name + ".log" + "\n");
//	fr.write("output = " + name + ".out" + "\n");

//	fr.write ("periodic_release = (NumSystemHolds <= 3)" + "\n");
//	fr.write ("periodic_remove = (NumSystemHolds > 3)" + "\n");			
//	fr.write("remote_initialdir = " + job.repo_storagePath + "/" + job.getJobID() + "\n");

//	fr.write("transfer_error = true" + "\n");
//	fr.write("transfer_executable = false" + "\n");
//	fr.write("transfer_output = true" + "\n");
//	fr.write("universe = globus" + "\n");
//	fr.write("queue" + "\n\n");
//	fr.close();
//	}
//	} catch (Exception e) {
//	System.out.println (e);
//	}		
//	}

//	public void createUniqueDirOnRemote (String dirName) {
//	String jobName = "HPC_cdir";
//	try {
//	FileWriter fr = new FileWriter(outputDir + jobName+".sub");
//	fr.write ("\n\n");
//	fr.write("environment = GLOBUS_LOCATION=/usr/local/vdt/globus;LD_LIBRARY_PATH=/usr/local/vdt/globus/lib;\n");
//	fr.write ("arguments = -n dirmanager -N Pegasus::dirmanager:1.0 -R hpc /auto/rcf-104/dpmeyers/proj/pegasus-2.0.0RC1/bin/dirmanager");
//	fr.write (" --create --dir "+dirName+"\n");
//	fr.write("copy_to_spool = false\n");
//	fr.write ("error = "+jobName+".err\n");
//	fr.write("executable = /auto/rcf-104/dpmeyers/proj/vds-1.4.7/bin/kickstart\n");
//	fr.write("globusrsl = (jobtype=single)\n");
//	fr.write ("globusscheduler = "+rp.getHostName()+"/" + rp.getForkScheduler() + "\n");
//	fr.write ("log = "+jobName+".log\n");
//	fr.write ("output = "+jobName+".out\n");			
//	fr.write("periodic_release = (NumSystemHolds <= 3)\n");
//	fr.write("periodic_remove = (NumSystemHolds > 3)\n");
//	fr.write("remote_initialdir = " + rp.getStoragePath() + "/" + job.getJobID() + "\n");
//	fr.write("transfer_error = true\n");
//	fr.write("transfer_executable = false\n");
//	fr.write("transfer_output = true\n");
//	fr.write("universe = globus\n");
//	fr.write("queue\n");
//	fr.close();
//	} catch (Exception e) {
//	System.out.println (e);
//	}		
//	}	

	/**
	 * Creates condor submit jobs and DAG from the given xml file (first argument).
	 * 
	 * The 2nd optional argument is a boolean that, if true, will not actually create
	 * CVM files but assume that they are already created in the job directory (or will
	 * be moved there after the job creation is completed)
	 * 
	 * The 3rd optional argument is a boolean that, if true, treats this as a
	 * restart of a failed run.It will check to see if any of the jobs failed, and create
	 * submission files in jobName_restart
	 * 
	 * @param args - XML_File.xml [skipCVMfiles] [restart]
	 */
	public static void main(String args[]) {

//		String outputDir = "";
//		if (args.length == 0) {
//		System.err.println("RUNNING FROM DEBUG MODE!");
//		args = new String[5];
//		args[0] = "scratchJavaDevelopers/kevin/job_example.xml";
//		args[0] = "output.xml";
//		args[0] = "/home/kevin/OpenSHA/condor/jobs/abe_output.xml";
//		args[1] = "false"; //don't skip cvm
//		args[2] = "false"; //don't restart
//		args[3] = "1209900";
//		args[4] = "16132000";
//		outputDir = "/home/kevin/OpenSHA/condor/jobs/";
//		}

//		try {
//		String metadata = args[0];
//		SAXReader reader = new SAXReader();
//		Document document = reader.read(new File(metadata));
//		Element root = document.getRootElement();

//		Element jobElem = root.element(HazardMapJob.XML_METADATA_NAME);

//		HazardMapJob job = HazardMapJob.fromXMLMetadata(jobElem);

//		System.out.println("rp_host = " + rp.rp_host);
//		System.out.println("rp_storagePath = " + rp.rp_storagePath + "/" + job.getJobID());
//		System.out.println("rp_javaPath = " + rp.rp_javaPath);
//		System.out.println("rp_getBatchScheduler() = " + rp.rp_getBatchScheduler());
//		System.out.println("repo_host = " + job.repo_host);
//		System.out.println("repo_storagePath = " + job.repo_storagePath + "/" + job.getJobID());
//		System.out.println("sitesPerJob = " + calcParams.getSitesPerJob());
//		System.out.println("useCVM = " + job.useCVM);
//		System.out.println("submitHost = " + job.submit.submitHost);
//		System.out.println("submitHostPath = " + job.submit.submitHostPath+"/"+job.getJobID());
//		System.out.println("submitHostPathToDependencies = " + job.submit.submitHostPathToDependencies);

//		boolean restart = false;
//		boolean skipCVMFiles = false;

//		if (args.length >= 2) {
//		skipCVMFiles = Boolean.parseBoolean(args[1]);
//		if (skipCVMFiles)
//		System.out.println("Skipping CVM File Creation!");
//		}

//		if (args.length >= 3) {
//		restart = Boolean.parseBoolean(args[2]);
//		if (restart) {
//		System.out.println("Restarting an old run!");
//		}
//		}

//		if (outputDir.length() == 0) { // we're not debugging
//		outputDir = job.submit.submitHostPath;
//		}

//		if (!outputDir.endsWith("/"))
//		outputDir = outputDir + "/";

//		boolean partial = false;
//		int startIndex = 0;
//		int endIndex = 0;

//		if (args.length >= 5) { // partial DAG
//		startIndex = Integer.parseInt(args[3]);
//		endIndex = Integer.parseInt(args[4]);

//		String suffix = "_" + HazardMapJobCreator.addLeadingZeros(startIndex, HazardMapJobCreator.nameLength)
//		+ "_" + HazardMapJobCreator.addLeadingZeros(endIndex, HazardMapJobCreator.nameLength);

//		job.getJobID() = job.getJobID() + suffix;

//		while (rp.rp_storagePath.endsWith("/")) {
//		int end = rp.rp_storagePath.length() - 2;
//		rp.rp_storagePath = rp.rp_storagePath.substring(0, end);
//		}

//		rp.rp_storagePath = rp.rp_storagePath + suffix;

//		job.getConfigFileName() = job.getJobID() + ".xml";

//		jobElem.detach();
//		root = job.toXMLMetadata(root);

//		partial = true;
//		}

//		outputDir = outputDir + job.getJobID();

//		String originalDir = "";

//		if (restart) {
//		originalDir = outputDir + "/";
//		outputDir = outputDir + "_RESTART/";
//		} else
//		outputDir = outputDir + "/";

////		String outputDir = "/home/kevin/OpenSHA/condor/jobs/benchmark_RELM_UCERF_0.1_Purdue/";
//		// SDSC
////		String remoteJobDir = "/gpfs/projects/scec/CyberShake2007/opensha/kevin/meetingMap";
//		// HPC
////		String remoteJobDir = "/auto/scec-00/kmilner/hazMaps/benchmark_RELM_UCERF_0.1";
//		// Dynamic
////		String remoteJobDir = "/nfs/dynamic-1/opensha/kmilner/verification_0.02";
//		// ORNL
////		String remoteJobDir = "/tmp/benchmark_RELM_UCERF_0.1";

//		File outputDirFile = new File(outputDir);
//		if (!outputDirFile.exists())
//		outputDirFile.mkdir();

//		File outFile = new File(outputDir + "out/");
//		if (!outFile.exists())
//		outFile.mkdir();
//		File errFile = new File(outputDir + "err/");
//		if (!errFile.exists())
//		errFile.mkdir();
//		File logFile = new File(outputDir + "log/");
//		if (!logFile.exists())
//		logFile.mkdir();

//		// load the region
//		Element regionElement = root.element(GriddedRegion.XML_METADATA_NAME);
//		GriddedRegion region = GriddedRegion.fromXMLMetadata(regionElement);
//		SitesInGriddedRegionAPI sites = new SitesInGriddedRegion(region.getRegionOutline(), region.getGridSpacing());

//		// see if the ERF needs to be created and saved

//		if (job.saveERF) {
//		Element erfElement = root.element(EqkRupForecast.XML_METADATA_NAME);
////		erfElement.setName("ERF_OLD");
//		root.add(erfElement.createCopy("ERF_REF"));
//		erfElement.detach();
//		System.out.println("Creating ERF...");
//		EqkRupForecast erf = EqkRupForecast.fromXMLMetadata(erfElement);
//		System.out.println("Updating Forecast...");
//		erf.updateForecast();
//		String erfFileName = job.getJobID() + "_ERF.obj";
//		System.out.println("Saving ERF to " + erfFileName + "...");
//		FileUtils.saveObjectInFileThrow(outputDir + erfFileName, erf);
//		Element newERFElement = root.addElement(EqkRupForecast.XML_METADATA_NAME);
//		newERFElement.addAttribute("fileName", erfFileName);
//		System.out.println("Done with ERF");
//		}

//		OutputFormat format = OutputFormat.createPrettyPrint();
//		XMLWriter writer = new XMLWriter(new FileWriter(outputDir + job.getConfigFileName()), format);
//		writer.write(document);
//		writer.close();

//		HazardMapJobCreator creator;
//		if (partial)
//		creator = new HazardMapJobCreator(outputDir, sites, startIndex, endIndex, job);
//		else
//		creator = new HazardMapJobCreator(outputDir, sites, job);


//		creator.skipCVMFiles = skipCVMFiles;

//		try {
//		if (restart)
//		creator.createRestartJobs(originalDir);
//		else
//		creator.createJobs();
//		creator.createSubmitScripts(24);

//		// Mahesh code

//		String remoteJobDir = rp.rp_storagePath;
//		/*				
//		DateFormat myformat = new SimpleDateFormat("MM_dd_yyyy_HH_mm_ss");  
//		StringBuffer buf = new StringBuffer ();
//		buf.append(remoteJobDir+"/");
//		buf.append(myformat.format(new Date()));
//		remoteJobDir = new String (buf);
//		System.out.println(remoteJobDir);				
//		*/				
//		creator.createMakeDirJob();
//		creator.createTestJob();
////		creator.createUniqueDirOnRemote (remoteJobDir);
//		creator.createCHModJob();
//		creator.createCopyLinkJob();
//		creator.createPostJob();
////		creator.createJarTransferToHostInputFile(outputDir, remoteJobDir);
//		creator.createDAG (outputDir, creator.getNumberOfJobs());
//		creator.createJarTransferJobFile();
//		creator.createJarTransferInputFile(outputDir, remoteJobDir);
////		creator.createTransferOutputJobFiles (creator.getNumberOfJobs());
//		// Mahesh code

//		} catch (IOException e) {
//		// TODO Auto-generated catch block
//		e.printStackTrace();
//		}
//		} catch (MalformedURLException e2) {
//		// TODO Auto-generated catch block
//		e2.printStackTrace();
//		} catch (DocumentException e2) {
//		// TODO Auto-generated catch block
//		e2.printStackTrace();
//		} catch (InvocationTargetException e) {
//		// TODO Auto-generated catch block
//		e.printStackTrace();
//		} catch (IOException e) {
//		// TODO Auto-generated catch block
//		e.printStackTrace();
//		}
	}
}
