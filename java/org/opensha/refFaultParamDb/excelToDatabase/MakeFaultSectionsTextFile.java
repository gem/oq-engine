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

package org.opensha.refFaultParamDb.excelToDatabase;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.FaultSectionData;
import org.opensha.sha.faultSurface.FaultTrace;



public class MakeFaultSectionsTextFile {
	
	private final static String SECTIONS_TXT_FILENAME = "FaultSectionsVer2.txt";
	private final static String ESTIMATE = "Estimate";
	private final static String SECTION_SOURCE = "Section_Source";
	
	public MakeFaultSectionsTextFile() {
		FaultSectionVer2_DB_DAO faultSectionDAO = new FaultSectionVer2_DB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
		try {
			FileWriter fw = new FileWriter(SECTIONS_TXT_FILENAME);
			// get all the fault sections from the database
			ArrayList faultSections  = faultSectionDAO.getAllFaultSections();
			int numSections = faultSections.size();
			// iterate over all the fault sections and write them to the file
			for(int i=0; i<numSections; ++i) {
				FaultSectionData faultSection = (FaultSectionData)faultSections.get(i);
				fw.write(faultSection.getSectionId()+";"+faultSection.getSectionName()+";"+
						faultSection.getSource()+"\n");
				//fw.write("#"+faultSection.getSectionName()+"\n");
				/*fw.write(FaultSectionVer2_DB_DAO.SECTION_ID+"="+faultSection.getSectionId()+"\n");
				fw.write(FaultSectionVer2_DB_DAO.ENTRY_DATE+"="+faultSection.getEntryDate()+"\n");
				fw.write(FaultSectionVer2_DB_DAO.DIP_DIRECTION+"="+faultSection.getDipDirection()+"\n");
				fw.write(SECTION_SOURCE+"="+faultSection.getSource()+"\n");
				fw.write(FaultSectionVer2_DB_DAO.COMMENTS+"="+faultSection.getComments()+"\n");
				writeEstimateToFile(fw, faultSection.getAseismicSlipFactorEst(), FaultSectionVer2_DB_DAO.ASEISMIC_SLIP_FACTOR_EST);
				writeEstimateToFile(fw, faultSection.getAveDipEst(), FaultSectionVer2_DB_DAO.AVE_DIP_EST);
				writeEstimateToFile(fw, faultSection.getAveLongTermSlipRateEst(), FaultSectionVer2_DB_DAO.AVE_LONG_TERM_SLIP_RATE_EST);
				writeEstimateToFile(fw, faultSection.getAveLowerDepthEst(), FaultSectionVer2_DB_DAO.AVE_LOWER_DEPTH_EST);
				writeEstimateToFile(fw, faultSection.getAveRakeEst(), FaultSectionVer2_DB_DAO.AVE_RAKE_EST);
				writeEstimateToFile(fw, faultSection.getAveUpperDepthEst(), FaultSectionVer2_DB_DAO.AVE_UPPER_DEPTH_EST);
				writeFaultTraceToFile(fw, faultSection.getFaultTrace());*/
			}
			fw.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}
	
	/**
	 * Write Fault trace to file
	 * 
	 * @param fw
	 */
	private void writeFaultTraceToFile(FileWriter fw, FaultTrace faultTrace) throws IOException {
		fw.write(FaultSectionVer2_DB_DAO.FAULT_TRACE+"="+faultTrace.getNumLocations()+"\n");
		for(int i=0; i<faultTrace.getNumLocations(); ++i) {
			Location location = faultTrace.get(i);
			fw.write(location.getLongitude()+"\t"+location.getLatitude()+"\n");
		}
	}
	
	
	/**
	 * Write estimate instance to  file
	 * @param fw
	 * @param estimateInstance
	 * @param label
	 * @throws IOException
	 */
	private void writeEstimateToFile(FileWriter fw, EstimateInstances estimateInstance, String label) throws IOException {
		fw.write(label+"="+ESTIMATE+"\n");
	    fw.write(estimateInstance.getEstimate().toString()+"\n");
	    fw.write(label+" Units="+estimateInstance.getUnits()+"\n");
	}
	
	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		new MakeFaultSectionsTextFile();
	}

}
