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

import java.io.FileOutputStream;
import java.text.DecimalFormat;
import java.util.ArrayList;

import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.opensha.commons.data.estimate.MinMaxPrefEstimate;
import org.opensha.refFaultParamDb.dao.db.CombinedEventsInfoDB_DAO;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.PaleoSiteDB_DAO;
import org.opensha.refFaultParamDb.dao.db.PrefFaultSectionDataDB_DAO;
import org.opensha.refFaultParamDb.data.ExactTime;
import org.opensha.refFaultParamDb.data.TimeAPI;
import org.opensha.refFaultParamDb.data.TimeEstimate;
import org.opensha.refFaultParamDb.vo.CombinedDisplacementInfo;
import org.opensha.refFaultParamDb.vo.CombinedEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedNumEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedSlipRateInfo;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.PaleoSite;
import org.opensha.refFaultParamDb.vo.PaleoSitePublication;
import org.opensha.refFaultParamDb.vo.Reference;

/**
 * This class creates spreadsheet which will be given to deformation modelers
 * 
 * @author vipingupta
 *
 */
public class FileForDeformationModelers {
	private final static String OUT_FILE_NAME = "org/opensha/refFaultParamDb/excelToDatabase/FileForDeformationModelersv4.xls";
	// DAO to get information from the database
	private PaleoSiteDB_DAO paleoSiteDAO = new PaleoSiteDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
	private PrefFaultSectionDataDB_DAO prefFaultSectionDAO = new PrefFaultSectionDataDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
	private CombinedEventsInfoDB_DAO combinedEventsInfoDAO = new CombinedEventsInfoDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
	private final static String BETWEEN_LOCATIONS_SITE_TYPE = "Between Locations";
	private final static String KA = "KA";
	private final static String ALT = " alt ";
	private final static DecimalFormat LAT_FORMAT= new DecimalFormat("0.0000");
	private final static DecimalFormat LON_FORMAT = new DecimalFormat("0.000");
	private final static DecimalFormat KA_FORMAT = new DecimalFormat("0.####");
	private final static DecimalFormat SLIP_DISP_FORMAT = new DecimalFormat("0.##");
	
	//private final static String UNKNOWN = "Unknown";
	
	public static void main(String[] args) {
		FileForDeformationModelers dmFile = new FileForDeformationModelers();
		dmFile.generateFile();
	}
	
