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

package org.opensha.nshmp.sha.nico;


import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.net.MalformedURLException;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;
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
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.Frankel02_AdjustableEqkRupForecastClient;
import org.opensha.sha.gui.infoTools.ConnectToCVM;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.BJF_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CB_2003_AttenRel;
import org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.util.SiteTranslator;

/**
 * <p>Title: MeanSigmaCalc</p>
 *
 * <p>Description: This class computes the Mean and Sigma for 4 attenuation
 * relationships and 3 IMTs.
 * AttenautionRelationships used are:
 * 1)AS_1997_AttenRel as1997 ;
 * 2)CB_2003_AttenRel cb2003 ;
 * 3)SCEMY_1997_AttenRel scemy1997;
 * 4)BJF_1997_AttenRel
 * IMTs used in the code are :PGA,SA-1sec, SA-0.3sec
 * Sites information is read from a input file.
 * </p>
 *
 * @author Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */
public class MeanSigmaCalc
    implements ParameterChangeWarningListener {

  protected ArrayList willsClass;
  protected LocationList locList;
  private ArrayList locNameList;

  protected Frankel02_AdjustableEqkRupForecastClient frankelForecast;

  //supported Attenuations
  protected ArrayList supportedAttenuationsList;

  protected final static String MEAN = "mean";
  protected final static String SIGMA = "sigma";

  //some static IMT names

  protected final static String PGA ="PGA";
  protected final static String SA_10 = "SA_10";
  protected final static String SA_03 = "SA_03";


  protected double sourceCutOffDistance;
  protected final static double MIN_DIST = 200;
  protected Site siteForSourceCutOff;

  // site translator
  private SiteTranslator siteTranslator = new SiteTranslator();

  private DecimalFormat format = new DecimalFormat("0.000##");

  protected String inputFileName = "trackSiteInfo.txt";
  protected String dirName = "MeanSigma";

  public MeanSigmaCalc(String inpFile,String outDir) {
    inputFileName = inpFile;
    dirName = outDir ;
  }

  /**
   * Creating the instance of the Frankel02 forecast
 * @throws NotBoundException 
 * @throws MalformedURLException 
   */
  protected void createFrankel02Forecast() throws RemoteException, MalformedURLException, NotBoundException{
    frankelForecast = new Frankel02_AdjustableEqkRupForecastClient();
    frankelForecast.getAdjustableParameterList().getParameter(Frankel02_AdjustableEqkRupForecast.
        BACK_SEIS_NAME).setValue(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_EXCLUDE);
    frankelForecast.getAdjustableParameterList().getParameter(Frankel02_AdjustableEqkRupForecast.
        RUP_OFFSET_PARAM_NAME).setValue(new Double(10.0));
    frankelForecast.getTimeSpan().setDuration(1.0);
    frankelForecast.updateForecast();
  }

  /**
   * Creating the instances of the Attenuation Relationhships
   */
  protected void createAttenuationRelationObjects() {
    AS_1997_AttenRel as1997 = new AS_1997_AttenRel(this);
    CB_2003_AttenRel cb2003 = new CB_2003_AttenRel(this);
    SadighEtAl_1997_AttenRel scemy1997 = new SadighEtAl_1997_AttenRel(this);
    BJF_1997_AttenRel bjf1997 = new BJF_1997_AttenRel(this);
    supportedAttenuationsList = new ArrayList();
    supportedAttenuationsList.add(as1997);
    supportedAttenuationsList.add(cb2003);
    supportedAttenuationsList.add(scemy1997);
    supportedAttenuationsList.add(bjf1997);
  }

  /**
   * Gets the wills  site class for the given sites
   */

  private void getSiteParamsForRegion() {
    // get the vs 30 and basin depth from cvm
    willsClass = new ArrayList();
    try {
      willsClass = ConnectToCVM.getWillsSiteTypeFromCVM(locList);
    }
    catch (Exception ex) {
      ex.printStackTrace();
    }

  }

  /**
   * Starting with the Mean and Sigma calculation.
   * Creates the directory to put the mean and sigma files.
   */
  protected void getMeanSigma() {

    int numIMRs = supportedAttenuationsList.size();
    File file = new File(dirName);
    file.mkdirs();
    this.generateRuptureFile(frankelForecast,
                             dirName +
                             SystemUtils.FILE_SEPARATOR +
                             "Rupture_Prob.txt");

    for (int i = 0; i < numIMRs; ++i) {
      ScalarIntensityMeasureRelationshipAPI attenRel = (ScalarIntensityMeasureRelationshipAPI)
          supportedAttenuationsList.get(i);
      attenRel.setParamDefaults();
      generateMeanAndSigmaFile(attenRel,dirName+SystemUtils.FILE_SEPARATOR);
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
                                  String willsClass) {

    Iterator it = imr.getSiteParamsIterator(); // get site params for this IMR
    while (it.hasNext()) {
      ParameterAPI tempParam = (ParameterAPI) it.next();
      //adding the site Params from the CVM, if site is out the range of CVM then it
      //sets the site with whatever site Parameter Value user has choosen in the application
      boolean flag = siteTranslator.setParameterValue(tempParam, willsClass,
          Double.NaN);

      if (!flag) {
        String message = "cannot set the site parameter \"" + tempParam.getName() +
            "\" from Wills class \"" + willsClass + "\"" +
            "\n (no known, sanctioned translation - please set by hand)";
      }
    }
  }

  /**
   * Creates the locationlist from the file for Nico.
   * Creates a location using the given locations to find source cut-off disance.
   * @return
   */
  protected void createSiteList() {
    locList = new LocationList();
    locNameList = new ArrayList();
    try {
      ArrayList fileLines = FileUtils.loadFile(inputFileName);

      //gets the min lat, lon and max lat, lon from given set of locations.
      double minLon = Double.MAX_VALUE;
      double maxLon = Double.NEGATIVE_INFINITY;
      double minLat = Double.MAX_VALUE;
      double maxLat = Double.NEGATIVE_INFINITY;
      int numSites= fileLines.size();
      for (int i = 0; i < numSites; ++i) {
        String firstLine = (String) fileLines.get(i);
        StringTokenizer st = new StringTokenizer(firstLine);
        String trackNumber = st.nextToken();
        double lon = Double.parseDouble(st.nextToken());
        double lat = Double.parseDouble(st.nextToken());
        locList.add(new Location(lat,lon));
        locNameList.add(trackNumber);
        if(lon > maxLon)
          maxLon = lon;
        if(lon < minLon)
          minLon = lon;
        if(lat > maxLat)
          maxLat = lat;
        if(lat < minLat)
          minLat = lat;
      }
      double middleLon = (minLon + maxLon)/2;
      double middleLat = (minLat + maxLat)/2;

      //getting the source-site cuttoff distance
      sourceCutOffDistance = LocationUtils.horzDistance(
    		  new Location(middleLat,middleLon),
    		  new Location(minLat,minLon)) + MIN_DIST;
      siteForSourceCutOff = new Site(new Location(middleLat,middleLon));
    }
    catch (FileNotFoundException ex) {
      ex.printStackTrace();
    }
    catch (IOException ex) {
      ex.printStackTrace();
    }
    return;
  }


  /**
   * Generates the Mean and Sigma files for selected Attenuation Relationship application
   * @param imr AttenuationRelationshipAPI
   * @param dirName String
   */
  protected void generateMeanAndSigmaFile(ScalarIntensityMeasureRelationshipAPI imr,String dirName) {

    // get total number of sources
    int numSources = frankelForecast.getNumSources();
    // init the current rupture number
    int currRuptures = 0;
    String fileNamePrefixCommon = dirName +
    SystemUtils.FILE_SEPARATOR + imr.getName();
    // set the Site in IMR
    try {
      // opens the files for writing
      FileWriter fwPGAMean = new FileWriter(fileNamePrefixCommon +"_"+PGA+ "_"+MEAN+".txt");
      FileWriter fwPGASigma = new FileWriter(fileNamePrefixCommon +"_"+PGA+ "_"+SIGMA+".txt");

      FileWriter fwSA_03_Mean = new FileWriter(fileNamePrefixCommon +"_"+SA_03+ "_"+MEAN+".txt");
      FileWriter fwSA_03_Sigma = new FileWriter(fileNamePrefixCommon +"_"+SA_03+ "_"+SIGMA+".txt");

      FileWriter fwSA_10_Mean = new FileWriter(fileNamePrefixCommon +"_"+SA_10+ "_"+MEAN+".txt");
      FileWriter fwSA_10_Sigma = new FileWriter(fileNamePrefixCommon +"_"+SA_10+ "_"+SIGMA+".txt");

      // loop over sources
      for (int sourceIndex = 0; sourceIndex < numSources; sourceIndex++) {

        // get the ith source
        ProbEqkSource source = frankelForecast.getSource(sourceIndex);

        if(source.getMinDistance(siteForSourceCutOff) > sourceCutOffDistance)
          continue;

        // get the number of ruptures for the current source
        int numRuptures = source.getNumRuptures();

        // loop over these ruptures
        for (int n = 0; n < numRuptures; n++, ++currRuptures) {

          EqkRupture rupture = source.getRupture(n);
          // set the EqkRup in the IMR
          imr.setEqkRupture(rupture);

          fwPGAMean.write(currRuptures + " ");
          fwPGASigma.write(currRuptures + " ");

          fwSA_03_Mean.write(currRuptures + " ");
          fwSA_03_Sigma.write(currRuptures + " ");

          fwSA_10_Mean.write(currRuptures + " ");
          fwSA_10_Sigma.write(currRuptures + " ");

          int numSites = locList.size();

          //looping over all the sites for the selected Attenuation Relationship
          for (int j = 0; j < numSites; ++j) {
            setSiteParamsInIMR(imr, (String)willsClass.get(j));
            //this method added to the Attenuation Relationship allows to set the
            //Location in the site of the attenuation relationship
            imr.setSiteLocation(locList.get(j));
            //setting different intensity measures for each site and writing those to the file.
            imr.setIntensityMeasure(PGA_Param.NAME);

            fwPGAMean.write(format.format(imr.getMean()) + " ");
            fwPGASigma.write(format.format(imr.getStdDev()) + " ");

            imr.setIntensityMeasure(SA_Param.NAME);
            imr.getParameter(PeriodParam.NAME).setValue(new
                Double(1.0));

            fwSA_10_Mean.write(format.format(imr.getMean()) + " ");
            fwSA_10_Sigma.write(format.format(imr.getStdDev()) + " ");

            imr.getParameter(PeriodParam.NAME).setValue(new
                Double(0.3));

            fwSA_03_Mean.write(format.format(imr.getMean()) + " ");
            fwSA_03_Sigma.write(format.format(imr.getStdDev()) + " ");

          }

          fwPGAMean.write("\n");
          fwPGASigma.write("\n");

          fwSA_03_Mean.write("\n");
          fwSA_03_Sigma.write("\n");

          fwSA_10_Mean.write("\n");
          fwSA_10_Sigma.write("\n");


        }
      }
      fwPGAMean.close();
      fwPGASigma.close();

      fwSA_03_Mean.close();
      fwSA_03_Sigma.close();

      fwSA_10_Mean.close();
      fwSA_10_Sigma.close();

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
    protected void generateRuptureFile(EqkRupForecastAPI eqkRupForecast,
                                  String outFileName) {
    // get total number of sources
    int numSources = eqkRupForecast.getNumSources();
    // init the current rupture number
    int currRuptures = 0;
    try {
      // opens the files for writing
      FileWriter fwRup = new FileWriter(outFileName);

      // loop over sources
      for (int sourceIndex = 0; sourceIndex < numSources; sourceIndex++) {

        // get the ith source
        ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);


        if(source.getMinDistance(siteForSourceCutOff) > sourceCutOffDistance)
          continue;
        // get the number of ruptures for the current source
        int numRuptures = source.getNumRuptures();

        // loop over these ruptures
        for (int n = 0; n < numRuptures; n++, ++currRuptures) {

          ProbEqkRupture rupture = (ProbEqkRupture) source.getRupture(n);
          fwRup.write(currRuptures + " " + rupture.getProbability() + "\n");
        }
      }
      fwRup.close();
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

    //System.out.println(b);
    param.setValueIgnoreWarning(e.getNewValue());

  }

  public static void main(String[] args) {
    if(args.length != 2){
      System.out.println("Usage :\n\t"+"java -jar [jarfileName] [inputFileName] [output directory name]\n\n");
      System.out.println("jarfileName : Name of the executable jar file, by default it is MeanSigmaCalc.jar");
      System.out.println("inputFileName :Name of the input file, this input file should contain only 3 columns"+
                         " \"SiteTrackNumber Lon Lat\", For eg: see \"trackSiteInfo.txt\". ");
      System.out.println("output directory name : Name of the output directory where all the output files will be generated");
      System.exit(0);
    }

    MeanSigmaCalc calc = new MeanSigmaCalc(args[0],args[1]);
    calc.createSiteList();

    try {
      calc.createFrankel02Forecast();
    }
    catch (RemoteException ex) {
      ex.printStackTrace();
    } catch (MalformedURLException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	} catch (NotBoundException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	}
    calc.createAttenuationRelationObjects();
    calc.getSiteParamsForRegion();
    calc.getMeanSigma();
  }
}
