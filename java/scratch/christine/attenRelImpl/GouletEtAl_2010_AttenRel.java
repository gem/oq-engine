//package org.opensha.sha.imr.attenRelImpl;
package scratch.christine.attenRelImpl;


import java.util.Hashtable;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.IMRException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.Parameter;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <b>Title:</b> Goulet et al SiteSpecific_2010_AttenRel<p>
 *
 * <b>Description:</b> This implements the site effect models
 * developed by Goulet (to be published 2010) , applied
 * to the Campbell and Bozorgnia (2008) rock-site predictions. <p>
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
 * <LI>fltTypeParam - Style of faulting
 * <LI>isOnHangingWallParam - tells if site is directly over the rupture surface
 * <LI>componentParam - Component of shaking (only one)
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL><p>
 *
 * @author     Christine A. Goulet
 * @created    March, 2009
 * @version    1.0
 */


public class GouletEtAl_2010_AttenRel
    extends AttenuationRelationship implements ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI {

  // debugging stuff:
  private final static String C = "GouletEtAl_2010_AttenRel";
  private final static boolean D = false;
  public final static String NAME = "Goulet et al (2010)";
  public final static String SHORT_NAME = "GouletEtAl_2010";
  private static final long serialVersionUID = 1234567890987654355L;

  // warning constraint fields:
  protected final static Double VS30_WARN_MIN = new Double(50.0);
  protected final static Double VS30_WARN_MAX = new Double(760.0);
 
  protected CB_2008_AttenRel cb_2008_attenRel;
  /**
   * The current set of coefficients based on the selected intensityMeasure
   */
  protected GouletEtAl_2010_AttenRelCoefficients coeffs = null;
   
  //Intercept param
  private DoubleParameter AF_InterceptParam;
  public final static String AF_INTERCEPT_PARAM_NAME = "AF Intercept";
  public final static String AF_INTERCEPT_PARAM_INFO = 
	  "Intercept of the median regression model for the ground response analyses";
  private DoubleConstraint AF_InterceptparamConstraint = new DoubleConstraint(-4,4);
  public final static double AF_INTERCEPT_PARAM_DEFAULT = 0;
  
  //Slope Param
  protected DoubleParameter AF_SlopeParam;
  public final static String AF_SLOPE_PARAM_NAME = "AF Slope";
  public final static String AF_SLOPE_PARAM_INFO = 
	  "Slope of the median regression model for the ground response analyses";
  private DoubleConstraint AF_slopeParamConstraint = new DoubleConstraint(-4,1);
  public final static double AF_SLOPE_PARAM_DEFAULT = 0;
  
  //Additive refeerence acceleration param
  protected DoubleParameter AF_AddRefAccParam;
  public final static String AF_ADDITIVE_REF_ACCELERATION_PARAM_NAME = "AF Add. Ref. Acceleration";
  public final static String AF_ADDITIVE_REF_ACCELERATION_PARAM_INFO = 
	  "Additive reference acceleration of the median regression model for the ground response " +
	  "analyses. This parameter improves the linear model fit for low Sa(rock) / PGA(rock)" +
	  "values and leads to more relaistic predictons than quadratic models";
  private DoubleConstraint AFaddRefAccParamConstraint = new DoubleConstraint(0,10);
  public final static double AF_ADDITIVE_REF_ACCERLATION_DEFAULT = 0.03;
  
  //Std. Dev AF param
  protected DoubleParameter AF_StdDevParam;
  public final static String AF_STD_DEV_PARAM_NAME = "Std. Dev. ln(AF)";
  public final static String AF_STD_DEV_PARAM_INFO = 
	  "Standard Deviation of the amplification factor from the ground response analyses" +
	  " regression model";
  private DoubleConstraint AF_StdDevParamConstraint = new DoubleConstraint(0,1.0);
  public final static double AF_STD_DEV_DEFAULT = 0.3;
  
   
  /**
   *  Hashtable of coefficients for the supported intensityMeasures
   */
  protected Hashtable horzCoeffs = new Hashtable();

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

   public GouletEtAl_2010_AttenRel(ParameterChangeWarningListener warningListener) {

    super();

    this.warningListener = warningListener;

    cb_2008_attenRel = new CB_2008_AttenRel(warningListener);

    // overide local params with those in cb_2008_attenRel
    this.sigmaTruncTypeParam = (SigmaTruncTypeParam) cb_2008_attenRel.getParameter(
    		SigmaTruncTypeParam.NAME);
    this.sigmaTruncLevelParam = (SigmaTruncLevelParam) cb_2008_attenRel.getParameter(
    		SigmaTruncLevelParam.NAME);
    this.exceedProbParam = (DoubleParameter) cb_2008_attenRel.getParameter(
        cb_2008_attenRel.EXCEED_PROB_NAME);
    this.stdDevTypeParam = (StdDevTypeParam) cb_2008_attenRel.getParameter(
    		StdDevTypeParam.NAME);
    this.saPeriodParam = (PeriodParam) cb_2008_attenRel.getParameter(
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
    this.cb_2008_attenRel.setEqkRupture(eqkRupture);
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
	  this.site = site;
	  // set the location in cb_2008_attenRel
	  cb_2008_attenRel.setSiteLocation(site.getLocation());
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
      coeffs = (GouletEtAl_2010_AttenRelCoefficients) horzCoeffs.get(key.toString());
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

    double cbRockSA, lnAF;

    // get AS-1997 SA for rock
    cb_2008_attenRel.setIntensityMeasure(im);
    cbRockSA = cb_2008_attenRel.getMean();
    
        // get the amp factor
    double aVal = ((Double)AF_InterceptParam.getValue()).doubleValue();
    double bVal = ((Double)AF_SlopeParam.getValue()).doubleValue();
    double cVal = ((Double)AF_AddRefAccParam.getValue()).doubleValue();
    lnAF = aVal+bVal*Math.log(Math.exp(cbRockSA)+cVal);   

    // return the result
    return lnAF + cbRockSA;
  }


  /**
   * Returns the Std Dev.
   */
  public double getStdDev(){
	  
	  String stdDevType = stdDevTypeParam.getValue().toString();
	  if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) { // "None (zero)"
		  return 0;
	  }
	  updateCoefficients();
	  return getStdDevForCG();
  }
  
  
  /**
   * @return    The stdDev value for Goulet et al (2010) Site Correction Model
   */
  private double getStdDevForCG(){
	  cb_2008_attenRel.setIntensityMeasure(im);
	  double cbRockSA;
	  cbRockSA = cb_2008_attenRel.getMean();
	  double bVal = ((Double)AF_SlopeParam.getValue()).doubleValue();
      double cVal = ((Double)AF_AddRefAccParam.getValue()).doubleValue();
	  double stdDevAF = ((Double)this.AF_StdDevParam.getValue()).doubleValue();
	  double tau = coeffs.tau;
	  double cbRockStdDev = cb_2008_attenRel.getStdDev();
//	  double stdDev = Math.pow(bVal+1, 2)*(Math.pow(cbRockStdDev, 2)-Math.pow(tau,2))+Math.pow(stdDevAF, 2)+Math.pow(tau, 2);
	  double stdDev = Math.pow(bVal*Math.exp(cbRockSA)/(Math.exp(cbRockSA)+cVal)+1, 2)*(Math.pow(cbRockStdDev, 2)-Math.pow(tau,2))+Math.pow(stdDevAF, 2)+Math.pow(tau, 2);;
	  return Math.sqrt(stdDev);
  }

 
  public void setParamDefaults() {

	    //((ParameterAPI)this.iml).setValue( IML_DEFAULT );
	    AF_AddRefAccParam.setValue(this.AF_ADDITIVE_REF_ACCERLATION_DEFAULT);
	    AF_InterceptParam.setValue(this.AF_INTERCEPT_PARAM_DEFAULT);
	    AF_SlopeParam.setValue(this.AF_SLOPE_PARAM_DEFAULT);
	    AF_StdDevParam.setValue(this.AF_STD_DEV_DEFAULT);
	    cb_2008_attenRel.setParamDefaults();
	    // re-set the site type to rock and component to ave horz
//	    cb_2008_attenRel.getParameter(cb_2008_attenRel.SITE_TYPE_NAME).setValue(
//	        cb_2008_attenRel.SITE_TYPE_ROCK);
//	    cb_2008_attenRel.getParameter(cb_2008_attenRel.COMPONENT_NAME).setValue(
//	        cb_2008_attenRel.COMPONENT_AVE_HORZ);
	    // re-set the site type to rock and component to ave horz
	    double rockVS = 1100.00;
	    cb_2008_attenRel.getParameter(Vs30_Param.NAME).setValue(rockVS);

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
    ListIterator it = cb_2008_attenRel.getMeanIndependentParamsIterator();
//    String ignoreStr1 = cb_2008_attenRel.SITE_TYPE_NAME;
//    String ignoreStr2 = cb_2008_attenRel.COMPONENT_NAME;
    while (it.hasNext()) {
      Parameter param = (Parameter) it.next();
//      if (!ignoreStr1.equals(param.getName()) &&
//          !ignoreStr2.equals(param.getName())) {
        meanIndependentParams.addParameter(param);
//      }
    }
    meanIndependentParams.addParameter(AF_AddRefAccParam);
    meanIndependentParams.addParameter(AF_InterceptParam);
    meanIndependentParams.addParameter(AF_SlopeParam);
    meanIndependentParams.addParameter(AF_StdDevParam);
 //   meanIndependentParams.addParameter(componentParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    
    it = cb_2008_attenRel.getStdDevIndependentParamsIterator();
    while (it.hasNext()) {
      Parameter param = (Parameter) it.next();
//      if (!ignoreStr1.equals(param.getName()) &&
//          !ignoreStr2.equals(param.getName())) {
        stdDevIndependentParams.addParameter(param);
//      }
    }
    
    stdDevIndependentParams.addParameter(AF_AddRefAccParam);
    stdDevIndependentParams.addParameter(AF_InterceptParam);
    stdDevIndependentParams.addParameter(AF_SlopeParam);
    stdDevIndependentParams.addParameter(AF_StdDevParam);
  //  stdDevIndependentParams.addParameter(componentParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    it = cb_2008_attenRel.getExceedProbIndependentParamsIterator();
    while (it.hasNext()) {
      Parameter param = (Parameter) it.next();
//      if (!ignoreStr1.equals(param.getName()) &&
//          !ignoreStr2.equals(param.getName())) {
        exceedProbIndependentParams.addParameter(param);
//      }
    }
    
    exceedProbIndependentParams.addParameter(AF_AddRefAccParam);
    exceedProbIndependentParams.addParameter(AF_InterceptParam);
    exceedProbIndependentParams.addParameter(AF_SlopeParam);
    exceedProbIndependentParams.addParameter(AF_StdDevParam);
//    exceedProbIndependentParams.addParameter(componentParam);

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
 
    //make the AF intercept parameter
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
    
     // add it to the siteParams list:
    siteParams.clear();
    siteParams.addParameter(AF_AddRefAccParam);
    siteParams.addParameter(AF_InterceptParam);
    siteParams.addParameter(AF_SlopeParam);
    siteParams.addParameter(AF_StdDevParam);

    ListIterator it = cb_2008_attenRel.getSiteParamsIterator();
	  while (it.hasNext()) {
		  siteParams.addParameter( (Parameter) it.next());
	  }


  }

  /**
   *  Creates the two Potential Earthquake parameters (magParam and
   *  fltTypeParam) and adds them to the eqkRuptureParams
   *  list. Makes the parameters noneditable.
   */
  protected void initEqkRuptureParams() {

    eqkRuptureParams.clear();
    ListIterator it = cb_2008_attenRel.getEqkRuptureParamsIterator();
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
    ListIterator it = cb_2008_attenRel.getPropagationEffectParamsIterator();
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
    Iterator it = cb_2008_attenRel.getSupportedIntensityMeasuresIterator();
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
    Iterator it = cb_2008_attenRel.getOtherParamsIterator();
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
   *  The values below are for Tau from CB 2008 NGA Earthquake Spectra paper.
   */
  protected void initCoefficients() {

    String S = C + ": initCoefficients():";
    if (D) {
      System.out.println(S + "Starting");
    }

    horzCoeffs.clear();

    GouletEtAl_2010_AttenRelCoefficients coeff = new GouletEtAl_2010_AttenRelCoefficients(
        PGA_Param.NAME,
        0.0, 0.219);
    GouletEtAl_2010_AttenRelCoefficients coeff0 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.01")).doubleValue(),
        0.01, 0.219);
    GouletEtAl_2010_AttenRelCoefficients coeff1 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.02")).doubleValue(),
        0.02, 0.219);
    GouletEtAl_2010_AttenRelCoefficients coeff2 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.03")).doubleValue(),
        0.03, 0.235);
    GouletEtAl_2010_AttenRelCoefficients coeff3 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.05")).doubleValue(),
        0.05, 0.258);
    GouletEtAl_2010_AttenRelCoefficients coeff4 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.075")).doubleValue(),
        0.075, 0.292);
    GouletEtAl_2010_AttenRelCoefficients coeff5 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.1")).doubleValue(),
        0.10, 0.286);
    GouletEtAl_2010_AttenRelCoefficients coeff6 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.15")).doubleValue(),
        0.15, 0.280);
    GouletEtAl_2010_AttenRelCoefficients coeff7 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.2")).doubleValue(),
        0.20, 0.249);
    GouletEtAl_2010_AttenRelCoefficients coeff8 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.25")).doubleValue(),
        0.25, 0.240);
    GouletEtAl_2010_AttenRelCoefficients coeff9 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.3")).doubleValue(),
        0.30, 0.215);
    GouletEtAl_2010_AttenRelCoefficients coeff10 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.4")).doubleValue(),
        0.40, 0.217);
    GouletEtAl_2010_AttenRelCoefficients coeff11 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.5")).doubleValue(),
        0.50, 0.214);
    GouletEtAl_2010_AttenRelCoefficients coeff12 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.75")).doubleValue(),
        0.75, 0.227);
    GouletEtAl_2010_AttenRelCoefficients coeff13 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("1.0")).doubleValue(),
        1.00, 0.255);
    GouletEtAl_2010_AttenRelCoefficients coeff14 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("1.5")).doubleValue(),
        1.50, 0.296);
    GouletEtAl_2010_AttenRelCoefficients coeff15 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("2.0")).doubleValue(),
        2.00, 0.296);
    GouletEtAl_2010_AttenRelCoefficients coeff16 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("3.0")).doubleValue(),
        3.00, 0.326);
    GouletEtAl_2010_AttenRelCoefficients coeff17 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("4.0")).doubleValue(),
        4.00, 0.297);
    GouletEtAl_2010_AttenRelCoefficients coeff18 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("5.0")).doubleValue(),
        5.00, 0.359);
    GouletEtAl_2010_AttenRelCoefficients coeff19 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("7.5")).doubleValue(),
        7.50, 0.428);
    GouletEtAl_2010_AttenRelCoefficients coeff20 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("10.0")).doubleValue(),
        10.00, 0.485);
    // add zero-period case; same as 0.01 sec.
    GouletEtAl_2010_AttenRelCoefficients coeff21 = new GouletEtAl_2010_AttenRelCoefficients(
        SA_Param.NAME + "/" + (new Double("0.0")).doubleValue(),
        0.00, 0.219);

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
  }

  /**
   *  <b>Title:</b> GouletEtAl_2010_AttenRelCoefficients<br>
   *  <b>Description:</b> This class encapsulates all the
   *  coefficients needed for the calculation.<br>
   *  <b>Copyright:</b> Copyright (c) 2001 <br>
   *  <b>Company:</b> <br>
   */

  class GouletEtAl_2010_AttenRelCoefficients
      implements NamedObjectAPI {

    protected final static String C = "GouletEtAl_2010_AttenRelCoefficients";
    protected final static boolean D = false;
    /** For serialization. */
    private static final long serialVersionUID = 1234567890987654399L;

    protected String name;
    protected double period = -1;
    protected double tau;

    /**
     *  Constructor for the GouletEtAl_2010_AttenRelCoefficients object that sets all values at once
     *
     * @param  name  Description of the Parameter
     */
    public GouletEtAl_2010_AttenRelCoefficients(String name, double period,
            double tau) {
    	
        this.name = name;
        this.period = period;
        this.tau = tau;
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
     *  Debugging - prints out all coefficient names and values
     *
     * @return    Description of the Return Value
     */
    
    
    public String toString() {
        StringBuffer b = new StringBuffer();
        b.append(C);
        b.append("\n  Period = " + period);
        b.append("\n  tau = " + tau);
        return b.toString();
      }
    }
}
