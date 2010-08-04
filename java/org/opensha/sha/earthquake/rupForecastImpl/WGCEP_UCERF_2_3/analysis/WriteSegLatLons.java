/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.io.File;
import java.io.FileWriter;
import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.DeformationModelSummaryDB_DAO;
import org.opensha.refFaultParamDb.vo.DeformationModelSummary;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data.A_FaultsFetcher;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 * Write Segment latitude and longitudes in a file.
 * One file for each segment.
 * 
 * @author vipingupta
 *
 */
public class WriteSegLatLons {
	private DeformationModelSummaryDB_DAO defModelSummaryDAO = new DeformationModelSummaryDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
	private final static boolean IS_ASEIS_REDUCES_AREA = false;

	/**
	 * Directory where files will be saved.
	 * A subdirectory for each fault name is created in this main directory.
	 * The files are named as segmentname.txt
	 * 
	 * @param dir
	 */
	public WriteSegLatLons(String dir) {
		A_FaultsFetcher faultFetcher = new A_FaultsFetcher();
		ArrayList<DeformationModelSummary> defModelSummaryList = defModelSummaryDAO.getAllDeformationModels();
		String defModelName = "D2.1";
		DeformationModelSummary defModelSummary=null;
		for(int i=0; i<defModelSummaryList.size() && defModelSummary==null; ++i) {
			if(defModelSummaryList.get(i).getDeformationModelName().equalsIgnoreCase(defModelName))
				defModelSummary = defModelSummaryList.get(i);
		}
		faultFetcher.setDeformationModel(defModelSummary, false);

		// fault segment data list
		ArrayList<FaultSegmentData> faultSegDataList = faultFetcher.getFaultSegmentDataList(IS_ASEIS_REDUCES_AREA);
		try {
			// loop over all fault names
			for(int i=0; i<faultSegDataList.size(); ++i) {
				FaultSegmentData faultSegData = faultSegDataList.get(i);
				ArrayList sectionToSegData = faultSegData.getSectionToSegmentData();
				String faultName = faultSegData.getFaultName();
				int numSegs = sectionToSegData.size();
				String faultDir = dir+"/"+faultName;
				File file = new File(faultDir);
				file.mkdirs();
				// loop over all segments
				for(int segIndex=0; segIndex<numSegs; ++segIndex) {
					String segName = faultSegData.getSegmentName(segIndex);
					ArrayList prefFaultSectionList = (ArrayList)sectionToSegData.get(segIndex);
					FileWriter fw = new FileWriter(faultDir+"/"+segName+".txt");
					for(int prefFaultSectionId=0; prefFaultSectionId<prefFaultSectionList.size(); ++prefFaultSectionId) {
						FaultSectionPrefData prefFaultSectionData = (FaultSectionPrefData)prefFaultSectionList.get(prefFaultSectionId);
						FaultTrace faultTrace = prefFaultSectionData.getFaultTrace();
						for(int pt=0; pt<faultTrace.getNumLocations(); ++pt) {
							Location loc = faultTrace.get(pt);
							fw.write((float)loc.getLatitude()+"\t"+(float)loc.getLongitude()+"\t0\n");
						}

					}
					fw.close();
				}
			}
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	public static void main(String[] args) {
		new WriteSegLatLons("SegmentFiles");
	}
}
