/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.calc;

//  The following is needed only by getCDF_Alt() which is commented out below.
// import edu.uah.math.psol.distributions.*;

// The following are needed only for the tests
import java.text.DecimalFormat;

import org.opensha.commons.data.function.EvenlyDiscretizedFunc;


/**
 * <b>Title:</b> GaussianDistCalc.java <p>
 * <b>Description:</p>This utility calculates the probability of exceedance
 * assuming a gaussian distribution.  The object
 * edu.uah.math.psol.distributions.NormalDistribution is not used
 * here because it was found to be ~3 times slower (see the getCDF_Alt()
 * method commented out).
  <p>
 *
 * @author Edward Field
 * @created    aug 22, 2002
 * @version 1.0
 */

public final class GaussianDistCalc {

	// if using edu.uah.math.psol.distributions package:
	//   static NormalDistribution gauss = new NormalDistribution( 0.0, 1.0 );

	// if computing pdf here (not using above)
	static double d1= 0.0498673470;
	static double d2=0.0211410061;
	static double d3=0.0032776263;
	static double d4=0.0000380036;
	static double d5=0.0000488906;
	static double d6=0.0000053830;

	/*
	 * This function calculates the Gaussian exceedance probability for the standardized
	 * random variable assuming no truncation of the distribution.
	 */
	public static double getExceedProb(double standRandVariable) {
		return 1.0 - getCDF(standRandVariable);
	}



	/**
	 * This function calculates the exceedance probability for a truncated Gaussian
	 * distribution.
	 *
	 * @param standRandVariable
	 * @param truncType  set 0 for none, 1 for upper only, and 2 for two sided
	 * @param truncLevel in units of SRV (must be positive, and can't = 0.0 for truncType = 2)
	 * @return the exceedance probability
	 */
	public static double getExceedProb(double standRandVariable, int truncType, double truncLevel) {


		// check that truncLevel is an allowed value
		if(truncType == 2) {
			if(truncLevel <= 0.0)
				throw new RuntimeException("GaussianDistCalc.getExceedProb(): truncLevel must be greater than zero for truncType=2");
		}
		else {
			if(truncLevel < 0.0)
				throw new RuntimeException("GaussianDistCalc.getExceedProb(): truncLevel cannot be negative");
		}

		double prob = getCDF( standRandVariable );

		// compute probability based on truncation type
		if (  truncType == 1 ) {  // upper truncation
			if ( standRandVariable > truncLevel )
				return  0.0;
			else {
				double pUp = getCDF( truncLevel );
				return  (1.0 - prob/pUp) ;
			}
		}
		else if ( truncType == 2 ) {  // the two sided case
			if ( standRandVariable > truncLevel )
				return (0.0);
			else if ( standRandVariable < -truncLevel )
				return (1.0);
			else {
				double pUp = getCDF( truncLevel );
				double pLow = getCDF( -truncLevel );
				return ( (pUp-prob)/(pUp-pLow) );
			}
		}
		else if (truncType == 0)
			return (1.0 - prob );  // no truncation
		else
			throw new RuntimeException("GaussianDistCalc.getExceedProb(): truncType must be 0, 1, or 2");
	}


	/**
	 * This function calculates the exceedance probability for a truncated Gaussian
	 * distribution. The distribution is non-symmetrically truncated on both sides
	 *
	 * @param standRandVariable
	 * @param lowerTruncLevel in units of SRV
	 * @param upperTruncLevel in units of SRV
	 * @return the exceedance probability
	 */
	public static double getExceedProb(double standRandVariable, double lowerTruncLevel, double upperTruncLevel) {
		if(lowerTruncLevel >= upperTruncLevel)
			throw new RuntimeException("GaussianDistCalc.getExceedProb(): lowerTruncLevel should be less than upperTruncLevel");

		double prob = getCDF(standRandVariable);
		if (standRandVariable > upperTruncLevel)
			return (0.0);
		else if (standRandVariable < lowerTruncLevel)
			return (1.0);
		else {
			double pUp = getCDF(upperTruncLevel);
			double pLow = getCDF( lowerTruncLevel);
			return ( (pUp - prob) / (pUp - pLow));
		}
	}


