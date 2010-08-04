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

package org.opensha.commons.gridComputing;

import java.util.ArrayList;
import java.util.List;

import org.dom4j.Element;

public class ResourceProvider extends GridResource {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	public static final String XML_METADATA_NAME = "ResourceProvider";
	
	/**
	 * Preset for running on HPC as tara3d
	 * @return
	 */
	public static final ResourceProvider HPC() {
		GlobusRSL rsl = new GlobusRSL(GlobusRSL.SINGLE_JOB_TYPE, 240);
//		rsl.setQueue("scec");
		ResourceProvider HPC = new ResourceProvider("HPC (USC)", "hpc.usc.edu", "jobmanager-pbs", "jobmanager-fork",
				"/usr/bin/java", "/home/scec-00/tera3d/opensha/hazmaps",
				"", "hpc.usc.edu", "grid", rsl);
		HPC.addSuggestedQueue("main");
		HPC.addSuggestedQueue("scec");
		HPC.addSuggestedQueue("quick");
		return HPC;
	}
	
	public static final ResourceProvider HPC_SCEC_QUEUE() {
		ResourceProvider hpc = HPC();
		hpc.setName("HPC (USC - SCEC queue)");
		hpc.getGlobusRSL().setQueue("scec");
		return hpc;
	}
	
	private static String ABE_HOST = "grid-abe.ncsa.teragrid.org";
	private static String ABE_BATCH = "jobmanager-pbs";
	private static String ABE_FORK = "jobmanager-fork";
	private static String ABE_JAVA = "/usr/local/jdk1.5.0_12/bin/java";
	private static String ABE_DIR = "/cfs/scratch/users/tera3d/opensha/hazMapRuns";
	private static String ABE_REQS = "(FileSystemDomain==\"abe-tera3d\")&&(Arch==\"X86_64\")&&(Disk!=0)&&(Memory!=0)&&(OpSys==\"LINUX\")";
	private static String ABE_GRID_FTP = "gridftp-abe.ncsa.teragrid.org:2811";
	
	/**
	 * Preset for running on ABE with Glide-Ins as tera3d
	 * @return
	 */
	public static final ResourceProvider ABE_GLIDE_INS() {
		GlobusRSL rsl = new GlobusRSL(GlobusRSL.SINGLE_JOB_TYPE, 240);
		ResourceProvider ABE_GLIDE_INS = new ResourceProvider("Abe (NCSA) (w/ Glide-Ins)", ABE_HOST, ABE_BATCH, ABE_FORK,
				ABE_JAVA, ABE_DIR, ABE_REQS, ABE_GRID_FTP, "vanilla", rsl);
		return ABE_GLIDE_INS;
	}
	
	/**
	 * Preset for running on ABE without Glide-Ins as tera3d
	 * @return
	 */
	public static final ResourceProvider ABE_NO_GLIDE_INS() {
		GlobusRSL rsl = new GlobusRSL(GlobusRSL.SINGLE_JOB_TYPE, 240);
		ResourceProvider ABE_NO_GLIDE_INS = new ResourceProvider("Abe (NCSA) (w/o Glide-Ins)", ABE_HOST, ABE_BATCH, ABE_FORK,
				ABE_JAVA, ABE_DIR, ABE_REQS, ABE_GRID_FTP, "grid", rsl);
		return ABE_NO_GLIDE_INS;
	}
	
	/**
	 * Preset for running on Dynamic as kmilner
	 * @return
	 */
	public static final ResourceProvider DYNAMIC() {
		GlobusRSL rsl = new GlobusRSL(GlobusRSL.SINGLE_JOB_TYPE, 240);
		rsl.setQueue("mpi");
		ResourceProvider DYNAMIC = new ResourceProvider("Dynamic (USC/SCEC)", "dynamic.usc.edu", "jobmanager-pbs", "jobmanager-fork",
				"/usr/java/jdk1.5.0_10/bin/java", "/nfs/dynamic-1/tera3d/opensha/hazMaps",
				"", "dynamic.usc.edu", "grid", rsl);
		DYNAMIC.addSuggestedQueue("mpi");
		return DYNAMIC;
	}
	
