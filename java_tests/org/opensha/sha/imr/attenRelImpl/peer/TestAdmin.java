package org.opensha.sha.imr.attenRelImpl.peer;

import java.awt.Desktop;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.FilenameFilter;
import java.io.IOException;
import java.io.Serializable;
import java.net.URI;
import java.net.URL;
import java.text.DecimalFormat;
import java.text.Format;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import org.apache.commons.io.IOUtils;
import org.apache.commons.lang.StringUtils;
import org.dom4j.Document;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import org.dom4j.Namespace;
import org.dom4j.io.HTMLWriter;
import org.dom4j.tree.DefaultElement;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.calc.HazardCurveCalculator;

/**
 * Administration class for PEER test cases. This class provides several methods
 * to run all or a subset of the test cases as well as results comparison tools.
 * 
 * At the start of each test run, the temp directory, if such exists, used to 
 * store results will be purged of any previous tests; any summary files will
 * be preserved.
 *
 * @author Peter Powers
 * @version $Id:$
 */
public class TestAdmin {

	private static final String PEER_DIR_OUT = "tmp/PEER_test_results/";
	private static final String PEER_FILE_SUFFIX = "-PGA_OpenSHA.txt";
	
	private static SimpleDateFormat sdf = new SimpleDateFormat();
	private static SimpleDateFormat sdf_file = 
		new SimpleDateFormat("yyyy_MM_dd-HH_mm");

	private static Format deltaFormat = new DecimalFormat("0.0####");
	private static double deltaThreshold = 0.01; // percent
	
	private ArrayList<Future<?>> futures;
	private Document resultSummary;

	/**
	 * Tester.
	 * @param args
	 */
	public static void main(String[] args) {
		//runTests();
		runTests(95,98);
		evaluateResults(true);
		
		
//		runShortTests();
		//runLongTests();

		//File resultDir = new File(PEER_DIR_OUT);
		
//		evaluateResults("tmp/PEER_test_results_9-9-2009/", true);
//		evaluateResults("tmp/PEER_test_results_2-25-2010/", true);
		
//		evaluateResults("/Users/petrus/Desktop/PEER/PEER_TESTS_RESULTS/", true);
		//evaluateResults("/Users/petrus/Desktop/PEER/PEER_TESTS_SRC/", true);
		System.exit(0);
	}
	
	/**
	 * Run a single test.
	 * @param test
	 */
	public static void runTest(PeerTest test) {
		ArrayList<PeerTest> testList = new ArrayList<PeerTest>();
		testList.add(test);
		TestAdmin ta = new TestAdmin();
		ta.submit(testList);
	}

	/**
	 * Run all 106 tests.
	 */
	public static void runTests() {
		ArrayList<PeerTest> masterList = TestConfig.getSetOneDecriptors();
		TestAdmin ta = new TestAdmin();
		ta.submit(masterList);
	}
	
	/**
	 * Run a range of tests. See TestConfig to match indices to tests.
	 * @param min test index (inclusive)
	 * @param max test index (inclusive)
	 */
	public static void runTests(int min, int max) {
		ArrayList<PeerTest> testList = new ArrayList<PeerTest>();
		addRangeToList(testList, min, max);
		TestAdmin ta = new TestAdmin();
		ta.submit(testList);
	}
	
	/**
	 * Runs all the short tests: those taking a minute or less (most take under
	 * a second to run); 91 in all. Takes ~2min on an 8-core processor.
	 */
	public static void runShortTests() {
		ArrayList<PeerTest> testList = new ArrayList<PeerTest>();
		addRangeToList(testList, 0, 20);
		addRangeToList(testList, 28, 76);
		addRangeToList(testList, 84, 105);
		TestAdmin ta = new TestAdmin();
		ta.submit(testList);
	}
	
	/**
	 * Runs all the long tests: 14 tests (cases 4 and 9b) take ~20min each.
	 * Takes ~40min on an 8-core processor.
	 */
	public static void runLongTests() {
		ArrayList<PeerTest> testList = new ArrayList<PeerTest>();
		addRangeToList(testList, 21, 27);
		addRangeToList(testList, 77, 83);
		TestAdmin ta = new TestAdmin();
		ta.submit(testList);
	}
	
