package scratch.jennie.attenRelImpl;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;

/**
 * <b>Title:</b> ToroEtAl_1997_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship
 * developed by Toro et al. (1997) mid-continent, as described in SRL 1997 <p>
 *
 * Supported Intensity-Measure Parameters:<p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceJBParam - closest distance to surface projection of fault
 * <LI>vs30Param - 30-meter shear wave velocity (Toro et al. is hard rock (Vs30 = 6000 ft/sec, Silva (1996) is applied for other cases, this is not yet implemented)
 * </UL></p>
 * 
 *<p>
 *
 * Verification: 
 * 
 *</p>
 *
 *
 * @author     Jennie Watson-Lamprey
 * @created    May, 2008
 * @version    1.0
 */


public class ToroEtAl_1997_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI, ParameterChangeListener {


//		public static void main(String[] args) {
//			// TODO Auto-generated method stub
//			System.out.println("Hello world!");
//
//		}

	
	
  // Debugging stuff
  private final static String C = "ToroEtAl_1997_AttenRel";
  private final static boolean D = false;
  public final static String SHORT_NAME = "ToroEtAl1997";
  private static final long serialVersionUID = 1234567890987654353L;


  // Name of IMR
  public final static String NAME = "Toro et al. (1997)";

  
  // coefficients:
  // note that index 0 is for PGA 
  // the coefficients were originally for frequencies: 0.5, 1, 2.5, 5, 10, 25, 35, PGA
  
  double[] period= { 0, 0, 0.29, 0.04, 0.1, 0.2, 0.4, 1, 2};
  double[] c1= { 2.2, 2.2, 4, 3.68, 2.37, 1.73, 1.07, 0.09, -0.74};
  double[] c2= { 0.81, 0.81, 0.79, 0.8, 0.81, 0.84, 1.05, 1.42, 1.86};
  double[] c3= { 0, 0, 0, 0, 0, 0, -0.1, -0.2, -0.31};
  double[] c4= { 1.27, 1.27, 1.57, 1.46, 1.1, 0.98, 0.93, 0.9, 0.92};
  double[] c5= { 1.16, 1.16, 1.83, 1.77, 1.02, 0.66, 0.56, 0.49, 0.46};
  double[] c6= { 0.0021, 0.0021, 0.0008, 0.0013, 0.004, 0.0042, 0.0033, 0.0023, 0.0017};
  double[] c7= { 9.3, 9.3, 11.1, 10.5, 8.3, 7.5, 7.1, 6.8, 6.9};
  double[] m50= { 0.55, 0.55, 0.62, 0.62, 0.59, 0.6, 0.63, 0.63, 0.61};
  double[] m55= { 0.59, 0.59, 0.63, 0.63, 0.61, 0.64, 0.68, 0.64, 0.62};
  double[] m80= { 0.5, 0.5, 0.5, 0.5, 0.5, 0.56, 0.64, 0.67, 0.66};
  double[] r05= { 0.54, 0.54, 0.62, 0.57, 0.5, 0.45, 0.45, 0.45, 0.45};
  double[] r20= { 0.2, 0.2, 0.35, 0.29, 0.17, 0.12, 0.12, 0.12, 0.12};
  
  
 // double a1 = 0.03;  // g
  //double pgalow=0.06; // g
  //double a2 = 0.09; // g
  //double v1 = 180; // m/s
  //double v2 = 300; // m/s
  //double v_ref = 760; // m/s
  //double m_ref = 4.5;
  //double r_ref = 1; //km
  
  private HashMap indexFromPerHashMap;

  private int iper;
  private double vs30, rjb, mag;
  private boolean parameterChange;

  protected final static Double MAG_WARN_MIN = new Double(5);
  protected final static Double MAG_WARN_MAX = new Double(8);
  protected final static Double DISTANCE_JB_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_JB_WARN_MAX = new Double(500.0);
//  protected final static Double VS30_WARN_MIN = new Double(180.0);
//  protected final static Double VS30_WARN_MAX = new Double(2500.0);
  
