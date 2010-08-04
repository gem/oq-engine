package scratch.kevin.cybershake;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.cybershake.db.CybershakeHazardCurveRecord;
import org.opensha.sha.cybershake.db.CybershakeIM;
import org.opensha.sha.cybershake.db.CybershakeRun;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.HazardCurve2DB;
import org.opensha.sha.cybershake.db.HazardCurveComputation;
import org.opensha.sha.cybershake.db.PeakAmplitudesFromDB;
import org.opensha.sha.cybershake.db.SiteInfo2DB;
import org.opensha.sha.gui.controls.CyberShakePlotFromDBControlPanel;

public class BulkCSCurveReplacer {
	
	private DBAccess db;
	
	private PeakAmplitudesFromDB amps2db;
	private SiteInfo2DB sites2db;
	private HazardCurve2DB curve2db;
	
	private ArrayList<CybershakeSite> ampSites;
	private ArrayList<CybershakeRun> ampRuns;
	private HashMap<Integer, ArrayList<CybershakeHazardCurveRecord>> curveRecordsMap;
	private HashMap<Integer, ArrayList<DiscretizedFuncAPI>> curvesMap;
	
	private HashMap<Integer, CybershakeIM> imMap = new HashMap<Integer, CybershakeIM>();
	
	public BulkCSCurveReplacer(DBAccess db) {
		this(db, null);
	}
	
	public BulkCSCurveReplacer(DBAccess db, ArrayList<Integer> runIDs) {
		this.db = db;
		this.amps2db = new PeakAmplitudesFromDB(db);
		this.sites2db = new SiteInfo2DB(db);
		this.curve2db = new HazardCurve2DB(db);
		
		ampRuns = amps2db.getPeakAmpRuns();
		ampSites = new ArrayList<CybershakeSite>();
		curveRecordsMap = new HashMap<Integer, ArrayList<CybershakeHazardCurveRecord>>();
		curvesMap = new HashMap<Integer, ArrayList<DiscretizedFuncAPI>>();
		
		for (CybershakeRun run : ampRuns) {
			if (runIDs != null && !runIDs.contains(run.getRunID()))
				continue;
			ampSites.add(sites2db.getSiteFromDB(run.getSiteID()));
			ArrayList<CybershakeHazardCurveRecord> records = curve2db.getHazardCurveRecordsForRun(run.getRunID());
			if (records != null && !records.isEmpty()) {
				ArrayList<DiscretizedFuncAPI> curves = new ArrayList<DiscretizedFuncAPI>();
				for (CybershakeHazardCurveRecord record : records) {
					curves.add(curve2db.getHazardCurve(record.getCurveID()));
				}
				curveRecordsMap.put(run.getRunID(), records);
				curvesMap.put(run.getRunID(), curves);
			}
		}
	}
	
	public static String getFileName(int runID, int curveID) {
		return "run_" + runID + "_curve_" + curveID + ".txt";
	}
	
	public void writeAllCurvesToDir(String dir) throws IOException {
		File dirFile = new File(dir);
		
		if (!dirFile.exists())
			dirFile.mkdirs();
		
		if (!dir.endsWith(File.separator))
			dir += File.separator;
		
		for (CybershakeRun run : ampRuns) {
			ArrayList<CybershakeHazardCurveRecord> records = curveRecordsMap.get(new Integer(run.getRunID()));
			ArrayList<DiscretizedFuncAPI> curves = curvesMap.get(new Integer(run.getRunID()));
			if (records == null)
				continue;
			for (int i=0; i<records.size(); i++) {
				CybershakeHazardCurveRecord record = records.get(i);
				DiscretizedFuncAPI curve = curves.get(i);
				
				String fileName = dir + getFileName(run.getRunID(), record.getCurveID());
				
				ArbitrarilyDiscretizedFunc.writeSimpleFuncFile(curve, fileName);
			}
		}
	}
	
	private boolean doesCurveHaveXValues(DiscretizedFuncAPI curve, ArrayList<Double> xVals) {
		if (xVals.size() != curve.getNum())
			return false;
		for (int i=0; i<curve.getNum(); i++) {
			boolean matched = false;
			for (double xVal : xVals) {
				if (xVal == curve.getX(i)) {
					matched = true;
					break;
				}
			}
			if (!matched)
				return false;
		}
		return true;
	}
	
