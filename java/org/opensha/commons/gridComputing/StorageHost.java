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

import org.dom4j.Element;

public class StorageHost extends GridResource {
	
	public static final String XML_METADATA_NAME = "StorageHost";
	
	public static final StorageHost HPC = new StorageHost("HPC", "hpc.usc.edu", "hpc.usc.edu", "/home/scec-00/tera3d/opensha/hazmaps", "jobmanager-fork", "jobmanager-pbs", "/usr/bin/java", "/home/scec-00/tera3d/opensha/hazmaps/hazMapProcessing.jar");
	
	private String name = "";
	private String schedulerHostName = "";
	private String gridFTPHostName = "";
	private String path = "";
	private String forkScheduler = "";
	private String batchScheduler = "";
	private String javaPath = "";
	private String jarPath = "";
	
	public StorageHost(String name, String forkHostName, String gridFTPHostName, String path, String forkScheduler, String batchScheduler, String javaPath, String jarPath) {
		this.name = name;
		this.schedulerHostName = forkHostName;
		this.gridFTPHostName = gridFTPHostName;
		this.path = path;
		this.forkScheduler = forkScheduler;
		this.batchScheduler = batchScheduler;
		this.javaPath = javaPath;
		this.jarPath = jarPath;
	}

	public Element toXMLMetadata(Element root) {
		Element xml = root.addElement(StorageHost.XML_METADATA_NAME);
		
		xml.addAttribute("name", this.name);
		xml.addAttribute("schedulerHostName", this.schedulerHostName);
		xml.addAttribute("gridFTPHostName", this.gridFTPHostName);
		xml.addAttribute("path", this.path);
		xml.addAttribute("forkScheduler", this.forkScheduler);
		xml.addAttribute("batchScheduler", this.batchScheduler);
		xml.addAttribute("javaPath", this.javaPath);
		xml.addAttribute("jarPath", this.jarPath);
		
		return root;
	}
	
	public static StorageHost fromXMLMetadata(Element resourceProviderElem) {
		
		String name = resourceProviderElem.attribute("name").getValue();
		String schedulerHostName = resourceProviderElem.attribute("schedulerHostName").getValue();
		String gridFTPHostName = resourceProviderElem.attribute("gridFTPHostName").getValue();
		String path = resourceProviderElem.attribute("path").getValue();
		String forkScheduler = resourceProviderElem.attribute("forkScheduler").getValue();
		String batchScheduler = resourceProviderElem.attribute("batchScheduler").getValue();
		String javaPath = resourceProviderElem.attribute("javaPath").getValue();
		String jarPath = resourceProviderElem.attribute("jarPath").getValue();
		
		return new StorageHost(name, schedulerHostName, gridFTPHostName, path, forkScheduler, batchScheduler, javaPath, jarPath);
	}
	
	@Override
	public String toString() {
		String str = "";
		
		str += "Storage Host" + "\n";
		str += "\tname: " + name + "\n";
		str += "\tschedulerHostName: " + schedulerHostName + "\n";
		str += "\tgridFTPHostName: " + gridFTPHostName + "\n";
		str += "\tpath: " + path + "\n";
		str += "\tforkScheduler: " + forkScheduler + "\n";
		str += "\tbatchScheduler: " + batchScheduler + "\n";
		str += "\tjavaPath: " + javaPath + "\n";
		str += "\tjarPath: " + jarPath;
		
		return str;
	}

	public String getName() {
		return name;
	}

	public String getSchedulerHostName() {
		return schedulerHostName;
	}

	public String getGridFTPHostName() {
		return gridFTPHostName;
	}

	public String getPath() {
		return path;
	}

	public String getForkScheduler() {
		return forkScheduler;
	}

	public String getBatchScheduler() {
		return batchScheduler;
	}

	public String getJavaPath() {
		return javaPath;
	}

	public String getJarPath() {
		return jarPath;
	}
}
