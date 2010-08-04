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

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;

import org.opensha.commons.calc.FaultMomentCalc;
import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Ellsworth_B_WG02_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Somerville_2006_MagAreaRel;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbDiscrEmpiricalDistFunc;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_TypeB_EqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.FrankelGriddedSurface;
import org.opensha.sha.faultSurface.GriddedSubsetSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;


/**
 * <p>Title: UnsegmentedSource </p>
 * <p>Description: 	
 * 
 * The EmpricalModel option only influence what's returned by the getRupture() method (it doesn't influence any
 * other diagnostics included what's returned by getMagFreqDist).
 * 
 * Need to add floating in down-dip direction since NGAs will use this
 * 
 * If Asismicity is applied as a reduction of area, then effective all down-dip widths (DDW) are reduced, 
 * and given a single value applied to all segments (DDW = the total reduced area divided by total length).
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Ned Field
 * @date Sept, 2003
 * @version 1.0
 */

public class UnsegmentedSource extends ProbEqkSource {

	//for Debug purposes
	private static String C = new String("UnsegmentedSource");
	private final static boolean D = false;
	ArrayList<ProbEqkRupture> ruptureList;
	private double rake;
	protected double duration;
	//these are the static static defined varibles to be used to find the number of ruptures.
	private final static double RUPTURE_WIDTH =100.0;
	private double rupOffset= UCERF2.RUP_OFFSET;
	private int totNumRups, totNumGR_rups, totNumChar_rups;
	private EvenlyGriddedSurface surface;
	private ArrayList gr_mags, char_mags, gr_rates, char_rates;
	public final static double DEFAULT_DURATION  = 1;
	//name for this classs
	protected String NAME = "Unsegmented Source";

	private int num_seg;
	private double[] segRate, segVisibleRate; // segment rates 
	//private double[] segAveSlipRate; // ave slip rate for segment
	private ArbDiscrEmpiricalDistFunc[] segSlipDist, segVisibleSlipDist;  // segment slip dist

	private IncrementalMagFreqDist sourceMFD, grMFD, charMFD; // Mag Freq dist for source
	private IncrementalMagFreqDist visibleSourceMFD; // Mag Freq dist for visible ruptures
	private IncrementalMagFreqDist[] segSourceMFD;  // Mag Freq Dist for each segment
	private IncrementalMagFreqDist[] visibleSegSourceMFD;  // Mag Freq Dist for visible ruptures on each segment
	private double sourceMag;  // this is the char mag or upper mag if mag PDF is not given

	// inputs:
	private FaultSegmentData segmentData;
	private MagAreaRelationship magAreaRel;
	private double fixMag, fixRate, mag_lowerGR, b_valueGR;

//	the following is the total moment-rate reduction, including that which goes to the  
	// background, sfterslip, events smaller than the min mag here, and aftershocks and foreshocks.
	private double moRateReduction;  
	private double moRate;

	// List of discretized locations on the surface
	protected LocationList surfaceLocList;
	
	private EmpiricalModel empiricalModel;
	private double empirical_weight; // this is the weight to give to the empirical model
	private double sourceGain;

	protected ArbitrarilyDiscretizedFunc origSlipRateFunc, predSlipRateFunc;
	private ArrayList<ArbitrarilyDiscretizedFunc> magBasedUncorrSlipRateFuncs;
	
	private static HanksBakun2002_MagAreaRel hb_MagAreaRel = new HanksBakun2002_MagAreaRel();
	private static Ellsworth_B_WG02_MagAreaRel ellB_magAreaRel = new Ellsworth_B_WG02_MagAreaRel();
	private static Somerville_2006_MagAreaRel somerville_magAreaRel = new Somerville_2006_MagAreaRel();

	
	public final static int FULL_DDW_FLOATER = 0;
	public final static int STRIKE_AND_DOWNDIP_FLOATER = 1;
	public final static int CENTERED_DOWNDIP_FLOATER = 2;

	
	/**
	 * Description:  The constructs the source for the average UCERF2 logic tree branch, where param values have been hard coded.
	 * Note that not all derivative info is generate here (such as segSlipDist[])
	 * 
	 * this is used for making B-Faults sources for Average UCERF2
	 * 
	 * @param floaterType - FULL_DDW_FLOATER (0) = only along strike ( rupture full DDW); 
	 *                      STRIKE_AND_DOWNDIP_FLOATER (1) = float along strike and down dip;
	 *                      CENTERED_DOWNDIP_FLOATER (2) = float along strike & centered down dip
	 * 
	 */
	public UnsegmentedSource(FaultSegmentData segmentData,  EmpiricalModel empiricalModel, 
			double rupOffset,double weight, 
			double empiricalModelWeight, double duration, 
			boolean applyCyberShakeDDW_Corr, int floaterType, double fixMag) {
		this(segmentData, empiricalModel, rupOffset, 0.8, 0.0, weight, 
				empiricalModelWeight, duration, segmentData.getTotalMomentRate(),
				0.67,  applyCyberShakeDDW_Corr, floaterType, fixMag);
		
	}
	
