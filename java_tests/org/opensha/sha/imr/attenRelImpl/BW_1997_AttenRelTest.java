package org.opensha.sha.imr.attenRelImpl;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import junit.framework.TestCase;

public class BW_1997_AttenRelTest extends TestCase {
	BW_1997_AttenRel bw_1997_AttenRel;
	
	@Before
	public void setUp() {
		BW_1997_AttenRel bw_1997_AttenRel = new BW_1997_AttenRel();	
	} // setUp()

	@After
	public void tearDown() {}
	
	@Test
	public void testCallMethods() {
		int magnitude = 5;
		int epicentralDistance = 1;
		assertTrue("Results must be congruent with Damiano's spread sheet",
				9.52 == bw_1997_AttenRel.getMean(magnitude, epicentralDistance));
	} // testCallMethods
} // class TestCase
