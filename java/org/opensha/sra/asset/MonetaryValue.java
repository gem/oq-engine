package org.opensha.sra.asset;

/**
 * Add comments here
 *
 * 
 * @author Peter Powers
 * @version $Id:$
 */
public class MonetaryValue implements Value {
	
	public MonetaryValue(double value, int valueBasisYear) {
		this.value = value;
		this.valueBasisYear = valueBasisYear;
	}

	
	// TODO get mean, 4th and 96th %ile
	
	private int valueBasisYear;
	private double value;
	
	public String getCurrencyCode() {
		return null;
	}
	
	@Override
	public int getValueBasisYear() {
		return valueBasisYear;
	}
	
	public double getValue() {
		return value;
	}
	
	
	
	
	
	
}