	public void generateFile() {
		// write to the  the excel file
		try {
			HSSFWorkbook wb  = new HSSFWorkbook();
			HSSFSheet sheet = wb.createSheet();
			writeHeader(sheet);
		
			// Get all paleo sites from the database
			ArrayList paleoSitesList = paleoSiteDAO.getAllPaleoSites();
			// loop over all the available sites
			int row = 1;
			for (int i = 0; i < paleoSitesList.size(); ++i) {
				PaleoSite paleoSite = (PaleoSite) paleoSitesList.get(i);
				System.out.println(i+". "+paleoSite.getSiteName());
				ArrayList paleoSitePublicationList = paleoSite.getPaleoSitePubList();
				// loop over all the reference publications for that site
				for (int j = 0; j < paleoSitePublicationList.size(); ++j) {
					PaleoSitePublication paleoSitePub = (PaleoSitePublication)
					paleoSitePublicationList.get(j);
					Reference reference = paleoSitePub.getReference();
					
					// get combined events info for that site and reference
					ArrayList combinedInfoList = combinedEventsInfoDAO.
					getCombinedEventsInfoList(paleoSite.getSiteId(),
							reference.getReferenceId());
					for (int k = 0; k < combinedInfoList.size(); ++k,++row) {
						CombinedEventsInfo combinedEventsInfo = (CombinedEventsInfo)
						combinedInfoList.get(k);
						// write a row of data into the spreadsheet
						writeRow( sheet,  row,  paleoSite,  combinedEventsInfo, paleoSitePub );
		  			}
				}
			}
			FileOutputStream fileOut = new FileOutputStream(OUT_FILE_NAME);
			wb.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}	
	}
	
	
	/**
	 * Write a row of information into spreadsheet
	 * 
	 * @param sheet
	 * @param rowId
	 * @param paleoSite
	 * @param combinedEventsInfo
	 * @param paleoSitePub
	 */
	private void writeRow(HSSFSheet sheet, int rowId, 
			PaleoSite paleoSite, CombinedEventsInfo combinedEventsInfo,
			PaleoSitePublication paleoSitePub ) {
		HSSFRow row = sheet.createRow((short)rowId);
		row.createCell((short)0).setCellValue(combinedEventsInfo.getEntryDate());
		row.createCell((short)1).setCellValue(getEntryType(combinedEventsInfo.getIsExpertOpinion()));
		row.createCell((short)2).setCellValue(combinedEventsInfo.getFaultSectionId());
		
		String faultSectionName = prefFaultSectionDAO.getFaultSectionPrefData(combinedEventsInfo.getFaultSectionId()).getSectionName();
		
		// WRITE CODE to specify whether ALTERNATES exist for fault Section
		String alternates = "N";
		if(faultSectionName.indexOf(ALT)>0) alternates="Y";
		row.createCell((short)3).setCellValue(alternates);
		
		row.createCell((short)4).setCellValue(faultSectionName);
		row.createCell((short)5).setCellValue(combinedEventsInfo.getNeokinemaFaultNumber());
		row.createCell((short)6).setCellValue(paleoSite.getSiteId());
		row.createCell((short)7).setCellValue(paleoSite.getSiteName());
		row.createCell((short)8).setCellValue(getSiteType(paleoSitePub.getSiteTypeNames()));
		
		// WRITE CODE TO SPECIFY THE DATA SOURCE
		String dataSource= "";
		if(combinedEventsInfo.getDataSource()!=null) dataSource = combinedEventsInfo.getDataSource();
		row.createCell((short)9).setCellValue(dataSource);
		
		row.createCell((short)10).setCellValue(LON_FORMAT.format(paleoSite.getSiteLon1()));
		row.createCell((short)11).setCellValue(LAT_FORMAT.format(paleoSite.getSiteLat1()));
		String siteElev="";
		if(!Float.isNaN(paleoSite.getSiteElevation1())) siteElev=""+paleoSite.getSiteElevation1();
		row.createCell((short)12).setCellValue(siteElev);
		
		String lon2="",lat2="",elev2="";
		if(paleoSitePub.getSiteTypeNames().contains(BETWEEN_LOCATIONS_SITE_TYPE))  {
			lon2 = LON_FORMAT.format(paleoSite.getSiteLon2());
			lat2 = LAT_FORMAT.format(paleoSite.getSiteLat2());
			if(!Float.isNaN(paleoSite.getSiteElevation2())) elev2=""+paleoSite.getSiteElevation2();
		}
		
		row.createCell((short)13).setCellValue(lon2);
		row.createCell((short)14).setCellValue(lat2);
		row.createCell((short)15).setCellValue(elev2);
		
		row.createCell((short)16).setCellValue(getStrandIndex(paleoSitePub.getRepresentativeStrandName()));
		
		row.createCell((short)17).setCellValue(paleoSitePub.getReference().getSummary());
		String qFaultRefId="";
		if(paleoSitePub.getReference().getQfaultReferenceId()>0)
			qFaultRefId = ""+paleoSitePub.getReference().getQfaultReferenceId();
		row.createCell((short)18).setCellValue(qFaultRefId);
		row.createCell((short)19).setCellValue(paleoSitePub.getReference().getReferenceId());
		
		// combined slip rate info
		CombinedSlipRateInfo combinedSlipRateInfo = combinedEventsInfo.getCombinedSlipRateInfo();
		// combined displacement info
		CombinedDisplacementInfo combinedDisplacementInfo = combinedEventsInfo.getCombinedDisplacementInfo();
		// num events info
		CombinedNumEventsInfo combinedNumEventsInfo = combinedEventsInfo.getCombinedNumEventsInfo();
	

		row.createCell((short)20).setCellValue(getMeasuredCompOfSlip(combinedSlipRateInfo, combinedDisplacementInfo));
		row.createCell((short)21).setCellValue(getSenseOfMotion(combinedSlipRateInfo, combinedDisplacementInfo));
		row.createCell((short)22).setCellValue(getRake(combinedSlipRateInfo, combinedDisplacementInfo));
		
		// start time 
		
		TimeAPI startTime = combinedEventsInfo.getStartTime();
		String startTimeUnits = getTimeUnits(startTime);
		row.createCell((short)23).setCellValue(startTimeUnits);
		row.createCell((short)24).setCellValue(getPrefTime(startTime,startTimeUnits));
		row.createCell((short)25).setCellValue(getMaxTime(startTime, startTimeUnits));
		row.createCell((short)26).setCellValue(getMinTime(startTime, startTimeUnits));
		
		// end time
		TimeAPI endTime = combinedEventsInfo.getEndTime();
		String endTimeUnits = getTimeUnits(endTime);
		row.createCell((short)27).setCellValue(endTimeUnits);
		row.createCell((short)28).setCellValue(getPrefTime(endTime,endTimeUnits));
		row.createCell((short)29).setCellValue(getMaxTime(endTime, endTimeUnits));
		row.createCell((short)30).setCellValue(getMinTime(endTime, endTimeUnits));
		
		//aseismic slip factor and Slip Rate
		String minAseismic="", prefAseismic="", maxAseismic="", minSlipRate="", maxSlipRate="", prefSlipRate="", slipRateComments="";
		if(combinedSlipRateInfo!=null) {
			minAseismic = getMin(combinedSlipRateInfo.getASeismicSlipFactorEstimateForSlip());
			prefAseismic = getPref(combinedSlipRateInfo.getASeismicSlipFactorEstimateForSlip());
			maxAseismic = getMax(combinedSlipRateInfo.getASeismicSlipFactorEstimateForSlip());
			minSlipRate = getMin(combinedSlipRateInfo.getSlipRateEstimate());
			prefSlipRate = getPref(combinedSlipRateInfo.getSlipRateEstimate());
			maxSlipRate = getMax(combinedSlipRateInfo.getSlipRateEstimate());
			if(combinedSlipRateInfo.getSlipRateComments()!=null)
				slipRateComments = combinedSlipRateInfo.getSlipRateComments();
		}
		row.createCell((short)31).setCellValue(prefAseismic);
		row.createCell((short)32).setCellValue(maxAseismic);
		row.createCell((short)33).setCellValue(minAseismic);
		row.createCell((short)34).setCellValue(prefSlipRate);
		row.createCell((short)35).setCellValue(maxSlipRate);
		row.createCell((short)36).setCellValue(minSlipRate);
		
		// displacement and asismic slip factor
		String minAseismicDisp="", prefAseismicDisp="", maxAseismicDisp="", minDisp="", maxDisp="", prefDisp="", displacementComments="";
		if(combinedDisplacementInfo!=null) {
			minAseismicDisp = getMin(combinedDisplacementInfo.getASeismicSlipFactorEstimateForDisp());
			prefAseismicDisp = getPref(combinedDisplacementInfo.getASeismicSlipFactorEstimateForDisp());
			maxAseismicDisp = getMax(combinedDisplacementInfo.getASeismicSlipFactorEstimateForDisp());
			minDisp = getMin(combinedDisplacementInfo.getDisplacementEstimate());
			prefDisp = getPref(combinedDisplacementInfo.getDisplacementEstimate());
			maxDisp = getMax(combinedDisplacementInfo.getDisplacementEstimate());
			if(combinedDisplacementInfo.getDisplacementComments()!=null)
				displacementComments = combinedDisplacementInfo.getDisplacementComments();
		}
		row.createCell((short)37).setCellValue(prefAseismicDisp);
		row.createCell((short)38).setCellValue(maxAseismicDisp);
		row.createCell((short)39).setCellValue(minAseismicDisp);
		row.createCell((short)40).setCellValue(prefDisp);
		row.createCell((short)41).setCellValue(maxDisp);
		row.createCell((short)42).setCellValue(minDisp);
		
		String minNumEvents="", maxNumEvents="", prefNumEvents="",numEventComments="";
		if(combinedNumEventsInfo!=null) {
			minNumEvents = getMin(combinedNumEventsInfo.getNumEventsEstimate());
			maxNumEvents = getMax(combinedNumEventsInfo.getNumEventsEstimate());
			prefNumEvents = getPref(combinedNumEventsInfo.getNumEventsEstimate());
			if(combinedNumEventsInfo.getNumEventsComments()!=null)
				numEventComments=combinedNumEventsInfo.getNumEventsComments();
		}
		row.createCell((short)43).setCellValue(prefNumEvents);
		row.createCell((short)44).setCellValue(maxNumEvents);
		row.createCell((short)45).setCellValue(minNumEvents);
		row.createCell((short)46).setCellValue(numEventComments);
		
		String datingComments="";
		if(startTime!=null && startTime.getDatingComments()!=null) datingComments = startTime.getDatingComments();
		row.createCell((short)47).setCellValue(datingComments);
		
		row.createCell((short)48).setCellValue(slipRateComments);
		row.createCell((short)49).setCellValue(displacementComments);
		String generalComments="";
		if(paleoSite.getGeneralComments()!=null) generalComments= paleoSite.getGeneralComments();
		row.createCell((short)50).setCellValue(generalComments);
	}
	
	
	private String getPrefTime(TimeAPI time, String timeUnits) {
		if(time==null) return "";
		if (time instanceof TimeEstimate) {
			TimeEstimate timeEstimate = (TimeEstimate)time;
			MinMaxPrefEstimate estimate =  (MinMaxPrefEstimate)timeEstimate.getEstimate();
			double val = estimate.getPreferred();
			if(Double.isNaN(val)) return "";
			if(timeUnits.equalsIgnoreCase(KA)) return KA_FORMAT.format(val);
			return ""+(int)val;
		} else {
			ExactTime exacTime = (ExactTime)time;
			return ""+exacTime.getYear();
		}
	}
	
