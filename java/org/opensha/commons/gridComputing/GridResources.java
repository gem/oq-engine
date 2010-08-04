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

public class GridResources implements XMLSaveable {
	
	public static final String XML_METADATA_NAME = "GridResources";
	
	private SubmitHost submitHost;
	private ResourceProvider resourceProvider;
	private StorageHost storageHost;
	
	public GridResources(SubmitHost submitHost, ResourceProvider resourceProvider, StorageHost storageHost) {
		this.submitHost = submitHost;
		this.resourceProvider = resourceProvider;
		this.storageHost = storageHost;
	}

	public SubmitHost getSubmitHost() {
		return submitHost;
	}

	public ResourceProvider getResourceProvider() {
		return resourceProvider;
	}

	public StorageHost getStorageHost() {
		return storageHost;
	}
	
	public Element toXMLMetadata(Element root) {
		Element xml = root.addElement(XML_METADATA_NAME);
		
		xml = this.submitHost.toXMLMetadata(xml);
		xml = this.resourceProvider.toXMLMetadata(xml);
		xml = this.storageHost.toXMLMetadata(xml);
		
		return root;
	}
	
	public static GridResources fromXMLMetadata(Element resourcesElem) {
		SubmitHost submitHost = SubmitHost.fromXMLMetadata(resourcesElem.element(SubmitHost.XML_METADATA_NAME));
		ResourceProvider resourceProvider = ResourceProvider.fromXMLMetadata(resourcesElem.element(ResourceProvider.XML_METADATA_NAME));
		StorageHost storageHost = StorageHost.fromXMLMetadata(resourcesElem.element(StorageHost.XML_METADATA_NAME));
		
		return new GridResources(submitHost, resourceProvider, storageHost);
	}
	
	@Override
	public String toString() {
		String str = "";
		
		str += "Grid Resources" + "\n";
		str += GridJob.indentString(this.submitHost.toString()) + "\n";
		str += GridJob.indentString(this.resourceProvider.toString()) + "\n";
		str += GridJob.indentString(this.storageHost.toString());
		
		return str;
	}
}
