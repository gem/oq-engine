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

import org.opensha.sha.imr.attenRelImpl.AW_2010_AttenRel;

public class AW_2010_test {

	private AW_2010_AttenRel aw_2010_AttenRel = null;

	private static String inputFilePath = "/java_tests/data/";
	private static String inputFileNameFinite = "AW2010FINITE.TXT";
	private static String inputFileNamePoint = "AW2010POINT.TXT";

	@Before
	public void setUp() {
		aw_2010_AttenRel = new AW_2010_AttenRel(null);
	}

	@After
	public void tearDown() {
		aw_2010_AttenRel = null;
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
					computedstddev =aw_2010_AttenRel.getStdDevForPointRup(r[i]);
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

	@Test
	public void testAW_2010() {

		boolean isFiniteRupture = true; // else, PointRupture
		// TOLERANCE VALUE FOR TEST
		double tolerance = 1E-8;

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

		// TEST POINT RUPTURES
		isFiniteRupture = false;
		inFile = new File(dirPath + inputFilePath + inputFileNamePoint);
		numlines = countFileLines(inFile);
		System.out.println("Num of lines in Point ruptures file: " + numlines);
		doTest(isFiniteRupture, tolerance, numlines, inFile);

		System.out.println("End AW_2010 Attenuation Relationship test...");
	}

}
