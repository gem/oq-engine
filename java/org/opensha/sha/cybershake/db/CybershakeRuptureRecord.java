package org.opensha.sha.cybershake.db;

public class CybershakeRuptureRecord {
	
	private int sourceID;
	private int rupID;
	private double mag;
	private double prob;
	
	public CybershakeRuptureRecord(int sourceID, int rupID, double mag, double prob) {
		this.sourceID = sourceID;
		this.rupID = rupID;
		this.mag = mag;
		this.prob = prob;
	}

	public int getSourceID() {
		return sourceID;
	}

	public void setSourceID(int sourceID) {
		this.sourceID = sourceID;
	}

	public int getRupID() {
		return rupID;
	}

	public void setRupID(int rupID) {
		this.rupID = rupID;
	}

	public double getMag() {
		return mag;
	}

	public void setMag(double mag) {
		this.mag = mag;
	}

	public double getProb() {
		return prob;
	}

	public void setProb(double prob) {
		this.prob = prob;
	}

	@Override
	public String toString() {
		return "sourceID: " + sourceID + " rupID: " + rupID + " mag: " + mag + " prob: " + prob;
	}

}
