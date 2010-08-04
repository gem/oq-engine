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


import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DecimalFormat;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

/**
 * <p>Title: HazardMapCalculator </p>
 * <p>Description: This class calculates the Hazus data Set curves based on the
 * input parameters imr, site and eqkRupforecast</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta & Vipin Gupta
 * @date Oct 28, 2002
 * @version 1.0
 */

public class HazusMapCalculator {

  protected final static String C = "HazusMapCalculator";
  protected final static boolean D = false;

  /* maximum permitted distance between fault and site to consider source in
  hazard analysis for that site; this default value is to allow all PEER test
  cases to pass through
  */
  protected double MAX_DISTANCE = 2500;
  private DecimalFormat format = new DecimalFormat("0.000000##");

  // boolean for telling whether to show a progress bar
  boolean showProgressBar = true;

  private CalcProgressBar progressClass ;
  private static final double hazusTimePeriod =50;
  private DecimalFormat decimalFormat=new DecimalFormat("0.000000##");
  // directory where all the hazard map data sets will be saved
  public static final String DATASETS_PATH = "HazusMapDataSets/";
  // flag to indicate whether this IMT requires X values to be in log
  boolean xLogFlag = true;
  // name of the new directory for this data set
  private String newDir;

  //EqkRupForecast TimePd
  private double duration;
  //checks if PGV is supported by the selected Attenuation Relationship
  boolean pgvSupported = true;
  

  private double[] returnPd = {100, 250,500,750,1000,1500,2000,2500};
  
  private String hazusMapMetadata;
  
  //private double[] returnPd = {100};

  /**
   * This sets the maximum distance of sources to be considered in the calculation
   * (as determined by the getMinDistance(Site) method of ProbEqkSource subclasses).
   * Sources more than this distance away are ignored.
   * Default value is 250 km.
   *
   * @param distance: the maximum distance in km
   */
  public void setMaxSourceDistance(double distance) {
    MAX_DISTANCE = distance;
  }

  /**
     * this function determines the hazard curve based on the parameters
     *
     * @param imtLogFlag: Checks if the selected IMT is SA, PGA pr PGV, so that we can revert the
     * the Log X values of the Hazard func values back to the original values, before writing to the file
     * for each site.
     * @param hazFunction : it has X values set and result will be returned in this function
     * @param site  : site parameter
     * @param imr  :selected IMR object
     * @param eqkRupForecast  : selected Earthquake rup forecast
     * @param mapParametersInfo  : Parameters in String form used to generate the map
     * @return
   */
  public void getHazardMapCurves(SitesInGriddedRegion sites,
                                 ScalarIntensityMeasureRelationshipAPI imr,
                                 EqkRupForecast eqkRupForecast,
                                 String mapParametersInfo) {

    // get the number of data sets presently in directory
    File mainDir = new File(this.DATASETS_PATH);
    this.hazusMapMetadata = mapParametersInfo;
    if(!mainDir.isDirectory()) { // if main directory does not exist
      boolean success = (new File(DATASETS_PATH)).mkdir();
      newDir=  DATASETS_PATH+"Set-1";
    }
    else {
      if(mainDir.list()!=null) { // if there are various data sets in directory
        int numDataSets = mainDir.list().length;
        newDir=  DATASETS_PATH+"Set-"+(numDataSets);
      } else {// if main directory is there but it is empty
        newDir=  DATASETS_PATH+"Set-1";
      }
    }
    //creating a new directory that stores all the HazardCurves for that region
    boolean success = (new File(newDir)).mkdir();
    // make the metadata.data and sites.data files
    try{
      FileWriter fr = new FileWriter(newDir+"/metadata.dat");
      fr.write(mapParametersInfo+"\n");
      fr.close();
      fr=new FileWriter(newDir+"/sites.dat");
      fr.write(sites.getRegion().getMinLat()+" "+sites.getRegion().getMaxLat()+" "+
    		  sites.getRegion().getSpacing()+"\n"+sites.getRegion().getMinLon()+" "+
    		  sites.getRegion().getMaxLon()+" "+ sites.getRegion().getSpacing()+"\n");
      fr.close();
    }catch(IOException ee){
      ee.printStackTrace();
    }
    calculate(sites, imr, eqkRupForecast);
  }

