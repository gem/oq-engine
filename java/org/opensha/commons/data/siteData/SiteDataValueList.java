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

import java.io.IOException;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Iterator;

import org.dom4j.Document;
import org.dom4j.Element;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.metadata.XMLSaveable;
import org.opensha.commons.util.XMLUtils;

/**
 * This class represents a list of site data values. The advantage that it has over an ArrayList of
 * SiteDataValue objects is that it only stores the metadata for the values once, instead of once
 * for each value.
 * 
 * @author Kevin Milner
 *
 * @param <E>
 */
public class SiteDataValueList<E> implements XMLSaveable, Serializable {
	
	public static final String XML_METADATA_NAME = "SiteDataValueList";
	
	private String dataType;
	private String dataMeasurementType;
	private ArrayList<E> values;
	private String sourceName = null;
	private LocationList locs = null;
	
	public SiteDataValueList(ArrayList<E> values, SiteDataAPI<E> source) {
		this(values, source, null);
	}
	
	public SiteDataValueList(ArrayList<E> values, SiteDataAPI<E> source, LocationList locs) {
		this(source.getDataType(), source.getDataMeasurementType(), values, source.getName(), locs);
	}
	
	public SiteDataValueList(String dataType, String dataMeasurementType,
								ArrayList<E> values, String sourceName) {
		this(dataType, dataMeasurementType, values, sourceName, null);
	}
	
	public SiteDataValueList(String dataType, String dataMeasurementType,
								ArrayList<E> values, String sourceName, LocationList locs) {
		this.dataType = dataType;
		this.dataMeasurementType = dataMeasurementType;
		this.values = values;
		this.sourceName = sourceName;
		this.locs = locs;
		
		if (values == null) {
			throw new RuntimeException("Values cannot be null!");
		}
		
		if (locs != null && locs.size() != values.size()) {
			throw new RuntimeException("Locations must be null, or contain the same amount of points as values!");
		}
	}
	
	public String getType() {
		return dataType;
	}

	public String getFlag() {
		return dataMeasurementType;
	}
	
	/**
	 * Get an annotated value for the given location.
	 * 
	 * @param index
	 * @return
	 */
	public SiteDataValue<E> getValue(int index) {
		return new SiteDataValue<E>(dataType, dataMeasurementType, values.get(index), sourceName);
	}
	
	public Location getLocationAt(int index) {
		if (locs == null)
			return null;
		return locs.get(index);
	}

	public ArrayList<E> getValues() {
		return values;
	}
	
	public E getValueForLocation(Location loc) {
		for (int i=0; i<locs.size(); i++) {
			Location valLoc = locs.get(i);
			if (loc.equals(valLoc))
				return values.get(i);
		}
		return null;
	}
	
	public String getSourceName() {
		return sourceName;
	}
	
	public int size() {
		return values.size();
	}
	
	public LocationList getLocationList() {
		return locs;
	}
	
	public boolean hasLocations() {
		return locs != null;
	}

	@Override
	public String toString() {
		String str = "Type: " + dataType + ", Measurement Type: " + dataMeasurementType + ", Num: " + values.size();
		if (sourceName != null)
			str += ", Source: " + sourceName;
		return str;
	}

	public Element toXMLMetadata(Element root) {
		Element el = root.addElement(XML_METADATA_NAME);
		
		el.addAttribute("Type", getType());
		el.addAttribute("TypeFlag", getFlag());
		el.addAttribute("SourceName", getSourceName());
		el.addAttribute("Num", size() + "");
		
		Element valsEl = el.addElement("Values");
		
		boolean hasLocs = this.hasLocations();
		
		// we use short names here to save space
		ArrayList<E> vals = this.getValues();
		
		/* Decided not to use this, but it's worth keeping...
		 * It is for using java's XMLEncoder to encode an element and
		 * add it to an existing Dom4J element */
//		ByteArrayOutputStream out = new ByteArrayOutputStream();
//		XMLEncoder enc = new XMLEncoder(out);
//		
//		enc.writeObject(vals);
//		enc.flush();
//		enc.close();
//		
//		try {
//			out.flush();
//		} catch (IOException e1) {
//			throw new RuntimeException(e1);
//		}
//		
//		String arrayStr = out.toString();
//		System.out.println(arrayStr);
//		
//		ByteArrayInputStream bs = new ByteArrayInputStream(arrayStr.getBytes());
//		SAXReader read = new SAXReader();
//		Document arrayDoc = null;
//		try {
//			arrayDoc = read.read(bs);
//		} catch (DocumentException e) {
//			throw new RuntimeException(e);
//		}
//		Element arrayRoot = arrayDoc.getRootElement();
//		
//		valsEl.add(arrayRoot);
		
		if (hasLocs) {
			LocationList list = this.getLocationList();
			list.toXMLMetadata(root);
		}
		
		for (int i=0; i<vals.size(); i++) {
			E val = vals.get(i);
			
			if (val instanceof Double) {
				Double dVal = (Double)val;
				if (dVal.isNaN())
					continue;
			} else if (val instanceof String) {
				String sVal = (String)val;
				if (dataType.equals(SiteDataAPI.TYPE_VS30)) {
					if (sVal.equals("NA"))
						continue;
				} else {
					if (sVal.length() == 0)
						continue;
				}
			}
			
			Element valEl = valsEl.addElement("V");
			
			// if we have more complex types, we can do comparisons on 'type'
			// then add complex types
			valEl.addAttribute("v", val.toString());
			valEl.addAttribute("i", i + "");
		}
		
		return el;
	}
	