	/**
	 * this is used for making A-Faults sources for Average UCERF2
	 * 
	 * Description:  The constructs the source for the average UCERF2 logic tree branch, where param values have been hard coded.
	 * Note that not all derivative info is generate here (such as segSlipDist[]).
	 * 
	 * @param floaterType - FULL_DDW_FLOATER (0) = only along strike ( rupture full DDW); 
	 *                      STRIKE_AND_DOWNDIP_FLOATER (1) = float along strike and down dip;
	 *                      CENTERED_DOWNDIP_FLOATER (2) = float along strike & centered down dip
	 * 
	 */
	public UnsegmentedSource(FaultSegmentData segmentData,  EmpiricalModel empiricalModel, 
			double rupOffset, double b_valueGR_1, double b_valueGR_2,  double weight, 
			double empiricalModelWeight, double duration, double moRate, 
			double fractCharVsGR, boolean applyCyberShakeDDW_Corr, int floaterType, double fixMag) {

		this.isPoissonian = true;
		empirical_weight = empiricalModelWeight;
		this.rupOffset = rupOffset;
		this.mag_lowerGR = 6.5;
		this.segmentData = segmentData;
		double min_mag = UCERF2.MIN_MAG;
		double max_mag = UCERF2.MAX_MAG;
		int num_mag = UCERF2.NUM_MAG;
		double delta_mag = (max_mag-min_mag)/(num_mag-1);
		double charMagSigma=0.12;
		double charMagTruncLevel = 2;
		this.moRateReduction = 0.1;  // fraction of slip rate reduction
		moRate = moRate*(1-moRateReduction); // this has been reduced by aseis
		this.empiricalModel = empiricalModel;
		
		double sourceMag1 = 0;
		double sourceMag2 = 0;
		
		// get mags from M(A) relationships if fixMag is NaN
		if(Double.isNaN(fixMag)) {
			sourceMag1 = hb_MagAreaRel.getMedianMag(segmentData.getTotalArea()/1e6);  // this area is reduced by aseis if appropriate
			sourceMag2 = ellB_magAreaRel.getMedianMag(segmentData.getTotalArea()/1e6);  // this area is reduced by aseis if appropriate			
		}
		else {
			sourceMag1 = fixMag;
			sourceMag2 = fixMag;
		}
		
		// round to nice values
		sourceMag1 = Math.round(sourceMag1/delta_mag) * delta_mag;
		sourceMag2 = Math.round(sourceMag2/delta_mag) * delta_mag;
		


		//OVERRIDE VALUES FOR SAF CREEPING SECTION WITH NSHMP VALUES
		if(segmentData.getFaultName().equals("San Andreas (Creeping Segment)")) {
			moRateReduction = 0.0;

			// The following values come from the file "creepflt.1sta.in" sent by Steve Harmsen on 08/30/07
			// this produces a total rate of 0.01095, hwereas that annoted in their file is 0.01079 (close enough)
			mag_lowerGR = 6.0;
			b_valueGR_1 = 0.91;
			b_valueGR_2 = 0.91;
			sourceMag1 = 6.7;
			sourceMag2 = 6.7;
			fractCharVsGR = 0;
			moRate = 3.8593e16;  // correct units?

		}
		IncrementalMagFreqDist tempCharMFD, tempGR_MFD;
		sourceMFD = new SummedMagFreqDist(min_mag, max_mag, num_mag);
		charMFD = new SummedMagFreqDist(min_mag, max_mag, num_mag);
		grMFD = new SummedMagFreqDist(min_mag, max_mag, num_mag);

		sourceMag = sourceMag1;
		if(sourceMag <= mag_lowerGR) {
			tempCharMFD = new GaussianMagFreqDist(min_mag, max_mag, num_mag, 
						sourceMag, charMagSigma, moRate*weight*0.5, charMagTruncLevel, 2);
			((SummedMagFreqDist) charMFD).addIncrementalMagFreqDist(tempCharMFD);
		}
		else {
			tempCharMFD = new GaussianMagFreqDist(min_mag, max_mag, num_mag, 
						sourceMag, charMagSigma, moRate*fractCharVsGR*weight*0.5, charMagTruncLevel, 2);
			((SummedMagFreqDist) charMFD).addIncrementalMagFreqDist(tempCharMFD);
			// note half-bin offset of lower and upper GR mags in what follows
			b_valueGR = b_valueGR_1;
			tempGR_MFD = new GutenbergRichterMagFreqDist(min_mag, num_mag, delta_mag,
					mag_lowerGR+delta_mag/2, sourceMag-delta_mag/2, moRate*(1-fractCharVsGR)*weight*0.5*0.5, b_valueGR);
			((SummedMagFreqDist)grMFD).addIncrementalMagFreqDist(tempGR_MFD);
			b_valueGR = b_valueGR_2;
			tempGR_MFD = new GutenbergRichterMagFreqDist(min_mag, num_mag, delta_mag,
					mag_lowerGR+delta_mag/2, sourceMag-delta_mag/2, moRate*(1-fractCharVsGR)*weight*0.5*0.5, b_valueGR);
			((SummedMagFreqDist)grMFD).addIncrementalMagFreqDist(tempGR_MFD);

		}
		
		sourceMag = sourceMag2;
		if(sourceMag <= mag_lowerGR) {
			tempCharMFD = new GaussianMagFreqDist(min_mag, max_mag, num_mag, 
						sourceMag, charMagSigma, moRate*weight*0.5, charMagTruncLevel, 2);
			((SummedMagFreqDist) charMFD).addIncrementalMagFreqDist(tempCharMFD);
		}
		else {
			tempCharMFD = new GaussianMagFreqDist(min_mag, max_mag, num_mag, 
						sourceMag, charMagSigma, moRate*fractCharVsGR*weight*0.5, charMagTruncLevel, 2);
			((SummedMagFreqDist) charMFD).addIncrementalMagFreqDist(tempCharMFD);
			// note half-bin offset of lower and upper GR mags in what follows
			b_valueGR = b_valueGR_1;
			tempGR_MFD = new GutenbergRichterMagFreqDist(min_mag, num_mag, delta_mag,
					mag_lowerGR+delta_mag/2, sourceMag-delta_mag/2, moRate*(1-fractCharVsGR)*weight*0.5*0.5, b_valueGR);
			((SummedMagFreqDist)grMFD).addIncrementalMagFreqDist(tempGR_MFD);
			b_valueGR = b_valueGR_2;
			tempGR_MFD = new GutenbergRichterMagFreqDist(min_mag, num_mag, delta_mag,
					mag_lowerGR+delta_mag/2, sourceMag-delta_mag/2, moRate*(1-fractCharVsGR)*weight*0.5*0.5, b_valueGR);
			((SummedMagFreqDist)grMFD).addIncrementalMagFreqDist(tempGR_MFD);

		}
		((SummedMagFreqDist) sourceMFD).addIncrementalMagFreqDist(charMFD);
		((SummedMagFreqDist) sourceMFD).addIncrementalMagFreqDist(grMFD);


		num_seg = segmentData.getNumSegments();
		StirlingGriddedSurface combinedGriddedSurface;
		if (applyCyberShakeDDW_Corr) {
			double ddwCorrFactor = somerville_magAreaRel.getMedianArea((sourceMag1+sourceMag2)/2)/(segmentData.getTotalArea()/1e6);
			combinedGriddedSurface = segmentData.getCombinedGriddedSurface(UCERF2.GRID_SPACING, ddwCorrFactor);
		} else {
			combinedGriddedSurface = segmentData.getCombinedGriddedSurface(UCERF2.GRID_SPACING);
		}
		
		// create the source
		mkRuptureList(combinedGriddedSurface,
				rupOffset,
				segmentData.getAveRake(),
				duration,
				segmentData.getFaultName(),
				applyCyberShakeDDW_Corr,
				floaterType);


		// change the info in the MFDs
		String new_info = "Source MFD\n"+sourceMFD.getInfo();
		new_info += "|n\nRescaled to:\n\n\tMoment Rate: "+(float)sourceMFD.getTotalMomentRate()+"\n\n\tNew Total Rate: "+(float)sourceMFD.getCumRate(0);
		sourceMFD.setInfo(new_info);

	}
	
	
	
	
	
	