  public final static String STD_DEV_TYPE_BASEMENT = "Basement rock";
 
  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   *  This initializes several ParameterList objects.
   */
  public ToroEtAl_1997_AttenRel(ParameterChangeWarningListener
                                    warningListener) {

    super();

    this.warningListener = warningListener;

    initSupportedIntensityMeasureParams();
    indexFromPerHashMap = new HashMap();
    for (int i = 0; i < period.length ; i++) {
      indexFromPerHashMap.put(new Double(period[i]), new Integer(i));
    }

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
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   */
  public void setSite(Site site) throws ParameterException {

//    vs30Param.setValue(site.getParameter(Vs30_Param.NAME).getValue());
    this.site = site;
    setPropagationEffectParams();

  }

  /**
   * 
   */
  protected void setPropagationEffectParams() {

    if ( (this.site != null) && (this.eqkRupture != null)) {

      distanceJBParam.setValue(eqkRupture, site);

    }
  }

  /**
   * This function returns the array index for the coeffs corresponding to the chosen IMT
   */
  protected void setCoeffIndex() throws ParameterException {

    // Check that parameter exists
    if (im == null) {
      throw new ParameterException(C +
                                   ": updateCoefficients(): " +
                                   "The Intensity Measusre Parameter has not been set yet, unable to process."
          );
    }
    
    iper = ( (Integer) indexFromPerHashMap.get(saPeriodParam.getValue())).intValue();
    

    parameterChange = true;
    intensityMeasureChanged = false;

  }

  /**
   * Calculates the mean of the exceedence probability distribution. <p>
   * @return    The mean value
   */
  public double getMean() {
	  
	  // check if distance is beyond the user specified max
	  if (rjb > USER_MAX_DISTANCE) {
		  return VERY_SMALL_MEAN;
	  }
	  
	  if (intensityMeasureChanged) {
		  setCoeffIndex(); // intensityMeasureChanged is set to false in this method
	  }
	  
	  return getMean(iper, vs30, rjb, mag);
  }

  /**
   * @return    The stdDev value
   */
  public double getStdDev() {
    if (intensityMeasureChanged) {
      setCoeffIndex();// intensityMeasureChanged is set to false in this method
    }
    return getStdDev(iper, rjb, mag);
  }
  
  
  /**
   * Allows the user to set the default parameter values for the selected Attenuation
   * Relationship.
   */
  public void setParamDefaults() {

 //   vs30Param.setValueAsDefault();
    magParam.setValueAsDefault();
    distanceJBParam.setValueAsDefault();
    saParam.setValueAsDefault();
    saPeriodParam.setValueAsDefault();
    saDampingParam.setValueAsDefault();
    pgaParam.setValueAsDefault();
    stdDevTypeParam.setValueAsDefault();

 //   vs30 = ( (Double) vs30Param.getValue()).doubleValue(); 
    rjb = ( (Double) distanceJBParam.getValue()).doubleValue();
    mag = ( (Double) magParam.getValue()).doubleValue();
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
    meanIndependentParams.addParameter(distanceJBParam);
//    meanIndependentParams.addParameter(vs30Param);
    meanIndependentParams.addParameter(magParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    stdDevIndependentParams.addParameter(distanceJBParam);
    stdDevIndependentParams.addParameter(magParam);
    stdDevIndependentParams.addParameter(stdDevTypeParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    exceedProbIndependentParams.addParameterList(meanIndependentParams);
    exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
    exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

    // params that the IML at exceed. prob. depends upon
    imlAtExceedProbIndependentParams.addParameterList(
        exceedProbIndependentParams);
    imlAtExceedProbIndependentParams.addParameter(exceedProbParam);
  }

  /**
   * This sets the site and eqkRu passed in. Warning constrains are ingored.
   * @param propEffect
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setPropagationEffect(PropagationEffect propEffect) throws
      InvalidRangeException, ParameterException {

    this.site = propEffect.getSite();
    this.eqkRupture = propEffect.getEqkRupture();

//    vs30Param.setValueIgnoreWarning(site.getParameter(Vs30_Param.NAME).getValue());

    magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));

    propEffect.setParamValue(distanceJBParam);
  }
  
  
  /**
   *  Creates the Site-Type parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {

    // create and add the warning constraint:
//    DoubleConstraint warn = new DoubleConstraint(VS30_WARN_MIN, VS30_WARN_MAX);
//    warn.setNonEditable();
//    vs30Param.setWarningConstraint(warn);
//    vs30Param.addParameterChangeWarningListener(warningListener);
//    vs30Param.setNonEditable();

//    siteParams.clear();
//    siteParams.addParameter(vs30Param);
  }

  /**
   *  Creates the one Earthquake parameters (magParam) and adds it to the eqkRuptureParams
   *  list. Makes the parameter noneditable.
   */
  protected void initEqkRuptureParams() {

	magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);

    eqkRuptureParams.clear();
    eqkRuptureParams.addParameter(magParam);
  }

  /**
   *  Creates the Propagation Effect parameters and adds them to the
   *  propagationEffectParams list. Makes the parameters noneditable.
   */
  protected void initPropagationEffectParams() {

	distanceJBParam = new DistanceJBParameter(0.0);
    distanceJBParam.addParameterChangeWarningListener(warningListener);
    DoubleConstraint warn = new DoubleConstraint(DISTANCE_JB_WARN_MIN,
                                                 DISTANCE_JB_WARN_MAX);
    warn.setNonEditable();
    distanceJBParam.setWarningConstraint(warn);
    distanceJBParam.setNonEditable();

    propagationEffectParams.addParameter(distanceJBParam);

  }

  /**
   *  Creates the two supported IM parameters (PGA and SA), as well as the
   *  independenParameters of SA (periodParam and dampingParam) and adds
   *  them to the supportedIMParams list. Makes the parameters noneditable.
   */
  protected void initSupportedIntensityMeasureParams() {

    // Create saParam:
    DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
    for (int i = 0; i < period.length; i++) {
      periodConstraint.addDouble(new Double(period[i]));
    }
    periodConstraint.setNonEditable();
	saPeriodParam = new PeriodParam(periodConstraint);
	saDampingParam = new DampingParam();
	saParam = new SA_Param(saPeriodParam, saDampingParam);
	saParam.setNonEditable();

	//  Create PGA Parameter (pgaParam):
	pgaParam = new PGA_Param();
	pgaParam.setNonEditable();

    // Add the warning listeners:
    saParam.addParameterChangeWarningListener(warningListener);
    pgaParam.addParameterChangeWarningListener(warningListener);

    // Put parameters in the supportedIMParams list:
    supportedIMParams.clear();
    supportedIMParams.addParameter(saParam);
    supportedIMParams.addParameter(pgaParam);

  }

  protected void initOtherParams() {

	    // init other params defined in parent class
	    super.initOtherParams();

	    // the stdDevType Parameter
	    StringConstraint stdDevTypeConstraint = new StringConstraint();
	    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
	    stdDevTypeConstraint.addString(STD_DEV_TYPE_BASEMENT);
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

  public double getMean(int iper, double vs30, double rjb, double mag) {

    // 
	
	double lnY, Fsite;
	double v1 = 2000.0;
	
	double magDiff = mag - 6.0;
	double rM = Math.sqrt(rjb*rjb+c7[iper]*c7[iper]);
	
	lnY = c1[iper]+c2[iper]*magDiff+c3[iper]*magDiff*magDiff-c4[iper]*Math.log(rM)-(c5[iper]-c4[iper])*Math.max(Math.log(rM/100), 0)-c6[iper]*rM;
	  
	// site response from Silva et al. 1996 not implemented
	
	if (vs30 < v1) {
		Fsite = 0;
	}
	else {
		Fsite = 0;
	}
	
    return (lnY + Fsite);
  }

  public double getStdDev(int iper, double rjb, double mag) {
	  
	  double sigmaaM, sigmaaR, sigmae, sigmatot;
	  
	  if (mag <= 5.0) {
		  sigmaaM = m50[iper]; 
	  }
	  else if (mag <= 5.5) {
		  sigmaaM = m50[iper] + (m55[iper] - m50[iper])/(5.5-5.0)*(mag-5.0);
	  }
	  else if (mag <= 8.0) {
		  sigmaaM = m55[iper] + (m80[iper] - m55[iper])/(8.0-5.5)*(mag-5.5);
	  }
	  else {
		  sigmaaM = m80[iper];
	  }
	  
	  if (rjb <= 5.0) {
		  sigmaaR = r05[iper]; 
	  }
	  else if (rjb <= 20.0) {
		  sigmaaR = r05[iper] + (r20[iper] - r05[iper])/(20.0-5.0)*(rjb-5.0);
	  }
	  else {
		  sigmaaR = r20[iper];
	  }	  
	  
	  if (period[iper] == 2.0) {
		  sigmae = 0.34 + 0.06*(mag-6.0);
	  }
	  else {
		  sigmae = 0.36 + 0.07*(mag-6.0);
	  }
	  
	  sigmatot = (Math.sqrt(sigmaaM*sigmaaM+sigmaaR*sigmaaR+sigmae*sigmae));
	  
	    if (stdDevTypeParam.getValue().equals(STD_DEV_TYPE_BASEMENT)) {
	        return Math.sqrt(sigmatot*sigmatot-0.3*0.3);
	      }
	    else {
	    	return sigmatot ;
	    }	  
  }

  /**
   * This listens for parameter changes and updates the primitive parameters accordingly
   * @param e ParameterChangeEvent
   */
  public void parameterChange(ParameterChangeEvent e) {

    String pName = e.getParameterName();
    Object val = e.getNewValue();
    parameterChange = true;
    if (pName.equals(DistanceJBParameter.NAME)) {
      rjb = ( (Double) val).doubleValue();
    }
//    else if (pName.equals(Vs30_Param.NAME)) {
//      vs30 = ( (Double) val).doubleValue();
//    }
    else if (pName.equals(magParam.NAME)) {
      mag = ( (Double) val).doubleValue();
    }
    else if (pName.equals(PeriodParam.NAME) ) {
    	intensityMeasureChanged = true;
    }
  }

  /**
   * Allows to reset the change listeners on the parameters
   */
  public void resetParameterEventListeners(){
    distanceJBParam.removeParameterChangeListener(this);
//    vs30Param.removeParameterChangeListener(this);
    magParam.removeParameterChangeListener(this);
    saPeriodParam.removeParameterChangeListener(this);

    this.initParameterEventListeners();
  }

  /**
   * Adds the parameter change listeners. This allows to listen to when-ever the
   * parameter is changed.
   */
  protected void initParameterEventListeners() {

    distanceJBParam.addParameterChangeListener(this);
//    vs30Param.addParameterChangeListener(this);
    magParam.addParameterChangeListener(this);
    saPeriodParam.addParameterChangeListener(this);
  }

  /**
   * 
   * @throws MalformedURLException if returned URL is not a valid URL.
   * @returns the URL to the AttenuationRelationship document on the Web.
   */
  public URL getAttenuationRelationshipURL() throws MalformedURLException{
	  return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/BA_2008.html");
  }   
  
}