	/**
	 * This function calculates the cumulative density function for a Gaussian
	 * distribution (the area under the curve up to standRandVariable).  This
	 * algorithm comes from Norm Abrahamson, who says he got it from a book by
	 * Abramowitz and Stegun. <br><br>
	 *
	 * Comparing the probabilities computed with this method between
	 * +/- 7.5 SRVs with those computed using Excel gives a difference of 0.3 % at
	 * SRV=-4, and grows to 364 % (a factor of 3.64) at SRV=-7.5.  The difference
	 * is negligible for all positive CRVs (up to at least 7.5).  Norm Abrahamson
	 * says this is good enough for seismic hazard calculations.
	 *
	 */
	public static double getCDF(double standRandVariable) {

		double val;
		double result;
		val = Math.abs(standRandVariable);
		result = 0.5 * Math.pow( (((((d6*val+d5)*val+d4)*val+d3)*val+d2)*val+d1)*val+1, -16);
		if(standRandVariable < 0) return result;
		else                      return 1.0-result;
	}


	/**
	 * This returns the standardized random variable (SRV) associated with the
	 * given exceedance probability.  The tolerance specifies the accuracy of the
	 * result such that:<br><br>
	 *
	 * <i>(prob_target-getExceedProb(SRV_found,trTyp, trLev))/prob_target < tolerance</i><br><br>
	 *
	 * There is another potential ambiguity in that there may be a wide range
	 * of SRVs that satisfy the above.  For example, if the target probability is 1e-5,
	 * and the tolerance is 1e-3, then all SRVs greater than 4.26 satisfy
	 * the above.  We solve this ambiguity by giving the first occurrence (generally
	 * the value closest to zero).  Specifically, if the target probability is less
	 * than 0.5, we find an SRV such that the probability for (SRV_found-tolerance) <i>does
	 * not</i> satisfy the above condition (is not within tolerance of the target
	 * probability).  For target probabilities greater than 0.5 we give the SRV such that
	 * the probability for (SRV_found+toloerance) will not be within tolerance of the
	 * target probability.<br><br>
	 *
	 * The cases where exceedProb = 0.0 or 1.0 are treated explicity (e.g.,
	 * Double.POSITIVE_INFINITY or Double.NEGATIVE_INFINITY are returned
	 * if no truncation is applied).<br><br>
	 *
	 * Note that the result is not necessarily symmetric in that getStandRandVar(prob,*) may
	 * not exactly equal the negative of getStandRandVar((1-prob),*).  This simply represents
	 * the lack of numerical precision under some conditions, with the problem worsening for
	 * greater tolerances and as the input probability approaches zero or one.  For example,<br><br>
	 *
	 * getStandRandVar(0.0001,0,2,1e-6) =  3.72<br>
	 * getStandRandVar(0.9999,0,2,1e-6) = -3.72<br><br>
	 *
	 * getStandRandVar(0.000001,0,2,1e-6) =  4.76<br>
	 * getStandRandVar(0.999999,0,2,1e-6) = -4.62
	 *
	 * This could simply call the other getStandRandVar method, but we're leaving this 
	 * here because it's more efficient with untruncated cases (although this may not be significant)
	 *
	 * @param exceedProb  The target exceedance probability
	 * @param truncType   The truncation type
	 * @param truncLevel  The truncation level (num SRVs)
	 * @param tolerance   The tolerance
	 * @return  The SRV found for the target exceedProb
	 */
	public static double getStandRandVar(double exceedProb, int truncType, double truncLevel, double tolerance) {

		float delta = 1;
		double testNum = 100;
		double oldNum = 0;
		double prob = 100;

		// check that tolerance is within the allowed range
		if(tolerance < 1e-6 || tolerance > 0.1)
			throw new RuntimeException("GaussianDistCalc.getStandRandVar(): tolerance is not within the allowed range");

		if( exceedProb <= 0.5 && exceedProb > 0.0 ) {

			oldNum = -3;    // less than zero in case one sided with trunc-level=0
			do {
				testNum = oldNum;
				do {
					testNum += delta;
					prob = getExceedProb(testNum, truncType, truncLevel);

					//                                System.out.println("testNum="+testNum+",  prob="+prob+", test:  "+ (prob-exceedProb-tolerance*exceedProb));
				}
				while ( prob >= (exceedProb+tolerance*exceedProb) );
				oldNum = testNum - delta;
				delta /= 10;
				//                        System.out.println("new OldNum="+oldNum+"; new delta="+delta+"; test:  "+(testNum-oldNum-tolerance));
			}
			while (testNum-oldNum > tolerance);
			//                System.out.println("final testNum (returned) = "+ testNum+"; oldNum: "+oldNum);
			return testNum;
		}
		else if ( exceedProb > 0.5 && exceedProb < 1.0 ) {

			oldNum=1;
			do {
				testNum = oldNum;
				do {
					testNum -= delta;
					prob = getExceedProb(testNum, truncType, truncLevel);
				}
				while (prob <= (exceedProb-tolerance*exceedProb) );
				oldNum = testNum  + delta;
				delta /= 10;
			}
			while ( oldNum-testNum > tolerance);
			return testNum;
		}
		else if (exceedProb == 0.0) {
			if (truncType == 0)
				return Double.POSITIVE_INFINITY;
			else
				return truncLevel;
		}
		else if (exceedProb == 1.0) {
			if (truncType != 2)
				return Double.NEGATIVE_INFINITY;
			else
				return -truncLevel;
		}
		else
			throw new RuntimeException("invalid exceed probability (prob="+exceedProb+")");
	}