	/**
	 * Description:  The constructs the source as a fraction of charateristic (Gaussian) and GR
	 * 
	 * @param floaterType - FULL_DDW_FLOATER (0) = only along strike ( rupture full DDW); 
	 *                      STRIKE_AND_DOWNDIP_FLOATER (1) = float along strike and down dip;
	 *                      CENTERED_DOWNDIP_FLOATER (2) = float along strike & centered down dip
	 */
	public UnsegmentedSource(FaultSegmentData segmentData, MagAreaRelationship magAreaRel, 
			double fractCharVsGR, double min_mag, double max_mag, int num_mag, 
			double charMagSigma, double charMagTruncLevel, 
			double mag_lowerGR, double b_valueGR, double moRateReduction, double fixMag,
			double fixRate, double meanMagCorrection, EmpiricalModel empiricalModel,
			int floaterType) {

		this.isPoissonian = true;
		empirical_weight = 1.0;
		this.segmentData = segmentData;
		this.magAreaRel = magAreaRel;
		this.fixMag = fixMag; // change this by meanMagCorrection?
		this.fixRate = fixRate*(1-moRateReduction);  // do we really want to reduce this???
		double delta_mag = (max_mag-min_mag)/(num_mag-1);
		this.moRateReduction = moRateReduction;  // fraction of slip rate reduction
		this.mag_lowerGR = mag_lowerGR;
		this.b_valueGR = b_valueGR;
		this.empiricalModel = empiricalModel;
		sourceMag = magAreaRel.getMedianMag(segmentData.getTotalArea()/1e6)+meanMagCorrection;  // this area is reduced by aseis if appropriate
		//System.out.print(this.segmentData.getFaultName()+" mag_before="+sourceMag+";  mag_after=");
		sourceMag = Math.round(sourceMag/delta_mag) * delta_mag;
//		System.out.print(sourceMag+"\n");
		moRate = segmentData.getTotalMomentRate()*(1-moRateReduction); // this has been reduced by aseis



		//OVERRIDE VALUES FOR SAF CREEPING SECTION WITH NSHMP VALUES
		if(segmentData.getFaultName().equals("San Andreas (Creeping Segment)")) {
			moRateReduction = 0.0;
			this.moRateReduction = moRateReduction;  // fraction of slip rate reduction

			// The following values come from the file "creepflt.1sta.in" sent by Steve Harmsen on 08/30/07
			// this produces a total rate of 0.01095, hwereas that annoted in their file is 0.01079 (close enough)
			mag_lowerGR = 6.0;
			this.mag_lowerGR = mag_lowerGR;
			b_valueGR = 0.91;
			this.b_valueGR = b_valueGR;
			this.sourceMag = 6.7;
			fractCharVsGR = 0;
			moRate = 3.8593e16;  // correct units?

		}




		// only apply char if mag <= lower RG mag 
		if(sourceMag <= mag_lowerGR) {
			if(Double.isNaN(fixMag)) // if it is not a B Fault Fix
				charMFD = new GaussianMagFreqDist(min_mag, max_mag, num_mag, 
						sourceMag, charMagSigma, moRate, charMagTruncLevel, 2);
			else { // if it is a B Fault Fix
				charMFD = new GaussianMagFreqDist(min_mag, max_mag, num_mag,
						fixMag, charMagSigma, 1.0, charMagTruncLevel, 2);
				charMFD.scaleToCumRate(0, this.fixRate);

			}
			sourceMFD = charMFD;
		}
		else {
			sourceMFD = new SummedMagFreqDist(min_mag, max_mag, num_mag);
			//	make char dist 
			if(Double.isNaN(fixMag)) // if it is not a B Fault Fix
				charMFD = new GaussianMagFreqDist(min_mag, max_mag, num_mag, 
						sourceMag, charMagSigma, moRate*fractCharVsGR, charMagTruncLevel, 2);
			else { // if it is a B Fault Fix
				charMFD = new GaussianMagFreqDist(min_mag, max_mag, num_mag,
						fixMag, charMagSigma, 1.0, charMagTruncLevel, 2);
				charMFD.scaleToCumRate(0, this.fixRate);		
			}
			((SummedMagFreqDist) sourceMFD).addIncrementalMagFreqDist(charMFD);
			// note half-bin offset of lower and upper GR mags in what follows
			grMFD = new GutenbergRichterMagFreqDist(min_mag, num_mag, delta_mag,
					mag_lowerGR+delta_mag/2, sourceMag-delta_mag/2, moRate*(1-fractCharVsGR), b_valueGR);
			((SummedMagFreqDist)sourceMFD).addIncrementalMagFreqDist(grMFD);
		}

		num_seg = segmentData.getNumSegments();

		// get the impled MFD for "visible" ruptures (those that are large 
		// enough that their rupture will be seen at the surface)
		visibleSourceMFD = (IncrementalMagFreqDist)sourceMFD.deepClone();
		for(int i =0; i<sourceMFD.getNum(); i++)
			visibleSourceMFD.set(i,sourceMFD.getY(i)*getProbVisible(sourceMFD.getX(i)));

		// create the source
		mkRuptureList(segmentData.getCombinedGriddedSurface(UCERF2.GRID_SPACING),
				rupOffset,
				segmentData.getAveRake(),
				DEFAULT_DURATION,
				segmentData.getFaultName(),
				false,
				floaterType);



		// get the rate of ruptures on each segment (segSourceMFD[seg])
		getSegSourceMFD();

		// now get the visible MFD for each segment
		visibleSegSourceMFD = new IncrementalMagFreqDist[num_seg];
		for(int s=0; s< num_seg; s++) {
			visibleSegSourceMFD[s] = (IncrementalMagFreqDist) segSourceMFD[s].deepClone();
			for(int i =0; i<sourceMFD.getNum(); i++)
				visibleSegSourceMFD[s].set(i,segSourceMFD[s].getY(i)*getProbVisible(segSourceMFD[s].getX(i)));
		}

		// change the info in the MFDs
		String new_info = "Source MFD\n"+sourceMFD.getInfo();
		new_info += "|n\nRescaled to:\n\n\tMoment Rate: "+(float)sourceMFD.getTotalMomentRate()+"\n\n\tNew Total Rate: "+(float)sourceMFD.getCumRate(0);
		sourceMFD.setInfo(new_info);

		new_info = "Visible Source MFD\n"+visibleSourceMFD.getInfo();
		new_info += "|n\nRescaled to:\n\n\tMoment Rate: "+(float)visibleSourceMFD.getTotalMomentRate()+
		"\n\n\tNew Total Rate: "+(float)visibleSourceMFD.getCumRate(0);
		visibleSourceMFD.setInfo(new_info);


		// find the total rate of ruptures for each segment
		segRate = new double[num_seg];
		segVisibleRate = new double[num_seg];
		for(int s=0; s< num_seg; s++) {
			segRate[s] = segSourceMFD[s].getTotalIncrRate();
			segVisibleRate[s] = visibleSegSourceMFD[s].getTotalIncrRate();
		}

		// find the slip distribution of each segment
		computeSegSlipDist();

		saveSurfaceLocs();
		//System.out.println("Moment Rate:"+this.moRate);

		//if(D)
		//  for(int i=0; i<num_seg; ++i)
		//	  System.out.println("Slip for segment "+i+":  " +segSlipDist[i] +";  "+segVisibleSlipDist[i] );

		// test
		// System.out.println(getNSHMP_SrcFileString());
	}


	/**
	 * Compute orig and final slip rates along the fault
	 *
	 */
	private void saveSurfaceLocs() {
		EvenlyGriddedSurface sourceSurface = this.getSourceSurface();
		int numCols = sourceSurface.getNumCols();
		//System.out.println(this.segmentData.getFaultName());
		// Surface trace location list
		surfaceLocList = new LocationList();
		for(int col=0; col<numCols; ++col) 
			surfaceLocList.add(sourceSurface.getLocation(0, col));
		// original slip rate
		//this.getOrigSlipRateAlongFault();
		// uncorrected slip rate
		//this.getFinalSlipRateAlongFault();

		// write Average uncorrected slip rates for each segment
		/*double totSegLength = 0;
		int index1, index2;
		System.out.println(this.segmentData.getFaultName());
		for(int segIndex=0; segIndex<num_seg; ++segIndex) {
			index1 = (int)totSegLength;
			totSegLength += this.segmentData.getSegmentLength(segIndex)/1e3;
			index2 = (int)totSegLength;
			double totSlipRate=0;
			for(int j=index1; j<=index2; ++j) {
				totSlipRate += this.predSlipRateFunc.getY(j); 
			}
			totSlipRate = totSlipRate/(index2-index1);
			System.out.println(segIndex+":\t"+totSlipRate/this.getFinalAveSegSlipRate(segIndex));
		}*/



		//System.out.println(ratioFunc.toString());
	}

	/**
	 * Get Mag Based slip rate func list along the fault. 
	 * These are for uncorrected slip rates
	 * 
	 * @return
	 */
	public ArrayList<ArbitrarilyDiscretizedFunc> getMagBasedFinalSlipRateListAlongFault() {
		if(this.magBasedUncorrSlipRateFuncs==null) getFinalSlipRateAlongFault();
		return this.magBasedUncorrSlipRateFuncs;
	}