  /**
   * this function determines the hazard curve based on the parameters
   *
   * @param dirName : Directory name for this new data set
   * @param imtLogFlag: Checks if the selected IMT is SA, PGA pr PGV, so that we can revert the
   * the Log X values of the Hazard func values back to the original values, before writing to the file
   * for each site.
   * @param hazFunction : it has X values set and result will be returned in this function
   * @param site  : site parameter
   * @param imr  :selected IMR object
   * @param eqkRupForecast  : selected Earthquake rup forecast
   * @param mapParametersInfo  : Parameters in String form used to generate the map
   * @return
   */
  public void getHazardMapCurves(String dirName,
		  SitesInGriddedRegion sites,
                                 ScalarIntensityMeasureRelationshipAPI imr,
                                 EqkRupForecast eqkRupForecast,
                                 String mapParametersInfo) {

    File mainDir = new File(this.DATASETS_PATH);
    this.hazusMapMetadata = mapParametersInfo;
	if(!mainDir.isDirectory()){  // if main directory does not exist
	  boolean success = (new File(DATASETS_PATH)).mkdir();
	}
    
    newDir = DATASETS_PATH+dirName;
    File f = new File(newDir);
  
    int counter =2;
    while(f.exists()){
       newDir = DATASETS_PATH+dirName+"_"+counter;
       f = new File(newDir);
       ++counter;
    }
    boolean success = (new File(newDir)).mkdir();
  
    // make the metadata.data and sites.data files
    try{
      FileWriter fr = new FileWriter(newDir+"/metadata.dat");
      fr.write(mapParametersInfo+"\n");
      fr.close();
      fr=new FileWriter(newDir+"/sites.dat");
      fr.write(sites.getRegion().getMinLat()+" "+sites.getRegion().getMaxLat()+" "+
    		  sites.getRegion().getSpacing()+"\n"+sites.getRegion().getMinLon()+" "+
    		  sites.getRegion().getMaxLon()+" "+ sites.getRegion().getSpacing()+"\n");
      fr.close();
    }catch(IOException ee){
      ee.printStackTrace();
    }


    calculate(sites, imr, eqkRupForecast);
  }



  /**
   * function to compute hazard curves and make the lat/lon files
   * @param griddedSites
   * @param imr
   * @param eqkRupForecast
   *
   */
  private void calculate( SitesInGriddedRegion sites,
                          ScalarIntensityMeasureRelationshipAPI imr,
                          EqkRupForecast eqkRupForecast) {

    try{

       int numSites = sites.getRegion().getNodeCount();
       duration = eqkRupForecast.getTimeSpan().getDuration();
       FileWriter[] fw = new FileWriter[returnPd.length];
       for(int j=0;j<returnPd.length;++j){
   	    fw[j] = new FileWriter(newDir+"/"+ "final_"+returnPd[j]+".dat");
   	    fw[j].write(this.hazusMapMetadata+"\n");
   	    fw[j].write("##Column Info: Lat,Lon,PGA,PGV,SA-0.3,SA-1\n");
       }
       // set the maximum distance in the attenuation relationship
       // (Note- other types of IMRs may not have this method so we should really check type here)
       imr.setUserMaxDistance(MAX_DISTANCE);
       //resetting the Parameter change Listeners on the AttenuationRelationship
       //parameters. This allows the Server version of our application to listen to the
       //parameter changes.
       ( (AttenuationRelationship) imr).resetParameterEventListeners();
       for(int i=0;i<numSites;++i){
    	      Site site = sites.getSite(i);
    	      imr.setSite(site);

    	      DiscretizedFuncAPI[] hazardFunc = getSiteHazardCurve(site,
    	    		  imr,eqkRupForecast);

    	      writeToFile(fw,site.getLocation(),hazardFunc);
       }

       for(int j=0;j<fw.length;++j)
      	    fw[j].close();

    }catch(Exception e){
      e.printStackTrace();
    }
  }

