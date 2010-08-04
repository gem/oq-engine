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

public class SubmitHost extends GridResource {
	
	public static final String XML_METADATA_NAME = "SubmitHost";
	
	// presets
	public static final SubmitHost SCECIT18 = new SubmitHost("scecit18", "scecit18.usc.edu",
			"/home/kmilner/hazMapRuns", "/home/kmilner/dependencies", "jobmanager-fork", "/usr/local/condor/bin/",
			"GLOBUS_LOCATION=/usr/local/vdt/globus;LD_LIBRARY_PATH=/usr/local/vdt/globus/lib;",
			"-n transfer -N VDS::transfer:1.0 -i - -R local /usr/local/vds-1.4.7/bin/transfer  -f  base-uri se-mount-point",
			"/usr/local/vds-1.4.7/bin/kickstart");
	
	public static final SubmitHost INTENSITY = new SubmitHost("Intensity", "intensity.usc.edu",
			"/scratch/opensha/kmilner/hazMapRuns", "/scratch/opensha/kmilner/dependencies", "jobmanager-fork", "/usr/scec/condor/default/bin/",
			"GLOBUS_LOCATION=/usr/scec/globus-4.0.4;LD_LIBRARY_PATH=/usr/scec/globus-4.0.4/lib;",
			"-n transfer -N pegasus::transfer:1.0 -i - -R local /usr/scec/pegasus/pegasus-2.1.0cvs-20080130/bin/transfer  -f  base-uri se-mount-point",
			"/usr/scec/pegasus/pegasus-2.1.0cvs-20080130/bin/kickstart");
	
	public static final SubmitHost AFTERSHOCK = new SubmitHost("Aftershock", "aftershock.usc.edu",
			"/scratch/opensha/tera3d/hazMapRuns", "/home/aftershock/opensha/hazmaps/dependencies", "jobmanager-fork", "/usr/local/condor/default/bin/",
			"GLOBUS_LOCATION=/usr/local/globus/default;LD_LIBRARY_PATH=/usr/local/globus/default/lib;",
			"-n transfer -N pegasus::transfer:1.0 -i - -R local /usr/local/pegasus/default/bin/transfer  -f  base-uri se-mount-point",
			"/usr/local/pegasus/default/bin/kickstart");
	
	private String name = "";
	private String hostName = "";
	private String path = "";
	private String dependencyPath = "";
	private String forkScheduler = "";
	private String condorPath = "";
	private String transferEnvironment = "";
	private String transferArguments = "";
	private String transferExecutable = "";
	
	public SubmitHost(String name, String hostName, String path, String dependencyPath, String forkScheduler, String condorPath,
			String transferEnvironment, String transferArguments, String transferExecutable) {
		this.name = name;
		this.hostName = hostName;
		this.path = path;
		this.dependencyPath = dependencyPath;
		this.forkScheduler = forkScheduler;
		this.condorPath = condorPath;
		this.transferEnvironment = transferEnvironment;
		this.transferArguments = transferArguments;
		this.transferExecutable = transferExecutable;
	}

	public Element toXMLMetadata(Element root) {
		Element xml = root.addElement(SubmitHost.XML_METADATA_NAME);
		
		xml.addAttribute("name", this.name);
		xml.addAttribute("hostName", this.hostName);
		xml.addAttribute("path", this.path);
		xml.addAttribute("dependencyPath", this.dependencyPath);
		xml.addAttribute("forkScheduler", this.forkScheduler);
		xml.addAttribute("condorPath", this.condorPath);
		xml.addAttribute("transferEnvironment", this.transferEnvironment);
		xml.addAttribute("transferArguments", this.transferArguments);
		xml.addAttribute("transferExecutable", this.transferExecutable);
		
		return root;
	}
	
	public static SubmitHost fromXMLMetadata(Element submitHostElem) {
		String name = submitHostElem.attribute("name").getValue();
		String submitHost = submitHostElem.attribute("hostName").getValue();
		String submitHostPath = submitHostElem.attribute("path").getValue();
		String submitHostPathToDependencies = submitHostElem.attribute("dependencyPath").getValue();
		String forkScheduler = submitHostElem.attribute("forkScheduler").getValue();
		String condorPath = submitHostElem.attribute("condorPath").getValue();
		String submitHostTransfer_env = submitHostElem.attribute("transferEnvironment").getValue();
		String submitHostTransfer_args = submitHostElem.attribute("transferArguments").getValue();
		String submitHostTransfer_exec = submitHostElem.attribute("transferExecutable").getValue();
		
		return new SubmitHost(name, submitHost, submitHostPath, submitHostPathToDependencies, forkScheduler, condorPath,
				submitHostTransfer_env, submitHostTransfer_args, submitHostTransfer_exec);
	}
	
	@Override
	public String toString() {
		String str = "";
		
		str += "Submit Host" + "\n";
		str += "\tname: " + name + "\n";
		str += "\thostName: " + hostName + "\n";
		str += "\tpath: " + path + "\n";
		str += "\tdependencyPath: " + dependencyPath + "\n";
		str += "\tforkScheduler: " + forkScheduler + "\n";
		str += "\tcondorPath: " + condorPath + "\n";
		str += "\ttransferEnvironment: " + transferEnvironment + "\n";
		str += "\ttransferArguments: " + transferArguments + "\n";
		str += "\ttransferExecutable: " + transferExecutable;
		
		return str;
	}

	public String getName() {
		return name;
	}

	public String getHostName() {
		return hostName;
	}

	public String getPath() {
		return path;
	}

	public String getDependencyPath() {
		return dependencyPath;
	}

	public String getForkScheduler() {
		return forkScheduler;
	}

	public String getCondorPath() {
		return condorPath;
	}

	public String getTransferEnvironment() {
		return transferEnvironment;
	}

	public String getTransferArguments() {
		return transferArguments;
	}

	public String getTransferExecutable() {
		return transferExecutable;
	}
}
