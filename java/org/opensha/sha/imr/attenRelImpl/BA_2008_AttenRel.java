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
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <b>Title:</b> BA_2008_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship published by Boore & Atkinson (2008,
 * "Ground-Motion Prediction Equations for the Average Horizontal Component of PGA, PGV, and 5%-Damped PSA 
 * at Spectral Periods between 0.01 s and 10.0 s", Earthquake Spectra, Volume 24, Number 1, pp. 99-138)
 * 
 *
 * Supported Intensity-Measure Parameters:<p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>pgaParam - Peak Ground Velocity
 * <LI>saParam - Response Spectral Acceleration
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceJBParam - closest distance to surface projection of fault
 * <LI>vs30Param - 30-meter shear wave velocity
 * <LI>fltTypeParam - Style of faulting
 * <LI>componentParam - Component of shaking (only one)
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL></p>
 * 
 *<p>
 *
 * Verification - This model has been tested against: 1) a verification file generated independently by Ken Campbell,
 * implemented in the JUnit test class BA_2008_test; and  2) by the test class NGA08_Site_EqkRup_Tests, which makes sure
 * parameters are set properly when Site and EqkRupture objects are passed in.
 * 
 *</p>
 *
 *
 * @author     Edward H. Field
 * @created    November, 2008
 * @version    1.0
 */


public class BA_2008_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI, ParameterChangeListener {

  // Debugging stuff
  private final static String C = "BA_2008_AttenRel";
  private final static boolean D = false;
  public final static String SHORT_NAME = "Boore2008";
  private static final long serialVersionUID = 1234567890987654353L;

  // Name of IMR
  public final static String NAME = "Boore & Atkinson (2008)";
  
