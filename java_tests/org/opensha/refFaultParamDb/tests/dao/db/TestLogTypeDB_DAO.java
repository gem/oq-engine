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
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.LogTypeDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.tests.AllTests;
/**
 *
 * <p>Title: TestLogTypeDB_DAO.java </p>
 * <p>Description: Test the LogType DB DAO class</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */
public class TestLogTypeDB_DAO {
	private DB_AccessAPI dbConnection;
	private LogTypeDB_DAO logTypeDB_DAO = null;

	public TestLogTypeDB_DAO() {
		dbConnection = AllTests.dbConnection;
	}

	@Before
	public void setUp() throws Exception {
		logTypeDB_DAO = new LogTypeDB_DAO(dbConnection);
	}

	@After
	public void tearDown() throws Exception {
		logTypeDB_DAO = null;
	}

	@Test
	public void testLogTypeDB_DAO() {
		logTypeDB_DAO = new LogTypeDB_DAO(dbConnection);
		assertNotNull("logTypeDB_DAO object should not be null",logTypeDB_DAO);
	}

	@Test
	public void testGetLogType() throws QueryException {
		int actualReturn = logTypeDB_DAO.getLogTypeId("12");
		assertEquals( -1, actualReturn);
		actualReturn = logTypeDB_DAO.getLogTypeId("10");
		assertEquals( 1, actualReturn);
		actualReturn = logTypeDB_DAO.getLogTypeId("E");
		assertEquals( 2, actualReturn);
		actualReturn = logTypeDB_DAO.getLogTypeId("e");
		assertEquals( -1, actualReturn);
		String logBase = logTypeDB_DAO.getLogBase(1);
		assertEquals("10",logBase);
		logBase = logTypeDB_DAO.getLogBase(2);
		assertEquals("E",logBase);
	}

}
