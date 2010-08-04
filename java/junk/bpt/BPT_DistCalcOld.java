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

package junk.bpt;

//The following are needed only for the tests
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;


/**
 * <b>Title:</b> BPT_DistCalc.java <p>
 * <b>Description:</p>.
 <p>
 *
 * @author Edward Field
 * @created    July, 2007
 * @version 1.0
 */

public final class BPT_DistCalcOld {
	
	EvenlyDiscretizedFunc pdf, cdf, hazFunc;
	double alpha;
	public final double DELTA_DEFAULT = 0.001;
	
	
	/*
	 * delta is the discretization of the x-axis for unit rate
	 */
	public BPT_DistCalcOld(double alpha, double delta){
		this.alpha = alpha;
		makeFunctions(delta);
	}
	
	/*
	 * This applies the default delta
	 */
	public BPT_DistCalcOld(double alpha){
		this.alpha = alpha;
		makeFunctions(DELTA_DEFAULT);
	}
	
	/*
	 * no arg constructor
	 */
	public BPT_DistCalcOld(){
		this.alpha = Double.NaN;
	}
	
	
	public void setAlpha(double alpha) {
		this.alpha = alpha;
		makeFunctions(DELTA_DEFAULT);
	}

	/*
	 * delta is the discretization of the x-axis.  
	 * The total number of points in the function will be 10*alpha/delta
	 */
	public void setAlphaAndDelta(double alpha, double delta) {
		this.alpha = alpha;
		makeFunctions(delta);
	}

	/*
	 * delta is the discretization of the x-axis.  The total number of points in the 
	 * function will be 10*alpha/delta+1.
	 */
	public void setDelta(double delta) {
		makeFunctions(delta);
	}
	
	public double getAlpha() {return alpha;}
	
	/*
	 * The discretization of the x-axis
	 */
	public double getDelta() {return cdf.getDelta();}

	/*
	 * delta is the discretization of the x-axis.  The total number of points in the 
	 * function will be 10*alpha/delta+1.  This obtains the cdf from the pdf using 
	 * Trapezoidal integration (more accurate than rectangular integration using by
	 * the static method). 
	 */
	private void makeFunctions(double delta) {
		
		// make sure alpha has been set
		if(Double.isNaN(alpha))
			throw new RuntimeException("Error in BPT_DistCalc: alpha is NaN");
		
		int num = Math.round((float)(alpha*10/delta));
		pdf = new EvenlyDiscretizedFunc(0,num,delta);
		cdf = new EvenlyDiscretizedFunc(0,num,delta);
		// set first y-values to zero
		pdf.set(0,0);
		cdf.set(0,0);
		
		double temp1 = 1.0/(2.*Math.PI*(alpha*alpha));
		double temp2 = 2.*(alpha*alpha);
		double t,pd,cd=0;
		for(int i=1; i< pdf.getNum(); i++) { // skip first point because it's NaN
			t = cdf.getX(i);
			pd = Math.sqrt(temp1/(t*t*t)) * Math.exp(-(t-1)*(t-1)/(temp2*t));
			if(Double.isNaN(pd)){
				pd=0;
				System.out.println("pd=0 for i="+i);
			}
			cd += delta*(pd+pdf.getY(i-1))/2;
			pdf.set(i,pd);
			cdf.set(i,cd);
		}
	}

	
	/*
	 * This gets the CDF for the alpha (and delta) already set
	 */
	public EvenlyDiscretizedFunc getCDF(double rate) {
		EvenlyDiscretizedFunc newCDF = new EvenlyDiscretizedFunc(cdf.getMinX()/rate, cdf.getMaxX()/rate, cdf.getNum());
		for(int i=0;i<newCDF.getNum();i++) newCDF.set(i,cdf.getY(i));
		// Add Info ?????
		return newCDF;
	}

	/*
	 * This gets the PDF for the alpha (and delta) already set
	 */
	public EvenlyDiscretizedFunc getPDF(double rate) {
		EvenlyDiscretizedFunc newPDF = new EvenlyDiscretizedFunc(pdf.getMinX()/rate, pdf.getMaxX()/rate, pdf.getNum());
		for(int i=0;i<newPDF.getNum();i++) newPDF.set(i,pdf.getY(i)*rate);
		// Add Info ?????
		return newPDF;
	}

	
	/*
	 * This gets the hazard function for the alpha (and delta) already set.  THIS NEEDS VERIFICATION
	 */
	public EvenlyDiscretizedFunc getHazFunc(double rate) {
		EvenlyDiscretizedFunc hazFunc = new EvenlyDiscretizedFunc(pdf.getMinX()/rate, pdf.getMaxX()/rate, pdf.getNum());
		double haz;
		for(int i=0;i<hazFunc.getNum();i++) {
			haz = pdf.getY(i)/(1.0-cdf.getY(i));
			hazFunc.set(i,haz);
		}
		// Add Info ?????
		return hazFunc;
	}
	
