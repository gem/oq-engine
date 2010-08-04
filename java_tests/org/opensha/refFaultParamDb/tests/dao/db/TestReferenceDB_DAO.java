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
import org.opensha.refFaultParamDb.dao.db.ReferenceDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
import org.opensha.refFaultParamDb.tests.AllTests;
import org.opensha.refFaultParamDb.vo.Reference;
/**
 *
 * <p>Title: TestReferenceDB_DAO.java </p>
 * <p>Description: Test the Reference DB DAO class</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */
public class TestReferenceDB_DAO {
	private DB_AccessAPI dbConnection;
	private ReferenceDB_DAO referenceDB_DAO = null;
	private static int primaryKey1, primaryKey2;

	public TestReferenceDB_DAO() {
		dbConnection = AllTests.dbConnection;
	}

	@Before
	public void setUp() throws Exception {
		referenceDB_DAO = new ReferenceDB_DAO(dbConnection);
	}

	@After
	public void tearDown() throws Exception {
		referenceDB_DAO = null;
	}

	@Test
	public void testReferenceDB_DAO() {
		referenceDB_DAO = new ReferenceDB_DAO(dbConnection);
		assertNotNull("reference_DAO object should not be null",referenceDB_DAO);
	}

	@Test
	public void testAddReference() throws InsertException {
		Reference reference1 = new Reference("Test1","2005", "FullBiblio1");
		Reference reference2 = new Reference("Test2","2005", "FullBiblio2");
		Reference reference3 = new Reference("Test3","2005", "FullBiblio3");
		primaryKey1 = referenceDB_DAO.addReference(reference1);
		primaryKey2 = referenceDB_DAO.addReference(reference3);
		assertTrue(primaryKey1!=primaryKey2);
	}

	@Test
	public void testGetAllReferences() throws QueryException {
		ArrayList actualReturn = referenceDB_DAO.getAllReferences();
		assertEquals("Should have 2 references in the table", 2, actualReturn.size());
	}

	@Test
	public void testGetReference() throws QueryException {
		Reference actualReturn = referenceDB_DAO.getReference(67866);
		assertEquals("No reference exists with id 67866", null, actualReturn);
		actualReturn = referenceDB_DAO.getReference(primaryKey1);
		assertNotNull("should not be null as reference exists with id = "+primaryKey1,actualReturn);
		assertEquals("Test1", actualReturn.getRefAuth());
		assertEquals("FullBiblio1", actualReturn.getFullBiblioReference());
	}

	@Test
	public void testUpdateReference() throws UpdateException {
		Reference reference = new Reference(7879,"Test2","2005", "Bib2");
		boolean status  = referenceDB_DAO.updateReference(7879, reference);
		assertFalse("cannot update reference with 7879 as it does not exist", status);
		reference = new Reference(primaryKey1,"TestTest1","2005", "Bib2");
		status = referenceDB_DAO.updateReference(primaryKey1, reference);
		assertTrue("reference with id="+primaryKey1+ " should be updated in the database",status);
		Reference actualReturn = referenceDB_DAO.getReference(primaryKey1);
		assertNotNull("should not be null as reference exists with id = "+primaryKey1,actualReturn);
		assertEquals("reference id "+primaryKey1+" has short name test 1", "TestTest1", actualReturn.getRefAuth());
		assertEquals("reference id "+primaryKey1+" has full biibliographic name Bib2", "Bib2", actualReturn.getFullBiblioReference());
	}

	@Test
	public void testRemoveReference() throws UpdateException {
		boolean status = referenceDB_DAO.removeReference(7878);
		assertFalse("cannot remove reference with 7878 as it does not exist", status);
		status = referenceDB_DAO.removeReference(primaryKey2);
		assertTrue("reference with id="+primaryKey2+" should be removed from the database",status);
		assertEquals("should now contain only 1 reference",1, referenceDB_DAO.getAllReferences().size());
		status=referenceDB_DAO.removeReference(primaryKey1);
		assertTrue("reference with id="+primaryKey1+" should be removed from the database",status);
		assertEquals("should now contain only 0 reference",0, referenceDB_DAO.getAllReferences().size());
	}
}
