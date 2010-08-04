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

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.A_Faults;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.StringTokenizer;

import org.opensha.commons.calc.FaultMomentCalc;
import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Somerville_2006_MagAreaRel;
import org.opensha.commons.calc.nnls.NNLSWrapper;
import org.opensha.commons.data.ValueWeight;
import org.opensha.commons.data.function.ArbDiscrEmpiricalDistFunc;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.EmpiricalModel;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data.SegRateConstraint;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfFromSimpleFaultData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;

//import cj.math.nnls.NNLSWrapper;


/**
 * <p>Title: A_FaultSource </p>
 * <p>Description: This has been verified as follows: 1) the final
 * segment slip rates are matched for all solution types; 2) the correct mag-areas are obtained where a
 * mag-area relationship is used (seen in a GUI).
 * 
 * There is potential confusion here in that ruptures referred to here are actaully
 * sources (i.e., occurrences of "rup" should be changed to "rupSrc").
 * 
 * To Do: Matlab inversion tests
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Ned Field
 * @date Sept, 2003
 * @version 1.0
 */


public class A_FaultSegmentedSourceGenerator {
	
	//for Debug purposes
	private static String C = new String("A_FaultSource");
	private final static boolean D = false;
	private final static boolean MATLAB_TEST = false;
	
	//name for this classs
	protected String NAME = "Type-A Fault Source";
		
	private int num_seg, num_rup;
	
	// x-axis attributes for the MagFreqDists
	private final static double MIN_MAG = UCERF2.MIN_MAG;
	private final static double MAX_MAG = UCERF2.MAX_MAG;
	private final static double DELTA_MAG = UCERF2.DELTA_MAG;
	private final static int NUM_MAG = UCERF2.NUM_MAG;
	
	// this is used to filter out infrequent ruptures (approx age of earth)
	private final static double MIN_RUP_RATE = 1e-10;
	
	private double magSigma, magTruncLevel;
	
//	private boolean preserveMinAFaultRate;		// don't let any post inversion rates be below the minimum a-priori rate
	private double minRates[]; // the minimum rate constraint
	private boolean wtedInversion;	// weight the inversion according to slip rate and segment rate uncertainties
	private double relativeSegRate_wt, aPrioriRupWt, minNonZeroAprioriRate;
//	public final static double MIN_A_PRIORI_ERROR = 1e-6;
	
	
	// slip model:
	private String slipModelType;
	public final static String CHAR_SLIP_MODEL = "Characteristic (Dsr=Ds)";
	public final static String UNIFORM_SLIP_MODEL = "Uniform/Boxcar (Dsr=Dr)";
	public final static String WG02_SLIP_MODEL = "WGCEP-2002 model (Dsr prop to Vs)";
	public final static String TAPERED_SLIP_MODEL = "Tapered Ends ([Sin(x)]^0.5)";
	
	private static EvenlyDiscretizedFunc taperedSlipPDF, taperedSlipCDF;
	
	private int[][] rupInSeg;
	private double[][] segSlipInRup;
	
	private FaultSegmentData segmentData;
	
	private ArbDiscrEmpiricalDistFunc[] segSlipDist;  // segment slip dist
	private ArbitrarilyDiscretizedFunc[] rupSlipDist;
	
	private double[] finalSegRate, segRateFromApriori, segRateFromAprioriWithMinRateConstr, finalSegSlipRate, aPrioriSegSlipRate;
	
	private String[] rupNameShort, rupNameLong;
	private double[] rupArea, rupMeanMag, rupMeanMo, rupMoRate, totRupRate;
	double[] rupRateSolution; // these are the rates from the inversion (not total rate of MFD)
	private IncrementalMagFreqDist[] rupMagFreqDist; // MFD for rupture
	
	private SummedMagFreqDist summedMagFreqDist;
	private double totalMoRateFromRups;
	
	private ValueWeight[] aPrioriRupRates;
	
	// the following is the total moment-rate reduction, including that which goes to the  
	// background, sfterslip, events smaller than the min mag here, and aftershocks and foreshocks.
	private double moRateReduction;  
	
	 // The following is the ratio of the average slip for the Gaussian MFD divided by the slip of the average magnitude.
	private double aveSlipCorr;
	private double meanMagCorrection;
	
	private MagAreaRelationship magAreaRel;
	
	// NNLS inversion solver - static to save time and memory
	private static NNLSWrapper nnls = new NNLSWrapper();

	// list of sources
	private ArrayList<FaultRuptureSource> sourceList;
	
	private final static double DEFAULT_GRID_SPACING = UCERF2.GRID_SPACING;
	
	private Boolean isTimeDeptendent;
	
	private double[] segProb, segGain, segAperiodicity, segTimeSinceLast, rupProb, rupGain;
	
	/*Create a Rupture-Source Mapping, This is needed because some sources are not put into SourceList 
	when we call getTimeDependentSources() or getTimeIndependentSources() or getTimeDepEmpiricalSources() */
	private HashMap<Integer, Integer> rupSrcMapping; 
	private HashMap<Integer, Integer> srcRupMapping; 

	private static Somerville_2006_MagAreaRel somerville_magAreaRel = new Somerville_2006_MagAreaRel();

	/**
	 * Description:
	 * 
	 * @param segmentData - SegmentedFaultData, where it is assumed that these are in proper order such 
	 * that concatenating the FaultTraces will produce a total FaultTrace with locations in the proper order.
	 * 
	 * NOTES:
	 * 
	 * 1) if magSigma=0, magnitude gets rounded to nearest integer value of DELTA_MAG, which means the total rupture rate
	 * (from the MFD) may differ from the a-priori rate by up to 10^(1.5*DELTA_MAG/2) which = 19% if DELTA_MAG = 0.1!  This assumes
	 * the a-priori rates are rate-balanced to begin with.
	 * 
	 * 2) if magSigma>0, a correction is made for the fact that average slip for the MFD is different from the slip of
	 * the average mag.  This correction assumes ave mag equals an integer times DELTA_MAG; this latter assumption can
	 * lead to rate discrepancies of up to ~1.5%
	 * 
	 * @param segmentData - 
	 * @param magAreaRel - any MagAreaRelationship
	 * @param slipModelType - 
	 * @param aPrioriRupRates - 
	 * @param magSigma - 
	 * @param magTruncLevel - 
	 * @param moRateReduction - 
	 * @param meanMagCorrection - 
	 * @param preserveMinAFaultRate - 
	 * @param wtedInversion - determines whether data standard deviations are applied as weights
	 * @param relativeSegRate_wt - the amount to weight all segment rates relative to segment slip rates
	 * @param aPrioriRupWt - the amount to weight the a-priori rates (1/uncertainty)
	 */

