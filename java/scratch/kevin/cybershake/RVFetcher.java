package scratch.kevin.cybershake;

import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.sha.cybershake.db.CybershakeERF;
import org.opensha.sha.cybershake.db.CybershakeRuptureRecord;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.ERF2DB;
import org.opensha.sha.cybershake.db.PeakAmplitudesFromDB;

public class RVFetcher {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		DBAccess db = new DBAccess(Cybershake_OpenSHA_DBApplication.HOST_NAME,
				Cybershake_OpenSHA_DBApplication.DATABASE_NAME);
		
		ERF2DB erf2db = new ERF2DB(db);
		
		// get the ERFs so we can choose an ID. idealy you'd have a drop down box for this in the gui
		// the first one in this list will have the greatest ID
		ArrayList<CybershakeERF> erfs = erf2db.getAllERFs();
		int erfID = erfs.get(0).id;
		
		System.out.println("ERF_ID: " + erfID);
		
		ArrayList<Integer> sourceIDs = new ArrayList<Integer>();
		ArrayList<String> sourceNames = new ArrayList<String>();
		erf2db.loadSourceList(erfID, sourceIDs, sourceNames);
		
		// you would have a drop down box to choose source ID from the list (display the names in the list)
		int sourceID = sourceIDs.get(0);
		System.out.println("Source ID: " + sourceID + " name: " + sourceNames.get(0));
		
		ArrayList<CybershakeRuptureRecord> rups = erf2db.getRuptures(erfID, sourceID);
		System.out.println("Got these ruptures:");
		for (CybershakeRuptureRecord rup : rups) {
			System.out.println(rup);
		}
		
		CybershakeRuptureRecord rup = rups.get(0); // maybe select the one with greatest probability by default
		System.out.println("Selected Rup_ID: " + rup.getRupID());
		
		// we need a rv scenario ID...idealy this would be in a drop down box as well
		PeakAmplitudesFromDB amps2db = new PeakAmplitudesFromDB(db);
		// this is the rv scenario IDs, greatest first
		ArrayList<Integer> rvScenIDs = amps2db.getRupVarScenarioIDs();
		int rupVarScenID = rvScenIDs.get(0);
		System.out.println("Rupture Variation Scenario ID: " + rupVarScenID);
		
		ArrayList<String> lfns = new ArrayList<String>();
		ArrayList<Location> hypocenterLocs = new ArrayList<Location>();
		erf2db.loadRVs(erfID, rupVarScenID, sourceID, rup.getRupID(), lfns, hypocenterLocs);
		
		System.out.println("Got these RVs:");
		for (int i=0; i<lfns.size(); i++) {
			System.out.println(lfns.get(i) + " loc: " + hypocenterLocs.get(i));
		}
		db.destroy();
		System.exit(0);
	}

}
