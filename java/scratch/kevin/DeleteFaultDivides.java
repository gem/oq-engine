package scratch.kevin;

import java.util.ArrayList;

import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.vo.FaultSectionSummary;

public class DeleteFaultDivides {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		try {
			DB_AccessAPI dbConnection = DB_ConnectionPool.getDB3ReadWriteConn();
			DB_ConnectionPool.authenticateDBConnection(true, true);
			
			FaultSectionVer2_DB_DAO fault2DB = new FaultSectionVer2_DB_DAO(dbConnection);
			
			System.out.print("Fetching faults...");
			ArrayList<FaultSectionSummary> faults = fault2DB.getAllFaultSectionsSummary();
			System.out.println("DONE!");
			
			for (FaultSectionSummary fault : faults) {
				String name = fault.getSectionName();
				String nameMinus1 = name.substring(0, name.length()-1);
				if (nameMinus1.endsWith("_testsplit")) {
					System.out.println("Removing fault '" + name + "' id=" + fault.getSectionId());
					fault2DB.removeFaultSection(fault.getSectionId());
				}
			}
			
			System.exit(0);
		} catch (Throwable e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(1);
		}
	}

}
