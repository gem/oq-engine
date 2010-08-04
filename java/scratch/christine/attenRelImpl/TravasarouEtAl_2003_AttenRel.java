package scratch.christine.attenRelImpl;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.IMRException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.IA_Param;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

/**
 * <b>Title:</b>  TravasarouEtAl_2003_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship
 * developed by Travasarou et al. (2003) for Arias Intensity, as described in 
 * Earthquake Engng Struct. Dyn. 2003; 32:1133–1155 <p>
 *
 * Supported Intensity-Measure Parameters:<p>
 * <UL>
 * <LI>IaParam - Arias Intensity
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceRupParam - closest distance to surface projection of fault
 * <LI>siteTypeParam - Site class as defined as "SGS" in Travasarou et al. (2003), Table II (B, C or D).
 * <LI>fltTypeParam - Style of faulting
 * <LI>stdDevTypeParam - The type of standard deviation

 * </UL></p>
 * 
 *<p>
 *
 * Verification: 
 * 
 *</p>
 *
 *
 * @author     Christine Goulet
 * @created    August, 2009
 * @version    1.0
 */

public class TravasarouEtAl_2003_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI, ParameterChangeListener {

  // Debugging stuff
  private final static String C = "TravasarouEtAl_2003_AttenRel";
  private final static boolean D = false;
  public final static String SHORT_NAME = "TravasarouEtAl2003";
  private static final long serialVersionUID = 1234567890987654353L;

  // Name of IMR
  public final static String NAME = "Travasarou et al. (2003)";

  // URL Info String
  private final static String URL_INFO_STRING = "http://www.opensha.org/documentation/modelsImplemented/attenRel/T_2003.html";

  // Model coefficients:
  double c1= 2.800;
  double c2= -1.981;
  double c3= 20.72;
  double c4= -1.703;
  double h= 8.78;
  double s11= 0.454;
  double s12= 0.101;
  double s21= 0.479;
  double s22= 0.334;
  double f1= -0.166;
  double f2= 0.512;
  
  private HashMap indexFromPerHashMap;
 
   
  private double rrup, mag, f_rv, f_nm, s_c, s_d;
  private IA_Param iaParam;
  double median;
// TODO add stddevtypes in the code
//  private String stdDevType;
  private boolean parameterChange;
  String fltType, siteType;
  
// CG commented below 2 009-08-13 - not in BA08!!?
//	private PropagationEffect propagationEffect;

  
 //CG Need to change mag warnings to min 4.7, max=7.6, as per Travasaou et al's paper 
  protected final static Double MAG_WARN_MIN = new Double(4.0);
  protected final static Double MAG_WARN_MAX = new Double(8.5);
  //CG Need to change Rrup warning min value to 0.1 km, as per Travasaou et al's paper 
  protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_RUP_WARN_MAX = new Double(200.0);
//  protected final static Double PGA_PARAM_MAX = new Double(100.0);


  /**
   * Style of faulting option
   */
  public final static String FLT_TYPE_REVERSE = "Reverse/Rev. Oblique";
  public final static String FLT_TYPE_NORMAL = "Normal";
  public final static String FLT_TYPE_STRIKESLIP = "Strike-slip";
  public final static String FLT_TYPE_DEFAULT = FLT_TYPE_STRIKESLIP;

  /**
   * Site Type Parameter (B, C or D, See Table II in paper)
   */
  private StringParameter siteTypeParam = null;
  public final static String SITE_TYPE_NAME = "SGS Site Type";
  public final static String SITE_TYPE_INFO =
      "Site class (SGS) see Table II of Travasarou et al.";
  public final static String SITE_TYPE_B = "SGS Class B";
  public final static String SITE_TYPE_C = "SGS Class C";
  public final static String SITE_TYPE_D = "SGS Class D";
  public final static String SITE_TYPE_DEFAULT = SITE_TYPE_C;
  
  private final static String IA_PARAM_NAME = "IA";
  private final static String IA_PARAM_UNITS = "m/s";
  private final static String IA_PARAM_INFO = "Arias Intensity";


  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  
  /**
   * SiteTypeParam, a StringParameter for representing different
   * soil types. The default must also be specified in the constructor.
   * See constructors for info on editability and default values.
   */

  private class SiteTypeParam extends StringParameter {

  	private final static String NAME = "Site Type";
  	private final static String INFO = "SGS Site Category";

  	/**
  	 * This sets the parameter as non-editable
  	 * @param options
  	 * @param defaultValue
  	 */
  	private SiteTypeParam(StringConstraint options, String defaultValue) {
  		super(NAME, options);
  	    setInfo(INFO);
  	    setDefaultValue(defaultValue);
  	    this.setNonEditable();
  	}
  }
  
