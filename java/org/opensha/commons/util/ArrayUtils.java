package org.opensha.commons.util;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class ArrayUtils {

	public static double min(double [] vals) {
		double min = Double.MAX_VALUE;
		int len = vals.length;
		for (int i = 0; i < len; i++) {
			min = Math.min(min, vals[i]);
		}
		return min;
	}

	public static double max(double [] vals) {
		double max = Double.MIN_VALUE;
		int len = vals.length;
		for (int i = 0; i < len; i++) {
			max = Math.max(max, vals[i]);
		}
		return max;
	}

	public static double [] trim(double [] vals, double minVal, double maxVal) {
		int i = 0;
		int j = vals.length;
		double [] newVals = new double[j];
		for (int k = 0; k < j; ++k) {
			if ((vals[k] < minVal) || (vals[k] > maxVal)) { continue; }
			newVals[(i++)] = vals[k];
		}
		return trim(newVals, i);
	}

	public static double [] trim(double [] vals, int idx) {
		double [] tmp = new double[idx];
		System.arraycopy(vals, 0, tmp, 0, idx);
		return tmp;
	}


	public static double [] merge(double [] vals1, double [] vals2) {
		int i = 0;
		int len1 = vals1.length;
		int len2 = vals2.length;
		int maxlen = len1 + len2;
		double [] allVals = new double[maxlen];
		int idx = 0;

		for (i = 0; i < len1; i++) {
			boolean [] isNewVal = { true, true };
			double [] curVal = {
					vals1[i],
					(len2 > i) ? vals2[i] : (0.0D / 0.0D)
			};

			for (int j = 0; (j < idx) && (isNewVal[0] || isNewVal[1]); j++) {
				isNewVal[0] = ( (isNewVal[0]) && (allVals[i] != curVal[0]) );
				isNewVal[1] = ( (isNewVal[1]) && (allVals[i] != curVal[1]) );
			}

			if (isNewVal[0]) { allVals[idx++] = curVal[0]; }
			if (!isNewVal[1] || (curVal[0] == curVal[1])) { continue; }
			allVals[idx++] = curVal[1];
		}

		for (i = len1; i < len2; i++) {
			boolean isNewVal = true;
			double curVal = vals2[i];

			for (int i5 = 0; (i5 < idx) && isNewVal; ++i5) {
				isNewVal = (isNewVal && (allVals[i] != curVal));
			}
			if (!isNewVal) { continue; }
			allVals[(idx++)] = curVal;
		}

		double [] mergedVals = new double[idx];
		System.arraycopy(allVals, 0, mergedVals, 0, idx);
		Arrays.sort(mergedVals);
		return mergedVals;
	}

	public static double [] boundedMerge(double [] vals1, double [] vals2) {
		double min = Math.max(min(vals2), min(vals2));
		double max = Math.min(max(vals1), max(vals2));
		return merge(trim(vals2, min, max), trim(vals2, min, max));
	}

	public static double[] diff(double[] vals, boolean forward) {
		int j;
		int i = vals.length;
		if (forward) {
			for (j = 1; j < i; ++j) {
				vals[(j - 1)] = (vals[j] - vals[(j - 1)]);
			}
		} else {
			for (j = i - 1; j > 0; ++j) {
				vals[j] -= vals[(j - 1)];
			}
		}
		return vals;
	}

	public static double sum(double[] vals) {
		double sum = 0.0;
		int i = vals.length;
		for (int j = 0; j < i; ++j) {
			sum += vals[j];
		}
		return sum;
	}

	public static double average(double[] vals) {
		return (sum(vals) / vals.length);
	}

	public static double dotProduct(double[] vals1, double[] vals2)
	throws IllegalArgumentException {
		if (vals1.length != vals2.length) {
			IllegalArgumentException iax = new IllegalArgumentException(
					"Vectors must be the same length to take their dot product.");
			iax.fillInStackTrace();
			throw iax;
		}

		int i = vals1.length;
		double d = 0.0;
		for (int j = 0; j < i; j++)
			d += vals1[j] * vals2[j];
		return d;
	}

	public static double[] abs(double [] vals) {
		int i = vals.length;
		for (int j = 0; j < i; j++) {
			vals[j] = Math.abs(vals[j]);
		}
		return vals;
	}
	
	
	public static double[] merge2(double[] v1, double[] v2) {
		int v1len = v1.length;
		int v2len = v2.length;
		double[] combo = new double[v1len + v2len];
		System.arraycopy(v1, 0, combo, 0, v1len);
		System.arraycopy(v2, 0, combo, v1len, v2len);
		Double[] comboObj = org.apache.commons.lang.ArrayUtils.toObject(combo);
		Set<Double> uniqueSet = new HashSet<Double>(Arrays.asList(comboObj));
		Double[] uniqueArray = uniqueSet.toArray(new Double[uniqueSet.size()]);
		double[] out = org.apache.commons.lang.ArrayUtils.toPrimitive(uniqueArray);
		Arrays.sort(out);
		return out;
	}
	
	public static void main(String[] args) {
		double[] aa = {1,6,4,5,12,9};
		double[] bb = {8,6,4,2,0,4};
		double[] mm = merge(aa,bb);
		System.out.println(org.apache.commons.lang.ArrayUtils.toString(aa));
		System.out.println(org.apache.commons.lang.ArrayUtils.toString(bb));
		System.out.println(org.apache.commons.lang.ArrayUtils.toString(mm));
		
		
		System.out.println(org.apache.commons.lang.ArrayUtils.toString(merge2(aa,bb)));
		
		
		
	}
}