	/**
	 * Compute the slip rate along fault.
	 * For Uncorrected slip rate, it gets rupture from parent class
	 * For corrected slip rate, it gets rupture from this class.
	 * 
	 * @param slipRateFunc
	 * @param isSlipRateCorrection
	 */
	protected void computeSlipRateAlongFault(ArbitrarilyDiscretizedFunc slipRateFunc, 
			ArrayList<ArbitrarilyDiscretizedFunc> magBasedFuncs,
			boolean isSlipRateCorrection) {
		int numRups = this.getNumRuptures();
		EvenlyGriddedSurface sourceSurface = this.getSourceSurface();
		int numCols = sourceSurface.getNumCols();
		for(int col=0; col<numCols; ++col) { // initialize all slip rates to 0
			slipRateFunc.set((double)col,0);
		}

		// mag based contributions
		HashMap<Double, ArbitrarilyDiscretizedFunc> magFuncMap = new HashMap<Double, ArbitrarilyDiscretizedFunc>();
		int numMags = this.sourceMFD.getNum();
		for(int i=0; i<numMags; ++i) {
			if(sourceMFD.getY(i)==0) continue;
			ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
			for(int col=0; col<numCols; ++col) { // initialize all slip rates to 0
				func.set((double)col,0);
			}
			magFuncMap.put(sourceMFD.getX(i), func);
			magBasedFuncs.add(func);
		}


		double area, slip, slipRate, moRate, totMoRate=0;
		for(int rupIndex=0; rupIndex<numRups; ++rupIndex) { // iterate over all ruptures
			ProbEqkRupture rupture;
			if(isSlipRateCorrection) rupture = getRupture(rupIndex);
			else rupture = getRupture(rupIndex);
			EvenlyGriddedSurfaceAPI rupSurface = rupture.getRuptureSurface();
			area = rupSurface.getSurfaceLength()*rupSurface.getSurfaceWidth();
			moRate = MomentMagCalc.getMoment(rupture.getMag());
			totMoRate+=moRate*rupture.getMeanAnnualRate(this.duration);
			slip = FaultMomentCalc.getSlip(area*1e6,moRate);
			slipRate = rupture.getMeanAnnualRate(this.duration)*slip;

			//if(this.segmentData.getFaultName().equalsIgnoreCase("S. San Andreas") && isSlipRateCorrection)
			// System.out.println(rupIndex+","+rupture.getMag()+","+slipRate);
			ArbitrarilyDiscretizedFunc magBasedFunc = magFuncMap.get(rupture.getMag());
			int index1 = this.surfaceLocList.indexOf(rupSurface.getLocation(0, 0));
			int index2 = this.surfaceLocList.indexOf(rupSurface.getLocation(0, rupSurface.getNumCols()-1));
			for(int col=index1; col<=index2; ++col) { // update the slip rates for this rupture
				slipRateFunc.set(col, slipRateFunc.getY(col)+slipRate);
				magBasedFunc.set(col, magBasedFunc.getY(col)+slipRate);
			}
		}
		//System.out.println(totMoRate);
	}

	/**
	 * Get final slip Rate along fault
	 * 
	 * @return
	 */
	public ArbitrarilyDiscretizedFunc getFinalSlipRateAlongFault() {
		if(predSlipRateFunc!=null) return predSlipRateFunc;
		predSlipRateFunc = new ArbitrarilyDiscretizedFunc();
		predSlipRateFunc.setName("Final slip rate along fault");
		magBasedUncorrSlipRateFuncs = new ArrayList<ArbitrarilyDiscretizedFunc>();
		//System.out.print("Uncorrected Moment Rate:");
		computeSlipRateAlongFault(predSlipRateFunc, magBasedUncorrSlipRateFuncs, false);
		return predSlipRateFunc;
	}



	/**
	 * Get Original Slip Rate along fault (e.g., w/ step functions at segment boundaries)
	 * 
	 * @return
	 */
	public ArbitrarilyDiscretizedFunc getOrigSlipRateAlongFault() {
		if(origSlipRateFunc!=null) return origSlipRateFunc;

		// save cumulative segment lengths
		ArbitrarilyDiscretizedFunc segLengths = new ArbitrarilyDiscretizedFunc();
		double totSegLength = 0;
		for(int segIndex=0; segIndex<num_seg; ++segIndex) {
			totSegLength += this.segmentData.getSegmentLength(segIndex)/1e3;
			segLengths.set((double)segIndex, totSegLength);
		}
		EvenlyGriddedSurface sourceSurface = this.getSourceSurface();
		int numCols = sourceSurface.getNumCols();
		double slipRate=0;
		// Iterate over all points to get the orig slip rate on each gridded location
		origSlipRateFunc = new ArbitrarilyDiscretizedFunc();
		origSlipRateFunc.setName("Orig slip rate along fault");
		for(int col=0; col<numCols; ++col) {
			double length = col*UCERF2.GRID_SPACING;
			// find the segment where this location exists
			for(int segIndex=0; segIndex<num_seg; ++segIndex) {
				if(length<segLengths.getY(segIndex)) {
					slipRate = segmentData.getSegmentSlipRate(segIndex)*(1-moRateReduction);
					break;
				}
			}
			origSlipRateFunc.set((double)col, slipRate);
		}
		//System.out.println(origSlipRateFunc.toString());
		return origSlipRateFunc;
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
	 * Get the reduced moment rate
	 * @return
	 */
	public double getMomentRate() {
		return this.moRate;
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
			normResids[segIndex] = getFinalAveSegSlipRate(segIndex)-getFaultSegmentData().getSegmentSlipRate(segIndex)*reduction;
			normResids[segIndex] /= (getFaultSegmentData().getSegSlipRateStdDev(segIndex)*reduction);
		}

		return normResids;
	}

	/**
	 * This returns of magnitude computed for the characteristic earthquake 
	 * (and upper mag of the GR) if that constructor was used (no mag PDF given)
	 * @return
	 */
	public double getSourceMag() {
		return sourceMag;
	}

	/**
	 * Get B Fault Mag Fix (Some B faults have Mag fix which is specified in a text file)
	 * @return
	 */
	public double getFixMag() {
		return this.fixMag;
	}

	/**
	 * Get B Fault Rate Fix (Some B faults have Rate fix which is specified in a text file)
	 * @return
	 */
	public double getFixRate() {
		return this.fixRate;
	}

	/**
	 * Get fault segment data
	 * @return
	 */
	public FaultSegmentData getFaultSegmentData() {
		return this.segmentData;
	}

	/**
	 * This gets the magnitude frequency distribution for each segment by multiplying the original MFD
	 * by the average probability of observing each rupture on each segment (assuming ruptures have a
	 * uniform spatial distribution - or equal probability of landing anywhere).  If asiemicity reduces
	 * area, then the DDW here is effectively reduced (is this what we want?).
	 *
	 */
	private void getSegSourceMFD() {
		// get segment lengths
		double[] segLengths = new double[num_seg];
		for(int i = 0; i< num_seg; i++) segLengths[i] = 1e-3*segmentData.getSegmentLength(i); // converted to km
		double totalLength = segmentData.getTotalLength()*1e-3;
		double aveDDW = (segmentData.getTotalArea()*1e-6)/totalLength; // average Down dip width in km
		segSourceMFD = new IncrementalMagFreqDist[num_seg]; 
		for(int i=0; i<num_seg; ++i) segSourceMFD[i] = (IncrementalMagFreqDist) sourceMFD.deepClone(); 
		// loop over all magnitudes in flaoter MFD
		for (int i=0; i<sourceMFD.getNum(); ++i) {
			double mag = sourceMFD.getX(i);
			double rupLength = magAreaRel.getMedianArea(mag)/aveDDW;  // in km
			double[] segProbs = getProbSegObsRupture(segLengths, totalLength, rupLength);
			for(int j=0; j<num_seg; ++j) {
				segSourceMFD[j].set(i, segProbs[j]*segSourceMFD[j].getY(i));
			}
		}
	}

