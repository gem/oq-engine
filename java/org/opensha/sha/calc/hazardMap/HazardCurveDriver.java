package org.opensha.sha.calc.hazardMap;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.util.HashMap;
import java.util.List;

import org.dom4j.Document;
import org.opensha.commons.data.Site;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.hazardMap.components.CalculationInputsXMLFile;
import org.opensha.sha.calc.hazardMap.components.CalculationSettings;
import org.opensha.sha.calc.hazardMap.components.CurveResultsArchiver;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This is a command line hazard curve calculator. It will be called by the Condor submit
 * scripts to calculate a set of hazard curves. It sets up the inputs to {@link HazardCurveSetCalculator}
 * and initiates the calculation.
 * 
 * Initially this will take an XML file which describes the inputs. This is the XML format that
 * I (Kevin Milner) used for a previous implementation. For GEM purposes, this could be changed
 * to some other input, as long as all of the inputs are specified.
 * 
 * @author kevin
 *
 */
public class HazardCurveDriver {
	
	private List<Site> sites;
	private EqkRupForecastAPI erf;
	private List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps;
	private List<DependentParameterAPI<Double>> imts;
	private HazardCurveSetCalculator calc;
	private CurveResultsArchiver archiver;
	private CalculationSettings calcSettings;
	
	public HazardCurveDriver(Document doc) throws InvocationTargetException, IOException {
		this(CalculationInputsXMLFile.loadXML(doc));
	}
	
	public HazardCurveDriver(CalculationInputsXMLFile inputs) throws InvocationTargetException, IOException {
		sites = inputs.getSites();
		erf = inputs.getERF();
		imrMaps = inputs.getIMRMaps();
		imts = inputs.getIMTs();
		archiver = inputs.getArchiver();
		calcSettings = inputs.getCalcSettings();
		
		calc = new HazardCurveSetCalculator(erf, imrMaps, imts, archiver, calcSettings);
	}
	
	public void startCalculation() throws IOException {
		calc.calculateCurves(sites);
	}
	
	/**
	 * Command line hazard curve calculator
	 * 
	 * @param args
	 */
	public static void main(String args[]) {
		System.out.println(HazardCurveDriver.class.getName() + ": starting up");
		try {
			if (args.length != 1) {
				System.err.println("USAGE: HazardCurveDriver <XML File>");
				System.exit(2);
			}
			File xmlFile = new File(args[0]);
			if (!xmlFile.exists()) {
				throw new IOException("XML Input file '" + args[0] + "' not found!");
			}
			
			Document doc = XMLUtils.loadDocument(xmlFile.getAbsolutePath());
			HazardCurveDriver driver = new HazardCurveDriver(doc);
			
			driver.startCalculation();
			System.exit(0);
		} catch (Throwable t) {
			t.printStackTrace();
			System.exit(1);
		}
	}

}
