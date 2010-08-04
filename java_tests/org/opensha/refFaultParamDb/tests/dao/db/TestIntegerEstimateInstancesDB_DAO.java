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

import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.estimate.IntegerEstimate;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.EstimateInstancesDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
import org.opensha.refFaultParamDb.tests.AllTests;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
/**
 *
 * <p>Title: TestIntegerEstimateInstancesDB_DAO.java </p>
 * <p>Description: Test the Estimate Instances DB DAO</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */
public class TestIntegerEstimateInstancesDB_DAO {
	private DB_AccessAPI dbConnection;
	private EstimateInstancesDB_DAO estimateInstancesDB_DAO = null;
	static int primaryKey1, primaryKey2;

	public TestIntegerEstimateInstancesDB_DAO() {
		dbConnection = AllTests.dbConnection;
	}

	@Before
	public void setUp() throws Exception {
		estimateInstancesDB_DAO = new EstimateInstancesDB_DAO(dbConnection);
	}

	@Before
	public void tearDown() throws Exception {
		estimateInstancesDB_DAO = null;
	}

	@Test
	public void testIntegerEstimateInstancesDB_DAO() {
		estimateInstancesDB_DAO = new EstimateInstancesDB_DAO(dbConnection);
		assertNotNull("estimateInstancesDB_DAO object should not be null",estimateInstancesDB_DAO);
	}

	@Test
	public void testAddIntegerEstimateInstance() throws InsertException {
		ArbitrarilyDiscretizedFunc func1 = new ArbitrarilyDiscretizedFunc();

		func1.set(2.0,0.0);
		func1.set(1.0,0.0);
		ArbitrarilyDiscretizedFunc func2 = new ArbitrarilyDiscretizedFunc();
		func2.set(1.0,0.0);
		func2.set(4.0,9.0);
		func2.set(8.0,0.0);

		IntegerEstimate estimate1 = new IntegerEstimate(func1,false);
		IntegerEstimate estimate2 = new IntegerEstimate(func2,false);
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
	public void testGetIntegerEstimateInstance() throws QueryException {
		EstimateInstances actualReturn = estimateInstancesDB_DAO.getEstimateInstance(4546);
		assertEquals("No estimate exists with id 4546", null, actualReturn);

		actualReturn = estimateInstancesDB_DAO.getEstimateInstance(primaryKey1);
		assertNotNull("should not be null as estimate exists with id ="+primaryKey1,actualReturn);
		IntegerEstimate estimate  = (IntegerEstimate)actualReturn.getEstimate();
		DiscretizedFuncAPI func1 =  estimate.getValues();
		assertEquals(1, (int)func1.getX(0));
		assertEquals(0, (int)func1.getY(0));
		assertEquals(2, (int)func1.getX(1));
		assertEquals(0, (int)func1.getY(1));
		assertEquals("meters", actualReturn.getUnits());

		actualReturn = estimateInstancesDB_DAO.getEstimateInstance(primaryKey2);
		assertNotNull("should not be null as estimate exists with id ="+primaryKey2,actualReturn);
		estimate  = (IntegerEstimate)actualReturn.getEstimate();
		DiscretizedFuncAPI func2 =  estimate.getValues();
		assertEquals(1, (int)func2.getX(0));
		assertEquals(0, (int)func2.getY(0));
		assertEquals(4, (int)func2.getX(1));
		assertEquals(9, (int)func2.getY(1));
		assertEquals(8, (int)func2.getX(2));
		assertEquals(0, (int)func2.getY(2));
		assertEquals("meters", actualReturn.getUnits());


	}

	@Test
	public void testRemoveIntegerEstimateInstance() throws UpdateException {
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
