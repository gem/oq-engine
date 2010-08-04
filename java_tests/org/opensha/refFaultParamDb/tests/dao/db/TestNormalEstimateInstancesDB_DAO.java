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

import static org.junit.Assert.*;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.estimate.NormalEstimate;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.EstimateInstancesDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
import org.opensha.refFaultParamDb.tests.AllTests;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
/**
 *
 * <p>Title: TestNormalEstimateInstancesDB_DAO.java </p>
 * <p>Description: Test the Estimate Instances DB DAO</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */
public class TestNormalEstimateInstancesDB_DAO {
	private DB_AccessAPI dbConnection;
	private EstimateInstancesDB_DAO estimateInstancesDB_DAO = null;
	static int primaryKey1, primaryKey2;

	public TestNormalEstimateInstancesDB_DAO() {
		dbConnection = AllTests.dbConnection;
	}

	@Before
	public void setUp() throws Exception {
		estimateInstancesDB_DAO = new EstimateInstancesDB_DAO(dbConnection);
	}

	@After
	public void tearDown() throws Exception {
		estimateInstancesDB_DAO = null;
	}

	@Test
	public void testNormalEstimateInstancesDB_DAO() {
		estimateInstancesDB_DAO = new EstimateInstancesDB_DAO(dbConnection);
		assertNotNull("estimateInstancesDB_DAO object should not be null",estimateInstancesDB_DAO);
	}

	@Test
	public void testAddNormalEstimateInstance() throws InsertException {
		NormalEstimate estimate1 = new NormalEstimate(5, 2);
		NormalEstimate estimate2 = new NormalEstimate(3, 5);
		EstimateInstances estimateInstance = new EstimateInstances();
		estimateInstance.setEstimate(estimate1);
		estimateInstance.setUnits("meters");
		primaryKey1 = estimateInstancesDB_DAO.addEstimateInstance(estimateInstance);
		estimateInstance.setEstimate(estimate2);
		primaryKey2 = estimateInstancesDB_DAO.addEstimateInstance(estimateInstance);
		assertTrue(primaryKey1!=primaryKey2);
		assertEquals("there should be 2 estimate instances", 2, estimateInstancesDB_DAO.getAllEstimateInstances().size());
	}

	@Test
	public void testGetNormalEstimateInstance() throws QueryException {
		EstimateInstances actualReturn = estimateInstancesDB_DAO.getEstimateInstance(4546);
		assertEquals("No estimate exists with id 4546", null, actualReturn);

		actualReturn = estimateInstancesDB_DAO.getEstimateInstance(primaryKey1);
		assertNotNull("should not be null as estimate exists with id ="+primaryKey1,actualReturn);
		NormalEstimate estimate  = (NormalEstimate)actualReturn.getEstimate();
		assertEquals(5, estimate.getMean(),0.000001);
		assertEquals(2, estimate.getStdDev(),0.000001);
		assertEquals("meters", actualReturn.getUnits());

		actualReturn = estimateInstancesDB_DAO.getEstimateInstance(primaryKey2);
		assertNotNull("should not be null as estimate exists with id ="+primaryKey2,actualReturn);
		estimate  = (NormalEstimate)actualReturn.getEstimate();
		assertEquals(3, estimate.getMean(),0.000001);
		assertEquals(5, estimate.getStdDev(),0.000001);
		assertEquals("meters", actualReturn.getUnits());

	}

	@Test
	public void testRemoveNormalEstimateInstance() throws UpdateException {
		boolean status = estimateInstancesDB_DAO.removeEstimateInstance(5225);
		assertFalse("cannot remove estimate with 5225 as it does not exist", status);
		assertEquals("there should be 2 estimate instances", 2, estimateInstancesDB_DAO.getAllEstimateInstances().size());
		status = estimateInstancesDB_DAO.removeEstimateInstance(primaryKey1);
		assertTrue(status);
		assertEquals("there should be 1 estimate instance", 1, estimateInstancesDB_DAO.getAllEstimateInstances().size());
		status = estimateInstancesDB_DAO.removeEstimateInstance(primaryKey2);
		assertTrue(status);
		assertEquals("there should be 0 estimate instances", 0, estimateInstancesDB_DAO.getAllEstimateInstances().size());

	}
}
