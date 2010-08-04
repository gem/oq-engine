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
import java.util.ArrayList;
import java.util.HashMap;

import org.apache.poi.hssf.usermodel.HSSFCell;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.poifs.filesystem.POIFSFileSystem;
import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.data.estimate.MinMaxPrefEstimate;
import org.opensha.commons.geo.Location;
import org.opensha.refFaultParamDb.dao.db.CombinedEventsInfoDB_DAO;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.dao.db.PaleoSiteDB_DAO;
import org.opensha.refFaultParamDb.dao.db.ReferenceDB_DAO;
import org.opensha.refFaultParamDb.data.ExactTime;
import org.opensha.refFaultParamDb.data.TimeAPI;
import org.opensha.refFaultParamDb.data.TimeEstimate;
import org.opensha.refFaultParamDb.gui.addEdit.paleoSite.AddEditCumDisplacement;
import org.opensha.refFaultParamDb.gui.addEdit.paleoSite.AddEditSlipRate;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.vo.CombinedDisplacementInfo;
import org.opensha.refFaultParamDb.vo.CombinedEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedSlipRateInfo;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.FaultSectionData;
import org.opensha.refFaultParamDb.vo.FaultSectionSummary;
import org.opensha.refFaultParamDb.vo.PaleoSite;
import org.opensha.refFaultParamDb.vo.PaleoSitePublication;
import org.opensha.refFaultParamDb.vo.Reference;


