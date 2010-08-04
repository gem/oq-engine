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


import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.gui.infoTools.ConnectToCVM;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.util.SiteTranslator;


/**
 * <p>Title: ObsExceedProbCalculator</p>
 *
 * <p>Description: This class calculates the ExceedProb from the output SA values
 * from CyberShake and compares it with the given attenuation relationship application.</p>
 *
 * @author Nitin Gupta, Vipin Gupta, and Ned Field
 * @version 1.0
 */
public class ObsExceedProbCalculator implements ParameterChangeWarningListener{


  /**
   * Parameters from the input file
   */
  private Location loc; //Geographic Location

  private String imt;
  private double period;
  private String defaultSiteType; //in case we are not able to get the site type for any site
  //in the region.

  //Cybershake SA values
  private ArbitrarilyDiscretizedFunc xyVals;
  private  Frankel02_AdjustableEqkRupForecast frankelForecast = null;
  //one of the ruptures in Frankel-02 code
  private EqkRupture rupture;
  //approx Dist to 4 corners to the rupture
  private double approxDist;
  private String willsClass = "NA";
  private double basinDepth = Double.NaN;
  private final static double CM_S2_TO_G_CONVERSION_FACTOR = 980.0;

  /**
   *  The object class names for all the supported attenuation ralations (IMRs)
   *  Temp until figure out way to dynamically load classes during runtime
   */
  public final static String AS_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel";
  public final static String C_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.Campbell_1997_AttenRel";
  public final static String SCEMY_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.SCEMY_1997_AttenRel";
  public final static String F_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.Field_2000_AttenRel";
  //public final static String A_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.Abrahamson_2000_AttenRel";
  public final static String CB_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.CB_2003_AttenRel";
  public final static String SM_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.ShakeMap_2003_AttenRel";
  public final static String USGS04_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.USGS_Combined_2004_AttenRel";
  public final static String AS_2005_PRELIM_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.depricated.AS_2005_prelim_AttenRel";
  //public final static String CB_2005_PRELIM_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.depricated.CB_2006_AttenRel";
  public final static String CY_2005_PRELIM_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.depricated.CY_2006_AttenRel";
  public final static String Boore_2005_PRELIM_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.depricated.BA_2006_AttenRel";

  //arrayList to store the supported AttenRel Class Names with their full package structure.
  ArrayList supportedAttenRelClasses = new ArrayList();


  private void parseFile(String fileName) throws FileNotFoundException,IOException{

      ArrayList fileLines = null;

      fileLines = FileUtils.loadFile(fileName);

      int j = 0;
      String component1Line=null;
      for(int i=0; i<fileLines.size(); ++i) {
        String line = ((String)fileLines.get(i)).trim();
        // if it is comment skip to next line
        if(line.startsWith("#") || line.equals("")) continue;

        //
        if(j==0) getLocation(line); // first line sets the region Params
        else if(j==1) setRupture(line) ; // set the rupture params
        else if(j==2) setIMT(line);  // set the IMT
        else if(j==3) setDefaultWillsSiteType(line); // default site to use if site parameters are not known for a site
        else if(j==4) component1Line = line;
        else if(j==5) setSAVals(component1Line, line);
        ++j;
      }
  }

  /**
   * Setting the SA vals for the Exceed Prob.
   * @param str String
   */
  private void setSAVals(String component1Str, String component2Str) {
    StringTokenizer component1Tokenizer = new StringTokenizer(component1Str);
    StringTokenizer component2Tokenizer = new StringTokenizer(component2Str);
    double comp1=0.0, comp2, avg;
    xyVals = new ArbitrarilyDiscretizedFunc();
    while(component1Tokenizer.hasMoreTokens()) {
      comp1 = Double.parseDouble(component1Tokenizer.nextToken().trim());
      comp2 = Double.parseDouble(component2Tokenizer.nextToken().trim());
      avg = Math.sqrt(comp1 * comp1 + comp2 * comp2);
      xyVals.set(avg / CM_S2_TO_G_CONVERSION_FACTOR, 1.0); // convert cm/s*s to G
    }
  }

  /**
   * Calculates the Exceed Prob Vals for the given Cybershake SA vals
   * Calculates the exceed prob. from the peak SA Vaules of Cybershake.
   * There peak SA values are arranged in ascending order. It calculates the
   * exced prob. using:
   *  1 - exceed prob that does not exceed the given peak value.
   *
   */
  private void calcObsExceedProbVals(){
    int numVals= xyVals.getNum();
    for(int i=0;i<numVals;++i){
      double val = 1-((double)i)/numVals;
      xyVals.set(i,val);
    }
  }


  /**
   * Setting the Region parameters
   * @param str String
   */
  private void getLocation(String str) {
    StringTokenizer tokenizer = new StringTokenizer(str);
    double lat = Double.parseDouble(tokenizer.nextToken());
    double lon = Double.parseDouble(tokenizer.nextToken());
    loc = new Location(lat,lon);
  }


