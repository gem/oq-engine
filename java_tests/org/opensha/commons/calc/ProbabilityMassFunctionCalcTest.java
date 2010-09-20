package org.opensha.commons.calc;

import static org.junit.Assert.assertEquals;

import org.junit.Test;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;

public class ProbabilityMassFunctionCalcTest {
	
	// tolerance
	double tolerance = 1e-6;
	
	@Test
	public void probabilityMassFunctionCalcWithGaussianDistribution(){
		
		/**
		 * This test compares the PMF for a Gaussian distribution
		 * (mean zero, standard deviation one)
		 * explicitly calculated using the method GaussianDistCalc.getExceedProb
		 * and the formula PMF((I1+I2)/2) = POE(I1) - POE(I2) with
		 * the PMF obtained by using the method ProbabilityMassFunctionCalc.getPMFfromPOE
		 * and passing as input a POE for a Gaussian distribution
		 * obtained with the same method GaussianDistCalc.getExceedProb
		 */
		
		// POE parameters
		double minX = -9.0;
		double maxX = 9.0;
		int numVal = 19;
		
		// get POE for Gaussian distribution
		// using the GaussianDistCalc.getExceedProb method
		EvenlyDiscretizedFunc poe = getGaussianPOE(minX, maxX, numVal);
	    // get PMF using the getPMFfromPOE method
	    EvenlyDiscretizedFunc pmf1 = ProbabilityMassFunctionCalc.getPMFfromPOE(poe);
	    
	    // compute PMF directly from 
	    // the GaussianDistCalc.getExceedProb method
	    // the PMF values are calculated for the bins' middle points.
	    // that's why the minimum is shifted by half delta 
	    // and the number of values is reduced by a factor of 1
		double delta = (maxX-minX)/(numVal-1);
	    EvenlyDiscretizedFunc pmf2 = getGaussianPMF(minX+delta/2, numVal-1, delta);
	    
	    // compare the 2 pmfs
	    comparePMFs(pmf1, pmf2);
	}
	
	@Test
	public void probabilityMassFunctionCalcWith2ValuesPOE(){
		
		/**
		 * This test checks the behaviour of the getPMFfromPOE method
		 * when a POE with only 2 values is passed (using the same strategy
		 * of the probabilityMassFunctionCalcWithGaussianDistribution test)
		 */
		
		// POE parameters
		double minX = -1.0;
		double maxX = 1.0;
		int numVal = 2;
		
		// calculate POE values for Gaussian distribution
		EvenlyDiscretizedFunc poe = getGaussianPOE(minX, maxX, numVal);
	    // compute PMF using the getPMFfromPOE method
	    EvenlyDiscretizedFunc pmf1 = ProbabilityMassFunctionCalc.getPMFfromPOE(poe);
	    
	    // compute PMF directly from 
	    // the GaussianDistCalc.getExceedProb method
	    // the PMF values are calculated for the bins' middle points.
	    // that's why the minimum is shifted by half delta
		double delta = (maxX-minX)/(numVal-1);
	    EvenlyDiscretizedFunc pmf2 = getGaussianPMF(minX+delta/2, numVal-1, delta);
	    
	    // compare the 2 pmfs
	    comparePMFs(pmf1, pmf2);
	}
	
	@Test(expected=IllegalArgumentException.class)
	public void probabilityMassFunctionCalcWith1ValuePOE(){
		
		/**
		 * This test check the behaviour of the getPMFfromPOE method
		 * when a POE function with only one values is passed
		 */
		EvenlyDiscretizedFunc poe = new EvenlyDiscretizedFunc(0.0, 0.0, 1);
		EvenlyDiscretizedFunc pmf = ProbabilityMassFunctionCalc.getPMFfromPOE(poe);
		
	}
	
	@Test(expected=IllegalArgumentException.class)
	public void probabilityMassFunctionCalcWithNullPOE(){
		
		/**
		 * This test check the behaviour of the getPMFfromPOE method
		 * when a null poe is passed
		 */
		EvenlyDiscretizedFunc pmf = ProbabilityMassFunctionCalc.getPMFfromPOE(null);
		
	}
	
	/**
	 * Get probability of exceedence (poe) values for a Gaussian distribution
	 * (mean=0,std=1) using the method GaussianDistCalc.getExceedProb
	 * @param minX: minimum value for which computing the poe
	 * @param maxX: maximum value for which computing the poe
	 * @param numVal: number of values for which computing the poe (together with minX and maxX 
	 * controls the spacing)
	 * @return: probability of exceedence values in a EvenlyDiscretizerFunc object 
	 */
	private EvenlyDiscretizedFunc getGaussianPOE(double minX, double maxX, int numVal){
		EvenlyDiscretizedFunc poe = new EvenlyDiscretizedFunc(minX, maxX, numVal);
		for(int i=0;i<numVal;i++){
			double valX = poe.getX(i);
			poe.set(i, GaussianDistCalc.getExceedProb(valX));
		}
		return poe;
	}
	
	/**
	 *  Get probability mass function (PMF) values for a Gaussian distribution
	 *  (mean=0,std=1) using the GaussianDistCalc.getExceedProb method
	 *  and using the formula PMF((I1+I2)/2) = POE(I1) - POE(I2) 
	 * @param minX: minimum (bin's middle point) value for which calculating the PMF
	 * @param numVal: number of values for which computing the PMF
	 * @param delta: binwidth associated to each PMF value 
	 * @return: probability mass function values in a EvenlyDiscretized object
	 */
	private EvenlyDiscretizedFunc getGaussianPMF(double minX, int numVal, double delta){
		EvenlyDiscretizedFunc pmf = new EvenlyDiscretizedFunc(minX, numVal, delta);
		for(int i=0;i<numVal;i++){
			double x1 = pmf.getX(i)-delta/2;
			double x2 = pmf.getX(i)+delta/2;
			double val = GaussianDistCalc.getExceedProb(x1) - 
	    	GaussianDistCalc.getExceedProb(x2);
			pmf.set(i, val);
		}
		return pmf;
	}
	
	/**
	 * Compare probability mass functions
	 * @param pmf1
	 * @param pmf2
	 */
	private void comparePMFs(EvenlyDiscretizedFunc pmf1, EvenlyDiscretizedFunc pmf2){
		int numVal1 = pmf1.getNum();
		int numVal2 = pmf2.getNum();
		assertEquals(numVal1, numVal2, 0.0);
	    for(int i=0;i<numVal1;i++){
	    	double x1 = pmf1.getX(i);
	    	double x2 = pmf2.getX(i);
	    	assertEquals(x1, x2, tolerance);
	    	double y1 = pmf1.getY(i);
	    	double y2 = pmf2.getY(i);
	    	assertEquals(y1,y2,tolerance);
	    }	
	}
}