  /**
   * This constitutes the natural-log Arias Intensity intensity measure
   * parameter.  
   * See constructors for info on editability and default values.
   * @author goulet (aug 2009) - modified based on PGA_Param from field
   *
   */
//  private class IA_Param extends WarningDoubleParameter {
//
//  	/**
//  	 * This uses the supplied warning constraint and default (both in natural-log space).
//  	 * The parameter is left as non editable
//  	 * @param warningConstraint
//  	 * @param defaultIa
//  	 */
//  	private IA_Param(DoubleConstraint warningConstraint, double defaultIA) {
//  		super(IA_PARAM_NAME, new DoubleConstraint(IA_PARAM_MIN, IA_PARAM_MAX), IA_PARAM_UNITS);
//  		getConstraint().setNonEditable();
//  	    this.setInfo(IA_PARAM_INFO);
//  	    setWarningConstraint(warningConstraint);
//  	    setDefaultValue(defaultIA);
//  	    setNonEditable();
//  	}
//  	
//  	/**
//  	 * This uses the DEFAULT_WARN_MIN and DEFAULT_WARN_MAX fields to set the
//  	 * warning constraint, and sets the default as Math.log(1.0) (the natural
//  	 * log of 1.0).
//  	 * The parameter is left as non editable
//  	 */
//  	private IA_Param() {
//  		super(IA_PARAM_NAME, new DoubleConstraint(IA_PARAM_WARN_MIN, IA_PARAM_WARN_MAX), IA_PARAM_UNITS);
//  		getConstraint().setNonEditable();
//  	    setInfo(IA_PARAM_INFO);
//  	    DoubleConstraint warn2 = new DoubleConstraint(IA_PARAM_WARN_MIN, IA_PARAM_WARN_MAX);
//  	    warn2.setNonEditable();
//  	    setWarningConstraint(warn2);
//  	    setDefaultValue(Math.log(1.0));
//  	    setNonEditable();
//  	}
//  }

  
  
  /**
   *  This initializes several ParameterList objects.
   */
  public TravasarouEtAl_2003_AttenRel(ParameterChangeWarningListener
                                    warningListener) {
    super();

    this.warningListener = warningListener;

    initSupportedIntensityMeasureParams();
    indexFromPerHashMap = new HashMap();
    
    initEqkRuptureParams();
    initPropagationEffectParams();
    initSiteParams();
    initOtherParams();

    initIndependentParamLists(); // This must be called after the above
    initParameterEventListeners(); //add the change listeners to the parameters
    
  }

  /**
   *  This sets the eqkRupture related parameters (magParam)
   *  based on the eqkRupture passed in.
   *  The internally held eqkRupture object is also set as that
   *  passed in.  Warning constrains are ingored.
   *
   * @param  eqkRupture  The new eqkRupture value
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setEqkRupture(EqkRupture eqkRupture) throws InvalidRangeException {

    magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
    this.eqkRupture = eqkRupture;
    setPropagationEffectParams();

  }

  /**
   *  This sets the site-related parameter (siteTypeParam) based on what is in
   *  the Site object passed in (the Site object must have a parameter with
   *  the same name as that in siteTypeParam).  This also sets the internally held
   *  Site object as that passed in.
   *
   * @param  site             The new site object
   * @throws ParameterException Thrown if the Site object doesn't contain a value
   */
  public void setSite(Site site) throws ParameterException {

	    siteTypeParam.setValue((String)site.getParameter(SITE_TYPE_NAME).getValue());
	    this.site = site;
	    setPropagationEffectParams();

	  }

 
  /**
   * This sets the propagation-effect parameter (distanceRupParam) based on the 
   * current site and eqkRupture.
   */
  protected void setPropagationEffectParams() {

    if ( (this.site != null) && (this.eqkRupture != null)) {

      distanceRupParam.setValue(eqkRupture, site);
    }
  }

