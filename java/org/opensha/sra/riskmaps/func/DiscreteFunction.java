package org.opensha.sra.riskmaps.func;

import java.util.Arrays;

import gov.usgs.util.AssociativeSorter;

/**
 * This class represents the mathematical idea of a discrete function. Discrete
 * functions have discrete domains and ranges. They are eseentially a pairing of
 * x/y values. Once a function is instantiated, that instance become immutable.
 *
 *<pre>
 * -=* CHANGE LOG *=-
 * 06/19/2008 -- EMM: Original implementation.
 *
 *</pre>
 *
 * @author  Eric Martinez
 * @version 0.0.1
 */
public class DiscreteFunction implements FunctionAPI {

	/** The x-values of this function */
	protected double [] xvals;
	/** The y-values of this function */
	protected double [] yvals;
	/** The name of this function */
	private String name;
	/** The default name of discrete functions if not specified. */
	private static final String DEFAULT_NAME = "Discrete Function";

	/**
	 * Creates a discrete function with the given <code>xvals</code>,
	 * <code>yvals</code>, and the <code>DEFAULT_NAME</code>.
	 *
	 * @param xvals The x-values of the function.
	 * @param yvals The y-values of the function.
	 */
	public DiscreteFunction(double [] xvals, double [] yvals) {
		this(xvals, yvals, DEFAULT_NAME);
	}

	/**
	 * Creates a discrete function with the given <code>xvals</code>,
	 * <code>yvals</code>, and <code>name</code>.
	 *
	 * @param xvals The x-values of the function.
	 * @param yvals The y-values of the function.
	 * @param name  The name of the function.
	 */
	public DiscreteFunction(double [] xvals, double [] yvals, String name) {
		// We need to make sure that the xvals are properly sorted. We can't use
		// the built-in Arrays.sort because  we need to know which values were
		// changed so the same changes can be made to the yvals.

		// Sort by xvals and re-order yvals to match.
		AssociativeSorter.sort(xvals, yvals);

		this.xvals = xvals;
		this.yvals = yvals;
		this.name  = name;

	}

	/**
	 * Gets the domain of this function. The domain is the set of unique
	 * x-values. In practice, this is exactly the set of x-values since the
	 * domain is defined to map each value exactly once. Thus this method may be
	 * used interchangeably with the <code>getXVals()</code> function.
	 *
	 * @return The domain of this function.
	 */
	public SetAPI getDomain() {
		return new DiscreteSet(xvals);
	}

	/**
	 * Gets the range of this function. The range is the set of unique  y-values.
	 * In practice this set may contain fewer values than the raw set of y-values
	 * since two values in the range are allowed to map to the same y-value.
	 * Thus, that y-value would appear twice in our array of y-values, but would
	 * appear only once in the range. Use <code>getYVals()</code> to get the raw
	 * array of y-values.
	 *
	 * @return The range of the function.
	 */
	public SetAPI getRange() {
		return new DiscreteSet(yvals);
	}

	/**
	 * Gets the name of this function.
	 *
	 * @return The name of this function.
	 */
	public String getName() {
		return name;
	}

	/**
	 * Gets the function value for the given <code>x</code> input.
	 *
	 * @param x The value of which to take f(x).
	 * @return The function value for this function evaluated at <code>x</code>.
	 * @throws IllegalArgumentException If x is not in the domain of the
	 * function.
	 */
	public double valueOf(double x) {
		try {
			int idx = Arrays.binarySearch(xvals, x);
			return yvals[idx];
		} catch (ArrayIndexOutOfBoundsException abx) {
			IllegalArgumentException iax = new IllegalArgumentException(
					"The value " + x + " was not in the domain of the function."
				);
			iax.fillInStackTrace();
			throw iax;
		}
	}

	/**
	 * Gets the raw xvals array of data.
	 *
	 * @return The primitive array of doubles representing the discrete x-values.
	 */
	public double [] getXVals() {
		return xvals;
	}

	/**
	 * Gets the raw yvals array of data.
	 *
	 * @return The primitive array of doubles representing the discrete y-values.
	 */
	public double [] getYVals() {
		return yvals;
	}

	/**
	 * Checks the domain and range of the two functions are the same, and the for
	 * each value <code>i</code> in the domain of the functions, <code>f(i) =
	 * g(i)</code>.
	 *
	 * @param func The function to compare agaist.
	 * @return True if the two functions are logically equal, false otherwise.
	 */
	public boolean equals(Object obj) {
		if (obj instanceof DiscreteFunction) {
			DiscreteFunction func = (DiscreteFunction)obj;
			double [] otherX = func.getXVals();
			double [] otherY = func.getYVals();

			for (int i = 0; i < xvals.length; ++i) {
				try {
					if (xvals[i] != otherX[i] || yvals[i] != otherY[i]) {return false;}
				} catch (ArrayIndexOutOfBoundsException abx) {
					return false;
				}
			}
			return true;
		}
		return false;
	}

	public String toString() {
		String s = name + "\n";
		s += Arrays.toString(xvals) + "\n";
		s += Arrays.toString(yvals) + "\n";
		return s;
	}
}
