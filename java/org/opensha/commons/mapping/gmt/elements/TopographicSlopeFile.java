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

package org.opensha.commons.mapping.gmt.elements;

import org.opensha.commons.geo.Region;
import org.opensha.commons.mapping.gmt.GMT_Map;

public enum TopographicSlopeFile {
	CA_THREE		(3, "calTopoInten03.grd", GMT_Map.ca_topo_region),
	CA_SIX			(6, "calTopoInten06.grd", GMT_Map.ca_topo_region),
	CA_EIGHTEEN		(18, "calTopoInten18.grd", GMT_Map.ca_topo_region),
	CA_THIRTY 		(30, "calTopoInten30.grd", GMT_Map.ca_topo_region),
	SRTM_30_PLUS	(30, "srtm30_plus_v5.0_inten.grd", Region.getGlobalRegion());
	
	private final int resolution;
	private final String fileName;
	private final Region region;
	TopographicSlopeFile(int resolution, String fileName, Region region) {
		this.resolution = resolution;
		this.fileName = fileName;
		this.region = region;
	}
	
	public int resolution() { return resolution; }
	public String fileName() { return fileName; }
	public Region region() { return region; }
}
