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

package org.opensha.sha.calc;



import java.io.IOException;
import java.rmi.server.UnicastRemoteObject;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;


/**
 * <p>Title: HazardCurveCalculator </p>
 * <p>Description: This class calculates the Hazard curve based on the
 * input parameters imr, site and eqkRupforecast</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Ned Field & Nitin Gupta & Vipin Gupta
 * @date Oct 28, 2002
 * @version 1.0
 */

public class PortfolioLossCurveCalculator extends UnicastRemoteObject {

	protected final static String C = "HazardCurveCalculator";
	protected final static boolean D = false;


	/* maximum permitted distance between fault and site to consider source in
  hazard analysis for that site; this default value is to allow all PEER test
  cases to pass through
	 */
	public final static double MAX_DISTANCE_DEFAULT = 200;
	protected double MAX_DISTANCE = MAX_DISTANCE_DEFAULT;

	protected int currRuptures = -1;
	protected int totRuptures=0;

	//index to keep track how many sources have been traversed
	protected int sourceIndex;
	// get total number of sources
	protected int numSources;

	/**
	 * creates the HazardCurveCalculator object
	 *
	 * @throws java.rmi.RemoteException
	 * @throws IOException
	 */
	public PortfolioLossCurveCalculator()
	throws java.rmi.RemoteException {}


	/**
	 * This sets the maximum distance of sources to be considered in the calculation
	 * (as determined by the getMinDistance(Site) method of ProbEqkSource subclasses).
	 * Sources more than this distance away are ignored.
	 * Default value is 250 km.
	 *
	 * @param distance: the maximum distance in km
	 */
	public void setMaxSourceDistance(double distance) throws java.rmi.RemoteException{
		MAX_DISTANCE = distance;
	}


	/**
	 * Returns the Annualized Rates for the Hazard Curves 
	 * @param hazFunction Discretized Hazard Function
	 * @return DiscretizedFuncAPI Annualized Rate Curve
	 */
	public DiscretizedFuncAPI getAnnualizedRates(DiscretizedFuncAPI hazFunction,double years) 
	throws java.rmi.RemoteException{
		DiscretizedFuncAPI annualizedRateFunc = hazFunction.deepClone();
		int size = annualizedRateFunc.getNum();
		for(int i=0;i<size;++i){
			annualizedRateFunc.set(i, - Math.log(1-annualizedRateFunc.getY(i))/years);
		}
		return annualizedRateFunc;
	}