	private String getMaxTime(TimeAPI time, String timeUnits) {
		if(time==null) return "";
		if (time instanceof TimeEstimate) {
			TimeEstimate timeEstimate = (TimeEstimate)time;
			MinMaxPrefEstimate estimate =  (MinMaxPrefEstimate)timeEstimate.getEstimate();
			double val=estimate.getMaximum();
			//if(timeUnits.equalsIgnoreCase(KA)) val = estimate.getMinimum();
			//else val = estimate.getMaximum();
			if(Double.isNaN(val)) return "";
			if(timeUnits.equalsIgnoreCase(KA)) return KA_FORMAT.format(val);
			return ""+(int)val;
		}
		return "";
	}
	
	/**
	 * 
	 * @param time
	 * @return
	 */
	private String getMinTime(TimeAPI time, String timeUnits) {
		if(time==null) return "";
		if (time instanceof TimeEstimate) {
			TimeEstimate timeEstimate = (TimeEstimate)time;
			MinMaxPrefEstimate estimate =  (MinMaxPrefEstimate)timeEstimate.getEstimate();
			double val=estimate.getMinimum();			
			//if(timeUnits.equalsIgnoreCase(KA)) val = estimate.getMaximum();
			//else val = estimate.getMinimum();
			if(Double.isNaN(val)) return "";
			if(timeUnits.equalsIgnoreCase(KA)) return KA_FORMAT.format(val);
			return ""+(int)val;
		}
		return "";
	}
	
	
	private String getTimeUnits(TimeAPI time) {
		if(time==null) return "";
		if (time instanceof TimeEstimate) {
			TimeEstimate timeEstimate = (TimeEstimate)time;
			if(timeEstimate.isKaSelected()) return KA;
			else return timeEstimate.getEra();
		} 
		return ((ExactTime)time).getEra();
	}
	
	
	/**
	 * Measured component of slip
	 * @param combinedSlipRateInfo
	 * @param combinedDisplacementInfo
	 * @return
	 */
	private String getMeasuredCompOfSlip(CombinedSlipRateInfo combinedSlipRateInfo,
			CombinedDisplacementInfo combinedDisplacementInfo) {
		String measuredCompSlip="";
		if(combinedSlipRateInfo!=null) 
			measuredCompSlip = getMeasuredCompOfSlipCode(combinedSlipRateInfo.getMeasuredComponentQual());
		if(combinedDisplacementInfo!=null && (measuredCompSlip==null || measuredCompSlip.equalsIgnoreCase("")) ) 
			measuredCompSlip = getMeasuredCompOfSlipCode(combinedDisplacementInfo.getMeasuredComponentQual());
		return measuredCompSlip;
	}	
	
	
    private String 	getMeasuredCompOfSlipCode(String measuredComp) {
    	if(measuredComp==null) return "";
    	if(measuredComp.equalsIgnoreCase("Total")) return "A";
    	if(measuredComp.equalsIgnoreCase("Vertical")) return "B";
    	if(measuredComp.equalsIgnoreCase("Horizontal,Trace-Parallel")) return "C";
    	if(measuredComp.equalsIgnoreCase("Horizontal,Trace-NORMAL")) return "D";
    	return null;
    }
    
    
    /**
	 * Sense of Motion
	 * @param combinedSlipRateInfo
	 * @param combinedDisplacementInfo
	 * @return
	 */
	private String getSenseOfMotion(CombinedSlipRateInfo combinedSlipRateInfo,
			CombinedDisplacementInfo combinedDisplacementInfo) {
		String senseOfMotion="";
		if(combinedSlipRateInfo!=null) 
			senseOfMotion = getSenseOfMotionCode(combinedSlipRateInfo.getSenseOfMotionQual());
		if(combinedDisplacementInfo!=null && senseOfMotion.equalsIgnoreCase("")) 
			senseOfMotion = getSenseOfMotionCode(combinedDisplacementInfo.getSenseOfMotionQual());
		return senseOfMotion;
	}	
	
	
    private String 	getSenseOfMotionCode(String senseOfMotion) {
    	if(senseOfMotion==null) return "";
    	else return senseOfMotion;
    }
    
    
    private String getRake(CombinedSlipRateInfo combinedSlipRateInfo,
			CombinedDisplacementInfo combinedDisplacementInfo) {
    	String rake="";
    	if(combinedSlipRateInfo!=null) rake = getSingleVal(combinedSlipRateInfo.getASeismicSlipFactorEstimateForSlip());
    	if(combinedDisplacementInfo!=null && rake.equalsIgnoreCase(""))
    		 rake = getSingleVal(combinedDisplacementInfo.getASeismicSlipFactorEstimateForDisp());
    	return rake;
    }
    
    	
   
