package org.opensha.commons.calc;

import static org.junit.Assert.assertEquals;

import org.junit.Test;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;

public class TestProbabilityMassFunctionCalc {
	
	// tolerance
	double tolerance = 1e-6;
	
	// contructor
	public TestProbabilityMassFunctionCalc(){		
	}
	
	@Test
	public void testProbabilityMassFunctionCalcWithGaussianDistribution(){
		
		/**
		 * This test compares the PMF for a Gaussian distribution
		 * (mean zero, standard deviation one)
		 * calculated using the method GaussianDistCalc.getExceedProb
		 * using the formula PMF((I1+I2)/2) = POE(I1) - POE(I2) with
		 * the PMF obtained using the method ProbabilityMassFunctionCalc.getPMFfromPOE
		 * and passing as input a POE for a Gaussian distribution
		 * obtained with the same method GaussianDistCalc.getExceedProb
		 */
		
		// define probability of exceedance function
		double minX = -9.0;
		double maxX = 9.0;
		int numVal = 19;
		EvenlyDiscretizedFunc poe = new EvenlyDiscretizedFunc(minX, maxX, numVal);
		// define probability of exceedance values using a Gaussian distribution function
	    for(int i=0;i<poe.getNum();i++){
	    	double valX = poe.getX(i);
	    	poe.set(i, GaussianDistCalc.getExceedProb(valX));
	    }
	    
	    // compute probability mass function
	    EvenlyDiscretizedFunc pmf = ProbabilityMassFunctionCalc.getPMFfromPOE(poe);
	    
	    // compare probability mass function values with values computed explicitly
	    // using the getExceedProb method
	    for(int i=0;i<pmf.getNum();i++){
	    	double delta = pmf.getDelta();
	    	double x = pmf.getX(i);
	    	double y1 = pmf.getY(i);
	    	double y2 = GaussianDistCalc.getExceedProb(x-delta/2) - GaussianDistCalc.getExceedProb(x+delta/2);
			assertEquals(y1,y2,tolerance);
	    }
		
	}

}
