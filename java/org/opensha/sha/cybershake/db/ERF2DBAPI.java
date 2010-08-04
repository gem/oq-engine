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

package org.opensha.sha.cybershake.db;

import java.util.ArrayList;

import org.opensha.sha.earthquake.EqkRupForecastAPI;

public interface ERF2DBAPI {
	
	
	/**
	 * Get a list of all ERFs in the database
	 * @return
	 */
	public ArrayList<CybershakeERF> getAllERFs();
	
	/**
	 * Inserts the ERF parameters info in the table "ERF_Metadata"
	 * @param erfName
	 * @param attrName
	 * @param attrVal
	 */
	public void insertERFParams(int erfId,String attrName, String attrVal, String attrType,String attrUnits);
	
	/**
	 * 
	 * Inserts ERF name and description in table ERF_IDs
	 * @param erfName
	 * @param erfDesc
	 * @return
	 */
	public int insertERFId(String erfName, String erfDesc);
	

	/**
	 * Inserts source rupture information for the ERF in table "Ruptures"
	 * @param erfName
	 * @param sourceId
	 * @param ruptureId
	 * @param sourceName
	 * @param sourcetype
	 * @param magnitude
	 * @param probability
	 * @param gridSpacing
	 * @param numRows
	 * @param numCols
	 * @param numPoints
	 */
	public void insertERFRuptureInfo(int erfId ,int sourceId,int ruptureId,
			                        String sourceName,String sourcetype,double magnitude,
			                        double probability,double gridSpacing,
			                        double surfaceStartLat,double surfaceStartLon,double surfaceStartDepth,
			                        double surfaceEndLat,double surfaceEndLon,double surfaceEndDepth,
			                        int numRows,int numCols,int numPoints);
	
	/**
	 * Inserts surface locations information for each rupture in table "Points"
	 * @param erfName
	 * @param sourceId
	 * @param ruptureId
	 * @param lat
	 * @param lon
	 * @param depth
	 * @param rake
	 * @param dip
	 * @param strike
	 */
	public void insertRuptureSurface(int erfId,int sourceId,int ruptureId,
			                         double lat,double lon,double depth,double rake,
			                         double dip,double strike);
	
	/**
	 * Retrives the id of the ERF from the table ERF_IDs  for the corresponding ERF_Name.
	 * @param erfName
	 * @return
	 */
	public int getInserted_ERF_ID(String erfName);
	
	/**
	 * Retrives the rupture probability
	 * @param erfId
	 * @param sourceId
	 * @param rupId
	 * @return
	 */
	public double getRuptureProb(int erfId,int sourceId,int rupId);
	
	/**
	 * Insert the specified rupture from the given forecast
	 * @param forecast
	 * @param erfID
	 * @param sourceID
	 * @param rupID
	 */
	public void insertSrcRupInDB(EqkRupForecastAPI forecast, int erfID, int sourceID, int rupID);
	
	/**
	 * Deletes a rupture
	 * @param erfID
	 * @param srcID
	 * @param rupID
	 */
	public void deleteRupture(int erfID, int srcID, int rupID);
	
	/**
	 * Returns the ID for a given rupture name
	 * @param erfID
	 * @param name
	 * @return
	 */
	public int getSourceIDFromName(int erfID, String name);

}