    private String getSingleVal(EstimateInstances estimateInstance) {
    	String val = getPref(estimateInstance);
    	if(val.equalsIgnoreCase("")) val = getMax(estimateInstance);
    	if(val.equalsIgnoreCase("")) val = getMin(estimateInstance);
    	return val;
    }
    /**
     * Get Min value from Min/Max/Pref Estimate
     * @param estimateInstance
     * @return
     */
    private String getMin(EstimateInstances estimateInstance) {
    	if(estimateInstance==null) return "";
    	MinMaxPrefEstimate estimate =  (MinMaxPrefEstimate)estimateInstance.getEstimate();
    	if(Double.isNaN(estimate.getMinimum())) return "";
    	else return SLIP_DISP_FORMAT.format(estimate.getMinimum());
    }
    
    /**
     * Get Max value from Min/Max/Pref Estimate
     * @param estimateInstance
     * @return
     */
    private String getMax(EstimateInstances estimateInstance) {
    	if(estimateInstance==null) return "";
    	MinMaxPrefEstimate estimate =  (MinMaxPrefEstimate)estimateInstance.getEstimate();
    	if(Double.isNaN(estimate.getMaximum())) return "";
    	else return SLIP_DISP_FORMAT.format(estimate.getMaximum());
    }
    
    /**
     * Get Preferred value from Min/Max/Pref Estimate
     * @param estimateInstance
     * @return
     */
    private String getPref(EstimateInstances estimateInstance) {
    	if(estimateInstance==null) return "";
    	MinMaxPrefEstimate estimate =  (MinMaxPrefEstimate)estimateInstance.getEstimate();
    	if(Double.isNaN(estimate.getPreferred())) return "";
    	else return SLIP_DISP_FORMAT.format(estimate.getPreferred());
    }
    
	
	
