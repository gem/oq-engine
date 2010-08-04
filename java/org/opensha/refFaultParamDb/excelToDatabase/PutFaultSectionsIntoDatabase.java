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

import java.io.FileInputStream;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.StringTokenizer;

import org.apache.poi.hssf.usermodel.HSSFCell;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.poifs.filesystem.POIFSFileSystem;
import org.opensha.commons.data.estimate.DiscreteValueEstimate;
import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.data.estimate.MinMaxPrefEstimate;
import org.opensha.commons.data.estimate.NormalEstimate;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.util.FileUtils;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.FaultSectionData;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 * <p>Title: PutFaultSectionsIntoDatabase.java </p>
 * <p>Description: this class reads the 2006_fault_sections.MID and
 * 2006_fault_sections.MIF files. These files contain fault section information
 * and provided by Chris Wills.
 *  It puts the information into database.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PutFaultSectionsIntoDatabase {
  // input files
  private final static String INPUT_FILE1 = "2006_fault_sections.MID";
  private final static String INPUT_FILE2 = "2006_fault_sections.MIF";
  private final static String NAME_CHANGE_FILE_NAME = "FaultSectionNameChanges.v1.xls";
  // units for various paramaters
  private final static String DIP_UNITS = "degrees";
  private final static String SLIP_RATE_UNITS = "mm/yr";
  private final static String DEPTH_UNITS = "km";
  private final static String RAKE_UNITS = "degrees";
  private final static String ASEISMIC_SLIP_FACTOR_UNITS = " ";

  // Strings that mark the start and end of each fault trace in the file
  private final static String PLINE = "Pline";
  private final static String  PEN = "Pen";

  // fault section trace file
  private ArrayList faultSectionTraceLines;
  private int nextTraceStartIndex=0;

  // DAO to put fault sections to database
  private FaultSectionVer2_DB_DAO faultSectionDAO = new FaultSectionVer2_DB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
  
  private final static int MIN_ROW_NAME_CHANGES = 1; // skip first row as it is header
  private final static int MAX_ROW_NAME_CHANGES = 256;  

  // filename to compare the dips
 // private final static String DIP_FILENAME = "DipComparisons.txt";
  //private FileWriter fwDip;
  private final static String SECTION_TRACE_FILE_NAME = "WGCEP_FaultSectionsTrace.txt";
  
  private String dipDirectionFromFile;

  /**
   * Put fault sections into the database
   */
  public PutFaultSectionsIntoDatabase() {
    try {
      ArrayList fileLines1 = FileUtils.loadFile(INPUT_FILE1);
      ArrayList faultSectionsList = new ArrayList();
      // load fault trace
      faultSectionTraceLines = FileUtils.loadFile(INPUT_FILE2);

      HashMap nameChangeMap = loadNameChangeFile(NAME_CHANGE_FILE_NAME);
      //fwDip = new FileWriter(PutFaultSectionsIntoDatabase.DIP_FILENAME);
      // load all the fault sections and their properties (except Fault Trace)
      FileWriter fwSectionTrace = new FileWriter(SECTION_TRACE_FILE_NAME);
      for(int i=0; i<fileLines1.size(); ++i) {
        try {
          FaultTrace faultSectionTrace = getNextTrace("temp");
          FaultSectionData faultSection = getFaultSection( (String) fileLines1.get(i));
          faultSectionTrace.setName(faultSection.getSectionName());
          faultSectionsList.add(faultSection);
          faultSection.setFaultTrace(faultSectionTrace);
          calculateDipDirection(faultSection);
          //fwSectionTrace.write((i+1)+","+faultSection.getSectionName()+"\n");
          /*fwSectionTrace.write((i+1)+",");
          int numLocs = faultSectionTrace.getNumLocations();
          for(int j=0; j<numLocs; ++j) {
        	  fwSectionTrace.write(faultSectionTrace.getLocationAt(j)+",");
          }
          fwSectionTrace.write("\n");*/
          //fwDip.write(dipDirection+"\n");
          // add fault section to the database
          String newName = (String)nameChangeMap.get(""+(i+1));
          if(newName!=null) faultSection.setSectionName(newName);
          faultSectionDAO.addFaultSection(faultSection);
          //System.out.println(faultSection.getSectionName());
        }catch(Exception e) {
          e.printStackTrace();
          System.exit(0);
          //System.out.println("Problem "+ e.getMessage());
        }
      }
      //fwDip.close();
      fwSectionTrace.close();
      fileLines1 = null;
      faultSectionTraceLines = null;
    }catch(Exception e) {
      e.printStackTrace();
    }
  }
  
  /**
   * Calculate dip direction from OpenSHA and compare it with dip direction from Chris's file.
   * 
   * @param faultSection
   */
  private void calculateDipDirection(FaultSectionData faultSection) {
	  double dip = ((MinMaxPrefEstimate)faultSection.getAveDipEst().getEstimate()).getPreferred();
	  // there is no dip direction if dip is 90 degrees
	  if(dip==90) {
		  faultSection.setDipDirection(Float.NaN);
		  return;
	  }
	  // calculate dip direction from OpenSHA
	  FaultTrace faultSectionTrace = faultSection.getFaultTrace();
	  double dipDirectionFromOpenSHA = 90+LocationUtils.vector(faultSectionTrace.get(0),
              faultSectionTrace.get(faultSectionTrace.getNumLocations()-1)).getAzimuth();
	  if(dipDirectionFromOpenSHA<0) dipDirectionFromOpenSHA+=360;
	  else if(dipDirectionFromOpenSHA>360) dipDirectionFromOpenSHA-=360;
	  faultSection.setDipDirection((float)dipDirectionFromOpenSHA);
	  
	  //calculate numerical dip direction based on String values from Chris Will's file
	  if(this.dipDirectionFromFile.equalsIgnoreCase("") || dipDirectionFromFile.equalsIgnoreCase("n/a")) {
		  System.out.println("Dip direction not available for section:"+faultSection.getSectionName()+" with dip "+dip);
		  return;
	  }
	  
	  double dipDirFromString=0; 
	  if(dipDirectionFromFile.equalsIgnoreCase("N")) dipDirFromString=0;
	  else if(dipDirectionFromFile.equalsIgnoreCase("NE")) dipDirFromString=45;
	  else if(dipDirectionFromFile.equalsIgnoreCase("E")) dipDirFromString=90;
	  else if(dipDirectionFromFile.equalsIgnoreCase("SE")) dipDirFromString=135;
	  else if(dipDirectionFromFile.equalsIgnoreCase("S")) dipDirFromString=180;
	  else if(dipDirectionFromFile.equalsIgnoreCase("SW")) dipDirFromString=225;
	  else if(dipDirectionFromFile.equalsIgnoreCase("W")) dipDirFromString=270;
	  else if(dipDirectionFromFile.equalsIgnoreCase("NW")) dipDirFromString=315;
	  
	  double dipDirectionDiff = Math.abs(dipDirectionFromOpenSHA-dipDirFromString);
	  // reverse the location points
	  if(dipDirectionDiff>=135 && dipDirectionDiff<=225) {
		  faultSectionTrace.reverse();
		  //System.out.println("Locations reversed for section:"+faultSection.getSectionName()+" with dip "+dip);
	  }
	  else if((dipDirectionDiff>45 && dipDirectionDiff<135) || (dipDirectionDiff>225 && dipDirectionDiff<315)) {
		  System.out.println("Please check the section:"+faultSection.getSectionName()+" as difference in dip direction is "+dipDirectionDiff);
	  }
	  
  }

  /**
   * Get next fault trace from the file
   * @param fileLines ArrayList
   * @param startIndex int
   * @return FaultTrace
   */
  private FaultTrace getNextTrace(String faultSectionName) {
    boolean found = false;
    double lat=0, lon;
    FaultTrace sectionTrace = new FaultTrace(faultSectionName);
    for(; !found ;++nextTraceStartIndex) {
      String line = ((String)faultSectionTraceLines.get(nextTraceStartIndex)).trim();
      if(line.startsWith(PLINE)) {
        found = true;
        String locString = ((String)faultSectionTraceLines.get(++nextTraceStartIndex)).trim();
        while(!locString.startsWith(PEN)) {
          StringTokenizer tokenizer = new StringTokenizer(locString);
          lon = Double.parseDouble(tokenizer.nextToken());
          lat = Double.parseDouble(tokenizer.nextToken());
          sectionTrace.add(new Location(lat,lon));
          locString = ((String)faultSectionTraceLines.get(++nextTraceStartIndex)).trim();
        }
      }
    }
    return sectionTrace;
  }

   private HashMap loadNameChangeFile(String fileName) {
	   HashMap nameChangesMap = new HashMap();
	   try {
		   POIFSFileSystem fs = new POIFSFileSystem(new FileInputStream(fileName));
		   HSSFWorkbook wb = new HSSFWorkbook(fs);
		   HSSFSheet sheet = wb.getSheetAt(0);
		   
		   // read data for each row
		   for(int r = MIN_ROW_NAME_CHANGES; r<=MAX_ROW_NAME_CHANGES; ++r) {
			   //System.out.println("Processing Row:"+(r+1));
			   HSSFRow row = sheet.getRow(r);
			   HSSFCell cell1 = row.getCell( (short) 0);
			   HSSFCell cell2 = row.getCell( (short) 2);
			   if(cell2!=null && !(cell2.getCellType()==HSSFCell.CELL_TYPE_BLANK)) {
				   nameChangesMap.put(cell1.getStringCellValue().trim(),
						   cell2.getStringCellValue().trim());
			   }
		   }
	   }catch(Exception e) {
		   e.printStackTrace();
	   }
	   return nameChangesMap;
   }

  /**
   * Get fault section from a file line
   *
   * @param line
   * @return
   */
  private FaultSectionData getFaultSection(String line) {
    FaultSectionData faultSection = new FaultSectionData();
    String comments = "";
    int index = line.indexOf("\",\"");
    // fault section name
    faultSection.setSectionName(line.substring(1, index));
    
    System.out.println(faultSection.getSectionName());
    String line2 = line.substring(index+2);
    index = line2.indexOf("\",\"");
    
    //System.out.println(line2);
    //System.out.println(index);

    //used only when 2 incompatible models exist, lists which model includes this fault
    String qFaultId = removeQuotes(line2.substring(0, index+1));
    if(!qFaultId.equalsIgnoreCase("")) faultSection.setQFaultId(qFaultId);
    
    line2 = line2.substring(index+2);
    index = line2.indexOf("\",\"");
    String model = removeQuotes(line2.substring(0, index+1));
    //System.out.println(model);
    //System.exit(0);
    if(!model.equalsIgnoreCase("")) {
      comments = comments + "Model="+model+"\n";
    }
    
    StringTokenizer tokenizer = new StringTokenizer(line2.substring(index+2),",");
    //2002 or CFM
    faultSection.setSource(removeQuotes(tokenizer.nextToken().trim()));
    //from 2002 model, text representation of rake, blank if not available
    String faultType = removeQuotes(tokenizer.nextToken().trim());
    if(!faultType.equalsIgnoreCase("")) {
      comments = comments+"FaultType="+faultType+"\n";
    }
    //converted from sense of movement field in 2002 model using Aki and Richards convention, blank if not available
    String rake = removeQuotes(tokenizer.nextToken().trim());
    // set rake to default if it is not present
    if(!rake.equalsIgnoreCase("")) {
    	faultSection.setAveRakeEst(this.getMinMaxPrefEstimateInstance(
    	          removeQuotes(rake), PutFaultSectionsIntoDatabase.RAKE_UNITS));
    }

    //from CFM when available, 2002 if not, average of dips of "panels" in CFM-R
    String dip = removeQuotes(tokenizer.nextToken().trim());
    faultSection.setAveDipEst(this.getMinMaxPrefEstimateInstance(dip, PutFaultSectionsIntoDatabase.DIP_UNITS));

    // from CFM when available, 2002 if not
    dipDirectionFromFile = removeQuotes(tokenizer.nextToken().trim());
   
    //from 2002 model, blank if not available
    String slipRate = removeQuotes(tokenizer.nextToken().trim());
    //from 2002 model, blank if not available
    String slipRateUncert = removeQuotes(tokenizer.nextToken().trim());
    if(!slipRate.equalsIgnoreCase("")) {	
    	Estimate slipRateEst = new NormalEstimate(Double.parseDouble(slipRate),
    			Double.parseDouble(slipRateUncert));
    	faultSection.setAveLongTermSlipRateEst(new EstimateInstances(slipRateEst, PutFaultSectionsIntoDatabase.SLIP_RATE_UNITS));
    }
    
    // from 2002 model
    String rank = removeQuotes(tokenizer.nextToken().trim());
    if( !rank.equalsIgnoreCase("")) {
      comments=comments+"Rank="+rank+"\n";
    }
    //from CFM when available, 2002 if not
    String upperDepth = removeQuotes(tokenizer.nextToken().trim());
    faultSection.setAveUpperDepthEst(getMinMaxPrefEstimateInstance(upperDepth, PutFaultSectionsIntoDatabase.DEPTH_UNITS));

    //from CFM when available, 2002 if not
    String lowerDepth = removeQuotes(tokenizer.nextToken().trim());
    faultSection.setAveLowerDepthEst(getMinMaxPrefEstimateInstance(lowerDepth, PutFaultSectionsIntoDatabase.DEPTH_UNITS));

    // calculated from dip and top and bottom depths
    String width = removeQuotes(tokenizer.nextToken().trim());
    if( !width.equalsIgnoreCase("")) {
      comments=comments+"Width="+width+"\n";
    }
    //from 2002 model
    String fileName = removeQuotes(tokenizer.nextToken().trim());
    if(!fileName.equalsIgnoreCase("")) {
      comments=comments+"FileName="+fileName+"\n";
    }

    // Aseimsic Slip Factor
    double rfactor1=0,rfactor1Wt=0, rfactor2=0, rfactor2Wt=0, rfactor3=0, rfactor3Wt=0;
    String str=null;
    //from Working Group 2003 report, 0 if not available
    str = tokenizer.nextToken().trim();
    if(str.equalsIgnoreCase("")) str="0";
    rfactor1 = Double.parseDouble(str);
    //from Working Group 2003 report, 0 if not available
    str = tokenizer.nextToken().trim();
    if(str.equalsIgnoreCase("")) str="0";
    rfactor1Wt = Double.parseDouble(str);
    //from Working Group 2003 report, 1 if not available
    str = tokenizer.nextToken().trim();
    if(str.equalsIgnoreCase("")) str="1";
    rfactor2 = Double.parseDouble(str);
    //from Working Group 2003 report, 1 if not available
    str = tokenizer.nextToken().trim();
    if(str.equalsIgnoreCase("")) str="1";
    rfactor2Wt = Double.parseDouble(str);
    //from Working Group 2003 report, 0 if not available
    str = tokenizer.nextToken().trim();
    if(str.equalsIgnoreCase("")) str="0";
    rfactor3 = Double.parseDouble(str);
    //from Working Group 2003 report, 0 if not available
    str = tokenizer.nextToken().trim();
    if(str.equalsIgnoreCase("")) str="0";
    rfactor3Wt = Double.parseDouble(str);

    faultSection.setAseismicSlipFactorEst(getAsesmicEstimate(rfactor1, rfactor1Wt,
        rfactor2, rfactor2Wt, rfactor3, rfactor3Wt, PutFaultSectionsIntoDatabase.ASEISMIC_SLIP_FACTOR_UNITS));
    return faultSection;
  }

  /**
   * Removes the double quotes from the string ends
   * @param str
   * @return
   */
  private String removeQuotes(String str) {
    if(str.charAt(0)=='"') return str.substring(1, str.length()-1);
    else return str;
  }

  /**
   * Get aseismic slip estimate
   * @param rfactor1
   * @param rfactor1Wt
   * @param rfactor2
   * @param rfactor2Wt
   * @param rfactor3
   * @param rfactor3Wt
   * @param units
   * @return
   */
  private EstimateInstances getAsesmicEstimate(double rfactor1, double rfactor1Wt,
                                      double rfactor2, double rfactor2Wt, double rfactor3, double rfactor3Wt,
                                      String units) {
    ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
    func.set(1-rfactor1, rfactor1Wt);
    func.set(1-rfactor2, rfactor2Wt);
    func.set(1-rfactor3, rfactor3Wt);
    DiscreteValueEstimate estimate = new DiscreteValueEstimate(func, false);
    return new EstimateInstances(estimate, units);
  }


  /**
   * Make Min-Max-Pref estimate from a single value.
   * That single value can be the Pref Estimate
   *
   * @param value
   * @return
   */
  private EstimateInstances getMinMaxPrefEstimateInstance(String value, String units) {
    Estimate estimate =  new MinMaxPrefEstimate(Double.NaN, Double.NaN,
                                                Double.parseDouble(value),
                                                Double.NaN, Double.NaN, Double.NaN);
    return new EstimateInstances(estimate, units);
  }

  
  public static void main(String[] args) {
     new PutFaultSectionsIntoDatabase();
  }


}
