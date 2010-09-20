package org.opensha.commons.calc;

import org.opensha.commons.data.function.EvenlyDiscretizedFunc;

/**
 * This class provide methods for calculating a probability mass function (PMF)
 * from a probability of exceedance function (POE). The class is declared final
 * so that it can be made inline and therefore be faster when executing. This
 * can be important because this class can be called many times when calculating
 * PMFs for many hazard curves.
 * 
 * @author damianomonelli
 * 
 */

public final class ProbabilityMassFunctionCalc {

	/**
	 * This method compute a PMF from a POE function assuming both to be evenly
	 * discretized.
	 * 
	 * @param poe
	 *            POE function
	 * @return a PMF as an EvenlyDiscretizedFunc object. PMF values refer to 
	 * middle points of POEs bins.
	 */
	public static EvenlyDiscretizedFunc getPMFfromPOE(EvenlyDiscretizedFunc poe) {

		if (poe == null) {
			throw new IllegalArgumentException(
					"Probability of exceedence function cannot be null");
		}

		if (poe.getNum() == 1) {
			throw new IllegalArgumentException(
					"Probability of exceedence function must contain more than one value");
		}

		// PMF parameters (as derived from the POE function)
		// bin width (given that the POE is evenly spaced, also the PMF will be
		// evenly spaced with the same bin width)
		double binWidth = poe.getDelta();
		// number of values (PMF values refer to bins' middle points,
		// so the number of values in the PMF is equal to
		// the number of values in the POE but decreased by 1)
		int numVal = poe.getNum() - 1;
		// minimum value (it corresponds to
		// the the middle point of the first bin)
		double minVal = poe.getX(0) + binWidth / 2;

		// PMF function
		EvenlyDiscretizedFunc pmf = new EvenlyDiscretizedFunc(minVal, numVal,
				binWidth);

		// calculate PMF values
		for (int i = 0; i < numVal; i++) {
			double val = poe.getY(i) - poe.getY(i + 1);
			pmf.set(i, val);
		}

		return pmf;

	}

}
