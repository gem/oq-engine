/**
 * 
 */
package org.opensha.refFaultParamDb.excelToDatabase;

import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.util.FileUtils;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;

/**
 * Update the end time from 0 AD to Publication year. It came from Peter Bird's updates
 * 
 * @author vipingupta
 *
 */
public class EndTimeUpdation {
	// update the end time with publication year instead of 0 AD
	private final static String FILE_NAME = "org/opensha/refFaultParamDb/excelToDatabase/EndTime.csv";
	// database connection
	private  static final DB_AccessAPI dbConnection = DB_ConnectionPool.getDB2ReadOnlyConn();
	 
	public static void main(String[] args) {
		SessionInfo.setUserName("vgupta");
		SessionInfo.setPassword("vgupta");
		try {
			ArrayList<String> lines = FileUtils.loadFile(FILE_NAME);
			int updatedLines = 0;
			for(int i=1; i<lines.size(); ++i) {
				String line = lines.get(i);
				StringTokenizer tokenizer = new StringTokenizer(line,",");
				int siteId= Integer.parseInt(tokenizer.nextToken());
				int referenceId =  Integer.parseInt(tokenizer.nextToken());
				int year= Integer.parseInt(tokenizer.nextToken()); 
				ResultSet rsEndTime = dbConnection.queryData("select end_time_id from " +
						"combined_events_info,COMBINED_EVENTS_REFERENCES  where site_id="+siteId+
						" and REFERENCE_ID="+referenceId +" and COMBINED_EVENTS_REFERENCES.COMBINED_EVENTS_ID=combined_events_info.info_id");
				while(rsEndTime.next()) {
					int endTimeId = rsEndTime.getInt("end_time_id");
					ResultSet rsTimeEstId = dbConnection.queryData("select is_ka, time_est_id from time_estimate_info where time_instance_id="+endTimeId);
					while(rsTimeEstId.next()) {
						int estimateId = rsTimeEstId.getInt("time_est_id");
						String isKa = rsTimeEstId.getString("is_ka");
						if(isKa.equalsIgnoreCase("y")) continue;
						String query = "select EST_ID, (PREF_X+0) PREF_X, (MIN_X+0) MIN_X, (MAX_X+0) MAX_X  from min_max_pref_est where est_id="+estimateId;
						//System.out.println(query);
						ResultSet minMaxRs = dbConnection.queryData(query);
						minMaxRs.next(); 
						double prefX = minMaxRs.getFloat("pref_x");
						double minX = minMaxRs.getFloat("min_x");
						double maxX = minMaxRs.getFloat("max_x");
						if(prefX<1e-6 && minX<1e-6 && maxX<1e-6) {
							dbConnection.insertUpdateOrDeleteData("update MIN_MAX_PREF_EST set pref_x="+year+" where est_id="+estimateId);
							++updatedLines;
						}
					}
				}
			
			}
			System.out.println("Lines in Excel sheet="+(lines.size()-1));
			System.out.println("Updated Lines="+updatedLines);
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
}
