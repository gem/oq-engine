/**
 * AW_2010_test
 * 
 * Description: This program tests that correct values are calculated by
 * 				the AW_2010_AttenRel Class.
 * 				Run as JUnit test.
 * 
 * Input:		Excel spreadsheet prepared by D. Monelli
 * 				Converted to CSV text file in 2 possible formats:
 * 				(1) For Finite Ruptures: in AW2010FINITE.TXT
 * 					Format:	ruptureDistance, MMI(Mw=5), MMI(Mw=6), 
 * 								MMI(Mw=7), MMI(Mw=8), Sigma
 * 				(2) For Point Ruptures: in AW2010POINT.TXT
 * 					Format: hypocentralDistance, MMI(Mw=5), MMI(Mw=6), 
 * 								MMI(Mw=7), Sigma
 * 
 * Please refer to the following files (added):
 * 				AW_2010_AttenRel.java
 * 						(in org.opensha.sha.imr.attenRelImpl)
 * 				MMI_Param.java
 * 						(in org.opensha.sha.imr.param.IntensityMeasureParams)
 * 				DistanceHypoParameter.java
 * 						(in org.opensha.sha.imr.param.PropagationEffectParams)
 * 
 * And the following files (modified):
 * 				AttenuationRelationship.java
 * 						(in org.opensha.sha.imr)
 * 
 * @author 		Aurea Moemke
 * @created 	22 September 2010
 * @version 	1.0
 * 
 */

package org.opensha.sha.imr.attenRelImpl.test;

import static org.junit.Assert.assertEquals;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.LineNumberReader;
import java.util.Scanner;
import java.util.StringTokenizer;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.PointSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.imr.attenRelImpl.AW_2010_AttenRel;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

public class AW_2010_test implements ParameterChangeWarningListener {

	private AW_2010_AttenRel aw_2010_AttenRel = null;

	private static String inputFilePath = "/java_tests/data/";
	private static String inputFileNameFinite = "AW2010FINITE.TXT";
	private static String inputFileNamePoint = "AW2010POINT.TXT";

	// TOLERANCE VALUE FOR TEST
	private static double tolerance = 1E-8;

	@Before
	public void setUp() {
		aw_2010_AttenRel = new AW_2010_AttenRel(this);
		aw_2010_AttenRel.setParamDefaults();
	}

	@After
	public void tearDown() {
		aw_2010_AttenRel = null;
	}

	@Test
	public void pointRuptureEquation() {

		/**
		 * This test validate the getMean(m,r) and getStdDev(r) methods for
		 * point ruptures against a verification table obtained using an Excel
		 * spreadsheet
		 */

		boolean isFiniteRupture = false;

		// GET CORRECT DIR PATH
		File dir1 = new File(".");
		String dirPath = null;
		try {
			System.out.println("Current dir : " + dir1.getCanonicalPath());
			dirPath = dir1.getCanonicalPath();
		} catch (Exception e) {
			e.printStackTrace();
		}

		// TEST POINT RUPTURES
		File inFile = new File(dirPath + inputFilePath + inputFileNamePoint);
		int numlines = countFileLines(inFile);
		System.out.println("Num of lines in Point ruptures file: " + numlines);
		doTest(isFiniteRupture, tolerance, numlines, inFile);

		System.out.println("End AW_2010 Attenuation Relationship test...");
	}

	@Test
	public void finiteRuptureEquation() {

		/**
		 * This test validate the getMean(m,r) and getStdDev(r) methods for
		 * finite ruptures against a verification table obtained using an Excel
		 * spreadsheet
		 */

		boolean isFiniteRupture = true;

		// GET CORRECT DIR PATH
		File dir1 = new File(".");
		String dirPath = null;
		try {
			System.out.println("Current dir : " + dir1.getCanonicalPath());
			dirPath = dir1.getCanonicalPath();
		} catch (Exception e) {
			e.printStackTrace();
		}

		// TEST FINITE RUPTURES
		File inFile = new File(dirPath + inputFilePath + inputFileNameFinite);
		int numlines = countFileLines(inFile);
		System.out.println("Num of lines in Finite ruptures file: " + numlines);
		doTest(isFiniteRupture, tolerance, numlines, inFile);

		System.out.println("End AW_2010 Attenuation Relationship test...");
	}

