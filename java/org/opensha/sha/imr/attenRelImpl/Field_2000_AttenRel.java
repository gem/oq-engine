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
import java.util.Enumeration;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.TreeSet;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.IMRException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FaultUtils;
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
 * <b>Title:</b> Field_2000_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship
 * developed by Field (2000, Bulletin of the Seismological Society of America, vol
 * 90, num 6b, pp S209-S221) <p>
 *
 * Supported Intensity-Measure Parameters:<p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration
 * <LI>pgvParam - Peak Ground Velocity (from 1-sec SA using the Newmark & Hall (1982) mult factor of 37.27*2.54)
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceJBParam - closest distance to surface projection of fault
 * <LI>vs30Param - Average 30-meter shear-wave velocity at the site
 * <LI>basinDepthParam - Depth to 2.5 km/sec S-wave velocity
 * <LI>fltTypeParam - Style of faulting
 * <LI>componentParam - Component of shaking (only one)
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL><p>
 *
 * @author     Edward H. Field
 * @created    February 27, 2002
 * @version    1.0
 */


public class Field_2000_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI {

  // debugging stuff:
  private final static String C = "Field_2000_AttenRel";
  private final static boolean D = false;
  public final static String NAME = "Field (2000)";
  public final static String SHORT_NAME = "Field2000";
  private static final long serialVersionUID = 1234567890987654362L;


  // style of faulting options
  public final static String FLT_TYPE_OTHER = "Other/Unknown";
  public final static String FLT_TYPE_REVERSE = "Reverse";

  protected WarningDoubleParameter basinDepthParam = null;
  public final static String BASIN_DEPTH_NAME = "Field-Basin-Depth";
  public final static String BASIN_DEPTH_UNITS = "km";
  public final static String BASIN_DEPTH_INFO =
      "Depth to 2.5 km/sec S-wave-velocity isosurface, from SCEC Phase III Report";
  protected final static Double BASIN_DEPTH_DEFAULT = new Double(0.0);
  protected final static Double BASIN_DEPTH_MIN = new Double(0);
  protected final static Double BASIN_DEPTH_MAX = new Double(30);
  //protected final static Double BASIN_DEPTH_WARN_MIN = new Double(0);
  //protected final static Double BASIN_DEPTH_WARN_MAX = new Double(10);

  // warning constraint fields:
  protected final static Double VS30_WARN_MIN = new Double(180.0);
  protected final static Double VS30_WARN_MAX = new Double(3500.0);
  protected final static Double MAG_WARN_MIN = new Double(5.0);
  protected final static Double MAG_WARN_MAX = new Double(8.0);

  /**
   * Joyner-Boore Distance parameter
   */
  protected final static Double DISTANCE_JB_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_JB_WARN_MAX = new Double(150.0);

  /**
   * The current set of coefficients based on the selected intensityMeasure
   */
  private Field_2000_AttenRelCoefficients coeff = null;