	/*
	 * This gives the probability of an event occurring between time T
	 * (on the x-axis) and T+duration, conditioned that it has not occurred before T
	 * (for the set alpha and delta).  THIS NEEDS TO BE TESTED
	 */
	public EvenlyDiscretizedFunc getCondProbFunc(double rate, double duration) {
		double delta = cdf.getDelta()/rate;
		int num = (int)((cdf.getMaxX()/rate - duration)/delta) - 1;
		EvenlyDiscretizedFunc condFunc = new EvenlyDiscretizedFunc(0.0, num , delta);
		for(int i=0;i<condFunc.getNum();i++) {
			condFunc.set(i,getCondProb(condFunc.getX(i), rate, duration));
		}
		// Add Info ?????
		return condFunc;
	}
	

	
	/**
	 * This computed the conditional probability using Trapezoidal integration (slightly more
	 * accurrate that the WGCEP-2002 code, which this method is modeled after). Although this method 
	 * is static (doesn't require instantiation), it is less efficient than the non-static version 
	 * here (it is also very slightly less accurate because the other interpolates the cdf).  
	 * @param timeSinceLast - time since last event
	 * @param rate - average rate of events
	 * @param alpha - coefficient of variation (technically corrrect??)
	 * @param duration - forecast duration
	 * @return
	 */
	public static double getCondProb(double mean, double aperiodicity, double timeSinceLast, double duration) {
		
		double step = 0.001;
		double cdf=0, pdf, pdf_last=0, t, temp1, temp2, x, cBPT1=0, cBPT2;
		int i, i1, i2;
		
		// avoid numerical problems when too far out on tails
		if ( timeSinceLast/mean > aperiodicity*10 )
			x = 10.*aperiodicity*mean;
		else
			x = timeSinceLast;
		
		// find index of the two points in time
		i1 = Math.round((float)((x/mean)/step))+1;
		i2 = Math.round((float)(((x+duration)/mean)/step))+1;
		
		temp1 = 1/(2.*Math.PI*(aperiodicity*aperiodicity));
		temp2 = 2.*(aperiodicity*aperiodicity)*1;
		t = step*1.;
		for(i=1; i<=i2; i++) {
			pdf = Math.sqrt(temp1/(t*t*t)) * Math.exp(-(t-1)*(t-1) / (temp2*t) );
			cdf += step*(pdf+pdf_last)/2;
			if ( i == i1 ) cBPT1 = cdf;
			t += step;
			pdf_last=pdf;
		}
		cBPT2 = cdf;
		
		if ( cBPT1 >= 1.0 )
			return Double.NaN;
		else
			return (cBPT2-cBPT1)/( 1.-cBPT1);
		
	}
	

	/**
	 * This is a non-static version that is more efficient and slightly more accurate (due to
	 * interpolation of the cdf function), although it requires instantiation and for alpha
	 * to have been set (whereupon the pdf and cdf functions for unit rate are created and
	 * stored). The commented out bit of code shows gives the non interpolated result which is
	 * exactly the same as what comes from the static version.
	 * @param timeSinceLast
	 * @param rate
	 * @param duration
	 * @return
	 */
	public double getCondProb(double timeSinceLast, double rate, double duration) {
		double t1 = timeSinceLast*rate;
		double t2 = (timeSinceLast+duration)*rate;
		double p1 = cdf.getInterpolatedY(t1);
		if(p1 >= 1.0) return Double.NaN;
		double p2 = cdf.getInterpolatedY(t2);
		return (p2-p1)/(1.0-p1);
		
		// non interpolated alt:
		/*
		int pt1 = (int) Math.round(timeSinceLast*rate/cdf.getDelta())+1;
		int pt2 = (int) Math.round((timeSinceLast+duration)*rate/cdf.getDelta())+1;
		return (cdf.getY(pt2)-cdf.getY(pt1))/(1.0-cdf.getY(pt1));
		*/

	}
	
