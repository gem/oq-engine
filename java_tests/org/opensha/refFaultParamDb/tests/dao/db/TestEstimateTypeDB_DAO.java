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

package org.opensha.refFaultParamDb.tests.dao.db;

import java.util.ArrayList;

import static org.junit.Assert.*;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.EstimateTypeDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.tests.AllTests;
import org.opensha.refFaultParamDb.vo.EstimateType;
/**
 *
 * <p>Title: Test_EstimateTypeDB_DAO.java </p>
 * <p>Description: Test the Test_EstimateType DB DAO class</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */
public class TestEstimateTypeDB_DAO {
	private DB_AccessAPI dbConnection ;
	private EstimateTypeDB_DAO estimateTypeDB_DAO = null;

	public TestEstimateTypeDB_DAO(String name) {
		dbConnection = AllTests.dbConnection;
	}

	@Before
	public void setUp() throws Exception {
		estimateTypeDB_DAO = new EstimateTypeDB_DAO(dbConnection);
	}

	@After
	public void tearDown() throws Exception {
		estimateTypeDB_DAO = null;
	}

	@Test
	public void testEstimateTypeDB_DAO() {
		estimateTypeDB_DAO = new EstimateTypeDB_DAO(dbConnection);
		assertNotNull("estimateTypeDB_DAO object should not be null",estimateTypeDB_DAO);
	}

	@Test
	public void testGetAllEstimateTypes() throws QueryException {
		ArrayList actualReturn = estimateTypeDB_DAO.getAllEstimateTypes();
		assertEquals("Should have 6 estimate types in the table", 6, actualReturn.size());
	}

	@Test
	public void testGetEstimateTypeById() throws QueryException {
		EstimateType actualReturn = estimateTypeDB_DAO.getEstimateType(1);
		assertEquals("NormalEstimate",actualReturn.getEstimateName());
		actualReturn = estimateTypeDB_DAO.getEstimateType(2);
		assertEquals("LogNormalEstimate",actualReturn.getEstimateName());
		actualReturn = estimateTypeDB_DAO.getEstimateType(3);
		assertEquals("PDF_Estimate",actualReturn.getEstimateName());
		actualReturn = estimateTypeDB_DAO.getEstimateType(4);
		assertEquals("FractileListEstimate",actualReturn.getEstimateName());
		actualReturn = estimateTypeDB_DAO.getEstimateType(5);
		assertEquals("IntegerEstimate",actualReturn.getEstimateName());
		actualReturn = estimateTypeDB_DAO.getEstimateType(6);
		assertEquals("DiscreteValueEstimate",actualReturn.getEstimateName());
	}

	@Test
	public void testGetEstimateTypeByName() throws QueryException {
		EstimateType actualReturn = estimateTypeDB_DAO.getEstimateType("NormalEstimate");
		assertEquals(1,actualReturn.getEstimateTypeId());
		actualReturn = estimateTypeDB_DAO.getEstimateType("LogNormalEstimate");
		assertEquals(2,actualReturn.getEstimateTypeId());
		actualReturn = estimateTypeDB_DAO.getEstimateType("PDF_Estimate");
		assertEquals(3,actualReturn.getEstimateTypeId());
		actualReturn = estimateTypeDB_DAO.getEstimateType("FractileListEstimate");
		assertEquals(4,actualReturn.getEstimateTypeId());
		actualReturn = estimateTypeDB_DAO.getEstimateType("IntegerEstimate");
		assertEquals(5,actualReturn.getEstimateTypeId());
		actualReturn = estimateTypeDB_DAO.getEstimateType("DiscreteValueEstimate");
		assertEquals(6,actualReturn.getEstimateTypeId());
	}


}
