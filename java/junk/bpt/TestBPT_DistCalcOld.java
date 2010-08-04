package junk.bpt;


import static org.junit.Assert.*;

import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.util.DataUtils;


public class TestBPT_DistCalcOld {

	double timeSinceLast = 96;
	double nYr = 30;
	double alph = 0.5;
	double[] rate = {0.00466746464,0.00432087015,0.004199435,0.004199435};
	double[] prob = {0.130127236,0.105091952,0.0964599401,0.0964599401};
	double[] static_prob;
	
	@Before
	public void setUp() throws Exception {
		static_prob = new double[rate.length];
		for(int i=0;i<rate.length;i++) {
			static_prob[i] = BPT_DistCalcOld.getCondProb(1/rate[i],alph, timeSinceLast, nYr);
		}
	}
	
	@Test
	public void testStaticWG02() {
		System.out.println("Test1: comparison with probs from WG02 code");
		for(int i=0;i<rate.length;i++) {
			double diff = DataUtils.getPercentDiff(static_prob[i], prob[i]);
			assertTrue(diff <= 0.5);
		}
	}
	
	@Test
	public void testFastAgainstStatic() {
		// Test2 (faster method based on pre-computed & saved function)
		double p;
		BPT_DistCalcOld calc = new BPT_DistCalcOld(0.5);
		for(int i=0;i<rate.length;i++) {
			p = calc.getCondProb(timeSinceLast,rate[i],nYr);
			double diff = org.opensha.commons.util.DataUtils.getPercentDiff(p, static_prob[i]);
//			System.out.println("DIFF: " + diff);
			assertTrue(diff <= 0.5);
		}
	}
	
	@Test
	public void testDelta0_01() {
		// Test2 (faster method based on pre-computed & saved function)
		double p;
		BPT_DistCalcOld calc = new BPT_DistCalcOld(0.5);
		calc.setDelta(0.01);
		for(int i=0;i<rate.length;i++) {
			p = calc.getCondProb(timeSinceLast,rate[i],nYr);
			double diff = org.opensha.commons.util.DataUtils.getPercentDiff(p, static_prob[i]);
//			System.out.println("DIFF: " + diff);
			assertTrue(diff <= 0.5);
		}
	}

}
