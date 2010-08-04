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
import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSection2002DB_DAO;
import org.opensha.refFaultParamDb.vo.FaultSection2002;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 * <p>Title: Read2002FaultSections.java </p>
 * <p>Description: Read the 2002 fault sections from the database and save
 * in a file to see that the info is correct. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class Read2002FaultSections {
  private FaultSection2002DB_DAO faultSection2002DAO = new FaultSection2002DB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
  private final static String SECTION_TRACE_OUT_FILENAME = "FaultSections_Trace2002.txt";
  private final static String SECTION_NAMES_FILENAME="FaultSections_Name2002.txt";
  //private final static String DIP_FILENAME = "DipForFaultSections2002.txt";
  public Read2002FaultSections() {
    ArrayList faultSections  = faultSection2002DAO.getAllFaultSections();
    try {
      FileWriter fwTrace = new FileWriter(SECTION_TRACE_OUT_FILENAME);
      FileWriter fwNames = new FileWriter(SECTION_NAMES_FILENAME);
      fwTrace.write("#SectionName,AvgUppeSeisDepth, AvgLowerSeisDepth, AveDip\n");
      //FileWriter fwDip = new FileWriter(DIP_FILENAME);
      for (int i = 0; i < faultSections.size(); ++i) {
        FaultSection2002 faultSection = (FaultSection2002) faultSections.get(i);
        fwTrace.write("#"+faultSection.getSectionName()+","+faultSection.getAveUpperSeisDepth()+","+
        		faultSection.getAveLowerSeisDepth()+","+faultSection.getAveDip()+"\n");
        fwNames.write("#"+faultSection.getSectionName()+"\n");
        FaultTrace faultTrace = faultSection.getFaultTrace();
        int numFaultTraceLocations = faultTrace.getNumLocations();
        double upperSeisDepth = faultSection.getAveUpperSeisDepth();
        for(int j=0; j<numFaultTraceLocations; ++j) {
          Location loc = faultTrace.get(j);
          fwTrace.write(loc.getLongitude()+"\t"+loc.getLatitude()+"\t"+upperSeisDepth+"\n");
        }
       // fwDip.write(faultSection.getSectionName()+","+faultSection.getAveDip()+"\n");
/*
        fw.write("Section Name=" + faultSection.getSectionName() + "\n");
        fw.write("\tFaultId=" + faultSection.getFaultId() +
                 ",SectionId=" + faultSection.getSectionId() +
                 ",NSHM02ID=" + faultSection.getNshm02Id() +
                 ", faultModel=" + faultSection.getFaultModel() + "\n");
        fw.write("\tDip=" + faultSection.getAveDip() +
                 ",Avg LT Slip Rate=" + faultSection.getAveLongTermSlipRate() +
                 ", Avg Upper Seis Depth=" + faultSection.getAveUpperSeisDepth() +
                 ", Avg Lower Seis Depth=" + faultSection.getAveLowerSeisDepth() +
                 "\n");
        fw.write("\tComments=" + faultSection.getComments() + ",entryDate=" +
                 faultSection.getEntryDate() + "\n");
        fw.write("\tFault Trace=" + faultSection.getFaultTrace().toString() +
                 "\n\n\n");*/
      }
      fwTrace.close();
      fwNames.close();
     // fwDip.close();
    }catch(Exception e) {
      e.printStackTrace();
    }
  }
  public static void main(String[] args) {
   // SessionInfo.setUserName("vipin");
   // SessionInfo.setPassword("vip");
   // SessionInfo.setContributorInfo();
    Read2002FaultSections read2002FaultSections1 = new Read2002FaultSections();
  }

}
