package org.opensha.sha.calc.hazardMap.components;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.ListIterator;
import java.util.Map;

import org.dom4j.Attribute;
import org.dom4j.Document;
import org.dom4j.Element;
import org.opensha.commons.data.Site;
import org.opensha.commons.metadata.XMLSaveable;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.hazardMap.dagGen.HazardDataSetDAGCreator;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.imr.IntensityMeasureRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This class represends all of the inputs to the hazard map calculation process,
 * and handles writing/loading them to/from XML.
 * 
 * @author kevin
 *
 */
public class CalculationInputsXMLFile implements XMLSaveable {
	
	private EqkRupForecastAPI erf;
	private List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps;
	private List<Site> sites;
	private List<DependentParameterAPI<Double>> imts;
	private CalculationSettings calcSettings;
	private CurveResultsArchiver archiver;
	
	private boolean erfSerialized = false;
	private String serializedERFFile;
	
	public CalculationInputsXMLFile(EqkRupForecastAPI erf,
			List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps,
			List<Site> sites,
			CalculationSettings calcSettings,
			CurveResultsArchiver archiver) {
		this(erf, imrMaps, null, sites, calcSettings, archiver);
	}
	
	public CalculationInputsXMLFile(EqkRupForecastAPI erf,
		List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps,
		List<DependentParameterAPI<Double>> imts,
		List<Site> sites,
		CalculationSettings calcSettings,
		CurveResultsArchiver archiver) {
		this.erf = erf;
		this.imrMaps = imrMaps;
		this.imts = imts;
		this.sites = sites;
		this.calcSettings = calcSettings;
		this.archiver = archiver;
	}
	
	public EqkRupForecastAPI getERF() {
		return erf;
	}
	
	public void serializeERF(String odir) throws IOException {
		erf.updateForecast();
		FileUtils.saveObjectInFile(serializedERFFile, erf);
		String serializedERFFile = odir + HazardDataSetDAGCreator.ERF_SERIALIZED_FILE_NAME;
		setSerialized(serializedERFFile);
	}
	
	public void setSerialized(String serializedERFFile) {
		erfSerialized = serializedERFFile != null;
		this.serializedERFFile = serializedERFFile;
	}

	public List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> getIMRMaps() {
		return imrMaps;
	}
	
	public void setIMTs(List<DependentParameterAPI<Double>> imts) {
		this.imts = imts;
	}
	
	public List<DependentParameterAPI<Double>> getIMTs() {
		return this.imts;
	}

	public List<Site> getSites() {
		return sites;
	}

	public CalculationSettings getCalcSettings() {
		return calcSettings;
	}

	public CurveResultsArchiver getArchiver() {
		return archiver;
	}

	public Element toXMLMetadata(Element root) {
		if (erf instanceof EqkRupForecast) {
			EqkRupForecast newERF = (EqkRupForecast)erf;
			root = newERF.toXMLMetadata(root);
			if (erfSerialized) {
				// load the erf element from metadata
				Element erfElement = root.element(EqkRupForecast.XML_METADATA_NAME);

				// rename the old erf to ERF_REF so that the params are preserved, but it is not used for calculation
				root.add(erfElement.createCopy("ERF_REF"));
				erfElement.detach();
				
				// create new ERF element and add to root
				Element newERFElement = root.addElement(EqkRupForecast.XML_METADATA_NAME);
				newERFElement.addAttribute("fileName", serializedERFFile);
			}
		} else {
			throw new ClassCastException("Currently only EqkRupForecast subclasses can be saved" +
			" to XML.");
		}
		ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs =
			new ArrayList<ScalarIntensityMeasureRelationshipAPI>();
		ArrayList<Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> newList =
			new ArrayList<Map<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>>();
		for (HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI> map : imrMaps) {
			newList.add(map);
			for (TectonicRegionType tect : map.keySet()) {
				ScalarIntensityMeasureRelationshipAPI imr = map.get(tect);
				boolean add = true;
				for (ScalarIntensityMeasureRelationshipAPI newIMR : imrs) {
					if (newIMR.getShortName().equals(imr.getShortName())) {
						add = false;
						break;
					}
				}
				if (add)
					imrs.add(imr);
			}
		}
		imrsToXML(imrs, root);
		imrMapsToXML(newList, imts, root);
		Site.writeSitesToXML(sites, root);
		calcSettings.toXMLMetadata(root);
		archiver.toXMLMetadata(root);
		return null;
	}
	
