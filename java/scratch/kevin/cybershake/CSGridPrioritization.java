package scratch.kevin.cybershake;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.calc.hazardMap.HazardDataSetLoader;
import org.opensha.sha.cybershake.db.CybershakeHazardCurveRecord;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.HazardCurve2DB;
import org.opensha.sha.cybershake.db.SiteInfo2DB;

/**
 * This class is used to prioritize the sites to be calculated in CyberShake. as we create the first
 * map (April-June(ish), 2009)
 * 
 * @author kevin
 *
 */
public class CSGridPrioritization {
	
	public static final int box_nx = 39;
	public static final int box_ny = 22;
	
	public static final int num_grid_sites = 802;
	
	// multiplyer for the weight of diagonals
	private static final double diag_scale_factor = 1.0 / Math.sqrt(2.0);
	
	public static final boolean allow_diags = false;
	
	private DBAccess db;
	
	private SiteInfo2DB site2db;
	private HazardCurve2DB curve2db;
	
	CybershakeSite sites[][] = new CybershakeSite[box_nx][box_ny];
	Double vals[][] = new Double[box_nx][box_ny];
	Double diffs[][] = new Double[box_nx][box_ny];
	
	boolean isProbAt_IML;
	double level;
	int imTypeID;
	
	public CSGridPrioritization(DBAccess db, boolean isProbAt_IML, double level, int imTypeID) {
		System.out.println("DIAG SCALE: " + diag_scale_factor);
		this.db = db;
		site2db = new SiteInfo2DB(db);
		curve2db = new HazardCurve2DB(db);
		
		this.isProbAt_IML = isProbAt_IML;
		this.level = level;
		this.imTypeID = imTypeID;
		System.out.println("isProbAt_IML: " + isProbAt_IML + ", level: " + level + ", imTypeID: " + imTypeID);
		
		populateSiteLists();
//		printArray(false);
		printArray(true);
	}
	
	private CybershakeSite getSiteForID(ArrayList<CybershakeSite> sites, int id) {
		String name = id + "";
		while (name.length() < 3)
			name = "0" + name;
		name = "s" + name;
		
		for (CybershakeSite site : sites) {
			if (site.short_name.equals(name))
				return site;
		}
		throw new RuntimeException("No site found for id=" + id + ", name='" + name + "'");
	}
	
	private void pushColumnIntoArray(ArrayList<CybershakeSite> curColumn, int x) {
		int offset = box_ny - curColumn.size();
		System.out.println("x: " + x + ", off: " + offset + ", colSize: " + curColumn.size());
		for (int j=0; j<curColumn.size(); j++) {
			CybershakeSite site = curColumn.get(j);
			int y = j + offset;
			sites[x][y] = site;
			vals[x][y] = getCurveValForSite(site);
		}
	}
	
	private Double getCurveValForSite(CybershakeSite site) {
		ArrayList<CybershakeHazardCurveRecord> curves = curve2db.getHazardCurveRecordsForSite(site.id);
		if (curves == null || curves.size() == 0)
			return null;
		for (CybershakeHazardCurveRecord curve : curves) {
			System.out.println("FOUND A CURVE (im: " + curve.getImTypeID() + " ? " + imTypeID + ")");
			if (curve.getImTypeID() != imTypeID)
				continue;
			DiscretizedFuncAPI func = curve2db.getHazardCurve(curve.getCurveID());
			System.out.println("FOUND A CURVE VAL!!!!!!!!!");
			return HazardDataSetLoader.getCurveVal(func, isProbAt_IML, level);
		}
		return null;
	}
	
