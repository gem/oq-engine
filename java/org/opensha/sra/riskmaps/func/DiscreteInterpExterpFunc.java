package org.opensha.sra.riskmaps.func;

import gov.usgs.util.MathUtils;

import java.util.Arrays;

import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

/**
 * This class behaves much like the <code>DiscreteFunction</code> class, however
 * it allows for values between the discrete domain values to be interpolated,
 * and values outside the domain altogether to be extrapolated. This
 * interpolation/extrapolation can be done in different arithmetic spaces to
 * allow for a &ldquo;best fit&rdquo; regression curve. Extrapolation follows
 * one of four different approaches for each side of the curve. See the
 * predefined constants for a list of options and their meanings.
 *
 *<pre>
 * -=* CHANGE LOG *=-
 * 07/07/08 -- EMM: Original implementation.
 *
 *</pre>
 *
 * @author  Eric Martinez
 * @version 0.0.1
 */
public class DiscreteInterpExterpFunc extends DiscreteFunction {
	
	/** Identifies interpolation in linear-x, linear-y domains. */
	public static final int LINEAR_LINEAR = 0;
	/** Identifies interpolation in linear-x, logarithmic-y domains. */
	public static final int LINEAR_LOG    = 1;
	/** Identifies interpolation in logarithmic-x, linear-y domains. */
	public static final int LOG_LINEAR    = 2;
	/** Identifies interpolation in logarithmic-x, logarithmic-y domains. */
	public static final int LOG_LOG       = 3;

	/** Extrapolation should just drop values to zero. */
	public static final int EXTRAP_ZERO     = 0;
	/** Extrapolation should assume the constant value of the endpoint. */
	public static final int EXTRAP_FLATTEN  = 1;
	/** Extrapolation should continue a linear regression of the final points. */
	public static final int EXTRAP_EXTEND   = 2;
	/** Extrapolation should jump to +/- infinity (slope dependent). */
	public static final int EXTRAP_INFINITY = 3;

	/** The default name of this type of function. */
	private static final String DEFAULT_NAME = 
			"Interpolated/Extrapolated Discrete Function";

	/* Default interpolation/extrapolation schemes. */
	protected int interpType  = LINEAR_LINEAR;
	protected int extrapBelow = EXTRAP_EXTEND;
	protected int extrapAbove = EXTRAP_EXTEND;

	/**
	 * Creates a discrete function with interpolation and extrapolation methods
	 * based on the given <code>xvals</code> and <code>yvals</code>. The name of
	 * this function will be the default name, and the interpolation and
	 * extrapoltion methods will be the defaults as well.
	 *
	 * @param xvals The x-values of this discrete function.
	 * @param yvals The y-values of this descrete function.
	 */
	public DiscreteInterpExterpFunc(double [] xvals, double [] yvals) {
		super(xvals, yvals, DEFAULT_NAME);
	}

	/**
	 * Creates a discrete function with interpolation and extrapolation methods
	 * based on the given <code>xvals</code>, <code>yvals</code> and
	 * <code>name</code>. The interpolation and extrapolation methods will be the
	 * defaults.
	 *
	 * @param xvals The x-values of this discrete function.
	 * @param yvals The y-values of this discrete function.
	 * @param name  The name of this discrete function.
	 */
	public DiscreteInterpExterpFunc(double [] xvals, double [] yvals,
			String name) {
		super(xvals, yvals, name);
	}

	/**
	 * Creates a discrete function with interpolation and extrapolation methods
	 * based on the given <code>xvals</code>, <code>yvals</code> and
	 * <code>name</code>. Assuming the <code>interpType</code>,
	 * <code>extrapBelow</code> and/or <code>extrapAbove</code> correspond to a
	 * well-known method, they will be used as the respective
	 * interpolation/extrapolation methods. Otherwise the defaults will be used.
	 *
	 * @param xvals The x-values of this discrete function.
	 * @param yvals The y-values of this discrete function.
	 * @param name  The name of this discrete function.
	 * @param interpType  The arithmetic space in which to interpolate.
	 * @param extrapBelow The method of extrapolation for values below the lower
	 * bound of the function domain.
	 * @param extrapAbove The method of extrapolation for the values above the
	 * upper bound of the function domain.
	 */
	public DiscreteInterpExterpFunc(double [] xvals, double [] yvals,
			String name, int interpType, int extrapBelow, int extrapAbove) {
		super(xvals, yvals, name);
		if (LINEAR_LINEAR <= interpType && interpType <= LOG_LOG) {
			this.interpType = interpType;
		}
		if (EXTRAP_ZERO <= extrapBelow && extrapBelow <= EXTRAP_INFINITY) {
			this.extrapBelow = extrapBelow;
		}
		if (EXTRAP_ZERO <= extrapAbove && extrapAbove <= EXTRAP_INFINITY) {
			this.extrapAbove = extrapAbove;
		}
	}