	private String getStrandIndex(String repStrandIndex) {
		if(repStrandIndex.equalsIgnoreCase("Entire Fault")) return "1";
		else if(repStrandIndex.equalsIgnoreCase("Most Significant Strand")) return "2";
		else if(repStrandIndex.equalsIgnoreCase("One of Several Strands")) return "3";
		else  return "4"; // unknown
	}
	
	private String getSiteType(ArrayList siteTypeNames) {
		if(siteTypeNames.contains(BETWEEN_LOCATIONS_SITE_TYPE)) return "2";
		else return "1";
	}
	
	
	private String getEntryType(boolean isExpertOpinion) {
		if(isExpertOpinion) return "E";
		else return "R";
	}
	
	/**
	 * Write header for the excel sheet
	 *
	 */
	 private void writeHeader(HSSFSheet sheet) {
		 HSSFRow row = sheet.createRow((short)0);
		 int col=0;
		 row.createCell((short)col++).setCellValue("ENTRY DATE");
		 row.createCell((short)col++).setCellValue("ENTRY TYPE");
		 row.createCell((short)col++).setCellValue("WG_FAULT_ID");
		 row.createCell((short)col++).setCellValue("ALTERNATES?");
		 row.createCell((short)col++).setCellValue("FAULT_NAME");
		 row.createCell((short)col++).setCellValue("BIRD FAULT  ID-REFCAT");
		 row.createCell((short)col++).setCellValue("WG SITE ID");
		 row.createCell((short)col++).setCellValue("SITE NAME");
		 row.createCell((short)col++).setCellValue("SITE TYPE");
		 row.createCell((short)col++).setCellValue("DATA SOURCE");
		 row.createCell((short)col++).setCellValue("SITE_LONG 1");
		 row.createCell((short)col++).setCellValue("SITE_LAT 1");
		 row.createCell((short)col++).setCellValue("SITE_ELEV 1");
		 row.createCell((short)col++).setCellValue("SITE LONG 2");
		 row.createCell((short)col++).setCellValue("SITE LAT 2");
		 row.createCell((short)col++).setCellValue("SITE ELEV 2");
		 row.createCell((short)col++).setCellValue("HOW REPRESENTATIVE IS SITE?");
		 row.createCell((short)col++).setCellValue("SHORT CITATION");
		 row.createCell((short)col++).setCellValue("QFAULTS REF ID");
		 row.createCell((short)col++).setCellValue("WG REF ID");
		 row.createCell((short)col++).setCellValue("MEASURED COMPONENT OF SLIP");
		 row.createCell((short)col++).setCellValue("SENSE OF MOTION");
		 row.createCell((short)col++).setCellValue("RAKE");
		 row.createCell((short)col++).setCellValue("START TIME UNITS");
		 row.createCell((short)col++).setCellValue("PREF START TIME");
		 row.createCell((short)col++).setCellValue("MAX START TIME(earliest)");
		 row.createCell((short)col++).setCellValue("MIN START TIME");
		 row.createCell((short)col++).setCellValue("END TIME UNITS");
		 row.createCell((short)col++).setCellValue("PREF END TIME");
		 row.createCell((short)col++).setCellValue("MAX END TIME (earliest)");
		 row.createCell((short)col++).setCellValue("MIN END TIME");
		 row.createCell((short)col++).setCellValue("SR: Aseismic Slip Est PREF");
		 row.createCell((short)col++).setCellValue("SR: Aseismic Slip Est MAX");
		 row.createCell((short)col++).setCellValue("SR: Aseismic Slip Est MIN");
		 row.createCell((short)col++).setCellValue("PREF SLIP RATE (mm/yr)");
		 row.createCell((short)col++).setCellValue("MAX SLIP RATE");
		 row.createCell((short)col++).setCellValue("MIN SLIP RATE");
		 row.createCell((short)col++).setCellValue("Offset: Aseismic Slip Est PREF");
		 row.createCell((short)col++).setCellValue("Offset: Aseismic Slip Est MAX");
		 row.createCell((short)col++).setCellValue("Offset: Aseismic Slip Est MIN");
		 row.createCell((short)col++).setCellValue("PREF OFFSET (m)");
		 row.createCell((short)col++).setCellValue("MAX OFFSET");
		 row.createCell((short)col++).setCellValue("MIN OFFSET");
		 row.createCell((short)col++).setCellValue("PREF NUM EVENTS");
		 row.createCell((short)col++).setCellValue("MAX NUM EVENTS");
		 row.createCell((short)col++).setCellValue("MIN NUM EVENTS");
		 row.createCell((short)col++).setCellValue("NUM EVENTS COMMENTS");
		 row.createCell((short)col++).setCellValue("TIME AND DATING COMMENTS");
		 row.createCell((short)col++).setCellValue("SLIP RATE COMMENTS");
		 row.createCell((short)col++).setCellValue("OFFSET COMMENTS");
		 row.createCell((short)col++).setCellValue("GENERAL COMMENTS");
	 }
}
