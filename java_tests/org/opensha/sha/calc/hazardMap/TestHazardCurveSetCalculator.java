package org.opensha.sha.calc.hazardMap;


import java.io.File;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.HashMap;

import junit.framework.TestCase;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.junit.Before;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DependentParameter;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.hazardMap.components.AsciiFileCurveArchiver;
import org.opensha.sha.calc.hazardMap.components.CalculationInputsXMLFile;
import org.opensha.sha.calc.hazardMap.components.CalculationSettings;
import org.opensha.sha.calc.hazardMap.components.CurveResultsArchiver;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_AdjustableEqkRupForecast;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.SiteParams.DepthTo2pt5kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.TectonicRegionType;

public class TestHazardCurveSetCalculator extends TestCase {
	
	private EqkRupForecastAPI erf;
	private ArrayList<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps;
	private ArrayList<Site> sites;
	private CalculationSettings calcSettings;
	private CurveResultsArchiver archiver;
	
	private String xmlFile;

	public static ArrayList<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> getIMRMaps() {
		ArrayList<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps;
		imrMaps = new ArrayList<HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>>();
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> map1 =
			new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> map2 =
			new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		CB_2008_AttenRel cb08 = new CB_2008_AttenRel(null);
		cb08.setParamDefaults();
		BA_2008_AttenRel ba08 = new BA_2008_AttenRel(null);
		ba08.setParamDefaults();
		
		cb08.setIntensityMeasure(SA_Param.NAME);
		((DependentParameter<Double>)cb08.getIntensityMeasure())
				.getIndependentParameter(PeriodParam.NAME).setValue((Object)new Double(1.0));
		
		ba08.setIntensityMeasure(SA_Param.NAME);
		((DependentParameter<Double>)ba08.getIntensityMeasure())
				.getIndependentParameter(PeriodParam.NAME).setValue((Object)new Double(1.0));
		
		map1.put(TectonicRegionType.ACTIVE_SHALLOW, cb08);
		map2.put(TectonicRegionType.ACTIVE_SHALLOW, ba08);
		
		imrMaps.add(map1);
		imrMaps.add(map2);
		return imrMaps;
	}
	
	@Before
	public void setUp() throws Exception {
		erf = new Frankel96_AdjustableEqkRupForecast();
		
		imrMaps = getIMRMaps();
		
		ScalarIntensityMeasureRelationshipAPI cb08 = imrMaps.get(0).get(TectonicRegionType.ACTIVE_SHALLOW);
		
		Location loc = new Location(34, -118);
		
		sites = new ArrayList<Site>();
		for (int i=0; i<5; i++) {
			Site site = new Site(loc);
			
			site.addParameter(cb08.getParameter(Vs30_Param.NAME));
			site.addParameter(cb08.getParameter(DepthTo2pt5kmPerSecParam.NAME));
			
			sites.add(site);
			
			loc = new Location(loc.getLatitude() + 0.1, loc.getLongitude());
		}
		
		calcSettings = new CalculationSettings(IMT_Info.getUSGS_SA_Function(), 200);
		File tempDir = FileUtils.createTempDir();
		archiver = new AsciiFileCurveArchiver(tempDir.getAbsolutePath(), false, false);
		
		CalculationInputsXMLFile inputs = new CalculationInputsXMLFile(erf, imrMaps, sites, calcSettings, archiver);
		Document doc = XMLUtils.createDocumentWithRoot();
		Element root = doc.getRootElement();
		inputs.toXMLMetadata(root);
		
		xmlFile = tempDir.getAbsolutePath() + File.separator + "input.xml";
		XMLUtils.writeDocumentToFile(xmlFile, doc);
	}
	
	public void testHazardCurves() throws IOException {
		HazardCurveSetCalculator calc = new HazardCurveSetCalculator(erf, imrMaps, archiver, calcSettings);
		
		calc.calculateCurves(sites);
	}
	
	public void testCurvesFromXML() throws DocumentException, InvocationTargetException, IOException {
		Document doc = XMLUtils.loadDocument(xmlFile);
		
		CalculationInputsXMLFile inputs = CalculationInputsXMLFile.loadXML(doc);
		AsciiFileCurveArchiver archiver = (AsciiFileCurveArchiver) inputs.getArchiver();
		String outputDir = archiver.getOutputDir();
		if (outputDir.endsWith(File.separator))
			outputDir = outputDir.substring(0, outputDir.length()-2);
		outputDir += "_fromXML" + File.separator;
		archiver.setOutputDir(outputDir);
		
		HazardCurveDriver driver = new HazardCurveDriver(inputs);
		driver.startCalculation();
	}

}
