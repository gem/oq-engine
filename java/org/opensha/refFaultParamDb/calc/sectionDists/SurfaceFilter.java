package org.opensha.refFaultParamDb.calc.sectionDists;

import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

public interface SurfaceFilter {
	
	public double getCornerMidptFilterDist();
	
	public boolean isIncluded(EvenlyGriddedSurfaceAPI surface, int row, int col);

}
