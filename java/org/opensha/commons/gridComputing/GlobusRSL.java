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

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Iterator;

import org.dom4j.Attribute;
import org.dom4j.Element;
import org.opensha.commons.metadata.XMLSaveable;

public class GlobusRSL implements XMLSaveable, Serializable {
	
	public static final String JOB_TYPE_NAME = "jobtype";
	public static final String MAX_WALL_TIME_NAME = "maxwalltime";
	public static final String QUEUE_NAME = "queue";
	
	public static final String SINGLE_JOB_TYPE = "single";
	
	public static final String XML_METADATA_NAME = "GlobusRSL";
	
	private ArrayList<String[]> pairs;
	
	private GlobusRSL(ArrayList<String[]> pairs) {
		this.pairs = pairs;
	}
	
	public GlobusRSL(String jobType, int maxWallTime) {
		pairs = new ArrayList<String[]>();
		this.addPair(GlobusRSL.JOB_TYPE_NAME, jobType);
		this.addPair(GlobusRSL.MAX_WALL_TIME_NAME, maxWallTime + "");
	}
	
	public void addPair(String name, String value) {
		String pair[] = {name, value};
		
		// if this is a duplicate, remove the old one
		boolean remove = false;
		int i=0;
		for (i=0; i<pairs.size(); i++) {
			String check[] = pairs.get(i);
			if (check[0].equals(pair[0])) {
				remove = true;
				break;
			}
		}
		if (remove)
			pairs.remove(i);
		if (value.length() > 0)
			pairs.add(pair);
	}
	
	public void setQueue(String queueName) {
		this.addPair(GlobusRSL.QUEUE_NAME, queueName);
	}
	
	public String getQueue() {
		return this.getValue(GlobusRSL.QUEUE_NAME);
	}
	
	public String getJobType() {
		return this.getValue(GlobusRSL.JOB_TYPE_NAME);
	}
	
	public int getMaxWallTime() {
		String str = this.getValue(GlobusRSL.MAX_WALL_TIME_NAME);
		if (str.length() == 0)
			return -1;
		return Integer.parseInt(str);
	}
	
	public void setMaxWallTime(int wallTime) {
		this.addPair(GlobusRSL.MAX_WALL_TIME_NAME, wallTime + "");
	}
	
	public String getValue(String name) {
		for (String[] pair : pairs) {
			if (pair[0].equals(name))
				return pair[1];
		}
		return "";
	}
	
	public String getRSLString() {
		String rsl = "";
		
		for (String[] pair : pairs) {
			rsl += "(" + pair[0] + "=" + pair[1] + ")";
		}
		
		return rsl;
	}

	public Element toXMLMetadata(Element root) {
		Element xml = root.addElement(GlobusRSL.XML_METADATA_NAME);
		
		for (String[] pair : pairs) {
			xml.addAttribute(pair[0], pair[1]);
		}
		
		return root;
	}
	
	public static GlobusRSL fromXMLMetadata(Element rslElem) {
		ArrayList<String[]> pairs = new ArrayList<String[]>();
		
		Iterator<Attribute> attIt = rslElem.attributeIterator();
		while (attIt.hasNext()) {
			Attribute att = attIt.next();
			String pair[] = {att.getName(), att.getValue()};
			pairs.add(pair);
		}
		
		return new GlobusRSL(pairs);
	}
}
