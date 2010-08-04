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

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.fileGen;

import java.io.FileWriter;
import java.io.IOException;
import java.text.Collator;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;

import org.dom4j.Document;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import org.dom4j.io.OutputFormat;
import org.dom4j.io.XMLWriter;
import org.opensha.commons.geo.Location;
import org.opensha.refFaultParamDb.vo.DeformationModelSummary;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelPrefDataFinal;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelSummaryFinal;
import org.opensha.sha.faultSurface.FaultTrace;

public class DeformationModelFileGenerator {
	
	private static final String FILE_PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/data/finalReferenceFaultParamDb/fileGen/";
	
	private boolean sort = true;
	
	DeformationModelSummaryFinal summaries = new DeformationModelSummaryFinal();
	DeformationModelPrefDataFinal defModels = new DeformationModelPrefDataFinal();
	
	ArrayList<DeformationModelSummary> deformationModelSummariesList;
	ArrayList<ArrayList<FaultSectionPrefData>> faulSectionIDListList = new ArrayList<ArrayList<FaultSectionPrefData>>();
	
	/**
	 * This class generates files representations of each deformation model. 
	 */
	public DeformationModelFileGenerator() {
		this.loadDefModels();
	}
	
	/** 
	 * This loads the Deformation Models and Data to ArrayLists to be written later.
	 */
	private void loadDefModels() {
		deformationModelSummariesList = summaries.getAllDeformationModels();
		
		for (DeformationModelSummary summary : deformationModelSummariesList) {
			int id = summary.getDeformationModelId();
			
			ArrayList<FaultSectionPrefData> faultSections = defModels.getAllFaultSectionPrefData(id);
			
			ArrayList<FaultSectionPrefData> noSlips = new ArrayList<FaultSectionPrefData>();
			
			for (FaultSectionPrefData section : faultSections) {
				// skip all sections with NaN slip rates
				if (section.getAveLongTermSlipRate() == Double.NaN ||
						(section.getAveLongTermSlipRate() + "").equals(Double.NaN + "")) {
//					System.out.println("Skipping Fault " + section.getSectionName());
					noSlips.add(section);
				}
			}
			
			int before = faultSections.size();
			if (noSlips.size() > 0)
				faultSections.removeAll(noSlips);
			System.out.println("Removed " + (before - faultSections.size()) + " NaN Faults for "
					+ summary.getDeformationModelName() + " (" + summary.getFaultModel().getFaultModelName() + ")");
			
			if (sort)
				Collections.sort(faultSections, new FaultSectionNameComparator());
			
			faulSectionIDListList.add(faultSections);
		}
	}
	
	/**
	 * Write the deformation models to XML and text files
	 */
	public void saveToFiles() {
		for (int i=0; i<deformationModelSummariesList.size(); i++) {
			DeformationModelSummary summary = deformationModelSummariesList.get(i);
			ArrayList<FaultSectionPrefData> sections = faulSectionIDListList.get(i);
			
			String filePrefix = FILE_PATH + "DeformationModel_" + summary.getDeformationModelName();
			
			// save to XML
			this.saveDefModelToXML(summary, sections, filePrefix);
			this.saveDefModelToText(summary, sections, filePrefix);
		}
	}
	