  private void setRupture(String str) {
    StringTokenizer tokenizer = new StringTokenizer(str);
    int  sourceIndex = Integer.parseInt(tokenizer.nextToken());
    int ruptureIndex = Integer.parseInt(tokenizer.nextToken());
    rupture =  frankelForecast.getRupture(sourceIndex, ruptureIndex);
  }

  private void setIMR() {
    //adds all the AttenRel classes to the ArrayList
    supportedAttenRelClasses.add(AS_CLASS_NAME);
    supportedAttenRelClasses.add(C_CLASS_NAME);
    supportedAttenRelClasses.add(SCEMY_CLASS_NAME);
    supportedAttenRelClasses.add(F_CLASS_NAME);
   // supportedAttenRelClasses.add(A_CLASS_NAME);
    supportedAttenRelClasses.add(CB_CLASS_NAME);
    supportedAttenRelClasses.add(SM_CLASS_NAME);
    supportedAttenRelClasses.add(USGS04_CLASS_NAME);
    supportedAttenRelClasses.add(AS_2005_PRELIM_CLASS_NAME);
   // supportedAttenRelClasses.add(CB_2005_PRELIM_CLASS_NAME);
    supportedAttenRelClasses.add(CY_2005_PRELIM_CLASS_NAME);
    supportedAttenRelClasses.add(Boore_2005_PRELIM_CLASS_NAME);
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

  private ScalarIntensityMeasureRelationshipAPI createIMRClassInstance(String AttenRelClassName){
    //String attenRelClassPackage = "org.opensha.sha.imr.attenRelImpl.";
      try {
        Class listenerClass = Class.forName( "org.opensha.commons.param.event.ParameterChangeWarningListener" );
        Object[] paramObjects = new Object[]{ this };
        Class[] params = new Class[]{ listenerClass };
        Class imrClass = Class.forName(AttenRelClassName);
        Constructor con = imrClass.getConstructor( params );
        ScalarIntensityMeasureRelationshipAPI attenRel = (ScalarIntensityMeasureRelationshipAPI)con.newInstance( paramObjects );
        //setting the Attenuation with the default parameters
        attenRel.setParamDefaults();
        return attenRel;
      } catch ( ClassCastException e ) {
        e.printStackTrace();
      } catch ( ClassNotFoundException e ) {
       e.printStackTrace();
      } catch ( NoSuchMethodException e ) {
       e.printStackTrace();
      } catch ( InvocationTargetException e ) {
        e.printStackTrace();
      } catch ( IllegalAccessException e ) {
        e.printStackTrace();
      } catch ( InstantiationException e ) {
        e.printStackTrace();
      }
      return null;
  }




  /**
   * Setting the intensity Measure in the Attenuation Relationship
   * @param str String
   */
  public void setIMT(String str){
    StringTokenizer tokenizer = new StringTokenizer(str);
    imt = tokenizer.nextToken().trim();
    if(imt.equalsIgnoreCase("SA")){
      double period = Double.parseDouble(tokenizer.nextToken());
      this.period = period;
    }
  }

  /**
   * Sets the IMT in the AttenuationRelationship
   * @param attenRel AttenuationRelationshipAPI
   */
  private void setIMT(ScalarIntensityMeasureRelationshipAPI attenRel) {
    try{
      attenRel.setIntensityMeasure(imt);
    }catch(Exception e){
      System.out.println(imt+" not supported by attenuation relationship "+attenRel.getName());
      System.exit(0);
    }
    if(imt.equalsIgnoreCase("SA")){

      try{
        attenRel.getParameter(PeriodParam.NAME).setValue(new
            Double(period));
      }
      catch (Exception e) {
        System.out.println("SA Period = "+period + " not supported by attenuation relationship " +
                           attenRel.getName());
        System.exit(0);
      }
    }
  }







  /**
   * Getting the default site type in case region is outside the California region
   * @param str String
   */
  private void setDefaultWillsSiteType(String str) {
    defaultSiteType = str.trim();
  }




  /**
   * set the site params in IMR according to basin Depth and vs 30
   * @param imr
   * @param lon
   * @param lat
   * @param willsClass
   * @param basinDepth
   */
  private void setSiteParamsInIMR(ScalarIntensityMeasureRelationshipAPI attenRel,
                                  String willsClass, double basinDepth) {

    Iterator it = attenRel.getSiteParamsIterator(); // get site params for this IMR
    SiteTranslator siteTranslator = new SiteTranslator();
    Site site = new Site(loc);
    while(it.hasNext()) {
      ParameterAPI tempParam = (ParameterAPI)it.next();
      site.addParameter(tempParam);
      //adding the site Params from the CVM, if site is out the range of CVM then it
      //sets the site with whatever site Parameter Value user has choosen in the application
      boolean flag = siteTranslator.setParameterValue(tempParam,willsClass,basinDepth);
      if( !flag ) {
        String message = "cannot set the site parameter \""+tempParam.getName()+"\" from Wills class \""+willsClass+"\""+
                         "\n (no known, sanctioned translation - please set by hand)";

        System.out.println(message);
      }
    }
    attenRel.setSite(site);

  }

  /**
   * This method is called when user presses the button to set the params from CVM
   * for choosen IMR's
   * @param e
   */
  void setSiteParam() {
    LocationList locList = new LocationList();
    locList.add(new Location(loc.getLatitude(),loc.getLongitude()));

    // get the vs 30 and basin depth from cvm
    try {
      willsClass = (String) (ConnectToCVM.getWillsSiteTypeFromCVM(locList)).get(
          0);
      basinDepth = ( (Double) (ConnectToCVM.getBasinDepthFromCVM(locList)).get(0)).
          doubleValue();
    }
    catch (Exception ex) {
      ex.printStackTrace();
    }
    if(willsClass.equals("NA"))
      willsClass = defaultSiteType;

  }


  /**
   * Creates the ObsExceedProbFile
   */
  private void createObsExceedProbFile(){

    try{
      FileWriter fw = new FileWriter("AttenuationRelationship_Cybershake_test.txt");
      for(int i=0;i<this.supportedAttenRelClasses.size();++i){
        String attenRel = (String)supportedAttenRelClasses.get(i);
        ScalarIntensityMeasureRelationshipAPI imr = this.createIMRClassInstance(attenRel);
        this.setIMT(imr);
        setSiteParamsInIMR(imr,willsClass, basinDepth);
        imr.setEqkRupture(rupture);
        DiscretizedFuncAPI arb = initX_Values();
        imr.getExceedProbabilities(arb);
        toggleHazFuncLogValues(arb);
        fw.write("#Exceed Prob Vals for :"+imr.getName()+"\n");
        fw.write(xyVals.toString()+"\n\n");
      }
      this.calcObsExceedProbVals();
      fw.write("#Observed Exceed Prob. Values in the Cybershake\n");
      fw.write(xyVals.toString()+"\n");

      fw.close();
    }catch(IOException e){
      e.printStackTrace();
    }
  }

  /**
   * set x values in log space for Hazard Function to be passed to IMR
   * if the selected IMT are SA , PGA , PGV or FaultDispl
   * It accepts 1 parameters
   *
   * @param originalFunc :  this is the function with X values set
   */
  private DiscretizedFuncAPI initX_Values(){
    DiscretizedFuncAPI arb = new ArbitrarilyDiscretizedFunc();
      for(int i=0;i<xyVals.getNum();++i)
        arb.set(Math.log(xyVals.getX(i)),1);
      return arb;
  }


  /**
   * set x values back from the log space to the original linear values
   * for Hazard Function after completion of the Hazard Calculations
   * if the selected IMT are SA , PGA or PGV
   * It accepts 1 parameters
   *
   * @param hazFunction :  this is the function with X values set
   */
  private ArbitrarilyDiscretizedFunc toggleHazFuncLogValues(DiscretizedFuncAPI arb){

      for(int i=0; i<arb.getNum(); ++i)
        xyVals.set(i, arb.getY(i));
      return xyVals;

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


  private void createERFInstance(){
    frankelForecast = new
        Frankel02_AdjustableEqkRupForecast();

    frankelForecast.getAdjustableParameterList().getParameter(
        Frankel02_AdjustableEqkRupForecast.
        BACK_SEIS_NAME).setValue(Frankel02_AdjustableEqkRupForecast.
                                 BACK_SEIS_INCLUDE);

    frankelForecast.getAdjustableParameterList().getParameter(
        Frankel02_AdjustableEqkRupForecast.BACK_SEIS_RUP_NAME).
        setValue(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_RUP_FINITE);

    frankelForecast.getAdjustableParameterList().getParameter(
        Frankel02_AdjustableEqkRupForecast.FAULT_MODEL_NAME).setValue(
            frankelForecast.FAULT_MODEL_STIRLING);
    frankelForecast.getAdjustableParameterList().getParameter(
        Frankel02_AdjustableEqkRupForecast.RUP_OFFSET_PARAM_NAME).setValue(
            new Double(5.0));

    frankelForecast.getTimeSpan().setDuration(1.0);
    frankelForecast.updateForecast();

  }


  /**
   * Main Methid to run the application
   * @param args String[]
   */
  public static void main(String[] args) {


    ObsExceedProbCalculator calc = new ObsExceedProbCalculator();
    calc.createERFInstance();
    try {
      calc.parseFile("/Users/nitingupta/projects/sha_new/org/opensha/cybershake/CyberShakeInputFile.txt");
    }
    catch (FileNotFoundException ex) {
      ex.printStackTrace();
    }
    catch (IOException ex) {
      ex.printStackTrace();
    }
    /*try {
      calc.parseFile(args[0]);
    }
    catch (FileNotFoundException ex) {
      System.out.println("Input File "+ args[0] +" not found");
      System.exit(0);
    }
    catch (Exception ex) {
      System.out.println("Unable to parse the input file"+ args[0]);
      System.out.println("Please provide correct input file.");
      System.exit(0);
    }*/
    calc.setIMR();
    calc.setSiteParam();
    calc.createObsExceedProbFile();
  }
}
