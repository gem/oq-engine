package org.opensha.refFaultParamDb.calc.sectionDists;

import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

public class SmartSurfaceFilter implements SurfaceFilter {
	
	private int internalModulus;
	private int outlineModulus;
	
	private double cornerMidptDistFilter;
	
	public SmartSurfaceFilter(int outlineModulus, int internalModulus, double cornerMidptDistFilter) {
		if (internalModulus < 2)
			internalModulus = 2;
		this.internalModulus = internalModulus;
		if (outlineModulus < 1)
			outlineModulus = 1;
		this.outlineModulus = outlineModulus;
		this.cornerMidptDistFilter = cornerMidptDistFilter;
	}

	@Override
	public boolean isIncluded(EvenlyGriddedSurfaceAPI surface, int row, int col) {
		// include all corners
		if (isCorner(surface, row, col))
			return true;
		
		// include the entire outline
		if (row == 0)
			return row % outlineModulus == 0;
		if (col == 0)
			return col % outlineModulus == 0;
		if (row == surface.getNumRows()-1)
			return row % outlineModulus == 0;
		if (col == surface.getNumCols()-1)
			return col % outlineModulus == 0;
		
		// if we got here, it's not on the outline
		return row % internalModulus == 0 && col % internalModulus == 0;
	}
	
	private static boolean isCorner(EvenlyGriddedSurfaceAPI surface, int row, int col) {
		if (row == 0 || row == surface.getNumRows()-1)
			return col == 0 || col == surface.getNumCols()-1;
		return false;
	}

	@Override
	public double getCornerMidptFilterDist() {
		return cornerMidptDistFilter;
	}

}
