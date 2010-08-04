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

package org.opensha.nshmp.sha.pager;


import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.ScenarioShakeMapCalculator;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.gui.beans.MapGuiBean;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.param.SimpleFaultParameter;
import org.opensha.sha.util.SiteTranslator;


/**
 * <p>Title: PagerShakeMapCalc</p>
 *
 * <p>Description: </p>
 *
 * @author Nitin Gupta, Vipin Gupta, and Ned Field
 * @version 1.0
 */
public class PagerShakeMapCalc implements ParameterChangeWarningListener{


  /**
   * Parameters from the input file
   */
  private SitesInGriddedRegion sites; //Geographic Region
  private EqkRupture rupture; //EqkRupture
  private ScalarIntensityMeasureRelationshipAPI attenRel; //Attenunation Relationship to be used.
  private boolean imlAtProb; //checks what to plot IML_At_Prob or Prob_At_IML
  private double imlProbVal; //if IML@Prob needs to be calculated the Prob val
  //will be given,else IML val will be given
  private String imt;
  private boolean pointSourceCorrection; //if point source corrcetion needs to be applied
  private boolean gmtMapToGenerate; // if GMT map needs to be geberated
  private String defaultSiteType; //in case we are not able to get the site type for any site
  //in the region.
  
  private ArrayList lats, lons,dips,depths;

  //instance to the Scenario ShakeMap Calc
  private ScenarioShakeMapCalculator calc;

  //checks if Point of Finite source rupture.
  private int numPoints;
  private double mag,aveRake,aveDip,aveUpperSiesDepth,aveLowerSiesDepth;
  

  private DecimalFormat latLonFormat  = new DecimalFormat("0.000##");
  private DecimalFormat meanSigmaFormat = new DecimalFormat("0.000##");

  //Map Making Gui Bean
  private MapGuiBean mapGuiBean;

  private String outputFilePrefix;


  public PagerShakeMapCalc() {
  }


  private void parseFile(String fileName) throws FileNotFoundException,IOException{

      ArrayList fileLines = null;

      fileLines = FileUtils.loadFile(fileName);
      
      int j = 0;
      for(int i=0; i<fileLines.size(); ++i) {
        String line = ((String)fileLines.get(i)).trim();
        // if it is comment skip to next line
        if(line.startsWith("#") || line.equals("")) continue;

        if(j==0) setRegionParams(line); // first line sets the region Params
        else if(j==1) getRupture(line) ; // set the rupture params
        else if(j==2){
        	numPoints = Integer.parseInt(line.trim());
        	if(numPoints == 1){
        		++i;
    			line = ((String)fileLines.get(i)).trim();
        		setPointRuptureSurface(line);
        	}
        	else if(numPoints >1){
        		
        		lats = new ArrayList();
        		lons = new ArrayList();
        		depths = new ArrayList();
        		dips  = new ArrayList();
        		for(int k=0;k<numPoints;++k){
        			++i;
        			line = ((String)fileLines.get(i)).trim();
        			readLocationLine(line);
        		}
        		setFiniteRuptureSurface();
        	}
        }
        else if(j==3) setIMR(line); // set the imr
        else if(j==4) setIMT(line);  // set the IMT
        else if(j==5) setMapType(line); // map type iml at Prob or Prob at IML
        else if(j==6) setPointSrcCorrection(line); // whether point source correction is needed or not needed
        else if(j==7) setDefaultWillsSiteType(line); // default site to use if site parameters are not known for a site
        else if(j==8) setMapRequested(line) ; // whether to generate GMT map
        else if(j==9) setOutputFileName(line); // set the output file name
        ++j;
      }
  }
  
