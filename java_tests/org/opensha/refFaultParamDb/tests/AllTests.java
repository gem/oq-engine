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

package org.opensha.refFaultParamDb.tests;

import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;

public class AllTests {

	public static DB_AccessAPI dbConnection = DB_ConnectionPool.getLatestReadOnlyConn();

	//  public AllTests(String s) {
	//    super(s);
	//  }
	//
	//  public static Test suite() {
	//    TestSuite suite = new TestSuite();
	//    /*suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestContributorDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestSiteTypeDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.Test_QFault2002B_DB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestPaleoSiteDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestEstimateTypeDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestNormalEstimateInstancesDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestLogTypeDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestLogNormalEstimateInstancesDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestIntegerEstimateInstancesDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestFractileListEstimateInstancesDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestDiscreteValueEstimateInstancesDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestReferenceDB_DAO.class);
	//    suite.addTestSuite(org.opensha.refFaultParamDb.tests.dao.db.TestFaultModelDB_DAO.class);*/
	//    return suite;
	//  }
}