	/**
	 * This returns the standardized random variable (SRV) associated with the
	 * given exceedance probability.  The tolerance specifies the accuracy of the
	 * result such that:<br><br>
	 *
	 * <i>(prob_target-getExceedProb(SRV_found,trTyp, trLev))/prob_target < tolerance</i><br><br>
	 *
	 * There is another potential ambiguity in that there may be a wide range
	 * of SRVs that satisfy the above.  For example, if the target probability is 1e-5,
	 * and the tolerance is 1e-3, then all SRVs greater than 4.26 satisfy
	 * the above.  We solve this ambiguity by giving the first occurrence (generally
	 * the value closest to zero).  Specifically, if the target probability is less
	 * than 0.5, we find an SRV such that the probability for (SRV_found-tolerance) <i>does
	 * not</i> satisfy the above condition (is not within tolerance of the target
	 * probability).  For target probabilities greater than 0.5 we give the SRV such that
	 * the probability for (SRV_found+toloerance) will not be within tolerance of the
	 * target probability.<br><br>
	 *
	 * The cases where exceedProb = 0.0 or 1.0 are treated explicity (e.g.,
	 * Double.POSITIVE_INFINITY or Double.NEGATIVE_INFINITY are returned
	 * if no truncation is applied).<br><br>
	 *
	 * Note that the result is not necessarily symmetric in that getStandRandVar(prob,*) may
	 * not exactly equal the negative of getStandRandVar((1-prob),*).  This simply represents
	 * the lack of numerical precision under some conditions, with the problem worsening for
	 * greater tolerances and as the input probability approaches zero or one.  For example,<br><br>
	 *
	 * getStandRandVar(0.0001,0,2,1e-6) =  3.72<br>
	 * getStandRandVar(0.9999,0,2,1e-6) = -3.72<br><br>
	 *
	 * getStandRandVar(0.000001,0,2,1e-6) =  4.76<br>
	 * getStandRandVar(0.999999,0,2,1e-6) = -4.62
	 *
	 *
	 * @param exceedProb  The target exceedance probability
	 * @param lowerTruncLevel   The lower truncation level must be � 0
	 * @param upperTruncLevel  The upper truncation level must be � 0
	 * @param tolerance   The tolerance
	 * @return  The SRV found for the target exceedProb
	 */
	public static double getStandRandVar(double exceedProb, double lowerTruncLevel, double upperTruncLevel, double tolerance) {

		if(lowerTruncLevel >= 0 )
			throw new RuntimeException("GaussianDistCalc.getStandRandVar(): lowerTruncLevel should be < 0");
		if(upperTruncLevel < 0 )
			throw new RuntimeException("GaussianDistCalc.getStandRandVar(): upperTruncLevel should be � 0");


		float delta = 1;
		double testNum = 100;
		double oldNum = 0;
		double prob = 100;

		// check that tolerance is within the allowed range
		if(tolerance < 1e-6 || tolerance > 0.1)
			throw new RuntimeException("GaussianDistCalc.getStandRandVar(): tolerance is not within the allowed range");

		if( exceedProb <= 0.5 && exceedProb > 0.0 ) {

			oldNum = -3;    // less than zero in case one sided with trunc-level=0
			do {
				testNum = oldNum;
				do {
					testNum += delta;
					prob = getExceedProb(testNum, lowerTruncLevel, upperTruncLevel);

					//                                System.out.println("testNum="+testNum+",  prob="+prob+", test:  "+ (prob-exceedProb-tolerance*exceedProb));
				}
				while ( prob >= (exceedProb+tolerance*exceedProb) );
				oldNum = testNum - delta;
				delta /= 10;
				//                        System.out.println("new OldNum="+oldNum+"; new delta="+delta+"; test:  "+(testNum-oldNum-tolerance));
			}
			while (testNum-oldNum > tolerance);
			//                System.out.println("final testNum (returned) = "+ testNum+"; oldNum: "+oldNum);
			return testNum;
		}
		else if ( exceedProb > 0.5 && exceedProb < 1.0 ) {

			oldNum=1;
			do {
				testNum = oldNum;
				do {
					testNum -= delta;
					prob = getExceedProb(testNum, lowerTruncLevel, upperTruncLevel);
				}
				while (prob <= (exceedProb-tolerance*exceedProb) );
				oldNum = testNum  + delta;
				delta /= 10;
			}
			while ( oldNum-testNum > tolerance);
			return testNum;
		}
		else if (exceedProb == 0.0)  return upperTruncLevel;
		else if (exceedProb == 1.0) return lowerTruncLevel;
		else throw new RuntimeException("invalid exceed probability (prob="+exceedProb+")");
	}


