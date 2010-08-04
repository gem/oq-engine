package org.opensha.sha.gui.beans;

import java.util.ArrayList;

import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.util.TectonicRegionType;

public class MultiERFDummy extends EqkRupForecast {
	
	ArrayList<TectonicRegionType> regions;
	
	public MultiERFDummy() {
		regions = new ArrayList<TectonicRegionType>();
		regions.add(TectonicRegionType.ACTIVE_SHALLOW);
		regions.add(TectonicRegionType.STABLE_SHALLOW);
		regions.add(TectonicRegionType.SUBDUCTION_SLAB);
	}

	@Override
	public int getNumSources() {
		// TODO Auto-generated method stub
		return 0;
	}

	@Override
	public ProbEqkSource getSource(int iSource) {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public ArrayList getSourceList() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public String getName() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void updateForecast() {
		// TODO Auto-generated method stub
		
	}

	@Override
	public ArrayList<TectonicRegionType> getIncludedTectonicRegionTypes() {
		return regions;
	}

}

