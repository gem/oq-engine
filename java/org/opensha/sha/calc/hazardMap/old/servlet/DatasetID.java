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

import java.io.Serializable;
import java.text.Collator;

public class DatasetID implements Comparable<DatasetID>, Serializable {
	public static Collator c = Collator.getInstance();
	
	private String id;
	private String name;
	private boolean logFile;
	private boolean mapDir;
	
	public DatasetID(String id, String name, boolean logFile, boolean mapDir) {
		this.id = id;
		this.name = name;
		this.logFile = logFile;
		this.mapDir = mapDir;
	}

	public int compareTo(DatasetID d2) {
		return -1*c.compare(id, d2.getID());
	}

	public String getID() {
		return id;
	}

	public String getName() {
		return name;
	}

	public boolean isLogFile() {
		return logFile;
	}

	public boolean isMapDir() {
		return mapDir;
	}

	public void setIsLogFile(boolean logFile) {
		this.logFile = logFile;
	}

	public void setIsMapDir(boolean mapDir) {
		this.mapDir = mapDir;
	}
}