	/**
	 * This returns the probability of observing a rupture (of given length) 
	 * on each of the various segments (of given lengths) assuming the rupture has equal
	 * probabily of occurring anywhere along the fault (which means the probabilities 
	 * are greatest at the middle and taper toward the ends).  This is done by first
	 * getting the probability of observing the rupture at 100 points along the
	 * fault, and then averaging those probabilities in each segment.
	 * @param segLengths
	 * @param totalLength
	 * @param rupLength
	 * @return
	 */
	private double[] getProbSegObsRupture(double[] segLengths, double totalLength, double rupLength) {

//		if(this.segmentData.getFaultName().equals("Calaveras"))
//		System.out.println("Calaveras: "+segLengths[0]+"  "+segLengths[1]+"  "+segLengths[2]+"  "+totalLength+"  "+rupLength);

		double[] segProbs = new double[segLengths.length];

		// check whether rup length exceed fault length; all get it if so
		if(rupLength>totalLength) {
			for(int j=0; j<segLengths.length; ++j) segProbs[j]=1.0;;
			return segProbs;
		}

		EvenlyDiscretizedFunc probFunc = new EvenlyDiscretizedFunc(0, totalLength, 100);
		// first get the probability of observing the rupture at 100 points long the fault
		if(rupLength<totalLength/2) {
			double multFactor = rupLength/(totalLength-rupLength);  
			for(int i=0; i<probFunc.getNum(); ++i) {
				double l = probFunc.getX(i);
				double prob;
				if(l<rupLength) prob = l/rupLength*multFactor;
				else if(l<(totalLength-rupLength)) prob = multFactor;
				else prob = (totalLength-l)*multFactor/rupLength;
				probFunc.set(i, prob);
			}
		} else { //  if(rupLength>totalLength/2) {
			for(int i=0; i<probFunc.getNum(); ++i) {
				double l = probFunc.getX(i);
				double prob;
				if(l<(totalLength-rupLength)) prob = l/(totalLength-rupLength);
				else if(l<=rupLength) prob = 1;
				else prob = (totalLength-l)/(totalLength-rupLength);
				probFunc.set(i, prob);
			}
		} 
		//if (D) System.out.println("Prob Func="+probFunc.toString());

		// now average the probabilities for those points in each segment
		double firstLength = 0;
		double lastLength;
		for(int i=0 ; i<segLengths.length ; ++i) {
			int  index1 = (int)Math.ceil((firstLength-probFunc.getMinX())/probFunc.getDelta());
			lastLength = firstLength + segLengths[i];
			int index2 = (int) Math.floor((lastLength-probFunc.getMinX())/probFunc.getDelta());
			double total=0;
			for(int j=index1; j<=index2; ++j) total+=probFunc.getY(j);
			segProbs[i]= total/(index2-index1+1);
			firstLength=lastLength;
		}

		return segProbs;
	}

	/**
	 * This returns the probability that the given magnitude 
	 * event will be observed at the ground surface.  This is based
	 * on equation 4 of Youngs et al. [2003, A Methodology for Probabilistic Fault
	 * Displacement Hazard Analysis (PFDHA), Earthquake Spectra 19, 191-219] using 
	 * the coefficients they list in their appendix for "Data from Wells and 
	 * Coppersmith (1993) 276 worldwide earthquakes".
	 * @return
	 */
	private double getProbVisible(double mag) {
		return Math.exp(-12.51+mag*2.053)/(1.0 + Math.exp(-12.51+mag*2.053));
		/* Ray & Glenn's equation
		 if(mag <= 5) 
		 return 0.0;
		 else if (mag <= 7.6)
		 return -0.0608*mag*mag + 1.1366*mag + -4.1314;
		 else 
		 return 1.0;
		 */
	}

	/**
	 * Final, implied average, slip rate on the segment
	 */
	public double getFinalAveSegSlipRate(int ithSegment) {
		ArbDiscrEmpiricalDistFunc segmenstSlipDist = getSegmentSlipDist(ithSegment);
		double slipRate=0;
		for(int i=0; i<segmenstSlipDist.getNum(); ++i)
			slipRate+=segmenstSlipDist.getX(i)*segmenstSlipDist.getY(i);
		return slipRate;
	}



	/**
	 * Get Slip Distribution for this segment
	 * 
	 * @param ithSegment
	 * @return
	 */
	public ArbDiscrEmpiricalDistFunc getSegmentSlipDist(int ithSegment) {
		return segSlipDist[ithSegment];
	}

	/**
	 * Get Visible Slip Distribution for this segment
	 * 
	 * @param ithSegment
	 * @return
	 */
	public ArbDiscrEmpiricalDistFunc getSegmentVisibleSlipDist(int ithSegment) {
		return segVisibleSlipDist[ithSegment];
	}


	/**
	 * Get the Mag Freq Dist for the source
	 * 
	 * @return
	 */
	public IncrementalMagFreqDist getMagFreqDist() {
		return sourceMFD; 
	}

	/**
	 * The returns the characteristic mag freq dist if it exists (i.e., the constructor
	 * that specifies a fraction of char vs GR was used)
	 * @return
	 */
	public IncrementalMagFreqDist getCharMagFreqDist() {
		return charMFD; 
	}


	/**
	 * The returns the GR mag freq dist if it exists (i.e., the constructor
	 * that specifies a fraction of char vs GR was used)
	 * @return
	 */
	public IncrementalMagFreqDist getGR_MagFreqDist() {
		return grMFD;
	}


	/**
	 * Get the Mag Freq Dist for "visible" source ruptures
	 * 
	 * @return
	 */
	public IncrementalMagFreqDist getVisibleSourceMagFreqDist() {
		return visibleSourceMFD; 
	}

	/**
	 * Compute both total and visible slip distribution for each segment (segSlipDist[seg] & segVisibleSlipDist[seg])
	 */
	private void computeSegSlipDist() {

		segSlipDist = new ArbDiscrEmpiricalDistFunc[num_seg];
		segVisibleSlipDist = new ArbDiscrEmpiricalDistFunc[num_seg];

		for(int seg=0; seg<num_seg; ++seg) {
			segSlipDist[seg]=new ArbDiscrEmpiricalDistFunc();
			segVisibleSlipDist[seg]=new ArbDiscrEmpiricalDistFunc();
			IncrementalMagFreqDist segMFD =  segSourceMFD[seg];
//			if(this.segmentData.getFaultName().equals("Calaveras"))
//			System.out.println(segMFD);
			IncrementalMagFreqDist visibleSegMFD =  visibleSegSourceMFD[seg];
			for(int i=0; i<segMFD.getNum(); ++i) {
				double mag = segMFD.getX(i);
				double moment = MomentMagCalc.getMoment(mag);
				double slip = FaultMomentCalc.getSlip(magAreaRel.getMedianArea(mag)*1e6, moment);
				segSlipDist[seg].set(slip, segMFD.getY(i));
				segVisibleSlipDist[seg].set(slip, visibleSegMFD.getY(i));
			}
		}
	}




