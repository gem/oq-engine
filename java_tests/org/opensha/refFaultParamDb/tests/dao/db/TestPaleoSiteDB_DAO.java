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
import org.opensha.refFaultParamDb.dao.db.PaleoSiteDB_DAO;
import org.opensha.refFaultParamDb.dao.db.SiteTypeDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
import org.opensha.refFaultParamDb.tests.AllTests;
import org.opensha.refFaultParamDb.vo.Contributor;
import org.opensha.refFaultParamDb.vo.PaleoSite;
import org.opensha.refFaultParamDb.vo.SiteType;
/**
 *
 * <p>Title: TestPaleoSiteDB_DAO.java </p>
 * <p>Description: Test the Paleo Site DB DAO class</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */
public class TestPaleoSiteDB_DAO {
	private DB_AccessAPI dbConnection;
	private ContributorDB_DAO contributorDB_DAO = null;
	private SiteTypeDB_DAO siteTypeDB_DAO = null;
	private PaleoSiteDB_DAO paleoSiteDB_DAO = null;
	private static int contributorKey1, siteTypeKey1, siteTypeKey2;

	public TestPaleoSiteDB_DAO() {
		dbConnection = AllTests.dbConnection;
	}

	@Before
	public void setUp() throws Exception {
		contributorDB_DAO = new ContributorDB_DAO(dbConnection);
		siteTypeDB_DAO = new SiteTypeDB_DAO(dbConnection);
		paleoSiteDB_DAO = new PaleoSiteDB_DAO(dbConnection);
	}

	@After
	public void tearDown() throws Exception {
		contributorDB_DAO = null;
		siteTypeDB_DAO=null;
		paleoSiteDB_DAO = null;
	}

	@Test
	public void testPaleoSiteDB_DAO() {
		paleoSiteDB_DAO = new PaleoSiteDB_DAO(dbConnection);
		assertNotNull("paleoSiteDB_DAO object should not be null",paleoSiteDB_DAO);
	}

	@Test
	public void testAddPaleoSite() throws InsertException {
		Contributor contributor1 = new Contributor("Test1");
		contributorKey1 = contributorDB_DAO.addContributor(contributor1,"testpass1");
		contributor1.setId(contributorKey1);
		SiteType siteType1 = new SiteType("geologic",contributor1,"Comments1");
		SiteType siteType3 = new SiteType("paleosite",contributor1,"Comments2");

		siteTypeKey1 = siteTypeDB_DAO.addSiteType(siteType1);
		siteType1.setSiteTypeId(siteTypeKey1);
		siteTypeKey2 = siteTypeDB_DAO.addSiteType(siteType3);
		siteType3.setSiteTypeId(siteTypeKey2);

		// paleo site 1
		PaleoSite paleoSite = new PaleoSite();
		paleoSite.setSiteId(1);
		ArrayList siteTypes = new ArrayList();
		siteTypes.add(siteType1.getSiteType());
		//paleoSite.setSiteTypeNames(siteTypes);
		paleoSite.setSiteName("Test1");
		paleoSite.setSiteLat1(32.1f);
		paleoSite.setSiteLon1(-117.0f);
		paleoSite.setSiteElevation1(0.5f);
		//paleoSite.setRepresentativeStrandName("Most Significant Strand");
		paleoSite.setGeneralComments("Test comments");
		paleoSite.setOldSiteId("55-2");

		paleoSiteDB_DAO.addPaleoSite(paleoSite);

		try {
			paleoSite.setSiteId(2);
			Contributor contributor2 = new Contributor(2,"Test1");
			paleoSiteDB_DAO.addPaleoSite(paleoSite);
			fail("should not insert this paleosite as contributor id 2 does not exist in contributor table");
		}catch(InsertException e) {}

		try {
			SiteType siteType2 = new SiteType(2,"paleosite",contributor1,"TestComments1");
			ArrayList siteTypes2 = new ArrayList();
			siteTypes2.add(siteType2.getSiteType());
			//paleoSite.setSiteTypeNames(siteTypes2);
			paleoSiteDB_DAO.addPaleoSite(paleoSite);
			fail("should not insert this paleosite as site type id 2 does not exist in sitetype table");
		}catch(InsertException e) {}

		paleoSite.setSiteId(3);
		ArrayList siteTypes3 = new ArrayList();
		siteTypes3.add(siteType3.getSiteType());
		//paleoSite.setSiteTypeNames(siteTypes3);
		paleoSiteDB_DAO.addPaleoSite(paleoSite);
	}

	@Test
	public void testGetPaleoSites() throws QueryException {
		ArrayList actualReturn = paleoSiteDB_DAO.getAllPaleoSites();
		assertEquals("Should have 2 paleoSites in the table", 2, actualReturn.size());
	}

	@Test
	public void testGetPaleoSite() throws QueryException {
		PaleoSite actualReturn ;
		assertNull("No paleoSite exists with id 2",  paleoSiteDB_DAO.getPaleoSite(2));
		actualReturn = (PaleoSite)paleoSiteDB_DAO.getPaleoSite(1);
		assertNotNull("should not be null as paloeSite exists with id = 1",actualReturn);

		//paleoSite.setEffectiveDate(new java.util.Date());
		assertEquals(1, actualReturn.getSiteId());
		//assertEquals("geologic", (String)actualReturn.getSiteTypeNames().get(0));
		assertEquals("Test1",actualReturn.getSiteName());
		assertEquals(32.1,actualReturn.getSiteLat1(),.0001);
		assertEquals(-117.0,actualReturn.getSiteLon1(),.0001);
		assertEquals(0.5,actualReturn.getSiteElevation1(),.0001);
		//assertEquals("Most Significant Strand", actualReturn.getRepresentativeStrandName());
		assertEquals("Test comments", actualReturn.getGeneralComments());
		assertEquals("1", actualReturn.getOldSiteId());
	}

	@Test
	public void testRemovePaleoSite() throws UpdateException {
		boolean status = paleoSiteDB_DAO.removePaleoSite(2);
		assertFalse("cannot remove paleo site with 2 as it does not exist", status);
		status =  paleoSiteDB_DAO.removePaleoSite(3);
		assertTrue("paleoSite with id=3 should be removed from the database",status);
		assertEquals("should now contain only 1 paleoSite",1, paleoSiteDB_DAO.getAllPaleoSites().size());
		status=paleoSiteDB_DAO.removePaleoSite(1);
		assertTrue("paleosite with id=1 should be removed from the database",status);
		assertEquals("should now contain only 0 paleosite",0, paleoSiteDB_DAO.getAllPaleoSites().size());
		siteTypeDB_DAO.removeSiteType(siteTypeKey1);
		siteTypeDB_DAO.removeSiteType(siteTypeKey2);
		contributorDB_DAO.removeContributor(contributorKey1);

	}
}