	/**
	 * This method tests the getStandRandVar() method over a wide range of input
	 * probabilities for a given tolerance, truncation type, and truncation
	 * value (the range of probabilites tested are those computed from getExceedProb()
	 * for SRV from -7.5 to 7.5). Specifically, if <br><br>
	 *
	 * <i>SRV_found = getStandRandVar(Prob_target, trTyp, trLev, tol)</i><br><br>
	 *
	 * and<br><br>
	 *
	 * <i>Prob_implied = getExceedProb(SRV_found, trTyp, trLev)</i><br><br>
	 *
	 * this makes sure that <br><br>
	 *
	 * <i>abs(Prob_target-Prob_implied) < tol*Prob_target</i><br><br>
	 *
	 * This also ensures that the probability for SRV_found+tol (or SRV_found-tol)
	 * is more than tolerance from Prob_target (the above test fails; to make
	 * sure whe have the SRV closest to zero, since some SRV's farther from zero
	 * will satisfy the first test as well.
	 *
	 * @param tol    tolerance
	 * @param trTyp  truncation type
	 * @param trLev  truncation level
	 * @return boolean (true if all tests successful)
	 */
	public static boolean test1_getStandRandVar(double tol, int trTyp, double trLev) {

		double p, n1, n2, p2, p3, val_incr=0.1;

		boolean testA, testB;

		boolean success = true;

		DecimalFormat df2 = new DecimalFormat("#.0000");

		for (double val=-7.5; val <= 7.5; val += val_incr) {

			n1 = (double)((int)(val*10))/10.0;                    // rounding to nice value
			p = getExceedProb(n1,trTyp,trLev);   // rounding to float precision
			n2 = getStandRandVar(p,trTyp,trLev,tol);
			p2 = getExceedProb(n2,trTyp,trLev);

			// TestA: make sure probability is within tolerance of the original
			if(p != 0)
				testA = (Math.abs((p-p2)/p) < tol);
			else  // if p=0.0, avoid dividing by zero and make sure p2 is zero also
				testA = (p2 == 0);

			// TestB: now make sure that we've found the SRV closest to zero that satisfies testA
			// (that is, make sure prob for SRV+tol (or SRV-tol) is not within tol of the target prob)
			if(p>0.5) {
				p3 = getExceedProb(n2+tol,trTyp,trLev);
				testB = (((p-p3)/p) > tol);
			}
			else {
				p3 = getExceedProb(n2-tol,trTyp,trLev);
				testB = (((p3-p)/p) > tol);
			}

			// override testB if p=1.0 & trTyp=2 because the test is irrelevant
			// (and fails).
			if (p == 1.0 && trTyp == 2) {
				testB = true;
			}

			if(!testA || !testB) {
				success = false;
				System.out.println("n1="+n1+";  p="+p+";  n2="+n2+";  p2="+p2+";  p3="+p3+";  testA="+testA+";  testB="+testB);
			}
		}

		System.out.println("Success="+ success+" with tol="+tol+" trTyp="+trTyp+ " & trLev="+trLev);

		return success;

	}