	/**
	 * Get rate at a particular location on the fault trace. 
	 * It is calculated by adding the rates of all ruptures that include that location.
	 * 
	 * @param loc
	 * @param distanceCutOff - rupture included in total if point on surface is within this distance
	 * @return
	 */
	public double getPredSlipRate(Location loc) {
		// find distance to closest point on surface trace
		EvenlyGriddedSurface surface = this.getSourceSurface();
		double minDist = Double.MAX_VALUE, dist;
		for(int col=0; col < surface.getNumCols(); col++){
			dist = LocationUtils.horzDistanceFast(surface.getLocation(0,col), loc);
			if(dist <minDist) minDist = dist;
		}
		double distanceCutOff=minDist+0.001;  // add one meter to make sure we always get it
//		System.out.println(this.segmentData.getFaultName()+"  min dist to Tom's site ="+minDist);
		if(distanceCutOff > 2) throw new RuntimeException ("Location:("+loc.getLatitude()+","+loc.getLongitude()+") is more than 2 km from any rupture");
		double slipRate = 0;
		int numRups = getNumRuptures();
		//System.out.println(loc.getLatitude()+","+loc.getLongitude());
		for(int rupIndex=0; rupIndex<numRups; ++rupIndex) { // iterate over all ruptures
			ProbEqkRupture rupture = this.getRupture(rupIndex);
			Iterator it = rupture.getRuptureSurface().getLocationsIterator();
			while(it.hasNext()) { // iterate over all locations in a rupture
				Location surfaceLoc = (Location)it.next();
				if(LocationUtils.horzDistanceFast(surfaceLoc, loc)< distanceCutOff) {
					double area = rupture.getRuptureSurface().getSurfaceLength()*rupture.getRuptureSurface().getSurfaceWidth();
					double slip = FaultMomentCalc.getSlip(area*1e6,MomentMagCalc.getMoment(rupture.getMag()));
					slipRate+= rupture.getMeanAnnualRate(this.duration)*slip;
					//System.out.println(this.segmentData.getFaultName()+","+rupIndex+","+
					//	rupture.getMeanAnnualRate(this.duration));
					break;
				}
			}
		}
		if(slipRate==0) throw new RuntimeException ("No rupture close to event rate location:"+loc.getLatitude()+","+loc.getLongitude());
		//System.out.println(this.segmentData.getFaultName()+","+"Total Rate="+rate);
		return slipRate;
	}


	/**
	 * Get rate at a particular location on the fault trace. 
	 * It is calculated by adding the rates of all ruptures that include that location.
	 * 
	 * @param loc
	 * @param distanceCutOff - rupture included in total if point on surface is within this distance
	 * @return
	 */
	public double getPredEventRate(Location loc) {
		// find distance to closest point on surface trace
		EvenlyGriddedSurface surface = this.getSourceSurface();
		double minDist = Double.MAX_VALUE, dist;
		for(int col=0; col < surface.getNumCols(); col++){
			dist = LocationUtils.horzDistanceFast(surface.getLocation(0,col), loc);
			if(dist <minDist) minDist = dist;
		}
		double distanceCutOff=minDist+0.001;  // add one meter to make sure we always get it
//		System.out.println(this.segmentData.getFaultName()+"  min dist to Tom's site ="+minDist);
		if(distanceCutOff > 2) throw new RuntimeException ("Location:("+loc.getLatitude()+","+loc.getLongitude()+") is more than 2 km from any rupture");
		double rate = 0;
		int numRups = getNumRuptures();
		//System.out.println(loc.getLatitude()+","+loc.getLongitude());
		for(int rupIndex=0; rupIndex<numRups; ++rupIndex) { // iterate over all ruptures
			ProbEqkRupture rupture = this.getRupture(rupIndex);
			Iterator it = rupture.getRuptureSurface().getLocationsIterator();
			while(it.hasNext()) { // iterate over all locations in a rupture
				Location surfaceLoc = (Location)it.next();
				if(LocationUtils.horzDistanceFast(surfaceLoc, loc)< distanceCutOff) {
					rate+= rupture.getMeanAnnualRate(this.duration);
					//System.out.println(this.segmentData.getFaultName()+","+rupIndex+","+
					//	rupture.getMeanAnnualRate(this.duration));
					break;
				}
			}
		}
		//System.out.println(this.segmentData.getFaultName()+","+"Total Rate="+rate);
		return rate;
	}



	/**
	 * Get the "observed" rate at a particular location on the fault trace. By "observed" we mean reduce the rate
	 * according to the probability that each rupture might not be seen in paleoseismic data.
	 * It is calculated by adding the rates*prob_obs of all ruptures that include that location.
	 * 
	 * @param loc
	 * @param distanceCutOff - rupture included in total if point on surface is within this distance
	 * @return
	 */
	public double getPredObsEventRate(Location loc) {
		// find distance to closest point on surface trace
		EvenlyGriddedSurface surface = this.getSourceSurface();
		double minDist = Double.MAX_VALUE, dist;
		for(int col=0; col < surface.getNumCols(); col++){
			dist = LocationUtils.horzDistanceFast(surface.getLocation(0,col), loc);
			if(dist <minDist) minDist = dist;
		}
		double distanceCutOff=minDist+0.001;  // add one meter to make sure we always get it
		if(distanceCutOff > 2) throw new RuntimeException ("Location:("+loc.getLatitude()+","+loc.getLongitude()+") is more than 2 km from any rupture");
		double rate = 0;
		int numRups = getNumRuptures();
		//System.out.println(loc.getLatitude()+","+loc.getLongitude());
		for(int rupIndex=0; rupIndex<numRups; ++rupIndex) { // iterate over all ruptures
			ProbEqkRupture rupture = this.getRupture(rupIndex);
			double probVis = getProbVisible(rupture.getMag());
			Iterator it = rupture.getRuptureSurface().getLocationsIterator();
			while(it.hasNext()) { // iterate over all locations in a rupture
				Location surfaceLoc = (Location)it.next();
				if(LocationUtils.horzDistanceFast(surfaceLoc, loc)< distanceCutOff) {
					rate+= rupture.getMeanAnnualRate(this.duration) * probVis;
					//System.out.println(this.segmentData.getFaultName()+","+rupIndex+","+
					//	rupture.getMeanAnnualRate(this.duration));
					break;
				}
			}
		}
		//System.out.println(this.segmentData.getFaultName()+","+"Total Rate="+rate);
		return rate;
	}



	/**
	 * This makes the vector of fault corner location used by the getMinDistance(site)
	 * method.
	 * @param faultSurface
	 */
	/*private void makeFaultCornerLocs(EvenlyGriddedSurface faultSurface) {

		int nRows = faultSurface.getNumRows();
		int nCols = faultSurface.getNumCols();
		faultCornerLocations.add(faultSurface.get(0, 0));
		faultCornerLocations.add(faultSurface.get(0, (int) (nCols / 2)));
		faultCornerLocations.add(faultSurface.get(0, nCols - 1));
		faultCornerLocations.add(faultSurface.get(nRows - 1, 0));
		faultCornerLocations.add(faultSurface.get(nRows - 1, (int) (nCols / 2)));
		faultCornerLocations.add(faultSurface.get(nRows - 1, nCols - 1));

	}*/

