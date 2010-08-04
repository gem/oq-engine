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

package org.opensha.refFaultParamDb.dao;

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
/**
 * <p>Title: NormalEstimateDAO_API.java </p>
 * <p>Description: Inserts/gets/delete normal estimates from the tables</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public interface EstimateDAO_API {

  /**
   * Add a new  estimate object to the database
   *
   */
  public void addEstimate(int estimateInstanceId, Estimate estimate) throws InsertException;


  /**
   * Get the  Estimate Instance info for a particular estimateInstanceId
   */
  public Estimate getEstimate(int estimateInstanceId) throws QueryException;


  /**
   * Remove the  Estimate from the list
   */
  public boolean removeEstimate(int estimateInstanceId) throws UpdateException;

  public String getEstimateTypeName();

  public void setDB_Connection(DB_AccessAPI dbAccessAPI);

}
