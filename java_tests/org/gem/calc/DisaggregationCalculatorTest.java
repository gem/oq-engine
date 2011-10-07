package org.gem.calc;

import static org.junit.Assert.*;

import java.util.Arrays;

import org.junit.Test;

import static org.gem.calc.DisaggregationTestHelper.*;

public class DisaggregationCalculatorTest
{

	/**
	 * If any of the bin edges passed to the constructor are null,
	 * an IllegalArgumentException should be thrown.
	 */
	@Test(expected=IllegalArgumentException.class)
	public void testConstructorOneNull()
	{
		new DisaggregationCalculator(
				new Double[10], new Double[10], null,
				new Double[10], new Double[5]);
	}

	/**
	 * Same the test above, except with all null input.
	 */
	@Test(expected=IllegalArgumentException.class)
	public void testConstructorManyNull()
	{
		new DisaggregationCalculator(null, null, null, null, null);
	}

	/**
	 * If any of the bin edges passed to the constructor have a length < 2,
	 * an IllegalArgumentException should be thrown.
	 */
	@Test(expected=IllegalArgumentException.class)
	public void testConstructorOneTooShort() 
	{
		new DisaggregationCalculator(
				new Double[2], new Double[2], new Double[1],
				new Double[2], new Double[2]);
	}

	/**
	 * Same as the test above, except all input arrays are too short.
	 */
	@Test(expected=IllegalArgumentException.class)
	public void testConstructorAllTooShort()
	{
		new DisaggregationCalculator(
				new Double[1], new Double[1], new Double[1],
				new Double[1], new Double[1]);
	}

	@Test(expected=IllegalArgumentException.class)
	public void testConstructorUnsortedBinEdges()
	{
		Double[] unsorted = {1.1, 1.0};
		new DisaggregationCalculator(
				LAT_BIN_LIMS, LON_BIN_LIMS, unsorted,
				EPS_BIN_LIMS, DIST_BIN_LIMS);
	}

	/**
	 * Test constructor with known-good input.
	 * (No errors should be thrown.)
	 */
	@Test
	public void testConstructorGoodInput()
	{
		new DisaggregationCalculator(
				LAT_BIN_LIMS, LON_BIN_LIMS, MAG_BIN_LIMS,
				EPS_BIN_LIMS, DIST_BIN_LIMS);
	}

	@Test
	public void testComputeMatrix()
	{
		DisaggregationCalculator disCalc = new DisaggregationCalculator(
				LAT_BIN_LIMS, LON_BIN_LIMS, MAG_BIN_LIMS,
				EPS_BIN_LIMS, DIST_BIN_LIMS);
		
		double[][][][][] result = disCalc.computeMatrix(
				SITE, ERF, IMR_MAP, POE, HAZARD_CURVE);
				
		
		assertTrue(Arrays.deepEquals(EXPECTED, result));
	}

	@Test
	public void testGetBinIndices()
	{
		
	}
}
