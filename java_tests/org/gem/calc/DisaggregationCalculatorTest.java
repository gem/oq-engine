package org.gem.calc;

import static org.junit.Assert.*;

import org.junit.Test;

public class DisaggregationCalculatorTest
{
	public static final Double[] LAT_BIN_LIMS = {-0.6, -0.3, -0.1, 0.1, 0.3, 0.6};
	public static final Double[] LON_BIN_LIMS = {-0.6, -0.3, -0.1, 0.1, 0.3, 0.6};
	public static final Double[] MAG_BIN_LIMS = {5.0, 6.0, 7.0, 8.0, 9.0};
	public static final Double[] EPS_BIN_LIMS = {-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5};
	public static final Double[] DIST_BIN_LIMS = {0.0, 20.0, 40.0, 60.0};

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
}
