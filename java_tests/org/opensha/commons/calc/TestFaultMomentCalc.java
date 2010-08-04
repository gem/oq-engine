package org.opensha.commons.calc;

import static org.junit.Assert.*;

import org.junit.Test;
import org.opensha.commons.util.DataUtils;


public class TestFaultMomentCalc {

	public TestFaultMomentCalc() {
	}

	@Test
	public void testGetMoment() {
		assertTrue(FaultMomentCalc.getMoment(1, 1) == 3e10);
		assertTrue(FaultMomentCalc.getMoment(1, 5) == 1.5e11);
		assertTrue(FaultMomentCalc.getMoment(10, 1) == 3e11);
		assertTrue(FaultMomentCalc.getMoment(10, 5) == 1.5e12);
		assertTrue(FaultMomentCalc.getMoment(100, 1) == 3e12);
		assertTrue(FaultMomentCalc.getMoment(100, 5) == 1.5e13);
	}
	
	@Test
	public void testGetSlip() {
		assertTrue(FaultMomentCalc.getSlip(1, 3e10) == 1d);
		assertTrue(FaultMomentCalc.getSlip(1, 1.5e11) == 5d);
		assertTrue(FaultMomentCalc.getSlip(10, 3e11) == 1d);
		assertTrue(FaultMomentCalc.getSlip(10, 1.5e12) == 5d);
		assertTrue(FaultMomentCalc.getSlip(100, 3e12) == 1d);
		assertTrue(FaultMomentCalc.getSlip(100, 1.5e13) == 5d);
	}
	
	@Test
	public void testSlipFromMoment() {
		int tests = 0;
		for (double area=1.0; area<10000d; area*=1.25) {
			for (double slip=0.1; slip<10; slip+=0.1) {
				double moment = FaultMomentCalc.getMoment(area, slip);
				double calcSlip = FaultMomentCalc.getSlip(area, moment);
				assertTrue((float)slip == (float)calcSlip);
				tests++;
			}
		}
		System.out.println("Tested " + tests + " points");
	}
	
	@Test
	public void testMomentFromSlip() {
		int tests = 0;
		for (double area=1.0; area<10000d; area*=1.25) {
			for (double moment=3e9; moment<10e15; moment*=1.25) {
				double slip = FaultMomentCalc.getSlip(area, moment);
				double calcMoment = FaultMomentCalc.getMoment(area, slip);
				assertTrue(DataUtils.getPercentDiff(calcMoment, moment) < 0.01);
				tests++;
			}
		}
		System.out.println("Tested " + tests + " points");
	}

}