	public void recalculateAllCurves(String dir) throws IOException {
		File dirFile = new File(dir);
		
		if (!dirFile.exists())
			dirFile.mkdirs();
		
		if (!dir.endsWith(File.separator))
			dir += File.separator;
		
		ArbitrarilyDiscretizedFunc func = CyberShakePlotFromDBControlPanel.createUSGS_PGA_Function();
		ArrayList<Double> imVals = new ArrayList<Double>();
		for (int i=0; i<func.getNum(); i++)
			imVals.add(func.getX(i));
		
		HazardCurveComputation calc = new HazardCurveComputation(db);
		
		for (CybershakeRun run : ampRuns) {
			ArrayList<CybershakeHazardCurveRecord> records = curveRecordsMap.get(new Integer(run.getRunID()));
			if (records == null)
				continue;
			for (int i=0; i<records.size(); i++) {
				CybershakeHazardCurveRecord record = records.get(i);
				
				String fileName = dir + getFileName(run.getRunID(), record.getCurveID());
				File curveFile = new File(fileName);
				if (curveFile.exists()) {
					try {
						DiscretizedFuncAPI oldFunc = ArbitrarilyDiscretizedFunc.loadFuncFromSimpleFile(fileName);
						if (oldFunc.getNum() == imVals.size())
							continue;
					} catch (Exception e) {
						e.printStackTrace();
					}
				} else if (record.getImTypeID() == 26) {
//					// this is a 2 sec curve, i might have just recalculated it. Lets make sure it doesn't
//					// already have a point at 1.0 on the curve
//					DiscretizedFuncAPI dbCurve = curve2db.getHazardCurve(record.getCurveID());
//					boolean skip = doesCurveHaveXValues(dbCurve, imVals);
//					if (skip) {
//						System.out.println("This 2sec curve is already good...");
//						continue;
//					} else {
//						System.out.println("This 2sec curve needs recalculating!!!!!!");
//					}
				}
				
				CybershakeIM im = imMap.get(record.getImTypeID());
				if (im == null) {
					im = curve2db.getIMFromID(record.getImTypeID());
					imMap.put(record.getImTypeID(), im);
				}
				
				long prev = System.currentTimeMillis();
				DiscretizedFuncAPI curve = calc.computeHazardCurve(imVals, run, im);
				double secs = ((double)(System.currentTimeMillis() - prev)) / 1000d;
				
				// hit at garbage collection every 10 curves
				if (i % 10 == 0 && i > 0)
					System.gc();
				
				System.out.println("Took " + secs + " secs to calculate curve, writing " + fileName);
				
				ArbitrarilyDiscretizedFunc.writeSimpleFuncFile(curve, fileName);
			}
		}
	}
	
	public void insertNewCurves(String newDir, String doneDir) {
		File dirFile = new File(doneDir);
		
		if (!dirFile.exists())
			dirFile.mkdirs();
		
		if (!newDir.endsWith(File.separator))
			newDir += File.separator;
		
		if (!doneDir.endsWith(File.separator))
			doneDir += File.separator;
		
		for (CybershakeRun run : ampRuns) {
			ArrayList<CybershakeHazardCurveRecord> records = curveRecordsMap.get(new Integer(run.getRunID()));
			if (records == null)
				continue;
			for (int i=0; i<records.size(); i++) {
				CybershakeHazardCurveRecord record = records.get(i);
				
				String newFileName = newDir + getFileName(run.getRunID(), record.getCurveID());
				String doneFileName = doneDir + getFileName(run.getRunID(), record.getCurveID());
				File curveFile = new File(newFileName);
				File doneFile = new File(doneFileName);
				if (curveFile.exists() && !doneFile.exists()) {
					try {
						DiscretizedFuncAPI func = ArbitrarilyDiscretizedFunc.loadFuncFromSimpleFile(newFileName);
						curve2db.replaceHazardCurve(record.getCurveID(), func);
						ArbitrarilyDiscretizedFunc.writeSimpleFuncFile(func, doneFileName);
					} catch (IOException e) {
						e.printStackTrace();
						continue;
					}
				}
			}
		}
	}
	
	public static void main(String args[]) throws IOException {
		DBAccess db = null;
		
		boolean doInsert = true;
		
		if (doInsert)
			db = Cybershake_OpenSHA_DBApplication.getAuthenticatedDBAccess(true, false);
		else
			db = Cybershake_OpenSHA_DBApplication.db;
		
		ArrayList<Integer> runs = new ArrayList<Integer>();
		runs.add(228);
		runs.add(229);
		runs.add(230);
		runs.add(231);
		runs.add(234);
		runs.add(236);
		runs.add(237);
		runs.add(238);
		runs.add(239);
		runs.add(245);
		runs.add(247);
		runs.add(249);
		runs.add(336);
		
		BulkCSCurveReplacer bulk = new BulkCSCurveReplacer(db, runs);
		
		String initialDir = "/home/kevin/CyberShake/curves/prePatchS";
		String newDir = "/home/kevin/CyberShake/curves/postPatchS";
		
		bulk.writeAllCurvesToDir(initialDir);
		bulk.recalculateAllCurves(newDir);
		
		if (doInsert) {
			String doneDir = "/home/kevin/CyberShake/curves/patchedCurvesS";
			bulk.insertNewCurves(newDir, doneDir);
		}
		
		System.exit(0);
	}

	public ArrayList<CybershakeSite> getAmpSites() {
		return ampSites;
	}

	public ArrayList<CybershakeRun> getAmpRuns() {
		return ampRuns;
	}
}