	/**
	 * This runs test1_getStandRandVar() over a range of tolerances, truncation
	 * types, and trucation levels.
	 */
	public static void test2_getStandRandVar() {

		GaussianDistCalc.test1_getStandRandVar(1e-1,0,2);

		GaussianDistCalc.test1_getStandRandVar(1e-1,1,0.0);
		GaussianDistCalc.test1_getStandRandVar(1e-1,1,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-1,1,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-1,1,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-1,1,3.5);

		GaussianDistCalc.test1_getStandRandVar(1e-1,2,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-1,2,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-1,2,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-1,2,3.5);


		GaussianDistCalc.test1_getStandRandVar(1e-2,0,2);

		GaussianDistCalc.test1_getStandRandVar(1e-2,1,0.0);
		GaussianDistCalc.test1_getStandRandVar(1e-2,1,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-2,1,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-2,1,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-2,1,3.5);

		GaussianDistCalc.test1_getStandRandVar(1e-2,2,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-2,2,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-2,2,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-2,2,3.5);


		GaussianDistCalc.test1_getStandRandVar(1e-3,0,2);

		GaussianDistCalc.test1_getStandRandVar(1e-3,1,0.0);
		GaussianDistCalc.test1_getStandRandVar(1e-3,1,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-3,1,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-3,1,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-3,1,3.5);

		GaussianDistCalc.test1_getStandRandVar(1e-3,2,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-3,2,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-3,2,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-3,2,3.5);


		GaussianDistCalc.test1_getStandRandVar(1e-4,0,2);

		GaussianDistCalc.test1_getStandRandVar(1e-4,1,0.0);
		GaussianDistCalc.test1_getStandRandVar(1e-4,1,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-4,1,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-4,1,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-4,1,3.5);

		GaussianDistCalc.test1_getStandRandVar(1e-4,2,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-4,2,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-4,2,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-4,2,3.5);


		GaussianDistCalc.test1_getStandRandVar(1e-5,0,2);

		GaussianDistCalc.test1_getStandRandVar(1e-5,1,0.0);
		GaussianDistCalc.test1_getStandRandVar(1e-5,1,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-5,1,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-5,1,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-5,1,3.5);

		GaussianDistCalc.test1_getStandRandVar(1e-5,2,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-5,2,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-5,2,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-5,2,3.5);


		GaussianDistCalc.test1_getStandRandVar(1e-6,0,2);

		GaussianDistCalc.test1_getStandRandVar(1e-6,1,0.0);
		GaussianDistCalc.test1_getStandRandVar(1e-6,1,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-6,1,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-6,1,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-6,1,3.5);

		GaussianDistCalc.test1_getStandRandVar(1e-6,2,0.5);
		GaussianDistCalc.test1_getStandRandVar(1e-6,2,1.5);
		GaussianDistCalc.test1_getStandRandVar(1e-6,2,2.5);
		GaussianDistCalc.test1_getStandRandVar(1e-6,2,3.5);

		/* some of the following fail so we're making 1e-6 the smallest tolerance allowed

      GaussianDistCalc.test1_getStandRandVar(1e-7,0,2);

      GaussianDistCalc.test1_getStandRandVar(1e-7,1,0.0);
      GaussianDistCalc.test1_getStandRandVar(1e-7,1,0.5);
      GaussianDistCalc.test1_getStandRandVar(1e-7,1,1.5);
      GaussianDistCalc.test1_getStandRandVar(1e-7,1,2.5);
      GaussianDistCalc.test1_getStandRandVar(1e-7,1,3.5);

      GaussianDistCalc.test1_getStandRandVar(1e-7,2,0.5);
      GaussianDistCalc.test1_getStandRandVar(1e-7,2,1.5);
      GaussianDistCalc.test1_getStandRandVar(1e-7,2,2.5);
      GaussianDistCalc.test1_getStandRandVar(1e-7,2,3.5);


      GaussianDistCalc.test1_getStandRandVar(1e-8,0,2);

      GaussianDistCalc.test1_getStandRandVar(1e-8,1,0.0);
      GaussianDistCalc.test1_getStandRandVar(1e-8,1,0.5);
      GaussianDistCalc.test1_getStandRandVar(1e-8,1,1.5);
      GaussianDistCalc.test1_getStandRandVar(1e-8,1,2.5);
      GaussianDistCalc.test1_getStandRandVar(1e-8,1,3.5);

      GaussianDistCalc.test1_getStandRandVar(1e-8,2,0.5);
      GaussianDistCalc.test1_getStandRandVar(1e-8,2,1.5);
      GaussianDistCalc.test1_getStandRandVar(1e-8,2,2.5);
      GaussianDistCalc.test1_getStandRandVar(1e-8,2,3.5);


      GaussianDistCalc.test1_getStandRandVar(1e-9,0,2);

      GaussianDistCalc.test1_getStandRandVar(1e-9,1,0.0);
      GaussianDistCalc.test1_getStandRandVar(1e-9,1,0.5);
      GaussianDistCalc.test1_getStandRandVar(1e-9,1,1.5);
      GaussianDistCalc.test1_getStandRandVar(1e-9,1,2.5);
      GaussianDistCalc.test1_getStandRandVar(1e-9,1,3.5);

      GaussianDistCalc.test1_getStandRandVar(1e-9,2,0.5);
      GaussianDistCalc.test1_getStandRandVar(1e-9,2,1.5);
      GaussianDistCalc.test1_getStandRandVar(1e-9,2,2.5);
      GaussianDistCalc.test1_getStandRandVar(1e-9,2,3.5);
		 */
	}