	/**
	 * Get NSHMP GR Source File String. 
	 * This method is needed to create file for NSHMP. NOTE that the a-value here is the incremental rate
	 * between magnitude -delta/2 to delta/2.
	 * 
	 * @return
	 */
	public String getNSHMP_GR_SrcFileString() {
		// treat as char if mag<=6.5
		if(sourceMag <= 6.5)
			return getNSHMP_Char_SrcFileString();

		StringBuffer strBuffer = new StringBuffer("");
		strBuffer.append("2\t"); // GR MFD
		double rake = segmentData.getAveRake();
		String rakeStr = "";
		if((rake>=-45 && rake<=45) || rake>=135 || rake<=-135) rakeStr="1"; // Strike slip
		else if(rake>45 && rake<135) rakeStr="2"; // Reverse
		else if(rake>-135 && rake<-45) rakeStr="3"; // Normal
		else throw new RuntimeException("Invalid Rake:"+rake);
		strBuffer.append(rakeStr+"\t"+"1"+"\t"+this.segmentData.getFaultName()+"\n");
		int numNonZeroMags = (int)Math.round((sourceMag-mag_lowerGR)/sourceMFD.getDelta()+1);
		double moRate = sourceMFD.getTotalMomentRate();
		double delta = sourceMFD.getDelta();
		double a_value = getNSHMP_aValue(mag_lowerGR+delta/2,numNonZeroMags-1,delta,moRate,b_valueGR);
		double momentCheck = getMomentRate(mag_lowerGR+delta/2,numNonZeroMags-1,delta,a_value,b_valueGR);
		double wt = 1.0;
		if(momentCheck/moRate < 0.999 || momentCheck/moRate > 1.001)
			System.out.println("WARNING -- Bad a-value!: "+this.segmentData.getFaultName()+"  "+momentCheck+"  "+moRate);
//		throw new RuntimeException("Bad a-value!: "+momentCheck+"  "+moRate);
		strBuffer.append((float)a_value+"\t"+
				(float)b_valueGR+"\t"+
				(float)mag_lowerGR+"\t"+
				(float)sourceMag+"\t"+
				(float)delta+"\t"+
				(float)wt+"\t"+
				(float)moRate+"\n");
		StirlingGriddedSurface surface = (StirlingGriddedSurface)this.getSourceSurface();
		// dip, Down dip width, upper seismogenic depth, rup Area
		strBuffer.append((float)surface.getAveDip()+"\t"+(float)surface.getSurfaceWidth()+"\t"+
				(float)surface.getUpperSeismogenicDepth()+"\t"+(float)surface.getSurfaceLength()+"\n");
		FaultTrace faultTrace = surface.getFaultTrace();
		// All fault trace locations
		strBuffer.append(faultTrace.getNumLocations()+"\n");
		for(int locIndex=0; locIndex<faultTrace.getNumLocations(); ++locIndex)
			strBuffer.append(faultTrace.get(locIndex).getLatitude()+"\t"+
					faultTrace.get(locIndex).getLongitude()+"\n");
		return strBuffer.toString();
	}


	/**
	 * Get NSHMP Char Source File String. 
	 * This method is needed to create file for NSHMP. NOTE that the a-value here is the incremental rate
	 * between magnitude -delta/2 to delta/2.
	 * 
	 * @return
	 */
	public String getNSHMP_Char_SrcFileString() {
		StringBuffer strBuffer = new StringBuffer("");
		strBuffer.append("1\t"); // Char MFD
		double rake = segmentData.getAveRake();
		String rakeStr = "";
		if((rake>=-45 && rake<=45) || rake>=135 || rake<=-135) rakeStr="1"; // Strike slip
		else if(rake>45 && rake<135) rakeStr="2"; // Reverse
		else if(rake>-135 && rake<-45) rakeStr="3"; // Normal
		else throw new RuntimeException("Invalid Rake:"+rake);

		//System.out.println(rake+","+rakeStr);

		strBuffer.append(rakeStr+"\t"+"1"+"\t"+this.segmentData.getFaultName()+"\n");
		int numNonZeroMags = (int)Math.round((sourceMag-mag_lowerGR)/sourceMFD.getDelta()+1);
		double moRate = sourceMFD.getTotalMomentRate();
		double rate = moRate/MomentMagCalc.getMoment(sourceMag);
		double wt = 1.0;
		strBuffer.append((float)sourceMag+"\t"+rate+"\t"+wt+"\t"+(float)moRate+"\n");
		StirlingGriddedSurface surface = (StirlingGriddedSurface)this.getSourceSurface();
		// dip, Down dip width, upper seismogenic depth, rup Area
		strBuffer.append((float)surface.getAveDip()+"\t"+(float)surface.getSurfaceWidth()+"\t"+
				(float)surface.getUpperSeismogenicDepth()+"\t"+(float)surface.getSurfaceLength()+"\n");
		FaultTrace faultTrace = surface.getFaultTrace();
		// All fault trace locations
		strBuffer.append(faultTrace.getNumLocations()+"\n");
		for(int locIndex=0; locIndex<faultTrace.getNumLocations(); ++locIndex)
			strBuffer.append(faultTrace.get(locIndex).getLatitude()+"\t"+
					faultTrace.get(locIndex).getLongitude()+"\n");
		return strBuffer.toString();
	}




	/**
	 * this computes the moment for the GR distribution exactly the way frankel's code does it
	 */
	private double getMomentRate(double magLower, int numMag, double deltaMag, double aVal, double bVal) {
		double mo = 0;
		double mag;
		for(int i = 0; i <numMag; i++) {
			mag = magLower + i*deltaMag;
			mo += Math.pow(10,aVal-bVal*mag+1.5*mag+9.05);
		}
		return mo;
	}

	/**
	 * this computes the a-value for the GR distribution by inverting what's done in getMomentRate(*)
	 */
	private double getNSHMP_aValue(double magLower, int numMag, double deltaMag, double moRate, double bVal) {
		double sum = 0;
		double mag;
		for(int i = 0; i <numMag; i++) {
			mag = magLower + i*deltaMag;
			sum += Math.pow(10,-bVal*mag+1.5*mag+9.05);
		}
		return Math.log10((moRate/sum));
	}


