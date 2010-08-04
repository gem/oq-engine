package org.opensha.sra.riskmaps.func;

/**
 * This interface defines the mathematical concept of a Set. Sets can be
 * continuous or discrete and are defined in a number of ways. Since a Set can
 * take on many forms, no real structure of a Set is defined here, however this
 * does provide an API for actions that can be done on a Set.
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
public interface SetAPI {

	/**
	 * Checks if a given value <code>x</code> exists in this set. Due to double
	 * floating point precision errors, all comparisons should take place within
	 * a reasonable tolerance for the specific set. This tolerance is left up to
	 * the implementation to determine.
	 *
	 * @param x The value to check for.
	 * @return True if the value exists in the set, false otherwise.
	 */
	public boolean contains(double x);

	/**
	 * Creates and returns a set whose values are a composite single-copy of any
	 * value appearing in one or both of the calling <code>SetAPI</code> and the
	 * passed <code>set</code>.
	 *
	 * @return A composite <code>SetAPI</code> as specified above.
	 */
	public SetAPI unionWith(SetAPI set);

	/**
	 * Creates and returns a set whose values are a composite single-copy of any
	 * value appearing in both of the calling <code>SetAPI</code> and the passed 
	 * <code>set</code>.
	 *
	 * @return A composite <code>SetAPI</code> as specified above.
	 */
	public SetAPI intersectionOf(SetAPI set);

	/**
	 * Checks whether the calling <code>SetAPI</code> and the passed
	 * <code>set</code> are logically equal.
	 *
	 * @return True if the sets are logically equal, false otherwise.
	 */
	public boolean equals(SetAPI set);

	/**
	 * @return The greatest lower bound of this set. That is, the smallest number
	 * that is still in this set.
	 */
	public double lowerBound();

	/**
	 * @return The least upper bound of this set. That is, the largest number
	 * that is still in this set.
	 */
	public double upperBound();
}
