/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.calc.IM_EventSet.v03.test;

import java.io.File;
import java.io.IOException;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.ArrayList;
import java.util.StringTokenizer;

import static org.junit.Assert.*;

import org.junit.Test;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.IM_EventSet.v02.IM_EventSetCalc_v2_1;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetCalc_v3_0_ASCII;

public class IM_EventSetTest {
	
	public static double TOLERANCE = 0.05;
	
	private File outputDir;
	
	private File ver2DirFile = null;
	private File ver3DirFile = null;
	
	public IM_EventSetTest() {
		outputDir = getTempDir();
		System.out.println("outputDir: " + outputDir.getAbsolutePath());
	}
	
	public static File getTempDir() {
		File tempDir;
		try {
			tempDir = File.createTempFile("asdf", "fdsa").getParentFile();
		} catch (IOException e) {
			e.printStackTrace();
			tempDir = new File("/tmp");
		}
		tempDir = new File(tempDir.getAbsolutePath() + File.separator + "imEventSetTest");
		if (!tempDir.exists())
			tempDir.mkdir();
		return tempDir;
	}
	
	private File getVer2DirFile() {
		if (ver2DirFile == null) {
			try {
				ver2DirFile = runVer2();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
		return ver2DirFile;
	}
	
	private File getVer3DirFile() {
		if (ver3DirFile == null) {
			try {
				ver3DirFile = runVer3();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
		return ver3DirFile;
	}
	
	@Test
	public void testCB08_PGA() throws IOException {
		File dir2 = getVer2DirFile();
		File dir3 = getVer3DirFile();
		System.out.println("Testing CB 08 PGA");
		File PGA2 = new File(dir2.getAbsolutePath() + File.separator + "CB2008_PGA.txt");
		File PGA3 = new File(dir3.getAbsolutePath() + File.separator + "CB2008_PGA.txt");
		verifyFiles(PGA2, PGA3);
	}
	
	@Test
	public void testCB08_SA02() throws IOException {
		File dir2 = getVer2DirFile();
		File dir3 = getVer3DirFile();
		System.out.println("Testing CB 08 SA 0.2sec");
		File PGA2 = new File(dir2.getAbsolutePath() + File.separator + "CB2008_SA_0_2.txt");
		File PGA3 = new File(dir3.getAbsolutePath() + File.separator + "CB2008_SA02.txt");
		verifyFiles(PGA2, PGA3);
	}
	
	private void verifyFiles(File ver2File, File ver3File) throws IOException {
		ArrayList<String> lines2 = FileUtils.loadFile(ver2File.getAbsolutePath());
		ArrayList<String> lines3 = FileUtils.loadFile(ver3File.getAbsolutePath());
		
		double maxMeanDiff = 0;
		double maxSigmaDiff = 0;
		
		assertEquals(lines2.size(), lines3.size());
		
		for (int i=0; i<lines2.size(); i++) {
			String line2 = lines2.get(i);
			String line3 = lines3.get(i);
			
			StringTokenizer tok2 = new StringTokenizer(line2);
			StringTokenizer tok3 = new StringTokenizer(line3);
			
			int src2 = Integer.parseInt(tok2.nextToken());
			int src3 = Integer.parseInt(tok3.nextToken());
			
			assertEquals(src2, src3);
			
			int rup2 = Integer.parseInt(tok2.nextToken());
			int rup3 = Integer.parseInt(tok3.nextToken());
			
			assertEquals(rup2, rup3);
			
			double mean2 = Double.parseDouble(tok2.nextToken());
			double mean3 = Double.parseDouble(tok3.nextToken());
			
			double diff = getPercentDiff(mean2, mean3);
			if (diff > maxMeanDiff)
				maxMeanDiff = diff;
			if (diff > TOLERANCE) {
				System.out.println("Mean doesn't match! Line " + i);
				System.out.println(line2.trim());
				System.out.println(line3.trim());
				assertTrue(false);
			}
			
			double stdDev2 = Double.parseDouble(tok2.nextToken());
			double stdDev3 = Double.parseDouble(tok3.nextToken());
			
			diff = getPercentDiff(stdDev2, stdDev3);
			if (diff > maxSigmaDiff)
				maxSigmaDiff = diff;
			if (diff > TOLERANCE) {
				System.out.println("Total Std Dev doesn't match! Line " + i);
				System.out.println(line2.trim());
				System.out.println(line3.trim());
				assertTrue(false);
			}
		}
		
		System.out.println("File verified successfully!");
		System.out.println("Max mean diff: " + maxMeanDiff + " %");
		System.out.println("Max std dev diff: " + maxSigmaDiff + " %");
	}
	
	private static double getPercentDiff(double val1, double val2) {
		double diff = Math.abs(val1 - val2);
		double percentDiff = 100d * (diff / val1);
		return percentDiff;
	}
	
	private File runVer2() throws IOException {
		System.out.println("Running version 2!");
		URL inputURL = this.getClass().getResource("TestInputFile_v2_1.txt");
		File inputFile = null;
		File outDir = new File(outputDir.getAbsolutePath() + File.separator + "v2");
		outDir.mkdirs();
		try {
			inputFile = new File(inputURL.toURI());
		} catch (URISyntaxException e) {
			throw new RuntimeException(e);
		}
		IM_EventSetCalc_v2_1 calc = new IM_EventSetCalc_v2_1(inputFile.getAbsolutePath(), outDir.getAbsolutePath());
		calc.parseFile();
		calc.createSiteList();
		calc.getMeanSigma();
		
		return outDir;
	}
	
	private File runVer3() throws IOException {
		System.out.println("Running version 3!");
		URL inputURL = this.getClass().getResource("TestInputFile_v3_0_ASCII.txt");
		File inputFile = null;
		File outDir = new File(outputDir.getAbsolutePath() + File.separator + "v3");
		outDir.mkdirs();
		try {
			inputFile = new File(inputURL.toURI());
		} catch (URISyntaxException e) {
			throw new RuntimeException(e);
		}
		IM_EventSetCalc_v3_0_ASCII calc = new IM_EventSetCalc_v3_0_ASCII(inputFile.getAbsolutePath(), outDir.getAbsolutePath());
		calc.parseFile();
		calc.getMeanSigma(false);
		
		return outDir;
	}

}
