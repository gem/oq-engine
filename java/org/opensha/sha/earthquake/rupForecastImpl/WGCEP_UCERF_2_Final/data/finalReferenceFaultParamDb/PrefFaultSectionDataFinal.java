/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb;

import java.io.FileWriter;
import java.io.IOException;
import java.io.Serializable;
import java.lang.reflect.InvocationTargetException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import org.dom4j.io.OutputFormat;
import org.dom4j.io.SAXReader;
import org.dom4j.io.XMLWriter;
import org.opensha.commons.geo.Location;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.PrefFaultSectionDataDB_DAO;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.faultSurface.FaultTrace;
/**
 * <p>Title: PrefFaultSectionDataFinal.java </p>
 * <p>Description: This class reads the Preferred Fault Section Data from an XML file.
 * @author Ned Field
 * @version 1.0
 *
 */
public class PrefFaultSectionDataFinal implements Serializable {
	private static ArrayList<FaultSectionPrefData> faultSectionsList;
	private static ArrayList<FaultSectionPrefData> dbFaultSectionsList = new ArrayList<FaultSectionPrefData>();
	private static HashMap indexForID_Map;
	private static HashMap dbMap;
	
	private static final String XML_DATA_FILENAME = "PrefFaultSectionData.xml";
	
	public PrefFaultSectionDataFinal() {
//		writeFaultSectionDataFromDatabaseTo_XML();
		readFaultSectionDataFromXML();
		
	}
	
	int numSections = 0;
	ArrayList<Integer> faultNums = new ArrayList<Integer>();
	
	private void test() {
		System.out.println("TESTING!");
		for (Integer num : faultNums) {
			int i = num;
//			System.out.println("Testint fault " + i);
			FaultSectionPrefData dbFault = (FaultSectionPrefData)dbFaultSectionsList.get((Integer)dbMap.get(new Integer(i)));
			FaultSectionPrefData fileFault = (FaultSectionPrefData)faultSectionsList.get((Integer)dbMap.get(new Integer(i)));
			
			if (dbFault.getSectionId() != fileFault.getSectionId())
				System.out.println("ERROR: Id's not equal!");
			
			if (dbFault.getAseismicSlipFactor() != fileFault.getAseismicSlipFactor())
				System.out.println("ERROR: Test Failed 1");
			
			if (dbFault.getAveDip() != fileFault.getAveDip())
				System.out.println("ERROR: Test Failed 2");
			
//			if (dbFault.getAveLongTermSlipRate() != fileFault.getAveLongTermSlipRate()) {
//				System.out.println("ERROR: Test Failed 3");
//				System.out.println(dbFault.getAveLongTermSlipRate() + " " + dbFault.getAveLongTermSlipRate());
//			}
			
			if (dbFault.getAveLowerDepth() != fileFault.getAveLowerDepth())
				System.out.println("ERROR: Test Failed 4");
			
//			if (dbFault.getAveRake() != fileFault.getAveRake()) {
//				System.out.println("ERROR: Test Failed 5");
//				System.out.println(dbFault.getAveRake() + " " + dbFault.getAveRake());
//			}
			
			if (dbFault.getAveUpperDepth() != fileFault.getAveUpperDepth())
				System.out.println("ERROR: Test Failed 6");
			
			if (dbFault.getDipDirection() != fileFault.getDipDirection())
				System.out.println("ERROR: Test Failed 7");
			
			if (dbFault.getSectionId() != fileFault.getSectionId())
				System.out.println("ERROR: Test Failed 9");
			
			if (!dbFault.getSectionName().equals(fileFault.getSectionName()))
				System.out.println("ERROR: Test Failed 10");
			
//			if (!dbFault.getShortName().equals(dbFault.getShortName()))
//				System.out.println("ERROR: Test Failed 11");
			
			if (dbFault.getLength() != fileFault.getLength())
				System.out.println("ERROR: Test Failed 12");
			
			if (dbFault.getDownDipWidth() != fileFault.getDownDipWidth())
				System.out.println("ERROR: Test Failed 13");
			
			if (dbFault.getSlipRateStdDev() != fileFault.getSlipRateStdDev())
				System.out.println("ERROR: Test Failed 14");
			
			FaultTrace dbTrace = dbFault.getFaultTrace();
			FaultTrace fileTrace = fileFault.getFaultTrace();
			
			for (int j=0; j<dbTrace.getNumLocations(); j++) {
				Location dbLoc = dbTrace.get(j);
				Location fileLoc = fileTrace.get(j);
				
				if (!dbLoc.equals(fileLoc)) {
					System.out.println("Loc on fault trace is bad!");
					System.out.println(dbLoc);
					System.out.println(fileLoc);
				}
			}
		}
	}