	public static CalculationInputsXMLFile loadXML(Document doc) throws InvocationTargetException, IOException {
		Element root = doc.getRootElement();
		
		/* Load the ERF 							*/
		EqkRupForecastAPI erf;
		Element erfElement = root.element(EqkRupForecast.XML_METADATA_NAME);
		Attribute className = erfElement.attribute("className");
		if (className == null) { // load it from a file
			String erfFileName = erfElement.attribute("fileName").getValue();
			erf = (EqkRupForecast)FileUtils.loadObject(erfFileName);
		} else {
			erf = EqkRupForecast.fromXMLMetadata(erfElement);
			System.out.println("Updating Forecast");
			erf.updateForecast();
		}
		
		/* Load the IMRs							*/
		Element imrsEl = root.element(XML_IMRS_NAME);
		ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs =imrsFromXML(imrsEl);
		ArrayList<ParameterAPI> paramsToAdd = new ArrayList<ParameterAPI>();
		for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
			ListIterator<ParameterAPI<?>> it = imr.getSiteParamsIterator();
			while (it.hasNext()) {
				ParameterAPI param = it.next();
				boolean add = true;
				for (ParameterAPI prevParam : paramsToAdd) {
					if (param.getName().equals(prevParam.getName())) {
						add = false;
						break;
					}
				}
				if (add)
					paramsToAdd.add(param);
			}
		}
		
		/* Load the IMR Maps						*/
		Element imrMapsEl = root.element(XML_IMR_MAP_LIST_NAME);
		ArrayList<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps =
			imrMapsFromXML(imrs, imrMapsEl);
		
		/* Load the IMTs if applicaple				*/
		List<DependentParameterAPI<Double>> imts = imtsFromXML(imrs.get(0), imrMapsEl);
		
		/* Load the sites 							*/
		Element sitesEl = root.element(Site.XML_METADATA_LIST_NAME);
		ArrayList<Site> sites = Site.loadSitesFromXML(sitesEl, paramsToAdd);
		
		/* Load Curve Archiver						*/
		Element archiverEl = root.element(AsciiFileCurveArchiver.XML_METADATA_NAME);
		CurveResultsArchiver archiver = AsciiFileCurveArchiver.fromXMLMetadata(archiverEl);
		
		/* Load calc settings						*/
		Element calcSettingsEl = root.element(CalculationSettings.XML_METADATA_NAME);
		CalculationSettings calcSettings = CalculationSettings.fromXMLMetadata(calcSettingsEl);
		
