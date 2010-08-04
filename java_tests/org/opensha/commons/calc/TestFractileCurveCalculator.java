package org.opensha.commons.calc;

import static org.junit.Assert.*;

import java.util.ArrayList;

import org.junit.Test;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;

public class TestFractileCurveCalculator {
	
	public static DiscretizedFuncList getGoodTestData() {
		DiscretizedFuncList list = new DiscretizedFuncList();
		
		ArbitrarilyDiscretizedFunc func1 = new ArbitrarilyDiscretizedFunc();
		ArbitrarilyDiscretizedFunc func2 = new ArbitrarilyDiscretizedFunc();
		ArbitrarilyDiscretizedFunc func3 = new ArbitrarilyDiscretizedFunc();
		
		for (int x=0; x<20; x++) {
			func1.set((double)x, (double)x);
			func2.set((double)x, 1.);
			func3.set((double)x, (double)(20 - x));
		}
		
		list.add(func1);
		list.add(func2);
		list.add(func3);
		
		return list;
	}
	
	public static DiscretizedFuncList getBaddTestData() {
		DiscretizedFuncList list = new DiscretizedFuncList();
		
		ArbitrarilyDiscretizedFunc func1 = new ArbitrarilyDiscretizedFunc();
		ArbitrarilyDiscretizedFunc func2 = new ArbitrarilyDiscretizedFunc();
		ArbitrarilyDiscretizedFunc func3 = new ArbitrarilyDiscretizedFunc();
		
		func1.set(0.0, 5.);
		func1.set(2.0, 2.);
		func1.set(4.0, 6.);
		
		func2.set(0.0, 23.);
		func2.set(2.0, 8.);
		
		func3.set(19.0, 5.);
		
		list.add(func1);
		list.add(func2);
		list.add(func3);
		
		return list;
	}
	
	public static ArrayList<Double> getGoodWeights() {
		ArrayList<Double> wts = new ArrayList<Double>();
		
		wts.add(15.);
		wts.add(5.);
		wts.add(20.);
		
		return wts;
	}
	
	public static ArrayList<Double> getNormalizedWeights() {
		ArrayList<Double> wts = new ArrayList<Double>();
		
		wts.add(0.375);	// 15 / 40
		wts.add(0.125);	// 05 / 40
		wts.add(0.5);	// 20 / 40
		
		return wts;
	}
	
	public static ArrayList<Double> getBadWeights() {
		ArrayList<Double> wts = new ArrayList<Double>();
		
		wts.add(5.);
		wts.add(20.);
		
		return wts;
	}
	
	@Test
	public void testSet() {
		DiscretizedFuncList goodList = getGoodTestData();
		DiscretizedFuncList badList = getBaddTestData();
		
		ArrayList<Double> goodWts = getGoodWeights();
		ArrayList<Double> badWts = getBadWeights();
		
		try {
			new FractileCurveCalculator(goodList, null);
			fail("Giving null weights should throw a NullPointerException");
		} catch (NullPointerException e) {}
		
		try {
			new FractileCurveCalculator(null, goodWts);
			fail("Giving a null func list should throw a NullPointerException");
		} catch (NullPointerException e) {}
		
		try {
			new FractileCurveCalculator(goodList, badWts);
			fail("Should check to verify function list and wieght list are same size");
		} catch (RuntimeException e) {}
		
		try {
			new FractileCurveCalculator(badList, goodWts);
			fail("Should check to verify function list has equal sized functions");
		} catch (RuntimeException e) {}
		
		try {
			new FractileCurveCalculator(goodList, goodWts);
		} catch (Exception e) {
			// should work
			e.printStackTrace();
			fail("Exception even with good data!");
		}
	}

	@Test
	public void testGetMeanCurve() {
		FractileCurveCalculator calc = new FractileCurveCalculator(getGoodTestData(), getGoodWeights());
		ArbitrarilyDiscretizedFunc func = calc.getMeanCurve();
		calc.set(getGoodTestData(), getNormalizedWeights());
		ArbitrarilyDiscretizedFunc normFunc = calc.getMeanCurve();
//		System.out.println(func);
		for (int x=0; x<20; x++) {
			double expectedY = 10.125 - (x * 0.125);
			double actualY = func.getY(x);
			assertEquals(expectedY, actualY, 0.0);
			
			// you shouldn't have to normalize your weights yourself, so these should match
			double normY = normFunc.getY(x);
			assertEquals(actualY, normY, 0.0);
		}
	}

	@Test
	public void testGetFractile() {
		FractileCurveCalculator calc = new FractileCurveCalculator(getGoodTestData(), getGoodWeights());
		ArbitrarilyDiscretizedFunc fractal;
		
		// test case for fraction of 0
		fractal = calc.getFractile(0);
		assertEquals(fractal.getY(0), 0.0, 0.0);
		for (int x=1; x<20; x++) {
			assertEquals(fractal.getY(x), 1.0, 0.0);
		}
		
		// test case for fraction of 0.3
		fractal = calc.getFractile(0.3);
		for (int x=0; x<20; x++) {
			double actualY = fractal.getY(x);
			double expectedY;
			if (x < 10)
				expectedY = (x % 10);
			else
				expectedY = 10 - (x % 10);
			assertEquals(actualY, expectedY, 0.0);
		}
		
		// test case for fraction of 0.5
		fractal = calc.getFractile(0.5);
		for (int x=0; x<20; x++) {
			double actualY = fractal.getY(x);
			double expectedY;
			if (x == 0)
				expectedY = 1.0;
			else if (x < 10)
				expectedY = (x % 10);
			else
				expectedY = 10 - (x % 10);
			assertEquals(actualY, expectedY, 0.0);
		}
		
		// test case for fraction of 1.0
		fractal = calc.getFractile(1.0);
		for (int x=0; x<20; x++) {
			double actualY = fractal.getY(x);
			double expectedY;
			if (x < 10)
				expectedY = 20 - x;
			else
				expectedY = x;
			assertEquals(actualY, expectedY, 0.0);
		}
	}

}