	private void writeFaultSectionDataFromDatabaseTo_XML() {
		PrefFaultSectionDataDB_DAO faultSectionDAO = new PrefFaultSectionDataDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
		ArrayList faultSectionDataListFromDatabase = faultSectionDAO.getAllFaultSectionPrefData();
		
		Document document = DocumentHelper.createDocument();
		Element root = document.addElement( "PrefFaultSectionData" );
		
		// make the index to ID hashmap
		indexForID_Map = new HashMap();
		dbMap = new HashMap();
		FaultSectionPrefData fspd;
		for(int i=0; i<faultSectionDataListFromDatabase.size(); i++) {
			fspd = (FaultSectionPrefData) faultSectionDataListFromDatabase.get(i);
			
			root = fspd.toXMLMetadata(root);
			
			indexForID_Map.put(fspd.getSectionId(), new Integer(i));
			dbMap.put(fspd.getSectionId(), new Integer(i));
//			System.out.println(fspd.getSectionId()+"\t"+fspd.getSectionName());
			faultNums.add(new Integer(fspd.getSectionId()));
			dbFaultSectionsList.add(fspd);
		}
		
		// save each fault section to an XML file (save all elements that have an associated set method in FaultSectionPrefData) 
		
		XMLWriter writer;


		try {
			OutputFormat format = OutputFormat.createPrettyPrint();

			System.out.println("Writing Pref Fault Section Data to " + XML_DATA_FILENAME);
			writer = new XMLWriter(new FileWriter(XML_DATA_FILENAME), format);
			writer.write(document);
			writer.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		// need the following until the read* method is implemented
		faultSectionsList = faultSectionDataListFromDatabase;
	}
	
	/**
	 * This reads the XML file and populates faultSectionsList 
	 */
	private void readFaultSectionDataFromXML() {
		
		SAXReader reader = new SAXReader();
		faultSectionsList = new ArrayList<FaultSectionPrefData>();
		indexForID_Map = new HashMap();
        try {
			URL xmlURL = PrefFaultSectionDataFinal.class.getResource(XML_DATA_FILENAME);
			Document document = reader.read(xmlURL);
			Element root = document.getRootElement();
			
			Iterator<Element> it = root.elementIterator();
			while (it.hasNext()) {
				Element el = it.next();

				FaultSectionPrefData data;
				try {
					data = FaultSectionPrefData.fromXMLMetadata(el);
					faultSectionsList.add(data);
				} catch (InvocationTargetException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} 
			}
			
			for (int i=0; i<faultSectionsList.size(); i++) {
				FaultSectionPrefData fspd = faultSectionsList.get(i);
				indexForID_Map.put(fspd.getSectionId(), new Integer(i));
			}
		} catch (DocumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	/**
	 * Get a list of all Fault Section Pref Data from the database
	 * @return
	 */
	public ArrayList getAllFaultSectionPrefData() {
		return faultSectionsList;
	}
	
	/**
	 * Get Preferred fault section data for a Fault Section Id
	 * @param faultSectionId
	 * @return
	 */
	public FaultSectionPrefData getFaultSectionPrefData(int faultSectionId) {
		int index = ((Integer)indexForID_Map.get(faultSectionId)).intValue();
		return faultSectionsList.get(index);
	}
	
	public static void main(String[] args) {
		PrefFaultSectionDataFinal test = new PrefFaultSectionDataFinal();
		ArrayList junk = test.getAllFaultSectionPrefData();
		FaultSectionPrefData faultSectionPrefData = (FaultSectionPrefData) junk.get(5);
		int id = faultSectionPrefData.getSectionId();
		System.out.println(id);
		FaultSectionPrefData faultSectionPrefData2 = test.getFaultSectionPrefData(id);
		System.out.println(faultSectionPrefData2.getSectionId());
		
		test.test();
	}

}