	/**
	 * This tests the influence of tolerance on performance.  Tolerances of
	 * 0.1 and 1e-3 take about the same amount of time; tolerance of 1e-6 takes
	 * a little less than twice as long.
	 */
	public static void testSpeed_getStandRandVar() {

		System.out.println("starting tol=1e-1");
		for(int i=0;i<1e5;++i)
			getStandRandVar(0.2,0,2.0,1e-1);
		System.out.println("done");

		System.out.println("starting tol=1e-2");
		for(int i=0;i<1e5;++i)
			getStandRandVar(0.2,0,2.0,1e-2);
		System.out.println("done");

		System.out.println("starting tol=1e-3");
		for(int i=0;i<1e5;++i)
			getStandRandVar(0.2,0,2.0,1e-3);
		System.out.println("done");

		System.out.println("starting tol=1e-4");
		for(int i=0;i<1e5;++i)
			getStandRandVar(0.2,0,2.0,1e-4);
		System.out.println("done");

		System.out.println("starting tol=1e-5");
		for(int i=0;i<1e5;++i)
			getStandRandVar(0.2,0,2.0,1e-5);
		System.out.println("done");

		System.out.println("starting tol=1e-6");
		for(int i=0;i<1e5;++i)
			getStandRandVar(0.2,0,2.0,1e-6);
		System.out.println("done");

	}


	/**
	 *
	 */
	public static void test_symmetry_getStandRandVar() {

		DecimalFormat df2 = new DecimalFormat("#.00");
		for(double prob =1e-1; prob >=1e-7; prob /=10) {
			for (double t=1e-1; t >=1e-6; t /=10) {
				System.out.println("getStandRandVar("+(float)(prob)+",0,2,"+(float)t+") = "+ df2.format(getStandRandVar(prob,0,2,t)) );
				System.out.println("getStandRandVar("+(float)(1-prob)+",0,2,"+(float)t+") = "+ df2.format(getStandRandVar(1-prob,0,2,t)) );
			}
			System.out.println("  ");
		}

	}


	/**
	 *  main method for running tests
	 */
	public static void main(String args[]) {

		System.out.println(getCDF(Double.NEGATIVE_INFINITY));
		System.out.println(getCDF(Double.POSITIVE_INFINITY));
		//
		//     test_getCDF();
		//     test_symmetry_getStandRandVar();
		//     testSpeed_getStandRandVar();
		//     test2_getStandRandVar() ;
	}



