package org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData;

import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
@Deprecated
public class GEMGridSourceData extends GEMSourceData{
	public final static String TYPE = "G";
	private Location epicenter;
	private IncrementalMagFreqDist mfd;
	private double dip;
	private double rake;
	private double strike;
	
	// default constructor
	public GEMGridSourceData(){
		
	}

	public Location getEpicenter() {
		return epicenter;
	}

	public void setEpicenter(Location epicenter) {
		this.epicenter = epicenter;
	}

	public IncrementalMagFreqDist getMfd() {
		return mfd;
	}

	public void setMfd(IncrementalMagFreqDist mfd) {
		this.mfd = mfd;
	}

	public double getDip() {
		return dip;
	}

	public void setDip(double dip) {
		this.dip = dip;
	}

	public double getRake() {
		return rake;
	}

	public void setRake(double rake) {
		this.rake = rake;
	}

	public double getStrike() {
		return strike;
	}

	public void setStrike(double strike) {
		this.strike = strike;
	}
	

}