	private void populateSiteLists() {
		for (int x=0; x<box_nx; x++) {
			for (int y=0; y<box_ny; y++) {
				sites[x][y] = null;
				vals[x][y] = null;
			}
		}
		
		ArrayList<CybershakeSite> siteList = site2db.getAllSitesFromDB();
		
		double prevLat = Double.NEGATIVE_INFINITY;
		ArrayList<CybershakeSite> curColumn = new ArrayList<CybershakeSite>();
		int x = 0;
		for (int i=0; i<num_grid_sites; i++) {
			CybershakeSite site = getSiteForID(siteList, i);
			if (site.lat < prevLat) {
				// this means we're onto the next column
				pushColumnIntoArray(curColumn, x);
				curColumn.clear();
				x++;
			}
			curColumn.add(site);
			prevLat = site.lat;
		}
		pushColumnIntoArray(curColumn, x);
	}
	
	private void printArray(boolean printVals) {
		printArray(printVals, false);
	}
	
	private void printArray(boolean printVals, boolean printDiffs) {
		boolean xs = false;
		for (int y=box_ny-1; y>=0; y--) {
			String line = "";
			for (int x=0; x<box_nx; x++) {
				if (!printVals) {
					CybershakeSite site = sites[x][y];
					if (site == null) {
						if (xs)
							line += " ";
						else
							line += "[    ]";
					}else {
						if (xs)
							line += "x";
						else
							line += "[" + site.short_name + "]";
					}
				} else {
					Double val = vals[x][y];
					if (val == null) {
						if (xs)
							line += " ";
						else {
							if (sites[x][y] == null) {
								line += "[      ]";
							}
							else {
								Double diff = 0d;
								if (diffs[x][y] != null)
									diff = diffs[x][y];
								if (diff > 0) {
									String str = diff.toString();
									while (str.length() < 4)
										str += "0";
									line += "[ " + str.substring(0, 4) + " ]";
								}
								else {
									line += "[      ]";
								}
							}
						}
					}else {
						if (xs)
							line += "x";
						else {
							String str = val.toString();
							while (str.length() < 4)
								str += "0";
							line += "[*" + str.substring(0, 4) + "*]";
						}
					}
				}
			}
			System.out.println(line);
		}
	}
	
	private class CybershakeDiffSite extends CybershakeSite {
		public double diff;
		public CybershakeDiffSite(CybershakeSite site, double diff) {
			super(site.id, site.lat, site.lon, site.name, site.short_name, site.type_id);
			this.diff = diff;
		}
		
		public String toString() {
			return super.toString() + " DIFF: " + diff;
		}
	}
	
	public void addSiteInPlace(ArrayList<CybershakeDiffSite> list, CybershakeSite site, double diff) {
		for (int i=0; i<list.size(); i++) {
			if (list.get(i).diff < diff) {
				list.add(i, new CybershakeDiffSite(site, diff));
				return;
			}
		}
		list.add(new CybershakeDiffSite(site, diff));
	}
	
	private Double getValueAt(int x, int y) {
		if (x < 0 || y < 0 || x >= box_nx || y >= box_ny) {
			return null;
		}
		return vals[x][y];
	}
	
	private void printMat(Double mat[][]) {
		for (int i=mat.length-1; i>=0; i--) {
			Double row[] = mat[i];
			String line = "";
			for (int j=row.length-1; j>=0; j--) {
				line += "[" + row[j] + "]";
			}
			System.out.println(line);
		}
	}
	
