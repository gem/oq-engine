package scratch.jennie.attenRelImpl;

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
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

/**
 * <b>Title:</b> AS_1997_SiteSpecific_AttenRel<p>
 *
 * <b>Description:</b> This applies a site specific site effect model
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
 * @author     Jennie Watson-Lamprey
 * @created    june, 2008
 * @version    1.0
 */


public class AS_1997_SiteSpecific_AttenRel
    extends AttenuationRelationship implements ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI {

  // debugging stuff:
  private final static String C = "AS_1997_SiteSpecific_AttenRel";
  private final static boolean D = false;
  public final static String NAME = "Abrahamson and Silva (1997) Site Specific";
  public final static String SHORT_NAME = "AS1997SS";
  private static final long serialVersionUID = 1234567890987654355L;



  // warning constraint fields:
  protected final static Double VS30_WARN_MIN = new Double(50.0);
  protected final static Double VS30_WARN_MAX = new Double(2500.0);

 
  protected AS_1997_AttenRel as_1997_attenRel;
  
  /**
   * The current set of coefficients based on the selected intensityMeasure
   */
  
//  private double mag;
  
  //Functional Form
  private StringParameter AF_FuncForm;
  public final static String AF_FuncForm_NAME = "AF Functional Form";
  public final static String AF_FuncForm_INFO = 
	  "Intercept of the median regression model for the ground response analyses";
//  private DoubleConstraint AF_InterceptparamConstraint = new DoubleConstraint(-2,2);
  public final static String AF_FuncForm_DEFAULT = "lnAF = a + b*ln(SaRock+c) + d*(Mag-6) +e*ln(Rup/20)";
  
  //Intercept param
  private DoubleParameter AF_InterceptParam;
  public final static String AF_INTERCEPT_PARAM_NAME = "AF Intercept (a)";
  public final static String AF_INTERCEPT_PARAM_INFO = 
	  "Intercept of the median regression model for the ground response analyses";
  private DoubleConstraint AF_InterceptparamConstraint = new DoubleConstraint(-2,2);
  public final static double AF_INTERCEPT_PARAM_DEFAULT = 0;
  
  //Slope Param
  protected DoubleParameter AF_SlopeParam;
  public final static String AF_SLOPE_PARAM_NAME = "AF Slope (b)";
  public final static String AF_SLOPE_PARAM_INFO = 
	  "Slope of the median regression model for the ground response analyses";
  private DoubleConstraint AF_slopeParamConstraint = new DoubleConstraint(-1,1);
  public final static double AF_SLOPE_PARAM_DEFAULT = 0;
  
  //Additive reference acceleration param
  protected DoubleParameter AF_AddRefAccParam;
  public final static String AF_ADDITIVE_REF_ACCELERATION_PARAM_NAME = "AF Add. Ref. Acceleration (c)";
  public final static String AF_ADDITIVE_REF_ACCELERATION_PARAM_INFO = 
	  "Additive reference acceleration of the median regression model for the ground response " +
	  "analyses. This parameter improves the linear model fit for low Sa(rock) / PGA(rock)" +
	  "values and leads to more relaistic predictons than quadratic models";
  private DoubleConstraint AFaddRefAccParamConstraint = new DoubleConstraint(0,0.5);
  public final static double AF_ADDITIVE_REF_ACCERLATION_DEFAULT = 0.03;
  
  //Mag reference param
  protected DoubleParameter AF_MagParam;
  public final static String AF_MagPARAM_NAME = "AF Magnitude (d)";
  public final static String AF_MagPARAM_INFO = 
	  "Slope of the regression for magnitude";
  private DoubleConstraint AFMagParamConstraint = new DoubleConstraint(-4,4);
  public final static double AF_MagParam_DEFAULT = 0.0;
  
  //Rup reference param
  protected DoubleParameter AF_RupParam;
  public final static String AF_RupPARAM_NAME = "AF Ruture Distance (e)";
  public final static String AF_RupPARAM_INFO = 
	  "Slope of the regression for rupture distance";
  private DoubleConstraint AFRupParamConstraint = new DoubleConstraint(-4,4);
  public final static double AF_RupParam_DEFAULT = 0.0;
  
  
  //Std. Dev AF param
  protected DoubleParameter AF_StdDevParam;
  public final static String AF_STD_DEV_PARAM_NAME = "Std. Dev. AF";
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

   public AS_1997_SiteSpecific_AttenRel(ParameterChangeWarningListener warningListener) {

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

//    initCoefficients();
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

	  AF_FuncForm.setValue(AF_FuncForm_DEFAULT);
	  AF_InterceptParam.setValue((Double)site.getParameter(AF_INTERCEPT_PARAM_NAME).getValue());
	  AF_AddRefAccParam.setValue((Double)site.getParameter(AF_ADDITIVE_REF_ACCELERATION_PARAM_NAME).getValue());
	  AF_SlopeParam.setValue((Double)site.getParameter(AF_SLOPE_PARAM_NAME).getValue());
	  AF_MagParam.setValue((Double)site.getParameter(AF_MagPARAM_NAME).getValue());
	  AF_RupParam.setValue((Double)site.getParameter(AF_RupPARAM_NAME).getValue());
	  AF_StdDevParam.setValue((Double)site.getParameter(AF_STD_DEV_PARAM_NAME).getValue());  
	  this.site = site;
	  // set the location in as_1997_attenRel
	  as_1997_attenRel.setSiteLocation(site.getLocation());
  }

  /**
   * Calculates the mean
   * @return    The mean value
   */
  public double getMean() throws IMRException {

    double asRockSA, lnAF, magTest;


    // get AS-1997 SA for rock
    as_1997_attenRel.setIntensityMeasure(im);
    asRockSA = as_1997_attenRel.getMean();
    double  mag = ( (Double) magParam.getValue()).doubleValue();
    double dist = ( (Double) distanceRupParam.getValue()).doubleValue();
//    mag = ( (Double) as_1997_attenRel.getEqkRupture().getMag()).doubleValue();
//    magTest = as_1997_attenRel.EqkRupture().getMag();
//    magTest = as_1997_attenRel.
//    magTest = as_
    
    // get the amp factor
    double aVal = ((Double)AF_InterceptParam.getValue()).doubleValue();
    double bVal = ((Double)AF_SlopeParam.getValue()).doubleValue();
    double cVal = ((Double)AF_AddRefAccParam.getValue()).doubleValue();
    double mVal = ((Double)AF_MagParam.getValue()).doubleValue();
    double rVal = ((Double)AF_RupParam.getValue()).doubleValue();
    lnAF = aVal+bVal*Math.log(Math.exp(asRockSA)+cVal)+mVal*(mag-6)+rVal*Math.log(dist/20);   

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
	  return getStdDevForGoulet();
  }
  
  
  /**
   * @return    The stdDev value for Bazzurro and Cornell (2004) Site Correction Model
   */
  private double getStdDevForBC(){
	  double bVal = ((Double)AF_SlopeParam.getValue()).doubleValue();
	  double stdDevAF = ((Double)this.AF_StdDevParam.getValue()).doubleValue();
	  as_1997_attenRel.setIntensityMeasure(im);
	  double asRockStdDev = as_1997_attenRel.getStdDev();
	  double stdDev = Math.pow(bVal+1, 2)*Math.pow(asRockStdDev, 2)+Math.pow(stdDevAF, 2);
	  return Math.sqrt(stdDev);
  }
  private double getStdDevForGoulet(){
	  double bVal = ((Double)AF_SlopeParam.getValue()).doubleValue();
	  double cVal = ((Double)this.AF_AddRefAccParam.getValue()).doubleValue();
	  double stdDevAF = ((Double)this.AF_StdDevParam.getValue()).doubleValue();
//	  double tau = coeffs.tau;
	  as_1997_attenRel.setIntensityMeasure(im);
	  double asRockMean = as_1997_attenRel.getMean();
	  double asRockStdDev = as_1997_attenRel.getStdDev();
//	  double stdDev = Math.pow((bVal*asRockMean)/(asRockMean+cVal)+1, 2)*
//	                  (Math.pow(asRockStdDev,2)-Math.pow(tau, 2))+Math.pow(stdDevAF,2)+Math.pow(tau,2);
	  double stdDev = Math.pow((bVal*asRockMean)/(asRockMean+cVal)+1, 2)*(Math.pow(asRockStdDev,2))+Math.pow(stdDevAF,2);
	  return Math.sqrt(stdDev);
  }
 
  public void setParamDefaults() {

	    //((ParameterAPI)this.iml).setValue( IML_DEFAULT );
//	    AF_FuncForm.setValue(this.AF_FuncForm_DEFAULT);
	    AF_AddRefAccParam.setValue(this.AF_ADDITIVE_REF_ACCERLATION_DEFAULT);
	    AF_InterceptParam.setValue(this.AF_INTERCEPT_PARAM_DEFAULT);
	    AF_SlopeParam.setValue(this.AF_SLOPE_PARAM_DEFAULT);
	    AF_MagParam.setValue(this.AF_MagParam_DEFAULT);
	    AF_RupParam.setValue(this.AF_RupParam_DEFAULT);
	    AF_StdDevParam.setValue(this.AF_STD_DEV_DEFAULT);
	    as_1997_attenRel.setParamDefaults();
	    // re-set the site type to rock and component to ave horz
	    as_1997_attenRel.getParameter(as_1997_attenRel.SITE_TYPE_NAME).setValue(
	        as_1997_attenRel.SITE_TYPE_ROCK);
	    as_1997_attenRel.getParameter(ComponentParam.NAME).setValue(
	        ComponentParam.COMPONENT_AVE_HORZ);
	    magParam.setValueAsDefault();
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
    meanIndependentParams.addParameter(AF_FuncForm);
    meanIndependentParams.addParameter(AF_AddRefAccParam);
    meanIndependentParams.addParameter(AF_InterceptParam);
    meanIndependentParams.addParameter(AF_SlopeParam);
    meanIndependentParams.addParameter(AF_MagParam);
    meanIndependentParams.addParameter(AF_RupParam);
    meanIndependentParams.addParameter(AF_StdDevParam);
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
    
    stdDevIndependentParams.addParameter(AF_FuncForm);
    stdDevIndependentParams.addParameter(AF_AddRefAccParam);
//    stdDevIndependentParams.addParameter(AF_InterceptParam);
    stdDevIndependentParams.addParameter(AF_SlopeParam);
    stdDevIndependentParams.addParameter(AF_StdDevParam);
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
    
    exceedProbIndependentParams.addParameter(AF_FuncForm);
    exceedProbIndependentParams.addParameter(AF_AddRefAccParam);
    exceedProbIndependentParams.addParameter(AF_InterceptParam);
    exceedProbIndependentParams.addParameter(AF_SlopeParam);
    exceedProbIndependentParams.addParameter(AF_MagParam);
    exceedProbIndependentParams.addParameter(AF_RupParam);
    exceedProbIndependentParams.addParameter(AF_StdDevParam);
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

    //make the AF functional form parameter
    StringConstraint constraint = new StringConstraint();
    constraint.addString(AF_FuncForm_DEFAULT);
    constraint.setNonEditable();
    this.AF_FuncForm = new StringParameter(this.AF_FuncForm_NAME, constraint,
    		this.AF_FuncForm_DEFAULT);
    AF_FuncForm.setInfo(ComponentParam.INFO);
    AF_FuncForm.setNonEditable();
    
    //make the AF intercept parameter
    this.AF_InterceptParam = new DoubleParameter(this.AF_INTERCEPT_PARAM_NAME,
    		AF_InterceptparamConstraint,this.AF_INTERCEPT_PARAM_DEFAULT);
    AF_InterceptParam.setInfo(this.AF_INTERCEPT_PARAM_INFO);
    
    //make the AF slope parameter
    this.AF_SlopeParam = new DoubleParameter(this.AF_SLOPE_PARAM_NAME,
    		this.AF_slopeParamConstraint,this.AF_SLOPE_PARAM_DEFAULT);
    AF_SlopeParam.setInfo(this.AF_SLOPE_PARAM_INFO);
    
    //make theb AF Additive Reference Parameter
    this.AF_AddRefAccParam = new DoubleParameter(this.AF_ADDITIVE_REF_ACCELERATION_PARAM_NAME,
    		this.AFaddRefAccParamConstraint,this.AF_ADDITIVE_REF_ACCERLATION_DEFAULT);
    AF_AddRefAccParam.setInfo(this.AF_ADDITIVE_REF_ACCELERATION_PARAM_INFO);

    //make the AF Mag Parameter
    this.AF_MagParam = new DoubleParameter(this.AF_MagPARAM_NAME,
    		this.AFMagParamConstraint,this.AF_MagParam_DEFAULT);
    AF_MagParam.setInfo(this.AF_MagPARAM_INFO);

    //make the AF Rup Parameter
    this.AF_RupParam = new DoubleParameter(this.AF_RupPARAM_NAME,
    		this.AFRupParamConstraint,this.AF_RupParam_DEFAULT);
    AF_RupParam.setInfo(this.AF_RupPARAM_INFO);
    
    //make the AF Std. Dev.
    this.AF_StdDevParam = new DoubleParameter(this.AF_STD_DEV_PARAM_NAME,
    		this.AF_StdDevParamConstraint,this.AF_STD_DEV_DEFAULT);
    
    AF_StdDevParam.setInfo(this.AF_STD_DEV_PARAM_INFO);
    
     // add it to the siteParams list:
    siteParams.clear();
    siteParams.addParameter(AF_FuncForm);
    siteParams.addParameter(AF_AddRefAccParam);
    siteParams.addParameter(AF_InterceptParam);
    siteParams.addParameter(AF_SlopeParam);
    siteParams.addParameter(AF_MagParam);
    siteParams.addParameter(AF_RupParam);
    siteParams.addParameter(AF_StdDevParam);


  }

  /**
   *  Creates the two Potential Earthquake parameters (magParam and
   *  fltTypeParam) and adds them to the eqkRuptureParams
   *  list. Makes the parameters noneditable.
   */
  protected void initEqkRuptureParams() {

	  // Create magParam
	  //super.initEqkRuptureParams();

	  magParam = (MagParam) as_1997_attenRel.getParameter(magParam.NAME);

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
    // this is a pointer to that in as_1997_attenRel for local access 
    distanceRupParam = (DistanceRupParameter) as_1997_attenRel.getParameter(DistanceRupParameter.NAME);

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
    /**
     *  Gets the name attribute
     *
     * @return    The name value
     */



}
