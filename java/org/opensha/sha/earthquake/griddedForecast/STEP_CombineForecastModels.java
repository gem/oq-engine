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

package org.opensha.sha.earthquake.griddedForecast;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.GregorianCalendar;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.TimeZone;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagLengthRelationship;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupList;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupture;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.SimpleFaultData;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

import scratch.matt.calc.AkaikeInformationCriterion;
import scratch.matt.calc.BackGroundRatesGrid;
import scratch.matt.calc.CalcAIC_Weights;
import scratch.matt.calc.CompletenessMagCalc;
import scratch.matt.calc.CountObsInGrid;
import scratch.matt.calc.DistDecayFromRupCalc;
import scratch.matt.calc.OgataLogLike_Calc;
import scratch.matt.calc.RegionDefaults;
import scratch.matt.calc.STEP_TypeIIAftershockZone_Calc;

/**
 * <p>Title: </p>
 *
 * <p>Description: </p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 *
 * <p>Company: </p>
 *
 * @author not attributable
 * @version 1.0
 */
public class STEP_CombineForecastModels
    extends AfterShockHypoMagFreqDistForecast {

  public double minForecastMag;
  private double maxForecastMag;
  private double deltaMag;
  //private int numHypoLocation;
  //private double[] grid_aVal, grid_bVal, grid_cVal, grid_pVal, grid_kVal;
  //private double[] node_CompletenessMag;
  private SimpleFaultData mainshockFault;
  public boolean useFixed_cValue = true;
  private boolean hasExternalFaultModel = false;
  private boolean useCircularRegion = false;
  private boolean useSausageRegion = false;
  public double addToMc;
  private double zoneRadius;
  private double gridSpacing;
  private GregorianCalendar forecastEndTime, currentTime;
  private boolean isStatic = false, isPrimary = true,
      isSecondary = false, useSeqAndSpatial = false;
  private ArrayList griddedMagFreqDistForecast;
//private ObsEqkRupList newAftershocksInZone;
  //private RegionDefaults rDefs;
  private TimeSpan timeSpan;
  private double daysSinceMainshockStart, daysSinceMainshockEnd;
  private BackGroundRatesGrid backgroundRatesGrid;
  private double[] kScaler;
  private GenericAfterHypoMagFreqDistForecast genElement;
  private SequenceAfterHypoMagFreqDistForecast seqElement = null;
  private SpatialAfterHypoMagFreqDistForecast spaElement = null;
  private HypoMagFreqDistAtLoc combinedForecast[];
  //private double sampleSizeAIC;
  private GriddedRegion aftershockZone;
  private boolean existSeqElement = false, existSpaElement = false; 
  private boolean usedInForecast = false;
  
  /**
   * STEP_AftershockForecast
   */
  public STEP_CombineForecastModels(ObsEqkRupture mainshock,
                                 BackGroundRatesGrid
                                 backgroundRatesGrid, GregorianCalendar currentTime) {
    this.mainShock = mainshock;
    this.backgroundRatesGrid = backgroundRatesGrid;
    this.currentTime = currentTime;
    //this.rDefs = rDefs;

    this.set_CurrentTime();
    this.calcTimeSpan();
    this.setDaysSinceMainshock();

    /**
     * initialise the aftershock zone and mainshock for this model
     */
    this.set_AftershockZoneRadius();
    this.calcTypeI_AftershockZone();
    ObsEqkRupList emptyAftershocks = new ObsEqkRupList();
    this.setAfterShocks(emptyAftershocks);
    //this.aftershockZone = this.getAfterShockZone();
    double[] kScaler = DistDecayFromRupCalc.getDensity(this.mainShock,aftershockZone);
    
    GenericAfterHypoMagFreqDistForecast genElement =
        new GenericAfterHypoMagFreqDistForecast(this.mainShock,aftershockZone,kScaler);
        this.genElement = genElement;
    this.setChildParms(genElement);
  }

  /**
   * setChildParms
   */
  private void setChildParms(STEP_AftershockForecast model) {
    model.setTimeSpan(timeSpan);
    model.setMinForecastMag(RegionDefaults.minForecastMag);
    model.setMaxForecastMag(RegionDefaults.maxForecastMag);
    model.setDeltaForecastMag(RegionDefaults.deltaForecastMag);
    model.setUseFixed_cValue(RegionDefaults.useFixed_cValue);
    model.dayStart = this.daysSinceMainshockStart;
    model.dayEnd = this.daysSinceMainshockEnd;
  }


  /**
   * createSequenceElement
   */
  public void createSequenceElement() {
	this.existSeqElement = true;
    SequenceAfterHypoMagFreqDistForecast seqElement =
        new SequenceAfterHypoMagFreqDistForecast(this.mainShock,this.getAfterShockZone(),this.getAfterShocks());
    seqElement.set_kScaler(kScaler);
    this.setChildParms(seqElement); 
    this.seqElement = seqElement;
  }

  /**
   * createSpatialElement
   */
  public void createSpatialElement() {
	  this.existSpaElement = true;
    SpatialAfterHypoMagFreqDistForecast spaElement =
        new SpatialAfterHypoMagFreqDistForecast(this.mainShock,this.getAfterShockZone(),this.getAfterShocks());
    this.setChildParms(spaElement);    
    this.spaElement = spaElement;
  }
  
  /**
   * createCombinedForecast
   * 
   * Combine the 3 forecasts into a single forecast using AIC weighting
   *
   */
  public void createCombinedForecast(){
	  IncrementalMagFreqDist genDist, seqDist, spaDist, combDist;
	  //HypoMagFreqDistAtLoc combHypoMagFreqDist;
	  double genLikelihood, seqLikelihood, spaLikelihood;
	  double genAIC, seqAIC, spaAIC;
	  double[] genOmoriVals = new double[3];
	  double[] seqOmoriVals = new double[3];
	  double[] spaOmoriVals = new double[3];
	  
	  // first we must calculate the Ogata-Omori likelihood score at each
	  // gridnode, for each model element created
	  if (this.useSeqAndSpatial) {
		  int numGridNodes = this.getAfterShockZone().getNodeCount();
		
		  combinedForecast = new HypoMagFreqDistAtLoc[numGridNodes];
		  
		  // first find the number observed number within each grid cell for AIC calcs
		  CountObsInGrid numInGridCalc =  new CountObsInGrid(this.afterShocks,this.aftershockZone);
		  int[] griddedNumObs = numInGridCalc.getNumObsInGridList();
		  
		  // get the generic p and c - the same everywhere
		  genOmoriVals[2] = this.genElement.get_p_valueGeneric();
		  genOmoriVals[1] = this.genElement.get_c_valueGeneric();
		  
		  // get the sequence p and c - the same everywhere
		  seqOmoriVals[2] = this.seqElement.get_pValSequence();
		  seqOmoriVals[1] = this.seqElement.get_cVal_Sequence();
		  
		  /** loop over all grid nodes
		   *  get the likelihood for each node, for each model element
		   *  then calc the AICc score
		   */
		  //int gLoop = 0;
		  
		  // is this correct to be iterating over region, an EvenlyGriddedAPI??
		  //Iterator<Location> gridIt = getRegion().getNodeList().iterator();
		  
		  //while ( gridIt.hasNext() ){
		  for (int gLoop = 0; gLoop < numGridNodes; gLoop++){
			  // first find the events that should be associated with this grid cell
			  // gridSearchRadius is the radius used for calculating the Reasenberg & Jones params
			  double radius = this.spaElement.getGridSearchRadius();
			  ObsEqkRupList gridEvents;
			  Region nodeRegion = new Region(getRegion().locationForIndex(gLoop),radius);
			  gridEvents = this.afterShocks.getObsEqkRupsInside(nodeRegion);
			  
			  // get the smoothed generic k val for the grid node
		 	  genOmoriVals[0] = this.genElement.get_k_valueGenericAtLoc(gLoop);
		 	  // 1st calculate the Ogata likelihood of the generic parameters
		 	  OgataLogLike_Calc genOgataCalc = new OgataLogLike_Calc(genOmoriVals,gridEvents);
			  genLikelihood = genOgataCalc.get_OgataLogLikelihood();
			  // get the AIC score for the generic likelihood
			  AkaikeInformationCriterion genAIC_Calc = new AkaikeInformationCriterion(griddedNumObs[gLoop],RegionDefaults.genNumFreeParams,genLikelihood);
			  genAIC = genAIC_Calc.getAIC_Score();
			  
			  // get the smoothed k val for the sequence model for the grid node
			  seqOmoriVals[0] = this.seqElement.get_kVal_SequenceAtLoc(gLoop);
			  // now calculate the likelihood for the sequence parameters
			  OgataLogLike_Calc seqOgataCalc = new OgataLogLike_Calc(seqOmoriVals,gridEvents);
			  seqLikelihood = seqOgataCalc.get_OgataLogLikelihood();
			  // get the AIC score for the sequence likelihood
			  AkaikeInformationCriterion seqAIC_Calc = new AkaikeInformationCriterion(griddedNumObs[gLoop],RegionDefaults.seqNumFreeParams,seqLikelihood);
			  seqAIC = seqAIC_Calc.getAIC_Score();
			  
			  // get the parameters for the spatial  model for the grid node
			  spaOmoriVals[0] = this.spaElement.get_Spa_kValueAtLoc(gLoop);
			  spaOmoriVals[1] = this.spaElement.get_Spa_cValueAtLoc(gLoop);
			  spaOmoriVals[2] = this.spaElement.get_Spa_pValueAtLoc(gLoop);
			  // now calculate the likelihood for the spatial parameters
			  OgataLogLike_Calc spaOgataCalc = new OgataLogLike_Calc(spaOmoriVals,gridEvents);
			  spaLikelihood = spaOgataCalc.get_OgataLogLikelihood();
			  // get the AIC score for the spatial likelihood
			  AkaikeInformationCriterion spaAIC_Calc = new AkaikeInformationCriterion(griddedNumObs[gLoop],RegionDefaults.spaNumFreeParams,spaLikelihood);
			  spaAIC = spaAIC_Calc.getAIC_Score();
			  
			  // calculate the weighting factor for each model element
			  // forecast based on its AIC score.  
			  CalcAIC_Weights.calcWeights(genAIC,seqAIC,spaAIC);
			  double genWeight = CalcAIC_Weights.getGenWeight();
			  double seqWeight = CalcAIC_Weights.getSeqWeight();
			  double spaWeight = CalcAIC_Weights.getSpaWeight();
			  
			  // get the HypoMagFreqDist forecast for this location for each model element
			  genDist = this.genElement.getHypoMagFreqDistAtLoc(gLoop).getFirstMagFreqDist();
			  seqDist = this.seqElement.getHypoMagFreqDistAtLoc(gLoop).getFirstMagFreqDist(); 
			  spaDist = this.spaElement.getHypoMagFreqDistAtLoc(gLoop).getFirstMagFreqDist();
			  
			  			  
			  int numMags = (int)((genDist.getMaxX()-genDist.getMinX())/genDist.getDelta())+1;
			  combDist = new IncrementalMagFreqDist(RegionDefaults.minForecastMag,RegionDefaults.maxForecastMag,
					  numMags);
			  for (int mLoop = 0; mLoop < numMags; mLoop++){
				  // set the combined rate for each mag in the entire mag range
				  combDist.set(mLoop,genDist.getIncrRate(mLoop)*genWeight +
				  seqDist.getIncrRate(mLoop)*seqWeight + spaDist.getIncrRate(mLoop)*spaWeight); 
			  }
			  

			  HypoMagFreqDistAtLoc combHypoMagFreqDist = new HypoMagFreqDistAtLoc(combDist,genElement.getLocInGrid(gLoop));

			  this.combinedForecast[gLoop]=combHypoMagFreqDist;
		  
		  }
	  
	  }
	  else{
		  this.combinedForecast = genElement.griddedMagFreqDistForecast; //if there is no spatial or seq element just use the generic
	  }
		  
	  
  }

  /**
   * setRegionDefaults
   */
  //public void setRegionDefaults(RegionDefaults rDefs) {
  //  this.rDefs = rDefs;
  //}


  /**
   * calc_NodeCompletenessMag
   * calculate the completeness at each node
   */
  //public abstract void calc_NodeCompletenessMag();

  /**
   * set_minForecastMag
   * the minimum forecast magnitude
   */
  public void set_minForecastMag(double min_forecastMag) {
    minForecastMag = min_forecastMag;
  }

  /**
   * set_maxForecastMag
   * the maximum forecast magnitude
   */
  public void set_maxForecastMag(double max_forecastMag) {
    maxForecastMag = max_forecastMag;
  }

  /**
   * set_deltaMag
   * the magnitude step for the binning of the forecasted magnitude
   */
  public void set_deltaMag(double delta_mag) {
    deltaMag = delta_mag;
  }

  /**
   * set_GridSpacing
   */
  public void set_GridSpacing(double grid_spacing) {
    gridSpacing = grid_spacing;
  }

  /**
   * setUseFixed_cVal
   * if true c will be fixed for the Omori calculations
   * default is fixed
   */
  public void setUseFixed_cVal(boolean fix_cVal) {
    useFixed_cValue = fix_cVal;
  }
  
  /**
   * set_UsedInForecast
   * This will be set to true is any node in this model
   * forecasts greater rates than the background
   * the default is false.
   * @param used
   */
  public void set_UsedInForecast(boolean used){
  	usedInForecast = used;
  }

  /**
   * set_addToMcConstant
   */
  public void set_addToMcConstant(double mcConst) {
    addToMc = mcConst;
  }

  /**
   * set_isStatic
   * if true the sequence will take no more aftershocks
   */
  public void set_isStatic(boolean isStatic) {
    this.isStatic = isStatic;
  }

  /**
   * set_isPrimary
   * if true the sequence can be any model type (generic, sequence, sp. var)
   * set_isPrimary controls both primary and secondary.
   */
  public void set_isPrimary(boolean isPrimary) {
    this.isPrimary = isPrimary;
    if (isPrimary) {
      this.set_isSecondary(false);
    }
    else {
      this.set_isSecondary(true);
    }

  }

  /**
   * set_isSecondary
   * if isSecondary is true the model will be forced to be generic.
   *
   */
  private void set_isSecondary(boolean isSecondary) {
    this.isSecondary = isSecondary;
  }

  /**
   * setNewObsEventsList
   * This should contain All new events - this is the list that will
   * be used to look for new aftershocks.
   */
  //public void setNewObsEventsList(ObsEqkRupList newObsEventList) {
  //}

  /**
   * set_PreviousAftershocks
   * this will pass the aftershocks for this sequence that were saved in
   * the last run of the code.
   */
  public void set_PreviousAftershocks(ObsEqkRupList previousAftershockList) {
  }

  /**
   * set_AftershockZoneRadius
   * set the radius based on Wells and Coppersmith
   *
   * THIS USES A DIFFERENT RADIUS THAN I HAVE PREVIOUSLY USED!
   * NEED TO ADD THE SUBSURFACE RUPTURE LENGTH REL TO WC1994
   */
  public void set_AftershockZoneRadius() {
    ObsEqkRupture mainshock = this.getMainShock();
    double mainshockMag = mainshock.getMag();
    WC1994_MagLengthRelationship WCRel = new WC1994_MagLengthRelationship();
    this.zoneRadius = WCRel.getMedianLength(mainshockMag);
  }

  /**
   * calcTypeI_AftershockZone
   */
  public void calcTypeI_AftershockZone() {

    if (hasExternalFaultModel) {
      // This needs to be set up to read an external fault model.
    }
    else {
      ObsEqkRupture mainshock = this.getMainShock();
      Location mainshockLocation = mainshock.getHypocenterLocation();
//      this.aftershockZone = new GriddedRegion(
//    		  mainshockLocation, zoneRadius, RegionDefaults.gridSpacing, new Location(0,0));
//      this.aftershockZone.createRegionLocationsList(backgroundRatesGrid.getRegion());
      
      // NOTE: baishan this may not be working right; replaces above code
      Region asZoneGR = new Region(mainshockLocation, zoneRadius);
      aftershockZone = backgroundRatesGrid.getRegion().subRegion(asZoneGR);
      // end NOTE
      
      
       setRegion(aftershockZone);
       this.useCircularRegion = true;
      
      // make a fault that is only a single point.
      //String faultName = "typeIfault";
      //FaultTrace fault_trace = new FaultTrace(faultName);
      //fault_trace.addLocation(mainshock.getHypocenterLocation());
      //set_FaultSurface(fault_trace);
    }
  }

  /**
   * This will calculate the appropriate afershock zone based on the availability
   * of an external model, a circular Type I model, and a sausage shaped Type II model
   * Type II is only calculated if more than 100 events are found in the circular
   * Type II model.
   *
   * This will also set the aftershock list.
   */

  public void calcTypeII_AfterShockZone(ObsEqkRupList aftershockList,
                                        GriddedRegion
                                        backGroundRatesGrid) {
    if (hasExternalFaultModel) {
      // This needs to be set up to read an external fault model.
    }
    else {
      STEP_TypeIIAftershockZone_Calc typeIIcalc = new STEP_TypeIIAftershockZone_Calc(aftershockList, this);
      //GriddedRegion typeII_Zone = typeIIcalc.get_TypeIIAftershockZone();
      //typeII_Zone.createRegionLocationsList(backGroundRatesGrid); 

      // NOTE: baishan this may not be working right; replaces above code
      GriddedRegion typeII_Zone = 
    	  backGroundRatesGrid.subRegion(typeIIcalc.get_TypeIIAftershockZone());
      // end NOTE
      
      setRegion(typeII_Zone);
      //this.region = typeII_Zone;
      this.useSausageRegion = true;
     
      LocationList faultPoints = typeIIcalc.getTypeIIFaultModel();
      String faultName = "typeIIfault";
      // add the synthetic fault to the fault trace
      // do not add the 2nd element as it is the same as the 3rd (the mainshock location)
      FaultTrace fault_trace = new FaultTrace(faultName);
      fault_trace.add(faultPoints.get(0));
      fault_trace.add(faultPoints.get(1));
      fault_trace.add(faultPoints.get(3));
      //set_FaultSurface(fault_trace);
    }
  }

  /**
   * set_CurrentTime
   * this sets the forecast start time as the current time.
   */
  private void set_CurrentTime() {
    Calendar curTime = new GregorianCalendar(TimeZone.getTimeZone(
        "GMT"));
    int year = curTime.get(Calendar.YEAR);
    int month = curTime.get(Calendar.MONTH);
    int day = curTime.get(Calendar.DAY_OF_MONTH);
    int hour24 = curTime.get(Calendar.HOUR_OF_DAY);
    int min = curTime.get(Calendar.MINUTE);
    int sec = curTime.get(Calendar.SECOND);

    this.currentTime = new GregorianCalendar(year, month,
        day, hour24, min, sec);
  }
  
  public void set_CurrentTime(GregorianCalendar currentTime){
	  this.currentTime = currentTime;
  }

  /**
   * calcTimeSpan
   */
  public void calcTimeSpan() {
    String durationUnits = "Days";
    String timePrecision = "Seconds";
    timeSpan = new TimeSpan(timePrecision, durationUnits);

    if (RegionDefaults.startForecastAtCurrentTime) {
      set_CurrentTime();
      timeSpan.setStartTime(currentTime);
      timeSpan.setDuration(RegionDefaults.forecastLengthDays);
    }
    else {
      timeSpan.setStartTime(RegionDefaults.forecastStartTime);
      timeSpan.setDuration(RegionDefaults.forecastLengthDays);
    }
    this.setTimeSpan(timeSpan);
  }

  /**
   * setDaysSinceMainshock
   */
  public void setDaysSinceMainshock() {
    String durationUnits = "Days";
    GregorianCalendar startDate = this.timeSpan.getStartTimeCalendar();
    //System.out.println("From Timespan ="+startDate.toString());
    double duration = this.timeSpan.getDuration(durationUnits);
    ObsEqkRupture mainshock = this.getMainShock();
    GregorianCalendar mainshockDate = mainshock.getOriginTime();
    double startInMils = startDate.getTimeInMillis();
    double mainshockInMils = mainshockDate.getTimeInMillis();
    double timeDiffMils = startInMils - mainshockInMils;
    this.daysSinceMainshockStart = timeDiffMils / 1000.0 / 60.0 / 60.0 / 24.0;
    this.daysSinceMainshockEnd = this.daysSinceMainshockStart + duration;
  }
  
  /**
   * get_useSeqAndSpatial
   */
  public void set_useSeqAndSpatial() {
	int size = afterShocks.size();
	if(size < 100)
		useSeqAndSpatial = false;
	else{
		CompletenessMagCalc.setMcBest(this.afterShocks);
		double mComplete = CompletenessMagCalc.getMcBest();
		ObsEqkRupList compList = this.afterShocks.getObsEqkRupsAboveMag(mComplete);
		if (compList.size() > 100)
			this.useSeqAndSpatial = true;
		else
			this.useSeqAndSpatial = false;
	}
  }

  /**
   * getDaysSinceMainshockStart
   */
  public double getDaysSinceMainshockStart() {
    return daysSinceMainshockStart;
  }

  /**
   * getDaysSinceMainshockEnd
   */
  public double getDaysSinceMainshockEnd() {
    return daysSinceMainshockEnd;
  }

  /**
   * returns true is this model has been used in a forecast and should
   * be retained.
   * @return boolean
   */
  public boolean get_UsedInForecast(){
	  return usedInForecast;
  }


  /**
   * setHasExternalFaultModel
   */
  public void setHasExternalFaultModel(boolean hasExternalFaultModel) {
    this.hasExternalFaultModel = hasExternalFaultModel;
  }

  /**
   * Set the fault surface that will be used do define a Type II
   * aftershock zone.
   * This will not be used in a spatially varying model.
   */

  /**public void set_FaultSurface(FaultTrace fault_trace) {
    mainshockFault = new SimpleFaultData();
    mainshockFault.setAveDip(90.0);
    mainshockFault.setFaultTrace(fault_trace);
    mainshockFault.setLowerSeismogenicDepth(rDefs.lowerSeismoDepth);
    mainshockFault.setUpperSeismogenicDepth(rDefs.upperSeismoDepth);
  } */

  /**
   * get_minForecastMag
   */
  public double get_minForecastMag() {
    return minForecastMag;
  }

  /**
   * get_maxForecastMag
   */
  public double get_maxForecastMag() {
    return maxForecastMag;
  }

  /**
   * get_deltaMag
   */
  public double get_deltaMag() {
    return deltaMag;
  }

  /**
   * get_useSeqAndSpatial
   */
  public boolean get_useSeqAndSpatial() {
    return this.useSeqAndSpatial;
  }

  /**
   * get_GridSpacing
   */
  public double get_GridSpacing() {
    return gridSpacing;
  }

  /**
   * get_FaultModel
   */
  public SimpleFaultData get_FaultModel() {
    return mainshockFault;
  }

  /**
   * get_addToMcConst
   */
  public double get_addToMcConst() {
    return this.addToMc;
  }

  /**
   * get_isStatic
   */
  public boolean get_isStatic() {
    return this.isStatic;
  }

  /**
   * get_isPrimary
   */
  public boolean get_isPrimary() {
    return this.isPrimary;
  }

  /**
   * get_isSecondary
   */
  public boolean get_isSecondary() {
    return this.isSecondary;
  }

  /**
   * get_AftershockZoneRadius
   */
  public double get_AftershockZoneRadius() {
    return zoneRadius;
  }

  /**
   * get_griddedMagFreqDistForecast
   */
  public ArrayList get_griddedMagFreqDistForecast() {
    return griddedMagFreqDistForecast;
  }

  /**
   * getHasExternalFaultModel
   */
  public boolean getHasExternalFaultModel() {
    return this.hasExternalFaultModel;
  }

  /**
   * getGenElement
   */
  public GenericAfterHypoMagFreqDistForecast getGenElement() {
    return this.genElement;
  }

  /**
  * getSeqElement
  */
 public SequenceAfterHypoMagFreqDistForecast getSeqElement() {
   return this.seqElement;
 }

 /**
  * getSpaElement
  */
 public SpatialAfterHypoMagFreqDistForecast getSpaElement() {
   return this.spaElement;
 }

 /**
  * getHypoMagFreqDistAtLoc
  * this will return the AIC combined forecast at the location
  */
 public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(int ithLocation) {
	 return combinedForecast[ithLocation];
  }
 
 /**
  * getHypoMagFreqDistAtLoc
  * this will return the AIC combined forecast at the location
  */
 /**public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(Location loc) {
	 HypoMagFreqDistAtLoc locDist = combinedForecast[loc];
	 return locDist;
  }**/
 
 /**
  * getGriddedAIC_CombinedForecast
  * @return return an array of HypoMagFreqDistAtLoc for the gridded
  * AIC combined forecast
  */
 public HypoMagFreqDistAtLoc[] getGriddedAIC_CombinedForecast(){
	 return combinedForecast;
 }
 
 /**
  * getExistSeqModel
  * @return boolean
  * returns true if the seq model has been created
  */
 public boolean getExistSeqElement(){
	 return this.existSeqElement;
 }
 
 /**
  * getExistSpaModel
  * @return boolean
  * returns true is the spa model has been created
  */
 public boolean getExistSpaElement(){
	 return this.existSpaElement;
 }

}
