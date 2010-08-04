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

package org.opensha.sha.calc.hazardMap.old.grid;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.text.DecimalFormat;

import org.dom4j.Attribute;
import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.data.siteData.SiteDataValueListList;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.gridComputing.GridJob;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.hazardMap.old.HazardMapCalculationParameters;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.imr.AttenuationRelationship;


/**
 * GridHardcodedHazardMapCalculator
 * 
 * Class to calculate a set of hazard curves from a region as part of a grid hazard map
 * computation. All values except for the start and end indices should be hard coded into
 * this class before distributing to compute nodes.
 * @author kevin
 *
 */
public class MetadataHazardMapCalculator implements ParameterChangeWarningListener {

	boolean timer = true;
	boolean loadERFFromFile = false;
	boolean lessPrints = false;
	boolean skipPoints = false;
	int skipFactor = 10;

	int startIndex;
	int endIndex;
	boolean debug;
	// location to store output files if debugging
	static final String DEBUG_RESULT_FOLDER = "/home/kevin/OpenSHA/condor/test_results/";
	
	public static final String START_TIME_FILE = "startTime.txt";

	boolean useCVM = false;
	String cvmFileName = "";

	String outputDir = "";
	
	String metadataFileName;

	/**
	 * Sets variables for calculation of hazard curves in hazard map
	 * @param sites - sites in gridded region
	 * @param startIndex - index  to start at within sites
	 * @param endIndex - index to end at (the very last one is NOT computed)
	 * @param debug - flag to enable debugging mode. if true, the timer and graph window will be enabled
	 * 		if hard coded in.
	 */
	public MetadataHazardMapCalculator(String metadataFileName, int startIndex, int endIndex, boolean debug) {
		this.startIndex = startIndex;
		this.endIndex = endIndex;
		this.debug = debug;
		this.metadataFileName = metadataFileName;

		// show timing results if debug mode and timer is selected
		timer = timer & debug;
	}

	public void calculateCurves() throws MalformedURLException, DocumentException, InvocationTargetException {
		File metadataFile = new File(metadataFileName);
		System.out.println("Loading metadata from " + metadataFile.getAbsolutePath());
		if (!metadataFile.exists())
			throw new RuntimeException("Metadata file doesn't exists!");
		
		long start = 0;
		if (timer) {
			start = System.currentTimeMillis();
		}

		SAXReader reader = new SAXReader();
		Document document = reader.read(metadataFile);
		Element root = document.getRootElement();

		// load the ERF
		long start_erf = 0;
		System.out.println("Creating Forecast");
		if (timer) {
			start_erf = System.currentTimeMillis();
		}
		Element erfElement = root.element(EqkRupForecast.XML_METADATA_NAME);
		Attribute className = erfElement.attribute("className");
		EqkRupForecast erf;
		if (className == null) { // load it from a file
			String erfFileName = erfElement.attribute("fileName").getValue();
			erf = (EqkRupForecast)FileUtils.loadObject(erfFileName);
		} else {
			erf = EqkRupForecast.fromXMLMetadata(erfElement);
			System.out.println("Updating Forecast");
			erf.updateForecast();
		}
		if (timer) {
			System.out.println("Took " + getTime(start_erf) + " seconds to load ERF.");
		}
		
		Element regionElement = root.element(GriddedRegion.XML_METADATA_NAME);
		GriddedRegion region = GriddedRegion.fromXMLMetadata(regionElement);
		SitesInGriddedRegion sites = new SitesInGriddedRegion(region);
		
		// TODO revisit to ensure proper functioning
		
//		if (region.isRectangular()) {
//			try {
//				
//				sites = new SitesInGriddedRegion(region, region.getGridSpacing());
//			} catch (RegionConstraintException e) {
//				sites = new SitesInGriddedRegion(region.getRegionOutline(), region.getGridSpacing());
//			}
//		} else {
//			sites = new SitesInGriddedRegion(region.getRegionOutline(), region.getGridSpacing());
//		}

		// max cutoff distance for calculator
//		Element calcParams = root.element("calculationParameters");
		Element gridJobEl = root.element(GridJob.XML_METADATA_NAME);
		HazardMapCalculationParameters calcParams = new HazardMapCalculationParameters(gridJobEl);
		double maxDistance =  calcParams.getMaxSourceDistance();

		// load IMR
		//AttenuationRelationshipAPI imr = new CB_2008_AttenRel(this);
		AttenuationRelationship imr = (AttenuationRelationship)AttenuationRelationship.fromXMLMetadata(root.element("IMR"), this);
		
		Element hazFuncElem = root.element(DiscretizedFunc.XML_METADATA_NAME);
		ArbitrarilyDiscretizedFunc hazFunction = null;
		if (hazFuncElem == null) {
			IMT_Info imtInfo = new IMT_Info();
			// get the default function for the specified IMT
			hazFunction = imtInfo.getDefaultHazardCurve(imr.getIntensityMeasure().getName());
		} else {
			hazFunction = DiscretizedFunc.fromXMLMetadata(hazFuncElem);
		}
		
		SiteDataValueListList siteDataVals = null;
		
		if (useCVM) {
			Document doc = XMLUtils.loadDocument(cvmFileName);
			Element el = doc.getRootElement();
			Element valsEl = el.element(SiteDataValueListList.XML_METADATA_NAME);
			
			siteDataVals = SiteDataValueListList.fromXMLMetadata(valsEl);
		}

		HazardMapPortionCalculator calculator = new HazardMapPortionCalculator(sites, erf, imr, hazFunction, siteDataVals, maxDistance, outputDir);

		calculator.setTimer(timer);
		calculator.setLessPrints(lessPrints);
		calculator.setSkipPoints(skipPoints);
		calculator.setSkipFactor(skipFactor);

		if (timer) {
			System.out.println(getTime(start) + " seconds total pre-calculator overhead");
		}

		calculator.calculateCurves(startIndex, endIndex);
	}