/**
 * <p>Title: PutCombinedInfoIntoDatabase.java </p>
 * <p>Description: It reads the excel file and puts combined events into the
 * oracle database</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PutCombinedInfoIntoDatabase_FAD {
  private final static String FILE_NAME = "org/opensha/refFaultParamDb/excelToDatabase/FromFAD.v2.xls";
  // rows (number of records) in this excel file. First 2 rows are neglected as they have header info
  // rows containing the data related to a site for a particular timespan
  private final static int MIN_ROW_TIMESPAN = 2;
  private final static int MAX_ROW_TIMESPAN = 298;
  private final static int MIN_COL_TIMESPAN = 0;
  private final static int MAX_COL_TIMESPAN =17;
  // spread-sheet containing a list of references
  private final static int MIN_ROW_REF = 1;
  private final static int MAX_ROW_REF = 189;
  private final static int MIN_COL_REF = 1;
  private final static int MAX_COL_REF = 3;
  // spread sheet contaning site names and locations
  private final static int MIN_ROW_SITE_LOC= 2;
  private final static int MAX_ROW_SITE_LOC = 220;
  private final static int MIN_COL_SITE_LOC= 0;
  private final static int MAX_COL_SITE_LOC = 6;
  // columns in this excel file
  private PaleoSiteDB_DAO paleoSiteDAO = new PaleoSiteDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
  private ReferenceDB_DAO referenceDAO = new ReferenceDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
  private FaultSectionVer2_DB_DAO faultSectionDAO = new FaultSectionVer2_DB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
  private CombinedEventsInfoDB_DAO combinedEventsInfoDAO = new CombinedEventsInfoDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
  private final static String UNKNOWN = "Unknown";
  private final static String KA = "ka";
  private final static int ZERO_YEAR=1950;
  private String measuredComponent;
  private CombinedSlipRateInfo combinedSlipRateInfo;
  private CombinedDisplacementInfo combinedDispInfo;
  private boolean isSlipRate;
  private boolean isDisp;
  private double min, max, pref;
  private TimeAPI startTime, endTime;
  private String startTimeUnits, endTimeUnits;
  private final static String NO = "no";
  private HashMap fadReferences =  new HashMap();
  private HashMap fadSites = new HashMap();
  private int fadSiteId;
  private int fadReferenceId;
  private HashMap insertedFAD_SiteIntoDB = new HashMap();
  private final static String BETWEEN_LOCATIONS_SITE_TYPE = "Between Locations";
  private final static String DATA_SOURCE=" SCEC-FAD";
  
  public PutCombinedInfoIntoDatabase_FAD() {
    try {
    	this.loadFAD_References();
    	this.loadPaleoSites();
    	this.putCombinedEventsInfo();
    }catch(Exception e) {
    	e.printStackTrace();
    }
  }
  
  
  
  private void putCombinedEventsInfo() {
	  try {
//	 read the excel file
  	POIFSFileSystem fs = new POIFSFileSystem(new FileInputStream(FILE_NAME));
  	HSSFWorkbook wb = new HSSFWorkbook(fs);
  	HSSFSheet sheet = wb.getSheetAt(0);
	// site types
  	ArrayList siteTypeNames = new ArrayList();
	siteTypeNames.add(UNKNOWN);
  	// read data for each row
  	for(int r = MIN_ROW_TIMESPAN; r<=MAX_ROW_TIMESPAN; ++r) {	
  		HSSFRow row = sheet.getRow(r);
  		System.out.println("Combined Event Info, row="+(r+1));
  		// combined event info for this site
  		CombinedEventsInfo combinedEventsInfo = new CombinedEventsInfo();
  	
  		// make object of slip rate 
  		combinedSlipRateInfo = new CombinedSlipRateInfo();
  		combinedDispInfo = new CombinedDisplacementInfo();
  		isSlipRate=false;
  		isDisp = false;
  		// start time and end time
  		startTime = new TimeEstimate();
  		endTime = new TimeEstimate();
  		//    paleo site publication
		PaleoSitePublication paleoSitePub = new PaleoSitePublication();
		paleoSitePub.setRepresentativeStrandName(UNKNOWN);
		paleoSitePub.setSiteTypeNames(siteTypeNames);
		combinedEventsInfo.setPaleoSitePublication(paleoSitePub);
  		
  		try {
  			// get value of each column in the row
  			for (int c = MIN_COL_TIMESPAN; c <= MAX_COL_TIMESPAN; ++c) {
  				HSSFCell cell = row.getCell( (short) c);
  				String value = null;
  				if (cell != null &&
  						! (cell.getCellType() == HSSFCell.CELL_TYPE_BLANK)) {
  					if(cell.getCellType() == HSSFCell.CELL_TYPE_STRING)
  						value = cell.getStringCellValue().trim();
  					else value = ""+cell.getNumericCellValue();
  				}
  				process(c, value, combinedEventsInfo, paleoSitePub);
  			}
  		}catch(InvalidRowException e) {
  			System.out.println("Row "+(r+1)+":"+e.getMessage());
  			continue;
  		}catch(RuntimeException ex) {
  			ex.printStackTrace();
  			continue;
  		}
		// set the start and end time
		combinedEventsInfo.setStartTime(this.startTime);
		combinedEventsInfo.setEndTime(this.endTime);
		ArrayList refList = new ArrayList();
		refList.add(paleoSitePub.getReference());
		combinedEventsInfo.setReferenceList(refList);
		// set slip rate in combined events info
		if(isSlipRate) {
			combinedSlipRateInfo.setSenseOfMotionQual(null);
			combinedSlipRateInfo.setMeasuredComponentQual(this.measuredComponent);
			combinedEventsInfo.setCombinedSlipRateInfo(combinedSlipRateInfo);
		}
		if(isDisp) {
			this.combinedDispInfo.setSenseOfMotionQual(null);
			this.combinedDispInfo.setMeasuredComponentQual(this.measuredComponent);
			combinedEventsInfo.setCombinedDisplacementInfo(combinedDispInfo);
		}
		
      // site in DB
      PaleoSite siteInDB = getPaleoSite(paleoSitePub);
   
      paleoSitePub.setSiteEntryDate(siteInDB.getEntryDate());
      paleoSitePub.setSiteId(siteInDB.getSiteId());
      combinedEventsInfo.setIsExpertOpinion(false);
      combinedEventsInfo.setSiteId(siteInDB.getSiteId());
      combinedEventsInfo.setSiteEntryDate(siteInDB.getEntryDate());
      combinedEventsInfo.setDataSource(DATA_SOURCE);
      // add combined events info to database
       combinedEventsInfoDAO.addCombinedEventsInfo(combinedEventsInfo);
       Thread.sleep(500);
  		}
	  }catch(Exception e) {
  		e.printStackTrace();
  	}
    
  }
  
  private PaleoSite getPaleoSite(PaleoSitePublication paleoSitePub) throws Exception {
	  PaleoSite paleoSite = (PaleoSite)this.insertedFAD_SiteIntoDB.get(new Integer(this.fadSiteId));
	  PaleoSite fadPaleoSite = (PaleoSite)this.fadSites.get(new Integer(this.fadSiteId));
	  if(fadPaleoSite.getSiteName().equalsIgnoreCase("per"))
		  fadPaleoSite.setSiteName("Per "+paleoSitePub.getReference().getSummary());
	  if(paleoSite==null) {
		  // check whether a site exists in database with the same qfault Id
		  if(fadPaleoSite.getOldSiteId()==null || this.paleoSiteDAO.getPaleoSiteByQfaultId(fadPaleoSite.getOldSiteId())==null) {
			  //				 set publication in paleo site
				ArrayList pubList = new ArrayList();
				pubList.add(paleoSitePub);
				fadPaleoSite.setPaleoSitePubList(pubList);
				if(Float.isNaN(fadPaleoSite.getSiteLat1())) {
					FaultSectionSummary faultSectionSummary= faultSectionDAO.getFaultSectionSummary(fadPaleoSite.getFaultSectionId());
					fadPaleoSite.setFaultSectionNameId(faultSectionSummary.getSectionName(), faultSectionSummary.getSectionId());

					FaultSectionData faultSection = this.faultSectionDAO.getFaultSection(fadPaleoSite.getFaultSectionId());
					Location loc1 = faultSection.getFaultTrace().get(0);
					Location loc2 = faultSection.getFaultTrace().get(faultSection.getFaultTrace().getNumLocations()-1);
					fadPaleoSite.setSiteLat1((float)loc1.getLatitude());
					fadPaleoSite.setSiteLat2((float)loc2.getLatitude());
					fadPaleoSite.setSiteLon1((float)loc1.getLongitude());
					fadPaleoSite.setSiteLon2((float)loc2.getLongitude());
					fadPaleoSite.setGeneralComments(fadPaleoSite.getGeneralComments()+"\n"+
							"No site location available.   Site is associated with a WG fault section.");
					//System.out.println(fadPaleoSite.getSiteName()+";"+fadPaleoSite.getFaultSectionId()+";"+fadPaleoSite.getFaultSectionName());
					ArrayList siteTypeNames = paleoSitePub.getSiteTypeNames();
					siteTypeNames.clear();
					siteTypeNames.add(BETWEEN_LOCATIONS_SITE_TYPE);
					
					if(fadPaleoSite.getSiteName().equalsIgnoreCase("NaN,Nan"))
						fadPaleoSite.setSiteName( GUI_Utils.latFormat.format(fadPaleoSite.getSiteLat1())+","+GUI_Utils.lonFormat.format(fadPaleoSite.getSiteLon1())+";"+
								GUI_Utils.latFormat.format(fadPaleoSite.getSiteLat2())+","+GUI_Utils.lonFormat.format(fadPaleoSite.getSiteLon2()));
				}
				paleoSiteDAO.addPaleoSite(fadPaleoSite);
				Thread.sleep(1000);
				insertedFAD_SiteIntoDB.put(new Integer(this.fadSiteId), fadPaleoSite);
				paleoSite = fadPaleoSite;
		  } else paleoSite = paleoSiteDAO.getPaleoSiteByQfaultId(fadPaleoSite.getOldSiteId());
	  } 
	  return paleoSite;
  }
  
  
  /**
   * Load the fAD references and corresponding Ids  
   *
   */
  private void loadFAD_References() {
	  try {
		  // read the excel file
		  POIFSFileSystem fs = new POIFSFileSystem(new FileInputStream(FILE_NAME));
		  HSSFWorkbook wb = new HSSFWorkbook(fs);
		  HSSFSheet sheet = wb.getSheetAt(2);
		  // read data for each row
		  int fadRefId=-1;;
		  for(int r = MIN_ROW_REF; r<=MAX_ROW_REF; ++r) {
			  Reference reference=null;
			  HSSFRow row = sheet.getRow(r);
			  //System.out.println("Reference row="+(r+1));
			  for (int c = MIN_COL_REF; c <= MAX_COL_REF; ++c) {
		            HSSFCell cell = row.getCell( (short) c);
		            String value = null;
		            if (cell != null &&
		                ! (cell.getCellType() == HSSFCell.CELL_TYPE_BLANK)) {
		              if(cell.getCellType() == HSSFCell.CELL_TYPE_STRING)
		                value = cell.getStringCellValue().trim();
		              else value = ""+cell.getNumericCellValue();
		            }
		            // set the Ref Id, short citation and biblio grpahic reference
		            if(c==1) fadRefId =Integer.parseInt(value);
		            else if(c==2) {
		            	reference = getReference(value);
		            } else if(c==3) {
		            	reference.setFullBiblioReference(value);
		            }
		          }
			  this.fadReferences.put(new Integer(fadRefId), reference);
		  }
	  }catch(Exception e) {
		  e.printStackTrace();
	  }
  }
  
  
  /**
   * Make Paleo Site objects and save in hashmap
   *
   */
  private void loadPaleoSites() {
	  try {
		  // read the excel file
		  POIFSFileSystem fs = new POIFSFileSystem(new FileInputStream(FILE_NAME));
		  HSSFWorkbook wb = new HSSFWorkbook(fs);
		  HSSFSheet sheet = wb.getSheetAt(3);
		  int fadSiteId = -1;
		  for(int r = MIN_ROW_SITE_LOC; r<=MAX_ROW_SITE_LOC; ++r) {
			  HSSFRow row = sheet.getRow(r);
			  //System.out.println("Paleo Site row="+(r+1));
			  PaleoSite paleoSite = new PaleoSite();
			  for (int c = MIN_COL_SITE_LOC; c <= MAX_COL_SITE_LOC; ++c) {
		            HSSFCell cell = row.getCell( (short) c);
		            String value = null;
		            if (cell != null &&
		                ! (cell.getCellType() == HSSFCell.CELL_TYPE_BLANK)) {
		              if(cell.getCellType() == HSSFCell.CELL_TYPE_STRING)
		                value = cell.getStringCellValue().trim();
		              else value = ""+cell.getNumericCellValue();
		            }
		            if(c==0) fadSiteId = Integer.parseInt(value); // FAD site Id
		            else if(c==1 && value!=null && !value.equalsIgnoreCase("NULL")) paleoSite.setOldSiteId(value); // qfault Id
		            else if(c==2 && value!=null && !value.equalsIgnoreCase("NULL")) { // site lat
		            	paleoSite.setSiteLat1(Float.parseFloat(value));
		            	paleoSite.setSiteLat2(Float.NaN);
		            } else if(c==3 && value!=null && !value.equalsIgnoreCase("NULL")) { // site lon
		            	paleoSite.setSiteLon1(Float.parseFloat(value));
		            	paleoSite.setSiteLon2(Float.NaN);
		            } else if(c==4 && value!=null && !value.equalsIgnoreCase("NULL")) { // site elevation
		            	paleoSite.setSiteElevation1(Float.parseFloat(value));
		            	paleoSite.setSiteElevation2(Float.NaN);
		            } else if(c==5 && value!=null && !value.equalsIgnoreCase("NULL")) { // site name
		            	paleoSite.setSiteName(value);
		            } else if(c==6 && value!=null && !value.equalsIgnoreCase("NULL")) { // site comments
		            	paleoSite.setGeneralComments(value);
		            }
		          }
			  if(paleoSite.getSiteName()==null || paleoSite.getSiteName().equalsIgnoreCase("")) {
				    
	    	          paleoSite.setSiteName("per");
			  } 
			  if(paleoSite.getGeneralComments()==null) paleoSite.setGeneralComments("");
			  this.fadSites.put(new Integer(fadSiteId), paleoSite);
		  }
	  }catch(Exception e) {
		  e.printStackTrace();
	  }
  }
  
 

  /**
   * Process the excel sheet according to the specific column number
   *
   * @param columnNumber
   * @param value
   * @param paleoSite
   * @param combinedEventsInfo
   */
  private void process(int columnNumber, String value,
                       CombinedEventsInfo combinedEventsInfo,
                       PaleoSitePublication paleoSitePub) {
    switch (columnNumber) {
      case 0:
    	  if(value!=null && value.equalsIgnoreCase(NO)) throw new InvalidRowException("No need to put into database as ingest=no");
    	  break;
      case 1: //FSR
        break;
      case 2: //  FAD reference Id
    	  this.fadReferenceId = Integer.parseInt(value);
    	  Reference reference = (Reference)this.fadReferences.get(new Integer(fadReferenceId));
    	  Reference refFromDB = this.referenceDAO.getReference(reference.getRefAuth(), reference.getRefYear());
    	  if(refFromDB==null) {
    		  int refId = referenceDAO.addReference(reference);
    		  refFromDB = reference;
    		  refFromDB.setReferenceId(refId);
    	  }
    	  paleoSitePub.setReference(refFromDB);
    	  break;
      case 3: // FAD site Id
    	  this.fadSiteId = Integer.parseInt(value);
        break;
      case 4: // FAD fault Id
    	  break;
      case 5: // WG Fault section Id
    	  PaleoSite paleoSite = (PaleoSite)this.fadSites.get(new Integer(fadSiteId));
    	  paleoSite.setFaultSectionNameId("temp", (int)Double.parseDouble(value.trim()));
    	  break;
      case 6: // compiler
    	  String compilerComment = "Compiler="+value;
    	  combinedSlipRateInfo.setSlipRateComments(compilerComment);
    	  PaleoSite paleoSite1 = (PaleoSite)this.fadSites.get(new Integer(fadSiteId));
    	  paleoSite1.setGeneralComments(paleoSite1.getGeneralComments()+"\n"+compilerComment);
    	  break;
      case 7: // component of Slip
    	  if(value==null)  measuredComponent = UNKNOWN;
    	  else {
    		  if(value.equalsIgnoreCase("A")) measuredComponent="Total";
    		  else if(value.equalsIgnoreCase("B")) measuredComponent="Vertical";
    		  else if(value.equalsIgnoreCase("C")) measuredComponent="Horizontal,Trace-Parallel";
    		  else if(value.equalsIgnoreCase("D")) measuredComponent="Horizontal,Trace-NORMAL";
    	  }
    	  break;
      case 8: // end time Min
    	  if(value==null) this.min = Double.NaN;
          else min = Double.parseDouble(value);
    	  break;
      case 9: // start time pref
    	  if(value==null) this.pref = Double.NaN;
    	  else pref = Double.parseDouble(value);
    	  break;
      case 10:  // start time max
    	  if(value==null) this.max = Double.NaN;
    	  else max = Double.parseDouble(value);
    	  break;
      case 11: // start time units
    	  if(value==null) this.startTimeUnits = KA;
    	  else this.startTimeUnits =value;

          // set the start time
    	  if(Double.isNaN(max) && Double.isNaN(pref)) {
              //throw new InvalidRowException("Start Time is missing");
              startTime = null;
              endTime = null;
          	  break;
    	  }
          Estimate est = new MinMaxPrefEstimate(Double.NaN,max,pref,Double.NaN, Double.NaN, Double.NaN);
          if(startTimeUnits.equalsIgnoreCase(KA))
            ((TimeEstimate)startTime).setForKaUnits(est, ZERO_YEAR);
          else ((TimeEstimate)startTime).setForCalendarYear(est, startTimeUnits);
          // set reference in start time
          ArrayList refList = new ArrayList();
          refList.add(paleoSitePub.getReference());
          startTime.setReferencesList(refList);
          
          // set the end time
          endTimeUnits=this.startTimeUnits;
          
          if(Double.isNaN(min)) {
        	 int refYear;
        	 if(paleoSitePub.getReference().getRefYear().equalsIgnoreCase("2002a"))  refYear = 2002;
        	 else refYear = Integer.parseInt(paleoSitePub.getReference().getRefYear());
            endTime = new ExactTime(refYear, 0, 0, 0, 0, 0, TimeAPI.AD, true);
          } else {
            // set the end time
            Estimate endTimeEst = new MinMaxPrefEstimate(min,Double.NaN,Double.NaN,Double.NaN, Double.NaN, Double.NaN);
            if(endTimeUnits.equalsIgnoreCase(KA))
              ((TimeEstimate)endTime).setForKaUnits(endTimeEst, ZERO_YEAR);
            else ((TimeEstimate)endTime).setForCalendarYear(endTimeEst, endTimeUnits);
          }
          endTime.setReferencesList(refList);
    	  break;
      case 12: // dated feature comments
        if(value==null) value="";
        combinedEventsInfo.setDatedFeatureComments(value);
        break;
      case 13: // preferred displacement
    	  if(value!=null) {
    		  this.isDisp = true;
    		  double prefDisp  = Double.parseDouble(value)*1000; //convert into meters 
    		  Estimate displacementEst = new MinMaxPrefEstimate(Double.NaN,Double.NaN,prefDisp,Double.NaN, Double.NaN, Double.NaN);
    		  this.combinedDispInfo.setDisplacementEstimate(new EstimateInstances(displacementEst, AddEditCumDisplacement.CUMULATIVE_DISPLACEMENT_UNITS));
    	  }
    	  break;
      case 14: // min slip rate
        if(value==null) this.min = Double.NaN;
        else {
          this.isSlipRate = true;
          this.min = Double.parseDouble(value);
        }
        break;
      case 15: // max slip rate
          if(value==null) this.max = Double.NaN;
          else {
            this.isSlipRate = true;
            this.max = Double.parseDouble(value);
          }
          break;
      case 16: // pref slip rate
        if(value==null) this.pref = Double.NaN;
        else {
          this.isSlipRate = true;
          this.pref = Double.parseDouble(value);
        }
        if(isSlipRate) {
            Estimate estimate = new MinMaxPrefEstimate(min,max,pref,Double.NaN, Double.NaN, Double.NaN);
            this.combinedSlipRateInfo.setSlipRateEstimate(new EstimateInstances(estimate, AddEditSlipRate.SLIP_RATE_UNITS));
          }
        break;
      
      case 17: // slip rate comments
        if(value==null) value="";
        this.combinedSlipRateInfo.setSlipRateComments(value);
        this.combinedDispInfo.setDisplacementComments(value);
        break;
    }
  }


private Reference getReference(String referenceSummary) {
	Reference ref = new Reference();
    ref.setFullBiblioReference("");
    int index = referenceSummary.indexOf("(");
    ref.setRefAuth(referenceSummary.substring(0,index));
    ref.setRefYear(referenceSummary.substring(index+1,referenceSummary.indexOf(")")));
	return ref;
}
}