	@Test
	public void pointEqkRupture() {

		/**
		 * This test compares the results of the getMean() and getStdDev()
		 * methods when setting a Site and a point EqkRupture object with the
		 * results of the get getMeanForPointRup(m,r) method when passing
		 * directly the magnitude and hypocentral distance values. This test is
		 * meant to validate if the Site and EqkRupture parameters are passed
		 * correctly to the AttenuationRelationship object and correct
		 * distinction is done between point and finite rupture.
		 */

		// define earthquake point rupture
		// magnitude
		double mag = 5.0;
		// hypocenter coordinates (lat,lon,depth (km))
		Location hypo = new Location(0.0, 0.0, 5.0);
		// average rake (not needed by the IPE but to define EqkRupture object
		double aveRake = 0.0;
		// get earthquake rupture object
		EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);

		// define Site (on the same latitude of the of the hypocenter
		// but shifted towards East of 0.1 degrees)
		Site site = new Site(new Location(0.0, 0.1, 0.0));

		// calculate hypocentral distance
		double hypoDist = Math
				.sqrt(Math.pow(
						LocationUtils.horzDistance(hypo, site.getLocation()), 2)
						+ Math.pow(
								LocationUtils.vertDistance(hypo,
										site.getLocation()), 2));

		// set site
		aw_2010_AttenRel.setSite(site);
		// set earthquake rupture
		aw_2010_AttenRel.setEqkRupture(rup);
		// calculate mean
		double meanMMI = aw_2010_AttenRel.getMean();
		// calculate standard deviation
		double std = aw_2010_AttenRel.getStdDev();

		// calculate mean by passing directly magnitude and hypocentral distance
		// values
		double meanMMI_pointRupture = aw_2010_AttenRel.getMeanForPointRup(mag,
				hypoDist);
		// calculate std by passing directly the hypocentral distance
		double std_pointRupture = aw_2010_AttenRel
				.getStdDevForPointRup(hypoDist);