	public A_FaultSegmentedSourceGenerator(FaultSegmentData segmentData, MagAreaRelationship magAreaRel, 
			String slipModelType, ValueWeight[] aPrioriRupRates, double magSigma, 
			double magTruncLevel, double moRateReduction, double meanMagCorrection,
			double minRates[], boolean wtedInversion, double relativeSegRate_wt,
			double aPrioriRupWt) {
		
		this.segmentData = segmentData;
		this.magAreaRel = magAreaRel;
		this.slipModelType = slipModelType;
		this.aPrioriRupRates = aPrioriRupRates;
		this.magSigma = magSigma;
		this.magTruncLevel = magTruncLevel;
		this.moRateReduction = moRateReduction;  // fraction of slip rate reduction
		this.meanMagCorrection = meanMagCorrection;
//		this.preserveMinAFaultRate = preserveMinAFaultRate;
		this.minRates = minRates;
		this.wtedInversion = wtedInversion;
		this.relativeSegRate_wt = relativeSegRate_wt;
		this.aPrioriRupWt = aPrioriRupWt;
		num_seg = segmentData.getNumSegments();
		
		calcAllRates();
		
		isTimeDeptendent = null;
		
		// temp simulation
//		if(segmentData.getFaultName().equals("S. San Andreas"))
//			simulateEvents(10000);
	
		
	}
	
	
	/*
	 * This does all the main calculations related to long-term rates
	 */
	private void calcAllRates(){
		// get the RupInSeg Matrix for the given number of segments
		if(segmentData.getFaultName().equals("San Jacinto")) {
			rupInSeg = getSanJacintoRupInSeg();	// special case for this branching fault
			num_rup = 25;
		}
		else {
			rupInSeg = getRupInSegMatrix(num_seg);
			num_rup = getNumRuptureSurfaces(segmentData);
		}
		

		// do some checks
		if(num_rup != aPrioriRupRates.length)
			throw new RuntimeException("Error: number of ruptures is incompatible with number of elements in aPrioriRupRates");

		rupNameShort = getAllShortRuptureNames(segmentData);
		rupNameLong = getAllLongRuptureNames(segmentData);
		
		// compute minNonZeroAprioriRate
		minNonZeroAprioriRate=Double.MAX_VALUE;
		for(int rup=0; rup<num_rup; rup++) 
			if(aPrioriRupRates[rup].getValue() != 0.0 && aPrioriRupRates[rup].getValue() < minNonZeroAprioriRate)
				minNonZeroAprioriRate = aPrioriRupRates[rup].getValue();
//		System.out.println(this.segmentData.getFaultName()+":  minNonZeroAprioriRate = "+minNonZeroAprioriRate);

		// compute rupture areas
		computeRupAreas();
		
		// get rates on each segment implied by a-priori rates (segRateFromApriori[*])
		// Compute this both with and without the min-rate constraints applied 
		// (segRateFromApriori & segRateFromAprioriWithMinRateConstr, respectively) 
		// The latter is used in computing mags & char slip below when Char Slip model chosen
		computeSegRatesFromAprioriRates();
		
		// compute aveSlipCorr (ave slip is greater than slip of ave mag if MFD sigma non zero)
		setAveSlipCorrection();
//		System.out.println("AVE ratio: "+ aveSlipCorr);

		// compute rupture mean mags
		if(slipModelType.equals(CHAR_SLIP_MODEL))
			getRupMeanMagsAssumingCharSlip();
		else {
			// compute from mag-area relationship
			rupMeanMag = new double[num_rup];
			rupMeanMo = new double[num_rup];
			for(int rup=0; rup <num_rup; rup++) {
				rupMeanMag[rup] = magAreaRel.getMedianMag(rupArea[rup]/1e6) + meanMagCorrection;
				rupMeanMo[rup] = aveSlipCorr*MomentMagCalc.getMoment(rupMeanMag[rup]);   // increased if magSigma >0
			}
		}
		
		// compute matrix of Dsr (slip on each segment in each rupture)
		computeSegSlipInRupMatrix();
		
		
		// NOW SOLVE THE INVERSE PROBLEM
		
		// get the segment rate constraints
		ArrayList<SegRateConstraint> segRateConstraints = segmentData.getSegRateConstraints();
		int numRateConstraints = segRateConstraints.size();
		
		// set number of rows as one for each slip-rate/segment (the minimum)
		int totNumRows = num_seg;
		// add segment rate constrains if needed
		if(relativeSegRate_wt > 0.0)	totNumRows += numRateConstraints;
		// add a-priori rate constrains if needed
		if(aPrioriRupWt > 0.0)  totNumRows += num_rup;
		
		int numRowsBeforeSegRateData = num_seg;
		if(aPrioriRupWt > 0.0) numRowsBeforeSegRateData += num_rup;
		
		double[][] C = new double[totNumRows][num_rup];
		double[] d = new double[totNumRows];  // the data vector
		
		// CREATE THE MODEL AND DATA MATRICES
		// first fill in the slip-rate constraints
		for(int row = 0; row < num_seg; row ++) {
			d[row] = segmentData.getSegmentSlipRate(row)*(1-moRateReduction);
			for(int col=0; col<num_rup; col++)
				C[row][col] = segSlipInRup[row][col];
		}
		// now fill in the a-priori rates if needed
		if(aPrioriRupWt > 0.0) {
			for(int rup=0; rup < num_rup; rup++) {
				d[rup+num_seg] = aPrioriRupRates[rup].getValue();
				C[rup+num_seg][rup]=1.0;
			}
		}
		// now fill in the segment recurrence interval constraints if requested
		if(relativeSegRate_wt > 0.0) {
			SegRateConstraint constraint;
			for(int row = 0; row < numRateConstraints; row ++) {
				constraint = segRateConstraints.get(row);
				int seg = constraint.getSegIndex();
				d[row+numRowsBeforeSegRateData] = constraint.getMean(); // this is the average segment rate
				for(int col=0; col<num_rup; col++)
					C[row+numRowsBeforeSegRateData][col] = rupInSeg[seg][col];
			}
		}
		
		// CORRECT IF MINIMUM RATE CONSTRAINT DESIRED
		double[] Cmin = new double[totNumRows];  // the data vector
		// correct the data vector
		for(int row=0; row <totNumRows; row++) {
			for(int col=0; col < num_rup; col++)
				Cmin[row]+=minRates[col]*C[row][col];
			d[row] -= Cmin[row];
		}

		// APPLY DATA WEIGHTS IF DESIRED
		if(wtedInversion) {
			double data_wt;
			for(int row = 0; row < num_seg; row ++) {
//				data_wt = Math.pow((1-moRateReduction)*segmentData.getSegSlipRateStdDev(row), -2);
				data_wt = 1/((1-moRateReduction)*segmentData.getSegSlipRateStdDev(row));
				d[row] *= data_wt;
				for(int col=0; col<num_rup; col++)
					C[row][col] *= data_wt;
			}
			// now fill in the segment recurrence interval constraints if requested
			if(relativeSegRate_wt > 0.0) {
				SegRateConstraint constraint;
				for(int row = 0; row < numRateConstraints; row ++) {
					constraint = segRateConstraints.get(row);
//					data_wt = Math.pow(constraint.getStdDevOfMean(), -2);
					data_wt = 1/constraint.getStdDevOfMean();
					d[row+numRowsBeforeSegRateData] *= data_wt; // this is the average segment rate
					for(int col=0; col<num_rup; col++)
						C[row+numRowsBeforeSegRateData][col] *= data_wt;
				}
			}
		}
		
		// APPLY EQUATION-SET WEIGHTS
		// for the a-priori rates:
		if(aPrioriRupWt > 0.0) {
			double wt;
			for(int rup=0; rup < num_rup; rup++) {
				if(aPrioriRupRates[rup].getValue() > 0)
					wt = aPrioriRupWt/aPrioriRupRates[rup].getValue();
				else
					wt = aPrioriRupWt/minNonZeroAprioriRate; // make it the same as for smallest non-zero rate
//					wt = MIN_A_PRIORI_ERROR;

				// Hard code special constraints
//				if(this.segmentData.getFaultName().equals("N. San Andreas") && rup==9) wt = 1e10/aPrioriRupRates[rup].getValue();
				if(this.segmentData.getFaultName().equals("San Jacinto") && rup==3) wt = 1e10/minNonZeroAprioriRate;			
					
//				wt = aPrioriRupWt;
				d[rup+num_seg] *= wt;
				C[rup+num_seg][rup] *= wt;
			}
		}
		// for the segment recurrence interval constraints if requested:
		if(relativeSegRate_wt > 0.0) {
			for(int row = 0; row < numRateConstraints; row ++) {
				d[row+numRowsBeforeSegRateData] *= relativeSegRate_wt;
				for(int col=0; col<num_rup; col++)
					C[row+numRowsBeforeSegRateData][col] *= relativeSegRate_wt;
			}
		}
/*
		// manual check of matrices
		if(segmentData.getFaultName().equals("Elsinore")) {
			System.out.println("Elsinore");
			int nRow = C.length;
			int nCol = C[0].length;
			System.out.println("C = [");
			for(int i=0; i<nRow;i++) {
				for(int j=0;j<nCol;j++) 
					System.out.print(C[i][j]+"   ");
				System.out.print("\n");
			}
			System.out.println("];");
			System.out.println("d = [");
			for(int i=0; i<nRow;i++)
				System.out.println(d[i]);
			System.out.println("];");
		}
*/
		
		if(MATLAB_TEST) {
			// remove white space in name for Matlab
			StringTokenizer st = new StringTokenizer(segmentData.getFaultName());
			String tempName = st.nextToken();;
			while(st.hasMoreTokens())
				tempName += "_"+st.nextToken();
			System.out.println("display "+tempName);
		}
		
		
		// SOLVE THE INVERSE PROBLEM
		rupRateSolution = getNNLS_solution(C, d);
		
		
		// CORRECT FINAL RATES IF MINIMUM RATE CONSTRAINT APPLIED
		for(int rup=0; rup<num_rup;rup++)
			rupRateSolution[rup] += minRates[rup];
		
//		System.out.println("NNLS rates:");
//		for(int rup=0; rup < rupRate.length; rup++)
//			System.out.println((float) rupRateSolution[rup]);
		
/*		
		if(D) {
//			 check slip rates to make sure they match exactly
			double tempSlipRate;
			//System.out.println("Check of segment slip rates for "+segmentData.getFaultName()+":");
			for(int seg=0; seg < num_seg; seg++) {
				tempSlipRate = 0;
				for(int rup=0; rup < num_rup; rup++)
					tempSlipRate += rupRateSolution[rup]*segSlipInRup[seg][rup];
				double absFractDiff = Math.abs(tempSlipRate/(segmentData.getSegmentSlipRate(seg)*(1-this.moRateReduction)) - 1.0);				System.out.println("SlipRateCheck:  "+(float) (tempSlipRate/(segmentData.getSegmentSlipRate(seg)*(1-this.moRateReduction))));
				if(absFractDiff > 0.001)
					throw new RuntimeException("ERROR - slip rates differ!!!!!!!!!!!!");
			}
		}
*/
		
		// Make MFD for each rupture & the total sum
		totRupRate = new double[num_rup];
		rupMoRate = new double[num_rup];
		totalMoRateFromRups = 0.0;
		summedMagFreqDist = new SummedMagFreqDist(MIN_MAG, NUM_MAG, DELTA_MAG);
		// this boolean tells us if there is only one non-zero mag in the MFD
		boolean singleMag = (magSigma*magTruncLevel < DELTA_MAG/2);
		rupMagFreqDist = new GaussianMagFreqDist[num_rup];
		double mag;
		for(int i=0; i<num_rup; ++i) {
			// we conserve moment rate exactly (final rupture rates will differ from rupRateSolution[] 
			// due to MFD discretization or rounding if magSigma=0)
			rupMoRate[i] = rupRateSolution[i] * rupMeanMo[i];
			totalMoRateFromRups+=rupMoRate[i];
			// round the magnitude if need be
			if(singleMag)
				mag = Math.round((rupMeanMag[i]-MIN_MAG)/DELTA_MAG) * DELTA_MAG + MIN_MAG;
			else
				mag = rupMeanMag[i];
			rupMagFreqDist[i] = new GaussianMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG, 
					mag, magSigma, rupMoRate[i], magTruncLevel, 2);
						
			summedMagFreqDist.addIncrementalMagFreqDist(rupMagFreqDist[i]);
			totRupRate[i] = rupMagFreqDist[i].getTotalIncrRate();
			
//double testRate = rupMoRate[i]/MomentMagCalc.getMoment(rupMeanMag[i]);
//System.out.println((float)(testRate/rupRateSolution[i]));
// if(((String)getLongRupName(i)).equals("W")) System.out.print(totRupRate[i]+"  "+rupRateSolution[i]);
		}
		// add info to the summed dist
		String summed_info = "\n\nMoment Rate: "+(float) getTotalMoRateFromSummedMFD() +
		"\n\nTotal Rate: "+(float)summedMagFreqDist.getCumRate(0);
		summedMagFreqDist.setInfo(summed_info);
		
		// Computer final segment slip rate
		computeFinalSegSlipRate();
		
		// get final rate of events on each segment (this takes into account mag rounding of MFDs)
		computeFinalSegRates();		

		// find the slip distribution for each rupture (rupSlipDist{})
		computeRupSlipDist();
		
