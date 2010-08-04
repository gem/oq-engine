/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb;

import java.io.FileWriter;
import java.io.IOException;
import java.io.Serializable;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import org.dom4j.io.OutputFormat;
import org.dom4j.io.SAXReader;
import org.dom4j.io.XMLWriter;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.DeformationModelPrefDataDB_DAO;
import org.opensha.refFaultParamDb.vo.DeformationModelSummary;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;

/**
 * 
 * This provides static access to the final preferred data for each deformation model
 * (this does not access the oracle database dynamically, except for the one-time creation
 * of the static data files).
 * 
 * TO DO: need to implement methods that saves the data in the HashMaps 
 * (slipRateMap;aseismicSlipMap;stdDevMap;faultSectionIdIndexMapMap;faultSectionIdMap)
 * to a static file (ascii or XML), which will be run only once to create the files,
 * and then another to read the HashMap data back in from those files (which the constructor
 * will use).
 * 
 * @author Ned Field
 *
 */
public class DeformationModelPrefDataFinal implements Serializable {
	
	/*
	 * For each deformation model we need to store a faultSectionIdList and arrays of the following:
	 * slipRate, slipRateStdDev, aseismicSlip
	 */
	
	private static final String XML_DATA_FILENAME = "DeformationModelPrefData.xml";
	
	// these will store the data for each deformation model
	private static HashMap slipRateMap;
	private static HashMap aseismicSlipMap;
	private static HashMap stdDevMap;
	private static HashMap faultSectionIdIndexMapMap; // a map of maps (the array index for each Id, for each def model)
	private static HashMap<Integer, ArrayList<Integer>> faultSectionIdMap; // contains Array list of fault sections Ids for each def model
	
	private PrefFaultSectionDataFinal prefFaultSectionDataFinal;
	
	DeformationModelSummaryFinal deformationModelSummaryFinal; // keep copy of this for accessing more info about def models
	
