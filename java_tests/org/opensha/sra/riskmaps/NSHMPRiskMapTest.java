package org.opensha.sra.riskmaps;

import static org.junit.Assert.*;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.util.FileUtils;
import org.opensha.sra.riskmaps.func.DiscreteInterpExterpFunc;

public class NSHMPRiskMapTest {

	@Before
	public void setUp() throws Exception {
	}
	
	private ArrayList<Double> loadVerification(String fileName, int index) throws FileNotFoundException, IOException {
		String line = FileUtils.loadFile(fileName).get(index);
		ArrayList<Double> vals = new ArrayList<Double>();
		StringTokenizer tok = new StringTokenizer(line, ",");
		while (tok.hasMoreTokens()) {
			double val = Double.parseDouble(tok.nextToken());
			vals.add(val);
		}
		return vals;
	}
	
	@Test
	public void testMapCreation() throws Exception {
		String curveFile = "/home/kevin/OpenSHA/nico/curve_input_file.bin";
		BinaryHazardCurveReader curveReader = new BinaryHazardCurveReader(curveFile);
//		ArbitrarilyDiscretizedFunc fragilityCurve = new ArbitrarilyDiscretizedFunc();
		
		String fragFile = "/home/kevin/OpenSHA/nico/Fragility_C1H_High_2p0sec.xml";
		
		DiscreteInterpExterpFunc fragilityCurve = DiscreteInterpExterpFunc.fromArbDistFunc(
				FragilityCurveReader.loadFunc(fragFile, "Slight"));
		
		NSHMPRiskMapCalc.interp = fragilityCurve.getXVals().length != 20;
		
		long start = System.currentTimeMillis();
		NSHMPRiskMapCalc calc = new NSHMPRiskMapCalc(curveReader, fragilityCurve);
		
		calc.setStoreTestVals();
		calc.calcRiskMap();
		ArrayList<Double> testVals = calc.getTestVals();
		long end = System.currentTimeMillis();
		
		System.out.println("Took " + ((end - start) / 1000d) + " secs");
		
		ArrayList<Double> verificationVals =
			loadVerification("/home/kevin/OpenSHA/nico/verification/RiskMapExample100223(461imls).csv", 0);
		
		for (int i=0; i<verificationVals.size(); i++) {
			double expected = verificationVals.get(i);
			if (Double.isNaN(expected))
				continue;
			double actual = testVals.get(i);
			double diff = org.opensha.commons.util.DataUtils.getPercentDiff(actual, expected);
			assertTrue("index " + i + "/" + (verificationVals.size()-1) +
					" expected: " + expected + " actual: " + actual + " pdiff: " + diff, diff < 5d);
		}
		
		System.out.println("Verified " + verificationVals.size() + " vals!");
		
//		result.writeXYZBinFile("/home/kevin/OpenSHA/nico/testData");
	}

}
