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

package org.opensha.sha.calc.IM_EventSet.v03.test;

import static org.junit.Assert.*;

import org.junit.Test;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetOutputWriter;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

public class IMT_String_Test {
	
	private CB_2008_AttenRel cb08 = new CB_2008_AttenRel(null);

	public IMT_String_Test() {
	}
	
	private void checkIsSetCorrectly(double period) {
		ParameterAPI<?> imt = cb08.getIntensityMeasure();
		assertEquals(SA_Param.NAME, imt.getName());
		assertTrue(imt instanceof DependentParameterAPI);
		DependentParameterAPI<?> depIMT = (DependentParameterAPI<?>)imt;
		ParameterAPI<?> periodParam = depIMT.getIndependentParameter(PeriodParam.NAME);
		double imtPer = (Double)periodParam.getValue();
		System.out.println("got: " + imtPer + " sec, expecting: " + period + " sec");
		assertEquals(period, imtPer, 0);
	}
	
	private void doTestPeriod(String imtStr, double imtPeriod) {
		IM_EventSetOutputWriter.setIMTFromString(imtStr, cb08);
		checkIsSetCorrectly(imtPeriod);
		String newStr = IM_EventSetOutputWriter.getHAZ01IMTString(cb08.getIntensityMeasure());
		assertEquals(imtStr, newStr);
	}
	
	@Test
	public void test0_1Sec() {
		doTestPeriod("SA01", 0.1);
	}
	
	@Test
	public void test0_25Sec() {
		doTestPeriod("SA025", 0.25);
	}
	
	@Test
	public void test0_5Sec() {
		doTestPeriod("SA05", 0.5);
	}
	
	@Test
	public void test1Sec() {
		doTestPeriod("SA1", 1.0);
	}
	
	@Test
	public void test1_5Sec() {
		doTestPeriod("SA15", 1.5);
	}
	
	@Test
	public void test5Sec() {
		doTestPeriod("SA50", 5.0);
	}
	
	@Test
	public void test10Sec() {
		doTestPeriod("SA100", 10.0);
	}

}
