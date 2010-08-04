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

package org.opensha.commons.data.estimate;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;

/**
 * <p>Title: DiscreteValueEstimate.java </p>
 * <p>Description:  This can be used to specify probabilities associated with
 * discrete values from an ArbitrarilyDiscretizedFunction.
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class DiscreteValueEstimate extends DiscretizedFuncEstimate {
	public final static String NAME  =  "Discrete Values";

	/**
	 * Constructor - Accepts a ArbitrarilyDiscretizedFunc and an indication of whether it is
	 * normalized. Note that the function passed in is cloned.
	 * min and max are set according to those of the function
	 * passed in.
	 * @param func
	 */
	public DiscreteValueEstimate(ArbitrarilyDiscretizedFunc func, boolean isNormalized) {
		super(func, isNormalized);
	}



	/**
	 * Return the name of the estimate. This is the name visible to the user
	 * @return
	 */
	public String getName() {
		return NAME;
	}


	/**
	 * Get the cumulative distribution function
	 * @return
	 */
	public DiscretizedFunc getCDF_Test() {
		ArbitrarilyDiscretizedFunc cdfFunc = new ArbitrarilyDiscretizedFunc();
		int num = func.getNum();
		double delta = 1e-3;
		double x ;
		for(int i=0; i<num; ++i) {
			x = func.getX(i);
			cdfFunc.set(x, getProbLessThanEqual(x));
			if(i<(num-1)) {
				x = func.getX(i + 1) - delta; // get the value to make staircase function
				cdfFunc.set(x, getProbLessThanEqual(x));
			}
		}
		cdfFunc.setInfo("CDF from Discrete Distribution");
		return cdfFunc;
	}

	/**
	 * Get the probability for that the true value is less than or equal to provided
	 * x value
	 *
	 * @param x
	 * @return
	 */
	public double getProbLessThanEqual(double x) {
		if(x<this.cumDistFunc.getX(0)) return 0;// return 0 if it less than 1st X value in this estimate
		int num = cumDistFunc.getNum();
		for(int i=1; i<num; ++i)
			if(cumDistFunc.getX(i)>x)
				return cumDistFunc.getY(i-1);
		return 1;
	}

	/**
	 * Return the discrete fractile for this probability value.
	 *
	 * @param prob Probability for which fractile is desired
	 * @return
	 */
	/*public double getFractile(double prob) {
   int num = cumDistFunc.getNum();
   for(int i=0; i<num; ++i)
     if(cumDistFunc.getY(i)>prob)
       return cumDistFunc.getX(i);
   return 1;
 }*/


	public  DiscretizedFunc getPDF_Test() {
		return this.func;
	}

	/**
	 * It returns a random value from this estimate.
	 * It generates a random number from 0 to 1 using Math.random() function.
	 * Then it checks the Cum Dist Func and returns the first value where prob>=randomVal
	 * 
	 * @return
	 */
	public double getRandomValue() {
		double randomVal = Math.random();
		int num = cumDistFunc.getNum();
		for(int i=0; i<num; ++i)
			if(cumDistFunc.getY(i)>randomVal)
				return cumDistFunc.getX(i);
		return Double.NaN;
	}


}
