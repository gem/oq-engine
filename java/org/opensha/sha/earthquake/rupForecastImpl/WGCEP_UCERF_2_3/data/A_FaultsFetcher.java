/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;

import org.apache.poi.hssf.usermodel.HSSFCell;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.poifs.filesystem.POIFSFileSystem;
import org.opensha.commons.data.ValueWeight;
import org.opensha.commons.geo.Location;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.PrefFaultSectionDataDB_DAO;
import org.opensha.refFaultParamDb.vo.DeformationModelSummary;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.refFaultParamDb.vo.FaultSectionSummary;

/**
 *
 * This class read the A-Faults segments from a text file. Then it fetches the fault sections from the database
 * It also reads the table 7 (site name, event rate. sigma and 95% confidence bounds) in Appendix C of UCERF2 report 
 * Additionally. it reads Time Dependent data (last event, slip, aperiodicity) for each segment from an excel sheet.
 * 
 * @author vipingupta
 *
 */
public class A_FaultsFetcher extends FaultsFetcher implements java.io.Serializable {
	private final static String RUP_RATE_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/A_Faults_aPrioriRates.xls";
	private final static String SEG_RATE_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/Appendix_C_Table7_091807.xls";
	private final static String SEG_TIME_DEP_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/SegmentTimeDepData_v06.xls";
	private HashMap<String,A_PrioriRupRates> aPrioriRupRatesMap;
	private HashMap<String,ArrayList> segEventRatesMap;
	private HashMap<String, ArrayList> segTimeDepDataMap;
	public final static String MIN_RATE_RUP_MODEL = "Min Rate Model";
	public final static String MAX_RATE_RUP_MODEL = "Max Rate Model";
	public final static String GEOL_INSIGHT_RUP_MODEL = "Geol Insight Solution";
	private PrefFaultSectionDataDB_DAO faultSectionPrefDAO = new PrefFaultSectionDataDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
	private final static String A_FAULT_SEGMENTS_MODEL = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/SegmentModels.txt";
	private final static String UNSEGMENTED_MODEL = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/A_FaultUnsegmentedModels.txt";

	private ArrayList<EventRates> eventRatesList; // Location list where event rates are available

	/**
	 * 
	 * Default constructor
	 */
	public A_FaultsFetcher() {
		aPrioriRupRatesMap = new HashMap<String,A_PrioriRupRates>();
		this.readA_PrioriRupRates();
	}

	/**
	 *  Set the Deformation Model to be used. 
	 *  Also set whether A-Faults are segmented or unsegmented. Both these parameters decide the file
	 *  to be read.
	 * 
	 * @param defModelSummary
	 * @param isUnsegmented
	 */
	public void setDeformationModel(DeformationModelSummary defModelSummary, boolean isUnsegmented) {
		deformationModelId = defModelSummary.getDeformationModelId();
		this.isUnsegmented = isUnsegmented;
		//	find the deformation model
		String fileName=null;
		// get the A-Fault filename based on selected fault model
		if(isUnsegmented)  {
			fileName = UNSEGMENTED_MODEL;
		} else { 
			fileName = A_FAULT_SEGMENTS_MODEL;
		}
		this.loadSegmentModels(fileName);
		readSegEventRates();
		readSegTimeDepData();
	}