  /**
   *  Hashtable of coefficients for the supported intensityMeasures
   */
  protected Hashtable coefficients = new Hashtable();

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   * Determines the style of faulting from the rake angle (which
   * comes from the eqkRupture object) and fills in the
   * value of the fltTypeParam.  Options are "Reverse" if 135>rake>45
   * or "Other/Unknown" otherwise.
   *
   * @param rake                      in degrees
   * @throws InvalidRangeException    If not valid rake angle
   */
  protected void setFaultTypeFromRake(double rake) throws InvalidRangeException {
    FaultUtils.assertValidRake(rake);
    if (rake >= 45 && rake <= 135) {
      fltTypeParam.setValue(FLT_TYPE_REVERSE);
    }
    else {
      fltTypeParam.setValue(FLT_TYPE_OTHER);
    }
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
   *  This sets the site-related parameters (vs30Param and basinDepthParam) based on what is in
   *  the Site object passed in.  This also sets the internally held
   *  Site object as that passed in.   Warning constrains are ingored.
   *
   * @param  site             The new site
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   */
  public void setSite(Site site) throws ParameterException {

    vs30Param.setValueIgnoreWarning((Double)site.getParameter(Vs30_Param.NAME).getValue());
    basinDepthParam.setValueIgnoreWarning((Double)site.getParameter(BASIN_DEPTH_NAME).
                                          getValue());
    this.site = site;
    setPropagationEffectParams();

  }

  /**
   * This sets the site and eqkRupture, and the related parameters,
   *  from the propEffect object passed in. Warning constrains are ingored.
   * @param propEffect
   * @throws ParameterException Thrown if the Site object doesn't contain
   * Vs30 parameter.
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setPropagationEffect(PropagationEffect propEffect) throws
      ParameterException, InvalidRangeException {

    this.site = propEffect.getSite();
    this.eqkRupture = propEffect.getEqkRupture();

    // set the locat site-type param
    vs30Param.setValueIgnoreWarning((Double)site.getParameter(Vs30_Param.NAME).getValue());
    basinDepthParam.setValueIgnoreWarning((Double)site.getParameter(BASIN_DEPTH_NAME).
                                          getValue());

    magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
    setFaultTypeFromRake(eqkRupture.getAveRake());

    // set the distance param
    propEffect.setParamValue(distanceJBParam);

  }

  /**
   * This calculates the Distance JB propagation effect parameter based
   * on the current site and eqkRupture. <P>
   */
  protected void setPropagationEffectParams() {

    if ( (this.site != null) && (this.eqkRupture != null)) {
      distanceJBParam.setValue(eqkRupture, site);
    }
  }

  /**
   * This function determines which set of coefficients in the HashMap
   * are to be used given the current intensityMeasure (im) Parameter. The
   * lookup is done keyed on the name of the im, plus the period value if
   * im.getName() == "SA" (seperated by "/").
   *
   * SWR: I choose the name <code>update</code> instead of set, because set is so common
   * to java bean fields, i.e. getters and setters, that set() usually implies
   * passing in a new value to the java bean field. I prefer update or refresh
   * to functions that change internal values internally
   */
  protected void updateCoefficients() throws ParameterException {

    // Check that parameter exists
    if (im == null) {
      throw new ParameterException(C +
                                   ": updateCoefficients(): " +
                                   "The Intensity Measusre Parameter has not been set yet, unable to process."
          );
    }

    // if IMT is PGV, get the 1-sec SA coefficients
    if (im.getName().equals(PGV_Param.NAME)) {
      coeff = (Field_2000_AttenRelCoefficients) coefficients.get("SA/1.0");
    }
    else {
      StringBuffer key = new StringBuffer(im.getName());
      if (im.getName().equalsIgnoreCase(SA_Param.NAME)) {
        key.append("/" + saPeriodParam.getValue());
      }
      if (coefficients.containsKey(key.toString())) {
        coeff = (Field_2000_AttenRelCoefficients) coefficients.get(key.toString());
      }
      else {
        throw new ParameterException(C + ": setIntensityMeasureType(): " +
            "Unable to locate coefficients with key = " + key);
      }
    }
  }

  /**
   *  No-Arg constructor. This initializes several ParameterList objects.
   */
  public Field_2000_AttenRel(ParameterChangeWarningListener warningListener) {

    super();

    this.warningListener = warningListener;

    initCoefficients(); // This must be called before the next one
    initSupportedIntensityMeasureParams();

    initEqkRuptureParams();
    initPropagationEffectParams();
    initSiteParams();
    initOtherParams();

    initIndependentParamLists(); // Do this after the above

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
   * Calculates the mean of the exceedence probability distribution. <p>
   *
   * @return    The mean value
   */
  public double getMean() throws IMRException {

    double mag, vs30, distanceJB, depth;
    String fltTypeValue;

    try {
      mag = ( (Double) magParam.getValue()).doubleValue();
      vs30 = ( (Double) vs30Param.getValue()).doubleValue();
      distanceJB = ( (Double) distanceJBParam.getValue()).doubleValue();
      fltTypeValue = fltTypeParam.getValue().toString();
    }
    catch (NullPointerException e) {
      throw new IMRException(C + ": getMean(): " + ERR);
    }

    // check if distance is beyond the user specified max
    if (distanceJB > USER_MAX_DISTANCE) {
      return VERY_SMALL_MEAN;
    }

    // the following is inefficient if the im Parameter has not been changed in any way
    updateCoefficients();

    // Calculate b1 based on fault type
    double b1;
    if (fltTypeValue.equals(FLT_TYPE_REVERSE)) {
      b1 = coeff.b1rv;
    }
    else if (fltTypeValue.equals(FLT_TYPE_OTHER)) {
      b1 = coeff.b1ss;
    }
    else {
      throw new ParameterException(C +
          ": getMean(): Invalid EqkRupture Parameter value for : FaultType");
    }

    // Calculate the log mean
    double mean = b1 +
        coeff.b2 * (mag - 6) +
        coeff.b3 * (Math.pow( (mag - 6), 2)) +
        coeff.b5 *
        (Math.log(Math.pow( (distanceJB * distanceJB + coeff.h * coeff.h), 0.5))) +
        coeff.bv * (Math.log(vs30 / 760));

    if (basinDepthParam.getValue() != null) {
      depth = ( (Double) basinDepthParam.getValue()).doubleValue();
      mean += coeff.bdSlope * depth + coeff.bdIntercept;
    }

    // convert the 1.0-period SA value if IMT="PGV"
    if (im.getName().equals(PGV_Param.NAME)) {
      mean += Math.log(37.27 * 2.54);
    }

    // return the result
    return (mean);
  }

  /**
   * @return    The stdDev value
   */
  public double getStdDev() throws IMRException {

    double mag;
    String stdDevType = stdDevTypeParam.getValue().toString();

    try {
      mag = ( (Double) magParam.getValue()).doubleValue();
    }
    catch (NullPointerException e) {
      throw new IMRException(C + ": getMean(): " + ERR);
    }

    // make max mag equal to 7.0
    if (mag > 7.0) {
      mag = 7.0;
    }

    // this is inefficient if the im has not been changed in any way
    updateCoefficients();

    // set the correct standard deviation depending on component and type
    double temp_std;
    if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL_MAG_DEP)) { // "Total - Mag Dep."
      temp_std = Math.sqrt(coeff.intra_slope * mag + coeff.intra_intercept +
                           coeff.tau * coeff.tau);
    }
    else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL)) { // "Total"
      temp_std = Math.sqrt( (coeff.intra_mag_ind * coeff.intra_mag_ind +
                             coeff.tau * coeff.tau));
    }
    else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER)) { // "Inter-Event"
      temp_std = coeff.tau;
    }
    else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA_MAG_DEP)) { // "Intra-Event - Mag. Dep."
      temp_std = Math.sqrt(coeff.intra_slope * mag + coeff.intra_intercept);
    }
    else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA)) { // "Intra-Event"
      temp_std = coeff.intra_mag_ind;
    }
    else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) { // "None (zero)"
      temp_std = 0;
    }
    else {
      throw new ParameterException(C + ": getStdDev(): Invalid StdDevType");
    }

    return temp_std;

  }

  public void setParamDefaults() {

    //((ParameterAPI)this.iml).setValue( IML_DEFAULT );
    vs30Param.setValueAsDefault();
    magParam.setValueAsDefault();
    fltTypeParam.setValueAsDefault();
    distanceJBParam.setValueAsDefault();
    saParam.setValueAsDefault();
    saPeriodParam.setValueAsDefault();
    saDampingParam.setValueAsDefault();
    pgaParam.setValueAsDefault();
    pgvParam.setValueAsDefault();
    componentParam.setValueAsDefault();
    stdDevTypeParam.setValueAsDefault();
    basinDepthParam.setValue(BASIN_DEPTH_DEFAULT);

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
    meanIndependentParams.addParameter(basinDepthParam);
    meanIndependentParams.addParameter(magParam);
    meanIndependentParams.addParameter(fltTypeParam);
    meanIndependentParams.addParameter(componentParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    stdDevIndependentParams.addParameter(stdDevTypeParam);
    stdDevIndependentParams.addParameter(magParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    exceedProbIndependentParams.addParameter(distanceJBParam);
    exceedProbIndependentParams.addParameter(vs30Param);
    exceedProbIndependentParams.addParameter(basinDepthParam);
    exceedProbIndependentParams.addParameter(magParam);
    exceedProbIndependentParams.addParameter(fltTypeParam);
    exceedProbIndependentParams.addParameter(componentParam);
    exceedProbIndependentParams.addParameter(stdDevTypeParam);
    exceedProbIndependentParams.addParameter(this.sigmaTruncTypeParam);
    exceedProbIndependentParams.addParameter(this.sigmaTruncLevelParam);

    // params that the IML at exceed. prob. depends upon
    imlAtExceedProbIndependentParams.addParameterList(
        exceedProbIndependentParams);
    imlAtExceedProbIndependentParams.addParameter(exceedProbParam);

  }

  /**
   *  Creates the Vs30 & basinDepth arameters and adds them to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {

	vs30Param = new Vs30_Param(VS30_WARN_MIN, VS30_WARN_MAX);

    DoubleConstraint basinDepthConstraint = new DoubleConstraint(
        BASIN_DEPTH_MIN, BASIN_DEPTH_MAX);
    basinDepthConstraint.setNullAllowed(true);
    basinDepthConstraint.setNonEditable();
    basinDepthParam = new WarningDoubleParameter(BASIN_DEPTH_NAME,
                                                 basinDepthConstraint,
                                                 BASIN_DEPTH_UNITS);
    basinDepthParam.setInfo(BASIN_DEPTH_INFO);
    basinDepthParam.setNonEditable();

    // add it to the siteParams list:
    siteParams.clear();
    siteParams.addParameter(vs30Param);
    siteParams.addParameter(basinDepthParam);

  }

  /**
   *  Creates the two Potential Earthquake parameters (magParam and
   *  fltTypeParam) and adds them to the eqkRuptureParams
   *  list. Makes the parameters noneditable.
   */
  protected void initEqkRuptureParams() {

	magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);

    StringConstraint constraint = new StringConstraint();
    constraint.addString(FLT_TYPE_OTHER);
    constraint.addString(FLT_TYPE_REVERSE);
    constraint.setNonEditable();
    fltTypeParam = new FaultTypeParam(constraint,FLT_TYPE_OTHER);

    eqkRuptureParams.clear();
    eqkRuptureParams.addParameter(magParam);
    eqkRuptureParams.addParameter(fltTypeParam);

  }

  /**
   *  Creates the single Propagation Effect parameter and adds it to the
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
    TreeSet set = new TreeSet();
    Enumeration keys = coefficients.keys();
    while (keys.hasMoreElements()) {
      Field_2000_AttenRelCoefficients coeff = (Field_2000_AttenRelCoefficients)
          coefficients.get(keys.nextElement());
      if (coeff.period >= 0) {
        set.add(new Double(coeff.period));
      }
    }
    Iterator it = set.iterator();
    while (it.hasNext()) {
      periodConstraint.addDouble( (Double) it.next());
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
    constraint.addString(ComponentParam.COMPONENT_AVE_HORZ);
    constraint.setNonEditable();
    componentParam = new ComponentParam(constraint,componentParam.COMPONENT_AVE_HORZ);

    // the stdDevType Parameter
    StringConstraint stdDevTypeConstraint = new StringConstraint();
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL_MAG_DEP);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTER);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTRA_MAG_DEP);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTRA);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
    stdDevTypeConstraint.setNonEditable();
    stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint, StdDevTypeParam.STD_DEV_TYPE_TOTAL_MAG_DEP);

    // add these to the list
    otherParams.addParameter(componentParam);
    otherParams.addParameter(stdDevTypeParam);

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

    coefficients.clear();

    // PGA
    Field_2000_AttenRelCoefficients coeff = new Field_2000_AttenRelCoefficients(
        PGA_Param.NAME,
        0.0, 0.853, 0.872, 0.442, -0.067, -0.960, -0.154, 8.90, 0.067, -0.14,
        -0.1, 0.8771, 0.23, 0.47);

    // SA/0.00
    Field_2000_AttenRelCoefficients coeff0 = new
        Field_2000_AttenRelCoefficients(SA_Param.NAME + '/' +
                                        (new Double("0.0")).doubleValue(),
                                        0.0, 0.853, 0.872, 0.442, -0.067,
                                        -0.960, -0.154, 8.90, 0.067, -0.14,
                                        -0.1, 0.8771, 0.23, 0.47);
    // SA/0.3
    Field_2000_AttenRelCoefficients coeff1 = new
        Field_2000_AttenRelCoefficients("SA/" + (new Double("0.3")).doubleValue(),
                                        0.3, 0.995, 1.096, 0.501, -0.112,
                                        -0.841, -0.350, 7.20, 0.057, -0.12,
                                        -0.11, 0.9924, 0.26, 0.53);
    // SA/1.0
    Field_2000_AttenRelCoefficients coeff2 = new
        Field_2000_AttenRelCoefficients("SA/" + (new Double("1.0")).doubleValue(),
                                        1.0, -0.164, -0.267, 0.903, 0.0, -0.914,
                                        -0.704, 6.20, 0.12, -0.25, -0.1, 0.9516,
                                        0.22, 0.53);
    // SA/3.0
    Field_2000_AttenRelCoefficients coeff3 = new
        Field_2000_AttenRelCoefficients("SA/" + (new Double("3.0")).doubleValue(),
                                        3.0, -2.267, -2.681, 1.083, 0.0, -0.720,
                                        -0.674, 3.00, 0.11, -0.18, 0.14, -0.66,
                                        0.3, 0.52);

    coefficients.put(coeff.getName(), coeff);
    coefficients.put(coeff0.getName(), coeff0);
    coefficients.put(coeff1.getName(), coeff1);
    coefficients.put(coeff2.getName(), coeff2);
    coefficients.put(coeff3.getName(), coeff3);

  }

  /**
   *  <b>Title:</b> Field_2000_AttenRelCoefficients<br>
   *  <b>Description:</b> This class encapsulates all the
   *  coefficients needed to calculate the Mean and StdDev for
   *  the Field_2000_AttenRel.  One instance of this class holds the set of
   *  coefficients for each period (one row of their table 8).<br>
   *  <b>Copyright:</b> Copyright (c) 2001 <br>
   *  <b>Company:</b> <br>
   *
   *
   * @author     Steven W Rock
   * @created    February 27, 2002
   * @version    1.0
   */

  class Field_2000_AttenRelCoefficients
      implements NamedObjectAPI {

    protected final static String C = "Field_2000_AttenRelCoefficients";
    protected final static boolean D = false;
    /** For serialization. */
    private static final long serialVersionUID = 1234567890987654327L;


    protected String name;
    protected double period = -1;
    protected double b1ss;
    protected double b1rv;
    protected double b2;
    protected double b3;
    protected double b5;
    protected double bv;
    protected double h;
    protected double bdSlope;
    protected double bdIntercept;
    protected double intra_slope;
    protected double intra_intercept;
    protected double tau;
    protected double intra_mag_ind;

    /**
     *  Constructor for the Field_2000_AttenRelCoefficients object
     *
     * @param  name  Description of the Parameter
     */
    public Field_2000_AttenRelCoefficients(String name) {
      this.name = name;
    }

    /**
     *  Constructor for the Field_2000_AttenRelCoefficients object that sets all values at once
     *
     * @param  name  Description of the Parameter
     */
    public Field_2000_AttenRelCoefficients(String name, double period,
                                           double b1ss, double b1rv, double b2,
                                           double b3, double b5,
                                           double bv, double h, double bdSlope,
                                           double bdIntercept,
                                           double intra_slope,
                                           double intra_intercept, double tau,
                                           double intra_mag_ind) {
      this.name = name;
      this.period = period;
      this.b1ss = b1ss;
      this.b1rv = b1rv;
      this.b2 = b2;
      this.b3 = b3;
      this.b5 = b5;
      this.bv = bv;
      this.h = h;
      this.bdSlope = bdSlope;
      this.bdIntercept = bdIntercept;
      this.intra_slope = intra_slope;
      this.intra_intercept = intra_intercept;
      this.tau = tau;
      this.intra_mag_ind = intra_mag_ind;
    }

    /**
     *  Gets the name attribute of the Field_2000_AttenRelCoefficients object
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
      b.append("\n  b1ss = " + b1ss);
      b.append("\n  b1rv = " + b1rv);
      b.append("\n  b2 = " + b2);
      b.append("\n  b3 = " + b3);
      b.append("\n  b5 = " + b5);
      b.append("\n  bv = " + bv);
      b.append("\n  h = " + h);
      b.append("\n  bdSlope = " + bdSlope);
      b.append("\n  bdIntercept = " + bdIntercept);
      b.append("\n  intra_slope = " + intra_slope);
      b.append("\n  intra_intercept = " + intra_intercept);
      b.append("\n  tau = " + tau);
      b.append("\n  intra_mag_ind = " + intra_mag_ind);
      return b.toString();
    }
  }
  
  /**
   * This provides a URL where more info on this model can be obtained
   * @throws MalformedURLException if returned URL is not a valid URL.
   * @returns the URL to the AttenuationRelationship document on the Web.
   */
  public URL getInfoURL() throws MalformedURLException{
	  return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/Field_2000.html");
  }

}
