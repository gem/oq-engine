/**
 * 
 */
package org.opensha.refFaultParamDb.excelToDatabase;

import java.util.ArrayList;

import org.opensha.commons.geo.LocationUtils;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.dao.db.PrefFaultSectionDataDB_DAO;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 * It checks the dip directions in the database
 * @author vipingupta
 *
 */
public class CheckDipDirections {
	private PrefFaultSectionDataDB_DAO prefFaultSectionDAO = new PrefFaultSectionDataDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
	private FaultSectionVer2_DB_DAO faultSectionDAO = new FaultSectionVer2_DB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
	
	public CheckDipDirections() {
		
		ArrayList<FaultSectionPrefData> faultSectionPrefDataList = prefFaultSectionDAO.getAllFaultSectionPrefData();
		
		for(int i=0; i<faultSectionPrefDataList.size(); ++i) {
			FaultSectionPrefData faultSectionPrefData = faultSectionPrefDataList.get(i);
			FaultTrace faultSectionTrace = faultSectionPrefData.getFaultTrace();
			double dipDirectionFromOpenSHA = 90+LocationUtils.vector(faultSectionTrace.get(0),
					faultSectionTrace.get(faultSectionTrace.getNumLocations()-1)).getAzimuth();
			if(dipDirectionFromOpenSHA<0) dipDirectionFromOpenSHA+=360;
			else if(dipDirectionFromOpenSHA>360) dipDirectionFromOpenSHA-=360;
			System.out.println(faultSectionPrefData.getSectionId()+"\t"+dipDirectionFromOpenSHA+"\t"+faultSectionPrefData.getSectionName());
			faultSectionDAO.updateDipDirection(faultSectionPrefData.getSectionId(), (float) dipDirectionFromOpenSHA);
			}
	}
	
	public static void main(String[] args) {
		// FIRST SET USERNAME AND PASSOWRD IN SessionInfo Class
		new CheckDipDirections();
	}
}