		// compare mean values
		assertEquals(meanMMI_pointRupture, meanMMI, tolerance);
		// compare standard deviation values
		assertEquals(std_pointRupture, std, tolerance);

	}

	@Test
	public void finiteEqkRupture() {
		/**
		 * This test compares the results of the getMean() and getStdDev()
		 * methods when setting a Site and a finite EqkRupture object with the
		 * results of the get getMeanForFiniteRup(m,r) method when passing
		 * directly the magnitude and closest distance to rupture values. This
		 * test is meant to validate if the Site and EqkRupture parameters are
		 * passed correctly to the AttenuationRelationship object and correct
		 * distinction is done between point and finite rupture.
		 */
		// define finite rupture (data from the Elsinore fault (USGS california
		// model: aFault_aPriori_D2.1.in))
		double aveDip = 90.0;
		double lowerSeisDepth = 13.0;
		double upperSeisDepth = 0.0;
		FaultTrace trace = new FaultTrace("Elsinore;GI");
		trace.add(new Location(33.82890, -117.59000));
		trace.add(new Location(33.81290, -117.54800));
		trace.add(new Location(33.74509, -117.46332));
		trace.add(new Location(33.73183, -117.44568));
		trace.add(new Location(33.71851, -117.42415));
		trace.add(new Location(33.70453, -117.40265));
		trace.add(new Location(33.68522, -117.37270));
		trace.add(new Location(33.62646, -117.27443));
		double gridSpacing = 1.0;
		double mag = 6.889;
		double aveRake = 0.0;
		Location hypo = new Location(33.73183, -117.44568);
		EqkRupture rup = getFiniteEqkRupture(aveDip, lowerSeisDepth,
				upperSeisDepth, trace, gridSpacing, mag, hypo, aveRake);

		// define Site (on the same latitude of the of the hypocenter
		// but shifted towards East of 0.1 degrees)
		Site site = new Site(new Location(33.8, -117.6, 0.0));

		// set site
		aw_2010_AttenRel.setSite(site);
		// set earthquake rupture
		aw_2010_AttenRel.setEqkRupture(rup);

		// calculate mean
		double meanMMI = aw_2010_AttenRel.getMean();
		// calculate standard deviation
		double std = aw_2010_AttenRel.getStdDev();

		// calculate mean by passing directly magnitude and closest distance to
		// rupture values
		double rRup = (Double) aw_2010_AttenRel.getParameter(
				DistanceRupParameter.NAME).getValue();
		double meanMMI_finiteRupture = aw_2010_AttenRel.getMeanForFiniteRup(
				mag, rRup);
		// calculate std by passing directly the hypocentral distance
		double std_finiteRupture = aw_2010_AttenRel.getStdDevForFiniteRup(rRup);

		// compare mean values
		assertEquals(meanMMI_finiteRupture, meanMMI, tolerance);
		// compare standard deviation values
		assertEquals(std_finiteRupture, std, tolerance);
	}

	@Test(expected = org.opensha.commons.exceptions.WarningException.class)
	public void magnitudeValueTooSmall() {
		/**
		 * This test checks that the AW_2010_AttenRel object throws a warning
		 * exception when a magnitude value < 5 is passed
		 * 
		 */
		// define point source with magnitude 4
		double mag = 4.0;
		// hypocenter coordinates (lat,lon,depth (km))
		Location hypo = new Location(0.0, 0.0, 5.0);
		// average rake (not needed by the IPE but to define EqkRupture object
		double aveRake = 0.0;
		// get earthquake rupture object
		EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);

		aw_2010_AttenRel.setEqkRupture(rup);
	}

	@Test(expected = org.opensha.commons.exceptions.WarningException.class)
	public void magnitudeValueTooLarge() {
		/**
		 * This test checks that the AW_2010_AttenRel object throws a warning
		 * exception when a magnitude value > 8 is passed
		 * 
		 */
		// define point source with magnitude 4
		double mag = 9.0;
		// hypocenter coordinates (lat,lon,depth (km))
		Location hypo = new Location(0.0, 0.0, 5.0);
		// average rake (not needed by the IPE but to define EqkRupture object
		double aveRake = 0.0;
		// get earthquake rupture object
		EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);

		aw_2010_AttenRel.setEqkRupture(rup);
	}

	@Test(expected = org.opensha.commons.exceptions.WarningException.class)
	public void hypocentralDistanceTooLarge() {
		/**
		 * This test checks that the AW_2010_AttenRel object throws a warning
		 * exception when a hypocentral distance > 300 km is passed
		 * 
		 */
		// define point source with magnitude 5
		double mag = 5.0;
		// hypocenter coordinates (lat,lon,depth (km))
		Location hypo = new Location(0.0, 0.0, 5.0);
		// average rake (not needed by the IPE but to define EqkRupture object
		double aveRake = 0.0;
		// get earthquake rupture object
		EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);

		// define Site (on the same latitude of the of the hypocenter
		// but shifted towards East of 4 degrees)
		Site site = new Site(new Location(0.0, 4., 0.0));

		aw_2010_AttenRel.setSite(site);
		aw_2010_AttenRel.setEqkRupture(rup);
	}

	@Test(expected = org.opensha.commons.exceptions.WarningException.class)
	public void closestDistanceToRuptureTooLarge() {
		/**
		 * This test checks that the AW_2010_AttenRel object throws a warning
		 * exception when a closest distance to rupture > 300 km is passed
		 * 
		 */
		// define finite rupture (data from the Elsinore fault (USGS california
		// model: aFault_aPriori_D2.1.in))
		double aveDip = 90.0;
		double lowerSeisDepth = 13.0;
		double upperSeisDepth = 0.0;
		FaultTrace trace = new FaultTrace("Elsinore;GI");
		trace.add(new Location(33.82890, -117.59000));
		trace.add(new Location(33.81290, -117.54800));
		trace.add(new Location(33.74509, -117.46332));
		trace.add(new Location(33.73183, -117.44568));
		trace.add(new Location(33.71851, -117.42415));
		trace.add(new Location(33.70453, -117.40265));
		trace.add(new Location(33.68522, -117.37270));
		trace.add(new Location(33.62646, -117.27443));
		double gridSpacing = 1.0;
		double mag = 6.889;
		double aveRake = 0.0;
		Location hypo = new Location(33.73183, -117.44568);
		EqkRupture rup = getFiniteEqkRupture(aveDip, lowerSeisDepth,
				upperSeisDepth, trace, gridSpacing, mag, hypo, aveRake);

		// define Site (at the intersection of the equator and Greenwich
		// meridian, it should be enough far from California!)
		Site site = new Site(new Location(0.0, 0.0, 0.0));

		aw_2010_AttenRel.setSite(site);
		aw_2010_AttenRel.setEqkRupture(rup);
	}

	private int countFileLines(File testFile) {
		int count = 0;
		try {
			if (testFile.exists()) {
				FileReader fr = new FileReader(testFile);
				LineNumberReader ln = new LineNumberReader(fr);
				while (ln.readLine() != null) {
					count++;
				}
				System.out.println("Total line no: " + count);
				ln.close();
			} else {
				System.out.println("File does not exist!");
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
		return count - 1; // do not count 1st line
	}

	private void loadTestData(File testFile, int numMags, double rRup[],
			double vals[][], double sigma[]) {
		// Use scanner to read testFile
		Scanner scanner = null;
		try {
			scanner = new Scanner(testFile);
		} catch (FileNotFoundException e) {
			e.printStackTrace();// TODO Auto-generated catch block
		}

		// Load data per line in ASCII Text format using Scanner to get each
		// line
		// NOTE that first line in file contains a description in this case
		String lineContent = scanner.nextLine();

		int i = 0;

		StringTokenizer st;

		while (scanner.hasNextLine()) {
			lineContent = scanner.nextLine();
			System.out.println("line read " + lineContent);
			st = new StringTokenizer(lineContent, ",");
			rRup[i] = Double.parseDouble(st.nextToken());
			for (int j = 0; j < numMags + 1; j++) {
				if (j < numMags) {
					vals[i][j] = Double.parseDouble(st.nextToken());
					System.out.println("vals[" + i + "]" + "[" + (j) + "]="
							+ vals[i][j]);
				} else {
					sigma[i] = Double.parseDouble(st.nextToken());
					System.out.println("sigma[" + i + "]=" + sigma[i]);
				}
			}
			i++;
		}
		scanner.close();
	}

	// TEST to check if computed values are same as expected values
	// Different methods are called for FiniteRupture and PointRupture
	private void doTest(boolean isFiniteRupture, double tolerance,
			int numlines, File inFile) {
		int[] mw = { 5, 6, 7, 8 };
		int numMags = 0;

		if (isFiniteRupture)
			numMags = 4; // for finite rupture, magnitudes 5, 6, 7, 8
		else
			numMags = 3; // for point rupture, only magnitudes 5, 6, 7

		double[] r = new double[numlines];
		double[] sigma = new double[numlines];
		double[][] results;
		results = new double[numlines][];
		for (int i = 0; i < r.length; i++) {
			r[i] = 0.0;
			sigma[i] = 0.0;
			results[i] = new double[numMags + 1];
			for (int j = 0; j < numMags + 1; j++) {
				results[i][j] = 0.0;
			}
		}
		loadTestData(inFile, numMags, r, results, sigma);
		double expectedmean, computedmean;
		double expectedstddev, computedstddev;

		for (int i = 0; i < r.length; i++) {
			for (int j = 0; j < numMags; j++) {
				expectedmean = results[i][j];
				expectedstddev = sigma[i];
				if (isFiniteRupture) {
					computedmean = aw_2010_AttenRel.getMeanForFiniteRup(mw[j],
							r[i]);
					computedstddev = aw_2010_AttenRel
							.getStdDevForFiniteRup(r[i]);
				} else {
					computedmean = aw_2010_AttenRel.getMeanForPointRup(mw[j],
							r[i]);
					computedstddev = aw_2010_AttenRel
							.getStdDevForPointRup(r[i]);
				}
				System.out.println("mag = " + mw[j] + " rupture = " + r[i]
						+ " mean: expected = " + expectedmean + ", computed= "
						+ computedmean + "; stddev: expected = "
						+ expectedstddev + ", computed = " + computedstddev);
				assertEquals(expectedmean, computedmean, tolerance);
				assertEquals(expectedstddev, computedstddev, tolerance);
			}
		}
	}

	/**
	 * Creates an EqkRupture object for a point source given magnitude and
	 * hypocenter location, and average rake
	 * 
	 * @param mag
	 * @param hypo
	 * @param aveRake
	 * @return
	 */
	private EqkRupture getPointEqkRupture(double mag, Location hypo,
			double aveRake) {
		// rupture surface (for a point)
		EvenlyGriddedSurfaceAPI rupSurf = new PointSurface(hypo);
		EqkRupture rup = new EqkRupture(mag, aveRake, rupSurf, hypo);
		return rup;
	}

	private EqkRupture getFiniteEqkRupture(double aveDip,
			double lowerSeisDepth, double upperSeisDepth,
			FaultTrace faultTrace, double gridSpacing, double mag,
			Location hypo, double aveRake) {
		StirlingGriddedSurface rupSurf = new StirlingGriddedSurface(faultTrace,
				aveDip, upperSeisDepth, lowerSeisDepth, gridSpacing);
		EqkRupture rup = new EqkRupture(mag, aveRake, rupSurf, hypo);
		return rup;
	}

	public void parameterChangeWarning(ParameterChangeWarningEvent event) {
	}

}