  /**
   * Calculates the mean of the exceedance probability distribution. <p>
   * @return    The mean value
   */
  public double getMean() {
	  String fltType, siteType;

	  try {
		  mag = ( (Double) magParam.getValue()).doubleValue();
		  rrup = ( (Double) distanceRupParam.getValue()).doubleValue();
		  fltType = fltTypeParam.getValue().toString();
		  siteType = siteTypeParam.getValue().toString();
	  }
	  catch (NullPointerException e) {
		  throw new IMRException(C + ": getMean(): " + ERR);
	  }


	  // check if distance is beyond the user specified max
	  if (rrup > USER_MAX_DISTANCE) {
		  return VERY_SMALL_MEAN;
	  }

	  if (fltType.equals(FLT_TYPE_NORMAL)) {
		  f_rv = 0 ;
		  f_nm = 1;
	  }
	  else if (fltType.equals(FLT_TYPE_REVERSE)) {
		  f_rv = 1;
		  f_nm = 0;
	  }
	  else {
		  f_rv = 0;
		  f_nm = 0;
	  }

	  if (siteType.equals(SITE_TYPE_B)) {
		  s_c = 0;
		  s_d = 0;
	  }
	  else if (siteType.equals(SITE_TYPE_C)) {
		  s_c = 1;
		  s_d = 0;
	  }
	  else {
		  s_c = 0;
		  s_d = 1;
	  }



	  double mean = getMean(rrup, mag, f_nm, f_rv, s_c, s_d);
	  //		System.out.println("Inside getMean mag = "+mag +", f_nm = "+f_nm+", f_rv=" +f_rv+ ", s_c=" +s_c+", s_d=" +s_d);


	  return mean;
  }

  /**
   * @return    The stdDev value
   */
  public double getStdDev() {
//	  String fltType, siteType;
	  
//	    try {
	        mag = ( (Double) magParam.getValue()).doubleValue();
	        rrup = ( (Double) distanceRupParam.getValue()).doubleValue();
	        fltType = fltTypeParam.getValue().toString();
	        siteType = siteTypeParam.getValue().toString();
//	    }
//	    catch (NullPointerException e) {
//	        throw new IMRException(C + ": getStdDev(): " + ERR);
//	    }

			  
			if (fltType.equals(FLT_TYPE_NORMAL)) {
				f_rv = 0 ;
				f_nm = 1;
			}
			else if (fltType.equals(FLT_TYPE_REVERSE)) {
				f_rv = 1;
				f_nm = 0;
			}
			else {
				f_rv = 0;
				f_nm = 0;
			}
			if (siteType.equals(SITE_TYPE_B)) {
				s_c = 0;
				s_d = 0;
			}
			else if (siteType.equals(SITE_TYPE_C)) {
				s_c = 1;
				s_d = 0;
			}
			else {
				s_c = 0;
				s_d = 1;
	     	}

	        
		  // check if distance is beyond the user specified max
		  if (rrup > USER_MAX_DISTANCE) {
			  return VERY_SMALL_MEAN;
		  }
		  double mean = getMean(rrup, mag, f_nm, f_rv, s_c, s_d);
//		  double median = Math.exp(mean);
//	    System.out.println("mag = "+mag +", rrup= " +rrup+ ", median= "+median);

    return getStdDev(rrup, mag, s_c, s_d, mean);

  }
  
  
  /**
   * Allows the user to set the default parameter values for the selected Attenuation
   * Relationship.
   */
  public void setParamDefaults() {

//    siteTypeParam.setValueAsDefault();
    siteTypeParam.setValue(SITE_TYPE_DEFAULT);
	fltTypeParam.setValueAsDefault();
    distanceRupParam.setValueAsDefault();
    magParam.setValueAsDefault();
//    pgaParam.setValueAsDefault();
    iaParam.setValueAsDefault();
    stdDevTypeParam.setValueAsDefault();

    siteType = (String) siteTypeParam.getValue();
    rrup = ( (Double) distanceRupParam.getValue()).doubleValue();
    mag = ( (Double) magParam.getValue()).doubleValue();
    fltType = (String) fltTypeParam.getValue();
//TODO add this    stdDevType = (String) stdDevTypeParam.getValue();
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
	    meanIndependentParams.addParameter(distanceRupParam);
	    meanIndependentParams.addParameter(siteTypeParam);
	    meanIndependentParams.addParameter(magParam);
	    meanIndependentParams.addParameter(fltTypeParam);

	    // params that the stdDev depends upon
	    stdDevIndependentParams.clear();
	    stdDevIndependentParams.addParameter(stdDevTypeParam);
	    stdDevIndependentParams.addParameterList(meanIndependentParams);

	    // params that the exceed. prob. depends upon
	    exceedProbIndependentParams.clear();
	    exceedProbIndependentParams.addParameterList(stdDevIndependentParams);
	    exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
	    exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

	    // params that the IML at exceed. prob. depends upon
	    imlAtExceedProbIndependentParams.addParameterList(
	        exceedProbIndependentParams);
	    imlAtExceedProbIndependentParams.addParameter(exceedProbParam);
  }

  
  /**
   * This sets the site and eqkRupture, and the related parameters,
   *  from the propEffect object passed in. Warning constrains are ingored.
   * @param propEffect
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setPropagationEffect(PropagationEffect propEffect) throws
      ParameterException, InvalidRangeException {

    this.site = propEffect.getSite();
    this.eqkRupture = propEffect.getEqkRupture();

    // set the local site-type param
    // CG not sure this line below is correct. Should it be:
    //     siteTypeParam.setValue((String)site.getParameter(siteTypeParam.NAME).getValue());

    siteTypeParam.setValue((String)site.getParameter(SITE_TYPE_NAME).getValue());

    // set the eqkRupture params
    magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));

    // set the distance param
    propEffect.setParamValue(distanceRupParam);

  }

  
  /**
   *  Creates the Site-Type parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {

    StringConstraint siteConstraint = new StringConstraint();
    siteConstraint.addString(SITE_TYPE_B);
    siteConstraint.addString(SITE_TYPE_C);
    siteConstraint.addString(SITE_TYPE_D);
    siteConstraint.setNonEditable();
    siteTypeParam = new StringParameter(SITE_TYPE_NAME, siteConstraint, null);
    siteTypeParam.setInfo(SITE_TYPE_INFO);
    siteTypeParam.setNonEditable();

    siteParams.clear();
    siteParams.addParameter(siteTypeParam);

  }

  /**
   *  Creates the two Potential Earthquake parameters (magParam and
   *  fltTypeParam) and adds them to the eqkRuptureParams
   *  list. Makes the parameters noneditable.
   */
  protected void initEqkRuptureParams() {

	magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);

