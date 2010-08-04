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

package org.opensha.refFaultParamDb.dao.db;

import java.util.ArrayList;

import oracle.spatial.geometry.JGeometry;

import com.sun.rowset.CachedRowSetImpl;

/**
 * <p>Title: SpatialQueryResult.java </p>
 * <p>Description: This class can be used to return the results of spatial queries.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class SpatialQueryResult implements java.io.Serializable{
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	private CachedRowSetImpl cachedRowSetImpl;
	private ArrayList<ArrayList<JGeometry>> geomteryObjectsList = new ArrayList<ArrayList<JGeometry>>();

	public SpatialQueryResult() {
	}

	public void setCachedRowSet(CachedRowSetImpl cachedRowSetImpl) {
		this.cachedRowSetImpl = cachedRowSetImpl;
	}

	public ArrayList<JGeometry> getGeometryObjectsList(int index) {
		return geomteryObjectsList.get(index);
	}

	public void add(ArrayList<JGeometry> geomteryObjects) {
		geomteryObjectsList.add(geomteryObjects);
	}

	public CachedRowSetImpl getCachedRowSet() {
		return this.cachedRowSetImpl;
	}



}