	// create or clean temp output directory
	private void initOutputDir() {
		File peerDir = new File(PEER_DIR_OUT);
		peerDir.mkdirs();
		File[] files = peerDir.listFiles(new PeerFileFilter());
		for (File f : files) {
			f.delete();
		}
	}
	
	private static void addRangeToList(ArrayList<PeerTest> list, int min, int max) {
		ArrayList<PeerTest> masterList = TestConfig.getSetOneDecriptors();
		for (int i=min; i<=max; i++) {
			list.add(masterList.get(i));
		}
	}
	
	private void submit(List<PeerTest> tests) {
		try {

			initOutputDir();
			
			int numProc = Runtime.getRuntime().availableProcessors();
			ExecutorService ex = Executors.newFixedThreadPool(numProc);

			String start = sdf.format(new Date(System.currentTimeMillis()));
			System.out.println("Running PEER test cases...");
			System.out.println("Processors: " + numProc);
			System.out.println("Start Time: " + start);
	
			futures = new ArrayList<Future<?>>();
			for (PeerTest pt : tests) {
				futures.add(ex.submit(new TestRunner(pt)));
			}

			// all tests on a single processor machine should
			// not take more than 12 hours
			ex.shutdown();
			ex.awaitTermination(12, TimeUnit.HOURS);
			
			String end = sdf.format(new Date(System.currentTimeMillis()));
			System.out.println("  End Time: " + end);
			
		} catch (InterruptedException ie) {
			ie.printStackTrace();
		}
	}
	
	
	private class TestRunner implements Runnable {
		
		private PeerTest test;

		TestRunner(PeerTest test) {
			this.test = test;
		}

		public void run() {
			
			long start = System.currentTimeMillis();
			System.out.println("  Starting: " + test);
			
			try {
				TestConfig tc = new TestConfig(test);
				
				HazardCurveCalculator calc = new HazardCurveCalculator();
				calc.setMaxSourceDistance(TestConfig.MAX_DISTANCE);
				calc.setIncludeMagDistCutoff(false);
				DiscretizedFuncAPI adf = calc.getHazardCurve(
						tc.getFunction(),
						tc.getSite(),
						tc.getIMR(),
						tc.getERF());
				
				adf = TestConfig.functionFromLogX(adf);
				
				BufferedWriter br = new BufferedWriter(new FileWriter(
						PEER_DIR_OUT + test + PEER_FILE_SUFFIX));
				for (int j = 0; j < adf.getNum(); ++j) {
					br.write(adf.get(j).getX() + "\t"
							+ adf.get(j).getY() + "\n");
				}
				br.close();

			} catch (Exception e) {
				System.out.println("    FAILED: " + test);
				e.printStackTrace();
			}
			long end = System.currentTimeMillis();
			int dtm = (int) ((end - start) / 1000 / 60);
			int dts = (int) ((end - start) / 1000 % 60);
			System.out.println(
					"  Finished: " + test + " " + dtm + "m " + dts + "s");
		}
	}
	
	
	/**
	 * Compares results of a test run stored in a specified directory to  
	 * previously generated result keys. Summary is output to the result
	 * directory and may optionally be displayed in a browser.
	 * 
	 * @param resultDirName to process
	 * @param display in a browser, or not
	 */
	public static void evaluateResults(String resultDirName, boolean display) {
		
		TestAdmin ta = new TestAdmin();
		
		File resultDir = new File(resultDirName);
		File[] results = ta.getFileList(resultDir);
		Arrays.sort(results, new TestFileComparator());
		Map<String,File> keys = ta.getKeyFileMap();
		
		
		Element e_body = ta.initSummaryDocument();
		e_body.addText("Result Source Dir: " + resultDir.getName());
		e_body.addElement("br");
		e_body.addElement("br");
		
		for (File file : results) {
			ta.processResult(file, keys.get(file.getName()), e_body);
		}
		
		File summaryFile = ta.writeSummaryFile(resultDirName);
		try {
			URI summaryURI = summaryFile.toURI();
			if (display) {
				Desktop.getDesktop().browse(summaryURI);
			} else {
				System.out.println(summaryURI);
			}
		} catch (Exception ex) {
			ex.printStackTrace();
		}
	}
	