	public DeformationModelPrefDataFinal() {
		prefFaultSectionDataFinal = new PrefFaultSectionDataFinal();
//		writeDeformationModelSummariesXML_File();
		readDeformationModelSummariesXML_File();
	}
	
	
	private void writeDeformationModelSummariesXML_File() {

		// need one of these for each deformation model
		HashMap faultSectionIdIndexMap;
		double[] slipRateList, slipRateStdDevList, aseismicSlipList;
		
		// these are where they are stored
		slipRateMap = new HashMap();
		aseismicSlipMap = new HashMap();
		stdDevMap = new HashMap();
		faultSectionIdIndexMapMap = new HashMap();
		faultSectionIdMap = new HashMap();
		
		Document document = DocumentHelper.createDocument();
		Element root = document.addElement( "DeformationModelPrefData" );
		
		DeformationModelPrefDataDB_DAO deformationModelPrefDB_DAO = new DeformationModelPrefDataDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
		deformationModelSummaryFinal = new DeformationModelSummaryFinal();
		ArrayList<DeformationModelSummary> deformationModelSummaryList = deformationModelSummaryFinal.getAllDeformationModels();
		for(int i=0; i<deformationModelSummaryList.size();i++) {
			
			
			DeformationModelSummary dmSummary = deformationModelSummaryList.get(i);
//			System.out.println(dmSummary.getDeformationModelName()+",  "+dmSummary.getDeformationModelId());
			int defModId = dmSummary.getDeformationModelId();
			ArrayList faultSectionIdList = deformationModelPrefDB_DAO.getFaultSectionIdsForDeformationModel(defModId);
			faultSectionIdIndexMap = new HashMap();
			slipRateList = new double[faultSectionIdList.size()];
			slipRateStdDevList = new double[faultSectionIdList.size()];
			aseismicSlipList = new double[faultSectionIdList.size()];
			
			Element el = root.addElement("DeformationModel");
			el.addAttribute("defModId", dmSummary.getDeformationModelId() + "");
			
			
			
			for(int j=0;j<faultSectionIdList.size();j++) {
				int faultSectionId = ((Integer) faultSectionIdList.get(j)).intValue();
				
				faultSectionIdIndexMap.put(faultSectionId, new Integer(j));
				slipRateList[j]=deformationModelPrefDB_DAO.getSlipRate(defModId, faultSectionId);
				slipRateStdDevList[j]=deformationModelPrefDB_DAO.getSlipStdDev(defModId, faultSectionId);
				aseismicSlipList[j] = deformationModelPrefDB_DAO.getAseismicSlipFactor(defModId, faultSectionId);
				
				Element faultSectionEl = el.addElement("FaultSectionDefModelData");
				faultSectionEl.addAttribute("faultSectionId", faultSectionId + "");
				faultSectionEl.addAttribute("slipRate", slipRateList[j] + "");
				faultSectionEl.addAttribute("slipRateStdDev", slipRateStdDevList[j] + "");
				faultSectionEl.addAttribute("aseismicSlip", aseismicSlipList[j] + "");
			}
			//now put these in the HashMaps
			slipRateMap.put(defModId, slipRateList);
			stdDevMap.put(defModId, slipRateStdDevList);
			aseismicSlipMap.put(defModId, aseismicSlipList);
			faultSectionIdIndexMapMap.put(defModId, faultSectionIdIndexMap);
			faultSectionIdMap.put(defModId, faultSectionIdList);
		}
		
		XMLWriter writer;

		try {
			OutputFormat format = OutputFormat.createPrettyPrint();

			System.out.println("Writing Deformation Model Summary to " + XML_DATA_FILENAME);
			writer = new XMLWriter(new FileWriter(XML_DATA_FILENAME), format);
			writer.write(document);
			writer.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	/**
	 * Get Fault Section Pref data for a deformation model ID and Fault section Id
	 * @param deformationModelId
	 * @param faultSectionId
	 * @return
	 */
	public FaultSectionPrefData getFaultSectionPrefData(int deformationModelId, int faultSectionId) {

		// first get the default preferred data
		FaultSectionPrefData faultSectionPrefData = prefFaultSectionDataFinal.getFaultSectionPrefData(faultSectionId).clone();
		
		HashMap faultSectionIdIndexMap = (HashMap) faultSectionIdIndexMapMap.get(deformationModelId);
		int indexForSectId = ((Integer) faultSectionIdIndexMap.get(faultSectionId)).intValue();
		
		double[] slipRateList = (double[]) slipRateMap.get(deformationModelId);
		faultSectionPrefData.setAveLongTermSlipRate(slipRateList[indexForSectId]);

		double[] stdDevList = (double[]) stdDevMap.get(deformationModelId);
		faultSectionPrefData.setSlipRateStdDev(stdDevList[indexForSectId]);

		double[] aseismicSlipList = (double[]) aseismicSlipMap.get(deformationModelId);
		faultSectionPrefData.setAseismicSlipFactor(aseismicSlipList[indexForSectId]);

		return faultSectionPrefData;
	}
	
	/**
	 * Get a list of all fault sections within this deformation model
	 * @param deformationModelId
	 * @return
	 */
	public ArrayList<Integer> getFaultSectionIdsForDeformationModel(int deformationModelId) {
		return faultSectionIdMap.get(deformationModelId);
	}
	
	/**
	 * Get all Fault Section Pref data for a deformation model ID
	 * @param deformationModelId
	 * @return
	 */
	public ArrayList<FaultSectionPrefData> getAllFaultSectionPrefData(int deformationModelId) {
		ArrayList<Integer> ids = this.getFaultSectionIdsForDeformationModel(deformationModelId);
		
		ArrayList<FaultSectionPrefData> sections = new ArrayList<FaultSectionPrefData>();
		
		for (int id : ids) {
			sections.add(this.getFaultSectionPrefData(deformationModelId, id).clone());
		}
		
		return sections;
	}
	
	/**
	   * This reads the XML file containing the deformation model summaries and puts them into deformationModelSummariesList
	   */
	private void readDeformationModelSummariesXML_File() {
		// need one of these for each deformation model
		HashMap faultSectionIdIndexMap;
		double[] slipRateList, slipRateStdDevList, aseismicSlipList;
		
		// these are where they are stored
		slipRateMap = new HashMap();
		aseismicSlipMap = new HashMap();
		stdDevMap = new HashMap();
		faultSectionIdIndexMapMap = new HashMap();
		faultSectionIdMap = new HashMap();
		
		SAXReader reader = new SAXReader();
		try {
			URL xmlURL = DeformationModelPrefDataFinal.class.getResource(XML_DATA_FILENAME);
			Document document = reader.read(xmlURL);
			Element root = document.getRootElement();

			Iterator<Element> it = root.elementIterator();
			while (it.hasNext()) {
				Element el = it.next();
				
				int defModId = Integer.parseInt(el.attributeValue("defModId"));
				
				List<Element> elements = el.elements();
				
				int numSections = elements.size();
				
				ArrayList<Integer> faultSectionIdList = new ArrayList<Integer>(); 
				faultSectionIdIndexMap = new HashMap();
				slipRateList = new double[numSections];
				slipRateStdDevList = new double[numSections];
				aseismicSlipList = new double[numSections];
				
				int i = 0;
				for (Element faultSection : elements) {
					int faultSectionId = Integer.parseInt(faultSection.attributeValue("faultSectionId"));
					faultSectionIdList.add(faultSectionId);
					
					faultSectionIdIndexMap.put(faultSectionId, new Integer(i));
					slipRateList[i]=Double.parseDouble(faultSection.attributeValue("slipRate"));
					slipRateStdDevList[i]=Double.parseDouble(faultSection.attributeValue("slipRateStdDev"));
					aseismicSlipList[i] = Double.parseDouble(faultSection.attributeValue("aseismicSlip"));
					
					i++;
				}
				
				//now put these in the HashMaps
				slipRateMap.put(defModId, slipRateList);
				stdDevMap.put(defModId, slipRateStdDevList);
				aseismicSlipMap.put(defModId, aseismicSlipList);
				faultSectionIdIndexMapMap.put(defModId, faultSectionIdIndexMap);
				faultSectionIdMap.put(defModId, faultSectionIdList);
			}
		} catch (DocumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	private void saveCompleteXMLFile() {
		
	}
	
	public static void main(String[] args) {
		DeformationModelPrefDataFinal test = new DeformationModelPrefDataFinal();
	}
}
