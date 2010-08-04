package org.opensha.sra.riskmaps.func;

/**
 * This class represents the mathematical idea of an empty set. Empty sets
 * contain no values. The union of a set with the empty set is simply the
 * original set itself, and the intersection of a set with the empty set is
 * again an empty set. Empty sets are neither discrete nor continuous.
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
public class EmptySet implements SetAPI {

	/**
	 * Checks if the given value <code>x</code> exists within this set. Since
	 * this set is empty, the function always returns <code>false</code>.
	 *
	 * @param x The value to check for.
	 * @return False, this set is always empty.
	 */
	public boolean contains(double x) {
		return false;
	}

	/**
	 * Takes the union of the given <code>set</code> with the calling object.
	 * Since this set is empty, the given <code>set</code> is always returned.
	 *
	 * @param set The set to union with this set.
	 * @return A set with the same values as the passed <code>set</code>, namely,
	 * the passed <code>set</code> itself.
	 */
	public SetAPI unionWith(SetAPI set) {
		return set;
	}

	/**
	 * Takes the intersection of the given <code>set</code> with the calling
	 * object. Since this set is empty, the empty set is always returned.
	 *
	 * @param set The set to intersect with this set.
	 * @return An empty set, namely the calling set.
	 */
	public SetAPI intersectionOf(SetAPI set) {
		return this;
	}

	/**
	 * Checks if the calling <code>SetAPI</code> and the given <code>set</code>
	 * are logically equal.
	 *
	 * @return True if both sets are empty sets, false otherwise. Note that a
	 * continuous or discrete set containing no values is not considered an empty
	 * set.
	 */
	public boolean equals(SetAPI set) {
		if(set instanceof EmptySet) {
			return true;
		} else {
			return false;
		}
	}

	/**
	 * @return Not a number (NaN), this set is empty.
	 */
	public double lowerBound() {
		return Double.NaN;
	}

	/**
	 * @return Not a number (NaN), this set is empty.
	 */
	public double upperBound() {
		return Double.NaN;
	}
}