	/**
	 * Read rupture rates and segment rates from Excel file
	 *
	 */
	private void readA_PrioriRupRates() {
		try {
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(RUP_RATE_FILE_NAME));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet sheet = wb.getSheetAt(0);
			int lastIndex = sheet.getLastRowNum();
			// read data for each row
			for(int r = 1; r<=lastIndex; ++r) {	
				HSSFRow row = sheet.getRow(r);
				HSSFCell cell = row.getCell( (short) 0);
				// segment name
				String faultName = cell.getStringCellValue().trim();
				faultModelNames.add(faultName);
				A_PrioriRupRates aPrioriRupRates = new A_PrioriRupRates(faultName);
				ArrayList rupNames = new ArrayList();
				++r;
				row = sheet.getRow(r);
				// Get the supported rup model types
				int lastColIndex=0 ;
				ArrayList<String> rupModelTypes = new ArrayList<String>();;
				for(int i=1;true; ++i, ++lastColIndex) {
					cell = row.getCell((short)i);
					if(cell==null || cell.getCellType()==HSSFCell.CELL_TYPE_BLANK) break;
					rupModelTypes.add(row.getCell((short)i).getStringCellValue()); 
				}
				++r;
				while(true) {
					row = sheet.getRow(r++);
					cell = row.getCell( (short) 0);
					String name = cell.getStringCellValue().trim();
					if(name.equalsIgnoreCase("Total"))
						break;
					else rupNames.add(name);
					// get apriori rates
					for(int i=1;i<=lastColIndex; ++i) {
						aPrioriRupRates.putRupRate(rupModelTypes.get(i-1), row.getCell((short)i).getNumericCellValue());
					}
				}
				r=r+1;
				// convert segment names ArrayLList to String[] 
				String ruptureNames[] = new String[rupNames.size()];
				for(int i=0; i<rupNames.size(); ++i) ruptureNames[i] = (String) rupNames.get(i);
				this.aPrioriRupRatesMap.put(faultName, aPrioriRupRates);
				this.segmentNamesMap.put(faultName, ruptureNames);
			}

		}catch(Exception e) {
			e.printStackTrace();
		}
	}


	/**
	 * Read the segment recurrence intervals.
	 *  also reads the table 7 (site name, event rate. sigma and 95% confidence bounds) in Appendix C of UCERF2 report 
	 *
	 */
	private void readSegEventRates() {
		segEventRatesMap = new HashMap<String,ArrayList>();
		Iterator<String> it = faultModelNames.iterator();
		while(it.hasNext()) this.segEventRatesMap.put(it.next(),new  ArrayList());
		eventRatesList = new ArrayList<EventRates>();
		try {				
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(SEG_RATE_FILE_NAME));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet sheet = wb.getSheetAt(0);
			int lastRowIndex = sheet.getLastRowNum();
			double lat, lon, rate, sigma, lower95Conf, upper95Conf;
			String siteName;
			int faultSectionId;
			for(int r=1; r<=lastRowIndex; ++r) {	
//				if(r==8) continue; // Ignore the Hayward North
				HSSFRow row = sheet.getRow(r);
				if(row==null) continue;
				HSSFCell cell = row.getCell( (short) 1);
				if(cell==null || cell.getCellType()==HSSFCell.CELL_TYPE_STRING) continue;
				lat = cell.getNumericCellValue();
				siteName = row.getCell( (short) 0).getStringCellValue().trim();
				lon = row.getCell( (short) 2).getNumericCellValue();
				rate = row.getCell( (short) 3).getNumericCellValue();
				sigma =  row.getCell( (short) 4).getNumericCellValue();
				lower95Conf = row.getCell( (short) 7).getNumericCellValue();
				upper95Conf =  row.getCell( (short) 8).getNumericCellValue();
				faultSectionId = getClosestFaultSectionId(new Location(lat,lon));
				if(faultSectionId==-1) continue; // closest fault section is at a distance of more than 2 km
				String faultName = setRecurIntv(faultSectionId, rate, sigma, lower95Conf, upper95Conf);
				eventRatesList.add(new EventRates(siteName, faultName, lat,lon, rate, sigma, lower95Conf, upper95Conf));
			}
		}catch(Exception e) {
			e.printStackTrace();
		}
	}


	/**
	 * Read Time dependent data (year of last event, slip, aperiodicity) for each segment
	 *
	 */
	private void readSegTimeDepData() {
		segTimeDepDataMap = new HashMap<String, ArrayList>();
		try {
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(SEG_TIME_DEP_FILE_NAME));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet sheet = wb.getSheetAt(0);
			int lastIndex = sheet.getLastRowNum();
			double slip, aperiodicity, lastEventYr;
			// read data for each row
			for(int r = 1; r<=lastIndex; ) {	
				HSSFRow row = sheet.getRow(r);
				HSSFCell cell = row.getCell( (short) 0);
				// segment name
				String faultName = cell.getStringCellValue().trim();
				++r;
				int segIndex = -1;
				ArrayList<SegmentTimeDepData> segTimeDepDataList = new ArrayList<SegmentTimeDepData>();
				while(true) {
					row = sheet.getRow(r++);

					if(row==null) break;

					// Segment name
					cell = row.getCell( (short) 0);
					if(cell==null || cell.getCellType()==HSSFCell.CELL_TYPE_BLANK) break;

					++segIndex;

					// last event yr
					cell = row.getCell( (short) 1);
					if(cell==null || cell.getCellType()==HSSFCell.CELL_TYPE_BLANK) lastEventYr = Double.NaN;
					else lastEventYr = (int)cell.getNumericCellValue();

					// slip in MRE
					cell = row.getCell( (short) 2);
					if(cell==null || cell.getCellType()==HSSFCell.CELL_TYPE_BLANK) slip = Double.NaN;
					else slip = cell.getNumericCellValue();

					// apriodicity
					cell = row.getCell( (short) 3);
					if(cell==null || cell.getCellType()==HSSFCell.CELL_TYPE_BLANK) aperiodicity = Double.NaN;
					else aperiodicity = cell.getNumericCellValue();

					//System.out.println(faultName+","+segIndex+","+lastEventYr+","+slip+","+aperiodicity);

					// Segment Time dependent data
					SegmentTimeDepData segTimeDepData = new SegmentTimeDepData();
					segTimeDepData.setAll(faultName, segIndex, lastEventYr, slip, aperiodicity);
					segTimeDepDataList.add(segTimeDepData);
				}
				segTimeDepDataMap.put(faultName, segTimeDepDataList);
			}

		}catch(Exception e) {
			e.printStackTrace();
		}
	}



	/**
	 * Get time dependent data for selected fault.
	 * 
	 * @param faultName
	 * @return
	 */
	public  ArrayList<SegmentTimeDepData> getSegTimeDepData(String faultName) {
		return this.segTimeDepDataMap.get(faultName);
	}


	/**
	 * It gets the list of all event rates.
	 * It gets them  from Tom Parson's excel sheet
	 * 
	 * @return
	 */
	public ArrayList<EventRates> getEventRatesList() {
		return this.eventRatesList;
	}

	/**
	 * Get closest fault section Id to this location. The fault section should be within 2 km distance of the location else it returns null
	 * 
	 * @param loc
	 * @return
	 */
	private int getClosestFaultSectionId(Location loc) {
		ArrayList<Integer> faultSectionIdList = getAllFaultSectionsIdList();
		double minDist = Double.MAX_VALUE, dist;
		FaultSectionPrefData closestFaultSection=null;
		for(int i=0; i<faultSectionIdList.size(); ++i) {
			FaultSectionPrefData  prefFaultSectionData = faultSectionPrefDAO.getFaultSectionPrefData(faultSectionIdList.get(i));
			//System.out.println(faultSectionIdList.get(i));
			dist  = prefFaultSectionData.getFaultTrace().minDistToLine(loc);
			//System.out.println(prefFaultSectionData.getSectionId()+":"+dist);
			if(dist<minDist) {
				minDist = dist;
				closestFaultSection = prefFaultSectionData;
			}
		}
		//System.out.println(minDist);
		//if(minDist>2) throw new RuntimeException("No fault section close to event rate location:"+loc.getLatitude()+","+loc.getLongitude());
		if(minDist>2) return -1;
		return closestFaultSection.getSectionId();
	}


	/**
	 * Add a segRateConstraint object to the appropriate segRatesList in segEventRatesMap (a list for each segment)
	 * @param faultSectiondId
	 * @param rate
	 * @param sigma
	 */
	private String setRecurIntv(int faultSectionId, double rate, double sigma, double lower95Conf, double upper95Conf) {
		Iterator<String> it = faultModels.keySet().iterator();
		// Iterate over all A-Faults
		while(it.hasNext()) {
			String faultName = it.next();
			ArrayList segRatesList = this.segEventRatesMap.get(faultName);
			ArrayList segmentsList = (ArrayList)this.faultModels.get(faultName);
			// iterate over all segments in this fault
			for(int i=0; i<segmentsList.size(); ++i) {
				ArrayList segment = (ArrayList)segmentsList.get(i);
				// iterate over all sections in a segment
				for(int segIndex=0; segIndex<segment.size(); ++segIndex) {
					if(faultSectionId == ((FaultSectionSummary)segment.get(segIndex)).getSectionId()) {
						SegRateConstraint segRateConstraint = new SegRateConstraint(faultName);
						segRateConstraint.setSegRate(i, rate, sigma, lower95Conf, upper95Conf);
						segRatesList.add(segRateConstraint);
						return faultName;
					}
				}
			}
		}

		throw new RuntimeException ("The location cannot be mapped to a A-Fault segment");
	}

	/**
	 * Get recurrence intervals for selected segment model
	 * @param selectedSegmentModel
	 * @return
	 */
	public  ArrayList<SegRateConstraint> getSegRateConstraints(String faultName) {
		return this.segEventRatesMap.get(faultName);
	}

	/**
	 * Get segment rate constraints for selected faultName and segment index. Returns an empty list, if there is no rate constraint for this segment
	 * @param faultModel
	 * @param segIndex
	 * @return
	 */
	public ArrayList<SegRateConstraint> getSegRateConstraints(String faultName, int segIndex) {
		ArrayList<SegRateConstraint> segRateConstraintList = getSegRateConstraints(faultName);
		ArrayList<SegRateConstraint> segmentRates= new ArrayList<SegRateConstraint>();
		// set the recurrence intervals
		for(int i=0; i<segRateConstraintList.size(); ++i) {
			SegRateConstraint segRateConstraint = segRateConstraintList.get(i);
			if(segRateConstraint.getSegIndex() == segIndex)
				segmentRates.add(segRateConstraint);
		}
		return segmentRates;
	}


	/**
	 * Get apriori rupture rates
	 * @param selectedSegmentModel
	 * @return
	 */
	public ValueWeight[] getAprioriRupRates(String faultName, String rupModelType) {
		A_PrioriRupRates aPrioriRatesList = this.aPrioriRupRatesMap.get(faultName);
		ArrayList<Double> aPrioriRates = aPrioriRatesList.getA_PrioriRates(rupModelType);
		ValueWeight[] rupRates = new ValueWeight[aPrioriRates.size()];
		for(int i=0; i<aPrioriRates.size(); ++i)
			rupRates[i] = new ValueWeight(aPrioriRates.get(i), 1.0);
		return rupRates;
	}

	/**
	 * Get a list of rup models(Eg. Min, Max, Geological Insight) for selected faultName
	 * @param faultModel
	 * @return
	 */
	public ArrayList<String> getRupModels(String faultName) {
		return aPrioriRupRatesMap.get(faultName).getSupportedModelNames(); 
	}
}
