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

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.data.estimate.FractileListEstimate;
import org.opensha.commons.data.function.ArbDiscrEmpiricalDistFunc;
import org.opensha.refFaultParamDb.dao.EstimateDAO_API;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
/**
 * <p>Title: FractileListEstimateDB_DAO.java </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class FractileListEstimateDB_DAO implements EstimateDAO_API {

	public final static String EST_TYPE_NAME="FractileListEstimate";
	private final static String ERR_MSG = "This class just deals with Fractile List Estimates";
	private XY_EstimateDB_DAO xyEstimateDB_DAO  = new XY_EstimateDB_DAO();

	/**
	 * Constructor.
	 * @param dbConnection
	 *
	 */
	public FractileListEstimateDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	public FractileListEstimateDB_DAO() { }


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		xyEstimateDB_DAO.setDB_Connection(dbAccessAPI);
	}

	/**
	 * Add the normal estimate into the database table
	 * @param estimateInstanceId
	 * @param estimate
	 * @throws InsertException
	 */
	public void addEstimate(int estimateInstanceId, Estimate estimate) throws InsertException {
		if(!(estimate instanceof FractileListEstimate)) throw new InsertException(ERR_MSG);
		FractileListEstimate fractileListEstimate = (FractileListEstimate)estimate;
		xyEstimateDB_DAO.addEstimate(estimateInstanceId, fractileListEstimate.getValues());
	}

	/**
	 *
	 * @param estimateInstanceId
	 * @return
	 * @throws QueryException
	 */
	public Estimate getEstimate(int estimateInstanceId) throws QueryException {
		ArbDiscrEmpiricalDistFunc func = new ArbDiscrEmpiricalDistFunc();
		xyEstimateDB_DAO.getEstimate(estimateInstanceId,func);
		FractileListEstimate estimate=new FractileListEstimate(func);
		return estimate;
	}

	/**
	 *
	 * @param estimateInstanceId
	 * @return
	 * @throws UpdateException
	 */
	public boolean removeEstimate(int estimateInstanceId) throws UpdateException {
		return xyEstimateDB_DAO.removeEstimate(estimateInstanceId);
	}

	public String getEstimateTypeName() {
		return EST_TYPE_NAME;
	}

}