	/**
	 * Compares results of a test run stored in the default tmp directory to
	 * previously generated result keys. Summary is output to the result 
	 * directory and may optionally be displayed in a browser.

	 * @param display in a browser, or not
	 */
	public static void evaluateResults(boolean display) {
		evaluateResults(PEER_DIR_OUT, display);
	}
	
	// compute the % change between a result and a key
	private static double computeDelta(double result, double key) {
		double delta = (result - key) / key * 100;
		return (Double.isNaN(delta)) ? 0 : delta;
	}
	
	
	// compare results of one test to its key
	private void processResult(File result, File key, Element e) {
		
		String testName = StringUtils.stripEnd(
				result.getName(), 
				PEER_FILE_SUFFIX) + ": ";

		e.addElement("strong").addText(testName);
		
		Element compTable = generateComparisonTable(result, key);
		
		Element status = e.addElement("span");
		if (compTable == null) {
			status.addAttribute("class", "pass");
			status.addText("MATCH");
			e.addElement("br");
		} else {
			status.addAttribute("class", "fail");
			status.addText("ERROR");
			e.addElement("br");
			e.add(compTable);
			e.addElement("br");
		}
	}
	
	
	// generates a comparison table with deltas, if not significant
	// deltas exsist, returns null
	private Element generateComparisonTable(File result, File key) {
		Map<Double,Double> resultData = readFileData(result);
		Map<Double,Double> keyData = readFileData(key);

		boolean same = true;
		
		Element table =  new DefaultElement("table");
		Element h_row = table.addElement("tr");
		h_row.addElement("th").addText("PGA");
		h_row.addElement("th").addText("P (result)");
		h_row.addElement("th").addText("P (key)");
		h_row.addElement("th").addText("Delta (%)");

		for (Double xVal : resultData.keySet()) {
			
			double resultP = resultData.get(xVal);
			double keyP = keyData.get(xVal);
			double delta = computeDelta(resultP, keyP);
			double deltaAbs = Math.abs(delta);
			if (deltaAbs > deltaThreshold) same = false;

			Element row = table.addElement("tr");
			row.addElement("td").addText(Double.toString(xVal));
			row.addElement("td").addText(Double.toString(resultP));
			row.addElement("td").addText(Double.toString(keyP));
			Element deltaElem = row.addElement("td").addText(
					deltaFormat.format(delta));
			if (deltaAbs > 1.0) {
				deltaElem.addAttribute("class", "fail");
			}
		}
		return (same) ? null : table;
	}
	
	
	// init the summary html document and return the body element for writing
	private Element initSummaryDocument() {
		resultSummary = DocumentHelper.createDocument();
		Element root = new DefaultElement(
				"html", 
				new Namespace("", "http://www.w3.org/1999/xhtml"));
		resultSummary.add(root);
		Element e_head = root.addElement("head");
		e_head.addElement("title").addText("PEER Test Result Summary");
		
		Element e_style = e_head.addElement("style");
		e_style.addAttribute("type", "text/css");
		e_style.addText("body {");
		e_style.addText("font-family: Monaco, monospace, Courier;");
		e_style.addText("font-size: 12px;");
		e_style.addText("}");
		e_style.addText("td {");
		e_style.addText("font-size: 12px;");
		e_style.addText("padding: 0px 20px;");
		e_style.addText("}");
		e_style.addText("th {");
		e_style.addText("font-size: 12px;");
		e_style.addText("padding: 0px 20px;");
		e_style.addText("}");
		e_style.addText(".pass {");
		e_style.addText("color: SteelBlue;");
		e_style.addText("}");
		e_style.addText(".fail {");
		e_style.addText("color: Crimson;");
		e_style.addText("}");
		
		Element e_body = root.addElement("body");
		e_body.addAttribute("style", "font-family: Monaco, monospace, Courier");
		String tstamp = sdf.format(new Date(System.currentTimeMillis()));
		e_body.addElement("h2").addText("PEER Result Summary " + tstamp);		
		return e_body;
	}