  private void setFiniteRuptureSurface(){
	  depths.add(aveUpperSiesDepth);
	  depths.add(aveLowerSiesDepth);
	  dips.add(aveDip);
	  SimpleFaultParameter faultParameter;
	  faultParameter = new SimpleFaultParameter("Simple Fault Surface");
	  faultParameter.setNumFaultTracePoints(lats.size());
	  faultParameter.setNumDips(dips.size());
	  faultParameter.setAll(SimpleFaultParameter.DEFAULT_GRID_SPACING, 
				lats, lons, dips, depths, SimpleFaultParameter.STIRLING);
	  faultParameter.setEvenlyGriddedSurfaceFromParams();
	  rupture = new EqkRupture();
	  rupture.setRuptureSurface((EvenlyGriddedSurfaceAPI)faultParameter.getValue());
	  rupture.setAveRake(aveRake);
	  rupture.setMag(mag);
	  
  }
  
  private void readLocationLine(String str){
	  StringTokenizer tokenizer = new StringTokenizer(str);
	  lats.add(Double.parseDouble(tokenizer.nextToken().trim()));
	  lons.add(Double.parseDouble(tokenizer.nextToken().trim()));
  }
  

  /**
   * Setting the Region parameters
   * @param str String
   */
  private void setRegionParams(String str) {
    StringTokenizer tokenizer = new StringTokenizer(str);
    double minLat = Double.parseDouble(tokenizer.nextToken());
    double maxLat = Double.parseDouble(tokenizer.nextToken());
    double minLon = Double.parseDouble(tokenizer.nextToken());
    double maxLon = Double.parseDouble(tokenizer.nextToken());
    double gridSpacing = Double.parseDouble(tokenizer.nextToken());
    if(minLat >= maxLat){
      System.out.println("MinLat must be less than MaxLat");
      System.exit(0);
    }
    if(minLon >= maxLon){
      System.out.println("MinLon must be less than MaxLon");
      System.exit(0);
    }

//    try {
//  	  GriddedRegion eggr = 
//		  new GriddedRegion(minLat, maxLat, minLon,
//          maxLon, gridSpacing);
    GriddedRegion eggr = new GriddedRegion(
    		new Location(minLat, minLon),
    		new Location(maxLat, maxLon),
    		gridSpacing, new Location(0,0));
      sites = new SitesInGriddedRegion(eggr);
//    }
//    catch (RegionConstraintException ex) {
//      System.out.println(ex.getMessage());
//      System.exit(0);
//    }
  }
  
  private void getRupture(String str){
	  StringTokenizer tokenizer = new StringTokenizer(str);
	  mag = Double.parseDouble(tokenizer.nextToken());
	  aveRake = Double.parseDouble(tokenizer.nextToken());
	  aveDip = Double.parseDouble(tokenizer.nextToken());
	  aveUpperSiesDepth = Double.parseDouble(tokenizer.nextToken());
	  aveLowerSiesDepth = Double.parseDouble(tokenizer.nextToken());
  }

  private void setPointRuptureSurface(String str) {
    StringTokenizer tokenizer = new StringTokenizer(str);
    double rupLat = Double.parseDouble(tokenizer.nextToken());
    double rupLon = Double.parseDouble(tokenizer.nextToken());
    
    rupture = new EqkRupture();
    Location rupLoc = new Location(rupLat,rupLon,aveUpperSiesDepth);
    rupture.setPointSurface(rupLoc,aveDip);
    //    rupture.setHypocenterLocation(rupLoc);    // this will put a star at the hypocenter
    rupture.setMag(mag);
    rupture.setAveRake(aveRake);
  }