	/*  THE FOLLOWING 3 METHODS WERE USED TO TEST THE USE OF THE gauss OBJECT of
       edu.uah.math.psol.distributions

    /**
	 * This tests the speed of getCDF() vs getCDF_Alt(); the latter is about
	 * three times slower.
     /
    public static void testSeed_getCDF_vs_getCDFAlt() {

        System.out.println("Starting getCDF()");
        for(int i = 1; i < 500000; i++ )
            getCDF(0.5);
        System.out.println("Done with getCDF()");

        System.out.println("Starting getCDF_Alt()");
        for( int i = 1; i < 500000; i++ )
            getCDF_Alt(0.5);
        System.out.println("Done with getCDF_Alt()");
    }


    /**
	 * This compares the rusults of getCDF_Alt between +/- 7.5 SRVs with those
	 * computed using Excel.  The difference is less than 6.4% at SRV=-7.5, and
	 * less everywhere else.  Although this shows getCDF_Alt() to be more accurate
	 * than getCDF(), the latter is about three times faster according to the test3
	 * method below.
     /
    public static void test_getCDF_Alt() {

      // first put Excel results into a faunction
      EvenlyDiscretizedFunc func = new EvenlyDiscretizedFunc(-7.5,151,0.1);
      func.setTolerance(0.00001);

      func.set( -7.500 ,  0.00000000000003 );
      func.set( -7.400 ,  0.00000000000007 );
      func.set( -7.300 ,  0.00000000000014 );
      func.set( -7.200 ,  0.00000000000030 );
      func.set( -7.100 ,  0.00000000000063 );
      func.set( -7.000 ,  0.00000000000129 );
      func.set( -6.900 ,  0.00000000000262 );
      func.set( -6.800 ,  0.00000000000526 );
      func.set( -6.700 ,  0.00000000001048 );
      func.set( -6.600 ,  0.00000000002067 );
      func.set( -6.500 ,  0.00000000004036 );
      func.set( -6.400 ,  0.00000000007805 );
      func.set( -6.300 ,  0.00000000014947 );
      func.set( -6.200 ,  0.00000000028347 );
      func.set( -6.100 ,  0.00000000053238 );
      func.set( -6.000 ,  0.00000000099012 );
      func.set( -5.900 ,  0.00000000182358 );
      func.set( -5.800 ,  0.00000000332605 );
      func.set( -5.700 ,  0.00000000600765 );
      func.set( -5.600 ,  0.00000001074622 );
      func.set( -5.500 ,  0.00000001903640 );
      func.set( -5.400 ,  0.00000003339612 );
      func.set( -5.300 ,  0.00000005802207 );
      func.set( -5.200 ,  0.00000009983440 );
      func.set( -5.100 ,  0.00000017012231 );
      func.set( -5.000 ,  0.00000028710500 );
      func.set( -4.900 ,  0.00000047986955 );
      func.set( -4.800 ,  0.00000079435267 );
      func.set( -4.700 ,  0.00000130231565 );
      func.set( -4.600 ,  0.00000211464338 );
      func.set( -4.500 ,  0.00000340080306 );
      func.set( -4.400 ,  0.00000541695305 );
      func.set( -4.300 ,  0.00000854602119 );
      func.set( -4.200 ,  0.00001335409733 );
      func.set( -4.100 ,  0.00002066871577 );
      func.set( -4.000 ,  0.00003168603461 );
      func.set( -3.900 ,  0.00004811551887 );
      func.set( -3.800 ,  0.00007237243427 );
      func.set( -3.700 ,  0.00010783014541 );
      func.set( -3.600 ,  0.00015914571377 );
      func.set( -3.500 ,  0.00023267337367 );
      func.set( -3.400 ,  0.00033698082293 );
      func.set( -3.300 ,  0.00048348253664 );
      func.set( -3.200 ,  0.00068720208079 );
      func.set( -3.100 ,  0.00096767123560 );
      func.set( -3.000 ,  0.00134996722324 );
      func.set( -2.900 ,  0.00186588014039 );
      func.set( -2.800 ,  0.00255519064153 );
      func.set( -2.700 ,  0.00346702305311 );
      func.set( -2.600 ,  0.00466122178265 );
      func.set( -2.500 ,  0.00620967985875 );
      func.set( -2.400 ,  0.00819752886943 );
      func.set( -2.300 ,  0.01072408105972 );
      func.set( -2.200 ,  0.01390339890832 );
      func.set( -2.100 ,  0.01786435741803 );
      func.set( -2.000 ,  0.02275006203619 );
      func.set( -1.900 ,  0.02871649286457 );
      func.set( -1.800 ,  0.03593026551383 );
      func.set( -1.700 ,  0.04456543178248 );
      func.set( -1.600 ,  0.05479928945388 );
      func.set( -1.500 ,  0.06680722879345 );
      func.set( -1.400 ,  0.08075671125630 );
      func.set( -1.300 ,  0.09680054949574 );
      func.set( -1.200 ,  0.11506973171771 );
      func.set( -1.100 ,  0.13566610150762 );
      func.set( -1.000 ,  0.15865525975900 );
      func.set( -0.900 ,  0.18406009173192 );
      func.set( -0.800 ,  0.21185533393828 );
      func.set( -0.700 ,  0.24196357848479 );
      func.set( -0.600 ,  0.27425306493856 );
      func.set( -0.500 ,  0.30853753263572 );
      func.set( -0.400 ,  0.34457830341314 );
      func.set( -0.300 ,  0.38208864252738 );
      func.set( -0.200 ,  0.42074031283329 );
      func.set( -0.100 ,  0.46017210446634 );
      func.set( 0.000 ,  0.50000000000000 );
      func.set( 0.100 ,  0.53982789553366 );
      func.set( 0.200 ,  0.57925968716672 );
      func.set( 0.300 ,  0.61791135747262 );
      func.set( 0.400 ,  0.65542169658687 );
      func.set( 0.500 ,  0.69146246736428 );
      func.set( 0.600 ,  0.72574693506144 );
      func.set( 0.700 ,  0.75803642151521 );
      func.set( 0.800 ,  0.78814466606172 );
      func.set( 0.900 ,  0.81593990826808 );
      func.set( 1.000 ,  0.84134474024100 );
      func.set( 1.100 ,  0.86433389849238 );
      func.set( 1.200 ,  0.88493026828229 );
      func.set( 1.300 ,  0.90319945050426 );
      func.set( 1.400 ,  0.91924328874370 );
      func.set( 1.500 ,  0.93319277120655 );
      func.set( 1.600 ,  0.94520071054612 );
      func.set( 1.700 ,  0.95543456821752 );
      func.set( 1.800 ,  0.96406973448618 );
      func.set( 1.900 ,  0.97128350713543 );
      func.set( 2.000 ,  0.97724993796381 );
      func.set( 2.100 ,  0.98213564258197 );
      func.set( 2.200 ,  0.98609660109168 );
      func.set( 2.300 ,  0.98927591894028 );
      func.set( 2.400 ,  0.99180247113057 );
      func.set( 2.500 ,  0.99379032014125 );
      func.set( 2.600 ,  0.99533877821735 );
      func.set( 2.700 ,  0.99653297694689 );
      func.set( 2.800 ,  0.99744480935848 );
      func.set( 2.900 ,  0.99813411985961 );
      func.set( 3.000 ,  0.99865003277676 );
      func.set( 3.100 ,  0.99903232876440 );
      func.set( 3.200 ,  0.99931279791921 );
      func.set( 3.300 ,  0.99951651746336 );
      func.set( 3.400 ,  0.99966301917707 );
      func.set( 3.500 ,  0.99976732662633 );
      func.set( 3.600 ,  0.99984085428623 );
      func.set( 3.700 ,  0.99989216985459 );
      func.set( 3.800 ,  0.99992762756573 );
      func.set( 3.900 ,  0.99995188448114 );
      func.set( 4.000 ,  0.99996831396539 );
      func.set( 4.100 ,  0.99997933128423 );
      func.set( 4.200 ,  0.99998664590267 );
      func.set( 4.300 ,  0.99999145397881 );
      func.set( 4.400 ,  0.99999458304695 );
      func.set( 4.500 ,  0.99999659919694 );
      func.set( 4.600 ,  0.99999788535662 );
      func.set( 4.700 ,  0.99999869768435 );
      func.set( 4.800 ,  0.99999920564733 );
      func.set( 4.900 ,  0.99999952013045 );
      func.set( 5.000 ,  0.99999971289500 );
      func.set( 5.100 ,  0.99999982987769 );
      func.set( 5.200 ,  0.99999990016560 );
      func.set( 5.300 ,  0.99999994197793 );
      func.set( 5.400 ,  0.99999996660388 );
      func.set( 5.500 ,  0.99999998096360 );
      func.set( 5.600 ,  0.99999998925378 );
      func.set( 5.700 ,  0.99999999399235 );
      func.set( 5.800 ,  0.99999999667395 );
      func.set( 5.900 ,  0.99999999817642 );
      func.set( 6.000 ,  0.99999999900988 );
      func.set( 6.100 ,  0.99999999946763 );
      func.set( 6.200 ,  0.99999999971653 );
      func.set( 6.300 ,  0.99999999985053 );
      func.set( 6.400 ,  0.99999999992195 );
      func.set( 6.500 ,  0.99999999995964 );
      func.set( 6.600 ,  0.99999999997934 );
      func.set( 6.700 ,  0.99999999998952 );
      func.set( 6.800 ,  0.99999999999474 );
      func.set( 6.900 ,  0.99999999999738 );
      func.set( 7.000 ,  0.99999999999871 );
      func.set( 7.100 ,  0.99999999999937 );
      func.set( 7.200 ,  0.99999999999970 );
      func.set( 7.300 ,  0.99999999999986 );
      func.set( 7.400 ,  0.99999999999993 );
      func.set( 7.500 ,  0.99999999999997 );


      for(int i=0;i < func.getNum(); ++i) {

        double x = func.getX(i);
        double y = func.getY(i);
        double y_computed = getCDF_Alt(x);
        System.out.println("SRV = " + (float)x + "; Computed Prob = "+ y_computed + ";  Ratio = "+ y_computed/y );
      }

    }

    /**
	 * This is an alternative version of getCDF() that uses gauss object of
	 * edu.uah.math.psol.distributions
	 * @param standRandVariable
	 * @return CDF for the input SRV
     /
    public static double getCDF_Alt(double standRandVariable) {

        return gauss.getCDF( standRandVariable );
    }

	 */



}