	/**
	 *  Main method for running tests.  
	 *  Test1 compares the static getCondProb(*) method against values from the WGCEP-2002 
	 *  code; all are within 0.5%.
	 *  Test2 campares the other (non static) getCondProb(*)  method against values from the WGCEP-2002 
	 *  code; all are within 0.4%.  The systematic bias is due to what I believe is improved
	 *  bin centering in this version.
	 *  The static method takes about 2 times longer.
	 *  Test3 examines what happens if delta is changed to 0.01 (discrepancies are now up to 2.5%),
	 *  although it is faster by a factor of 8.
	 */
	public static void main(String args[]) {
		
		// test data from WGCEP-2002 code run (single branch for SAF) done by Ned Field
		// in Feb of 2006 (see his "Neds0206TestOutput.txt" file).
		double timeSinceLast = 96;
		double nYr = 30;
		double alph = 0.5;
		double[] rate = {0.00466746464,0.00432087015,0.004199435,0.004199435};
		double[] prob = {0.130127236,0.105091952,0.0964599401,0.0964599401};
		
		// Test1 (static method based on WGCEP-2002 code)
		double[] static_prob = new double[rate.length];
		double p;
		System.out.println("Test1: comparison with probs from WG02 code");
		for(int i=0;i<rate.length;i++) {
			p = getCondProb(1/rate[i],alph, timeSinceLast, nYr);
			System.out.println("Test1 (static): ="+(float)p+"; ratio="+(float)(p/prob[i]));
			static_prob[i]=p;
		}
		
		// Test2 (faster method based on pre-computed & saved function)
		BPT_DistCalcOld calc = new BPT_DistCalcOld(0.5);
		System.out.println("Test2: comparison between static and non static");
		for(int i=0;i<rate.length;i++) {
			p = calc.getCondProb(timeSinceLast,rate[i],nYr);
			System.out.println("Test2 (other): ="+(float)p+"; ratio="+(float)(p/static_prob[i]));
		}
		
		// Speed tests
		// First the static method based on WGCEP-2002 code
		long milSec0 = System.currentTimeMillis();
		int numCalcs = 10000;
		for(int i=0; i< numCalcs; i++)
			p = getCondProb(1/rate[0],alph,timeSinceLast,nYr);
		double time = (double)(System.currentTimeMillis()-milSec0)/1000;
		System.out.println("Speed Test for static = "+(float)time+" sec");
		// now the faster method based on pre-computed & saved function
		milSec0 = System.currentTimeMillis();
		for(int i=0; i< numCalcs; i++)
			p = calc.getCondProb(timeSinceLast,rate[0],nYr);
		double time2 = (double)(System.currentTimeMillis()-milSec0)/1000;
		System.out.println("Speed Test for other = "+(float)time2+" sec");
		System.out.println("Ratio of static to other = "+(float)(time/time2));
		
		
		// test the delta=0.01 case
		System.out.println("Test3: comparison static and non static w/ delta=0.01");
		calc.setDelta(0.01);
		for(int i=0;i<rate.length;i++) {
			p = calc.getCondProb(timeSinceLast,rate[i],nYr);
			System.out.println("Test3 (delta=0.01): ="+(float)p+"; ratio="+(float)(p/static_prob[i]));
		}
		// Speed tests
		milSec0 = System.currentTimeMillis();
		for(int i=0; i< numCalcs; i++)
			p = calc.getCondProb(timeSinceLast,rate[0],nYr);
		double time3 = (double)(System.currentTimeMillis()-milSec0)/1000;
		System.out.println("Speed Test for 0.01 delta (non static) = "+(float)time3+" sec");
		System.out.println("Ratio of compute time for default delta vs 0.01 delta  = "+(float)(time2/time3));


		
		// test the returned discretized functions
		// (need to un-comment println statements in makeFunctions method for the test comparison
		/*
		calc.setDelta(calc.DELTA_DEFAULT);
		
		EvenlyDiscretizedFunc func = calc.getPDF(0.01);
		System.out.println("PDF: func.getMinX="+func.getMinX()+"; func.getMaxX="+func.getMaxX());
		System.out.println("PDF: func.getY(1000)="+func.getY(1000));

		func = calc.getCDF(0.01);
		System.out.println("CDF: func.getMinX="+func.getMinX()+"; func.getMaxX="+func.getMaxX());
		System.out.println("CDF: func.getY(1000)="+func.getY(1000));
		
		EvenlyDiscretizedFunc func = calc.getCondProbFunc(0.01, 30);
		EvenlyDiscretizedFunc func = calc.getHazFunc(0.01);

		*/
	}
}

