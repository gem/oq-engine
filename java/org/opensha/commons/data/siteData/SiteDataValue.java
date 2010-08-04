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

package org.opensha.commons.data.siteData;

import org.dom4j.Attribute;
import org.opensha.commons.metadata.XMLSaveable;

/**
 * This represents a single site data value, along with metadata describing it's
 * type and source. It is returned by the SiteDataAPI.getAnnotatedValue method. 
 * 
 * @author Kevin
 *
 * @param <Element>
 */
public class SiteDataValue<Element> implements XMLSaveable {
	
	public static final String XML_METADATA_NAME = "SiteDataValue";
	
	private String dataType;
	private String dataMeasurementType;
	private Element value;
	private String sourceName = null;

	public SiteDataValue(String dataType, String dataMeasurementType, Element value) {
		this(dataType, dataMeasurementType, value, null);
	}
	
	public SiteDataValue(String dataType, String dataMeasurementType, Element value, String sourceName) {
		this.dataType = dataType;
		this.dataMeasurementType = dataMeasurementType;
		this.value = value;
		this.sourceName = sourceName;
	}
	
	public String getDataType() {
		return dataType;
	}

	public String getDataMeasurementType() {
		return dataMeasurementType;
	}

	public Element getValue() {
		return value;
	}
	
	public String getSourceName() {
		return sourceName;
	}

	@Override
	public String toString() {
		String str = "Type: " + dataType + ", Measurement Type: " + dataMeasurementType + ", Value: " + value;
		if (sourceName != null)
			str += ", Source: " + sourceName;
		return str;
	}

	public org.dom4j.Element toXMLMetadata(org.dom4j.Element root) {
		org.dom4j.Element elem = root.addElement(XML_METADATA_NAME);
		elem.addAttribute("type", dataType);
		elem.addAttribute("measurementType", dataMeasurementType);
		
		// in the future we could add complex elements here
		org.dom4j.Element valEl = elem.addElement("Value");
		if (value instanceof String)
			valEl.addAttribute("stringValue", value.toString());
		else if (value instanceof Double)
			valEl.addAttribute("doubleValue", value.toString());
		else
			throw new RuntimeException("Type '" + dataType + "' cannot be saved to XML!");
		
		return root;
	}
	
	public static SiteDataValue<?> fromXMLMetadata(org.dom4j.Element dataElem) {
		String dataType = dataElem.attributeValue("type");
		String measurementType = dataElem.attributeValue("measurementType");
		
		org.dom4j.Element valEl = dataElem.element("Value");
		
		Attribute strAtt = valEl.attribute("stringValue");
		Attribute doubAtt = valEl.attribute("doubleValue");
		
		Object val;
		if (strAtt != null) {
			val = strAtt.getValue();
		} else if (doubAtt != null) {
			val = Double.parseDouble(doubAtt.getValue());
		} else {
			throw new RuntimeException("Type '" + dataType + "' unknown, cannot load from XML!");
		}
		return new SiteDataValue(dataType, measurementType, val);
	}
}