		// find the slip distribution of each segment
		//computeSegSlipDist(segRupSlipFactor);
		/*
		if(D) {
			// print the slip distribution of each segment
			for(int i=0; i<num_seg; ++i) {
				System.out.println("Slip for segment "+i+":");
				System.out.println(segSlipDist[i]);
			}
		}
		*/

	}
	
	/**
	 * Get Combined surface for a particular rupture index
	 * @param rupIndex
	 * @return
	 */
	public StirlingGriddedSurface getCombinedGriddedSurface(int rupIndex, boolean applyCyberShakeDDW_Corr) {
		int[] segmentsInRup = getSegmentsInRup(rupIndex);
		if(applyCyberShakeDDW_Corr) {
			double ddwCorrFactor = somerville_magAreaRel.getMedianArea(rupMeanMag[rupIndex])/(rupArea[rupIndex]/1e6);
			return segmentData.getCombinedGriddedSurface(segmentsInRup, DEFAULT_GRID_SPACING, ddwCorrFactor);
		} else
			return segmentData.getCombinedGriddedSurface(segmentsInRup, DEFAULT_GRID_SPACING);
	}

	/*
	public void writeSegmentsInSource(int srcIndex) {
		int[] segmentsInRup = getSegmentsInRup(srcRupMapping.get(srcIndex));
		for(int s=0; s<segmentsInRup.length;s++) System.out.println(s+"\t"+segmentsInRup[s]);
		
	}
*/
	
	/**
	 * Get Combined surface for a particular rupture index
	 * @param rupIndex
	 * @return
	 */
	public StirlingGriddedSurface getCombinedGriddedSurfaceForSource(int srcIndex, boolean applyCyberShakeDDW_Corr) {
		return getCombinedGriddedSurface( srcRupMapping.get(srcIndex), applyCyberShakeDDW_Corr);
	}

	
	
	/**
	 * Get Ave Rake for a particular rupture index
	 * @param rupIndex
	 * @return
	 */
	public double getAveRake(int rupIndex) {
		int[] segmentsInRup = getSegmentsInRup(rupIndex);
		return segmentData.getAveRake(segmentsInRup);
	}

	
	/**
	 * Get Ave Rake for a particular rupture index
	 * @param rupIndex
	 * @return
	 */
	public double getAveRakeForSource(int srcIndex) {
		return getAveRake(srcRupMapping.get(srcIndex));
	}

	
	/**
	 * Get a list of time independent sources for the given duration
	 * 
	 * @return
	 */
	public ArrayList<FaultRuptureSource> getTimeIndependentSources(double duration) {
		
		isTimeDeptendent= false;
		
		segTimeSinceLast = null;
		segAperiodicity = null;

		// compute seg prob and gain
		segGain = new double[num_seg];
		segProb = new double[num_seg];
		for(int i=0;i<num_seg;i++) {
			segProb[i]=(1-Math.exp(-duration*finalSegRate[i]));
			segGain[i]=1.0;
		}

		// a check could be made here whether time-ind sources already exist, 
		// and if so the durations of each could simply be changed (rather than recreating the sources)
		this.sourceList = new ArrayList<FaultRuptureSource>();
		rupSrcMapping = new  HashMap<Integer, Integer> (); 
		srcRupMapping = new  HashMap<Integer, Integer> (); 
		rupGain = new double[num_rup];
		rupProb = new double[num_rup];
		for(int i=0; i<num_rup; i++) {
			rupProb[i]=(1-Math.exp(-duration*totRupRate[i]));
			rupGain[i]=1.0;
			
			//System.out.println(this.segmentData.getFaultName()+"\t"+i+"\t"+this.segmentData.getAveRake(segmentsInRup));

			// Create source if rate is greater than ~zero (or age of earth)
			if (rupMagFreqDist[i].getTotalIncrRate() > MIN_RUP_RATE) {				
				FaultRuptureSource faultRupSrc = new FaultRuptureSource(rupMagFreqDist[i], 
						getCombinedGriddedSurface(i, false),
						getAveRake(i),
						duration);
				faultRupSrc.setName(this.getLongRupName(i));
				
				if(faultRupSrc.getNumRuptures() == 0)
					System.out.println(faultRupSrc.getName()+ " has zero ruptures");
				rupSrcMapping.put(i, sourceList.size());
				srcRupMapping.put(sourceList.size(),i);
				sourceList.add(faultRupSrc);
				
				/*
				// this is a check to make sure the total prob from source is same as
				// that computed by hand. It is
				double probFromSrc =faultRupSrc.computeTotalProb();
				System.out.println(segme3ntData.getFaultName()+" Prob: from src="+(float)probFromSrc+
						"; from totRate="+(float)rupProb[i]+"; ratio="+
						(float)(probFromSrc/rupProb[i]));
				*/
			}	
			//else
				//System.out.println("Rate of "+this.getLongRupName(i)+" is below 1e-10 ("+rupMagFreqDist[i].getTotalIncrRate()+")");
		}
		return this.sourceList;
	}

	
	/**
	 * Get a list of time dependent empirical sources for the given duration
	 * 
	 * @return
	 */
	public ArrayList<FaultRuptureSource> getTimeDepEmpiricalSources(double duration, 
			EmpiricalModel empiricalModel) {
		
		isTimeDeptendent= false;
		
		segTimeSinceLast = null;
		segAperiodicity = null;

		
		// a check could be made here whether time-ind sources already exist, 
		// and if so the durations of each could simply be changed (rather than recreating the sources)
		this.sourceList = new ArrayList<FaultRuptureSource>();
		rupSrcMapping = new  HashMap<Integer, Integer> (); 
		srcRupMapping = new  HashMap<Integer, Integer> ();
		rupGain = new double[num_rup];
		rupProb = new double[num_rup];
		double[] modRupRate = new double[num_rup];
		for(int i=0; i<num_rup; i++) {
			
			StirlingGriddedSurface rupSurf = getCombinedGriddedSurface(i, false);
			double empiricalCorr = empiricalModel.getCorrection(rupSurf);

			modRupRate[i] = totRupRate[i]*empiricalCorr;
			rupProb[i]=(1-Math.exp(-duration*modRupRate[i]));
			rupGain[i]= rupProb[i]/(1-Math.exp(-duration*totRupRate[i]));

			// reduce rates in MFD
			IncrementalMagFreqDist modMagFreqDist = rupMagFreqDist[i].deepClone();
			for(int magIndex=0; magIndex<modMagFreqDist.getNum(); ++magIndex) {
				modMagFreqDist.set(magIndex, empiricalCorr*modMagFreqDist.getY(magIndex));
			}
			// Create source if rate is greater than ~zero (or age of earth)
			if (totRupRate[i] > MIN_RUP_RATE) {				
				FaultRuptureSource faultRupSrc = new FaultRuptureSource(modMagFreqDist, 
						rupSurf,
						getAveRake(i),
						duration);
				faultRupSrc.setName(this.getLongRupName(i));
				
				if(faultRupSrc.getNumRuptures() == 0)
					System.out.println(faultRupSrc.getName()+ " has zero ruptures");
				rupSrcMapping.put(i, sourceList.size());
				srcRupMapping.put(sourceList.size(),i);
				sourceList.add(faultRupSrc);
				
				/*
				// this is a check to make sure the total prob from source is same as
				// that computed by hand. It is
				double probFromSrc =faultRupSrc.computeTotalProb();
				System.out.println(segme3ntData.getFaultName()+" Prob: from src="+(float)probFromSrc+
						"; from totRate="+(float)rupProb[i]+"; ratio="+
						(float)(probFromSrc/rupProb[i]));
				*/
			}	
			//else
				//System.out.println("Rate of "+this.getLongRupName(i)+" is below 1e-10 ("+rupMagFreqDist[i].getTotalIncrRate()+")");
		}
		
		// compute seg prob and gain
		segGain = new double[num_seg];
		segProb = new double[num_seg];
		double[] modSegRate = new double[num_seg];
		for(int seg=0; seg<num_seg; ++seg) {
			modSegRate[seg]=0.0;
			// Sum the rates of all ruptures which are part of a segment
			for(int rup=0; rup<num_rup; rup++) 
				if(rupInSeg[seg][rup]==1) modSegRate[seg]+=modRupRate[rup];
		}

		for(int i=0;i<num_seg;i++) {
			segProb[i]=(1-Math.exp(-duration*modSegRate[i]));
			segGain[i]=segProb[i]/(1-Math.exp(-duration*finalSegRate[i]));
		}

		return this.sourceList;
	}

	
	
	/**
	 * Get a list of time dependent sources for the given info
	 * 
	 * @return
	 */
	public ArrayList<FaultRuptureSource> getTimeDependentSources(double duration, 
			double startYear, double aperiodicity, 
			boolean applySegVariableAperiodicity) {

		isTimeDeptendent= true;
		
		// compute time-dep data
		segTimeSinceLast = new double[num_seg];
		segAperiodicity = new double[num_seg];
		for(int i=0;i<num_seg;i++) {
			segTimeSinceLast[i] = startYear-this.segmentData.getSegCalYearOfLastEvent(i);
			if(applySegVariableAperiodicity) {
				segAperiodicity[i] = this.segmentData.getSegAperiodicity(i);
				if(Double.isNaN(segAperiodicity[i])) segAperiodicity[i] = aperiodicity;
			}
			else
				segAperiodicity[i] = aperiodicity;
		}
		rupProb = WG02_QkProbCalc.getRupProbs(finalSegRate, totRupRate, getFinalSegMoRate(), segAperiodicity, 
											segTimeSinceLast, duration, rupInSeg);		
		//set very low rupture probabilities to zero (nicer values)
		for(int i=0;i<num_rup;i++)
			if(rupProb[i] <= 1e-12) rupProb[i] = 0.0;
		
		segProb = WG02_QkProbCalc.getSegProbs(finalSegRate, segAperiodicity, segTimeSinceLast, duration);
		
// this writes out data that I pasted into the testAll() procedure of the Igor Experiment "testBPT_calcs",
// which is in Ned's Appendix N folder; everything looked good		
	//	for(int i=0; i<num_seg; i++)
		//	if(this.segmentData.getSegmentName(i).equals("CC"))
			//	System.out.println("testCondProb("+finalSegRate[i]+","+segAperiodicity[i]+","+segmentData.getSegCalYearOfLastEvent(i)+","+startYear+","+duration+","+segProb[i]+")");
		
		// now compute gain data
		segGain = new double[num_seg];
		for(int i=0;i<num_seg;i++) segGain[i]=segProb[i]/(1-Math.exp(-duration*finalSegRate[i]));
		rupGain = new double[num_rup];
		for(int i=0;i<num_rup;i++) {
			if(totRupRate[i] >1e-12) // avoid dividing by zero for very low prob events
				rupGain[i]=rupProb[i]/(1-Math.exp(-duration*totRupRate[i]));
			else
				rupGain[i]=1.0;
		}
		
		// now make the sources
		this.sourceList = new ArrayList<FaultRuptureSource>();
		rupSrcMapping = new  HashMap<Integer, Integer> (); 
		srcRupMapping = new  HashMap<Integer, Integer> ();
		for(int i=0; i<num_rup; i++) {
 //if (rupProb[i] <= MIN_RUP_RATE) System.out.println(this.getLongRupName(i));
			// Create source if prob is greater than ~zero
			if (rupProb[i] > MIN_RUP_RATE) {		
				FaultRuptureSource faultRupSrc = new FaultRuptureSource(rupProb[i], rupMagFreqDist[i], 
						getCombinedGriddedSurface(i, false), getAveRake(i));
				faultRupSrc.setName(this.getLongRupName(i));
				rupSrcMapping.put(i, sourceList.size());
				srcRupMapping.put(sourceList.size(),i);
				sourceList.add(faultRupSrc);
				/*
				// this is a check to make sure the total prob from source is same as
				// that computed by hand. It is
				double probFromSrc =faultRupSrc.computeTotalProb();
				System.out.println(segmentData.getFaultName()+" Prob: from src="+(float)probFromSrc+
						"; from rupProb="+(float)rupProb[i]+"; ratio="+
						(float)(probFromSrc/rupProb[i]));
				*/
			}	
		}
		
		// This shows that the BPT seg probs is not that same as the final aggregate segment probs
		/*
		System.out.println(segmentData.getFaultName()+" seg probs:");
		for(int i=0;i<num_seg;i++) {
			double p1 = segProb[i];
			double p2 = computeSegProbAboveMag(5, i);
			System.out.println((float)p1+"\t"+(float)p2+"\t"+(float)(p1/p2));
		}
		*/
		return this.sourceList;
	}
	
	/*
	 * This returns the total probability of occurrence assuming independence among all the rupture sources
	 */
	public double getTotFaultProb() {
		double totProbNoEvent = 1;
		for(int i=0;i<num_rup;i++) totProbNoEvent *= (1.0-this.getRupSourceProb(i));
		return 1.0 - totProbNoEvent;
	}
	
	/*
	 * This returns the total probability of occurrence assuming independence among all the rupture sources
	 */
	public double getTotFaultProb(double mag) {
		return getTotFaultProb(mag, null);
	}
	
	/*
	 * This returns the total probability of occurrence assuming independence among all the rupture sources
	 */
	public double getTotFaultProb(double mag, Region region) {
		double totProbNoEvent = 1;
		for(int i=0;i<num_rup;i++) totProbNoEvent *= (1.0-this.getRupSourceProbAboveMag(i, mag, region));
		return 1.0 - totProbNoEvent;
	}
	
	/*
	 * This returns the approximate total probability of occurrence assuming independence among all the rupture sources
	 * It calls the computeApproxTotalProbAbove of ProbEqkSource (instead of computeTotalProbAbove method)
	 */
	public double getApproxTotFaultProb(double mag, Region region) {
		double totProbNoEvent = 1;
		for(int i=0;i<num_rup;i++) totProbNoEvent *= (1.0-this.getRupSourceApproxProbAboveMag(i, mag, region));
		return 1.0 - totProbNoEvent;
	}
	
	/*
	 * This returns the total probability of occurrence assuming independence among all the rupture sources
	 */
	public double getTotFaultProbGain() {
		double totPoisProbNoEvent = 1;
		for(int i=0;i<num_rup;i++){
			double poisProb = getRupSourceProb(i)/getRupSourcProbGain(i);
			totPoisProbNoEvent *= (1-poisProb);
		}
		return getTotFaultProb()/(1.0-totPoisProbNoEvent);
	}
	
	/**
	 * This returns the total probability for the ith Rupture Source 
	 * (as computed the last time getTimeIndependentSources(*) or getTimeDependentSources(*) was called).
	 * @param ithRup
	 * @return
	 */
	public double getRupSourceProb(int ithRup) { 
		return rupProb[ithRup]; 
		}

	/**
	 * This returns the total probability for the ith Rupture Source above the given mag 
	 * (as computed the last time getTimeIndependentSources(*) or getTimeDependentSources(*) was called).
	 * @param ithRup
	 * @return
	 */
	public double getRupSourceProbAboveMag(int ithRup, double mag) { 
		return getRupSourceProbAboveMag(ithRup, mag, null);
	}
	
	/**
	 * This returns the total probability for the ith Rupture Source above the given mag 
	 * (as computed the last time getTimeIndependentSources(*) or getTimeDependentSources(*) was called).
	 * @param ithRup
	 * @return
	 */
	public double getRupSourceProbAboveMag(int ithRup, double mag, Region region) { 
		if (!this.rupSrcMapping.containsKey(ithRup)) return 0;
		int srcIndex = rupSrcMapping.get(ithRup);
		return sourceList.get(srcIndex).computeTotalProbAbove(mag, region);
	}
	
	/**
	 * This returns the approximate total probability for the ith Rupture Source above the given mag 
	 * (as computed the last time getTimeIndependentSources(*) or getTimeDependentSources(*) was called).
	 * It calls the computeApproxTotalProbAbove of ProbEqkSource (instead of computeTotalProbAbove method)
	 * @param ithRup
	 * @return
	 */
	public double getRupSourceApproxProbAboveMag(int ithRup, double mag, Region region) { 
		if (!this.rupSrcMapping.containsKey(ithRup)) return 0;
		int srcIndex = rupSrcMapping.get(ithRup);
		return sourceList.get(srcIndex).computeApproxTotalProbAbove(mag, region);
	}
	
	/**
	 * This returns the total probability for the ith Rupture Source divided by the Possion Prob
	 * (as computed the last time getTimeIndependentSources(*) or getTimeDependentSources(*) was called).
	 * @param ithRup
	 * @return
	 */
	public double getRupSourcProbGain(int ithRup) { return rupGain[ithRup]; }

	/**
	 * This returns the total probability for the ith Segment divided by the Poisson Prob
	 * (as computed the last time getTimeIndependentSources(*) or getTimeDependentSources(*) was called).
	 * @param ithRup
	 * @return
	 */
	public double getSegProbGain(int ithSeg) { return segGain[ithSeg]; }

	/**
	 * This returns the total probability for the ith Segment
	 * (as computed the last time getTimeIndependentSources(*) or getTimeDependentSources(*) was called).
	 * @param ithRup
	 * @return
	 */
	public double getSegProb(int ithSeg) { return segProb[ithSeg]; }

	/**
	 * This returns the aperiodicity for the ith Segment
	 * (as specified the last time getTimeDependentSources(*) was called).  Double.NaN is return
	 * if getTimeIndependentSources(*) was called last.
	 * @param ithRup
	 * @return
	 */
	public double getSegAperiodicity(int ithSeg) { 
		if(isTimeDeptendent)
			return segAperiodicity[ithSeg];
		else
			return Double.NaN;
	}

	/**
	 * This returns the time since last event for the ith Segment
	 * (as specified the last time getTimeDependentSources(*) was called).  Double.NaN is return
	 * if getTimeIndependentSources(*) was called last.
	 * @param ithRup
	 * @return
	 */
	public double getSegTimeSinceLast(int ithSeg) {
		if(isTimeDeptendent)
			return segTimeSinceLast[ithSeg];
		else
			return Double.NaN;
	}

	
	/*  NO LONGER NEEDED ??????????
	public double[] getWG02_RupProbs(double duration, double startYear, double aperiodicity, boolean applySegVariableAperiodicity) {
		segTimeSinceLast = new double[num_seg];
		segAperiodicity = new double[num_seg];
		for(int i=0;i<num_seg;i++) {
			segTimeSinceLast[i] = startYear-this.segmentData.getSegCalYearOfLastEvent(i);
			segAperiodicity[i] = this.segmentData.getSegAperiodicity(i);
			if(Double.isNaN(segAperiodicity[i])) segAperiodicity[i] = aperiodicity;
		}
		if(applySegVariableAperiodicity) {
			return WG02_QkProbCalc.getRupProbs(finalSegRate, totRupRate, getFinalSegMoRate(), segAperiodicity, 
					segTimeSinceLast, duration, rupInSeg);			
		} else {
			return WG02_QkProbCalc.getRupProbs(finalSegRate, totRupRate, getFinalSegMoRate(), aperiodicity, 
					segTimeSinceLast, duration, rupInSeg);			
		}
	}

	
	public double[] getWG02_SegProbs(double duration, double startYear, double aperiodicity, boolean applySegVariableAperiodicity) {
		double[] segTimeSinceLast = new double[num_seg];
		double[] segAlpha = new double[num_seg];
		for(int i=0;i<num_seg;i++) {
			segTimeSinceLast[i] = startYear-this.segmentData.getSegCalYearOfLastEvent(i);
			segAlpha[i] = this.segmentData.getSegAperiodicity(i);
			if(Double.isNaN(segAlpha[i])) segAlpha[i] = aperiodicity;
		}
		if(applySegVariableAperiodicity) {
			return WG02_QkProbCalc.getSegProbs(finalSegRate, segAlpha, segTimeSinceLast, duration);
		} else {
			return WG02_QkProbCalc.getSegProbs(finalSegRate, aperiodicity, segTimeSinceLast, duration);
		}
	}
*/
	
	/**
	 * Get NSHMP Source File String. 
	 * This method is needed to create file for NSHMP. 
	 * 
	 * @return
	 */
	public String getNSHMP_SrcFileString() {
		boolean localDebug = true;
		StringBuffer strBuffer = new StringBuffer("");
		ArrayList<FaultRuptureSource> sourceList = getTimeIndependentSources(1.0);
		int srcIndex=0;
		for(int rupIndex=0; rupIndex<num_rup; ++rupIndex) {
			if (!this.rupSrcMapping.containsKey(rupIndex)) continue; // if this rupture does not exist in the list
			FaultRuptureSource faultRupSrc = this.sourceList.get(srcIndex++);
			strBuffer.append("1\t"); // char MFD
			double rake = faultRupSrc.getRupture(0).getAveRake();
			double wt = 1.0;
			String rakeStr = "";
			if((rake>=-45 && rake<=45) || rake>=135 || rake<=-135) rakeStr="1"; // Strike slip
			else if(rake>45 && rake<135) rakeStr="2"; // Reverse
			else if(rake>-135 && rake<-45) rakeStr="3"; // Normal
			else throw new RuntimeException("Invalid Rake:"+rake+", index="+rupIndex+", name="+getLongRupName(rupIndex));
			strBuffer.append(rakeStr+"\t"+"1"+"\t"+segmentData.getFaultName()+";"+this.getLongRupName(rupIndex)+"\n");
			// get the rate needed by NSHMP code (rate assuming no aleatory uncertainty)
			double fixRate = rupMoRate[rupIndex]/MomentMagCalc.getMoment(rupMeanMag[rupIndex]);
			strBuffer.append((float)this.getRupMeanMag(rupIndex)+"\t"+(float)fixRate+"\t"+wt+"\n");
			EvenlyGriddedSurfFromSimpleFaultData surface = (EvenlyGriddedSurfFromSimpleFaultData)faultRupSrc.getSourceSurface();
			// dip, Down dip width, upper seismogenic depth, rup Area
			strBuffer.append((float)surface.getAveDip()+"\t"+(float)surface.getSurfaceWidth()+"\t"+
					(float)surface.getUpperSeismogenicDepth()+"\t"+(float)surface.getSurfaceLength()+"\n");
			FaultTrace faultTrace = surface.getFaultTrace();
			// All fault trace locations
			strBuffer.append(faultTrace.getNumLocations()+"\n");
			for(int locIndex=0; locIndex<faultTrace.getNumLocations(); ++locIndex)
				strBuffer.append(faultTrace.get(locIndex).getLatitude()+"\t"+
						faultTrace.get(locIndex).getLongitude()+"\n");
			// this is to make sure things look good
			if(localDebug){
				System.out.println(getLongRupName(rupIndex)+"\t"+
						(float)getRupMeanMag(rupIndex)+"\t"+
						(float)getRupRateSolution(rupIndex)+"\t"+
						(float)getRupRate(rupIndex)+"\t"+
						(float)(getRupRateSolution(rupIndex)/getRupRate(rupIndex))+"\t"+
						magAreaRel.getName()+"\t"+
						aPrioriRupWt);
			}
		}
		return strBuffer.toString();
	}
	
	
	/**
	 * Get segment indices for this particular rupture index
	 * 
	 * @param rupIndex
	 * @return
	 */
	private int[] getSegmentsInRup(int rupIndex) {
		// find the segments participating in this rupture
		ArrayList<Integer> segs = new ArrayList<Integer>();
		for(int segIndex=0; segIndex<this.num_seg; ++segIndex) 
			if(this.rupInSeg[segIndex][rupIndex]==1) segs.add(segIndex);
		// convert ArrayList to int[]
		int[] segArray = new int[segs.size()];
		for(int i=0; i<segArray.length; ++i) segArray[i] = segs.get(i);
		return segArray;
	}
	
	/**
	 * Computer Final Slip Rate for each segment (& aPrioriSegSlipRate)
	 *
	 */
	private void computeFinalSegSlipRate() {
		this.finalSegSlipRate = new double[num_seg];
		this.aPrioriSegSlipRate = new double[num_seg];
		for(int seg=0; seg < num_seg; seg++) {
			finalSegSlipRate[seg] = 0;
			aPrioriSegSlipRate[seg] = 0;
			for(int rup=0; rup < num_rup; rup++) {
				finalSegSlipRate[seg] += totRupRate[rup]*segSlipInRup[seg][rup];
				aPrioriSegSlipRate[seg] += aPrioriRupRates[rup].getValue()*segSlipInRup[seg][rup];
			}
		}
	}
	
	
	
	public final static ArrayList getSupportedSlipModels() {
		ArrayList models = new ArrayList();
		models.add(CHAR_SLIP_MODEL);
		models.add(UNIFORM_SLIP_MODEL);
		models.add(WG02_SLIP_MODEL);
		models.add(TAPERED_SLIP_MODEL);

		return models;
	}
	
	/**
	 * Moment rate reduction
	 * 
	 * @return
	 */
	public double getMoRateReduction() {
		return this.moRateReduction;
	}
	
	/**
	 * This computes rupture magnitudes assuming characteristic slip (not an M(A) relationship).
	 * This uses segment rates implied by a-priori model (not segmentData.getSegRateConstraints())
	 * and uses the version that includes the min-rate constraint (also uses segRateFromAprioriWithMinRateConstr).
	 *
	 */
	private void getRupMeanMagsAssumingCharSlip() {
		rupMeanMag = new double[num_rup];
		rupMeanMo = new double[num_rup];
		double area, slip;
		for(int rup=0; rup<num_rup; rup++){
			for(int seg=0; seg < num_seg; seg++) {
				if(rupInSeg[seg][rup]==1) { // if this rupture is included in this segment	
					area = segmentData.getSegmentArea(seg);
					slip = (segmentData.getSegmentSlipRate(seg)/segRateFromAprioriWithMinRateConstr[seg])*(1-moRateReduction);
					rupMeanMo[rup] += area*slip*FaultMomentCalc.SHEAR_MODULUS;
				}
			}
			// reduce moment by aveSlipCorr to reduce mag, so that ave slip in final MFD is correct
			rupMeanMag[rup] = MomentMagCalc.getMag(rupMeanMo[rup]/aveSlipCorr);	//
		}
	}
	
	
	private final static int[][] getRupInSegMatrix(int num_seg) {
		
		int num_rup = num_seg*(num_seg+1)/2;
		int[][] rupInSeg = new int[num_seg][num_rup];
		
		int n_rup_wNseg = num_seg;
		int remain_rups = num_seg;
		int nSegInRup = 1;
		int startSeg = 0;
		for(int rup = 0; rup < num_rup; rup += 1) {
			for(int seg = startSeg; seg < startSeg+nSegInRup; seg += 1)
				rupInSeg[seg][rup] = 1;
			startSeg += 1;
			remain_rups -= 1;
			if(remain_rups == 0) {
				startSeg = 0;
				nSegInRup += 1;
				n_rup_wNseg -= 1;
				remain_rups = n_rup_wNseg;
			}
		}
		
		// check result
		/*
		if(D) {
			for(int seg = 0; seg < num_seg; seg+=1) {
				System.out.print("\n");
				for(int rup = 0; rup < num_rup; rup += 1)
					System.out.print(rupInSeg[seg][rup]+"  ");
			}
			System.out.print("\n");
		}
		*/
		
		return rupInSeg;
	}
	
	
	private final static int[][] getSanJacintoRupInSeg() {
		int num_seg = 7;
		int num_rup = 25;
		int[][] sjfRupInSeg = {
				  // 1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5
					{1,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1,1,0,0,1,0,1}, // seg 1
					{0,1,0,0,0,0,0,1,1,0,0,0,0,1,1,1,0,0,1,1,1,0,1,1,1}, // seg 2
					{0,0,1,0,0,0,0,0,1,1,1,0,0,1,1,1,1,0,1,1,1,1,1,1,1}, // seg 3
					{0,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0}, // seg 4
					{0,0,0,0,1,0,0,0,0,0,1,1,0,0,0,1,1,1,0,1,1,1,1,1,1}, // seg 5
					{0,0,0,0,0,1,0,0,0,0,0,1,1,0,0,0,1,1,0,0,1,1,1,1,1}, // seg 6
					{0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0,0,0,1,0,1,1}, // seg 7
			  	};
		
		// check result
		/*
		if(D) {
			for(int seg = 0; seg < num_seg; seg+=1) {
				System.out.print("\n");
				for(int rup = 0; rup < num_rup; rup += 1)
					System.out.print(sjfRupInSeg[seg][rup]+"  ");
			}
		}
		*/
		
		return sjfRupInSeg;
	}
	
	
	public double getTotalMoRateFromRups() {
		return totalMoRateFromRups;
	}
	
	public double getTotalMoRateFromSummedMFD() {
		return summedMagFreqDist.getTotalMomentRate();
	}
	
	
	/**
	 * Get total rupture rate of the ith char rupture (the total of the final MFD)
	 * 
	 * @param ithRup
	 * @return
	 */
	public double getRupRate(int ithRup) {
		return totRupRate[ithRup];
	}
	
	/**
	 * Get total rupture rate of the ith char rupture obtained from the inversion
	 * (not the total from the MFD)
	 * 
	 * @param ithRup
	 * @return
	 */
	public double getRupRateSolution(int ithRup) {
		return rupRateSolution[ithRup];
	}
	
	
	/**
	 * Difference in final Rup rate and aPrioriRate.
	 * It is calculated as (finalRate-AprioriRate)/Max(FinalRate,AprioriRate)
	 * @param ithRup
	 * @return
	 */
	public double getRupRateResid(int ithRup) {
		// find the max between apriori and final rupture rates
		double max = totRupRate[ithRup];
		if(max<aPrioriRupRates[ithRup].getValue()) max = aPrioriRupRates[ithRup].getValue();
		// if final and apriori rates are 0, return 0
		if(max<=MIN_RUP_RATE) return 0;  // this MRI exceeds the age of the earth!
		return (totRupRate[ithRup]-aPrioriRupRates[ithRup].getValue())/max;
	}
	
	/**
	 * Get rupture moment rate of the ith char rupture
	 * 
	 * @param ithRup
	 * @return
	 */
	public double getRupMoRate(int ithRup) {
		return rupMoRate[ithRup];
	}
	
	/**
	 * Get a priori rupture rate of the ith char rupture
	 * 
	 * @param ithRup
	 * @return
	 */
	public double getAPrioriRupRate(int ithRup) {
		return aPrioriRupRates[ithRup].getValue();
	}
	
	
	/**
	 * Get total Mag Freq dist for ruptures (including floater)
	 *
	 */
	public IncrementalMagFreqDist getTotalRupMFD() {
		return this.summedMagFreqDist;
	}
	
	
	/**
	 * This returns the final, implied slip rate for each segment
	 */
	/*public double getFinalAveSegSlipRate(int ithSegment) {
		ArbDiscrEmpiricalDistFunc segmenstSlipDist = getSegmentSlipDist(ithSegment);
		double slipRate=0;
		for(int i=0; i<segmenstSlipDist.getNum(); ++i)
			slipRate+=segmenstSlipDist.getX(i)*segmenstSlipDist.getY(i);
		return slipRate;
	}*/
	
	/**
	 * This returns the final implied slip rate for each segment
	 */
	public double getFinalSegSlipRate(int ithSegment) {
		return this.finalSegSlipRate[ithSegment];
	}
	
	
	/**
	 * This returns the segment slip rate implied by the a-priori model
	 */
	public double get_aPrioriSegSlipRate(int ithSegment) {
		return this.aPrioriSegSlipRate[ithSegment];
	}
	
	
	/**
	 * Get final rate of events for ith segment
	 * 
	 * @param ithSegment
	 * @return
	 */
	public double getSegRateFromAprioriRates(int ithSegment) {
		return segRateFromApriori[ithSegment];
	}
	
	/**
	 * Get final rate of events for ith segment
	 * 
	 * @param ithSegment
	 * @return
	 */
	public double getFinalSegmentRate(int ithSegment) {
		return finalSegRate[ithSegment];
	}
	
	/**
	 * Get the final Slip Distribution for the ith segment
	 * 
	 * @param ithSegment
	 * @return
	 */
	public ArbDiscrEmpiricalDistFunc getSegmentSlipDist(int ithSegment) {
		return this.segSlipDist[ithSegment];
	}
	
	
	/**
	 * Get mean mag for ith Rupture
	 * @param ithRup
	 * @return
	 */
	public double getRupMeanMag(int ithRup) {
		return rupMeanMag[ithRup];
	}
	
	/**
	 * Get area for ith Rupture
	 * @param ithRup
	 * @return
	 */
	public double getRupArea(int ithRup) {
		return rupArea[ithRup];
	}
	
	
	/**
	 * Get the long name for ith Rup (the segment names combined)
	 * @param ithRup
	 * @return
	 */
	public String getLongRupName(int ithRup) {
		return rupNameLong[ithRup];
	}
	
	
	/**
	 * Get the short name for ith Rup (segment numbers combined; e.g., "123" is the
	 * rupture that involves segments 1, 2, and 3).
	 * @param ithRup
	 * @return
	 */
	public String getShortRupName(int ithRup) {
		return rupNameShort[ithRup];
	}
	
	
	/**
	 * Compute the slip distribution for each segment
	 * The average slip for each event is partitioned among the different segments
	 * according to segRupSlipFactor.
	 */
	private void computeSegSlipDist(double[][] segRupSlipFactor) {
		segSlipDist = new ArbDiscrEmpiricalDistFunc[num_seg];
		for(int seg=0; seg<num_seg; ++seg) {
			segSlipDist[seg]=new ArbDiscrEmpiricalDistFunc();
			// Add the rates of all ruptures which are part of a segment
			for(int rup=0; rup<num_rup; rup++)
				if(rupInSeg[seg][rup]==1) {
					for(int i=0; i<rupSlipDist[rup].getNum(); ++i)
						segSlipDist[seg].set(segRupSlipFactor[rup][seg]*rupSlipDist[rup].getX(i), 
								rupSlipDist[rup].getY(i));
				}
		}
	}
	
	/**
	 * This returns a "segSlipInRup[seg][rup]" matrix giving the average slip on each segment for each rupture
	 * @return
	 */
	public double[][] getSegSlipInRupMatrix() { return segSlipInRup; }
	
	/**
	 * This creates the segSlipInRup (Dsr) matrix based on the value of slipModelType.
	 * This slips are in meters.
	 *
	 */
	private void computeSegSlipInRupMatrix() {
		segSlipInRup = new double[num_seg][num_rup];
		
		// for case segment slip is independent of rupture, and equal to slip-rate * MRI
		// note that we're using the event rates that include the min constraint (segRateFromAprioriWithMinRateConstr)
		if(slipModelType.equals(CHAR_SLIP_MODEL)) {
			for(int seg=0; seg<num_seg; seg++) {
				double segCharSlip = segmentData.getSegmentSlipRate(seg)*(1-moRateReduction)/segRateFromAprioriWithMinRateConstr[seg];
				for(int rup=0; rup<num_rup; ++rup) {
					segSlipInRup[seg][rup] = rupInSeg[seg][rup]*segCharSlip;
				}
			}
		}
		// for case where ave slip computed from mag & area, and is same on all segments 
		else if (slipModelType.equals(UNIFORM_SLIP_MODEL)) {
			for(int rup=0; rup<num_rup; ++rup) {
				double aveSlip = rupMeanMo[rup]/(rupArea[rup]*FaultMomentCalc.SHEAR_MODULUS);  // inlcudes aveSlipCorr
				for(int seg=0; seg<num_seg; seg++) {
					segSlipInRup[seg][rup] = rupInSeg[seg][rup]*aveSlip;
				}
			}
		}
		// this is the model where seg slip is proportional to segment slip rate 
		// (bumped up or down based on ratio of seg slip rate over wt-ave slip rate (where wts are seg areas)
		else if (slipModelType.equals(WG02_SLIP_MODEL)) {
			for(int rup=0; rup<num_rup; ++rup) {
				double aveSlip = rupMeanMo[rup]/(rupArea[rup]*FaultMomentCalc.SHEAR_MODULUS);    // inlcudes aveSlipCorr
				double totMoRate = 0;	// a proxi for slip-rate times area
				double totArea = 0;
				for(int seg=0; seg<num_seg; seg++) {
					if(rupInSeg[seg][rup]==1) {
						totMoRate += segmentData.getSegmentMomentRate(seg); // a proxi for Vs*As
						totArea += segmentData.getSegmentArea(seg);
					}
				}
				for(int seg=0; seg<num_seg; seg++) {
					segSlipInRup[seg][rup] = aveSlip*rupInSeg[seg][rup]*segmentData.getSegmentMomentRate(seg)*totArea/(totMoRate*segmentData.getSegmentArea(seg));
				}
			}
		}
		else if (slipModelType.equals(TAPERED_SLIP_MODEL)) {
			// note that the ave slip is partitioned by area, not length; this is so the final model is moment balanced.
			mkTaperedSlipFuncs();
			for(int rup=0; rup<num_rup; ++rup) {
				double aveSlip = rupMeanMo[rup]/(rupArea[rup]*FaultMomentCalc.SHEAR_MODULUS);    // inlcudes aveSlipCorr
				double totRupArea = 0;
				// compute total rupture area
				for(int seg=0; seg<num_seg; seg++) {
					if(rupInSeg[seg][rup]==1) {
						totRupArea += segmentData.getSegmentArea(seg);
					}
				}
				double normBegin=0, normEnd, scaleFactor;
				for(int seg=0; seg<num_seg; seg++) {
					if(rupInSeg[seg][rup]==1) {
						normEnd = normBegin + segmentData.getSegmentArea(seg)/totRupArea;
						// fix normEnd values that are just past 1.0
						if(normEnd > 1 && normEnd < 1.00001) normEnd = 1.0;
						scaleFactor = taperedSlipCDF.getInterpolatedY(normEnd)-taperedSlipCDF.getInterpolatedY(normBegin);
						scaleFactor /= (normEnd-normBegin);
						segSlipInRup[seg][rup] = aveSlip*scaleFactor;
						normBegin = normEnd;
					}
				}
				if(D) { // check results
					double d_aveTest=0;
					for(int seg=0; seg<num_seg; seg++)
						d_aveTest += segSlipInRup[seg][rup]*segmentData.getSegmentArea(seg)/totRupArea;
					System.out.println("AveSlipCheck: " + (float) (d_aveTest/aveSlip));
				}
			}
		}
		else throw new RuntimeException("slip model not supported");
	}
	
	/*
	 * This computes the WG02 increase/decrease factor for the ave slip on a segment relative to the
	 * ave slip for the entire rupture (based on moment rates and areas).  The idea being, 
	 * for example, that if only full fault rupture is allowed on a fuult where the segments 
	 * have different slip rates, then the amount of slip on each segment for that rupture
	 * must vary to match the long-term slip rates).
	 * @param segAveSlipRate
	 
	private double[][] getWG02_SegRupSlipFactor() {
		double[][] segRupSlipFactor = new double[num_rup][num_seg];
		for(int rup=0; rup<num_rup; ++rup) {
			double totMoRate = 0;
			double totArea = 0;
			for(int seg=0; seg<num_seg; seg++) {
				if(rupInSeg[seg][rup]==1) {
					totMoRate += segmentData.getSegmentMomentRate(seg); // this is a proxi for Vs*As
					totArea += segmentData.getSegmentArea(seg);
				}
			}
			for(int seg=0; seg<num_seg; seg++) {
				segRupSlipFactor[rup][seg] = rupInSeg[seg][rup]*segmentData.getSegmentMomentRate(seg)*totArea/(totMoRate*segmentData.getSegmentArea(seg));
			}
		}
		return segRupSlipFactor;
	}
	*/
	
	/**
	 * This computes the rate of discrete ave-slips for each rupture (rupSlipDist) 
	 * by converting the x-axis magnitudes (of the rupture MFD) to slip amounts.
	 * 
	 */
	private void computeRupSlipDist() {
		rupSlipDist = new ArbitrarilyDiscretizedFunc[num_rup];
		for(int rup=0; rup<num_rup; ++rup) {
			rupSlipDist[rup] = new ArbitrarilyDiscretizedFunc();
			for(int imag=0; imag<rupMagFreqDist[rup].getNum(); ++imag) {
				if(rupMagFreqDist[rup].getY(imag)==0) continue; // if rate is 0, do not find the slip for this mag
				double moment = MomentMagCalc.getMoment(rupMagFreqDist[rup].getX(imag));
				double slip = FaultMomentCalc.getSlip(rupArea[rup], moment);
				rupSlipDist[rup].set(slip, rupMagFreqDist[rup].getY(imag));
			}
		}
	}
	
	/**
	 * Compute the rate for all segments (segRate[]) by summing totRupRate[rup] over all ruptures
	 * that involve each segment.
	 *  
	 */
	private void computeFinalSegRates() {
		finalSegRate = new double[num_seg];
		for(int seg=0; seg<num_seg; ++seg) {
			finalSegRate[seg]=0.0;
			// Sum the rates of all ruptures which are part of a segment
			for(int rup=0; rup<num_rup; rup++) 
				if(rupInSeg[seg][rup]==1) finalSegRate[seg]+=totRupRate[rup];
		}
	}
	
	
	/**
	 * Compute the rate of each segment from the a priori rupture rates 
	 * (e.g., used to check whether segments a priori rates are consistent with
	 * the seg rates in FaultSegmentData).
	 *  
	 */
	private void computeSegRatesFromAprioriRates() {
		segRateFromApriori = new double[num_seg];
		segRateFromAprioriWithMinRateConstr = new double[num_seg];
		for(int seg=0; seg<num_seg; ++seg) {
			segRateFromApriori[seg]=0.0;
			// Sum the rates of all ruptures which are part of a segment
			for(int rup=0; rup<num_rup; rup++)
				if(rupInSeg[seg][rup]==1) {
					segRateFromApriori[seg]+=aPrioriRupRates[rup].getValue();
					segRateFromAprioriWithMinRateConstr[seg]+=Math.max(aPrioriRupRates[rup].getValue(),minRates[rup]);
				}
		}
	}

	/**
	 * This computes the total final probability of a segment having an event larger than
	 * or equal to the given magnitude.  Note that even if mag is set to low value, the result
	 * here is different than that returned by getSegProb(seg) due to the internal inconsistency of the model
	 */
	public double computeSegProbAboveMag(double mag, int segIndex) {
		double segProbAboveMag=1;
		for(int rup=0; rup < num_rup; rup++)
			if (rupSrcMapping.containsKey(rup))
				if(rupInSeg[segIndex][rup]==1) {
					FaultRuptureSource src = sourceList.get(rupSrcMapping.get(rup));
					segProbAboveMag *= (1-src.computeTotalProbAbove(mag));
				}
		return 1.0-segProbAboveMag;
	}

	
	
	
	/**
	 * This gives an array of short names for each rupture (this is static so that GUIs can get this info
	 * without having to instantiate the object).  The short names are defined as the combination of
	 * segment numbers involved in the rupture (e.g., "23" is the rupture that involves segments 2 and 3).
	 * Here, segment indices start at 1 (not 0).
	 */
	public final static String[] getAllShortRuptureNames(FaultSegmentData segmentData) {
		int nSeg = segmentData.getNumSegments();
		int nRup = getNumRuptureSurfaces(segmentData);
		int[][] rupInSeg;
		// get the RupInSeg Matrix for the given number of segments
		if(segmentData.getFaultName().equals("San Jacinto"))
			rupInSeg = getSanJacintoRupInSeg();	// special case for this branching fault
		else
			rupInSeg = getRupInSegMatrix(nSeg);
		String[] rupNameShort = new String[nRup];
		for(int rup=0; rup<nRup; rup++){
			boolean isFirst = true;
			for(int seg=0; seg < nSeg; seg++) {
				if(rupInSeg[seg][rup]==1) { // if this rupture is included in this segment
					if(isFirst) { // append the section name to rupture name
						rupNameShort[rup] = ""+(seg+1);
						isFirst = false;
					} else {
						rupNameShort[rup] += (seg+1);
					}
				}
			}
		}
		return rupNameShort;
	}
	
	
	
	/**
	 * This gives an array of long names for each rupture (this is static so that GUIs can get this info
	 * without having to instantiate the object).  The long names are defined as the combination of
	 * segment names (combined with "; ").
	 */
	public final static String[] getAllLongRuptureNames(FaultSegmentData segmentData) {
		int nSeg = segmentData.getNumSegments();
		int nRup = getNumRuptureSurfaces(segmentData);
		int[][] rupInSeg;
		// get the RupInSeg Matrix for the given number of segments
		if(segmentData.getFaultName().equals("San Jacinto"))
			rupInSeg = getSanJacintoRupInSeg();	// special case for this branching fault
		else
			rupInSeg = getRupInSegMatrix(nSeg);
		String[] rupNameLong = new String[nRup];
		for(int rup=0; rup<nRup; rup++){
			boolean isFirst = true;
			for(int seg=0; seg < nSeg; seg++) {
				if(rupInSeg[seg][rup]==1) { // if this rupture is included in this segment
					if(isFirst) { // append the section name to rupture name
						rupNameLong[rup] = segmentData.getSegmentName(seg);
						isFirst = false;
					} else {
						rupNameLong[rup] += "+"+segmentData.getSegmentName(seg);
					}
				}
			}
		}
		return rupNameLong;
	}
	
	
	
	/**
	 * compute rupArea (meters)
	 */
	private void computeRupAreas() {
		rupArea = new double[num_rup];
		for(int rup=0; rup<num_rup; rup++){
			rupArea[rup] = 0;
			for(int seg=0; seg < num_seg; seg++) {
				if(rupInSeg[seg][rup]==1) { // if this rupture is included in this segment	
					rupArea[rup] += segmentData.getSegmentArea(seg);
				}
			}
		}
	}
	

	
	/**
	 * @return the total num of ruture sourcs
	 */
	public int getNumRupSources() {
		return num_rup;
	}
	
	/**
	 * This static method can be used (e.g., in GUIs) to get the number of ruptures
	 * without having to instantiate the object.
	 * @param segmentData
	 * @return
	 */
	public final static int getNumRuptureSurfaces(FaultSegmentData segmentData) {
		int nSeg = segmentData.getNumSegments();
		if(segmentData.getFaultName().equals("San Jacinto"))
			return 25;
		else
			return nSeg*(nSeg+1)/2;
	}

		/**
	 * set the name of this class
	 *
	 * @return
	 */
	public void setName(String name) {
		NAME = name;
	}
	
	/**
		 * Return the fault segment data
		 * 
		 * @return
		 */
		public FaultSegmentData getFaultSegmentData() {
			return this.segmentData;
		}

	/**
	 * get the name of this class
	 *
	 * @return
	 */
	public String getName() {
		return NAME;
	}
	
	
	/**
	 * This gets the non-negative least squares solution for the matrix C
	 * and data vector d.
	 * @param C
	 * @param d
	 * @return
	 */
	private static double[] getNNLS_solution(double[][] C, double[] d) {

		int nRow = C.length;
		int nCol = C[0].length;
		
		double[] A = new double[nRow*nCol];
		double[] x = new double[nCol];
		
		int i,j,k=0;
	
		if(MATLAB_TEST) {
			System.out.println("C = [");
			for(i=0; i<nRow;i++) {
				for(j=0;j<nCol;j++) 
					System.out.print(C[i][j]+"   ");
				System.out.print("\n");
			}
			System.out.println("];");
			System.out.println("d = [");
			for(i=0; i<nRow;i++)
				System.out.println(d[i]);
			System.out.println("];");
		}
/////////////////////////////////////
		
		for(j=0;j<nCol;j++) 
			for(i=0; i<nRow;i++)	{
				A[k]=C[i][j];
				k+=1;
			}
		nnls.update(A,nRow,nCol);
		
		boolean converged = nnls.solve(d,x);
		if(!converged)
			throw new RuntimeException("ERROR:  NNLS Inversion Failed");
		
		if(MATLAB_TEST) {
			System.out.println("x = [");
			for(i=0; i<x.length;i++)
				System.out.println(x[i]);
			System.out.println("];");
			System.out.println("max(abs(x-lsqnonneg(C,d)))");
		}
		
		return x;
	}
	
	
	/**
	 * This makes a tapered slip function based on the [Sin(x)]^0.5 fit of 
	 * Biasi & Weldon (in prep; pesonal communication), which is based on  
	 * the data comilation of Biasi & Weldon (2006, "Estimating Surface  
	 * Rupture Length and Magnitude of Paleoearthquakes from Point 
	 * Measurements of Rupture Displacement", Bull. Seism. Soc. Am. 96, 
	 * 1612-1623, doi: 10.1785/0120040172 E)
	 *
	 */
	private static void mkTaperedSlipFuncs() {
		
		// only do if another instance has not already done this
		if(taperedSlipCDF != null) return;
		
		taperedSlipCDF = new EvenlyDiscretizedFunc(0, 51, 0.02);
		taperedSlipPDF = new EvenlyDiscretizedFunc(0, 51, 0.02);
		double x,y, sum=0;
		int num = taperedSlipPDF.getNum();
		for(int i=0; i<num;i++) {
			x = taperedSlipPDF.getX(i);
			// y = Math.sqrt(1-(x-0.5)*(x-0.5)/0.25);
			y = Math.pow(Math.sin(x*Math.PI), 0.5);
			taperedSlipPDF.set(i,y);
			sum += y;
		}

		// now make final PDF & CDF
		y=0;
		for(int i=0; i<num;i++) {
				y += taperedSlipPDF.getY(i);
				taperedSlipCDF.set(i,y/sum);
				taperedSlipPDF.set(i,taperedSlipPDF.getY(i)/sum);
//				System.out.println(taperedSlipCDF.getX(i)+"\t"+taperedSlipPDF.getY(i)+"\t"+taperedSlipCDF.getY(i));
		}
	}
	
	/**
	 * Set the aveSlipCorr based on current magSigma and magTruncLevel.  
	 * aveSlipCorr is the ratio of the average slip for the MFD divided by the slip of the average magnitude.
	 * double aveSlipCorr
	 *
	 */
	private void setAveSlipCorrection() {
		if(magSigma == 0 || magTruncLevel == 0)
			aveSlipCorr = 1.0;
		else {
			// compute an average over a range of magitudes spanning DELTA_MAG
			double sum=0, temp;
			int num=0;
			for(double mag = 7.0; mag <7.0+DELTA_MAG-0.001; mag +=0.01) {
				GaussianMagFreqDist magFreqDist = new GaussianMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG, mag, magSigma, 1.0, magTruncLevel, 2);
				temp = magFreqDist.getTotalMomentRate()/(magFreqDist.getTotalIncrRate()*MomentMagCalc.getMoment(mag));
				num +=1;
				sum += temp;
				// System.out.println("ratio: "+ temp + "  "+mag);
			}
			aveSlipCorr = sum/(double)num;
		}
	}
	
	/**
	 * It creates the matrix and data vector for testing the numerical matrix limits
	 * for NNLS
	 * 
	 * @param num
	 */
	private static void testNNLS_SolutionLimits(int num) {
		// data vector
		double [] d= new double[num];
		d[0]=1;
		for(int i=1; i<num; ++i) d[i] = i;
		// matrix C
		double [][]C = new double[num][num];
		// first element is 1
		C[0][0]=1;
		for(int i=1; i<num-1; ++i)  C[0][i] = 0;
			
		for(int i=0; i<(num-1); ++i) {
			C[i+1][i] = -1;
			C[i+1][i+1] = 1;
		}
		double[] solution = getNNLS_solution(C, d);
		for(int i=0; i<solution.length; ++i)
			System.out.println(solution[i]);
	}
	
	public static void main(String[] args) {
		
		
	// TEST THE  LIMITS of NNLS SOLUTION	
		testNNLS_SolutionLimits(5000);
		
		
// ******* THIS REPRODUCES THE 2-SEGMENT EXAMPLE IN WG02 APPENDIX G ***************
		//  (slight diff likely due to the rounding of their mags & how that propagates)
		
		/*String[] segNames = new String[2];
		segNames[0] = "Seg1";
		segNames[1] = "Seg2";
		// sectionToSegmentData - an ArrayList containing N ArrayLists (one for each segment), 
	  	// where the arrayList for each segment contains some number of FaultSectionPrefData objects
		ArrayList sectionToSegmentData = new ArrayList();
		
		ArrayList faultSectDataList1 = new ArrayList();
		FaultSectionPrefData sectData1 = new FaultSectionPrefData();
		sectData1.setAseismicSlipFactor(0.0);
		sectData1.setAveDip(90);
		sectData1.setAveLongTermSlipRate(10);
		sectData1.setAveLowerDepth(15);
		sectData1.setAveUpperDepth(0);
		sectData1.setAveRake(0);
		FaultTrace faultTrace1 = new FaultTrace("trace1");
		Location loc1 = new Location(0,0,0);
		LocationVector dir = new LocationVector(0.0, 100, 0.0, 0.0);
		Location loc2 = LocationUtils.getLocation(loc1, dir);
		dir = new LocationVector(0.0, 50, 0.0, 0.0);
		Location loc3 = LocationUtils.getLocation(loc2, dir);
		faultTrace1.addLocation(loc1);
		faultTrace1.addLocation(loc2);
		System.out.println("faultTrace1 length = "+(float)faultTrace1.getTraceLength());
		sectData1.setFaultTrace(faultTrace1);
		sectData1.setSectionName("sect1");
		sectData1.setSectionName("s1");
		faultSectDataList1.add(sectData1);
		sectionToSegmentData.add(faultSectDataList1);

		ArrayList faultSectDataList2 = new ArrayList();
		FaultSectionPrefData sectData2 = new FaultSectionPrefData();
		sectData2.setAseismicSlipFactor(0.0);
		sectData2.setAveDip(90);
		sectData2.setAveLongTermSlipRate(10);
		sectData2.setAveLowerDepth(15);
		sectData2.setAveUpperDepth(0);
		sectData2.setAveRake(0);
		FaultTrace faultTrace2 = new FaultTrace("trace2");
		faultTrace2.addLocation(loc2);
		faultTrace2.addLocation(loc3);
		System.out.println("faultTrace2 length = "+(float)faultTrace2.getTraceLength());
		sectData2.setFaultTrace(faultTrace2);
		sectData2.setSectionName("sect2");
		sectData2.setSectionName("s2");
		faultSectDataList2.add(sectData2);
		sectionToSegmentData.add(faultSectDataList2);
		
		ArrayList<SegRateConstraint> segRateConstraints = new ArrayList();

		FaultSegmentData segData = new FaultSegmentData(
				sectionToSegmentData, 
				segNames, 
				true, 
				"WG02 Test", 
				segRateConstraints);

		System.out.println(segData.getSegmentName(0)+"\n\t"+
				segData.getSegmentSlipRate(0)+"\n\t"+
				segData.getSegmentLength(0)+"\n\t"+
				segData.getSegmentMomentRate(0)+"\n\t");
		System.out.println(segData.getSegmentName(1)+"\n\t"+
				segData.getSegmentSlipRate(1)+"\n\t"+
				segData.getSegmentLength(1)+"\n\t"+
				segData.getSegmentMomentRate(1)+"\n\t");
		
		PEER_testsMagAreaRelationship magAreaRel = new PEER_testsMagAreaRelationship();
		ValueWeight[] aPrioriRates= new ValueWeight[3];
		double w1 = 0.8;
		double w2 = 0.2;
		double rel1 = (w1/(w1+w1+w2)); 
		double rel2 = (w1/(w1+w1+w2));
		double rel3 = (w2/(w1+w1+w2));
		// totMoRate = r1*mo1+r2*mo2+r3*mo3 = totRate*(rel1*mo1+rel2*mo2+rel3*mo3)
		// totRate = totMoRate/(rel1*mo1+rel2*mo2+rel3*mo3)
		double totRate = (4.5+2.25)/(rel1*660  + rel2*240  + rel3*1200);
		double r1 = rel1*totRate; 
		double r2 = rel2*totRate;
		double r3 = rel3*totRate;
		
		System.out.println(r1/(r1+r2+r3)+"  "+r2/(r1+r2+r3) +"  "+r3/(r1+r2+r3));
		System.out.println(r1+"  "+r2 +"  "+r3);

		aPrioriRates[0] = new ValueWeight(r1,1);
		aPrioriRates[1] = new ValueWeight(r2,1);
		aPrioriRates[2] = new ValueWeight(r3,1);

		A_FaultSegmentedSourceGenerator src = new A_FaultSegmentedSourceGenerator(segData, magAreaRel,
				A_FaultSegmentedSourceGenerator.WG02_SLIP_MODEL, aPrioriRates, 0.12, 0.0, 0, 0, false,false,0,1e-7);

		System.out.println("MeanMags:\n\t"+
				(float)src.getRupMeanMag(0)+"\n\t"+
				(float)src.getRupMeanMag(1)+"\n\t"+
				(float)src.getRupMeanMag(2)+"\n\t");
		System.out.println("RupMoments:\n\t"+
				(float)MomentMagCalc.getMoment(src.getRupMeanMag(0))+"\n\t"+
				(float)MomentMagCalc.getMoment(src.getRupMeanMag(1))+"\n\t"+
				(float)MomentMagCalc.getMoment(src.getRupMeanMag(2))+"\n\t");
		System.out.println("RupRates:\n\t"+
				(float)src.getRupRateSolution(0)+"\n\t"+
				(float)src.getRupRateSolution(1)+"\n\t"+
				(float)src.getRupRateSolution(2)+"\n\t");
		totRate = src.getRupRateSolution(0)+src.getRupRateSolution(1)+src.getRupRateSolution(2);
		System.out.println("RelRupRates:\n\t"+
				(float)(src.getRupRateSolution(0)/totRate)+"\n\t"+
				(float)(src.getRupRateSolution(1)/totRate)+"\n\t"+
				(float)(src.getRupRateSolution(2)/totRate)+"\n\t");*/
		
// ****** END OF REPRODUCTION OF THE 2-SEGMENT EXAMPLE IN WG02 APPENDIX G ***********
		
		
		//setAveSlipCorrection();
		
		//mkTaperedSlipFuncs();
		
		/*
//		System.out.println("Starting - loading data");
		A_FaultsFetcher aFaultsFetcher = new A_FaultsFetcher();
		// Defomration model D2.1 ID =  42
		ArrayList aFaultSegmentData = aFaultsFetcher.getFaultSegmentDataList(42, true);
//		for(int i=0; i<aFaultSegmentData.size(); i++)
//			System.out.println(i+"  "+ ((FaultSegmentData)aFaultSegmentData.get(i)).getFaultName());
		FaultSegmentData segData = (FaultSegmentData) aFaultSegmentData.get(2);
//		System.out.println("Done getting data for "+segData.getFaultName());
		Ellsworth_B_WG02_MagAreaRel magAreaRel = new Ellsworth_B_WG02_MagAreaRel();
		ValueWeight[] aPrioriRates = aFaultsFetcher.getAprioriRupRates(segData.getFaultName(), 
				A_FaultsFetcher.GEOL_INSIGHT_RUP_MODEL);
//		System.out.println("now creating source");
		A_FaultSegmentedSource src = new A_FaultSegmentedSource(segData, magAreaRel,
				A_FaultSegmentedSource.WG02_SLIP_MODEL, aPrioriRates, 0.12, 2);
		*/
		
		/*
		double[][] C = {
		//_ rup  1,2,3,4,5,6,7,8,9,0,1,2,3,4,5
				{1,0,0,0,0,1,0,0,0,1,0,0,1,0,1},
				{0,1,0,0,0,1,1,0,0,1,1,0,1,1,1},
				{0,0,1,0,0,0,1,1,0,1,1,1,1,1,1},
				{0,0,0,1,0,0,0,1,1,0,1,1,1,1,1},
				{0,0,0,0,1,0,0,0,1,0,0,1,0,1,1},
		};
		final double[] d = {1/1.380,1/.250,1/.600,1/2.000,1/.9333333};  // AKA "b" vector		
		/*
		double[][] C = {
				{0.0372,0.2869},
			    {0.6861,0.7071},
			    {0.6233,0.6245},
			    {0.6344,0.6170},
			    };
		final double[] d = {0.8587,0.1781,0.0747,0.8405};  // AKA "b" vector		
		
		System.out.println("num rows  "+C.length);
		System.out.println("num cols  "+C[0].length);

		double[] x = getNNLS_solution(C,d);
		
		for(int i=0; i<x.length;i++)
			System.out.println(i+"  "+x[i]);
		*/

		
		/*
		A_FaultSegmentedSource.getSanJacintoRupInSeg();
		System.out.println(" ");
		A_FaultSegmentedSource.getRupInSegMatrix(2);
		System.out.println(" ");
		A_FaultSegmentedSource.getRupInSegMatrix(4);
		System.out.println(" ");
		A_FaultSegmentedSource.getRupInSegMatrix(6);
		System.out.println(" ");
		A_FaultSegmentedSource.getRupInSegMatrix(8);
		*/
		
	}
	

	
	/**
	 * Compute Normalized Segment Slip-Rate Residuals (where orig slip-rate and stddev are reduces by the fraction of moment rate removed)
	 *
	 */
	public double[] getNormModSlipRateResids() {
		int numSegments = getFaultSegmentData().getNumSegments();
		double[] normResids = new double[numSegments];
		// iterate over all segments
		double reduction = 1-getMoRateReduction();
		for(int segIndex = 0; segIndex<numSegments; ++segIndex) {
			normResids[segIndex] = getFinalSegSlipRate(segIndex)-getFaultSegmentData().getSegmentSlipRate(segIndex)*reduction;
			normResids[segIndex] /= (getFaultSegmentData().getSegSlipRateStdDev(segIndex)*reduction);
		}

	return normResids;
	}
	

	/**
	 * Compute Normalized Event-Rate Residuals
	 *
	 */
	public double[] getNormDataER_Resids() {
		int numSegments = this.getFaultSegmentData().getNumSegments();
		double[] normResids = new double[numSegments];
		// iterate over all segments
		for(int segIndex = 0; segIndex<numSegments; ++segIndex) {
			normResids[segIndex] = (getFinalSegmentRate(segIndex)-getFaultSegmentData().getSegRateMean(segIndex))/getFaultSegmentData().getSegRateStdDevOfMean(segIndex);
		}
		return normResids;
	}
	
	/**
	 * This returns the generalizeded prediction error as defined on page 54 of Menke's
	 * 1984 Book "Geophysical Data Analysis: Discrete Inverse Theory".
	 * @return
	 */
	public double getGeneralizedPredictionError() {
		return getNormModSlipRateError() + getNormDataER_Error() + getA_PrioriModelError();
	}
	
	/**
	 * Get the normalized slip rate error
	 * @return
	 */
	public double getNormModSlipRateError() {
		double totError = 0;
		double[] errors = getNormModSlipRateResids();
		for(int i=0;i<errors.length;i++)
			totError += errors[i]*errors[i];
		return totError;
	}
	
	/**
	 * Get normalized data Event rate error
	 * @return
	 */
	public double getNormDataER_Error() {
		double totError=0;
		double[] errors = getNormDataER_Resids();
		for(int i=0;i<errors.length;i++)
			if(!Double.isNaN(errors[i])) totError += errors[i]*errors[i];
		return totError;
	}
	
	/**
	 * Get A-Priori model error
	 * @return
	 */
	public double getA_PrioriModelError() {
		double wt, totError=0,finalRupRate, aPrioriRate;
		for(int rup=0; rup < num_rup; rup++) {
/**/
			// aPrioriRupWt = rate/stDev, and wt here should be 1/stDev
			if(aPrioriRupRates[rup].getValue() > 0)
				wt = aPrioriRupWt/aPrioriRupRates[rup].getValue();
			else
				wt = aPrioriRupWt/minNonZeroAprioriRate; // make it the same as for smallest non-zero rate

//				wt = MIN_A_PRIORI_ERROR;

//			wt= aPrioriRupWt;
			finalRupRate = getRupRate(rup);
			aPrioriRate = getAPrioriRupRate(rup);
			totError+=(finalRupRate-aPrioriRate)*(finalRupRate-aPrioriRate)*wt*wt;
		}
		return totError;
	}
	
	
	/**
	 * Get total a priori rupture rate
	 * 
	 * @return
	 */
	public double getTotalAPrioriRate() {
		double total = 0;
		for(int rup=0; rup < num_rup; rup++) {
//System.out.println(aPrioriRupRates[rup].getValue());
			total += aPrioriRupRates[rup].getValue();
		}
		return total;
	}
	
	
	/**
	 * Get non-normalized A-Priori model error
	 * @return
	 */
	public double getNonNormA_PrioriModelError() {
		double totError=0,finalRupRate, aPrioriRate;
		for(int rup=0; rup<num_rup; ++rup) {
			finalRupRate = getRupRate(rup);
			aPrioriRate = getAPrioriRupRate(rup);
			totError+=(finalRupRate-aPrioriRate)*(finalRupRate-aPrioriRate);
		}
		return totError;
	}
	
	/*
	 * This give the final segment moment rates (reduced by moRateReduction)
	 */
	public double[] getFinalSegMoRate() {
		double[] segMoRate = new double[num_seg];
		double totMoRate = 0;
		for(int i=0; i<num_seg;i++) {
			segMoRate[i] = segmentData.getSegmentMomentRate(i)*(1-this.moRateReduction);
			totMoRate += segMoRate[i];
		}
		return segMoRate;
	}
	
	/*
	 * This must be run after calling the getTimeDependentSources(double, double, double, boolean)() method.
	 */
	public void simulateEvents(int num) {
		
		if(!isTimeDeptendent)
			throw new RuntimeException("Error with method simulateEvents(): Source can't be time independent");
		
//		System.out.println("moments: "+totMoRate+"  "+this.getTotalMoRateFromRups());
		WG02_QkSimulations qkSim = new WG02_QkSimulations();
		qkSim.computeSimulatedEvents(totRupRate, getFinalSegMoRate(), segAperiodicity, rupInSeg, num);
		
		System.out.println("Rup rates: orig, sim, and sim/orig");
		for(int i=0;i<totRupRate.length;i++) {
			double simRate = qkSim.getSimAveRupRate(i);
			System.out.println((float)totRupRate[i]+"   "+(float)simRate+"   "+(float)(simRate/totRupRate[i]));
		}

		System.out.println("Seg rates: orig, sim, and sim/orig");
		for(int i=0;i<finalSegRate.length;i++) {
			double simRate = qkSim.getSimAveSegRate(i);
			System.out.println((float)finalSegRate[i]+"   "+(float)simRate+"   "+(float)(simRate/finalSegRate[i]));
		}
		
		
		System.out.println("Tot Moment rates: orig, sim, and sim/orig");
		double simMoRate = qkSim.getSimMoRate(rupMeanMag);
		double totMoRate = getTotalMoRateFromRups();
		System.out.println((float)totMoRate+"   "+(float)simMoRate+"   "+(float)(simMoRate/totMoRate));
		
		String[] segNames = new String[num_seg];
		for(int i=0; i<num_seg;i++)
			segNames[i]=this.segmentData.getSegmentName(i);
		qkSim.plotSegmentRecurIntPDFs(segNames);
	}
	
	
	public double[] tryTimePredProbs(double duration,double startYear,double aperiodicity) {
		double[] segSlipLast = new double[num_seg];
		double[] segSlipRate = new double[num_seg];
		double[] segArea = new double[num_seg];
		double[] segTimeLast  = new double[num_seg];
		for(int i=0;i<num_seg;i++) {
			segSlipLast[i]=this.segmentData.getSegAveSlipInLastEvent(i);
			segSlipRate[i]=this.segmentData.getSegmentSlipRate(i)*(1-this.moRateReduction);
			segArea[i]=this.segmentData.getSegmentArea(i);
			segTimeLast[i]=this.segmentData.getSegCalYearOfLastEvent(i);
		}
		return TimePredictableQkProbCalc.getRupProbs(totRupRate, segSlipLast, segSlipRate, segArea, segTimeLast, 
				rupInSeg, aperiodicity, startYear, duration);
	}

}