	/**
	 * Attempts to set the interpolataion method used for this discrete function.
	 * If the given <code>interpType</code> does not correspond to a known
	 * interpolation type, then nothing is done.
	 *
	 * @param interpType The new interpolation type to use.
	 */
	public void setInterpMethod(int interpType) {
		if (LINEAR_LINEAR <= interpType && interpType <= LOG_LOG) {
			this.interpType = interpType;
		}
	}
		
	/**
	 * Attempts to set the extrapolation methods used for this discrete function.
	 * If the given <code>extrapBelow</code> or <code>extrapAbove</code> does not
	 * correspond to a known extrapolation method, then the respective value is
	 * not set.
	 *
	 * @param extrapBelow The extrapolation method used for values below the
	 * lower bound of the domain of this discrete function.
	 * @param extrapAbove The extrapolation method used for values above the
	 * upper bound of the domain of this discrete function.
	 */
	public void setExtrapMethod(int extrapAbove, int extrapBelow) {
		if (EXTRAP_ZERO <= extrapBelow && extrapBelow <= EXTRAP_INFINITY) {
			this.extrapBelow = extrapBelow;
		}
		if (EXTRAP_ZERO <= extrapAbove && extrapAbove <= EXTRAP_INFINITY) {
			this.extrapAbove = extrapAbove;
		}
	}

	/**
	 * @return The current interpolation scheme used for this function.
	 */
	public int getInterp() { return interpType; }
	/**
	 * @return The current extrapolation method used for values below the lower
	 * bound of the domain of this function.
	 */
	public int getExtrapBelow() { return extrapBelow; }
	/**
	 * @return The current extrapolation method used for values above the upper
	 * bound of the domain of this function.
	 */
	public int getExtrapAbove() { return extrapAbove; }

	/**
	 * For the given value <code>x</code> returns the function value
	 * <code>f(x)</code> for this function. If <code>x</code> is one of the
	 * discrete defining values of this function, its corresponding discrete
	 * y-value is returned. If <code>x</code> is somehwere within the bounds of
	 * the domain of this discrete function, then an interpolation is performed
	 * according to the current interpolation type and that interpolated value is
	 * returned. If <code>x</code> is above or below the upper or lower bounds of
	 * this discrete function's domain (respectively), then the funcntion value
	 * of <code>x</code> is extrapolated according to the current extrapolation
	 * method for values above/below the domain (respectively).
	 *
	 * @param x The value for which we want to know <code>f(x)</code>.
	 * @return The function value <code>f(x)</code>, interpolated or extrapolated
	 * as needed.
	 */
	public double valueOf(double x) {
		DiscreteSet domain = (DiscreteSet) getDomain();
		if (domain.contains(x)) {
			return super.valueOf(x);
		} else if (x < domain.lowerBound()) {
			return extrapolate(xvals[1], xvals[0], yvals[1], yvals[0], x,
					extrapBelow);
		} else if (x > domain.upperBound()) {
			return extrapolate(xvals[xvals.length-2], xvals[xvals.length-1],
					yvals[yvals.length-2], yvals[yvals.length-1], x, extrapAbove);
		} else if (domain.lowerBound() <= x && x <= domain.upperBound()) {
			// X should be bounded below and above by the array, so there *should*
			// be two bounding values. 0 < idx < xvals.length - 1
			int idx = (-1 * (Arrays.binarySearch(xvals, x) + 1)) - 1;
			return interpolate(xvals[idx], xvals[idx+1], yvals[idx], yvals[idx+1],
					x);
		} else {
			return Double.NaN;
		}
	}

	/**
	 * For the given array of <code>x</code> values, a corresponding array of
	 * <code>f(x)</code> values is created and returned according to the
	 * computation methods described in <code>valueOf(double x)</code>.
	 *
	 * @param x The array of x-values for which you want to know y-values.
	 * @return An array of function values for the input array of <code>x</code>.
	 */
	public double [] valueOf(double [] x) {
		double [] y = new double[x.length];
		for (int i = 0; i < x.length; ++i) {
			y[i] = valueOf(x[i]);
		}
		return y;
	}



