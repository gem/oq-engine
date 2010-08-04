/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data;

/**
 * This class saves the time dependent data (last event yr, Slip and aperiodicity) for each A-Fault segment
 * @author vipingupta
 *
 */
public class SegmentTimeDepData  implements java.io.Serializable {

	private String faultName;
	private int segIndex;
	private double lastEventCalendarYr  = Double.NaN;
	private double slip = Double.NaN;
	private double aperiodicity = Double.NaN;
	
	public void setAll(String faultName, int segIndex, double lastEventCalendarYr, double slip, double aperiodicity) {
		setFaultName(faultName);
		setSegIndex(segIndex);
		setLastEventCalendarYr(lastEventCalendarYr);
		this.setSlip(slip);
		this.setAperiodicity(aperiodicity);
	}
	
	// Getters & Setters
	public double getAperiodicity() {
		return aperiodicity;
	}
	public void setAperiodicity(double aperiodicity) {
		this.aperiodicity = aperiodicity;
	}
	public String getFaultName() {
		return faultName;
	}
	public void setFaultName(String faultName) {
		this.faultName = faultName;
	}
	public double getLastEventCalendarYr() {
		return lastEventCalendarYr;
	}
	public void setLastEventCalendarYr(double lastEventCalendarYr) {
		this.lastEventCalendarYr = lastEventCalendarYr;
	}
	public int getSegIndex() {
		return segIndex;
	}
	public void setSegIndex(int segIndex) {
		this.segIndex = segIndex;
	}
	public double getSlip() {
		return slip;
	}
	public void setSlip(double slip) {
		this.slip = slip;
	}
	
}
