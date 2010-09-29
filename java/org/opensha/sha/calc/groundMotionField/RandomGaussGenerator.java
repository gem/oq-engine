package org.opensha.sha.calc.groundMotionField;

public class RandomGaussGenerator {
	
	private double rnd;
	
	/**
	 * 
	 */
	public RandomGaussGenerator() {
		
	}

	/**
	 * Gaussian random number generation based on the Box-Muller transform
	 * (see Thomas, D.B. et al. (2007). Gaussian Random Number Generator. 
	 * ACM Computing Surveys, 39(4), Article 11. 
	 * To get the final value (given mean and std):
	 * 		mean + std * rndGau.boxMullerTransform();
	 * 	
	 * @return 
	 */
	public double boxMullerTransform() {
		double a = Math.sqrt(-2*Math.log(Math.random())); 
		double b = 2*3.1415*Math.random();
		double val = a * Math.sin(b);
		return val;
	}

	public double getValue() {
		return this.rnd;
	}
}