  private void setIMR(String str) {
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

  private void createIMRClassInstance(String AttenRelClassName){
    String attenRelClassPackage = "org.opensha.sha.imr.attenRelImpl.";
      try {
        Class listenerClass = Class.forName( "org.opensha.commons.param.event.ParameterChangeWarningListener" );
        Object[] paramObjects = new Object[]{ this };
        Class[] params = new Class[]{ listenerClass };
        Class imrClass = Class.forName(attenRelClassPackage+AttenRelClassName);
        Constructor con = imrClass.getConstructor( params );
        attenRel = (ScalarIntensityMeasureRelationshipAPI)con.newInstance( paramObjects );
        //setting the Attenuation with the default parameters
        attenRel.setParamDefaults();
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
  }


  /**
   * Setting the intensity Measure in the Attenuation Relationship
   * @param str String
   */
  private void setIMT(String str) {
    StringTokenizer tokenizer = new StringTokenizer(str);
    imt = tokenizer.nextToken().trim();
    try{
      attenRel.setIntensityMeasure(imt);
    }catch(Exception e){
      System.out.println(imt+" not supported by attenuation relationship "+attenRel.getName());
      System.exit(0);
    }
    if(imt.equalsIgnoreCase("SA")){
      double period = Double.parseDouble(tokenizer.nextToken());
      try{
        attenRel.getParameter(PeriodParam.NAME).setValue(new
            Double(period));
      }
      catch (Exception e) {
        System.out.println("SA Period = "+period + " not supported by attenuation relationship " +
                           attenRel.getName());
        System.exit(0);
      }
      imt += "-"+period;
    }
  }


  /**
   * Getting what user wants to plot. IML@Prob or Prob@IML.
   * Then getting the IML or Prob value
   * @param str String
   */
  private void setMapType(String str) {
    StringTokenizer tokenizer = new StringTokenizer(str);
    int mapType = Integer.parseInt(tokenizer.nextToken());
    if (mapType == 0)
      this.imlAtProb = true;
    else if(mapType ==1)
      this.imlAtProb = false;
    else{
      System.out.println("Incorrect input for the MapType, please enter:");
      System.out.println("0: IML @ Prob Map ");
      System.out.println("1: Prob @ IML map ");
      System.exit(0);
    }
    imlProbVal = Double.parseDouble(tokenizer.nextToken());
  }


  /**
   * Checking if the point source corection needs to be applied for the calculation
   * @param str String
   */
  private void setPointSrcCorrection(String str) {
    StringTokenizer tokenizer = new StringTokenizer(str);
    int intVal = Integer.parseInt(tokenizer.nextToken());
    if(intVal==0) pointSourceCorrection = false;
    else if(intVal ==1)
      pointSourceCorrection = true;
    else{
      System.out.println("Incorrect input for Point Source Correction, please enter:");
      System.out.println("0: No Point Source Correction");
      System.out.println("1: Apply Point Source Correction");
      System.exit(0);
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
   * Checking if GMT map to be generated
   * @param str String
   */
  private void setMapRequested(String str) {
    StringTokenizer tokenizer = new StringTokenizer(str);
    int intVal = Integer.parseInt(tokenizer.nextToken());
    if(intVal==0) gmtMapToGenerate = false;
    else if(intVal == 1)gmtMapToGenerate = true;
    else{
      System.out.println("Incorrect input to see if map needs to be generated using GMT");
      System.out.println("0: No Map to be generated");
      System.out.println("1: Map to be generated using GMT");
      System.exit(0);

    }
  }

  /**
   * Name of the output file
   * @param str String
   */
  private void setOutputFileName(String str) {
    outputFilePrefix = str.trim();
  }


  /**
   * Gets the wills site class for the given sites
   */
  private void getSiteParamsForRegion() {
    sites.addSiteParams(attenRel.getSiteParamsIterator());
    //getting Wills Site Class
    sites.setSiteParamsForRegionFromServlet(false);
    //getting the Attenuation Site Parameters Liat
    ListIterator it = attenRel.getSiteParamsIterator();
    //creating the list of default Site Parameters, so that site parameter values can be filled in
    //if Site params file does not provide any value to us for it.
    ArrayList defaultSiteParams = new ArrayList();
    SiteTranslator siteTrans = new SiteTranslator();
    while (it.hasNext()) {
      //adding the clone of the site parameters to the list
      ParameterAPI tempParam = (ParameterAPI) ( (ParameterAPI) it.next()).clone();
      //getting the Site Param Value corresponding to the default Wills site class selected by the user
      // for the seleted IMR  from the SiteTranslator
      siteTrans.setParameterValue(tempParam, defaultSiteType, Double.NaN);
      defaultSiteParams.add(tempParam);
    }
    sites.setDefaultSiteParams(defaultSiteParams);
  }

  /**
   *
   * @return XYZ_DataSetAPI
   */
  private XYZ_DataSetAPI pagerShakeMapCalc() throws RegionConstraintException,
      ParameterException {

    PropagationEffect propagationEffect = new PropagationEffect();

    ParameterList paramList = propagationEffect.getAdjustableParameterList();
    paramList.getParameter(propagationEffect.APPROX_DIST_PARAM_NAME).setValue(new
        Boolean(true));

    if (pointSourceCorrection)
      paramList.getParameter(propagationEffect.POINT_SRC_CORR_PARAM_NAME).
          setValue(new Boolean(true));
    else
      paramList.getParameter(propagationEffect.POINT_SRC_CORR_PARAM_NAME).
          setValue(new Boolean(false));

    //Calls the ScenarioShakeMap Calculator to generate Median File
    calc = new ScenarioShakeMapCalculator(propagationEffect);
    ArrayList attenRelsSupported = new ArrayList();
    attenRelsSupported.add(attenRel);
    ArrayList attenRelWts = new ArrayList();
    attenRelWts.add(new Double(1.0));
    XYZ_DataSetAPI xyzDataSet = calc.getScenarioShakeMapData(attenRelsSupported,attenRelWts,sites,rupture,!imlAtProb,imlProbVal);
    //if the IMT is log supported then take the exponential of the Value if IML @ Prob
    if (IMT_Info.isIMT_LogNormalDist(attenRel.getIntensityMeasure().getName()) && imlAtProb) {
      ArrayList zVals = xyzDataSet.getZ_DataSet();
      int size = zVals.size();
      for (int i = 0; i < size; ++i) {
        double tempVal = Math.exp( ( (Double) (zVals.get(i))).doubleValue());
        zVals.set(i, new Double(tempVal));
      }
    }
    return xyzDataSet;
  }


  private void createMedianFile(XYZ_DataSetAPI xyzData){

    ArrayList xVals = xyzData.getX_DataSet();
    ArrayList yVals = xyzData.getY_DataSet();
    ArrayList zVals = xyzData.getZ_DataSet();
    try {
      FileWriter fw = new FileWriter(this.outputFilePrefix + "_data.txt");
      int size = xVals.size();
      for(int i=0;i<size;++i)
        fw.write(latLonFormat.format(xVals.get(i))+"  "+latLonFormat.format(yVals.get(i))+"  "+
                 meanSigmaFormat.format(zVals.get(i))+"\n");
      fw.close();
    }
    catch (IOException ex) {
      ex.printStackTrace();
    }
  }

  /**
   * This method creates the Scenario ShakeMap
   * @param xyzDataSet XYZ_DataSetAPI
   */
  private void createMap(XYZ_DataSetAPI xyzDataSet) {
    if (gmtMapToGenerate) {
      mapGuiBean = new MapGuiBean();
      mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.LOG_PLOT_NAME).
          setValue(new Boolean(false));
      mapGuiBean.setVisible(false);
      double minLat = sites.getRegion().getMinLat();
      double maxLat = sites.getRegion().getMaxLat();
      double minLon = sites.getRegion().getMinLon();
      double maxLon = sites.getRegion().getMaxLon();
      //checking if region bounds are within the range of the topographic file
      //else don't show any topography in the Scenario shakemaps
      if (maxLat > 43 || minLat < 32 || minLon < -126 || maxLon > -115) {
        mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.
            TOPO_RESOLUTION_PARAM_NAME).setValue(
                GMT_MapGenerator.TOPO_RESOLUTION_NONE);
      }
      mapGuiBean.setRegionParams(minLat, maxLat, minLon, maxLon,
    		  sites.getRegion().getSpacing());
      String label = "";
      if (imlAtProb)
        label = imt;
      else
        label = "prob";

      mapGuiBean.makeMap(xyzDataSet, rupture, label, getMapParametersInfo());
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

  /**
   *
   * @returns the String containing the values selected for different parameters
   */
  private String getMapParametersInfo() {

    String imrMetadata = "Selected Attenuation Relationship:<br>\n " +
        "---------------<br>\n";

    imrMetadata += attenRel.getName() + "\n";

    String imtMetadata = "Selected IMT :<br>\n "+
        "---------------<br>\n";
    imtMetadata += imt+"<br>\n";

    //getting the metadata for the Calculation setting Params
    String calculationSettingsParamsMetadata =
        "<br><br>Calculation Param List:<br>\n " +
        "------------------<br>\n" + getCalcParamMetadataString() + "\n";

    return imrMetadata +imtMetadata+
        "<br><br>Region Info: <br>\n" +
        "----------------<br>\n" +
        "Min Lat = "+sites.getRegion().getMinLat()+"<br>\n"+
        "Max Lat = "+sites.getRegion().getMaxLat()+"<br>\n"+
        "Min Lon = "+sites.getRegion().getMinLon()+"<br>\n"+
        "Max Lon = "+sites.getRegion().getMaxLon()+"<br>\n"+
        "Default Wills Site Class Value = "+defaultSiteType+"<br>"+
        "\n" +
        "<br> Rupture Info: <br>\n"+
        rupture.getInfo()+ "\n" +
        "<br><br>GMT Param List: <br>\n" +
        "--------------------<br>\n" +
        mapGuiBean.getParameterList().getParameterListMetadataString() + "\n" +
        calculationSettingsParamsMetadata;
  }
  /**
   *
   * @returns the Adjustable parameters for the ScenarioShakeMap calculator
   */
  private ParameterList getCalcAdjustableParams(){
    return calc.getAdjustableParams();
  }


  /**
   *
   * @returns the Metadata string for the Calculation Settings Adjustable Params
   */
  private String getCalcParamMetadataString(){
    return getCalcAdjustableParams().getParameterListMetadataString();
  }

  /**
   * Main Methid to run the application
   * @param args String[]
   */
  public static void main(String[] args) {
    if (args.length != 1) {
      System.out.println("Must provide the input file name\n");
      System.out.println("Usage :\n\t" +
          "java -jar [jarfileName] [inputFileName]\n\n");
      System.out.println("jarfileName : Name of the executable jar file, by default it is PagerShakeMapCalc.jar");
      System.out.println(
          "inputFileName :Name of the input file,For eg: see \"inputFile.txt\". ");
      System.exit(0);
    }

    PagerShakeMapCalc pagershakemapcalc = new PagerShakeMapCalc();
    try {
      pagershakemapcalc.parseFile(args[0]);
    }
    catch (FileNotFoundException ex) {
      System.out.println("Input File "+ args[0] +" not found");
      System.exit(0);
    }
    catch (Exception ex) {
    	ex.printStackTrace();
      System.out.println("Unable to parse the input file"+ args[0]);
      System.out.println("Please provide correct input file.");
      System.exit(0);
    }

    pagershakemapcalc.getSiteParamsForRegion();
    XYZ_DataSetAPI xyzDataSet = null;
    try {
      xyzDataSet = pagershakemapcalc.pagerShakeMapCalc();
    }
    catch (ParameterException ex1) {
      System.out.println(ex1.getMessage());
    }
    catch (RegionConstraintException ex1) {
      System.out.println(ex1.getMessage());
    }
    pagershakemapcalc.createMedianFile(xyzDataSet);
    pagershakemapcalc.createMap(xyzDataSet);
  }
}