	/**
	 * 
	 * @param surface
	 * @param rupOffset
	 * @param rake
	 * @param duration
	 * @param sourceName
	 * @param applyCyberShakeDDW_Corr
	 * @param floaterType - 0 = only along strike ( rupture full DDW); 
	 *                      1 = float along strike and down dip;
	 *                      2 = float along strike & centered down dip
	 */
	private void mkRuptureList(EvenlyGriddedSurface surface,
			double rupOffset,
			double rake,
			double duration,
			String sourceName,
			boolean applyCyberShakeDDW_Corr,
			int floaterType) {

		this.surface=surface;
		this.rupOffset = rupOffset;
		this.rake=rake;
		this.duration = duration;
		this.name = sourceName;
		ruptureList = new ArrayList<ProbEqkRupture>();
		double totSrcRate=0, totSrcRateEmp=0; // for computing the source gain
		
		// Make GR ruptures
		for (int i=0; grMFD!=null && i<grMFD.getNum(); ++i){
			double rate = grMFD.getY(i);
			if(rate == 0) continue;	// skip zero rates
			double mag = grMFD.getX(i);
			double rupArea  ;
			if(applyCyberShakeDDW_Corr) rupArea = somerville_magAreaRel.getMedianArea(mag);
			else rupArea  = hb_MagAreaRel.getMedianArea(mag);
			double rup_width = Math.sqrt(rupArea);
			if (rup_width > surface.getSurfaceWidth()) rup_width = surface.getSurfaceWidth();
			
			double rupLen = rupArea/rup_width;
			int numRup=-1, firstRupIndex=-1, lastRupIndex=-1, rupIndexOffset=-1;
			double finalRupOffset=0, finalRupWidth=0;
			
			if(floaterType == CENTERED_DOWNDIP_FLOATER) {
				// float only along center of DDW extent - FAILED ATTEMPT!
				int numRupAlongAt1kmOffset = surface.getNumSubsetSurfaces(rupLen,100,1.0); // rup width of 100 gets number floating along
				int totNumRupAt1kmOffset = surface.getNumSubsetSurfaces(rupLen,rup_width,1.0);
				firstRupIndex = ((totNumRupAt1kmOffset/numRupAlongAt1kmOffset)/2)*numRupAlongAt1kmOffset;
				lastRupIndex = firstRupIndex+numRupAlongAt1kmOffset;
				rupIndexOffset = (int)Math.round(rupOffset);
				numRup = surface.getNumSubsetSurfaces(rupLen,100,rupOffset);
				finalRupOffset = 1;
				finalRupWidth = rup_width;
				// int testNumRup =0;				
			}
			else if(floaterType == STRIKE_AND_DOWNDIP_FLOATER) {
				// float along strike and down dip
				numRup = surface.getNumSubsetSurfaces(rupLen,rup_width,rupOffset);
				firstRupIndex = 0;
				lastRupIndex = numRup;
				rupIndexOffset = 1;
				finalRupOffset = rupOffset;	
				finalRupWidth = rup_width;
			}
			else if (floaterType == FULL_DDW_FLOATER) {
				finalRupWidth = 100;
				numRup = surface.getNumSubsetSurfaces(rupLen,finalRupWidth,rupOffset);
				firstRupIndex = 0;
				lastRupIndex = numRup;
				rupIndexOffset = 1;
				finalRupOffset = rupOffset;	
			}
			
			
			
			rate /= numRup;
			for(int r=firstRupIndex; r<lastRupIndex; r+=rupIndexOffset) {
				ProbEqkRupture rup = new ProbEqkRupture();
				rup.setAveRake(rake);
				rup.setMag(mag);
				GriddedSubsetSurface rupSurf = surface.getNthSubsetSurface(rupLen,finalRupWidth,finalRupOffset,r);
				rup.setRuptureSurface(rupSurf);
				// set probability
			    double empiricalCorr=1;
			    if(empiricalModel != null) {
			    	empiricalCorr = empiricalModel.getCorrection(rupSurf)*empirical_weight + (1-empirical_weight); 
			    }
				double rupRate = rate * empiricalCorr;
			    totSrcRate += rate;
			    totSrcRateEmp += rupRate;
				rup.setProbability(1- Math.exp(-duration*rupRate));
				ruptureList.add(rup);
				//testNumRup += 1;
			}
			// if(testNumRup != numRup) throw  new RuntimeException("numRup="+numRup+"\ttestNumRup="+testNumRup);
			// System.out.println((numRup/testNumRup)+"\tnumRup="+numRup+"\ttestNumRup="+testNumRup);
			
		}
// if(floatsDownDip) System.out.println(segmentData.getFaultName());
		totNumGR_rups = ruptureList.size();

		double empiricalCorr=1;
	    if(empiricalModel != null) {
	    	empiricalCorr = empiricalModel.getCorrection(surface)*empirical_weight + (1-empirical_weight); 
	    }
	    for (int i=0; charMFD!=null && i<charMFD.getNum(); ++i){
	    	double rate = charMFD.getY(i);
	    	if(rate == 0) continue;	// skip zero rates
	    	double mag = charMFD.getX(i);
	    	ProbEqkRupture rup = new ProbEqkRupture();
	    	rup.setAveRake(rake);
	    	rup.setMag(mag);
	    	rup.setRuptureSurface(surface);
	    	double rupRate = rate * empiricalCorr;
	    	totSrcRate += rate;
	    	totSrcRateEmp += rupRate;
	    	rup.setProbability(1- Math.exp(-duration*rupRate));
	    	ruptureList.add(rup);
	    }
	    totNumChar_rups = ruptureList.size()-totNumGR_rups;
	    sourceGain = totSrcRateEmp/totSrcRate;
	}

	/**
	 * 
	 * @return
	 */
	public EvenlyGriddedSurface getSourceSurface() { return this.surface; }

	public int getNumRuptures() { return ruptureList.size(); }

	
	/**
	 * This gets the ProbEqkRupture object for the nth Rupture
	 */
	public ProbEqkRupture getRupture(int nthRupture){
		return ruptureList.get(nthRupture);
	}

	
	
	/**
	 * This returns the source gain
	 * @return
	 */
	public double getSourceGain() {
		return sourceGain;
		/*
		double totProb=0, totProbEmp=0;
		ProbEqkRupture tempRup;
		for(int i=0; i<getNumRuptures(); i++) {
			tempRup = getRupture(i);
			totProb+=Math.log(1-tempRup.getProbability());
			tempRup = getRupture(i, false);
			totProbEmp+=Math.log(1-tempRup.getProbability());

		}
		return (1 - Math.exp(totProbEmp))/(1 - Math.exp(totProb));
		*/
	}


	/** Set the time span in years
	 *
	 * @param yrs : timeSpan as specified in  Number of years
	 */
	public void setDuration(double yrs) {
		double oldDuration = duration;
		ProbEqkRupture rup;
		for(int r=0; r<ruptureList.size(); r++) {
			rup = ruptureList.get(r);
			double oldRate = rup.getMeanAnnualRate(oldDuration);
			rup.setProbability(1-Math.exp(-yrs*oldRate));
		}
		duration = yrs;
	}



	/**
	 * This returns the shortest dist to either end of the fault trace, or to the
	 * mid point of the fault trace.
	 * @param site
	 * @return minimum distance
	 */
	public  double getMinDistance(Site site) {

		double min;

		// get first location on fault trace
		LocationVector dir = LocationUtils.vector(site.getLocation(), (Location) surface.get(0,0));
		min = dir.getHorzDistance();

		// get last location on fault trace
		dir = LocationUtils.vector(site.getLocation(),(Location) surface.get(0,surface.getNumCols()-1));
		if (min > dir.getHorzDistance())
			min = dir.getHorzDistance();

		// get mid location on fault trace
		dir = LocationUtils.vector(site.getLocation(),(Location) surface.get(0,(int) surface.getNumCols()/2));
		if (min > dir.getHorzDistance())
			min = dir.getHorzDistance();

		return min;
	}

	/**
	 * get the name of this class
	 *
	 * @return
	 */
	public String getName() {
		return name;
	}


	/**
	 * this is to test the code
	 * @param args
	 */
	public static void main(String[] args) {
		FaultTrace fltTr = new FaultTrace("name");
		fltTr.add(new Location(33.0,-122,0));
		fltTr.add(new Location(34.0,-122,0));
		FrankelGriddedSurface surface = new FrankelGriddedSurface(fltTr,90,0,10,1);

		GutenbergRichterMagFreqDist gr = new GutenbergRichterMagFreqDist(6.5,3,0.5,6.5,7.5,1.0e14,1.0);
		System.out.println("cumRate="+(float)gr.getTotCumRate());

		Frankel02_TypeB_EqkSource src = new Frankel02_TypeB_EqkSource(gr,surface,
				10.0,0.0,1,"name");
		ProbEqkRupture rup;
		for(int i=0; i< src.getNumRuptures();i++) {
			rup = src.getRupture(i);
			System.out.print("rup #"+i+":\n\tmag="+rup.getMag()+"\n\tprob="+
					rup.getProbability()+"\n\tRup Ends: "+
					(float)rup.getRuptureSurface().getLocation(0,0).getLatitude()+"  "+
					(float)rup.getRuptureSurface().getLocation(0,rup.getRuptureSurface().getNumCols()-1).getLatitude()+
			"\n\n");
		}

	}

	/**
	 * It returns a list of all the locations which make up the surface for this
	 * source.
	 *
	 * @return LocationList - List of all the locations which constitute the surface
	 * of this source
	 */
	public LocationList getAllSourceLocs() {
		LocationList locList = new LocationList();
		Iterator it = this.surface.getAllByRowsIterator();
		while(it.hasNext()) locList.add((Location)it.next());
		return locList;
	}

}

