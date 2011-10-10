package org.gem.calc;

import static org.junit.Assert.*;

import java.util.Arrays;

import org.junit.Test;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.util.TectonicRegionType;

import static org.gem.calc.DisaggregationTestHelper.*;
import static org.gem.calc.DisaggregationCalculator.digitize;
import static org.gem.calc.DisaggregationCalculator.closestLocation;
import static org.gem.calc.DisaggregationCalculator.inRange;

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
	public void testDigitize()
	{
		int expected = 3;

		int actual = digitize(MAG_BIN_LIMS, 8.9);

		assertEquals(expected, actual);
	}

	@Test(expected=IllegalArgumentException.class)
	public void testDigitizeOutOfRange()
	{
		digitize(MAG_BIN_LIMS, 4.9);
	}

	@Test
	public void testGetBinIndices()
	{
		DisaggregationCalculator disCalc = new DisaggregationCalculator(
				LAT_BIN_LIMS, LON_BIN_LIMS, MAG_BIN_LIMS,
				EPS_BIN_LIMS, DIST_BIN_LIMS);

		int[] expected = {0, 2, 1, 6, 3};
		double lat, lon, mag, epsilon;
		lat = -0.6;
		lon = 0.0;
		mag = 6.5;
		epsilon = 3.49;
		TectonicRegionType trt = TectonicRegionType.SUBDUCTION_SLAB;

		int[] actual = disCalc.getBinIndices(lat, lon, mag, epsilon, trt);

		assertTrue(Arrays.equals(expected, actual));
	}

	@Test(expected=IllegalArgumentException.class)
	public void testGetBinIndicesOutOfRange()
	{
		DisaggregationCalculator disCalc = new DisaggregationCalculator(
				LAT_BIN_LIMS, LON_BIN_LIMS, MAG_BIN_LIMS,
				EPS_BIN_LIMS, DIST_BIN_LIMS);

		double lat, lon, mag, epsilon;
		lat = -0.6;
		lon = 0.0;
		mag = 6.5;
		epsilon = 3.5;  // out of range
		TectonicRegionType trt = TectonicRegionType.SUBDUCTION_SLAB;

		disCalc.getBinIndices(lat, lon, mag, epsilon, trt);
	}

	@Test
	public void testClosestLocation()
	{
		Location target = new Location(90.0, 180.0);

		LocationList locList = new LocationList();
		Location loc1, loc2, loc3;
		loc1 = new Location(0.0, 0.0);
		loc2 = new Location(90.0, 179.9);
		loc3 = new Location(90.0, -180.0);
		locList.add(loc1);
		locList.add(loc2);
		locList.add(loc3);

		assertEquals(loc3, closestLocation(locList, target));
	}

	@Test
	public void testInRange()
	{
		Double[] bins = {10.0, 20.0, 30.0};

		// boundaries:
		assertTrue(inRange(bins, 10.0));
		assertFalse(inRange(bins, 30.0));

		// in range:
		assertTrue(inRange(bins, 29.9));

		// out of range
		assertFalse(inRange(bins, 31.0));
	}

	@Test
	public void testNormalize()
	{
		
	}
}
