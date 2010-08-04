package org.opensha.sra.riskmaps.func;

/**
 * This API defines the basic structure of a function. A function is a mapping
 * of values from a domain to a range where each value in the domain maps to at
 * most one value in the range. Due to double floating point precision errors, 
 * all comparisons should be done within a reasonable tolerance for the scope of
 * the implementing function.
 *
 *<pre>
 * -=* CHNAGE LOG *=-
 * 06/19/2008 -- EMM: Original implementation.
 *
 *</pre>
 *
 * @author  Eric Martinez
 * @version 0.0.1
 */
public interface FunctionAPI {

	/**
	 * Gets the name of this function. All functions can be named, but do not
	 * need to be so. If the name of the function is not specified,
	 * implementations of this function should return a default string. The
	 * return value should never be <code>null</code>.
	 *
	 * @return The name of this function.
	 */
	public String getName();

	/**
	 * Gets the domain of this function. The domain of a function is the set of
	 * values that map into the range of the function. This domain may be
	 * discrete or continuous.
	 *
	 * @return The domain of the function.
	 */
	public SetAPI getDomain();

	/**
	 * Gets the range of this function. The range of a function is the set of
	 * values that can be reached by providing a value in the functions range.
	 *
	 * @return The range of the function.
	 */
	public SetAPI getRange();

	/**
	 * Gets the value of the function at the point <code>x</code>. If the given
	 * <code>x</code> value is not in the domain for the function, then an
	 * <code>IllegalArgumentException</code> is thrown.
	 *
	 * @param x The input value of the function.
	 * @return The output (y-value) of the function.
	 * @throws IllegalArgumentException If the given input <code>x</code> value
	 * is not in the domain of the function.
	 */
	public double valueOf(double x) throws IllegalArgumentException;
}
