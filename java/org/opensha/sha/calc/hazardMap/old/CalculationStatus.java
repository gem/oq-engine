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

import java.io.Serializable;
import java.text.SimpleDateFormat;
import java.util.Date;


public class CalculationStatus implements Serializable {
	
	String message;
	int total;
	int ip;
	int done;
	int retrieved;
	Date date;
	
	public CalculationStatus(String message, Date date, int total, int ip, int done, int retrieved) {
		this.message = message;
		this.total = total;
		this.ip = ip;
		this.done = done;
		this.retrieved = retrieved;
		this.date = date;
	}

	public String getMessage() {
		return message;
	}

	public int getTotal() {
		return total;
	}

	public int getIp() {
		return ip;
	}

	public int getDone() {
		return done;
	}

	public int getRetrieved() {
		return retrieved;
	}

	public Date getDate() {
		return date;
	}
	
	public String toString() {
		SimpleDateFormat format = HazardMapJobCreator.LINUX_DATE_FORMAT;
		return "Message: " + message + "\n"
				+ "Total: " + total + "\n"
				+ "In Progress: " + ip + "\n"
				+ "Done: " + done + "\n"
				+ "Retrieved: " + retrieved + "\n"
				+ "Date: " + format.format(date) + "\n";
	}
}
