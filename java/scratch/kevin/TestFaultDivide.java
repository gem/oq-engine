package scratch.kevin;

import java.sql.SQLException;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.dao.db.PrefFaultSectionDataDB_DAO;
import org.opensha.refFaultParamDb.gui.LoginWindow;
import org.opensha.refFaultParamDb.vo.FaultSectionData;
import org.opensha.sha.faultSurface.FaultTrace;

public class TestFaultDivide {
	
	private static DB_AccessAPI dbConnection = DB_ConnectionPool.getDB3ReadWriteConn();
	
	public TestFaultDivide() {
	}
	
	public static void divide(DB_AccessAPI dbConnection, FaultSectionVer2_DB_DAO fault2db,
			PrefFaultSectionDataDB_DAO prefDB, FaultSectionData fault) throws SQLException {
		FaultSectionData part1 = fault.clone();
		FaultSectionData part2 = fault.clone();
		
		FaultTrace trace = fault.getFaultTrace();
		
		System.out.println("Trace has " + trace.getNumLocations() + " locs!");
		
		FaultTrace trace1 = trace.clone();
		FaultTrace trace2 = trace.clone();
		
		int numLocs = trace.getNumLocations();
		int numFirst = numLocs / 2;
		for (int i=numFirst+1; i<numLocs; i++) {
			trace1.remove(numFirst+1);
		}
		for (int i=0; i<numFirst; i++) {
			trace2.remove(0);
		}
		
		if (trace1.getNumLocations() < 2)
			throw new RuntimeException("Trace 1 now has less than 2 locs");
		if (trace2.getNumLocations() < 2)
			throw new RuntimeException("Trace 2 now has less than 2 locs");
		if ((trace1.getNumLocations() + trace2.getNumLocations()) != (trace.getNumLocations() + 1))
			throw new RuntimeException("Trace split incorrectly (num pts doesn't match!");
		
		System.out.println("Split should work!");
		
		part1.setFaultTrace(trace1);
		part1.setSectionName(fault.getSectionName() + "_testsplit1");
		
		addNewFault(TestFaultDivide.dbConnection, fault2db, prefDB, part1);
		
		part2.setFaultTrace(trace2);
		part2.setSectionName(fault.getSectionName() + "_testsplit2");
		
		addNewFault(TestFaultDivide.dbConnection, fault2db, prefDB, part2);
	}
	
	public static void splitOnLoc(DB_AccessAPI dbConnection, FaultSectionVer2_DB_DAO fault2db,
			PrefFaultSectionDataDB_DAO prefDB, FaultSectionData fault, Location loc) throws SQLException {
		
		System.out.println("Splitting on location: " + loc);
		
		FaultSectionData part1 = fault.clone();
		FaultSectionData part2 = fault.clone();
		
		FaultTrace trace = fault.getFaultTrace();
		int numTraceLocs = trace.getNumLocations();
		
		System.out.println("Trace has " + numTraceLocs + " locs!");
		
		FaultTrace trace1 = trace.clone();
		FaultTrace trace2 = trace.clone();
		
		double minDist = Double.MAX_VALUE;
		int closestIndex = -1;
		for (int i=0; i<numTraceLocs; i++) {
			Location traceLoc = trace.get(i);
			double dist = LocationUtils.linearDistance(loc, traceLoc);
			
			if (dist < minDist) {
				minDist = dist;
				closestIndex = i;
			}
		}
		
		if (closestIndex < 0)
			throw new RuntimeException("something went wrong...");
		
		if (closestIndex == 0) {
			throw new RuntimeException("closest index is first trace el!");
		}
		
		if (closestIndex == (numTraceLocs-1)) {
			throw new RuntimeException("closest index is last trace el!");
		}
		
		int beforeIndex, afterIndex;
		
		double distBeforeClosest = LocationUtils.linearDistance(loc, trace.get(closestIndex-1));
		double distAfterClosest = LocationUtils.linearDistance(loc, trace.get(closestIndex+1));
		
		if (distBeforeClosest < distAfterClosest) {
			beforeIndex = closestIndex-1;
			afterIndex = closestIndex;
		} else {
			beforeIndex = closestIndex;
			afterIndex = closestIndex+1;
		}
		
		while (trace1.getNumLocations() > afterIndex) {
			trace1.remove(trace1.getNumLocations()-1);
		}
		trace1.add(loc);
		
		if (trace1.getNumLocations() != (afterIndex + 1))
			throw new RuntimeException("messed up with trace1!");
		
		while (trace2.getNumLocations() >= (numTraceLocs - beforeIndex)) {
			trace2.remove(0);
		}
		trace2.add(0, loc);
		
		if (trace1.getNumLocations() < 2)
			throw new RuntimeException("Trace 1 now has less than 2 locs");
		if (trace2.getNumLocations() < 2)
			throw new RuntimeException("Trace 2 now has less than 2 locs");
		if ((trace1.getNumLocations() + trace2.getNumLocations()) != (trace.getNumLocations() + 2))
			throw new RuntimeException("Trace split incorrectly (num pts doesn't match!");
		
		System.out.println("-----TRACE-----");
		printTrace(trace);
		System.out.println("-----TRACE 1-----");
		printTrace(trace1);
		System.out.println("-----TRACE 2-----");
		printTrace(trace2);
		
		System.out.println("Split should work!");
		
		part1.setFaultTrace(trace1);
		part1.setSectionName(fault.getSectionName() + "_testsplit1");
		
		addNewFault(TestFaultDivide.dbConnection, fault2db, prefDB, part1);
		
		part2.setFaultTrace(trace2);
		part2.setSectionName(fault.getSectionName() + "_testsplit2");
		
		addNewFault(TestFaultDivide.dbConnection, fault2db, prefDB, part2);
	}
	
	private static void printTrace(FaultTrace trace) {
		System.out.println("NAME: " + trace.getName() + " LOCS: " + trace.getNumLocations());
		for (Location loc : trace)
			System.out.println(loc.getLatitude() + "\t" + loc.getLongitude());
	}
	
	private static void addNewFault(DB_AccessAPI dbConnection, FaultSectionVer2_DB_DAO fault2db,
			PrefFaultSectionDataDB_DAO prefDB, FaultSectionData fault) throws SQLException {
		int newID = dbConnection.getNextSequenceNumber(FaultSectionVer2_DB_DAO.SEQUENCE_NAME);
		fault.setSectionId(newID);
		
		System.out.println("Adding sec # " + fault.getSectionId() + " to the DB");
		fault2db.addFaultSection(fault);
		prefDB.rePopulatePrefDataTable(newID);
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		try {
			DB_ConnectionPool.authenticateDBConnection(true, true);
			
			FaultSectionVer2_DB_DAO fault2db = new FaultSectionVer2_DB_DAO(dbConnection);
			PrefFaultSectionDataDB_DAO prefDB = new PrefFaultSectionDataDB_DAO(dbConnection);
			FaultSectionData fault = fault2db.getFaultSection(49);
			
//			divide(dbConnection, fault2db, fault);
			Location splitLoc = new Location(34.9068135, -118.7189);
			splitOnLoc(dbConnection, fault2db, prefDB, fault, splitLoc);
			
			System.exit(0);
		} catch (Throwable e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(1);
		}
	}

}