		return new CalculationInputsXMLFile(erf, imrMaps, imts, sites, calcSettings, archiver);
	}
	
	public static final String XML_IMRS_NAME = "IMRs";
	
	public static Element imrsToXML(ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs,
			Element root) {
		Element imrsEl = root.addElement(XML_IMRS_NAME);
		
		for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
			if (imr instanceof IntensityMeasureRelationship) {
				IntensityMeasureRelationship attenRel = (IntensityMeasureRelationship)imr;
				attenRel.toXMLMetadata(imrsEl);
			} else {
				throw new ClassCastException("Currently only IntensityMeasureRelationship subclasses can be saved" +
						" to XML.");
			}
		}
		
		return root;
	}
	
	public static ArrayList<ScalarIntensityMeasureRelationshipAPI> imrsFromXML(Element imrsEl) throws InvocationTargetException {
		ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs =
			new ArrayList<ScalarIntensityMeasureRelationshipAPI>();
		
		Iterator<Element> it = imrsEl.elementIterator();
		while (it.hasNext()) {
			Element imrEl = it.next();
			
			ScalarIntensityMeasureRelationshipAPI imr = 
				(ScalarIntensityMeasureRelationshipAPI) IntensityMeasureRelationship.fromXMLMetadata(imrEl, null);
			imrs.add(imr);
		}
		
		return imrs;
	}
	
	public static final String XML_IMR_MAP_NAME = "IMR_Map";
	public static final String XML_IMR_MAPING_NAME = "IMR_Maping";
	
	public static Element imrMapToXML(Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> map,
			List<DependentParameterAPI<Double>> imts,
			Element root, int index) {
		Element mapEl = root.addElement(XML_IMR_MAP_NAME);
		mapEl.addAttribute("index", index + "");
		
		for (TectonicRegionType tect : map.keySet()) {
			Element mapingEl = mapEl.addElement(XML_IMR_MAPING_NAME);
			ScalarIntensityMeasureRelationshipAPI imr = map.get(tect);
			mapingEl.addAttribute("tectonicRegionType", tect.toString());
			mapingEl.addAttribute("imr", imr.getShortName());
		}
		
		if (imts != null) {
			imts.get(index).toXMLMetadata(mapEl, IntensityMeasureRelationship.XML_METADATA_IMT_NAME);
		}
		
		return root;
	}
	
	public static DependentParameterAPI<Double> imtFromXML(
			ScalarIntensityMeasureRelationshipAPI testIMR,
			Element imrMapEl) {
		Element imtElem = imrMapEl.element(IntensityMeasureRelationship.XML_METADATA_IMT_NAME);
		if (imtElem == null)
			return null;
		
		String imtName = imtElem.attributeValue("name");

		System.out.println("IMT Name: " + imtName);

		testIMR.setIntensityMeasure(imtName);

		DependentParameterAPI<Double> imt = (DependentParameterAPI<Double>) testIMR.getIntensityMeasure();

		imt.setValueFromXMLMetadata(imtElem);
		
		return imt;
	}
	
	public static List<DependentParameterAPI<Double>> imtsFromXML(
			ScalarIntensityMeasureRelationshipAPI testIMR,
			Element imrMapsEl) {
		ArrayList<DependentParameterAPI<Double>> imts = new ArrayList<DependentParameterAPI<Double>>();
		
		Iterator<Element> it = imrMapsEl.elementIterator(XML_IMR_MAP_NAME);
		
		// this makes sure they get loaded in correct order
		HashMap<Integer, DependentParameterAPI<Double>> listsMap = 
			new HashMap<Integer, DependentParameterAPI<Double>>();
		while (it.hasNext()) {
			Element imrMapEl = it.next();
			int index = Integer.parseInt(imrMapEl.attributeValue("index"));
			DependentParameterAPI<Double> imt = imtFromXML(testIMR, imrMapEl);
			if (imt == null)
				return null;
			listsMap.put(new Integer(index), imt);
		}
		for (int i=0; i<listsMap.size(); i++) {
			imts.add(listsMap.get(new Integer(i)));
		}
		
		return imts;
	}
	
	public static HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMapFromXML(
			ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs, Element imrMapEl) {
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> map =
			new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		
		Iterator<Element> it = imrMapEl.elementIterator(XML_IMR_MAPING_NAME);
		
		while (it.hasNext()) {
			Element mappingEl = it.next();
			
			String tectName = mappingEl.attributeValue("tectonicRegionType");
			String imrName = mappingEl.attributeValue("imr");
			
			TectonicRegionType tect = TectonicRegionType.getTypeForName(tectName);
			ScalarIntensityMeasureRelationshipAPI imr = null;
			for (ScalarIntensityMeasureRelationshipAPI testIMR : imrs) {
				if (imrName.equals(testIMR.getShortName())) {
					imr = testIMR;
					break;
				}
			}
			if (imr == null)
				throw new RuntimeException("IMR '" + imrName + "' not found in XML mapping lookup");
			map.put(tect, imr);
		}
		
		return map;
	}
	
	public static final String XML_IMR_MAP_LIST_NAME = "IMR_Maps";
	
	public static Element imrMapsToXML(
			ArrayList<Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> maps,
			List<DependentParameterAPI<Double>> imts, Element root) {
		Element mapsEl = root.addElement(XML_IMR_MAP_LIST_NAME);
		
		for (int i=0; i<maps.size(); i++) {
			Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> map = maps.get(i);
			mapsEl = imrMapToXML(map, imts, mapsEl, i);
		}
		
		return root;
	}
	
	public static ArrayList<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMapsFromXML(
			ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs,
			Element imrMapsEl) {
		ArrayList<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> maps =
			new ArrayList<HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>>();
		
		Iterator<Element> it = imrMapsEl.elementIterator(XML_IMR_MAP_NAME);
		
		// this makes sure they get loaded in correct order
		HashMap<Integer, HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>> mapsMap = 
			new HashMap<Integer, HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>>();
		while (it.hasNext()) {
			Element imrMapEl = it.next();
			int index = Integer.parseInt(imrMapEl.attributeValue("index"));
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> map = imrMapFromXML(imrs, imrMapEl);
			mapsMap.put(new Integer(index), map);
		}
		for (int i=0; i<mapsMap.size(); i++) {
			maps.add(mapsMap.get(new Integer(i)));
		}
		
		return maps;
	}

}
