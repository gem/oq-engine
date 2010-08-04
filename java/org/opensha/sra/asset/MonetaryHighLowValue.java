package org.opensha.sra.asset;

public class MonetaryHighLowValue extends MonetaryValue {
	
	private double highValue;
	private double lowValue;
	
	public MonetaryHighLowValue(double value, double highValue, double lowValue, int valueBasisYear) {
		super(value, valueBasisYear);
		this.highValue = highValue;
		this.lowValue = lowValue;
	}

	public double getHighValue() {
		return highValue;
	}

	public void setHighValue(double highValue) {
		this.highValue = highValue;
	}

	public double getLowValue() {
		return lowValue;
	}

	public void setLowValue(double lowValue) {
		this.lowValue = lowValue;
	}

}
