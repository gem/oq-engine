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

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.A_Faults;

import org.opensha.sha.earthquake.calc.recurInterval.BPT_DistCalc;


/**
 * <p>Title: WG02_QkProbCalc </p>
 * <p>Description: 
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Ned Field
 * @date July, 2007
 * @version 1.0
 */


public class WG02_QkProbCalc {
	
	//for Debug purposes
	private static String C = new String("WG02_QkProbCalc");
	private final static boolean D = false;
	
	//name for this classs
	protected String NAME = "WG02_QkProbCalc";
		
	/*
	 * For segment specific alpha.  Note that segRate could be computed from rupRate and rupInSeg,
	 * but we don't do that in case this is called multiple times with the same values (e.g., in 
	 * a simulation).  It is up to the user do make sure segRate is consistent with rupRate and rupInSeg.
	 */
	public static double[] getRupProbs(double[] segRate, double[] rupRate, double[] segMoRate, 
			double[] segAlpha, double[] segTimeSinceLast, double duration, int[][] rupInSeg) {
		
		int num_seg = segRate.length;
		int num_rup = rupRate.length;

		double[] segProb = getSegProbs(segRate, segAlpha, segTimeSinceLast, duration);
		double[] rupProb = new double[num_rup];
		for(int rup=0; rup<num_rup; rup++) {
			// compute sum of segMoRates for segs in rupture
			double totMoRate = 0;
			for(int seg=0; seg < num_seg; seg++)
				totMoRate += segMoRate[seg]*rupInSeg[seg][rup];
			// now compute sum
			double sum = 0;
			for(int seg=0; seg < num_seg; seg++)
				sum += segProb[seg]*segMoRate[seg]*rupInSeg[seg][rup]/segRate[seg];
			rupProb[rup] = rupRate[rup]*sum/totMoRate;
		}	
		return rupProb;	}


	/*
	 * For constant alpha.    Note that segRate could be computed from rupRate and rupInSeg,
	 * but we don't do that in case this is called multiple times with the same values (e.g., in 
	 * a simulation).  It is up to the user do make sure segRate is consistent with rupRate and rupInSeg.
	 */
	public static double[] getRupProbs(double[] segRate, double[] rupRate, double[] segMoRate, double segAlpha, 
			                    double[] segTimeSinceLast, double duration, int[][] rupInSeg) {
		
		int num_seg = segRate.length;
		int num_rup = rupRate.length;

		double[] segProb = getSegProbs(segRate, segAlpha, segTimeSinceLast, duration);
		double[] rupProb = new double[num_rup];
		for(int rup=0; rup<num_rup; rup++) {
			// compute sum of segMoRates for segs in rupture
			double totMoRate = 0;
			for(int seg=0; seg < num_seg; seg++)
				totMoRate += segMoRate[seg]*rupInSeg[seg][rup];
			// now compute sum
			double sum = 0;
			for(int seg=0; seg < num_seg; seg++)
				sum += segProb[seg]*segMoRate[seg]*rupInSeg[seg][rup]/segRate[seg];
			rupProb[rup] = rupRate[rup]*sum/totMoRate;
		}	
		return rupProb;
	}

	
	/*
	 * compute seg probs for seg-variable alpha
	 */
	public static double[] getSegProbs(double[] segRate, double[] segAlpha, double[] segTimeSinceLast, double duration) {
		int num_seg = segRate.length;
		double[] segProb = new double[num_seg];
		for(int seg=0; seg < num_seg; seg++)
			segProb[seg] = BPT_DistCalc.getCondProb(1/segRate[seg], segAlpha[seg], segTimeSinceLast[seg], duration);
		return segProb;
	}


	/*
	 * compute seg probs for constant alpha
	 */
	public static double[] getSegProbs(double[] segRate, double segAlpha, double[] segTimeSinceLast, double duration) {
		int num_seg = segRate.length;
		double[] segProb = new double[num_seg];
		for(int seg=0; seg < num_seg; seg++)
			segProb[seg] = BPT_DistCalc.getCondProb(1/segRate[seg], segAlpha, segTimeSinceLast[seg], duration);
		return segProb;
	}
	
	
	

	
	/*
	 * This tests results against those obtained from the WGCEP-2002 Fortran code (single branch 
	 * for N. SAF done by Ned Field in Feb of 2006; see his "Neds0206TestOutput.txt" file).  Results
	 * are within 0.3%.

	 */
	public static void main(String args[]) {
		double[] segRate = {0.00466746464,0.00432087015,0.004199435,0.004199435};
		double[] rupRate = {0.00145604357,0.000706832856,0.,0.,0.000505269971,0.,0.00109066791,0.,0.000402616395,0.00270615076};
		double[] rupMag = {7.16886,7.24218,7.52195,7.37158,7.5081,7.70524,7.75427,7.81611,7.87073,7.94943};
		double[] segMoRate  = {4.74714853E+24,5.62020641E+24,1.51106804E+25,1.06885024E+25};
		double[] segAlpha = {0.5,0.5,0.5,0.5};
		double alpha = 0.5;
		double[] segTimeSinceLast = {96, 96, 96, 96};
		double duration = 30;
		int[][] rupInSeg = {
				// 1,2,3,4,5,6,7,8,9,10
				{1,0,0,0,1,0,0,1,0,1}, // seg 1
				{0,1,0,0,1,1,0,1,1,1}, // seg 2
				{0,0,1,0,0,1,1,1,1,1}, // seg 3
				{0,0,0,1,0,0,1,0,1,1} // seg 4
		};
		// test values
		double[] testRupProb = {0.0405939706,0.017191546,0.,0.,0.0131122563,0.,0.0250523612,0.,0.00934537873,0.0644722432};
		double[] testSegProb = {0.130127236,0.105091952,0.0964599401,0.0964599401};

		// try with both alpha and segAlpha
		double[] rupProb = WG02_QkProbCalc.getRupProbs(segRate,rupRate,segMoRate,alpha,segTimeSinceLast,duration,rupInSeg);
		// write out test results 
		/**/
		System.out.println("Test rup fractional differences:");
		for(int rup=0; rup<10;rup++)
			if(rupProb[rup] == 0)
				System.out.println("rup"+rup+": "+(float)(rupProb[rup]-testRupProb[rup]));
			else
				System.out.println("rup"+rup+": "+(float)((rupProb[rup]-testRupProb[rup])/testRupProb[rup]));
		
		
	}
}

