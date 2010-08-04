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
import java.util.ArrayList;
import java.util.Iterator;

import org.dom4j.Document;
import org.dom4j.Element;
import org.opensha.commons.geo.Location;
import org.opensha.commons.metadata.XMLSaveable;
import org.opensha.commons.util.XMLUtils;

/**
 * This represents a list of site data value lists. It is most useful for applications such
 * as hazard maps, and for XML saving/loading.
 * 
 * @author Kevin Milner
 *
 */
public class SiteDataValueListList implements XMLSaveable {
	
	public static final String XML_METADATA_NAME = "SiteDataValuesList";
	
	private ArrayList<SiteDataValueList<?>> lists;
	
	private int size = -1;
	
	private boolean hasLocations = true;
	
	public SiteDataValueListList(ArrayList<SiteDataValueList<?>> lists) {
		this.lists = lists;
		
		// get the overall size, and ensure they're all the same
		for (SiteDataValueList<?> list : lists) {
			if (size < 0)
				size = list.size();
			if (size != list.size())
				throw new RuntimeException("The size of each list must be same!");
			if (!list.hasLocations())
				hasLocations = false;
		}
	}
	
	public int size() {
		return size;
	}
	
	public int getNumProviders() {
		return lists.size();
	}
	
	public ArrayList<SiteDataValue<?>> getDataList(int index) {
		ArrayList<SiteDataValue<?>> datas = new ArrayList<SiteDataValue<?>>();
		
		for (SiteDataValueList<?> list : lists) {
			datas.add(list.getValue(index));
		}
		
		return datas;
	}
	
	public Location getDataLocation(int index) {
		return lists.get(0).getLocationAt(index);
	}
	
	public boolean hasLocations() {
		return hasLocations;
	}

	public Element toXMLMetadata(Element root) {
		Element listEl = root.addElement(XML_METADATA_NAME);
		
		for (int i=0; i<getNumProviders(); i++) {
			SiteDataValueList<?> vals = lists.get(i);
			
			Element provEl = listEl.addElement("Values");
			provEl.addAttribute("Priority", i + "");
			
			vals.toXMLMetadata(provEl);
		}
		
		return root;
	}
	
	public static SiteDataValueListList fromXMLMetadata(Element listsEl) {
		Iterator<Element> it = listsEl.elementIterator();
		
		ArrayList<SiteDataValueList<?>> lists = new ArrayList<SiteDataValueList<?>>();
		ArrayList<Integer> priorities = new ArrayList<Integer>();
		
		while (it.hasNext()) {
			Element listEl = it.next();
			
			int priority = Integer.parseInt(listEl.attributeValue("Priority"));
			
			Element valsEl = listEl.element(SiteDataValueList.XML_METADATA_NAME);
			SiteDataValueList<?> vals = SiteDataValueList.fromXMLMetadata(valsEl);
			
			lists.add(vals);
			priorities.add(priority);
		}
		
		ArrayList<SiteDataValueList<?>> ordered = new ArrayList<SiteDataValueList<?>>();
		
		for (int i=0; i<lists.size(); i++) {
			SiteDataValueList<?> list = null;
			for (int j=0; j<priorities.size(); j++) {
				if (priorities.get(j) == i) {
					list = lists.get(j);
					break;
				}
			}
			
			if (list == null)
				throw new RuntimeException("Malformed priorities list!");
			
			ordered.add(list);
		}
		
		return new SiteDataValueListList(ordered);
	}
	
	public static void main(String args[]) throws IOException {
		ArrayList<Double> vals = new ArrayList<Double>();
		vals.add(0.5);
		vals.add(1.5);
		vals.add(2.5);
		vals.add(3.5);
		vals.add(4.5);
		vals.add(5.5);
		vals.add(6.5);
		
		SiteDataValueList<Double> list = new SiteDataValueList<Double>(SiteDataAPI.TYPE_VS30, "Asdfs", vals, null);
		SiteDataValueList<Double> list2 = new SiteDataValueList<Double>(SiteDataAPI.TYPE_VS30, "Asdfs", vals, null);
		SiteDataValueList<Double> list3 = new SiteDataValueList<Double>(SiteDataAPI.TYPE_VS30, "Asdfs", vals, null);
		
		ArrayList<SiteDataValueList<?>> lists = new ArrayList<SiteDataValueList<?>>();
		lists.add(list);
		lists.add(list2);
		lists.add(list3);
		
		SiteDataValueListList valsLists = new SiteDataValueListList(lists);
		
		Document doc = XMLUtils.createDocumentWithRoot();
		Element root = doc.getRootElement();
		
		root = valsLists.toXMLMetadata(root);
		
		XMLUtils.writeDocumentToFile("/tmp/vals.xml", doc);
		
		Element listsEl = root.element(SiteDataValueListList.XML_METADATA_NAME);
		
		valsLists = SiteDataValueListList.fromXMLMetadata(listsEl);
	}

}