	public double getPriorityScoreForSite(int x, int y) {
		if (x == 0 || y == 0 || x == (box_nx-1) || y == (box_ny-1)) {
			return 0;
		}
		Double mat[][] = new Double[5][5];
		int theI = 0;
		for (int i=x-2; i<x+3; i++) {
			int theJ = 0;
			for (int j=y-2; j<y+3; j++) {
				mat[theI][theJ] = getValueAt(i, j);
				theJ++;
			}
			theI++;
		}
		printMat(mat);
		Double xDiff = null;
		if (mat[1][2] != null && mat[3][2] != null) {
			xDiff = Math.abs(mat[1][2] - mat[3][2]);
			System.out.println("INNER XDIF: " + xDiff);
		} else if (mat[0][2] != null && mat[4][2] != null) {
			xDiff = Math.abs(mat[0][2] - mat[4][2]);
			System.out.println("OUTER XDIF: " + xDiff);
		} else if (allow_diags && mat[1][1] != null && mat[3][3] != null) {
			xDiff = Math.abs(mat[1][1] - mat[3][3]) * diag_scale_factor;
			System.out.println("INNER DIAG XDIF: " + xDiff);
		} else if (allow_diags && mat[0][0] != null && mat[4][4] != null) {
			xDiff = Math.abs(mat[0][0] - mat[4][4]) * diag_scale_factor;
			System.out.println("OUTER DIAG XDIF: " + xDiff);
		}
		Double yDiff = null;
		if (mat[2][1] != null && mat[2][3] != null) {
			yDiff = Math.abs(mat[2][1] - mat[2][3]);
			System.out.println("INNER YDIF: " + yDiff);
		} else if (mat[2][0] != null && mat[2][4] != null) {
			yDiff = Math.abs(mat[2][0] - mat[2][4]);
			System.out.println("OUTER YDIF: " + yDiff);
		} else if (allow_diags && mat[3][1] != null && mat[1][3] != null) {
			xDiff = Math.abs(mat[3][1] - mat[1][3]) * diag_scale_factor;
			System.out.println("INNER DIAG YDIF: " + xDiff);
		} else if (allow_diags && mat[0][4] != null && mat[4][0] != null) {
			xDiff = Math.abs(mat[0][4] - mat[4][0]) * diag_scale_factor;
			System.out.println("OUTER DIAG YDIF: " + xDiff);
		}
		if (xDiff == null && yDiff == null)
			return 0;
		else if (xDiff == null)
			return yDiff;
		else if (yDiff == null)
			return xDiff;
		else
			return (xDiff + yDiff) * 0.5;
	}
	
	public ArrayList<CybershakeDiffSite> getPrioritizedList(int siteTypeID) {
		ArrayList<CybershakeDiffSite> list = new ArrayList<CybershakeDiffSite>();
		
		for (int x=0; x<box_nx; x++) {
			for (int y=0; y<box_ny; y++) {
				CybershakeSite site = sites[x][y];
				if (site == null || site.type_id != siteTypeID)
					continue;
				if (vals[x][y] != null)
					continue;
				double diff = getPriorityScoreForSite(x, y);
				System.out.println("(" + x + ", " + y + ", " + diff + ")");
				diffs[x][y] = diff;
				addSiteInPlace(list, site, diff);
			}
		}
		
		return list;
	}
	
	public ArrayList<CybershakeDiffSite> getMasterPriorityList() {
		ArrayList<CybershakeDiffSite> list = getPrioritizedList(CybershakeSite.TYPE_GRID_20_KM);
		list.addAll(getPrioritizedList(CybershakeSite.TYPE_GRID_10_KM));
		list.addAll(getPrioritizedList(CybershakeSite.TYPE_GRID_05_KM));
		return list;
	}
	
	public static void main(String args[]) throws IOException {
		boolean stdout;
		String outFile = "";
		if (args.length == 0) {
			stdout = true;
		} else {
			stdout = false;
			outFile = args[0];
		}
		
		boolean isProbAt_IML = false;
		double level = 0.0004;
		int imTypeID = 21;
		CSGridPrioritization grid = new CSGridPrioritization(Cybershake_OpenSHA_DBApplication.db, isProbAt_IML, level, imTypeID);
		ArrayList<CybershakeDiffSite> list = grid.getMasterPriorityList();
		grid.printArray(true, true);
		
		FileWriter fw = null;
		if (!stdout) {
			fw = new FileWriter(outFile);
		}
		int i=0;
		for (CybershakeDiffSite site : list) {
			String line = i + ". " + site;
			if (stdout)
				System.out.println(line);
			else
				fw.write(line + "\n");
			i++;
		}
		if (fw != null)
			fw.close();
		System.exit(0);
	}

}
