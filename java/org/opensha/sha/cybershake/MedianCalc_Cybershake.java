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

package org.opensha.sha.cybershake;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.StringTokenizer;

import org.apache.commons.lang.SystemUtils;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF1.WGCEP_UCERF1_EqkRupForecast;
import org.opensha.sha.gui.infoTools.ConnectToCVM;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.util.SiteTranslator;


/**
 * <p>Title: MeanSigmaCalc</p>
 *
 * <p>Description: This class computes the Mean and Sigma for any Attenuation
 * supported and any IMT supported by these AttenuationRelationships.
 * Sites information is read from a input file.
 * </p>
 *
 * @author Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */
public class MedianCalc_Cybershake
    implements ParameterChangeWarningListener {

  protected ArrayList willsSiteClassVals;
  protected ArrayList basinDepthVals;
  protected LocationList locList;


  protected EqkRupForecastAPI forecast;

  //supported Attenuations
  protected ArrayList supportedAttenuationsList;

  protected final static String MEAN = "mean";
  protected final static String SIGMA = "sigma";

  //some static IMT names
  protected ArrayList supportedIMTs;

  protected double sourceCutOffDistance;
  protected final static double MIN_DIST = 200;
  protected Site siteForSourceCutOff;

  // site translator
  private SiteTranslator siteTranslator = new SiteTranslator();

  protected DecimalFormat format = new DecimalFormat("0.000##");

  protected String inputFileName = "MeanSigmaCalc_InputFile.txt";
  protected String dirName = "MeanSigma";

  public MedianCalc_Cybershake(String inpFile,String outDir) {
    inputFileName = inpFile;
    dirName = outDir ;
  }

  protected void parseFile() throws FileNotFoundException,IOException{

      ArrayList fileLines = null;

      fileLines = FileUtils.loadFile(inputFileName);

      int j = 0;
      int numIMRdone=0;
      int numIMRs=0;
      int numIMTdone=0;
      int numIMTs=0;
      int numSitesDone=0;
      int numSites =0;
      for(int i=0; i<fileLines.size(); ++i) {
        String line = ((String)fileLines.get(i)).trim();
        // if it is comment skip to next line
        if(line.startsWith("#") || line.equals("")) continue;
        if(j==0)getERF(line);
        if(j==1){
          boolean toApplyBackGround = Boolean.parseBoolean(line.trim());
          toApplyBackGroud(toApplyBackGround);
        }
        if(j==2){
          double rupOffset = Double.parseDouble(line.trim());
          setRupOffset(rupOffset);
        }
        if(j==3)
          numIMRs = Integer.parseInt(line.trim());
        if(j==4){
            setIMR(line.trim());
            ++numIMRdone;
            if(numIMRdone == numIMRs)
              ++j;
            continue;
        }
        if(j==5)
          numIMTs = Integer.parseInt(line.trim());
        if(j==6){
          setIMT(line.trim());
          ++numIMTdone;
          if (numIMTdone == numIMTs)
            ++j;
          continue;
        }
        if(j==7)
          numSites = Integer.parseInt(line.trim());
        if(j==8){
          setSite(line.trim());
          ++numSitesDone;
          if (numSitesDone == numSites)
            ++j;
          continue;
        }
        ++j;
      }
  }

  /**
   * Gets the list of locations with their Wills Site Class values
   * @param line String
   */
  protected void setSite(String line){
    if(locList == null)
      locList = new LocationList();
    StringTokenizer st = new StringTokenizer(line);
    int tokens = st.countTokens();
    if(tokens > 3 || tokens < 2){
      throw new RuntimeException("Must Enter valid Lat Lon in each line in the file");
    }
    double lat = Double.parseDouble(st.nextToken().trim());
    double lon = Double.parseDouble(st.nextToken().trim());
    Location loc = new Location(lat,lon);
    locList.add(loc);
    String willsClass="";
    Double basinDepth =  null;
    if(tokens == 3){
      willsClass = st.nextToken().trim();
      //willsClass = SiteTranslator.getWillsSiteClassForVs30(vs30);
    }
    else if(tokens ==2){
      LocationList siteLocListForWillsSiteClass = new LocationList();
      siteLocListForWillsSiteClass.add(loc);
      try{
        willsClass = (String) ConnectToCVM.getWillsSiteTypeFromCVM(
            siteLocListForWillsSiteClass).get(0);
        if(willsClass.equals("NA"))
        	willsClass = SiteTranslator.WILLS_DE;
        basinDepth = (Double)ConnectToCVM.getBasinDepthFromCVM(siteLocListForWillsSiteClass).get(0);
        
      }catch(Exception e){
        throw new RuntimeException(e);
      }
    }
    if(willsSiteClassVals == null)
      willsSiteClassVals = new ArrayList();
    if(basinDepthVals == null)
    	basinDepthVals = new ArrayList();
    //System.out.println("WillsSiteClass :"+willsClass +" BasinDepth = "+basinDepth);
    if(basinDepth == null)	
       basinDepthVals.add(new Double(Double.NaN));
    else
       basinDepthVals.add(basinDepth);
    willsSiteClassVals.add(willsClass);
  }

  /**
   * Gets the suported IMTs as String
   * @param line String
   */
  protected void setIMT(String line){
    if(supportedIMTs == null)
      supportedIMTs = new ArrayList();
    this.supportedIMTs.add(line.trim());
  }


  /**
   * Creates the IMR instances and adds to the list of supported IMRs
   * @param str String
   */
  protected void setIMR(String str) {
    if(supportedAttenuationsList == null)
      supportedAttenuationsList = new ArrayList();
    createIMRClassInstance(str.trim());
  }


  /**
   * Creates a class instance from a string of the full class name including packages.
   * This is how you dynamically make objects at runtime if you don't know which\
   * class beforehand. For example, if you wanted to create a BJF_1997_AttenRel you can do
   * it the normal way:<P>
   *
   * <code>BJF_1997_AttenRel imr = new BJF_1997_AttenRel()</code><p>
   *
   * If your not sure the user wants this one or AS_1997_AttenRel you can use this function
   * instead to create the same class by:<P>
   *
   * <code>BJF_1997_AttenRel imr =
   * (BJF_1997_AttenRel)ClassUtils.createNoArgConstructorClassInstance("org.opensha.sha.imt.attenRelImpl.BJF_1997_AttenRel");
   * </code><p>
   *
   */
  private void createIMRClassInstance(String AttenRelClassName) {
    String attenRelClassPackage = "org.opensha.sha.imr.attenRelImpl.";
    try {
      Class listenerClass = Class.forName(
          "org.opensha.commons.param.event.ParameterChangeWarningListener");
      Object[] paramObjects = new Object[] {
          this};
      Class[] params = new Class[] {
          listenerClass};
      Class imrClass = Class.forName(attenRelClassPackage + AttenRelClassName);
      Constructor con = imrClass.getConstructor(params);
      ScalarIntensityMeasureRelationshipAPI attenRel = (ScalarIntensityMeasureRelationshipAPI) con.newInstance(paramObjects);
      /*attenRel.getParameter(SigmaTruncTypeParam.NAME).
          setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
      attenRel.getParameter(SigmaTruncLevelParam.NAME).
          setValue(new Double(3.0));*/
      

      //setting the Attenuation with the default parameters
      attenRel.setParamDefaults();
      supportedAttenuationsList.add(attenRel);
    }
    catch (ClassCastException e) {
      e.printStackTrace();
    }
    catch (ClassNotFoundException e) {
      e.printStackTrace();
    }
    catch (NoSuchMethodException e) {
      e.printStackTrace();
    }
    catch (InvocationTargetException e) {
      e.printStackTrace();
    }
    catch (IllegalAccessException e) {
      e.printStackTrace();
    }
    catch (InstantiationException e) {
      e.printStackTrace();
    }
  }

  protected void getERF(String line){
    if(line.trim().equals(Frankel02_AdjustableEqkRupForecast.NAME))
      createFrankel02Forecast();
    else
      createUCERF_Forecast();
  }

  /**
   * Creating the instance of the Frankel02 forecast
   */
  private void createFrankel02Forecast(){

    forecast = new Frankel02_AdjustableEqkRupForecast();
    forecast.getAdjustableParameterList().getParameter(Frankel02_AdjustableEqkRupForecast.
        BACK_SEIS_NAME).setValue(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_EXCLUDE);
    forecast.getAdjustableParameterList().getParameter(Frankel02_AdjustableEqkRupForecast.
    		FAULT_MODEL_NAME).setValue(Frankel02_AdjustableEqkRupForecast.FAULT_MODEL_STIRLING);
        forecast.getTimeSpan().setDuration(1.0);
        
  }

  /**
   * Creating the instance of the Frankel02 forecast
   */
  private void createUCERF_Forecast(){
    forecast = new WGCEP_UCERF1_EqkRupForecast();
    forecast.getAdjustableParameterList().getParameter(
        WGCEP_UCERF1_EqkRupForecast.
        BACK_SEIS_NAME).setValue(WGCEP_UCERF1_EqkRupForecast.BACK_SEIS_EXCLUDE);

    forecast.getAdjustableParameterList().getParameter(
        WGCEP_UCERF1_EqkRupForecast.TIME_DEPENDENT_PARAM_NAME).setValue(new Boolean(false));

    forecast.getTimeSpan().setDuration(1.0);

  }

  protected void toApplyBackGroud(boolean toApply){
    if(toApply){
      if(forecast instanceof Frankel02_AdjustableEqkRupForecast){
        forecast.getAdjustableParameterList().getParameter(
            Frankel02_AdjustableEqkRupForecast.
            BACK_SEIS_NAME).setValue(Frankel02_AdjustableEqkRupForecast.
                                     BACK_SEIS_INCLUDE);
        forecast.getAdjustableParameterList().getParameter(
            Frankel02_AdjustableEqkRupForecast.
            BACK_SEIS_RUP_NAME).setValue(Frankel02_AdjustableEqkRupForecast.
                                         BACK_SEIS_RUP_FINITE);
      }
      else{
        forecast.getAdjustableParameterList().getParameter(
            WGCEP_UCERF1_EqkRupForecast.BACK_SEIS_NAME).setValue(WGCEP_UCERF1_EqkRupForecast.
                                     BACK_SEIS_INCLUDE);
        forecast.getAdjustableParameterList().getParameter(
            WGCEP_UCERF1_EqkRupForecast.BACK_SEIS_RUP_NAME).setValue(
                WGCEP_UCERF1_EqkRupForecast.BACK_SEIS_RUP_FINITE);
      }
    }
    else{
      if(forecast instanceof Frankel02_AdjustableEqkRupForecast)
        forecast.getAdjustableParameterList().getParameter(Frankel02_AdjustableEqkRupForecast.
        BACK_SEIS_NAME).setValue(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_EXCLUDE);
      else
        forecast.getAdjustableParameterList().getParameter(
        Frankel02_AdjustableEqkRupForecast.
        BACK_SEIS_NAME).setValue(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_EXCLUDE);
    }
  }

  protected void setRupOffset(double rupOffset){
    if (forecast instanceof Frankel02_AdjustableEqkRupForecast){
      forecast.getAdjustableParameterList().getParameter(
          Frankel02_AdjustableEqkRupForecast.
          RUP_OFFSET_PARAM_NAME).setValue(new Double(rupOffset));
      forecast.updateForecast();
    }
    else{
      forecast.getAdjustableParameterList().getParameter(
          Frankel02_AdjustableEqkRupForecast.
          RUP_OFFSET_PARAM_NAME).setValue(new Double(rupOffset));
      forecast.updateForecast();
    }

  }


  /**
   * Starting with the Mean and Sigma calculation.
   * Creates the directory to put the mean and sigma files.
   */
  protected void getMedian() {

    int numIMRs = supportedAttenuationsList.size();
    File file = new File(dirName);
    file.mkdirs();
    /*this.generateSrcRupMetadataFile(forecast,
                                    dirName +
                                    SystemPropertiesUtils.
                                    getSystemFileSeparator());
    this.generateRupSiteDistFile(forecast,
                                 dirName +
                                 SystemPropertiesUtils.getSystemFileSeparator());*/

    int numIMTs = supportedIMTs.size();
    for (int i = 0; i < numIMRs; ++i) {
      ScalarIntensityMeasureRelationshipAPI attenRel = (ScalarIntensityMeasureRelationshipAPI)
          supportedAttenuationsList.get(i);
      attenRel.setParamDefaults();
      attenRel.setUserMaxDistance(sourceCutOffDistance);
      for (int j = 0; j < numIMTs; ++j) {
        String imtLine = (String) supportedIMTs.get(j);
        generateMedian(attenRel, imtLine,
                                 dirName +
                                 SystemUtils.FILE_SEPARATOR);
      }
    }
  }


  /**
   * set the site params in IMR according to basin Depth and vs 30
   * @param imr
   * @param lon
   * @param lat
   * @param willsClass
   * @param basinDepth
   */
  protected void setSiteParamsInIMR(ScalarIntensityMeasureRelationshipAPI imr,
                                  String willsClass, Double basinDepth) {

    Iterator it = imr.getSiteParamsIterator(); // get site params for this IMR
    while (it.hasNext()) {
      ParameterAPI tempParam = (ParameterAPI) it.next();
      //adding the site Params from the CVM, if site is out the range of CVM then it
      //sets the site with whatever site Parameter Value user has choosen in the application
      boolean flag = siteTranslator.setParameterValue(tempParam, willsClass,
          basinDepth.doubleValue());

      if (!flag) {
        String message = "cannot set the site parameter \"" + tempParam.getName() +
            "\" from Wills class \"" + willsClass + "\"" +
            "\n (no known, sanctioned translation - please set by hand)";
      }
    }
  }

  /**
   *
   * Creates a location using the given locations to find source cut-off disance.
   * @return
   */
  protected void createSiteList() {
     //gets the min lat, lon and max lat, lon from given set of locations.
    double minLon = Double.MAX_VALUE;
    double maxLon = Double.NEGATIVE_INFINITY;
    double minLat = Double.MAX_VALUE;
    double maxLat = Double.NEGATIVE_INFINITY;
    int numSites = locList.size();
    for (int i = 0; i < numSites; ++i) {

      Location loc = (Location) locList.get(i);
      double lon = loc.getLongitude();
      double lat = loc.getLatitude();
      if (lon > maxLon)
        maxLon = lon;
      if (lon < minLon)
        minLon = lon;
      if (lat > maxLat)
        maxLat = lat;
      if (lat < minLat)
        minLat = lat;
    }
    double middleLon = (minLon + maxLon) / 2;
    double middleLat = (minLat + maxLat) / 2;

    //getting the source-site cuttoff distance
    sourceCutOffDistance = (float) LocationUtils.horzDistance(
    		new Location(middleLat, middleLon),
    		new Location(minLat, minLon)) + MIN_DIST;
    siteForSourceCutOff = new Site(new Location(middleLat, middleLon));

    return;
  }


  /**
   * Generates the Mean and Sigma files for selected Attenuation Relationship application
   * @param imr AttenuationRelationshipAPI
   * @param dirName String
   */
  protected void generateMedian(ScalarIntensityMeasureRelationshipAPI imr,
                                          String imtLine,
                                          String dirName) {

    // get total number of sources
    int numSources = forecast.getNumSources();


    // init the current rupture number
    int currRuptures = 0;

    // set the Site in IMR
    try {
      FileWriter medianFile;

      String fileNamePrefixCommon = dirName +
      SystemUtils.FILE_SEPARATOR + imr.getShortName();

      // opens the files for writing
      StringTokenizer st = new StringTokenizer(imtLine);
      int numTokens = st.countTokens();
      String imt = st.nextToken().trim();
      imr.setIntensityMeasure(imt);
 
      String pd = "";
      if (numTokens == 2) {
        pd = st.nextToken().trim();
        if (pd != null && !pd.equals(""))	
        	  imr.getParameter(PeriodParam.NAME).setValue(new Double(Double.parseDouble(pd)));
        medianFile = new FileWriter(fileNamePrefixCommon + "_" +
                                       imt + "_" + pd + ".txt");
      }
      else
        medianFile = new FileWriter(fileNamePrefixCommon + "_" +
                                       imt + ".txt");
      medianFile.write("#SrcId\tRupId\tUSC-Median\tUSC-RUP_DIST\t"+
    		  "PAS-Median\tPAS-RUP_DIST\tLADT-Median\tLADT-RUP_DIST\tLBP-Median\t"+
    		  "LBP-RUP_DIST\tSABD-Median\tSABD-RUP_DIST\tWNGC-Median\tWNGC-RUP_DIST\t"+
    		  "SBSM-Median\tSBSM-RUP_DIST\tFFI-Median\tFFI-RUP_DIST\tCCP-Median\tCCP-RUP_DIST\t" +
    		  "SMCA-Median\tSMCA-RUP_DIST\n");
      // loop over sources
      for (int sourceIndex = 0; sourceIndex < numSources; sourceIndex++) {

        // get the ith source
        ProbEqkSource source = forecast.getSource(sourceIndex);
        double sourceDistFromSite = source.getMinDistance(siteForSourceCutOff);
        if (sourceDistFromSite > sourceCutOffDistance)
          continue;
        //if(!(source instanceof FaultRuptureSource))
     	  // continue;

        // get the number of ruptures for the current source
        int numRuptures = source.getNumRuptures();
        
         // loop over these ruptures
        for (int n = 0; n < numRuptures; n++, ++currRuptures) {

          EqkRupture rupture = source.getRupture(n);
          //float mag = (float)rupture.getMag();
        	  //mag = (float)(1.89 + 0.69 * mag);
          //if(mag >=6.0 && mag<=7.0){
        	      //rupture.setMag(mag);
	          // set the EqkRup in the IMR
	          imr.setEqkRupture(rupture);
	
	          medianFile.write(sourceIndex + "  " + n + "  ");
	
	          int numSites = locList.size();
	
	          //looping over all the sites for the selected Attenuation Relationship
	          for (int j = 0; j < numSites; ++j) {
	            setSiteParamsInIMR(imr, (String) willsSiteClassVals.get(j),(Double)basinDepthVals.get(j));
	            //this method added to the Attenuation Relationship allows to set the
	            //Location in the site of the attenuation relationship
	            Location loc = (Location)locList.get(j);
	            imr.setSiteLocation(loc);
	            //setting different intensity measures for each site and writing those to the file.
	            medianFile.write(format.format(Math.exp(imr.getMean())) + " ");
	            Site site = new Site(loc);
	            PropagationEffect propEffect = new PropagationEffect(site,rupture);
	            double rupDist = ((Double)propEffect.getParamValue(DistanceRupParameter.NAME)).doubleValue();
	            medianFile.write((float)rupDist+"  ");	
	          }
	          medianFile.write("\n");
	        //}
        }
      }
      medianFile.close();
    }
    catch (Exception e) {
      e.printStackTrace();
    }
  }

	  /**
	   * generate the Rupture Probability file
	   * @param eqkRupForecast EqkRupForecastAPI
	   * @param outFileName String
	   */
	  /*private void generateSrcRupMetadataFile(EqkRupForecastAPI eqkRupForecast,
	                                            String dirName) {
	    String outFileName = dirName+"src_rup_metadata.txt";
	    // get total number of sources
	    int numSources = eqkRupForecast.getNumSources();
	    // init the current rupture number
	    int currRuptures = 0;
	    try {
	      File fw = new File(outFileName);
	      if (!fw.exists()) {
	        //opens the files for writing
	        FileWriter fwRup = new FileWriter(outFileName);
	        double duration = ((TimeSpan)eqkRupForecast.getTimeSpan()).getDuration();
	
	        // loop over sources
	        for (int sourceIndex = 0; sourceIndex < numSources; sourceIndex++) {
	
	          // get the ith source
	          ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);
	
	          double sourceDistFromSite = source.getMinDistance(siteForSourceCutOff);
	          if (sourceDistFromSite > sourceCutOffDistance)
	            continue;
	          if(!(source instanceof FaultRuptureSource))
	        	   continue;
	          // get the number of ruptures for the current source
	          int numRuptures = source.getNumRuptures();
	          // loop over these ruptures
	          for (int n = 0; n < numRuptures; n++, ++currRuptures) {
	
	            ProbEqkRupture rupture = (ProbEqkRupture) source.getRupture(n);
	            float mag = (float)rupture.getMag();
	        	    //mag = (float)(1.89 + 0.69 * mag);
	            if(mag >=6.0 && mag<=7.0){
		            double rate = -Math.log(1 - rupture.getProbability())/duration;
		            fwRup.write(sourceIndex+"  "+n + " " + (float)rate+"  "+mag+"  "+source.getName() + "\n");
	            }
	          }
	        	}
	        	fwRup.close();
	    }
	   }
	    catch (Exception e) {
		  e.printStackTrace();
	  }	
    	}*/

  /**
   * generate the Rupture Probability file
   * @param eqkRupForecast EqkRupForecastAPI
   * @param outFileName String
   */
  private void generateRupSiteDistFile(EqkRupForecastAPI eqkRupForecast,
      String dirName) {
    String outFileName = dirName+"rup_dist_info.txt";
    // get total number of sources
    int numSources = eqkRupForecast.getNumSources();
    // init the current rupture number
    int currRuptures = 0;
    try {
      File fw = new File(outFileName);
      if (!fw.exists()) {
        //opens the files for writing
        FileWriter fwRup = new FileWriter(outFileName);

        // loop over sources
        for (int sourceIndex = 0; sourceIndex < numSources; sourceIndex++) {

          // get the ith source
          ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);

          double sourceDistFromSite = source.getMinDistance(siteForSourceCutOff);
          if (sourceDistFromSite > sourceCutOffDistance)
            continue;
          
          if(!(source instanceof FaultRuptureSource))
   	          continue;

          // get the number of ruptures for the current source
          int numRuptures = source.getNumRuptures();

          // loop over these ruptures
          for (int n = 0; n < numRuptures; n++, ++currRuptures) {

            ProbEqkRupture rupture = (ProbEqkRupture) source.getRupture(n);
            float mag = (float)rupture.getMag();
            if(mag >=6.0 && mag<=7.0){
	            fwRup.write(sourceIndex + "  " + n+" ");
	            int numSites = locList.size();
	            for(int s=0 ; s<numSites ; ++s){
	              Location loc = locList.get(s);
	              Site site = new Site(loc);
	              PropagationEffect propEffect = new PropagationEffect(site,rupture);
	              double rupDist = ((Double)propEffect.getParamValue(DistanceRupParameter.NAME)).doubleValue();
	              fwRup.write((float)rupDist+"  ");
	            }
	            fwRup.write("\n");
            }
           }
        }
        fwRup.close();
      }
    }
    catch (Exception e) {
      e.printStackTrace();
    }

  }

  /**
   *  Function that must be implemented by all Listeners for
   *  ParameterChangeWarnEvents.
   *
   * @param  event  The Event which triggered this function call
   */
  public void parameterChangeWarning(ParameterChangeWarningEvent e) {

    String S = " : parameterChangeWarning(): ";

    WarningParameterAPI param = e.getWarningParameter();

    param.setValueIgnoreWarning(e.getNewValue());

  }

  public static void main(String[] args) {
    if(args.length != 2){
      System.out.println("Usage :\n\t"+"java -jar [jarfileName] [inputFileName] [output directory name]\n\n");
      System.out.println("jarfileName : Name of the executable jar file, by default it is MeanSigmaCalc.jar");
      System.out.println("inputFileName :Name of the input file, this input file should contain only 3 columns"+
                         " \"Lon Lat Vs30\", For eg: see \"MeanSigmaCalc_InputFile.txt\". ");
      System.out.println("output directory name : Name of the output directory where all the output files will be generated");
      System.exit(0);
    }

    MedianCalc_Cybershake calc = new MedianCalc_Cybershake(args[0],args[1]);
    try {
      calc.parseFile();
    }
    catch (FileNotFoundException ex) {
      ex.printStackTrace();
    }
    catch (IOException ex) {
      ex.printStackTrace();
    }
    catch (Exception ex) {
      ex.printStackTrace();
    }

    calc.createSiteList();
    calc.getMedian();
  }
}
