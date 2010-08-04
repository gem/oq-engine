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

package junk;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DecimalFormat;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.gui.infoTools.HazardMapCalcPostProcessing;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;



/**
 * <p>Title: HazardMapCalculator </p>
 * <p>Description: This class calculates the Hazard curve based on the
 * input parameters imr, site and eqkRupforecast</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta & Vipin Gupta
 * @date Oct 28, 2002
 * @version 1.0
 */

public class HazardMapCalculatorOld {

  protected final static String C = "HazardMapCalculator";
  protected final static boolean D = false;

  /* maximum permitted distance between fault and site to consider source in
  hazard analysis for that site; this default value is to allow all PEER test
  cases to pass through
  */
  protected double MAX_DISTANCE = 200;

  private DecimalFormat decimalFormat=new DecimalFormat("0.00##");
  // directory where all the hazard map data sets will be saved
  public static final String DATASETS_PATH = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/HazardMapDatasets/";
  // flag to indicate whether this IMT requires X values to be in log
  boolean xLogFlag = true;
  // name of the new directory for this data set
  String newDir;


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
  public void getHazardMapCurves(boolean imtLogFlag, double [] xValues,
		  SitesInGriddedRegion griddedSites,
                                 ScalarIntensityMeasureRelationshipAPI imr,
                                 EqkRupForecast eqkRupForecast,
                                 String mapParametersInfo) {

    // get the number of data sets presently in directory
    File mainDir = new File(this.DATASETS_PATH);

    if(!mainDir.isDirectory()) { // if main directory does not exist
      boolean success = (new File(DATASETS_PATH)).mkdir();
      newDir=  DATASETS_PATH+"1";
    }
    else {
      if(mainDir.list()!=null) { // if there are various data sets in directory
        int numDataSets = mainDir.list().length;
        newDir=  DATASETS_PATH+(numDataSets+1);
      } else {// if main directory is there but it is empty
        newDir=  DATASETS_PATH+"1";
      }
    }
    //creating a new directory that stores all the HazardCurves for that region
    boolean success = (new File(newDir)).mkdir();
    calculate(imtLogFlag, xValues, griddedSites, imr, eqkRupForecast, mapParametersInfo,null);
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
  public void getHazardMapCurves(String dirName, boolean imtLogFlag, double [] xValues,
		  SitesInGriddedRegion griddedSites,
                                 ScalarIntensityMeasureRelationshipAPI imr,
                                 EqkRupForecast eqkRupForecast,
                                 String mapParametersInfo, String email) {
    newDir=  new String(dirName);
    File f = new File(DATASETS_PATH+dirName);
    if(!f.exists()){
      //creating a new directory that stores all the HazardCurves for that region
      boolean success = f.mkdir();
      calculate(imtLogFlag, xValues, griddedSites, imr, eqkRupForecast, mapParametersInfo,email);
    }
    else
      throw new RuntimeException("Directory already exists please give some other name");
  }



  /**
   * function to compute hazard curves and make the lat/lon files
   * @param imtLogFlag
   * @param xValues
   * @param griddedSites
   * @param imr
   * @param eqkRupForecast
   * @param mapParametersInfo
   */
  private void calculate( boolean imtLogFlag, double [] xValues,
		  SitesInGriddedRegion sites,
                                  ScalarIntensityMeasureRelationshipAPI imr,
                                  EqkRupForecast eqkRupForecast,
                                 String mapParametersInfo, String email) {
    Site site;
    this.xLogFlag = imtLogFlag;
    int numSites = sites.getRegion().getNodeCount();
    try{
      HazardCurveCalculator hazCurveCalc=new HazardCurveCalculator();
      //hazCurveCalc.showProgressBar(false);

      int numPoints = xValues.length;
      for(int j=0;j<numSites;++j){
        site = sites.getSite(j);
        // make and initialize the haz function
        ArbitrarilyDiscretizedFunc hazFunction = new ArbitrarilyDiscretizedFunc();
        this.initX_Values(hazFunction,xValues);
        hazCurveCalc.getHazardCurve(hazFunction,site,imr,eqkRupForecast);
        String lat = decimalFormat.format(site.getLocation().getLatitude());
        String lon = decimalFormat.format(site.getLocation().getLongitude());

        hazFunction = this.toggleHazFuncLogValues(hazFunction, xValues);
        try{
          FileWriter fr = new FileWriter(DATASETS_PATH+newDir+"/"+lat+"_"+lon+".txt");
          for(int i=0;i<numPoints;++i)
            fr.write(hazFunction.getX(i)+" "+hazFunction.getY(i)+"\n");
          fr.close();
        }catch(IOException e){
          e.printStackTrace();
        }
      }
    }catch(Exception e){
      e.printStackTrace();
    }

    // make the metadata.data and sites.data files
    try{
      FileWriter fr = new FileWriter(DATASETS_PATH+newDir+"/metadata.txt");
      fr.write(mapParametersInfo+"\n");
      fr.close();
      fr=new FileWriter(DATASETS_PATH+newDir+"/sites.txt");
      fr.write(sites.getRegion().getMinLat()+" "+sites.getRegion().getMaxLat()+" "+
    		  sites.getRegion().getSpacing()+"\n"+sites.getRegion().getMinLon()+" "+
               sites.getRegion().getMaxLon()+" "+ sites.getRegion().getSpacing()+"\n");
      fr.close();
      if(email !=null || !email.equals("")){
        HazardMapCalcPostProcessing mapPostProcessing = new HazardMapCalcPostProcessing(numSites,
            email,newDir,java.util.Calendar.getInstance().getTime().toString().replaceAll(" ","_"));
      }

    }catch(IOException ee){
      ee.printStackTrace();
    }

      }

  /**
   * set x values in log space for Hazard Function to be passed to IMR
   * if the selected IMT are SA , PGA or PGV
   * It accepts 1 parameters
   *
   * @param originalFunc :  this is the function with X values set
   */
  private void initX_Values(DiscretizedFuncAPI arb, double[]xValues){
    // take log only if it is PGA, PGV or SA
    if (this.xLogFlag) {
      for(int i=0; i<xValues.length; ++i)
        arb.set(Math.log(xValues[i]),1 );
    } else
      throw new RuntimeException("Unsupported IMT");
  }

  /**
   * set x values back from the log space to the original linear values
   * for Hazard Function after completion of the Hazard Calculations
   * if the selected IMT are SA , PGA or PGV
   * It accepts 1 parameters
   *
   * @param hazFunction :  this is the function with X values set
   */
  private ArbitrarilyDiscretizedFunc toggleHazFuncLogValues(
      ArbitrarilyDiscretizedFunc hazFunc, double [] xValues){
    int numPoints = hazFunc.getNum();
    DiscretizedFuncAPI tempFunc = hazFunc.deepClone();
    hazFunc = new ArbitrarilyDiscretizedFunc();
    // take log only if it is PGA, PGV or SA
    if (this.xLogFlag) {
      for(int i=0; i<numPoints; ++i)
        hazFunc.set(xValues[i], tempFunc.getY(i));
      return hazFunc;
    } else
      throw new RuntimeException("Unsupported IMT");
  }


}

