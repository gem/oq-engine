package org.opensha.commons.calc;

import org.opensha.commons.data.function.EvenlyDiscretizedFunc;

/**
 * This class provides a method for calculating a probability
 * mass function (PMF) from a probability of exceedance function (POE).
 * Both the two functions are assumed to be evenly discretized functions.
 * The class is declared final so that it can be made inline
 * and therefore be faster when executing. This can be important
 * because this class can be called many times when calculating PMFs
 * for many hazard curves.
 * @author damianomonelli
 *
 */

public final class ProbabilityMassFunctionCalc {
	
	public static EvenlyDiscretizedFunc getPMFfromPOE(EvenlyDiscretizedFunc poe){
		
		// PMF parameters
		// minimum value
		double minVal = (poe.getX(0)+poe.getX(1))/2;
		// maximum value
		double maxVal = (poe.getX(poe.getNum()-2) + poe.getX(poe.getNum()-1))/2;
		// number of values
		int numVal = poe.getNum() - 1;
		// PMF function
		EvenlyDiscretizedFunc pmf = new EvenlyDiscretizedFunc(minVal, maxVal, numVal);
		
		// calculate PMF values
		for(int i=0;i<poe.getNum()-1;i++){
			double val = poe.getY(i) - poe.getY(i+1);
			pmf.set(i, val);
		}
		
		return pmf;
	}

}
