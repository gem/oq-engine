package org.opensha.commons.calc;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.ListIterator;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
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
	 *            EvenlyDiscretizedFunc POE function
	 * @return EvenlyDiscretizedFunc PMF. PMF values refer to middle points of
	 *         POEs bins.
	 * @exception IllegalArgumentException
	 *                poe is null, poe contains less than 2 values (NOTE: In
	 *                theory the only situation we should avoid is
	 *                poe.getNum()==1 (because in this case the formula cannot
	 *                be applied). The case poe.getNum()==2 is avoided here
	 *                because the resulting PMF would have only one value, and
	 *                when an EvenlyDiscretizedFunc is defined with only one
	 *                value, than the delta parameter is overwritten in the
	 *                constructor and set to 0. This can cause some problems
	 *                later on, for instance when the PMF object is asked for
	 *                the delta value (for instance when saving the pmf in a XML
	 *                file). From the practical point of view this may not be a
	 *                big issue because we can expect that POE functions are
	 *                usually defined for more than 2 values), poe values are
	 *                not in the range [0,1], and poe values are not in
	 *                descending order.
	 */
	public static EvenlyDiscretizedFunc getPMFfromPOE(EvenlyDiscretizedFunc poe) {

		if (poe == null) {
			throw new IllegalArgumentException(
					"Probability of exceedence function cannot be null");
		}

		if (poe.getNum() <= 2) {
			throw new IllegalArgumentException(
					"Probability of exceedence function must contain more than two values");
		}

		if (poeValuesAreBetween0and1(poe) == false) {
			throw new IllegalArgumentException(
					"Probability of exceedence function values must be between 0 and 1");
		}

		if (poeValuesAreInDescendingOrder(poe) == false) {
			throw new IllegalArgumentException(
					"Probability of exceedence function values must be in descending order");
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

	/**
	 * This method calculate probability mass function (PMF) values from an
	 * arbitrarily discretized probability of exceedence (POE) function.
	 * 
	 * @param poe
	 *            ArbitrarilyDiscretizedFunc containing POE values
	 * @return ArbitrarilyDiscretizedFunc containing PMF values. PMF values
	 *         refer to the middle points of the POE bins.
	 * @exception IllegalArgumentException
	 *                poe is null, poe contains less than 2 values (NOTE: In
	 *                theory the only situation we should avoid is
	 *                poe.getNum()==1 (because in this case the formula cannot
	 *                be applied). The case poe.getNum()==2 is avoided here
	 *                because the resulting PMF would have only one value, and
	 *                when an EvenlyDiscretizedFunc is defined with only one
	 *                value, than the delta parameter is overwritten in the
	 *                constructor and set to 0. This can cause some problems
	 *                later on, for instance when the PMF object is asked for
	 *                the delta value (for instance when saving the pmf in a XML
	 *                file). From the practical point of view this may not be a
	 *                big issue because we can expect that POE functions are
	 *                usually defined for more than 2 values), poe values are
	 *                not in the range [0,1], and poe values are not in
	 *                descending order.
	 */
	public static ArbitrarilyDiscretizedFunc getPMFfromArbitrarilyDiscretizedPOE(
			ArbitrarilyDiscretizedFunc poe) {

		if (poe == null) {
			throw new IllegalArgumentException(
					"Probability of exceedence function cannot be null");
		}

		if (poe.getNum() <= 2) {
			throw new IllegalArgumentException(
					"Probability of exceedence function must contain more than two value");
		}
		
		if (poeValuesAreBetween0and1(poe) == false) {
			throw new IllegalArgumentException(
					"Probability of exceedence function values must be between 0 and 1");
		}

		if (poeValuesAreInDescendingOrder(poe) == false) {
			throw new IllegalArgumentException(
					"Probability of exceedence function values must be in descending order");
		}

		ArbitrarilyDiscretizedFunc pmf = new ArbitrarilyDiscretizedFunc();
		for (int i = 0; i < poe.getNum() - 1; i++) {
			double x1 = poe.getX(i);
			double x2 = poe.getX(i + 1);
			double xMean = (x1 + x2) / 2;
			double val = poe.getY(i) - poe.getY(i + 1);
			pmf.set(xMean, val);
		}
		return pmf;
	}

	/**
	 * This method checks if POE values are in descending order
	 * 
	 * @param poe
	 * @return
	 */
	private static Boolean poeValuesAreInDescendingOrder(DiscretizedFuncAPI poe) {
		Comparator comparator = Collections.reverseOrder();
		ArrayList<Double> val1 = new ArrayList<Double>();
		ArrayList<Double> val2 = new ArrayList<Double>();
		ListIterator<Double> valIter = poe.getYValuesIterator();
		int index = 0;
		while (valIter.hasNext()) {
			double val = valIter.next();
			val1.add(index, val);
			val2.add(index, val);
			index = index + 1;
		}
		// sort array in descending order
		Collections.sort(val1, comparator);
		// check if the sorted array is equal to the original array
		// if yes, this means that the original array is in descending order
		// (return true) otherwose return false.
		return Arrays.equals(val1.toArray(), val2.toArray());
	}

	/**
	 * This method checks that POE values are between 0 and 1
	 * 
	 * @param poe
	 * @return
	 */
	private static Boolean poeValuesAreBetween0and1(DiscretizedFuncAPI poe) {
		ListIterator<Double> valIter = poe.getYValuesIterator();
		while (valIter.hasNext()) {
			double val = valIter.next();
			if (val < 0 || val > 1)
				return false;
		}
		return true;
	}

}
