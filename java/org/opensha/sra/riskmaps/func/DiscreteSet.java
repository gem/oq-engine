package org.opensha.sra.riskmaps.func;

import java.util.Arrays;
import java.util.Vector;

/**
 * This class represents the mathematical idea of a discrete set. A discrete set
 * contains at most a finite number of values.
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
public class DiscreteSet implements SetAPI {
	
	/**
	 * This is the primitive structure used to store values in this set. The
	 * array will remain sorted for internal convenience.
	 */
	private double[] values;

	/**
	 * Creates a discrete set containing the values in the given
	 * <code>values</code> array.
	 *
	 * @param values An array of values to place in the discrete set.
	 */
	public DiscreteSet(double [] values) {
		this.values = values;
		Arrays.sort(this.values);
	}

	/**
	 * @return True of the given value <code>x</code> is in the set, false
	 * otherwise.
	 */
	public boolean contains(double x) {
		return (Arrays.binarySearch(values, x)>=0);
	}

	/**
	 * @return A set whose values are the union of the calling
	 * <code>DiscreteSet</code> and the passed <code>set</code>.
	 */
	public SetAPI unionWith(SetAPI set) {
		if (!(set instanceof DiscreteSet)) {
			IllegalArgumentException iax = new IllegalArgumentException(
					"Cannot union a discrete and non-discrete set."
				);
			iax.fillInStackTrace();
			throw iax;
		}

		double [] otherVals = ((DiscreteSet) set).toArray();
		// Create a Vector initially containing all of this sets values
		Vector<Double> unionSet = new Vector<Double>();
		for(int i = 0; i < values.length; ++i) {
			unionSet.add(new Double(values[i]));
		}

		// Add any new values from the "otherVals" array
		for(int i = 0; i < otherVals.length; ++i) {
			if((Arrays.binarySearch(values, otherVals[i])) < 0) {
				unionSet.add(new Double(otherVals[i]));
			}
		}

		// Convert to a primitive array
		double [] result = new double[unionSet.size()];
		for(int i = 0; i < result.length; ++i) {
			result[i] = unionSet.get(i).doubleValue();
		}

		return new DiscreteSet(result);
	}

	/**
	 * @return A set whose values are the intersection of the calling
	 * <code>DiscreteSet</code> and the passed <code>set</code>.
	 */
	public SetAPI intersectionOf(SetAPI set) {
		if (!(set instanceof DiscreteSet)) {
			IllegalArgumentException iax = new IllegalArgumentException(
					"Cannot intersect a discrete and non-discrete set"
				);
			iax.fillInStackTrace();
			throw iax;
		}
		double [] otherVals = ((DiscreteSet) set).toArray();
		// Create a Vector initially empty
		Vector<Double> intersect = new Vector<Double>();

		// Add any values that appear in both arrays.
		for(int i = 0; i < otherVals.length; ++i) {
			if((Arrays.binarySearch(values, otherVals[i])) >= 0) {
				intersect.add(otherVals[i]);
			}
		}

		// Convert to a primitive array
		double [] result = new double[intersect.size()];
		for(int i = 0; i < result.length; ++i) {
			result[i] = intersect.get(i);
		}
		return new DiscreteSet(result);
	}

	/**
	 * @return True if the primitive arrays of values are considrered equal,
	 * false otherwise.
	 */
	public boolean equals(SetAPI set) {	
		if(set instanceof DiscreteSet) {
			return this.equals((DiscreteSet) set);
		} else {
			return false;
		}
	}
		

	/**
	 * @return The greatest upper bound of this set, or NaN if the set contains
	 * no values. Note: A discrete set that contains no values is not considered
	 * the same as an empty set.
	 */
	public double lowerBound() {
		double d = Double.NaN;
		try {
			d = values[0];
		} catch (ArrayIndexOutOfBoundsException aix) {
			/* Ignore this error. */
		}
		return d;
	}

	/**
	 * @return The least upper bound of this set, or NaN if the set contains no
	 * values. Note: A discrete set that contains no values is not considered the
	 * same as an empty set.
	 */
	public double upperBound() {
		double d = Double.NaN;
		try {
			d = values[values.length-1];
		} catch (ArrayIndexOutOfBoundsException aix) {
			/* Ignore this error. */
		}
		return d;
	}

	/**
	 * @return The number of values in this set.
	 */
	public int size() {
		return values.length;
	}

	/**
	 * @return A primitive double array of the values in this set.
	 */
	public double[] toArray() {
		return values;
	}
}
