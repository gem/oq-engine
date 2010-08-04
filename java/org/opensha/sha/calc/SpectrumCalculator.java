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

import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;
import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

/**
 * <p>Title: SpectrumCalculator</p>
 *
 * <p>Description: This class computes the Spectral Values for given IML or Prob.
 * Value </p>
 *
 * @author Nitin Gupta
 * @version 1.0
 */
public class SpectrumCalculator extends UnicastRemoteObject
    implements SpectrumCalculatorAPI {


  protected final static String C = "SpectrumCalculator";
  protected final static boolean D = false;
  
  //Info for parameter that sets the maximum distance considered
  private DoubleParameter maxDistanceParam;
  public final static String MAX_DISTANCE_PARAM_NAME = "Maximum Distance";
  public final String MAX_DISTANCE_PARAM_UNITS = "km";
  public final String MAX_DISTANCE_PARAM_INFO = "Earthquake Ruptures beyond this distance are ignored";
  public final double MAX_DISTANCE_PARAM_MIN = 0;
  public final double MAX_DISTANCE_PARAM_MAX = 40000;
  public final static Double MAX_DISTANCE_DEFAULT = new Double(200);
  
  private ParameterList adjustableParams;


  protected int currRuptures = -1;
  protected int totRuptures = 0;

  //index to keep track how many sources have been traversed
  protected int sourceIndex;
  // get total number of sources
  protected int numSources;


  /**
   * SpectrumCalculator
   *
   * @throws RemoteException
   */
  public SpectrumCalculator() throws RemoteException {
	  
	  // Create adjustable parameters and add to list
	  
	  // Max Distance Parameter
	  maxDistanceParam = new DoubleParameter(MAX_DISTANCE_PARAM_NAME, MAX_DISTANCE_PARAM_MIN, 
			  MAX_DISTANCE_PARAM_MAX, MAX_DISTANCE_PARAM_UNITS, MAX_DISTANCE_DEFAULT);
	  maxDistanceParam.setInfo(MAX_DISTANCE_PARAM_INFO);

      adjustableParams = new ParameterList();
	  adjustableParams.addParameter(maxDistanceParam);
  }
  
  /**
  *
  * @returns the adjustable ParameterList
  */
 public ParameterList getAdjustableParams()  throws java.rmi.RemoteException{
   return this.adjustableParams;
 }

 
 /**
 *
 * @returns This was created so new instances of this calculator could be
 * given pointers to a set of parameter that already exist.
 */
public void setAdjustableParams(ParameterList paramList)  throws java.rmi.RemoteException{
  this.adjustableParams = paramList;
  this.maxDistanceParam= (DoubleParameter)paramList.getParameter(this.MAX_DISTANCE_PARAM_NAME);
}

/**
 * This is a direct way of getting the distance cutoff from that parameter
 */
public double getMaxSourceDistance() throws java.rmi.RemoteException { 
	  return maxDistanceParam.getValue().doubleValue(); 
}

 
 /**
  * get the adjustable parameters
  *
  * @return
  */
 public ListIterator getAdjustableParamsIterator()  throws java.rmi.RemoteException{
   return adjustableParams.getParametersIterator();
 }



 /**
  * This sets the maximum distance of sources to be considered in the calculation.
  * Sources more than this distance away are ignored.  This is simply a direct
  * way of setting the parameter.
  * Default value is 250 km.
  *
  * @param distance: the maximum distance in km
  */
 public void setMaxSourceDistance(double distance) throws java.rmi.RemoteException{
	  maxDistanceParam.setValue(distance);
 }

  /**
   * This function computes a spectrum curve for all SA Period supported
   * by the IMR and then interpolates the IML value from all the computed curves.
   * The curve in place in the passed in hazFunction
   * (with the X-axis values being the IMLs for which exceedance probabilites are desired).
   * @param specFunction: This function is where the final interplotaed spectrum
   * for the IML@prob curve is placed.
   * @param site: site object
   * @param imr: selected IMR object
   * @param eqkRupForecast: selected Earthquake rup forecast
   * @return
   */
  public DiscretizedFuncAPI getIML_SpectrumCurve(DiscretizedFuncAPI spectrumFunction,
                                           Site site,
                                           ScalarIntensityMeasureRelationshipAPI imr,
                                           EqkRupForecastAPI eqkRupForecast,
                                           double probVal,
                                           ArrayList supportedSA_Periods) throws
      java.rmi.RemoteException {

    this.currRuptures = -1;

    /* this determines how the calucations are done (doing it the way it's outlined
     in the paper SRL gives probs greater than 1 if the total rate of events for the
     source exceeds 1.0, even if the rates of individual ruptures are << 1).
     */
    boolean poissonSource = false;
    //creates a new Arb function with X value being in Log scale and Y values as 1.0
    DiscretizedFuncAPI tempSpecFunc =initDiscretizedValuesToLog(spectrumFunction,1.0);

    int numSAPeriods = supportedSA_Periods.size();
    DiscretizedFuncAPI[] hazFunction = new ArbitrarilyDiscretizedFunc[numSAPeriods];
    DiscretizedFuncAPI[] sourceHazFunc = new ArbitrarilyDiscretizedFunc[numSAPeriods];

    for(int i=0;i<numSAPeriods;++i){
      hazFunction[i] = tempSpecFunc.deepClone();
      sourceHazFunc[i] = tempSpecFunc.deepClone();
    }
    ArbitrarilyDiscretizedFunc condProbFunc = (ArbitrarilyDiscretizedFunc)
        tempSpecFunc.deepClone();


    //resetting the Parameter change Listeners on the AttenuationRelationship
    //parameters. This allows the Server version of our application to listen to the
    //parameter changes.
    ( (AttenuationRelationship) imr).resetParameterEventListeners();

    //System.out.println("hazFunction: "+hazFunction.toString());

    // declare some varibles used in the calculation
    double qkProb, distance;
    int k;

    // get the number of points
    int numPoints = tempSpecFunc.getNum();
    
    double maxDistance = maxDistanceParam.getValue();

    // set the maximum distance in the attenuation relationship
    // (Note- other types of IMRs may not have this method so we should really check type here)
    imr.setUserMaxDistance(maxDistance);

    // get total number of sources
    numSources = eqkRupForecast.getNumSources();
    //System.out.println("Number of Sources: "+numSources);
    //System.out.println("ERF info: "+ eqkRupForecast.getClass().getName());
    // compute the total number of ruptures for updating the progress bar
    totRuptures = 0;
    sourceIndex = 0;
    for (sourceIndex = 0; sourceIndex < numSources; ++sourceIndex)
      totRuptures += eqkRupForecast.getSource(sourceIndex).getNumRuptures();


    //System.out.println("Total number of ruptures:"+ totRuptures);


    // init the current rupture number (also for progress bar)
    currRuptures = 0;


    // set the Site in IMR
    imr.setSite(site);

    // this boolean will tell us whether a source was actually used
    // (e.g., all could be outside MAX_DISTANCE)
    boolean sourceUsed = false;

    if (D)
      System.out.println(C + ": starting hazard curve calculation");

    // loop over sources
    for (sourceIndex = 0; sourceIndex < numSources; sourceIndex++) {

      // get the ith source
      ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);

      // compute the source's distance from the site and skip if it's too far away
      distance = source.getMinDistance(site);
      if (distance > maxDistance) {
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
      if (!poissonSource)
        for(int m=0;m<numSAPeriods;++m)
          initDiscretizeValues(sourceHazFunc[m], 0.0);

      // get the number of ruptures for the current source
      int numRuptures = source.getNumRuptures();

      // loop over these ruptures
      for (int n = 0; n < numRuptures; n++, ++currRuptures) {

        EqkRupture rupture = source.getRupture(n);
        // get the rupture probability
        qkProb = ( (ProbEqkRupture) rupture).getProbability();

        // set the EqkRup in the IMR
        imr.setEqkRupture(rupture);

        //looping over all the SA Periods to get the ExceedProb Val for each.
        for (int saPeriodIndex = 0; saPeriodIndex < numSAPeriods; ++saPeriodIndex) {
          imr.getParameter(PeriodParam.NAME).setValue(
              supportedSA_Periods.get(saPeriodIndex));

          // get the conditional probability of exceedance from the IMR
          condProbFunc = (ArbitrarilyDiscretizedFunc) imr.getExceedProbabilities(
              condProbFunc);
          //System.out.println("CurrentRupture: "+currRuptures);
          // For poisson source
          if (poissonSource) {
            /* First make sure the probability isn't 1.0 (or too close); otherwise rates are
             infinite and all IMLs will be exceeded (because of ergodic assumption).  This
             can happen if the number of expected events (over the timespan) exceeds ~37,
             because at this point 1.0-Math.exp(-num) = 1.0 by numerical precision (and thus,
             an infinite number of events).  The number 30 used in the check below provides a
             safe margin */
            if (Math.log(1.0 - qkProb) < -30.0)
              throw new RuntimeException(
                  "Error: The probability for this ProbEqkRupture (" + qkProb +
                  ") is too high for a Possion source (~infinite number of events)");

            for (k = 0; k < numPoints; k++)
              hazFunction[saPeriodIndex].set(k,
                                             hazFunction[saPeriodIndex].getY(k) *
                                             Math.pow(1 - qkProb, condProbFunc.getY(k)));
          }
          // For non-Poissin source
          else
            for (k = 0; k < numPoints; k++)
              sourceHazFunc[saPeriodIndex].set(k,
                                sourceHazFunc[saPeriodIndex].getY(k) +
                                qkProb * condProbFunc.getY(k));
        }
      }
      // for non-poisson source:
      if (!poissonSource)
        for(int i=0;i<numSAPeriods;++i)
          for (k = 0; k < numPoints; k++)
            hazFunction[i].set(k, hazFunction[i].getY(k) * (1 - sourceHazFunc[i].getY(k)));
    }

    int i;
    // finalize the hazard function
    if (sourceUsed)
      for(int j=0;j<numSAPeriods;++j)
        for (i = 0; i < numPoints; ++i)
          hazFunction[j].set(i, 1 - hazFunction[j].getY(i));
    else
      for(int j=0;j<numSAPeriods;++j)
        for (i = 0; i < numPoints; ++i)
          hazFunction[j].set(i, 0.0);

    //creating the temp functionlist that gets the linear X Value for each SA-Period
    //spectrum curve.
    DiscretizedFuncAPI[] tempHazFunction = new ArbitrarilyDiscretizedFunc[numSAPeriods];
    for(int j=0;j<numSAPeriods;++j){
      tempHazFunction[j] = new ArbitrarilyDiscretizedFunc();
      for (i = 0; i < numPoints; ++i) {
        tempHazFunction[j].set(spectrumFunction.getX(i),hazFunction[j].getY(i));
      }
    }
    //creating the Spectrum function by interpolating in Log space the IML vals
    //for the given prob. value. It is done for each SA period function.
    DiscretizedFuncAPI imlSpectrumFunction = new ArbitrarilyDiscretizedFunc();
    for(int j=0;j<numSAPeriods;++j){
      double val = tempHazFunction[j].getFirstInterpolatedX_inLogXLogYDomain(probVal);
      imlSpectrumFunction.set(((Double)supportedSA_Periods.get(j)).doubleValue(), val);
    }

    if (D)
      System.out.println(C + "hazFunction.toString" + hazFunction.toString());
    return imlSpectrumFunction;
  }


  /**
   * Initialize the prob as 1 for the Hazard function
   *
   * @param arb
   */
  private void initDiscretizeValues(DiscretizedFuncAPI arb, double val){
    int num = arb.getNum();
    for(int i=0;i<num;++i)
      arb.set(i,val);
  }


  /**
   * Converts a Linear Arb. function to a function with X values being the Log scale.
   * It does not modify the original function, an returns  a new function.
   * @param linearFunc DiscretizedFuncAPI Linear Arb function
   * @param val double values to initialize the Y value of the Arb function with.
   * @return DiscretizedFuncAPI Arb function with X values being the log scale.
   */
  private DiscretizedFuncAPI initDiscretizedValuesToLog(DiscretizedFuncAPI linearFunc,double val){
    DiscretizedFuncAPI toXLogFunc = new ArbitrarilyDiscretizedFunc();
    if (IMT_Info.isIMT_LogNormalDist(SA_Param.NAME))
      for (int i = 0; i < linearFunc.getNum(); ++i)
        toXLogFunc.set(Math.log(linearFunc.getX(i)), val);
    return toXLogFunc;
  }



  /**
   * This function computes a spectrum curve for the given Site, IMR, and ERF.  The curve
   * in place in the passed in hazFunction (with the X-axis values being the SA
   * Periods for which exceedance probabilites are desired).
   * @param hazFunction: This function is where the hazard curve is placed
   * @param site: site object
   * @param imr: selected IMR object
   * @param eqkRupForecast: selected Earthquake rup forecast
   * @return
   */
  public DiscretizedFuncAPI getSpectrumCurve(Site site,
                                             ScalarIntensityMeasureRelationshipAPI imr,
                                             EqkRupForecastAPI eqkRupForecast,
                                             double imlVal,
                                             ArrayList supportedSA_Periods) throws
      RemoteException {

    //creating the Master function that initializes the Function with supported SA Periods Vals
    DiscretizedFuncAPI hazFunction = new ArbitrarilyDiscretizedFunc();
    initDiscretizeValues(hazFunction, supportedSA_Periods, 1.0);
    int numPoints = hazFunction.getNum();


     this.currRuptures = -1;

     /* this determines how the calucations are done (doing it the way it's outlined
     in the paper SRL gives probs greater than 1 if the total rate of events for the
     source exceeds 1.0, even if the rates of individual ruptures are << 1).
     */
     boolean poissonSource = false;

     //resetting the Parameter change Listeners on the AttenuationRelationship
     //parameters. This allows the Server version of our application to listen to the
     //parameter changes.
     ((AttenuationRelationship)imr).resetParameterEventListeners();

     //System.out.println("hazFunction: "+hazFunction.toString());

     // declare some varibles used in the calculation
     double qkProb, distance;
     int k;
     
     double maxDistance = maxDistanceParam.getValue();

     // set the maximum distance in the attenuation relationship
     // (Note- other types of IMRs may not have this method so we should really check type here)
     imr.setUserMaxDistance(maxDistance);



     //Source func
     DiscretizedFuncAPI sourceHazFunc = new ArbitrarilyDiscretizedFunc();
     initDiscretizeValues(sourceHazFunc,supportedSA_Periods,0.0);

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
       if(distance > maxDistance) {
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

       // get the number of ruptures for the current source
       int numRuptures = source.getNumRuptures();

       // loop over these ruptures
       for(int n=0; n < numRuptures ; n++,++currRuptures) {

         EqkRupture rupture = source.getRupture(n);
         // get the rupture probability
         qkProb = ((ProbEqkRupture)rupture).getProbability();

         // set the EqkRup in the IMR
         imr.setEqkRupture(rupture);

         DiscretizedFuncAPI condProbFunc = null;


         // get the conditional probability of exceedance from the IMR
         condProbFunc = (DiscretizedFuncAPI) imr.getSA_ExceedProbSpectrum(Math.log(
             imlVal));
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
   }



   /**
    *
    * @returns the current rupture being traversed
    * @throws java.rmi.RemoteException
    */
   public int getCurrRuptures() throws java.rmi.RemoteException {
     return this.currRuptures;
   }

   /**
    *
    * @returns the total number of ruptures in the earthquake rupture forecast model
    * @throws java.rmi.RemoteException
    */
   public int getTotRuptures() throws java.rmi.RemoteException {
     return this.totRuptures;
   }



   /**
    * Initialize the prob as 1 for the Hazard function
    *
    * @param arb
    */
   private void initDiscretizeValues(DiscretizedFuncAPI arb, ArrayList supportedSA_Periods,
                                       double val){
     int num = supportedSA_Periods.size();
     for(int i=0;i<num;++i)
       arb.set(((Double)supportedSA_Periods.get(i)).doubleValue(),val);
   }


   /**
    * This function computes a deterministic exceedance curve for the given Site, IMR, and ProbEqkrupture.  The curve
    * in place in the passed in hazFunction (with the X-axis values being the IMLs for which
    * exceedance probabilites are desired).
    * @param hazFunction: This function is where the hazard curve is placed
    * @param site: site object
    * @param imr: selected IMR object
    * @param rupture: Single Earthquake Rupture
    * @return
    */
   public DiscretizedFuncAPI getDeterministicSpectrumCurve(
       Site site, ScalarIntensityMeasureRelationshipAPI imr, EqkRupture rupture,
        boolean probAtIML, double imlProbVal)  throws RemoteException{


     //resetting the Parameter change Listeners on the AttenuationRelationship
     //parameters. This allows the Server version of our application to listen to the
     //parameter changes.
     ( (AttenuationRelationship) imr).resetParameterEventListeners();

     //System.out.println("hazFunction: "+hazFunction.toString());

     // set the Site in IMR
     imr.setSite(site);

     if (D) System.out.println(C + ": starting hazard curve calculation");

     // set the EqkRup in the IMR
     imr.setEqkRupture(rupture);

     DiscretizedFuncAPI hazFunction = null;
     if(probAtIML)
       // get the conditional probability of exceedance from the IMR
       hazFunction = (DiscretizedFuncAPI) imr.getSA_ExceedProbSpectrum(Math.log(imlProbVal));
     else{
       hazFunction = (DiscretizedFuncAPI) imr.getSA_IML_AtExceedProbSpectrum(
           imlProbVal);
       int numPoints = hazFunction.getNum();
       for(int i=0;i<numPoints;++i){
         hazFunction.set(i,Math.exp(hazFunction.getY(i)));
       }
     }
     if (D) System.out.println(C + "hazFunction.toString" + hazFunction.toString());
     return hazFunction;
  }


}
