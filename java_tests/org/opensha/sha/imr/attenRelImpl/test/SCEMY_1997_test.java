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

package org.opensha.sha.imr.attenRelImpl.test;

import static org.junit.Assert.*;

import java.io.IOException;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel;







/**
 *
 * <p>Title:SCEMY_1997_test </p>
 * <p>Description: Checks for the proper implementation of the SCEMY_1997_AttenRel
 * class.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Ned Field, Nitin Gupta & Vipin Gupta
 * @version 1.0
 */
public class SCEMY_1997_test implements ParameterChangeWarningListener {


	SadighEtAl_1997_AttenRel scemy_1997 = null;
	//Tolerence to check if the results fall within the range.
	private static double tolerence = .01; //default value for the tolerence

	private static final String RESULT_SET_PATH = "/org/opensha/sha/imr/attenRelImpl/test/AttenRelResultSetFiles/";
	private static final String SADIGH_1997_RESULTS = RESULT_SET_PATH +"SADIGH.txt";

	//Instance of the class that does the actual comparison for the AttenuationRelationship classes
	AttenRelResultsChecker attenRelChecker;

	public SCEMY_1997_test() {
	}

	@Before
	public void setUp() {
		// create the instance of the SCEMY_1997
		scemy_1997 = new SadighEtAl_1997_AttenRel(this);
		attenRelChecker = new AttenRelResultsChecker(scemy_1997,SADIGH_1997_RESULTS,tolerence);
	}

	@After
	public void tearDown() {
	}

	@Test
	public void testSCEMY1997Creation() throws IOException {

		boolean result =attenRelChecker.readResultFile();

		/**
		 * If any test for the SCEMY failed
		 */
		if(result == false)
			assertNull(attenRelChecker.getFailedTestParamsSettings(),attenRelChecker.getFailedTestParamsSettings());

		//if the all the succeeds and their is no fail for any test
		else {
			assertTrue("SCEMY-1997 Test succeeded for all the test cases",result);
		}
	}

	public void parameterChangeWarning(ParameterChangeWarningEvent e){
		return;
	}


	/**
	 * Run the test case
	 * @param args
	 */

	public static void main (String[] args)
	{
		org.junit.runner.JUnitCore.runClasses(SCEMY_1997_test.class);
	}

}