  private void writeToFile(FileWriter[] fw, Location loc, DiscretizedFuncAPI[] hazardFuncs) throws IOException{
	  DiscretizedFuncAPI pgaHazardFunction = hazardFuncs[0];
      DiscretizedFuncAPI sa03HazardFunction = hazardFuncs[1];
      DiscretizedFuncAPI sa1HazardFunction = hazardFuncs[2];
      DiscretizedFuncAPI pgvHazardFunction = hazardFuncs[3];

      for(int i=0;i<returnPd.length;++i){
    	    double rate = 1/returnPd[i] ;
    	    double prob = 1-Math.exp(-1*rate*duration);
    	    double pgaIML =0.0,sa03IML=0.0,sa1IML=0.0,pgvIML=0.0;
    	    
    	try{    
	        pgaIML = ((ArbitrarilyDiscretizedFunc)pgaHazardFunction).getFirstInterpolatedX_inLogXLogYDomain(prob);
	    
	        sa03IML = ((ArbitrarilyDiscretizedFunc)sa03HazardFunction).getFirstInterpolatedX_inLogXLogYDomain(prob);
	    
	        sa1IML = ((ArbitrarilyDiscretizedFunc)sa1HazardFunction).getFirstInterpolatedX_inLogXLogYDomain(prob);
	        
	        pgvIML = ((ArbitrarilyDiscretizedFunc)pgvHazardFunction).getFirstInterpolatedX_inLogXLogYDomain(prob);
    	}catch(InvalidRangeException e){}
        if(!pgvSupported)
        	pgvIML = pgvIML * 37.24*2.54;
    	fw[i].write(format.format(loc.getLatitude()) +","+format.format(loc.getLongitude())+","+
    	    		format.format(pgaIML)+","+format.format(pgvIML/2.5)+","+format.format(sa03IML)+","+format.format(sa1IML)+"\n");
      }
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
      for (int i = 0; i < linearFunc.getNum(); ++i)
        toXLogFunc.set(Math.log(linearFunc.getX(i)), val);
    return toXLogFunc;
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
  public DiscretizedFuncAPI[] getSiteHazardCurve(Site site,
                                           ScalarIntensityMeasureRelationshipAPI imr,
                                           EqkRupForecastAPI eqkRupForecast)  {


    /* this determines how the calucations are done (doing it the way it's outlined
     in the paper SRL gives probs greater than 1 if the total rate of events for the
     source exceeds 1.0, even if the rates of individual ruptures are << 1).
     */
    boolean poissonSource = false;


    int numIMTs = 4; //PGA,SA@0.3sec,SA@1secc,PGV for Hazus.
    DiscretizedFuncAPI[] hazFunction = new ArbitrarilyDiscretizedFunc[numIMTs];
    DiscretizedFuncAPI[] sourceHazFunc = new ArbitrarilyDiscretizedFunc[numIMTs];

    hazFunction[0] = IMT_Info.getUSGS_PGA_Function(); //PGA
    hazFunction[1] = IMT_Info.getUSGS_SA_Function(); //SA@0.3sec
    hazFunction[2] = hazFunction[1].deepClone(); //SA@1.0sec
    IMT_Info imtInfo = new IMT_Info();
    DiscretizedFuncAPI pgvFunction = imtInfo.getDefaultHazardCurve(PGV_Param.NAME);
    hazFunction[3] = pgvFunction.deepClone();; //PGV
 

    sourceHazFunc[0] = hazFunction[0].deepClone();
    sourceHazFunc[1] = hazFunction[1].deepClone();
    sourceHazFunc[2] = hazFunction[1].deepClone();
    sourceHazFunc[3] = hazFunction[1].deepClone();
    for(int m=0;m<numIMTs;++m){
    	  this.initDiscretizeValues(hazFunction[m],1.0);
    	  this.initDiscretizeValues(sourceHazFunc[m],1.0);
    }

    DiscretizedFuncAPI condProbFunc = null;

    //System.out.println("hazFunction: "+hazFunction.toString());

    // declare some varibles used in the calculation
    double qkProb, distance;
    int k;
    
    String pgv = PGV_Param.NAME;
    pgvSupported = ((AttenuationRelationship)imr).isIntensityMeasureSupported(pgv);
	

    // get total number of sources
    int numSources = eqkRupForecast.getNumSources();
    //System.out.println("Number of Sources: "+numSources);
    //System.out.println("ERF info: "+ eqkRupForecast.getClass().getName());
    // compute the total number of ruptures for updating the progress bar
    int totRuptures = 0;
    for (int sourceIndex = 0; sourceIndex < numSources; ++sourceIndex)
      totRuptures += eqkRupForecast.getSource(sourceIndex).getNumRuptures();


    //System.out.println("Total number of ruptures:"+ totRuptures);


    // init the current rupture number (also for progress bar)
    int currRuptures = 0;


    // this boolean will tell us whether a source was actually used
    // (e.g., all could be outside MAX_DISTANCE)
    boolean sourceUsed = false;
    if (D)
      System.out.println(C + ": starting hazard curve calculation");
	int numPoints =0;
    // loop over sources
    for (int sourceIndex = 0; sourceIndex < numSources; sourceIndex++) {

      // get the ith source
      ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);

      // compute the source's distance from the site and skip if it's too far away
      distance = source.getMinDistance(site);
      if (distance > MAX_DISTANCE) {
        currRuptures += source.getNumRuptures();
        continue;
      }

      // indicate that a source has been used
      sourceUsed = true;

      // determine whether it's poissonian
      poissonSource = source.isSourcePoissonian();

      // initialize the source hazard function to 0.0 if it's a non-poisson source
      if (!poissonSource)
        for(int m=0;m<numIMTs;++m)
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
        for (int imtIndex = 0; imtIndex < numIMTs; ++imtIndex) {

        	 if(imtIndex ==0){
        		 condProbFunc = IMT_Info.getUSGS_PGA_Function();
        		 imr.setIntensityMeasure(PGA_Param.NAME);
        	 }
        	 else if(imtIndex ==1){
        		 condProbFunc = IMT_Info.getUSGS_SA_Function();
        		 imr.setIntensityMeasure(SA_Param.NAME);
        		 imr.getParameter(PeriodParam.NAME).setValue(new Double(0.3));
        	 }
        	 else if(imtIndex ==2){
        		 condProbFunc = IMT_Info.getUSGS_SA_Function();
        		 imr.setIntensityMeasure(SA_Param.NAME);
        		 imr.getParameter(PeriodParam.NAME).setValue(new Double(1.0));
        	 }
        	 else if(imtIndex ==3){
        		 condProbFunc = pgvFunction.deepClone();
        		 if(pgvSupported)
        		     imr.setIntensityMeasure(pgv);
        		 else{
        			 imr.setIntensityMeasure(SA_Param.NAME);
            		 imr.getParameter(PeriodParam.NAME).setValue(new Double(1.0));
        		 }
        		 
        	 }
        	 numPoints = condProbFunc.getNum();
        	 condProbFunc = initDiscretizedValuesToLog(condProbFunc,1.0);
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
              hazFunction[imtIndex].set(k,
                                             hazFunction[imtIndex].getY(k) *
                                             Math.pow(1 - qkProb, condProbFunc.getY(k)));
          }
          // For non-Poissin source
          else
            for (k = 0; k < numPoints; k++)
              sourceHazFunc[imtIndex].set(k,
                                sourceHazFunc[imtIndex].getY(k) +
                                qkProb * condProbFunc.getY(k));
        }
      }
      // for non-poisson source:
      if (!poissonSource)
        for(int i=0;i<numIMTs;++i){
        	  numPoints = hazFunction[i].getNum();
          for (k = 0; k < numPoints; k++)
            hazFunction[i].set(k, hazFunction[i].getY(k) * (1 - sourceHazFunc[i].getY(k)));
        }
    }

    int i;
    // finalize the hazard function
    if (sourceUsed)
      for(int j=0;j<numIMTs;++j){
        numPoints = hazFunction[j].getNum();
        for (i = 0; i < numPoints; ++i)
          hazFunction[j].set(i, 1 - hazFunction[j].getY(i));
      }
    else
      for(int j=0;j<numIMTs;++j){
        numPoints = hazFunction[j].getNum();
        for (i = 0; i < numPoints; ++i)
          hazFunction[j].set(i, 0.0);
      }
    //creating the temp functionlist that gets the linear X Value for each SA-Period
    //spectrum curve.
    DiscretizedFuncAPI[] tempHazFunction = new ArbitrarilyDiscretizedFunc[numIMTs];
    for(int j=0;j<numIMTs;++j)
      tempHazFunction[j] = new ArbitrarilyDiscretizedFunc();
    numPoints = hazFunction[0].getNum();
    for (i = 0; i < numPoints; ++i)
      tempHazFunction[0].set(hazFunction[0].getX(i),
                            hazFunction[0].getY(i));
    
    numPoints = hazFunction[1].getNum();
    for (i = 0; i < numPoints; ++i)
      tempHazFunction[1].set(hazFunction[1].getX(i),
                             hazFunction[1].getY(i));
    
    numPoints = hazFunction[2].getNum();
    for (i = 0; i < numPoints; ++i)
      tempHazFunction[2].set(hazFunction[2].getX(i),
                             hazFunction[2].getY(i));
    numPoints = hazFunction[3].getNum();
    for (i = 0; i < numPoints; ++i)
       tempHazFunction[3].set(hazFunction[3].getX(i),
                             hazFunction[3].getY(i));
 
    if (D)
      System.out.println(C + "hazFunction.toString" + hazFunction.toString());
    return tempHazFunction;
  }


  /*private double convertToRate(double prob){
    double temp = 1-prob;
    if(temp == 0)
      temp = Double.MIN_VALUE;
    double val= -1*(Math.log(temp))/duration;
    return val;
  }*/


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
   * This allows tuning on or off the showing of a progress bar
   * @param show - set as true to show it, or false to not show it
   */
  public void showProgressBar(boolean show) {
    this.showProgressBar=show;
  }

}

