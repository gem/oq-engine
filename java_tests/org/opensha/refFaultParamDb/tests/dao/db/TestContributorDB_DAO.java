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
import org.opensha.refFaultParamDb.dao.db.ContributorDB_DAO;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
import org.opensha.refFaultParamDb.tests.AllTests;
import org.opensha.refFaultParamDb.vo.Contributor;
/**
 *
 * <p>Title: TestContributorDB_DAO.java </p>
 * <p>Description: Test the Contributor DB DAO class</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */
public class TestContributorDB_DAO {
	private DB_AccessAPI dbConnection ;
	private ContributorDB_DAO contributorDB_DAO = null;
	private static int primaryKey1, primaryKey2;

	public TestContributorDB_DAO() {
		dbConnection = AllTests.dbConnection;
	}

	@Before
	public void setUp() throws Exception {
		contributorDB_DAO = new ContributorDB_DAO(dbConnection);
	}

	@After
	public void tearDown() throws Exception {
		contributorDB_DAO = null;
	}

	@Test
	public void testContributorDB_DAO() {
		contributorDB_DAO = new ContributorDB_DAO(dbConnection);
		assertNotNull("contributor_DAO object should not be null",contributorDB_DAO);
	}

	@Test
	public void testAddContributor() throws InsertException {
		Contributor contributor1 = new Contributor("Test1");
		Contributor contributor2 = new Contributor("Test2");
		Contributor contributor3 = new Contributor("Test3");
		primaryKey1 = contributorDB_DAO.addContributor(contributor1,"testPass1");
		primaryKey2 = contributorDB_DAO.addContributor(contributor3,"testPass3");
		assertTrue(primaryKey1!=primaryKey2);
	}

	@Test
	public void testGetAllContributors() throws QueryException {
		ArrayList actualReturn = contributorDB_DAO.getAllContributors();
		assertEquals("Should have 2 contributors in the table", 2, actualReturn.size());
	}

	@Test
	public void testGetContributor() throws QueryException {
		Contributor actualReturn = contributorDB_DAO.getContributor(67866);
		assertEquals("No contributor exists with id 67866", null, actualReturn);
		actualReturn = contributorDB_DAO.getContributor(primaryKey1);
		assertNotNull("should not be null as contributor exists with id = "+primaryKey1,actualReturn);
		assertEquals("Test1", actualReturn.getName());
	}

	@Test
	public void testRemoveContributor() throws UpdateException {
		boolean status = contributorDB_DAO.removeContributor(7878);
		assertFalse("cannot remove contributor with 7878 as it does not exist", status);
		status = contributorDB_DAO.removeContributor(primaryKey2);
		assertTrue("contributor with id="+primaryKey2+" should be removed from the database",status);
		assertEquals("should now contain only 1 contributor",1, contributorDB_DAO.getAllContributors().size());
		status=contributorDB_DAO.removeContributor(primaryKey1);
		assertTrue("contributor with id="+primaryKey1+" should be removed from the database",status);
		assertEquals("should now contain only 0 contributor",0, contributorDB_DAO.getAllContributors().size());
	}
}
