package org.opensha.refFaultParamDb.calc.sectionDists;

import java.io.Serializable;
import java.util.ArrayList;

import org.opensha.commons.data.Container2D;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;

public class FaultSectDistRecord implements Serializable {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	private Container2D<Double> dists1;
	private Container2D<Double> dists2;
	
	private EvenlyGriddedSurfaceAPI surface1;
	private EvenlyGriddedSurfaceAPI surface2;
	
	private Pairing pairing;
	
	private double minDist = Double.MAX_VALUE;
	private double maxDist = 0;
	
	private int[] minDistLoc1 = new int[2];
	private int[] minDistLoc2 = new int[2];
	
	protected FaultSectDistRecord() {
		
	}
	
	/**
	 * This constructs the surfaces using the Stirling representation
	 * @param data1
	 * @param data2
	 * @param disc
	 */
	public FaultSectDistRecord(FaultSectionPrefData data1, FaultSectionPrefData data2, double disc) {
		this(data1.getSectionId(),  new StirlingGriddedSurface(data1.getSimpleFaultData(false), disc),
				data2.getSectionId(),  new StirlingGriddedSurface(data2.getSimpleFaultData(false), disc));
	}
	
	public FaultSectDistRecord(int id1, EvenlyGriddedSurfaceAPI surface1, int id2, EvenlyGriddedSurfaceAPI surface2) {
		// ensure the the lower id is first
		if (id1 < id2) {
			this.pairing = new Pairing(id1, id2);
			this.surface1 = surface1;
			this.surface2 = surface2;
		} else {
			this.pairing = new Pairing(id2, id1);
			this.surface2 = surface1;
			this.surface1 = surface2;
		}
	}
	
	private static ArrayList<int[]> getCornerMidpts(EvenlyGriddedSurfaceAPI surface) {
		ArrayList<int[]> pts = new ArrayList<int[]>();
		
		int lastRow = surface.getNumRows()-1;
		int lastCol = surface.getNumCols()-1;
		
		pts.add(getIndexArray(0, 0));
		pts.add(getIndexArray(0, lastCol));
		pts.add(getIndexArray(lastRow, 0));
		pts.add(getIndexArray(lastRow, lastCol));
		
		int midRow = -1;
		int midCol = -1;
		if (lastRow > 3)
			midRow = surface.getNumRows()/2;
		if (lastCol > 3)
			midCol = surface.getNumCols()/2;
		if (midRow > 0) {
			pts.add(getIndexArray(midRow, 0));
			pts.add(getIndexArray(midRow, lastCol));
		}
		if (midCol > 0) {
			pts.add(getIndexArray(0, midCol));
			pts.add(getIndexArray(lastRow, midCol));
		}
		if (midRow > 0 && midCol > 0) {
			pts.add(getIndexArray(midRow, midCol));
		}
		return pts;
	}
	
	private static int[] getIndexArray(int row, int col) {
		int[] ret = { row, col };
		return ret;
	}
	
	public double calcMinCornerMidptDist(boolean fast) {
		double minDist = Double.MAX_VALUE;
		
		ArrayList<int[]> pts1 = getCornerMidpts(surface1);
		ArrayList<int[]> pts2 = getCornerMidpts(surface2);
		
		for (int[] pt1 : pts1) {
			for (int[] pt2 : pts2) {
				Location loc1 = surface1.get(pt1[0], pt1[1]);
				Location loc2 = surface2.get(pt2[0], pt2[1]);
				double dist;
				if (fast)
					dist = LocationUtils.linearDistanceFast(loc1, loc2);
				else
					dist = LocationUtils.linearDistance(loc1, loc2);
				if (dist < minDist)
					minDist = dist;
			}
		}
		
		return minDist;
	}
	
	public boolean calcIsWithinDistThresh(double distThresh, SurfaceFilter filter, boolean fast) {
		for (int i1=0; i1<surface1.getNumRows(); i1++) {
			for (int j1=0; j1<surface1.getNumCols(); j1++) {
				if (filter != null && !filter.isIncluded(surface1, i1, j1))
					continue;
				Location loc1 = surface1.get(i1, j1);
				for (int i2=0; i2<surface2.getNumRows(); i2++) {
					for (int j2=0; j2<surface2.getNumCols(); j2++) {
						if (filter != null && !filter.isIncluded(surface2, i2, j2))
							continue;
						Location loc2 = surface2.get(i2, j2);
						double dist;
						if (fast)
							dist = LocationUtils.linearDistanceFast(loc1, loc2);
						else
							dist = LocationUtils.linearDistance(loc1, loc2);
						if (dist < distThresh)
							return true;
					}
				}
			}
		}
		return false;
	}
	
	public double calcMinDist(SurfaceFilter filter, boolean fast) {
		calcDistances(filter, fast);
		return minDist;
	}
	
	public void calcDistances(SurfaceFilter filter, boolean fast) {
		dists1 = new Container2D<Double>(surface1.getNumRows(), surface1.getNumCols());
		dists2 = new Container2D<Double>(surface2.getNumRows(), surface2.getNumCols());
		
//		minDist = Double.MAX_VALUE;
//		minDistLoc1 = new int[2];
//		minDistLoc2 = new int[2];
		
		// loop over all row/col combos
		for (int row1=0; row1<surface1.getNumRows(); row1++) {
			for (int col1=0; col1<surface1.getNumCols(); col1++) {
				if (filter != null && !filter.isIncluded(surface1, row1, col1))
					continue;
				for (int row2=0; row2<surface2.getNumRows(); row2++) {
					for (int col2=0; col2<surface2.getNumCols(); col2++) {
						if (filter != null && !filter.isIncluded(surface2, row2, col2))
							continue;
						Location loc1 = surface1.get(row1, col1);
						Location loc2 = surface2.get(row2, col2);
						
						double dist;
						if (fast)
							dist = LocationUtils.linearDistanceFast(loc1, loc2);
						else
							dist = LocationUtils.linearDistance(loc1, loc2);
						if (dist < minDist) {
							minDist = dist;
							minDistLoc1[0] = row1;
							minDistLoc1[1] = col1;
							minDistLoc2[0] = row2;
							minDistLoc2[1] = col2;
						}
						if (dist > maxDist)
							maxDist = dist;
						Double prevDist1 = dists1.get(row1, col1);
						Double prevDist2 = dists1.get(row1, col1);
						if (prevDist1 == null || dist < prevDist1)
							dists1.set(row1, col1, dist);
						if (prevDist2 == null || dist < prevDist2)
							dists2.set(row2, col2, dist);
					}
				}
			}
		}
	}
	
	public void calcDistances(boolean fast) {
		this.calcDistances(null, fast);
	}

	public static long getSerialversionuid() {
		return serialVersionUID;
	}

	public Container2D<Double> getDists1() {
		return dists1;
	}

	public Container2D<Double> getDists2() {
		return dists2;
	}

	public EvenlyGriddedSurfaceAPI getSurface1() {
		return surface1;
	}

	public EvenlyGriddedSurfaceAPI getSurface2() {
		return surface2;
	}

	public int getID1() {
		return pairing.getID1();
	}

	public int getID2() {
		return pairing.getID2();
	}
	
	public Pairing getPairing() {
		return pairing;
	}

	public double getMinDist() {
		return minDist;
	}

	public int[] getMinDistLoc1() {
		return minDistLoc1;
	}

	public int[] getMinDistLoc2() {
		return minDistLoc2;
	}
	
	public double getMaxDist() {
		return maxDist;
	}

}