	/**
	 * This function computes a hazard curve for the given Site, IMR, and ERF.  The curve
	 * in place in the passed in hazFunction (with the X-axis values being the IMLs for which
	 * exceedance probabilites are desired).
	 * @param hazFunction: This function is where the hazard curve is placed
	 * @param site: site object
	 * @param imr: selected IMR object
	 * @param eqkRupForecast: selected Earthquake rup forecast
	 * @return
	 */
	public DiscretizedFuncAPI getLossCurve(DiscretizedFuncAPI hazFunction,
			Site site, ScalarIntensityMeasureRelationshipAPI imr, EqkRupForecastAPI eqkRupForecast)
	throws java.rmi.RemoteException{
		// TODO Replace site with Portfolio
		this.currRuptures = -1;

		/* this determines how the calucations are done (doing it the way it's outlined
    in the paper SRL gives probs greater than 1 if the total rate of events for the
    source exceeds 1.0, even if the rates of individual ruptures are << 1).
		 */
		boolean poissonSource = false;

		ArbitrarilyDiscretizedFunc condProbFunc = (ArbitrarilyDiscretizedFunc) hazFunction.deepClone();
		ArbitrarilyDiscretizedFunc sourceHazFunc = (ArbitrarilyDiscretizedFunc) hazFunction.deepClone();

		//resetting the Parameter change Listeners on the AttenuationRelationship
		//parameters. This allows the Server version of our application to listen to the
		//parameter changes.
		((AttenuationRelationship)imr).resetParameterEventListeners();

		//System.out.println("hazFunction: "+hazFunction.toString());

		// declare some varibles used in the calculation
		double qkProb, distance;
		int k;

		// get the number of points
		int numPoints = hazFunction.getNum();

		// set the maximum distance in the attenuation relationship
		// (Note- other types of IMRs may not have this method so we should really check type here)
		imr.setUserMaxDistance(MAX_DISTANCE);

		// get total number of sources
		numSources = eqkRupForecast.getNumSources();
		//System.out.println("Number of Sources: "+numSources);
		//System.out.println("ERF info: "+ eqkRupForecast.getClass().getName());
		// compute the total number of ruptures for updating the progress bar
		totRuptures = 0;
		sourceIndex =0;
		for(sourceIndex=0;sourceIndex<numSources;++sourceIndex)
			totRuptures+=eqkRupForecast.getSource(sourceIndex).getNumRuptures();

		//System.out.println("Total number of ruptures:"+ totRuptures);


		// init the current rupture number (also for progress bar)
		currRuptures = 0;

		// initialize the hazard function to 1.0
		initDiscretizeValues(hazFunction, 1.0);

		// set the Site in IMR
		imr.setSite(site);

		// this boolean will tell us whether a source was actually used
		// (e.g., all could be outside MAX_DISTANCE)
		boolean sourceUsed = false;

		if (D) System.out.println(C+": starting hazard curve calculation");

		// loop over sources
		for(sourceIndex=0;sourceIndex < numSources ;sourceIndex++) {

			// get the ith source
			ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);

			// compute the source's distance from the site and skip if it's too far away
			distance = source.getMinDistance(site);
			if(distance > MAX_DISTANCE) {
				//update progress bar for skipped ruptures
				/*
        if(source.getRupture(0).getRuptureSurface().getNumCols() != 1) throw new RuntimeException("prob");
        System.out.println("rejected "+
        (float)source.getRupture(0).getRuptureSurface().getLocation(0,0).getLongitude()+"  "+
        (float)source.getRupture(0).getRuptureSurface().getLocation(0,0).getLatitude());
				 */
				currRuptures += source.getNumRuptures();
				continue;
			}

			// indicate that a source has been used
			sourceUsed = true;

			// determine whether it's poissonian
			poissonSource = source.isSourcePoissonian();

			// initialize the source hazard function to 0.0 if it's a non-poisson source
			if(!poissonSource)
				initDiscretizeValues(sourceHazFunc, 0.0);

			// get the number of ruptures for the current source
			int numRuptures = source.getNumRuptures();

			// loop over these ruptures
			for(int n=0; n < numRuptures ; n++,++currRuptures) {

				EqkRupture rupture = source.getRupture(n);
				// get the rupture probability
				qkProb = ((ProbEqkRupture)rupture).getProbability();

				// set the EqkRup in the IMR
				imr.setEqkRupture(rupture);

				// get the conditional probability of exceedance from the IMR
				condProbFunc=(ArbitrarilyDiscretizedFunc)imr.getExceedProbabilities(condProbFunc);


				// For poisson source
				if(poissonSource) {
					/* First make sure the probability isn't 1.0 (or too close); otherwise rates are
             infinite and all IMLs will be exceeded (because of ergodic assumption).  This
             can happen if the number of expected events (over the timespan) exceeds ~37,
             because at this point 1.0-Math.exp(-num) = 1.0 by numerical precision (and thus,
             an infinite number of events).  The number 30 used in the check below provides a
             safe margin.
					 */
					if(Math.log(1.0-qkProb) < -30.0)
						throw new RuntimeException("Error: The probability for this ProbEqkRupture ("+qkProb+
						") is too high for a Possion source (~infinite number of events)");

					for(k=0;k<numPoints;k++)
						hazFunction.set(k,hazFunction.getY(k)*Math.pow(1-qkProb,condProbFunc.getY(k)));
				}
				// For non-Poissin source
				else
					for(k=0;k<numPoints;k++)
						sourceHazFunc.set(k,sourceHazFunc.getY(k) + qkProb*condProbFunc.getY(k));
			}
			// for non-poisson source:
			if(!poissonSource)
				for(k=0;k<numPoints;k++)
					hazFunction.set(k,hazFunction.getY(k)*(1-sourceHazFunc.getY(k)));
		}

		int i;
		// finalize the hazard function
		if(sourceUsed)
			for(i=0;i<numPoints;++i)
				hazFunction.set(i,1-hazFunction.getY(i));
		else
			for(i=0;i<numPoints;++i)
				hazFunction.set(i,0.0);
		if (D) System.out.println(C+"hazFunction.toString"+hazFunction.toString());
		return hazFunction;
//		double tempVal = -1.0*Math.log(1.0-hazFunction.getY(1));
//		System.out.println(tempVal);
	}

	/**
	 *
	 * @returns the current rupture being traversed
	 * @throws java.rmi.RemoteException
	 */
	public int getCurrRuptures() throws java.rmi.RemoteException{
		return this.currRuptures;
	}

	/**
	 *
	 * @returns the total number of ruptures in the earthquake rupture forecast model
	 * @throws java.rmi.RemoteException
	 */
	public int getTotRuptures() throws java.rmi.RemoteException{
		return this.totRuptures;
	}

	/**
	 * stops the Hazard Curve calculations.
	 * @throws java.rmi.RemoteException
	 */
	public void stopCalc() throws java.rmi.RemoteException{
		sourceIndex = numSources;
	}

	/**
	 * Initialize the prob as 1 for the Hazard function
	 *
	 * @param arb
	 */
	protected void initDiscretizeValues(DiscretizedFuncAPI arb, double val){
		int num = arb.getNum();
		for(int i=0;i<num;++i)
			arb.set(i,val);
	}

	// this is temporary for testing purposes
	public static void main(String[] args) {
		double temp1, temp2, temp3, temp4;
		boolean OK;
		for(double n=1; n<2;n += 0.02) {
			temp1 = Math.pow(10,n);
			temp2 = 1.0-Math.exp(-temp1);
			temp3 = Math.log(1.0-temp2);
			temp4 = (temp3+temp1)/temp1;
			OK = temp1<=30;
			System.out.println((float)n+"\t"+temp1+"\t"+temp2+"\t"+temp3+"\t"+temp4+"\t"+OK);
		}
	}
}