	/**
	 * Preset for running on ORNL as kmilner
	 * @return
	 */
	public static final ResourceProvider ORNL() {
		GlobusRSL rsl = new GlobusRSL(GlobusRSL.SINGLE_JOB_TYPE, 240);
		ResourceProvider ORNL = new ResourceProvider("Oak Ridge National Labs", "tg-login.ornl.teragrid.org:2119", "jobmanager-pbs", "jobmanager-fork",
				"/usr/bin/java", "/scratch/kevinm/hazMaps",
				"", "tg-gridftp.ornl.teragrid.org:2811", "grid", rsl);
		return ORNL;
	}
	
//	private static String LEAR_HOST = "tg-gatekeeper.purdue.teragrid.org";
//	private static String LEAR_BATCH = "jobmanager-pbs";
//	private static String LEAR_FORK = "jobmanager-fork";
//	private static String LEAR_JAVA = "/opt/jdk1.6.0/bin/java";
//	private static String LEAR_DIR = "/usr/rmt_share/scratch96/k/kevinm/hazMaps";
//	private static String LEAR_REQS = "(FileSystemDomain==\"purdue.teragrid.org\")&&(Arch==\"X86_64\")&&(Disk>=0)&&(Memory>=0)&&(OpSys==\"LINUX\")";
//	private static String LEAR_GRID_FTP = "tg-data.purdue.teragrid.org";
//	
//	/**
//	 * Preset for running on LEAR with Glide-Ins as kmilner
//	 * @return
//	 */
//	public static final ResourceProvider LEAR_GLIDE_INS() {
//		GlobusRSL rsl = new GlobusRSL(GlobusRSL.SINGLE_JOB_TYPE, 240);
//		ResourceProvider LEAR_GLIDE_INS = new ResourceProvider("Lear (Purdue) (w/ Glide-Ins)", LEAR_HOST, LEAR_BATCH, LEAR_FORK,
//				LEAR_JAVA, LEAR_DIR, LEAR_REQS, LEAR_GRID_FTP, "vanilla", rsl);
//		return LEAR_GLIDE_INS;
//	}
//	
//	/**
//	 * Preset for running on LEAR without Glide-Ins as kmilner
//	 * @return
//	 */
//	public static final ResourceProvider LEAR_NO_GLIDE_INS() {
//		GlobusRSL rsl = new GlobusRSL(GlobusRSL.SINGLE_JOB_TYPE, 240);
//		ResourceProvider LEAR_NO_GLIDE_INS = new ResourceProvider("Lear (Purdue) (w/o Glide-Ins)", LEAR_HOST, LEAR_BATCH, LEAR_FORK,
//				LEAR_JAVA, LEAR_DIR, LEAR_REQS, LEAR_GRID_FTP, "globus", rsl);
//		return LEAR_NO_GLIDE_INS;
//	}
	
	private static String STEELE_HOST = "tg-steele.purdue.teragrid.org";
	private static String STEELE_BATCH = "jobmanager-pbs";
	private static String STEELE_FORK = "jobmanager-fork";
	private static String STEELE_JAVA = "/apps/steele/jdk1.6.0_05/bin/java";
	private static String STEELE_DIR = "/usr/rmt_share/scratch96/k/kevinm/hazMaps";
	private static String STEELE_REQS = "(FileSystemDomain==\"purdue.teragrid.org\")&&(Arch==\"X86_64\")&&(Disk>=0)&&(Memory>=0)&&(OpSys==\"LINUX\")";
	private static String STEELE_GRID_FTP = "tg-data.purdue.teragrid.org";
	
	/**
	 * Preset for running on STEELE with Glide-Ins as kmilner
	 * @return
	 */
	public static final ResourceProvider STEELE_GLIDE_INS() {
		GlobusRSL rsl = new GlobusRSL(GlobusRSL.SINGLE_JOB_TYPE, 240);
		ResourceProvider STEELE_GLIDE_INS = new ResourceProvider("Steele (Purdue) (w/ Glide-Ins)", STEELE_HOST, STEELE_BATCH, STEELE_FORK,
				STEELE_JAVA, STEELE_DIR, STEELE_REQS, STEELE_GRID_FTP, "vanilla", rsl);
		return STEELE_GLIDE_INS;
	}
	
	/**
	 * Preset for running on STEELE without Glide-Ins as kmilner
	 * @return
	 */
	public static final ResourceProvider STEELE_NO_GLIDE_INS() {
		GlobusRSL rsl = new GlobusRSL(GlobusRSL.SINGLE_JOB_TYPE, 240);
		ResourceProvider STEELE_NO_GLIDE_INS = new ResourceProvider("Steele (Purdue) (w/o Glide-Ins)", STEELE_HOST, STEELE_BATCH, STEELE_FORK,
				STEELE_JAVA, STEELE_DIR, STEELE_REQS, STEELE_GRID_FTP, "grid", rsl);
		return STEELE_NO_GLIDE_INS;
	}
	
	private String name = "";
	private String hostName = "";
	private String batchScheduler = "";
	private String forkScheduler = "";
	private String javaPath = "";
	private String storagePath = "";
	private String requirements = "";
	private String gridFTPHost = "";
	private String universe = "";
	private GlobusRSL globusRSL;
	ArrayList<String> suggestedQueues = new ArrayList<String>();
	
	public ResourceProvider(String name, String hostName, String batchScheduler, String forkScheduler,
			String javaPath, String storagePath, String requirements,
			String gridFTPHost, String universe, GlobusRSL globusRSL) {
		this.name = name;
		this.hostName = hostName;
		this.batchScheduler = batchScheduler;
		this.forkScheduler = forkScheduler;
		this.javaPath = javaPath;
		this.storagePath = storagePath;
		this.requirements = requirements;
		this.gridFTPHost = gridFTPHost;
		this.universe = universe;
		this.globusRSL = globusRSL;
	}

