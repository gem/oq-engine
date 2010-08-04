package org.opensha.sha.earthquake;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.ListIterator;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.util.TectonicRegionType;

public class ERFTestSubset implements EqkRupForecastAPI {
	
	HashMap<Integer, Integer> sourceIDMap = new HashMap<Integer, Integer>();
	
	private EqkRupForecast baseERF;
	
	public ERFTestSubset(EqkRupForecast baseERF) {
		this.baseERF = baseERF;
	}

	@Override
	public ParameterList getAdjustableParameterList() {
		return baseERF.getAdjustableParameterList();
	}

	@Override
	public ListIterator<ParameterAPI> getAdjustableParamsIterator() {
		return baseERF.getAdjustableParamsIterator();
	}

	@Override
	public Region getApplicableRegion() {
		return baseERF.getApplicableRegion();
	}

	@Override
	public ArrayList<TectonicRegionType> getIncludedTectonicRegionTypes() {
		return baseERF.getIncludedTectonicRegionTypes();
	}

	@Override
	public String getName() {
		return baseERF.getName() + "_TEST";
	}

	@Override
	public TimeSpan getTimeSpan() {
		return baseERF.getTimeSpan();
	}

	@Override
	public boolean isLocWithinApplicableRegion(Location loc) {
		return baseERF.isLocWithinApplicableRegion(loc);
	}

	@Override
	public boolean setParameter(String name, Object value) {
		return baseERF.setParameter(name, value);
	}

	@Override
	public void setTimeSpan(TimeSpan time) {
		baseERF.setTimeSpan(time);
	}

	@Override
	public String updateAndSaveForecast() {
		return baseERF.updateAndSaveForecast();
	}

	@Override
	public void updateForecast() {
		baseERF.updateForecast();
	}

	@Override
	public ArrayList<EqkRupture> drawRandomEventSet() {
		throw new RuntimeException("WARNING: drawRandomEventSet not implemented for test ERF!");
	}

	@Override
	public int getNumRuptures(int iSource) {
		// TODO Auto-generated method stub
		return baseERF.getNumRuptures(getBaseSourceID(iSource));
	}

	@Override
	public int getNumSources() {
		return sourceIDMap.size();
	}

	@Override
	public ProbEqkRupture getRupture(int iSource, int nRupture) {
		return baseERF.getRupture(getBaseSourceID(iSource), nRupture);
	}

	@Override
	public ProbEqkSource getSource(int iSource) {
		return baseERF.getSource(getBaseSourceID(iSource));
	}
	
	private int getBaseSourceID(int sourceID) {
		return sourceIDMap.get(new Integer(sourceID));
	}

	@Override
	public ArrayList getSourceList() {
		ArrayList<ProbEqkSource> sources = new ArrayList<ProbEqkSource>();
		for (int i=0; i<getNumSources(); i++) {
			sources.add(getSource(i));
		}
		return sources;
	}
	
	public void includeSource(int sourceID) {
		if (sourceIDMap.containsKey(new Integer(sourceID)))
			return; // it's already included
		if (sourceID < 0 || sourceID >= baseERF.getNumSources())
			throw new IndexOutOfBoundsException("source ID to include is out of bounds!");
		int newID = this.getNumSources();
		sourceIDMap.put(new Integer(newID), new Integer(sourceID));
	}
	
	public ProbEqkSource getOrigSource(int sourceID) {
		return baseERF.getSource(sourceID);
	}

}
