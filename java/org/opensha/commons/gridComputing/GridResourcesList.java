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

public class GridResourcesList implements Serializable {
	
	private ArrayList<ResourceProvider> resourceProviders;
	private ArrayList<SubmitHost> submitHosts;
	private ArrayList<StorageHost> storageHosts;
	
	public GridResourcesList(ArrayList<ResourceProvider> resourceProviders, ArrayList<SubmitHost> submitHosts,
			ArrayList<StorageHost> storageHosts) {
		this.resourceProviders = resourceProviders;
		this.submitHosts = submitHosts;
		this.storageHosts = storageHosts;
	}

	public ArrayList<ResourceProvider> getResourceProviders() {
		return resourceProviders;
	}

	public ArrayList<SubmitHost> getSubmitHosts() {
		return submitHosts;
	}

	public ArrayList<StorageHost> getStorageHosts() {
		return storageHosts;
	}

}