	/**
	 * Writes a given deformation model to a text file
	 * @param model
	 * @param sections
	 * @param filePrefix
	 */
	private void saveDefModelToText(DeformationModelSummary model, ArrayList<FaultSectionPrefData> sections, String filePrefix) {
		String fileName = filePrefix + ".txt";
		
		System.out.println("Writing Text " + model.getDeformationModelName() + " to " + fileName);
		
		try {
			FileWriter fw = new FileWriter(fileName);
			
//			#Section Name
//			#Ave Upper Seis Depth (km)
//			#Ave Lower Seis Depth (km)
//			#Ave Dip (degrees)
//			#Ave Long Term Slip Rate
//			#Ave Long Term Slip Rate Standard Deviation
//			#Ave Aseismic Slip Factor
//			#Ave Rake
//			#Trace Length (derivative value) (km)
//			#Num Trace Points
//			#lat1 lon1
//			#lat2 lon2 
			
			// write the header
			fw.write("#********************************" + "\n");
			fw.write("# This file represents a WGCEP UCERF 2 Deformation Model" + "\n");
			fw.write("#" + "\n");
			fw.write("# Deformation Model Name: " + model.getDeformationModelName() + "\n");
			fw.write("# Fault Model Name: " + model.getFaultModel().getFaultModelName() + "\n");
			fw.write("#" + "\n");
			fw.write("# Each fault trace is separated by an empty line." + "\n");
			fw.write("# The fields for each fault section are as follows:" + "\n");
			fw.write("# Section Name" + "\n");
			fw.write("# Ave Upper Seis Depth (km)" + "\n");
			fw.write("# Ave Lower Seis Depth (km)" + "\n");
			fw.write("# Ave Dip (degrees) defined by http://www.opensha.org/documentation/glossary/AkiRichardsDefn.html" + "\n");
			fw.write("# Ave Long Term Slip Rate" + "\n");
			fw.write("# Ave Long Term Slip Rate Standard Deviation" + "\n");
			fw.write("# Ave Aseismic Slip Factor" + "\n");
			fw.write("# Ave Rake defined by http://www.opensha.org/documentation/glossary/AkiRichardsDefn.html" + "\n");
//			fw.write("#Trace Length (derivative value) (km)" + "\n");
			fw.write("# Num Trace Points" + "\n");
			fw.write("# lat1 lon1" + "\n");
			fw.write("# lat2 lon2" + "\n");
			fw.write("# latN lonN" + "\n");
			fw.write("#********************************" + "\n");
			
			for (FaultSectionPrefData section : sections) {
				fw.write(section.getSectionName() + "\n");
				fw.write((float)section.getAveUpperDepth() + "\n");
				fw.write((float)section.getAveLowerDepth() + "\n");
				fw.write((float)section.getAveDip() + "\n");
				fw.write((float)section.getAveLongTermSlipRate() + "\n");
				fw.write((float)section.getSlipRateStdDev() + "\n");
				fw.write((float)section.getAseismicSlipFactor() + "\n");
				fw.write((float)section.getAveRake() + "\n");
				
				FaultTrace trace = section.getFaultTrace();
				
				fw.write(trace.getNumLocations() + "\n");
				
				for (int i=0; i<trace.getNumLocations(); i++) {
					Location loc = trace.get(i);
					
					fw.write(loc.getLatitude() + " " + loc.getLongitude() + "\n");
				}
				fw.write("\n");
			}
			fw.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	/**
	 * Writes a given deformation model to XML
	 * @param model
	 * @param sections
	 * @param filePrefix
	 */
	private void saveDefModelToXML(DeformationModelSummary model, ArrayList<FaultSectionPrefData> sections, String filePrefix) {
		String fileName = filePrefix + ".xml";
		
		Document document = DocumentHelper.createDocument();
		Element root = document.addElement( "DeformationModel" );
		
		root = model.toXMLMetadata(root);
		root = model.getFaultModel().toXMLMetadata(root);
		Element sectionsEl = root.addElement("FaultSections");
		for (FaultSectionPrefData section : sections) {
			sectionsEl = section.toXMLMetadata(root);
		}
		
		XMLWriter writer;

		try {
			OutputFormat format = OutputFormat.createPrettyPrint();

			System.out.println("Writing XML " + model.getDeformationModelName() + " to " + fileName);
			writer = new XMLWriter(new FileWriter(fileName), format);
			writer.write(document);
			writer.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	public void printComparisonTable() {
		// slow but easy to program this way
		ArrayList<Integer> differing = new ArrayList<Integer>();
		
		int max_model = 3;
		
		for (int i=0; i<deformationModelSummariesList.size(); i++) {
			if (i == max_model)
				break;
			DeformationModelSummary summary = deformationModelSummariesList.get(i);
			ArrayList<FaultSectionPrefData> sections = faulSectionIDListList.get(i);
			
			for (int j=0; j<sections.size(); j++) {
				FaultSectionPrefData section = sections.get(j);
				for (int k=0; k<deformationModelSummariesList.size(); k++) {
					if (k == max_model)
						break;
					DeformationModelSummary summary2 = deformationModelSummariesList.get(k);
					ArrayList<FaultSectionPrefData> sections2 = faulSectionIDListList.get(k);
					
					FaultSectionPrefData section2 = sections2.get(j);
					
					float slip1 = (float)section.getAveLongTermSlipRate();
					float slip2 = (float)section2.getAveLongTermSlipRate();
					
					if (slip1 != slip2) {

						boolean contains = false;

						for (Integer theInt : differing) {
							int l = theInt;
							if (l == j) {
								contains = true;
								break;
							}
						}
						if (!contains) {
//							System.out.println(slip1 + " " + slip2);
							differing.add(j);
						}
						break;
					}
				}
			}
			if (i > 0)
//				System.out.print("ID\t");
//			else
				System.out.print("\t\t");
			System.out.print(summary.getDeformationModelName());
		}
		for (Integer id : differing) {
			System.out.println();
//			System.out.print(faulSectionIDListList.get(0).get(id).getSectionId());
			for (int i=0; i<deformationModelSummariesList.size(); i++) {
				if (i == max_model)
					break;
				ArrayList<FaultSectionPrefData> sections = faulSectionIDListList.get(i);
				float slip = (float)sections.get(id).getAveLongTermSlipRate();
				float stdDev = (float)sections.get(id).getSlipRateStdDev();
				System.out.print(slip + "(" + stdDev + ")" + "\t");
			}
			System.out.print(faulSectionIDListList.get(0).get(id).getSectionName());
		}
	}
	
	public static void main(String args[]) {
		DeformationModelFileGenerator gen = new DeformationModelFileGenerator();
		gen.saveToFiles();
		gen.printComparisonTable();
	}
	
	/**
	 * Class for sorting fault sections by name
	 * @author kevin
	 *
	 */
	class FaultSectionNameComparator implements Comparator<FaultSectionPrefData> {
		// A Collator does string comparisons
		private Collator c = Collator.getInstance();
		
		/**
		 * This is called when you do Arrays.sort on an array or Collections.sort on a collection (IE ArrayList).
		 * 
		 * It simply compares their names using a Collator. It doesn't know how to compare
		 * a file with a directory, and returns -1 in this case.
		 */
		public int compare(FaultSectionPrefData f1, FaultSectionPrefData f2) {
			if(f1 == f2)
				return 0;

			// let the Collator do the string comparison, and return the result
			return c.compare(f1.getSectionName(), f2.getSectionName());
		}
	}
}