	/**
	 * Calculate and format the time from 'before'
	 * @param before - currentTimeMillis that should be counted from
	 * @return string in seconds of elapsed time
	 */
	public String getTime(long before) {
		double time = ((double)System.currentTimeMillis() - (double)before)/1000d; 
		return new DecimalFormat(	"###.##").format(time);
	}

	public void parameterChangeWarning(ParameterChangeWarningEvent event) {}

	/**
	 * Main class to calculate hazard curves. If there are less than 2 arguments, it is considered to be
	 * a test and timing messages will be displayed along with a graph window for the first 10 curves.
	 * Otherwise, the first argument is the start index for the site and the second argument is the end
	 * index.
	 * 
	 * Additionally, if endIndex is the string "TEST" then this is considered to be the first job in a DAG
	 * and will calculate 1 curve for each thread to make sure everything is working right.
	 * 
	 * @param args: startIndex endIndex metadataFileName [cvmFileName] [numThreads]
	 */
	public static void main(String[] args) {
		long start = System.currentTimeMillis();
		
		String outputDir = "";

		if (args.length < 3) { // this is a debug run
			System.err.println("RUNNING FROM DEBUG MODE!");
			args = new String[4];
//			args[0] = 0 + "";
//			args[1] = 50+ "";
			args[0] = 30600 + "";
			args[1] = 30650 + "";
			args[2] = "/home/kevin/OpenSHA/test/hazMap/meta.xml";
//			args[2] = "cvm_test.xml";
			args[3] = "/home/kevin/OpenSHA/test/hazMap/00000_00050.cvm";
			args[3] = "/home/kevin/OpenSHA/test/hazMap/30600_30650.cvm";
			outputDir = "/home/kevin/OpenSHA/test/hazMap/";
		}
		// get start and end index of sites to do within region from command line
		int startIndex = Integer.parseInt(args[0]);
		int endIndex;
		if (args[1].contains("TEST")) { // this is a single curve test run, the first job in the DAG
			endIndex = startIndex + 1;
			try {
				FileWriter fw = new FileWriter(START_TIME_FILE);
				fw.write(System.currentTimeMillis() + "");
				fw.flush();
				fw.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		} else {
			endIndex = Integer.parseInt(args[1]);
		}
		
		try {
			// run the calculator with debugging disabled
			String metadataFileName = args[2];
			MetadataHazardMapCalculator calc = new MetadataHazardMapCalculator(metadataFileName, startIndex, endIndex, false);
			if (args.length >=4 && args[3].toLowerCase().contains("cvm")) {
				calc.useCVM = true;
				calc.cvmFileName = args[3];
			}
			calc.skipPoints = false;
			calc.timer = true;
			calc.outputDir = outputDir;
			calc.calculateCurves();
			System.out.println("Total execution time: " + calc.getTime(start));
		} catch (Exception e) {
			// something bad happened, exit with code 1
			e.printStackTrace();
			System.exit(1);
		}
		// exit without error
		System.out.flush();
		System.err.flush();
		System.exit(0);
	}

}
