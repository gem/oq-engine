/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb;

import java.io.FileWriter;
import java.io.IOException;
import java.io.Serializable;
import java.net.URL;
import java.util.ArrayList;
import java.util.Iterator;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import org.dom4j.io.OutputFormat;
import org.dom4j.io.SAXReader;
import org.dom4j.io.XMLWriter;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.DeformationModelSummaryDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.vo.DeformationModelSummary;


/**
 * This class holds a deformation model summary (name, associated fault model) for each deformation model.
 * 
 * @author Ned Field
 *
 */
public class DeformationModelSummaryFinal implements Serializable {
	
	private static ArrayList<DeformationModelSummary> deformationModelSummariesList;
	private static final String XML_DATA_FILENAME = "DeformationModelSummaries.xml";

	  public DeformationModelSummaryFinal() {
		  // do this once to create file, and then comment it out
//		  writeDeformationModelSummariesXML_File();
		  readDeformationModelSummariesXML_File();
	  }

	  /**
	   * Get a deformation model based on deformation model ID
	   * 
	   * @param faultModelId
	   * @return
	   * @throws QueryException
	   */
	  public DeformationModelSummary getDeformationModel(int deformationModelId) throws QueryException {
		
		for (DeformationModelSummary def : deformationModelSummariesList) {
			if (def.getDeformationModelId() == deformationModelId)
				return def;
		}
		
	    return null;

	  }
	  
	  /**
	   * Get all the deformation Models from the database
	   * @return
	   * @throws QueryException
	   */
	  public ArrayList getAllDeformationModels() throws QueryException {
	   return deformationModelSummariesList;
	  }

	  
	  /**
	   * Get a deformation model based on deformation model Name
	   * 
	   * @param deformationModelName
	   * @return
	   * @throws QueryException
	   */
	  public DeformationModelSummary getDeformationModel(String deformationModelName) throws QueryException {
		  for (DeformationModelSummary def : deformationModelSummariesList) {
				if (def.getDeformationModelName().equals(deformationModelName))
					return def;
			}
			
		    return null;
	  }
	  
	  /**
	   * This reads from the oracle database and writes the results to an XML file (only need to do once)
	   */
	private void writeDeformationModelSummariesXML_File() {
		DeformationModelSummaryDB_DAO deformationModelSummaryDB_DAO = new DeformationModelSummaryDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
		ArrayList<DeformationModelSummary> deformationModelSummariesFromDatabaseList = deformationModelSummaryDB_DAO.getAllDeformationModels();
		DeformationModelSummary deformationModelSummary;
		
		Document document = DocumentHelper.createDocument();
		Element root = document.addElement( "DeformationModelSummaries" );
		
		for(int i=0; i<deformationModelSummariesFromDatabaseList.size(); ++i) {
			deformationModelSummary = (DeformationModelSummary) deformationModelSummariesFromDatabaseList.get(i);
			
			root = deformationModelSummary.toXMLMetadata(root);
			
//			System.out.print(deformationModelSummary.getDeformationModelId()+", ");
//			System.out.print(deformationModelSummary.getDeformationModelName()+", ");
//			System.out.print(deformationModelSummary.getContributor()+", ");	// this is an object with no toString() method
//			System.out.print(deformationModelSummary.getFaultModel()+"\n");	// this is an object with no toString() method
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
		
		//do this for now (until read from XML is implemented
		deformationModelSummariesList = deformationModelSummariesFromDatabaseList;
	}
	  
	  /**
	   * This reads the XML file containing the deformation model summaries and puts them into deformationModelSummariesList
	   */
	private void readDeformationModelSummariesXML_File() {
		SAXReader reader = new SAXReader();
		deformationModelSummariesList = new ArrayList<DeformationModelSummary>();

		try {
			URL xmlURL = DeformationModelSummaryFinal.class.getResource(XML_DATA_FILENAME);
			Document document = reader.read(xmlURL);
			Element root = document.getRootElement();

			Iterator<Element> it = root.elementIterator();
			while (it.hasNext()) {
				Element el = it.next();
				
				DeformationModelSummary def = DeformationModelSummary.fromXMLMetadata(el);
//				System.out.println("Loaded Def Model: " + def.getDeformationModelName() + " " + def.getDeformationModelId());
				deformationModelSummariesList.add(def);
			}
		} catch (DocumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	  
	  
	public static void main(String[] args) {
		DeformationModelSummaryFinal test = new DeformationModelSummaryFinal();
	}
}