	public static final SiteDataValueList<?> fromXMLMetadata(Element dataElement) {
		String type = dataElement.attributeValue("Type");
		String flag = dataElement.attributeValue("TypeFlag");
		String name = dataElement.attributeValue("SourceName");
		int num = Integer.parseInt(dataElement.attributeValue("Num"));
		if (name != null && name.equals("null"))
			name = null;
		
		boolean isDouble = false;
		boolean isString = false;
		if (type.equals(SiteDataAPI.TYPE_VS30))
			isDouble = true;
		else if (type.equals(SiteDataAPI.TYPE_WILLS_CLASS))
			isString = true;
		else if (type.equals(SiteDataAPI.TYPE_DEPTH_TO_2_5))
			isDouble = true;
		else if (type.equals(SiteDataAPI.TYPE_DEPTH_TO_1_0))
			isDouble = true;
		else
			throw new RuntimeException("Type '" + type + "' unknown, cannot load from XML!");
		
		Element locsEl = dataElement.element(LocationList.XML_METADATA_NAME);
		LocationList locs = null;
		if (locsEl != null) {
			locs = LocationList.fromXMLMetadata(locsEl);
		}
		
		Element valsEl = dataElement.element("Values");
		Iterator<Element> valsIt = valsEl.elementIterator();
		
		ArrayList vals = null;
		
		if (isDouble) {
			vals = new ArrayList<Double>();
			for (int i=0; i<num; i++) {
				vals.add(Double.NaN);
			}
		} else if (isString) {
			vals = new ArrayList<String>();
			for (int i=0; i<num; i++) {
				if (type.equals(SiteDataAPI.TYPE_WILLS_CLASS))
					vals.add("NA");
				else
					vals.add("");
			}
		}
		
		while (valsIt.hasNext()) {
			Element valEl = valsIt.next();
			String strVal = valEl.attributeValue("v");
			int i = Integer.parseInt(valEl.attributeValue("i"));
			if (isString)
				vals.set(i, strVal);
			else if (isDouble)
				vals.set(i, Double.parseDouble(strVal));
		}
		
		SiteDataValueList<?> list = null;
		
		if (isDouble)
			list = new SiteDataValueList<Double>(type, flag, vals, name, locs);
		else if (isString)
			list = new SiteDataValueList<String>(type, flag, vals, name, locs);
		
		return list;
	}
	
	public static void main(String args[]) throws IOException {
		ArrayList<Double> vals = new ArrayList<Double>();
		LocationList locs = new LocationList();
		vals.add(new Double(0.5));
		locs.add(new Location(34, -120.6));
		vals.add(new Double(0.4));
		locs.add(new Location(34, -120.5));
		vals.add(new Double(0.3));
		locs.add(new Location(34, -120.4));
		vals.add(new Double(0.2));
		locs.add(new Location(34, -120.3));
		vals.add(new Double(0.1));
		locs.add(new Location(34, -120.2));
		vals.add(new Double(0.05));
		locs.add(new Location(34, -120.1));
		
		SiteDataValueList<Double> list = new SiteDataValueList<Double>(SiteDataAPI.TYPE_VS30, "asdfas", vals, null, locs);
		
		Document doc = XMLUtils.createDocumentWithRoot();
		Element root = doc.getRootElement();
		
		Element el = list.toXMLMetadata(root);
		
		XMLUtils.writeDocumentToFile("/tmp/xml.xml", doc);
		
		System.out.println(SiteDataValueList.fromXMLMetadata(el));
	}

}
