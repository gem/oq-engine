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
import org.opensha.commons.metadata.XMLSaveable;

public class GridCalculationParameters implements XMLSaveable {
	
	public static final String XML_METADATA_NAME = "GridCalculationParameters";
	
	protected int maxWallTime;
	
	protected Element element = null;
	
	public GridCalculationParameters(int maxWallTime) {
		this.maxWallTime = maxWallTime;
	}
	
	public GridCalculationParameters(Element parentElement, String elemName) {
		element = this.getElement(parentElement, elemName);
		
		maxWallTime = Integer.parseInt(element.attribute("maxWallTime").getValue());
	}
	
	private Element getElement(Element parent, String elemName) {
		return parent.element(elemName);
	}

	public Element toXMLMetadata(Element root) {
		Element xml = root.addElement(XML_METADATA_NAME);
		
		xml.addAttribute("maxWallTime", maxWallTime + "");
		
		return root;
	}
	
	@Override
	public String toString() {
		String str = "";
		
		str += "Grid Calculation Parameters" + "\n";
		str += "\tmaxWallTime: " + maxWallTime;
		
		return str;
	}
}