	/**
	 * Interpolates the <code>x</code> value between <code>x1</code> and
	 * <code>x2</code> with corresponding <code>y1</code> and <code>y2</code> and
	 * returns the interpolated result <code>y</code> such that <code>f(x) =
	 * y</code>. Interpolation is performed according to the current
	 * <code>interpType</code> of this function. If the current
	 * <code>interpType</code> is not valid, then an
	 * <code>IllegalStateException</code> is thrown.
	 *
	 * @param x1 A bounding x-value for the desired <code>x</code>.
	 * @param x2 A bounding x-value for the desired <code>x</code>
	 * @param y1 A function value <code>f(x1) = y1</code> for <code>x1</code>.
	 * @param y2 A function value <code>f(x2) = y2</code> for <code>y2</code>.
	 * @param x The desired input value to be interpolated.
	 * @return The interpolated value <code>y</code> such that <code>f(x) ~
	 * y</code> where &ldquo;~&rdquo; means &ldquo;equals&rdquo; up to
	 * interpolation errors.
	 */
	private double interpolate(double x1, double x2, double y1, double y2, 
			double x) {
		if (interpType == LINEAR_LINEAR) {
			return MathUtils.linearInterp(x1, x2, y1, y2, x);
		} else if (interpType == LINEAR_LOG) {
			return Math.exp(MathUtils.linearInterp(x1, x2, Math.log(y1),
					Math.log(y2), x
				));
		} else if (interpType == LOG_LINEAR) {
			return MathUtils.linearInterp(Math.log(x1), Math.log(x2), y1, y2,
					Math.log(x)
				);
		} else if (interpType == LOG_LOG) {
			return Math.exp(MathUtils.linearInterp(Math.log(x1), Math.log(x2),
					Math.log(y1), Math.log(y2), Math.log(x)
				));
		}
		IllegalStateException isx = new IllegalStateException(
				"Unknown interpolation method: " + interpType
			);
		isx.fillInStackTrace(); throw isx;
	}

	/**
	 * Attempts to extrapolate the function value for <code>x</code> (<code>f(x)
	 * = y</code>) given the points <code>(x1, y1), (x2, y2)</code> that form a
	 * linear regression line in the current </code>interpType</code> space. If
	 * the current <code>interpType</code> or the given <code>extrapTye</code>
	 * are not a well-known type, than an <code>IllegalStateException</code> is
	 * thrown.
	 *
	 * @param x1 The x-value of the first point of the known regression line.
	 * @param x2 The x-value of the second point of the known regression line.
	 * @param y1 The y-value of the first pont of the known regression line.
	 * @param y2 The y-value of the second point of the known regression line.
	 * @param x  The desired x-value for which we want a y-value such that
	 * <code>f(x) ~ y</code> where &ldquo;~&rdquo; is &ldqou;equals&rdquo; up to
	 * extrapolation precision errors.
	 * @param extrapType The type of extrapolation to follow.
	 * @return The function value (as extrapolated) at the point <code>x</code>.
	 * @throws IllegalStateException If the current <code>interpType</code> or
	 * given <code>extrapType</code> are not well-defined.
	 */
	private double extrapolate(double x1, double x2, double y1, double y2,
			double x, int extrapType) {
		if (extrapType == EXTRAP_ZERO) {
			return 0.0;
		} else if (extrapType == EXTRAP_FLATTEN) {
			if (x < getDomain().lowerBound()) {
				return yvals[0];
			} else {
				return yvals[yvals.length-1];
			}
		} else if (extrapType == EXTRAP_EXTEND) {
			if (interpType == LINEAR_LINEAR) {
				return MathUtils.linearExtrap(x1, x2, y1, y2, x);
			} else if (interpType == LOG_LINEAR) {
				return MathUtils.linearExtrap(Math.log(x1), Math.log(x2), y1, y2,
						Math.log(x));
			} else if (interpType == LINEAR_LOG) {
				return Math.exp(MathUtils.linearExtrap(x1, x2, Math.log(y1),
						Math.log(y2), x)
					);
			} else if (interpType == LOG_LOG) {
				return Math.exp(MathUtils.linearExtrap(Math.log(x1), Math.log(x2),
						Math.log(y1), Math.log(y2), Math.log(x))
					);
			}
		} else if (extrapType == EXTRAP_INFINITY) {
			if (interpType == LOG_LINEAR || interpType == LOG_LOG) {
				x1 = Math.log(x1); x2 = Math.log(x2);
			}
			if(interpType == LINEAR_LOG || interpType == LOG_LOG) {
				y1 = Math.log(y1); y2 = Math.log(y2);
			}
			double slope = ( (y2 - y1) / (x2 - x1) );
			if (slope < 0.0) {
				return Double.NEGATIVE_INFINITY;
			} else if (slope > 0.0) {
				return Double.POSITIVE_INFINITY;
			} else {
				//  slope === 0.0
				return extrapolate(x1, x2, y1, y2, x, EXTRAP_FLATTEN);
			}
		}
		IllegalStateException isx = new IllegalStateException(
				"Unknown extrapolation method: " + extrapType
			);
		isx.fillInStackTrace(); throw isx;
	}
	
	public static DiscreteInterpExterpFunc fromArbDistFunc(ArbitrarilyDiscretizedFunc func) {
		int size = func.getNum();
		double xVals[] = new double[size];
		double yVals[] = new double[size];
		
		for (int i=0; i<size; i++) {
			DataPoint2D pt = func.get(i);
			xVals[i] = pt.getX();
			yVals[i] = pt.getY();
		}
		
		return new DiscreteInterpExterpFunc(xVals, yVals);
	}
}