	// write out summary 
	private File writeSummaryFile(String outDir) {

		String summaryTstamp = sdf_file.format(
				new Date(System.currentTimeMillis()));
		String summaryFilePath = 
			outDir + "Summary-" + summaryTstamp + ".html";
		File summaryFile = new File(summaryFilePath);
		
		try {
			HTMLWriter writer = new HTMLWriter(new FileWriter(summaryFilePath));
			writer.write(resultSummary);
			writer.close();
		} catch (IOException ioe) {
			ioe.printStackTrace();
		}

		return summaryFile;
	}
	
	
	// places pga-probability pairs into a sorted map
	private Map<Double,Double> readFileData(File f) {
		TreeMap<Double,Double> data = new TreeMap<Double,Double>();
		try {
			BufferedReader br = new BufferedReader(new FileReader(f));
			String line = br.readLine();
			while (line != null) {
				String[] vals = StringUtils.split(line);
				data.put(Double.valueOf(vals[0]), Double.valueOf(vals[1]));
				line = br.readLine();
			}
			IOUtils.closeQuietly(br);
		} catch (Exception e) {
			e.printStackTrace();
		}
		return data;
	}
	
	
	// scans a directory for PEER result files
	private File[] getFileList(File dir) {
		File[] files = dir.listFiles(new PeerFileFilter());
		return files;
	}
	
	
	// creates a lookup table for PEER keys (correct results)
	private Map<String,File> getKeyFileMap() {
		HashMap<String,File> map = new HashMap<String,File>();
		try {
			URL keyUrl = TestAdmin.class.getResource("keys");
			File keyDir = new File(keyUrl.toURI());
			File[] keys = getFileList(keyDir);			
			for (File file : keys) {
				map.put(file.getName(), file);
			}
		} catch (Exception e) {
			e.printStackTrace();
		}
		return map;
	}
	
	// special sorter so that Case10 does not immediately follow Case1
	// (preceeding Case2)
	static class TestFileComparator implements Comparator<File>, Serializable {
		
		/**
		 * 
		 */
		private static final long serialVersionUID = 1L;

		public int compare(File f1, File f2) {
			
			String[] f1s = StringUtils.split(
					StringUtils.stripEnd(f1.getName(), ".txt"), "-");
			String[] f2s = StringUtils.split(
					StringUtils.stripEnd(f2.getName(), ".txt"), "-");
			
			String setNum1 = StringUtils.stripStart(f1s[0], "Set");
			String setNum2 = StringUtils.stripStart(f2s[0], "Set");
			String caseNum1 = StringUtils.stripStart(f1s[1], "Case");
			String caseNum2 = StringUtils.stripStart(f2s[1], "Case");
			String siteNum1 = StringUtils.stripStart(f1s[1], "Site");
			String siteNum2 = StringUtils.stripStart(f2s[1], "Site");
			
			// set comparison
			int setComp = setNum1.compareTo(setNum2);
			if (setComp != 0) return setComp;
			
			// case comparison
			Integer caseVal1 = 0;
			String caseSuffix1 = "";
			if (StringUtils.containsAny(caseNum1, "abc")) {
				caseSuffix1 = StringUtils.right(caseNum1, 1);
				caseVal1 = Integer.valueOf(StringUtils.chop(caseNum1));
			} else {
				caseVal1 = Integer.valueOf(caseNum1);
			}
			
			Integer caseVal2 = 0;
			String caseSuffix2 = "";
			if (StringUtils.containsAny(caseNum2, "abc")) {
				caseSuffix2 = StringUtils.right(caseNum2, 1);
				caseVal2 = Integer.valueOf(StringUtils.chop(caseNum2));
			} else {
				caseVal2 = Integer.valueOf(caseNum2);
			}
			
			int caseComp = caseVal1.compareTo(caseVal2);
			if (caseComp != 0) return caseComp;
			caseComp = caseSuffix1.compareTo(caseSuffix2);
			if (caseComp != 0) return caseComp;
			
			// fall back to site comparison
			return siteNum1.compareTo(siteNum2);
		}
	}

	// selects test result files 
	static class PeerFileFilter implements FilenameFilter {
		public boolean accept(File dir, String name) {
			return (name.endsWith(PEER_FILE_SUFFIX)) ? true : false;
		}
	}

}