	public Element toXMLMetadata(Element root) {
		Element xml = root.addElement(ResourceProvider.XML_METADATA_NAME);
		
		xml.addAttribute("name", this.name);
		xml.addAttribute("hostName", this.hostName);
		xml.addAttribute("batchScheduler", this.batchScheduler);
		xml.addAttribute("forkScheduler", this.forkScheduler);
		xml.addAttribute("javaPath", this.javaPath);
		xml.addAttribute("storagePath", this.storagePath);
		xml.addAttribute("requirements", this.requirements);
		xml.addAttribute("gridFTPHost", this.gridFTPHost);
		xml.addAttribute("universe", this.universe);
		if (suggestedQueues.size() > 0) {
			Element queuesEl = xml.addElement("SuggestedQueues");
			for (String queue : suggestedQueues) {
				Element queueEl = queuesEl.addElement("Queue");
				queueEl.addAttribute("name", queue);
			}
		}
		
		xml = this.globusRSL.toXMLMetadata(xml);
		
		return root;
	}
	
	public static ResourceProvider fromXMLMetadata(Element resourceProviderElem) {
		
		String name = resourceProviderElem.attribute("name").getValue();
		String rp_host = resourceProviderElem.attribute("hostName").getValue();
		String rp_batchScheduler = resourceProviderElem.attribute("batchScheduler").getValue();
		String rp_forkScheduler = resourceProviderElem.attribute("forkScheduler").getValue();
		String rp_javaPath = resourceProviderElem.attribute("javaPath").getValue();
		String rp_storagePath = resourceProviderElem.attribute("storagePath").getValue();
		String rp_requirements = resourceProviderElem.attribute("requirements").getValue();
		String rp_globus_ftp_host = resourceProviderElem.attribute("gridFTPHost").getValue();
		String rp_universe = resourceProviderElem.attribute("universe").getValue();
		
		Element rslElem = resourceProviderElem.element(GlobusRSL.XML_METADATA_NAME);
		GlobusRSL globusRSL = GlobusRSL.fromXMLMetadata(rslElem);
		
		ResourceProvider rp = new ResourceProvider(name, rp_host, rp_batchScheduler, rp_forkScheduler,
				rp_javaPath, rp_storagePath, rp_requirements,
				rp_globus_ftp_host, rp_universe, globusRSL);
		
		Element queuesEl = resourceProviderElem.element("SuggestedQueues");
		if (queuesEl != null) {
			List<Element> list = queuesEl.elements("Queue");
			for (Element queueEl : list) {
				rp.addSuggestedQueue(queueEl.attributeValue("name"));
			}
		}
		
		return rp;
	}
	
	@Override
	public String toString() {
		String str = "";
		
		str += "Resource Provider" + "\n";
		str += "\tname: " + name + "\n";
		str += "\thostName: " + hostName + "\n";
		str += "\tbatchScheduler: " + batchScheduler + "\n";
		str += "\tforkScheduler: " + forkScheduler + "\n";
		str += "\tjavaPath: " + javaPath + "\n";
		str += "\tstoragePath: " + storagePath + "\n";
		str += "\trequirements: " + requirements + "\n";
		str += "\tgridFTPHost: " + gridFTPHost + "\n";
		str += "\tuniverse: " + universe + "\n";
		str += "\tGlobusRSL: " + globusRSL.getRSLString();
		if (suggestedQueues.size() > 0) {
			str += "\n\tSuggestedQueues:";
			for (String queue : suggestedQueues)
				str += "\n\t\t" + queue;
		}
		
		return str;
	}

	public String getName() {
		return name;
	}
	
	public void setName(String name) {
		this.name = name;
	}
	
	public String getHostName() {
		return hostName;
	}

	public String getBatchScheduler() {
		return batchScheduler;
	}

	public String getForkScheduler() {
		return forkScheduler;
	}

	public String getJavaPath() {
		return javaPath;
	}

	public String getStoragePath() {
		return storagePath;
	}

	public String getRequirements() {
		return requirements;
	}

	public String getGridFTPHost() {
		return gridFTPHost;
	}

	public String getUniverse() {
		return universe;
	}

	public GlobusRSL getGlobusRSL() {
		return globusRSL;
	}
	
	public ArrayList<String> getSuggestedQueues() {
		return suggestedQueues;
	}
	
	public void addSuggestedQueue(String queue) {
		suggestedQueues.add(queue);
	}
	
	public boolean isGridUniverse() {
		if (this.universe.toLowerCase().contains("globus"))
			return true;
		if (this.universe.toLowerCase().contains("grid"))
			return true;
		return false;
	}
}
