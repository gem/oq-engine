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

package org.opensha.sha.imr.attenRelImpl;

import java.text.DecimalFormat;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.IMRException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerConstraint;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.Parameter;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <b>Title:</b> BS_2003_AttenRel<p>
 *
 * <b>Description:</b> This implements the site effect models
 * developed by Bazzuro and Cornell(2004), Baturay and Stewart(2003), applied
 * to the Abrahamson & Silva (1997) rock-site predictions. <p>
 *
 * Supported Intensity-Measure Parameters:<p>
 * <UL>
 * <LI>saParam - Response Spectral Acceleration
 * <LI>pgaParam - Peak Ground Acceleration
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>distanceRupParam - closest distance to surface projection of fault
 * <LI>vs30Param - Average 30-meter shear-wave velocity at the site
 * <LI>softSoilParam - To overide Vs30 and apply NEHPR E (see INFO for details)
 * <LI>fltTypeParam - Style of faulting
 * <LI>isOnHangingWallParam - tells if site is directly over the rupture surface
 * <LI>componentParam - Component of shaking (only one)
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL><p>
 *
 * @author     Edward H. Field
 * @created    july, 2004
 * @version    1.0
 */


public class BS_2003_AttenRel
    extends AttenuationRelationship implements ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI {

  // debugging stuff:
  private final static String C = "BS_2006_AttenRel";
  private final static boolean D = false;
  public final static String NAME = "Baturay and Stewart (2003)";
  public final static String SHORT_NAME = "BS2006";
  private static final long serialVersionUID = 1234567890987654356L;



  // warning constraint fields:
  protected final static Double VS30_WARN_MIN = new Double(50.0);
  protected final static Double VS30_WARN_MAX = new Double(760.0);

  // the Soft Soil Parameter
  private BooleanParameter softSoilParam = null;
  public final static String SOFT_SOIL_NAME = "Soft Soil Case";
  public final static String SOFT_SOIL_INFO =
      "Indicates that site is considered NEHRP E regardless of Vs30.\n\n" +
      "Conditions required are undrained shear strength < 24 kPa, " +
      "PI > 20, water content > 40%, and thickness of clay exceeds 3 m.";
  public final static Boolean SOFT_SOIL_DEFAULT = new Boolean(false);

  private AS_1997_AttenRel as_1997_attenRel;
  /**
   * The current set of coefficients based on the selected intensityMeasure
   */
  private BS_2003_AttenRelCoefficients coeffs = null;
  
  
  //Intercept param
  private DoubleParameter AF_InterceptParam;
  public final static String AF_INTERCEPT_PARAM_NAME = "AF Intercept";
  public final static String AF_INTERCEPT_PARAM_INFO = 
	  "Intercept of the median regression model for the ground response analyses";
  private DoubleConstraint AF_InterceptparamConstraint = new DoubleConstraint(-2,2);
  public final static double AF_INTERCEPT_PARAM_DEFAULT = 0;
  
  //Slope Param
  private DoubleParameter AF_SlopeParam;
  public final static String AF_SLOPE_PARAM_NAME = "AF Slope";
  public final static String AF_SLOPE_PARAM_INFO = 
	  "Slope of the median regression model for the ground response analyses";
  private DoubleConstraint AF_slopeParamConstraint = new DoubleConstraint(-1,1);
  public final static double AF_SLOPE_PARAM_DEFAULT = 0;
  
  //Additive refeerence acceleration param
  private DoubleParameter AF_AddRefAccParam;
  public final static String AF_ADDITIVE_REF_ACCELERATION_PARAM_NAME = "AF Add. Ref. Acceleration";
  public final static String AF_ADDITIVE_REF_ACCELERATION_PARAM_INFO = 
	  "Additive reference acceleration of the median regression model for the ground response " +
	  "analyses. This parameter improves the linear model fit for low Sa(rock) / PGA(rock)" +
	  "values and leads to more relaistic predictons than quadratic models";
  private DoubleConstraint AFaddRefAccParamConstraint = new DoubleConstraint(0,0.5);
  public final static double AF_ADDITIVE_REF_ACCERLATION_DEFAULT = 0.03;
  
  
  //Std. Dev AF param
  private DoubleParameter AF_StdDevParam;
  public final static String AF_STD_DEV_PARAM_NAME = "Std. Dev. AF";
  public final static String AF_STD_DEV_PARAM_INFO = 
	  "Standard Deviation of the amplification factor from the ground response analyses" +
	  " regression model";
  private DoubleConstraint AF_StdDevParamConstraint = new DoubleConstraint(0,1.0);
  public final static double AF_STD_DEV_DEFAULT = 0.3;
  
  //number of runs parameter
  private IntegerParameter numRunsParam;
  public final static String NUM_RUNS_PARAM_NAME = "Number of Runs";
  public final static String NUM_RUNS_PARAM_INFO = "Number of runs of the wave propagation"+
	  " simulation for the site";
  private IntegerConstraint numRunsConstraint = new IntegerConstraint(1,Integer.MAX_VALUE);
  public final static int NUM_RUNS_PARAM_DEFAULT = 1;

  
  /**
   *  Hashtable of coefficients for the supported intensityMeasures
   */
  protected Hashtable horzCoeffs = new Hashtable();

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   *  No-Arg constructor. This initializes several ParameterList objects.
   */
  public BS_2003_AttenRel(ParameterChangeWarningListener warningListener) {

    super();

    this.warningListener = warningListener;

    as_1997_attenRel = new AS_1997_AttenRel(warningListener);
    // set the site type to rock
    as_1997_attenRel.getParameter(as_1997_attenRel.SITE_TYPE_NAME).setValue(
        as_1997_attenRel.SITE_TYPE_ROCK);
    // set the component to ave horz
    as_1997_attenRel.getParameter(ComponentParam.NAME).setValue(
        ComponentParam.COMPONENT_AVE_HORZ);

    // overide local params with those in as_1997_attenRel
    this.sigmaTruncTypeParam = (SigmaTruncTypeParam) as_1997_attenRel.getParameter(
        SigmaTruncTypeParam.NAME);
    this.sigmaTruncLevelParam = (SigmaTruncLevelParam) as_1997_attenRel.getParameter(
        SigmaTruncLevelParam.NAME);
    this.exceedProbParam = (DoubleParameter) as_1997_attenRel.getParameter(
        as_1997_attenRel.EXCEED_PROB_NAME);
    this.stdDevTypeParam = (StdDevTypeParam) as_1997_attenRel.getParameter(
    		StdDevTypeParam.NAME);
    this.saPeriodParam = (PeriodParam) as_1997_attenRel.getParameter(
        PeriodParam.NAME);

    initCoefficients();
    initSupportedIntensityMeasureParams();
    initEqkRuptureParams();
    initPropagationEffectParams();
    initSiteParams();		// do only in constructor
    initOtherParams();

    initIndependentParamLists(); // Do this after the above
  }
  
  protected void setRockAttenAndParamLists() {
	  
  }

  /**
   * This does nothing, but is needed.
   */
  protected void setPropagationEffectParams() {

  }

  /**
   *  This sets the eqkRupture related parameters.
   *
   * @param  eqkRupture  The new eqkRupture value
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setEqkRupture(EqkRupture eqkRupture) throws InvalidRangeException {
    this.as_1997_attenRel.setEqkRupture(eqkRupture);
    this.eqkRupture = eqkRupture;
  }

  /**
   *  This sets the site-related parameter (vs30Param) based on what is in
   *  the Site object passed in.  WarningExceptions are ingored
   *
   * @param  site             The new site value which contains a Vs30 Parameter
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   */
  public void setSite(Site site) throws ParameterException {

	
    AF_InterceptParam.setValue((Double)site.getParameter(AF_INTERCEPT_PARAM_NAME).getValue());
    AF_AddRefAccParam.setValue((Double)site.getParameter(AF_ADDITIVE_REF_ACCELERATION_PARAM_NAME).getValue());
    AF_SlopeParam.setValue((Double)site.getParameter(AF_SLOPE_PARAM_NAME).getValue());
    AF_StdDevParam.setValue((Double)site.getParameter(AF_STD_DEV_PARAM_NAME).getValue());
    
    vs30Param.setValueIgnoreWarning((Double)site.getParameter(Vs30_Param.NAME).getValue());
    softSoilParam.setValue((Boolean)(site.getParameter(SOFT_SOIL_NAME).getValue()));
    numRunsParam.setValue((Integer)site.getParameter(NUM_RUNS_PARAM_NAME).getValue());
    this.site = site;
    // set the location in as_1997_attenRel
    as_1997_attenRel.setSiteLocation(site.getLocation());
  }

  /**
   * This function determines which set of coefficients in the HashMap
   * are to be used given the current intensityMeasure (im) Parameter.
   */
  protected void updateCoefficients() throws ParameterException {
    // Check that parameter exists
    if (im == null) {
      throw new ParameterException(C +
                                   ": updateCoefficients(): " +
                                   "The Intensity Measusre Parameter has not been set yet, unable to process."
          );
    }

    StringBuffer key = new StringBuffer(im.getName());
    if (im.getName().equalsIgnoreCase(SA_Param.NAME)) {
      key.append("/" + saPeriodParam.getValue());
    }
    if (horzCoeffs.containsKey(key.toString())) {
      coeffs = (BS_2003_AttenRelCoefficients) horzCoeffs.get(key.toString());
    }
    else {
      throw new ParameterException(C + ": setIntensityMeasureType(): " +
                                   "Unable to locate coefficients with key = " +
                                   key);
    }
  }

  /**
   * Calculates the mean
   * @return    The mean value
   */
  public double getMean() throws IMRException {

    double asRockSA, lnAF;

    // get AS-1997 SA for rock
    as_1997_attenRel.setIntensityMeasure(im);
    asRockSA = as_1997_attenRel.getMean();
    
    // get the amp factor
    double aVal = ((Double)AF_InterceptParam.getValue()).doubleValue();
    double bVal = ((Double)AF_SlopeParam.getValue()).doubleValue();
    double cVal = ((Double)AF_AddRefAccParam.getValue()).doubleValue();
    lnAF = aVal+bVal*Math.log(Math.exp(asRockSA)+cVal);   

    // return the result
    return lnAF + asRockSA;
  }


  /**
   * Returns the Std Dev.
   */
  public double getStdDev(){
	  
	  String stdDevType = stdDevTypeParam.getValue().toString();
	  if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) { // "None (zero)"
		  return 0;
	  }
	  else {
			  float periodParamVal;
			  if(im.getName().equals(SA_Param.NAME))
				  periodParamVal = (float)((Double) saPeriodParam.getValue()).doubleValue();
			  else
				  periodParamVal = 0;
			   // this is inefficient if the im has not been changed in any way
		      updateCoefficients();
			  if(periodParamVal < 0.75)
				  return getStdDevForBS();
			  else if(periodParamVal > 1.5)
				  return getStdDevForCS();
			  else{
				  //getting the Std Dev for Period of 0.75
				  saPeriodParam.setValue(new Double(0.75));
				  double stdDev_BS = getStdDevForBS();
				  //getting the Std Dev. for period param 1.5
				  saPeriodParam.setValue(new Double(1.5));
				  double stdDev_CS = getStdDevForCS();
				  //setting the period to period selected by the user
				  DecimalFormat format = new DecimalFormat("##.###");
				  saPeriodParam.setValue(new Double(format.format(periodParamVal)));
				  //linear interpolation to get the Std Dev.
				  double stdDev = ((periodParamVal - 0.75)/(1.5 -0.75))*
				  (stdDev_CS - stdDev_BS) + stdDev_BS;
				  return stdDev;
			  }
	  }
  }
  
  
  /**
   * @return    The stdDev value for Baturay and Stewart (2003) Site Correction Model
   */
  private double getStdDevForBS(){
	  double stdDevAF = ((Double)this.AF_StdDevParam.getValue()).doubleValue();
	  int numRuns = ((Integer)this.numRunsParam.getValue()).intValue();
	  boolean softSoilCase = ((Boolean)this.softSoilParam.getValue()).booleanValue();
	  double stdError = stdDevAF/(Math.sqrt(numRuns));
	  double stdDev_gNet;
	  double vs30 = ((Double)vs30Param.getValue()).doubleValue();
	  if(vs30 <= 180 || softSoilCase)
		  stdDev_gNet = 0.38;
	  else
		  stdDev_gNet = 0.56;
	  double stdDev = Math.pow(stdDev_gNet,2)+Math.pow(stdError, 2)+coeffs.tau * coeffs.tau;
	  return Math.sqrt(stdDev);
  }

  /**
   * @return    The stdDev value for Choi and Stewart (2005) model
   */
  private double getStdDevForCS() throws IMRException {

      double vs30, sigmaV, sigmaAS;

      // get As-1997 stdDev
//      as_1997_attenRel.setIntensityMeasure(im);
//      sigmaAS = as_1997_attenRel.getStdDev();

      // set vs30 from the parameters
      if ( ( (Boolean) softSoilParam.getValue()).booleanValue()) {
        vs30 = 174;
      }
      else {
        try {
          vs30 = ( (Double) vs30Param.getValue()).doubleValue();
        }
        catch (NullPointerException e) {
          throw new IMRException(C + ": getMean(): " + ERR);
        }
      }

 
      // set sigmaV
      if (vs30 < 260) {
        sigmaV = coeffs.e1;
      }
      else if (vs30 < 360) {
        sigmaV = coeffs.e1 +
            ( (coeffs.e3 - coeffs.e1) / Math.log(360.0 / 260.0)) *
            Math.log(vs30 / 260.0);
      }
      else {
        sigmaV = coeffs.e3;
      }

      return Math.sqrt(sigmaV * sigmaV + coeffs.tau * coeffs.tau);
   
  }

  
  public void setParamDefaults() {

    //((ParameterAPI)this.iml).setValue( IML_DEFAULT );
    vs30Param.setValueAsDefault();
    softSoilParam.setValue(new Boolean(false));
    AF_AddRefAccParam.setValue(this.AF_ADDITIVE_REF_ACCERLATION_DEFAULT);
    AF_InterceptParam.setValue(this.AF_INTERCEPT_PARAM_DEFAULT);
    AF_SlopeParam.setValue(this.AF_SLOPE_PARAM_DEFAULT);
    AF_StdDevParam.setValue(this.AF_STD_DEV_DEFAULT);
    numRunsParam.setValue(this.NUM_RUNS_PARAM_DEFAULT);
    as_1997_attenRel.setParamDefaults();
    // re-set the site type to rock and component to ave horz
    as_1997_attenRel.getParameter(as_1997_attenRel.SITE_TYPE_NAME).setValue(
        as_1997_attenRel.SITE_TYPE_ROCK);
    as_1997_attenRel.getParameter(ComponentParam.NAME).setValue(
        ComponentParam.COMPONENT_AVE_HORZ);
    componentParam.setValueAsDefault();
  }

  /**
   * This creates the lists of independent parameters that the various dependent
   * parameters (mean, standard deviation, exceedance probability, and IML at
   * exceedance probability) depend upon. NOTE: these lists do not include anything
   * about the intensity-measure parameters or any of thier internal
   * independentParamaters.
   */
  protected void initIndependentParamLists() {

    // params that the mean depends upon
    meanIndependentParams.clear();
    ListIterator it = as_1997_attenRel.getMeanIndependentParamsIterator();
    String ignoreStr1 = as_1997_attenRel.SITE_TYPE_NAME;
    String ignoreStr2 = ComponentParam.NAME;
    while (it.hasNext()) {
      Parameter param = (Parameter) it.next();
      if (!ignoreStr1.equals(param.getName()) &&
          !ignoreStr2.equals(param.getName())) {
        meanIndependentParams.addParameter(param);
      }
    }
    meanIndependentParams.addParameter(AF_AddRefAccParam);
    meanIndependentParams.addParameter(AF_InterceptParam);
    meanIndependentParams.addParameter(AF_SlopeParam);
    meanIndependentParams.addParameter(AF_StdDevParam);
    meanIndependentParams.addParameter(vs30Param);
    meanIndependentParams.addParameter(softSoilParam);
    meanIndependentParams.addParameter(numRunsParam);
    meanIndependentParams.addParameter(componentParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    
    it = as_1997_attenRel.getStdDevIndependentParamsIterator();
    while (it.hasNext()) {
      Parameter param = (Parameter) it.next();
      if (!ignoreStr1.equals(param.getName()) &&
          !ignoreStr2.equals(param.getName())) {
        stdDevIndependentParams.addParameter(param);
      }
    }
    
    stdDevIndependentParams.addParameter(AF_AddRefAccParam);
    stdDevIndependentParams.addParameter(AF_InterceptParam);
    stdDevIndependentParams.addParameter(AF_SlopeParam);
    stdDevIndependentParams.addParameter(AF_StdDevParam);
    stdDevIndependentParams.addParameter(vs30Param);
    stdDevIndependentParams.addParameter(softSoilParam);
    stdDevIndependentParams.addParameter(numRunsParam);
    stdDevIndependentParams.addParameter(componentParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    it = as_1997_attenRel.getExceedProbIndependentParamsIterator();
    while (it.hasNext()) {
      Parameter param = (Parameter) it.next();
      if (!ignoreStr1.equals(param.getName()) &&
          !ignoreStr2.equals(param.getName())) {
        exceedProbIndependentParams.addParameter(param);
      }
    }
    
    exceedProbIndependentParams.addParameter(AF_AddRefAccParam);
    exceedProbIndependentParams.addParameter(AF_InterceptParam);
    exceedProbIndependentParams.addParameter(AF_SlopeParam);
    exceedProbIndependentParams.addParameter(AF_StdDevParam);
    exceedProbIndependentParams.addParameter(vs30Param);
    exceedProbIndependentParams.addParameter(softSoilParam);
    exceedProbIndependentParams.addParameter(numRunsParam);
    exceedProbIndependentParams.addParameter(componentParam);

    // params that the IML at exceed. prob. depends upon
    imlAtExceedProbIndependentParams.addParameterList(
        exceedProbIndependentParams);
    imlAtExceedProbIndependentParams.addParameter(exceedProbParam);

  }

  /**
   *  Creates the Vs30 site parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {

	vs30Param = new Vs30_Param(VS30_WARN_MIN, VS30_WARN_MAX);

    // make the Soft Soil parameter
    softSoilParam = new BooleanParameter(SOFT_SOIL_NAME, SOFT_SOIL_DEFAULT);
    softSoilParam.setInfo(SOFT_SOIL_INFO);
    
    //make the AF intercept paarameter
    AF_InterceptParam = new DoubleParameter(this.AF_INTERCEPT_PARAM_NAME,
    		AF_InterceptparamConstraint,this.AF_INTERCEPT_PARAM_DEFAULT);
    AF_InterceptParam.setInfo(this.AF_INTERCEPT_PARAM_INFO);
    
    //make the AF slope parameter
    this.AF_SlopeParam = new DoubleParameter(this.AF_SLOPE_PARAM_NAME,
    		this.AF_slopeParamConstraint,this.AF_SLOPE_PARAM_DEFAULT);
    AF_SlopeParam.setInfo(this.AF_SLOPE_PARAM_INFO);
    
    //make theb AF Additive Reference Paramerter
    this.AF_AddRefAccParam = new DoubleParameter(this.AF_ADDITIVE_REF_ACCELERATION_PARAM_NAME,
    		this.AFaddRefAccParamConstraint,this.AF_ADDITIVE_REF_ACCERLATION_DEFAULT);
    AF_AddRefAccParam.setInfo(this.AF_ADDITIVE_REF_ACCELERATION_PARAM_INFO);
    
    //make the AF Std. Dev.
    this.AF_StdDevParam = new DoubleParameter(this.AF_STD_DEV_PARAM_NAME,
    		this.AF_StdDevParamConstraint,this.AF_STD_DEV_DEFAULT);
    
    AF_StdDevParam.setInfo(this.AF_STD_DEV_PARAM_INFO);
    
    //make the number of runs parameter
    this.numRunsParam = new IntegerParameter(this.NUM_RUNS_PARAM_NAME,
    		this.numRunsConstraint,this.NUM_RUNS_PARAM_DEFAULT);
    numRunsParam.setInfo(this.NUM_RUNS_PARAM_INFO);
    

    // add it to the siteParams list:
    siteParams.clear();
    siteParams.addParameter(AF_AddRefAccParam);
    siteParams.addParameter(AF_InterceptParam);
    siteParams.addParameter(AF_SlopeParam);
    siteParams.addParameter(AF_StdDevParam);
    siteParams.addParameter(vs30Param);
    siteParams.addParameter(softSoilParam);
    siteParams.addParameter(numRunsParam);
  }

  /**
   *  Creates the two Potential Earthquake parameters (magParam and
   *  fltTypeParam) and adds them to the eqkRuptureParams
   *  list. Makes the parameters noneditable.
   */
  protected void initEqkRuptureParams() {

    eqkRuptureParams.clear();
    ListIterator it = as_1997_attenRel.getEqkRuptureParamsIterator();
    while (it.hasNext()) {
      eqkRuptureParams.addParameter( (Parameter) it.next());
    }
  }

  /**
   *  Creates the single Propagation Effect parameter and adds it to the
   *  propagationEffectParams list. Makes the parameters noneditable.
   */
  protected void initPropagationEffectParams() {
    propagationEffectParams.clear();
    ListIterator it = as_1997_attenRel.getPropagationEffectParamsIterator();
    while (it.hasNext()) {
      propagationEffectParams.addParameter( (Parameter) it.next());
    }

  }

  /**
   *  Creates the two supported IM parameters (PGA and SA), as well as the
   *  independenParameters of SA (periodParam and dampingParam) and adds
   *  them to the supportedIMParams list. Makes the parameters noneditable.
   */
  protected void initSupportedIntensityMeasureParams() {

    supportedIMParams.clear();
    Iterator it = as_1997_attenRel.getSupportedIntensityMeasuresIterator();
    while (it.hasNext()) {
      supportedIMParams.addParameter( (Parameter) it.next());
    }
  }

  /**
   *  Creates other Parameters that the mean or stdDev depends upon,
   *  such as the Component or StdDevType parameters.
   */
  protected void initOtherParams() {

    // init other params defined in parent class -- Don't need this
    // super.initOtherParams();

    // the Component Parameter (not supporting AS_1997's vertical)
    StringConstraint constraint = new StringConstraint();
    constraint.addString(ComponentParam.COMPONENT_AVE_HORZ);
    constraint.setNonEditable();
    componentParam = new ComponentParam(constraint,componentParam.COMPONENT_AVE_HORZ);

    // add this to the list
    otherParams.clear();
    otherParams.addParameter(componentParam);
    Iterator it = as_1997_attenRel.getOtherParamsIterator();
    Parameter param;
    while (it.hasNext()) {
      param = (Parameter) it.next();
      if (!ComponentParam.NAME.equals(param.getName())) {
        otherParams.addParameter(param);
      }
    }
  }

  /**
   * get the name of this IMR
   *
   * @returns the name of this IMR
   */
  public String getName() {
    return NAME;
  }

  /**
   * Returns the Short Name of each AttenuationRelationship
   * @return String
   */
  public String getShortName() {
    return SHORT_NAME;
  }

  /**
   *  This creates the hashtable of coefficients for the supported
   *  intensityMeasures (im).  The key is the im parameter name, plus the
   *  period value for SA (separated by "/").  For example, the key for SA
   *  at 1.0 second period is "SA/1.0".
   */
  protected void initCoefficients() {

    String S = C + ": initCoefficients():";
    if (D) {
      System.out.println(S + "Starting");
    }

    horzCoeffs.clear();

    BS_2003_AttenRelCoefficients coeff = new BS_2003_AttenRelCoefficients(
        PGA_Param.NAME,
        0.0, -0.64, 418, -0.36, -0.14, 0.27, 0.44, 0.50);

    BS_2003_AttenRelCoefficients coeff0 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.01")).doubleValue(),
        0.01, -0.64, 418, -0.36, -0.14, 0.27, 0.44, 0.50);
    BS_2003_AttenRelCoefficients coeff1 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.02")).doubleValue(),
        0.02, -0.63, 490, -0.34, -0.12, 0.26, 0.45, 0.51);
    BS_2003_AttenRelCoefficients coeff2 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.03")).doubleValue(),
        0.03, -0.62, 324, -0.33, -0.11, 0.26, 0.46, 0.51);
    BS_2003_AttenRelCoefficients coeff3 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.04")).doubleValue(),
        0.04, -0.61, 233, -0.31, -0.11, 0.26, 0.47, 0.51);
    BS_2003_AttenRelCoefficients coeff4 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.05")).doubleValue(),
        0.05, -0.64, 192, -0.29, -0.11, 0.25, 0.47, 0.52);
    BS_2003_AttenRelCoefficients coeff5 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.06")).doubleValue(),
        0.06, -0.64, 181, -0.25, -0.11, 0.25, 0.48, 0.52);
    BS_2003_AttenRelCoefficients coeff6 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.075")).doubleValue(),
        0.075, -0.64, 196, -0.23, -0.11, 0.24, 0.48, 0.52);
    BS_2003_AttenRelCoefficients coeff7 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.09")).doubleValue(),
        0.09, -0.64, 239, -0.23, -0.12, 0.23, 0.49, 0.52);
    BS_2003_AttenRelCoefficients coeff8 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.10")).doubleValue(),
        0.10, -0.60, 257, -0.25, -0.13, 0.23, 0.49, 0.53);
    BS_2003_AttenRelCoefficients coeff9 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.12")).doubleValue(),
        0.12, -0.56, 299, -0.26, -0.14, 0.24, 0.49, 0.53);
    BS_2003_AttenRelCoefficients coeff10 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.15")).doubleValue(),
        0.15, -0.53, 357, -0.28, -0.18, 0.25, 0.49, 0.54);
    BS_2003_AttenRelCoefficients coeff11 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.17")).doubleValue(),
        0.17, -0.53, 406, -0.29, -0.19, 0.26, 0.48, 0.55);
    BS_2003_AttenRelCoefficients coeff12 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.20")).doubleValue(),
        0.20, -0.52, 453, -0.31, -0.19, 0.27, 0.47, 0.56);
    BS_2003_AttenRelCoefficients coeff13 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.24")).doubleValue(),
        0.24, -0.52, 493, -0.38, -0.16, 0.29, 0.47, 0.56);
    BS_2003_AttenRelCoefficients coeff14 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.30")).doubleValue(),
        0.30, -0.52, 532, -0.44, -0.14, 0.35, 0.46, 0.57);
    BS_2003_AttenRelCoefficients coeff15 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.36")).doubleValue(),
        0.36, -0.51, 535, -0.48, -0.11, 0.38, 0.46, 0.57);
    BS_2003_AttenRelCoefficients coeff16 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.40")).doubleValue(),
        0.40, -0.51, 535, -0.50, -0.10, 0.40, 0.46, 0.57);
    BS_2003_AttenRelCoefficients coeff17 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.46")).doubleValue(),
        0.46, -0.50, 535, -0.55, -0.08, 0.42, 0.45, 0.58);
    BS_2003_AttenRelCoefficients coeff18 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.50")).doubleValue(),
        0.50, -0.50, 535, -0.60, -0.06, 0.42, 0.45, 0.59);
    BS_2003_AttenRelCoefficients coeff19 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.60")).doubleValue(),
        0.60, -0.49, 535, -0.66, -0.03, 0.42, 0.44, 0.60);
    BS_2003_AttenRelCoefficients coeff20 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.75")).doubleValue(),
        0.75, -0.47, 535, -0.69, 0.00, 0.42, 0.44, 0.63);
    BS_2003_AttenRelCoefficients coeff21 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.85")).doubleValue(),
        0.85, -0.46, 535, -0.69, 0.00, 0.42, 0.44, 0.63);
    BS_2003_AttenRelCoefficients coeff22 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("1.00")).doubleValue(),
        1.00, -0.44, 535, -0.70, 0.00, 0.42, 0.44, 0.64);
    BS_2003_AttenRelCoefficients coeff23 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("1.50")).doubleValue(),
        1.50, -0.40, 535, -0.72, 0.00, 0.42, 0.44, 0.67);
    BS_2003_AttenRelCoefficients coeff24 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("2.00")).doubleValue(),
        2.00, -0.38, 535, -0.73, 0.00, 0.43, 0.44, 0.69);
    BS_2003_AttenRelCoefficients coeff25 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("3.00")).doubleValue(),
        3.00, -0.34, 535, -0.74, 0.00, 0.45, 0.44, 0.71);
    BS_2003_AttenRelCoefficients coeff26 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("4.00")).doubleValue(),
        4.00, -0.31, 535, -0.75, 0.00, 0.47, 0.44, 0.73);
    BS_2003_AttenRelCoefficients coeff27 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("5.00")).doubleValue(),
        5.00, -0.30, 535, -0.75, 0.00, 0.49, 0.44, 0.75);
    // add zero-period case; same as 0.01 sec.
    BS_2003_AttenRelCoefficients coeff28 = new BS_2003_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.0")).doubleValue(),
        0.0, -0.64, 418, -0.36, -0.14, 0.27, 0.44, 0.50);

    horzCoeffs.put(coeff.getName(), coeff);
    horzCoeffs.put(coeff0.getName(), coeff0);
    horzCoeffs.put(coeff1.getName(), coeff1);
    horzCoeffs.put(coeff2.getName(), coeff2);
    horzCoeffs.put(coeff3.getName(), coeff3);
    horzCoeffs.put(coeff4.getName(), coeff4);
    horzCoeffs.put(coeff5.getName(), coeff5);
    horzCoeffs.put(coeff6.getName(), coeff6);
    horzCoeffs.put(coeff7.getName(), coeff7);
    horzCoeffs.put(coeff8.getName(), coeff8);
    horzCoeffs.put(coeff9.getName(), coeff9);

    horzCoeffs.put(coeff10.getName(), coeff10);
    horzCoeffs.put(coeff11.getName(), coeff11);
    horzCoeffs.put(coeff12.getName(), coeff12);
    horzCoeffs.put(coeff13.getName(), coeff13);
    horzCoeffs.put(coeff14.getName(), coeff14);
    horzCoeffs.put(coeff15.getName(), coeff15);
    horzCoeffs.put(coeff16.getName(), coeff16);
    horzCoeffs.put(coeff17.getName(), coeff17);
    horzCoeffs.put(coeff18.getName(), coeff18);
    horzCoeffs.put(coeff19.getName(), coeff19);

    horzCoeffs.put(coeff20.getName(), coeff20);
    horzCoeffs.put(coeff21.getName(), coeff21);
    horzCoeffs.put(coeff22.getName(), coeff22);
    horzCoeffs.put(coeff23.getName(), coeff23);
    horzCoeffs.put(coeff24.getName(), coeff24);
    horzCoeffs.put(coeff25.getName(), coeff25);
    horzCoeffs.put(coeff26.getName(), coeff26);
    horzCoeffs.put(coeff27.getName(), coeff27);
    horzCoeffs.put(coeff28.getName(), coeff28);
  }

  /**
   *  <b>Title:</b> BS_2003_AttenRelCoefficients<br>
   *  <b>Description:</b> This class encapsulates all the
   *  coefficients needed for the calculation.<br>
   *  <b>Copyright:</b> Copyright (c) 2001 <br>
   *  <b>Company:</b> <br>
   */

  class BS_2003_AttenRelCoefficients
      implements NamedObjectAPI {

    protected final static String C = "BS_2003_AttenRelCoefficients";
    protected final static boolean D = false;
    /** For serialization. */
    private static final long serialVersionUID = 1234567890987654399L;

    protected String name;
    protected double period = -1;
    protected double b1;
    protected double vRef;
    protected double c;
    protected double b2;
    protected double tau;
    protected double e1;
    protected double e3;

    /**
     *  Constructor for the BS_2003_AttenRelCoefficients object that sets all values at once
     *
     * @param  name  Description of the Parameter
     */
    public BS_2003_AttenRelCoefficients(String name, double period,
                                        double b1, double vRef, double c,
                                        double b2, double tau,
                                        double e1, double e3) {

      this.name = name;
      this.period = period;
      this.b1 = b1;
      this.vRef = vRef;
      this.c = c;
      this.b2 = b2;
      this.tau = tau;
      this.e1 = e1;
      this.e3 = e3;
    }

    /**
     *  Gets the name attribute
     *
     * @return    The name value
     */
    public String getName() {
      return name;
    }

    /**
     *  Debugging - prints out all cefficient names and values
     *
     * @return    Description of the Return Value
     */
    public String toString() {

      StringBuffer b = new StringBuffer();
      b.append(C);
      b.append("\n  Period = " + period);
      b.append("\n  b1 = " + b1);
      b.append("\n  vRef = " + vRef);
      b.append("\n  c = " + c);
      b.append("\n  b2 = " + b2);
      b.append("\n  tau = " + tau);
      b.append("\n  e1 = " + e1);
      b.append("\n e3 = " + e3);
      return b.toString();
    }
  }
}