  // URL Info String
  private final static String URL_INFO_STRING = "http://www.opensha.org/documentation/modelsImplemented/attenRel/BA_2008.html";

  
  // coefficients:
  //    note that index 0 below is for PGA4nl (rock-PGA for computing amp factor); previously this had a slightly 
  //    diff set of coeffs, but now they are exactly the same as PGA, we'd kept the index because it indicates to set site amp to zero
  //    index 1 is for PGV and index 2 is for PGA
  double[] period= { -2, -1, 0, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5, 7.5, 10};
  double[] b_lin= { -0.36, -0.6, -0.36, -0.36, -0.34, -0.33, -0.29, -0.23, -0.25, -0.28, -0.31, -0.39, -0.44, -0.5, -0.6, -0.69, -0.7, -0.72, -0.73, -0.74, -0.75, -0.75, -0.692, -0.65};
  double[] b1= { -0.64, -0.5, -0.64, -0.64, -0.63, -0.62, -0.64, -0.64, -0.6, -0.53, -0.52, -0.52, -0.52, -0.51, -0.5, -0.47, -0.44, -0.4, -0.38, -0.34, -0.31, -0.291, -0.247, -0.215};
  double[] b2= { -0.14, -0.06, -0.14, -0.14, -0.12, -0.11, -0.11, -0.11, -0.13, -0.18, -0.19, -0.16, -0.14, -0.1, -0.06, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  double[] c1= { -0.6605, -0.8737, -0.6605, -0.6622, -0.666, -0.6901, -0.717, -0.7205, -0.7081, -0.6961, -0.583, -0.5726, -0.5543, -0.6443, -0.6914, -0.7408, -0.8183, -0.8303, -0.8285, -0.7844, -0.6854, -0.5096, -0.3724, -0.09824};
  double[] c2= { 0.1197, 0.1006, 0.1197, 0.12, 0.1228, 0.1283, 0.1317, 0.1237, 0.1117, 0.09884, 0.04273, 0.02977, 0.01955, 0.04394, 0.0608, 0.07518, 0.1027, 0.09793, 0.09432, 0.07282, 0.03758, -0.02391, -0.06568, -0.138};
  double[] c3= { -0.01151, -0.00334, -0.01151, -0.01151, -0.01151, -0.01151, -0.01151, -0.01151, -0.01151, -0.01113, -0.00952, -0.00837, -0.0075, -0.00626, -0.0054, -0.00409, -0.00334, -0.00255, -0.00217, -0.00191, -0.00191, -0.00191, -0.00191, -0.00191};
  double[] h= { 1.35, 2.54, 1.35, 1.35, 1.35, 1.35, 1.35, 1.55, 1.68, 1.86, 1.98, 2.07, 2.14, 2.24, 2.32, 2.46, 2.54, 2.66, 2.73, 2.83, 2.89, 2.93, 3, 3.04};
  double[] e1= { -0.53804, 5.00121, -0.53804, -0.52883, -0.52192, -0.45285, -0.28476, 0.00767, 0.20109, 0.46128, 0.5718, 0.51884, 0.43825, 0.3922, 0.18957, -0.21338, -0.46896, -0.86271, -1.22652, -1.82979, -2.24656, -1.28408, -1.43145, -2.15446};
  double[] e2= { -0.5035, 5.04727, -0.5035, -0.49429, -0.48508, -0.41831, -0.25022, 0.04912, 0.23102, 0.48661, 0.59253, 0.53496, 0.44516, 0.40602, 0.19878, -0.19496, -0.43443, -0.79593, -1.15514, -1.7469, -2.15906, -1.2127, -1.31632, -2.16137};
  double[] e3= { -0.75472, 4.63188, -0.75472, -0.74551, -0.73906, -0.66722, -0.48462, -0.20578, 0.03058, 0.30185, 0.4086, 0.3388, 0.25356, 0.21398, 0.00967, -0.49176, -0.78465, -1.20902, -1.57697, -2.22584, -2.58228, -1.50904, -1.81022, -2.53323};
  double[] e4= { -0.5097, 5.0821, -0.5097, -0.49966, -0.48895, -0.42229, -0.26092, 0.02706, 0.22193, 0.49328, 0.61472, 0.57747, 0.5199, 0.4608, 0.26337, -0.10813, -0.3933, -0.88085, -1.27669, -1.91814, -2.38168, -1.41093, -1.59217, -2.14635};
  double[] e5= { 0.28805, 0.18322, 0.28805, 0.28897, 0.25144, 0.17976, 0.06369, 0.0117, 0.04697, 0.1799, 0.52729, 0.6088, 0.64472, 0.7861, 0.76837, 0.75179, 0.6788, 0.70689, 0.77989, 0.77966, 1.24961, 0.14271, 0.52407, 0.40387};
  double[] e6= { -0.10164, -0.12736, -0.10164, -0.10019, -0.11006, -0.12858, -0.15752, -0.17051, -0.15948, -0.14539, -0.12964, -0.13843, -0.15694, -0.07843, -0.09054, -0.14053, -0.18257, -0.2595, -0.29657, -0.45384, -0.35874, -0.39006, -0.37578, -0.48492};
  double[] e7= { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.00102, 0.08607, 0.10601, 0.02262, 0, 0.10302, 0.05393, 0.19082, 0.29888, 0.67466, 0.79508, 0, 0, 0};
  double[] mh= { 6.75, 8.5, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 8.5, 8.5, 8.5};
  double[] s= { 0, 0.5, 0.502, 0.502, 0.502, 0.507, 0.516, 0.513, 0.52, 0.518, 0.523, 0.527, 0.546, 0.541, 0.555, 0.571, 0.573, 0.566, 0.58, 0.566, 0.583, 0.601, 0.626, 0.645};
  double[] t_u= { 0, 0.286, 0.265, 0.267, 0.267, 0.276, 0.286, 0.322, 0.313, 0.288, 0.283, 0.267, 0.272, 0.267, 0.265, 0.311, 0.318, 0.382, 0.398, 0.41, 0.394, 0.414, 0.465, 0.355};
  double[] s_tu= { 0, 0.576, 0.566, 0.569, 0.569, 0.578, 0.589, 0.606, 0.608, 0.592, 0.596, 0.592, 0.608, 0.603, 0.615, 0.649, 0.654, 0.684, 0.702, 0.7, 0.702, 0.73, 0.781, 0.735};
  double[] t_m= { 0, 0.256, 0.26, 0.262, 0.262, 0.274, 0.286, 0.32, 0.318, 0.29, 0.288, 0.267, 0.269, 0.267, 0.265, 0.299, 0.302, 0.373, 0.389, 0.401, 0.385, 0.437, 0.477, 0.477};
  double[] s_tm= { 0, 0.56, 0.564, 0.566, 0.566, 0.576, 0.589, 0.606, 0.608, 0.594, 0.596, 0.592, 0.608, 0.603, 0.615, 0.645, 0.647, 0.679, 0.7, 0.695, 0.698, 0.744, 0.787, 0.801};

  
  
  
  double a1 = 0.03;  // g
  double pgalow=0.06; // g
  double a2 = 0.09; // g
  double v1 = 180; // m/s
  double v2 = 300; // m/s
  double v_ref = 760; // m/s
  double m_ref = 4.5;
  double r_ref = 1; //km
  
  private HashMap indexFromPerHashMap;

  private int iper;
  private double vs30, rjb, mag;
  private String stdDevType, fltType;
  private boolean parameterChange;

  protected final static Double MAG_WARN_MIN = new Double(5);
  protected final static Double MAG_WARN_MAX = new Double(8);
  protected final static Double DISTANCE_JB_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_JB_WARN_MAX = new Double(200.0);
  protected final static Double VS30_WARN_MIN = new Double(180.0);
  protected final static Double VS30_WARN_MAX = new Double(1300.0);

  
  // style of faulting options
  public final static String FLT_TYPE_UNKNOWN = "Unknown";
  public final static String FLT_TYPE_STRIKE_SLIP = "Strike-Slip";
  public final static String FLT_TYPE_REVERSE = "Thrust/Reverse";
  public final static String FLT_TYPE_NORMAL = "Normal";

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   *  This initializes several ParameterList objects.
   */
  public BA_2008_AttenRel(ParameterChangeWarningListener
                                    warningListener) {

    super();

    this.warningListener = warningListener;

    initSupportedIntensityMeasureParams();
    indexFromPerHashMap = new HashMap();
    for (int i = 3; i < period.length ; i++) {
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
   *  This sets the eqkRupture related parameters (magParam
   *  and fltTypeParam) based on the eqkRupture passed in.
   *  The internally held eqkRupture object is also set as that
   *  passed in.  Warning constrains are ingored.
   *
   * @param  eqkRupture  The new eqkRupture value
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setEqkRupture(EqkRupture eqkRupture) throws InvalidRangeException {

    magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
    setFaultTypeFromRake(eqkRupture.getAveRake());
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

    vs30Param.setValue((Double)site.getParameter(Vs30_Param.NAME).getValue());
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

    if (im.getName().equalsIgnoreCase(PGV_Param.NAME)) {
      iper = 1;
    }
    else if (im.getName().equalsIgnoreCase(PGA_Param.NAME)) {
      iper = 2;
    }
    else {
      iper = ( (Integer) indexFromPerHashMap.get(saPeriodParam.getValue())).
          intValue();
    }

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
	  
	  // remember that pga4nl term uses coeff index 0
	  double pga4nl = Math.exp(getMean(0, 760, rjb, mag, fltType, 0.0));
	  return getMean(iper, vs30, rjb, mag, fltType, pga4nl);
  }

  /**
   * @return    The stdDev value
   */
  public double getStdDev() {
    if (intensityMeasureChanged) {
      setCoeffIndex();// intensityMeasureChanged is set to false in this method
    }
    return getStdDev(iper, stdDevType, fltType);
  }

  /**
   * Determines the style of faulting from the rake angle.  Their report is not explicit,
   * so these ranges come from an email that told us to decide, but that within 30-degrees
   * of horz for SS was how the NGA data were defined.
   *
   * @param rake                      in degrees
   * @throws InvalidRangeException    If not valid rake angle
   */
  protected void setFaultTypeFromRake(double rake) throws InvalidRangeException {
	  if (rake<=30 && rake>=-30)
		  fltTypeParam.setValue(FLT_TYPE_STRIKE_SLIP);
	  else if (rake<=-150 || rake>=150)
		  fltTypeParam.setValue(FLT_TYPE_STRIKE_SLIP);
	  else if (rake > 30 && rake < 150)
		  fltTypeParam.setValue(FLT_TYPE_REVERSE);
	  else if (rake > -150 && rake < -30)
		  fltTypeParam.setValue(FLT_TYPE_NORMAL);
	  else
		  fltTypeParam.setValue(FLT_TYPE_UNKNOWN);
  } 
  
  
  
  /**
   * Allows the user to set the default parameter values for the selected Attenuation
   * Relationship.
   */
  public void setParamDefaults() {

	vs30Param.setValueAsDefault();
    magParam.setValueAsDefault();
    distanceJBParam.setValueAsDefault();
    fltTypeParam.setValueAsDefault();
    saParam.setValueAsDefault();
    saPeriodParam.setValueAsDefault();
    saDampingParam.setValueAsDefault();
    pgaParam.setValueAsDefault();
    pgvParam.setValueAsDefault();
    stdDevTypeParam.setValueAsDefault();
    componentParam.setValueAsDefault();

    vs30 = ( (Double) vs30Param.getValue()).doubleValue(); 
    rjb = ( (Double) distanceJBParam.getValue()).doubleValue();
    mag = ( (Double) magParam.getValue()).doubleValue();
    fltType = (String) fltTypeParam.getValue();
    stdDevType = (String) stdDevTypeParam.getValue();
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
    meanIndependentParams.addParameter(vs30Param);
    meanIndependentParams.addParameter(magParam);
    meanIndependentParams.addParameter(fltTypeParam);
    meanIndependentParams.addParameter(componentParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    stdDevIndependentParams.addParameter(stdDevTypeParam);
    stdDevIndependentParams.addParameter(componentParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    exceedProbIndependentParams.addParameterList(meanIndependentParams);
    exceedProbIndependentParams.addParameter(stdDevTypeParam);
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

    vs30Param.setValueIgnoreWarning((Double)site.getParameter(Vs30_Param.NAME).getValue());

    magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
    setFaultTypeFromRake(eqkRupture.getAveRake());

    propEffect.setParamValue(distanceJBParam);
  }
  
  
  
  
  /**
   *  Creates the Site-Type parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {

	vs30Param = new Vs30_Param(VS30_WARN_MIN, VS30_WARN_MAX);

    siteParams.clear();
    siteParams.addParameter(vs30Param);
  }

  /**
   *  Creates the two Potential Earthquake parameters (magParam and
   *  fltTypeParam) and adds them to the eqkRuptureParams
   *  list. Makes the parameters noneditable.
   */
  protected void initEqkRuptureParams() {


	magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);

    StringConstraint constraint = new StringConstraint();
    constraint.addString(FLT_TYPE_UNKNOWN);
    constraint.addString(FLT_TYPE_STRIKE_SLIP);
    constraint.addString(FLT_TYPE_NORMAL);
    constraint.addString(FLT_TYPE_REVERSE);
    constraint.setNonEditable();
    fltTypeParam = new FaultTypeParam(constraint,FLT_TYPE_UNKNOWN);

    eqkRuptureParams.clear();
    eqkRuptureParams.addParameter(magParam);
    eqkRuptureParams.addParameter(fltTypeParam);
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
    for (int i = 3; i < period.length; i++) {
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

	//  Create PGV Parameter (pgvParam):
	pgvParam = new PGV_Param();
	pgvParam.setNonEditable();

    // Add the warning listeners:
    saParam.addParameterChangeWarningListener(warningListener);
    pgaParam.addParameterChangeWarningListener(warningListener);
    pgvParam.addParameterChangeWarningListener(warningListener);

    // Put parameters in the supportedIMParams list:
    supportedIMParams.clear();
    supportedIMParams.addParameter(saParam);
    supportedIMParams.addParameter(pgaParam);
    supportedIMParams.addParameter(pgvParam);

  }

  /**
   *  Creates other Parameters that the mean or stdDev depends upon,
   *  such as the Component or StdDevType parameters.
   */
  protected void initOtherParams() {

    // init other params defined in parent class
    super.initOtherParams();

    // the Component Parameter
    StringConstraint constraint = new StringConstraint();
    constraint.addString(ComponentParam.COMPONENT_GMRotI50);
    constraint.setNonEditable();
    componentParam = new ComponentParam(constraint,ComponentParam.COMPONENT_GMRotI50);

    // the stdDevType Parameter
    StringConstraint stdDevTypeConstraint = new StringConstraint();
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTER);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTRA);
    stdDevTypeConstraint.setNonEditable();
	stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);

    // add these to the list
    otherParams.addParameter(componentParam);
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

  public double getMean(int iper, double vs30, double rjb, double mag,
                        String fltType, double pga4nl) {

    // remember that pga4ln term uses coeff index 0
    double Fm, Fd, Fs;
    int U =0, S=0, N=0, R=0;
    if(fltType.equals(FLT_TYPE_UNKNOWN))
    	  U=1;
    else if(fltType.equals(FLT_TYPE_NORMAL))
    	 N=1;
    else if(fltType.equals(FLT_TYPE_STRIKE_SLIP))
    	 S=1;
    else
    	 R=1;
    
    // Compute Fm
    double magDiff = mag-mh[iper];
    if (mag <= mh[iper]) {
      Fm = e1[iper]*U + e2[iper]*S + e3[iper]*N + e4[iper]*R + 
      	   e5[iper]*magDiff+e6[iper]*magDiff*magDiff;
    }
    else {
      Fm = e1[iper]*U + e2[iper]*S + e3[iper]*N + e4[iper]*R +
      		e7[iper]*(mag-mh[iper]);
    }

    double r = Math.sqrt(rjb * rjb + h[iper] * h[iper]);
    Fd = (c1[iper] + c2[iper]*(mag-m_ref))*Math.log(r/r_ref) +
         c3[iper]*(r-r_ref);

    // site response term
    if(iper == 0)
    		Fs =0; // pga4nl case
    else{
		double Flin = b_lin[iper]*Math.log(vs30/v_ref);	

		// compute bnl
		double bnl = 0;
	    if (vs30 <= v1) 
	      bnl = b1[iper];
	    else if (vs30 <= v2 && vs30 > v1) 
	      bnl = (b1[iper] - b2[iper]) * Math.log(vs30/v2) / Math.log(v1/v2) + b2[iper];
	    else if (vs30 < v_ref && vs30 > v2) 
	      bnl = b2[iper] * Math.log(vs30/v_ref) / Math.log(v2/v_ref);
	    else
	      bnl = 0.0;
	    
		// compute Fnl
		double Fnl;
	    if(pga4nl <= a1)
	    		Fnl = bnl*Math.log(pgalow/0.1);
	    else if (pga4nl <= a2 & pga4nl > a1) {
		    double c, d, dX, dY;
		    dX = Math.log(a2/a1);
		    dY = bnl*Math.log(a2/pgalow);
		    c = (3*dY-bnl*dX)/(dX*dX);
		    d = -(2*dY-bnl*dX)/(dX*dX*dX);

    		Fnl = bnl*Math.log(pgalow/0.1) + 
			c*Math.pow(Math.log(pga4nl/a1),2) +
			d*Math.pow(Math.log(pga4nl/a1),3);
	    	
	    }
	    else
	        Fnl = bnl*Math.log(pga4nl/0.1);
	    
	    Fs= Flin+Fnl;
    }
    return (Fm + Fd + Fs);
  }

  public double getStdDev(int iper, String stdDevType, String fltType) {
	  
	  if(fltType.equals(FLT_TYPE_UNKNOWN)) {
		  if(stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
			  return s_tu[iper];
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
			  return 0;
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
			  return t_u[iper];
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
			  return s[iper];
		  else 
			  return Double.NaN;
	  }
	  else {
		  if(stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
			  return s_tm[iper];
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
			  return 0;
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
			  return t_m[iper];
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
			  return s[iper];
		  else 
			  return Double.NaN; 
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
    else if (pName.equals(Vs30_Param.NAME)) {
      vs30 = ( (Double) val).doubleValue();
    }
    else if (pName.equals(magParam.NAME)) {
      mag = ( (Double) val).doubleValue();
    }
    else if (pName.equals(FaultTypeParam.NAME)) {
        fltType = (String)fltTypeParam.getValue();
    }
    else if (pName.equals(StdDevTypeParam.NAME)) {
      stdDevType = (String) val;
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
    vs30Param.removeParameterChangeListener(this);
    magParam.removeParameterChangeListener(this);
    fltTypeParam.addParameterChangeListener(this);
    stdDevTypeParam.removeParameterChangeListener(this);
    saPeriodParam.removeParameterChangeListener(this);

    this.initParameterEventListeners();
  }

  /**
   * Adds the parameter change listeners. This allows to listen to when-ever the
   * parameter is changed.
   */
  protected void initParameterEventListeners() {

    distanceJBParam.addParameterChangeListener(this);
    vs30Param.addParameterChangeListener(this);
    magParam.addParameterChangeListener(this);
    fltTypeParam.addParameterChangeListener(this);
    stdDevTypeParam.addParameterChangeListener(this);
    saPeriodParam.addParameterChangeListener(this);
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