    // Fault type parameter
    StringConstraint constraint = new StringConstraint();
    constraint.addString(FLT_TYPE_REVERSE);
    constraint.addString(FLT_TYPE_NORMAL);
    constraint.addString(FLT_TYPE_STRIKESLIP);
    constraint.setNonEditable();
    fltTypeParam = new FaultTypeParam(constraint,FLT_TYPE_STRIKESLIP);

    eqkRuptureParams.clear();
    eqkRuptureParams.addParameter(magParam);
    eqkRuptureParams.addParameter(fltTypeParam);
  }

  /**
   *  Creates the Propagation Effect parameters and adds them to the
   *  propagationEffectParams list. Makes the parameters noneditable.
   */
  protected void initPropagationEffectParams() {

    distanceRupParam = new DistanceRupParameter(0.0);
    distanceRupParam.addParameterChangeWarningListener(warningListener);
    DoubleConstraint warn = new DoubleConstraint(DISTANCE_RUP_WARN_MIN,
                                                 DISTANCE_RUP_WARN_MAX);
    warn.setNonEditable();
    distanceRupParam.setWarningConstraint(warn);
    distanceRupParam.setNonEditable();

    propagationEffectParams.addParameter(distanceRupParam);
  }


  /**
   *  Creates the supported IM parameter Ia. Makes the parameters noneditable.
   */
  protected void initSupportedIntensityMeasureParams() {

//		//  Create PGA Parameter (pgaParam):
//		pgaParam = new PGA_Param();
//		pgaParam.setNonEditable();
//
//	    // Add the warning listeners:
//	    pgaParam.addParameterChangeWarningListener(warningListener);
//
//	    // Put parameters in the supportedIMParams list:
//	    supportedIMParams.clear();
//	    supportedIMParams.addParameter(pgaParam);

		
  //  Create Ia Parameter (IaParam):
	iaParam = new IA_Param();
	iaParam.setNonEditable();

    // Add the warning listeners:
    iaParam.addParameterChangeWarningListener(warningListener);
   
    // Put parameters in the supportedIMParams list:
    supportedIMParams.clear();
    supportedIMParams.addParameter(iaParam);
   
  }
  
  /**
   *  Creates other Parameters that the mean or stdDev depends upon,
   *  such as the Component or StdDevType parameters.
   */
  protected void initOtherParams() {

	    // init other params defined in parent class
	    super.initOtherParams();

	    // the stdDevType Parameter
	    StringConstraint stdDevTypeConstraint = new StringConstraint();
	    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
	    stdDevTypeConstraint.setNonEditable();
	    stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);

	    // add these to the list
	    otherParams.addParameter(stdDevTypeParam);

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

  public double getMean(double rrup, double mag, double f_nm, double f_rv, double s_c, double s_d) {

	double lnY;
	
	lnY = c1 + c2*(mag-6.0) + c3*Math.log(mag/6.0)+c4*Math.log(Math.sqrt(rrup*rrup + h*h)) + (s11+s12*(mag-6.0))*s_c + (s21 + s22*(mag-6.0))*s_d +f1*f_nm + f2* f_rv;
	  
   System.out.println("lnY,"+lnY);

	
    return lnY;
  }

  public double getStdDev(double rrup, double mag, double s_c, double s_d, double mean) {
	  
	  double sig1, sig2, tau, sigma, sigmatot, median;
	  
	  median=Math.exp(mean);
	  
	  if(s_c == 0 && s_d == 0) {
		  sig1 = 1.18;
		  sig2 = 0.94;
	  } else if(s_c == 1 && s_d == 0) {
		  sig1 = 1.17;
		  sig2 = 0.93;
	  } else {
		  sig1 = 0.96;
		  sig2 = 0.73;
	  }
	  
/** 
 * Recommendation to limit tau for lower- and upper-bound mag; see text below Eq.15
 */
	  if(mag<4.7) {
		  tau=0.611;
	  }
	  else if (mag>7.6) {
		  tau = 0.475;
	  }
	  else {
	  tau = 0.611 - 0.047*(mag - 4.7);
	  }
	  
	  if(median<= 0.013) {
		  sigma = sig1;
	  } else if(median >= 0.125) {
		  sigma = sig2;
	  } else {
		  sigma = sig1-0.106*(Math.log(median)-Math.log(0.0132));
	  }

	  
	  sigmatot = Math.sqrt(sigma*sigma+tau*tau);
//	  sigmatot=0.6;
//	  System.out.println("sigmatot= "+sigmatot); 
	    System.out.println("sc,"+s_c+" sd=, "+s_d+", mag = "+mag +", rrup= " +rrup+ ", median= "+median+", mean= "+mean+", sigma="+sigma+" tau="+tau+" sigtot="+sigmatot);

	    	return sigmatot ;
  }

   
	/**
	 * This listens for parameter changes and updates the primitive parameters accordingly
	 * @param e ParameterChangeEvent
	 */
	public void parameterChange(ParameterChangeEvent e) {

		String pName = e.getParameterName();
		Object val = e.getNewValue();
		parameterChange = true;
		
		if (pName.equals(magParam.NAME)) {
			mag = ( (Double) val).doubleValue();
		}
//		else if (pName.equals(FaultTypeParam.NAME)) {
//			String fltType = (String)fltTypeParam.getValue();
//			if (fltType.equals(FLT_TYPE_NORMAL)) {
//				f_rv = 0 ;
//				f_nm = 1;
//			}
//			else if (fltType.equals(FLT_TYPE_REVERSE)) {
//				f_rv = 1;
//				f_nm = 0;
//			}
//			else {
//				f_rv = 0;
//				f_nm = 0;
//			}
//		}
//		else if (pName.equals(SiteTypeParam.NAME)) {
//			String siteType = (String)siteTypeParam.getValue();
//			if (siteType.equals(SITE_TYPE_B)) {
//				s_c = 0;
//				s_d = 0;
//			}
//			else if (siteType.equals(SITE_TYPE_C)) {
//				s_c = 1;
//				s_d = 0;
//			}
//			else {
//				s_c = 0;
//				s_d = 1;
//			}
//		}
		else if (pName.equals(DistanceRupParameter.NAME)) {
			rrup = ( (Double) val).doubleValue();
		}
	    else if (pName.equals(FaultTypeParam.NAME)) {
	        fltType = (String)fltTypeParam.getValue();
	    }
	    else if (pName.equals(SiteTypeParam.NAME)) {
	        siteType = (String)siteTypeParam.getValue();
	    }
//		else if (pName.equals(StdDevTypeParam.NAME)) {
//			stdDevType = (String) val;
//		}
	}
	
	/**
	   * Allows to reset the change listeners on the parameters
	   */
	  public void resetParameterEventListeners(){
	    distanceRupParam.removeParameterChangeListener(this);
	    siteTypeParam.removeParameterChangeListener(this);
	    fltTypeParam.removeParameterChangeListener(this);
	    magParam.removeParameterChangeListener(this);
	 
	    this.initParameterEventListeners();
	  }

	
	/**
	   * Adds the parameter change listeners. This allows to listen to when-ever the
	   * parameter is changed.
	   */
	  protected void initParameterEventListeners() {

	    distanceRupParam.addParameterChangeListener(this);
	    siteTypeParam.addParameterChangeListener(this);
	    fltTypeParam.addParameterChangeListener(this);
	    magParam.addParameterChangeListener(this);
	  }
	
 /**
 * This provides a URL where more info on this model can be obtained
 * @throws MalformedURLException if returned URL is not a valid URL.
 * @returns the URL to the AttenuationRelationship document on the Web.
 */
	  public URL getInfoURL() throws MalformedURLException{
		  return new URL(URL_INFO_STRING);
	  }

	  
}
 