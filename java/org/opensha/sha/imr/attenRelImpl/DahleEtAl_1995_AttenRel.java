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
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

/**
 * <b>Title:</b> DahleEtAl_1995_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship
 * developed by Dahle et al. (1995, Proc. 5th Int Conf on Seismic Zonation,
 * Oct 17-19, 1995, Nice, France, p 1005-1012) <p>
 *
 * Supported Intensity-Measure Parameters:<p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceRupParam - closest distance to rupture surface
 * <LI>componentParam - Component of shaking (only one)
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL><p>
 *
 * @author     Edward H. Field
 * @created    April, 2003
 * @version    1.0
 */


public class DahleEtAl_1995_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI {

  // debugging stuff:
  private final static String C = "DahleEtAl_1995_AttenRel";
  private final static boolean D = false;
  public final static String NAME = "Dahle et al. (1995)";
  public final static String SHORT_NAME = "Dahle1995";
  private static final long serialVersionUID = 1234567890987654361L;


  // component
  public final static String COMPONENT_UNKNOWN_HORZ = "Unknown Horizontal";
  public final static String COMPONENT_DEFAULT = COMPONENT_UNKNOWN_HORZ;

  // warning constraint fields:
  protected final static Double MAG_WARN_MIN = new Double(5.);
  protected final static Double MAG_WARN_MAX = new Double(8.);

  // Standard Deviation type options
  public final static String STD_DEV_TYPE_BAY = "Bayesian";
  public final static String STD_DEV_TYPE_LS = "Least Squares";
  public final static String STD_DEV_TYPE_DEFAULT = STD_DEV_TYPE_BAY;
  protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_RUP_WARN_MAX = new Double(400.0);

  /**
   * Site Type Parameter ("Rock" versus "Soil")
   */
  private StringParameter siteTypeParam = null;
  public final static String SITE_TYPE_NAME = "Dahle Site Type";
  // no units
  public final static String SITE_TYPE_INFO =
      "Geological conditions at the site";
  public final static String SITE_TYPE_ROCK = "Rock";
  public final static String SITE_TYPE_SOIL = "Soil";
  public final static String SITE_TYPE_DEFAULT = SITE_TYPE_ROCK;

  /**
   * The current set of coefficients based on the selected intensityMeasure
   */
  private DahleEtAl_AttenRelCoefficients coeff = null;

  /**
   *  Hashtable of coefficients for the supported intensityMeasures
   */
  protected Hashtable coefficients = new Hashtable();

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   *  This sets the eqkRupture related parameter (magParam
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
   *  This sets the site-related parameter (vs30Param) based on what is in
   *  the Site object passed in (the Site object must have a parameter with
   *  the same name as that in vs30Param).  This also sets the internally held
   *  Site object as that passed in.
   *
   * @param  site             The new site value which the site-related parameter
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   */
  public void setSite(Site site) throws ParameterException {

    siteTypeParam.setValue((String)site.getParameter(SITE_TYPE_NAME).getValue());
    this.site = site;
    setPropagationEffectParams();

  }

  /**
   * This calculates the Distance JB propagation effect parameter based
   * on the current site and eqkRupture. <P>
   */
  protected void setPropagationEffectParams() {

    if ( (this.site != null) && (this.eqkRupture != null)) {
      distanceRupParam.setValue(eqkRupture, site);
    }
  }

  /**
   * This function determines which set of coefficients in the HashMap
   * are to be used given the current intensityMeasure (im) Parameter. The
   * lookup is done keyed on the name of the im, plus the period value if
   * im.getName() == "SA" (seperated by "/").
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
    if (coefficients.containsKey(key.toString())) {
      coeff = (DahleEtAl_AttenRelCoefficients) coefficients.get(key.toString());
    }
    else {
      throw new ParameterException(C + ": setIntensityMeasureType(): " +
                                   "Unable to locate coefficients with key = " +
                                   key);
    }
  }

  /**
   *  No-Arg constructor. This initializes several ParameterList objects.
   */
  public DahleEtAl_1995_AttenRel(ParameterChangeWarningListener warningListener) {

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
   * Calculates the mean of the exceedence probability distribution. The exact
   * formula is: <p>
   *
   */
  public double getMean() throws IMRException {

    double mag, distanceRup;
    String siteTypeValue;

    try {
      mag = ( (Double) magParam.getValue()).doubleValue();
      distanceRup = ( (Double) distanceRupParam.getValue()).doubleValue();
      siteTypeValue = siteTypeParam.getValue().toString();
    }
    catch (NullPointerException e) {
      throw new IMRException(C + ": getMean(): " + ERR);
    }

    // check if distance is beyond the user specified max
    if (distanceRup > USER_MAX_DISTANCE) {
      return VERY_SMALL_MEAN;
    }

    // the following is inefficient if the im Parameter has not been changed in any way
    updateCoefficients();

    double R = Math.sqrt(distanceRup * distanceRup + coeff.rh * coeff.rh);

    int S;
    if (siteTypeValue.equals(SITE_TYPE_ROCK)) {
      S = 0;
    }
    else {
      S = 1;
    }

    // Calculate the log mean
    double mean = coeff.c1 + coeff.c2 * mag + coeff.c3 * Math.log(R) +
        coeff.c4 * R + coeff.c5 * S;

    /* convert to PSV for comparison with their figures (only for tests!):
             if ( coeff.period != 0.0 )
        mean /= (6.28318 /coeff.period);
     */

    // convert units
    String tempName = coeff.name;
    if (tempName.equals("PGA") || tempName.equals("SA/0.0")) {
      mean -= Math.log(9.8);
    }
    else {
      mean += Math.log( (6.28318 / coeff.period) / 9.8);
    }

    // return the result
    return mean;
  }

  /**
   * @return    The stdDev value
   */
  public double getStdDev() throws IMRException {

    String stdDevType = (String) stdDevTypeParam.getValue();

    // this is inefficient if the im has not been changed in any way
    updateCoefficients();

    // set the correct standard deviation depending on component and type
    if (stdDevType.equals(STD_DEV_TYPE_BAY)) {
      return coeff.sigmaBay;
    }
    else {
      return coeff.sigmaLs;
    }

  }

  public void setParamDefaults() {

    //((ParameterAPI)this.iml).setValue( IML_DEFAULT );
    siteTypeParam.setValue(SITE_TYPE_DEFAULT);
    magParam.setValueAsDefault();
    distanceRupParam.setValueAsDefault();
    saParam.setValueAsDefault();
    saPeriodParam.setValueAsDefault();
    saDampingParam.setValueAsDefault();
    pgaParam.setValueAsDefault();
    componentParam.setValueAsDefault();
    stdDevTypeParam.setValueAsDefault();

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
    meanIndependentParams.addParameter(componentParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    stdDevIndependentParams.addParameter(stdDevTypeParam);
    stdDevIndependentParams.addParameter(componentParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    exceedProbIndependentParams.addParameter(distanceRupParam);
    exceedProbIndependentParams.addParameter(siteTypeParam);
    exceedProbIndependentParams.addParameter(magParam);
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
   *  Creates the Vs30 site parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {

    StringConstraint siteConstraint = new StringConstraint();
    siteConstraint.addString(SITE_TYPE_ROCK);
    siteConstraint.addString(SITE_TYPE_SOIL);
    siteConstraint.setNonEditable();
    siteTypeParam = new StringParameter(SITE_TYPE_NAME, siteConstraint, null);
    siteTypeParam.setInfo(SITE_TYPE_INFO);
    siteTypeParam.setNonEditable();

    // add it to the siteParams list:
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

    eqkRuptureParams.clear();
    eqkRuptureParams.addParameter(magParam);

  }

  /**
   *  Creates the single Propagation Effect parameter and adds it to the
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
   *  Creates the two supported IM parameters (PGA and SA), as well as the
   *  independenParameters of SA (periodParam and dampingParam) and adds
   *  them to the supportedIMParams list. Makes the parameters noneditable.
   */
  protected void initSupportedIntensityMeasureParams() {

    // Create saParam's "Period" independent parameter:
    DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
    TreeSet set = new TreeSet();
    Enumeration keys = coefficients.keys();
    while (keys.hasMoreElements()) {
      DahleEtAl_AttenRelCoefficients coeff = (DahleEtAl_AttenRelCoefficients)
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

    // Add the warning listeners:
    saParam.addParameterChangeWarningListener(warningListener);
    pgaParam.addParameterChangeWarningListener(warningListener);

    // Put parameters in the supportedIMParams list:
    supportedIMParams.clear();
    supportedIMParams.addParameter(saParam);
    supportedIMParams.addParameter(pgaParam);

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
    constraint.addString(COMPONENT_UNKNOWN_HORZ);
    constraint.setNonEditable();
    componentParam = new ComponentParam(constraint,COMPONENT_UNKNOWN_HORZ);

    // the stdDevType Parameter
    StringConstraint stdDevTypeConstraint = new StringConstraint();
    stdDevTypeConstraint.addString(STD_DEV_TYPE_BAY);
    stdDevTypeConstraint.addString(STD_DEV_TYPE_LS);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
    stdDevTypeConstraint.setNonEditable();
    stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint, STD_DEV_TYPE_DEFAULT);

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
    DahleEtAl_AttenRelCoefficients coeff = new DahleEtAl_AttenRelCoefficients(
        PGA_Param.NAME,
        0, -1.579, 0.554, -0.560, -0.00302, 0.326, 6.0, 0.75, 0.73);

    // SA/0.00
    DahleEtAl_AttenRelCoefficients coeff0 = new DahleEtAl_AttenRelCoefficients(
        SA_Param.NAME + '/' + (new Double("0.00")).doubleValue(),
        0.00, -1.579, 0.554, -0.560, -0.00302, 0.326, 6.0, 0.75, 0.73);
    // SA/0.025
    DahleEtAl_AttenRelCoefficients coeff1 = new DahleEtAl_AttenRelCoefficients(
        "SA/" + (new Double("0.025")).doubleValue(),
        0.025, -7.106, 0.554, -0.560, -0.00302, 0.326, 6.0, 0.75, 0.73);
    // SA/0.05
    DahleEtAl_AttenRelCoefficients coeff2 = new DahleEtAl_AttenRelCoefficients(
        "SA/" + (new Double("0.05")).doubleValue(),
        0.05, -5.375, 0.449, -0.575, -0.00246, 0.308, 6.0, 0.78, 0.76);
    // SA/0.1
    DahleEtAl_AttenRelCoefficients coeff3 = new DahleEtAl_AttenRelCoefficients(
        "SA/" + (new Double("0.1")).doubleValue(),
        0.1, -4.608, 0.486, -0.609, -0.00198, 0.381, 6.0, 0.81, 0.79);
    // SA/0.2
    DahleEtAl_AttenRelCoefficients coeff4 = new DahleEtAl_AttenRelCoefficients(
        "SA/" + (new Double("0.2")).doubleValue(),
        0.2, -4.746, 0.645, -0.674, -0.00155, 0.470, 6.0, 0.82, 0.80);
    // SA/0.5
    DahleEtAl_AttenRelCoefficients coeff5 = new DahleEtAl_AttenRelCoefficients(
        "SA/" + (new Double("0.5")).doubleValue(),
        0.5, -5.717, 0.920, -0.761, -0.00106, 0.566, 6.0, 0.83, 0.81);
    // SA/1.0
    DahleEtAl_AttenRelCoefficients coeff6 = new DahleEtAl_AttenRelCoefficients(
        "SA/" + (new Double("1.0")).doubleValue(),
        1.0, -6.595, 1.084, -0.792, -0.00075, 0.588, 6.0, 0.82, 0.79);
    // SA/2.0
    DahleEtAl_AttenRelCoefficients coeff7 = new DahleEtAl_AttenRelCoefficients(
        "SA/" + (new Double("2.0")).doubleValue(),
        2.0, -7.205, 1.131, -0.762, -0.00051, 0.536, 6.0, 0.79, 0.75);
    // SA/4.0
    DahleEtAl_AttenRelCoefficients coeff8 = new DahleEtAl_AttenRelCoefficients(
        "SA/" + (new Double("4.0")).doubleValue(),
        4.0, -7.324, 1.009, -0.629, -0.00038, 0.496, 6.0, 0.73, 0.67);

    coefficients.put(coeff.getName(), coeff);
    coefficients.put(coeff0.getName(), coeff0);
    coefficients.put(coeff1.getName(), coeff1);
    coefficients.put(coeff2.getName(), coeff2);
    coefficients.put(coeff3.getName(), coeff3);
    coefficients.put(coeff4.getName(), coeff4);
    coefficients.put(coeff5.getName(), coeff5);
    coefficients.put(coeff6.getName(), coeff6);
    coefficients.put(coeff7.getName(), coeff7);
    coefficients.put(coeff8.getName(), coeff8);

  }

  /**
   *  <b>Title:</b> DahleEtAl_AttenRelCoefficients<br>
   *  <b>Description:</b> This class encapsulates all the
   *  coefficients needed to calculate the Mean and StdDev for
   *  this relationship.<br>
   *  <b>Copyright:</b> Copyright (c) 2001 <br>
   *  <b>Company:</b> <br>
   *
   *
   * @author     Steven W Rock
   * @created    February 27, 2002
   * @version    1.0
   */

  class DahleEtAl_AttenRelCoefficients
      implements NamedObjectAPI {

    protected final static String C = "DahleEtAl_AttenRelCoefficients";
    protected final static boolean D = false;
    /** For serialization. */
    private static final long serialVersionUID = 1234567890987654326L;


    protected String name;
    protected double period = -1;
    protected double c1;
    protected double c2;
    protected double c3;
    protected double c4;
    protected double c5;
    protected double rh;
    protected double sigmaBay;
    protected double sigmaLs;

    /**
     *  Constructor for the DahleEtAl_AttenRelCoefficients object
     *
     * @param  name  Description of the Parameter
     */
    public DahleEtAl_AttenRelCoefficients(String name) {
      this.name = name;
    }

    /**
     *  Constructor for the DahleEtAl_AttenRelCoefficients object that sets all values at once
     *
     * @param  name  Description of the Parameter
     */
    public DahleEtAl_AttenRelCoefficients(String name, double period,
                                          double c1, double c2, double c3,
                                          double c4, double c5,
                                          double rh, double sigmaBay,
                                          double sigmaLs) {
      this.name = name;
      this.period = period;
      this.c1 = c1;
      this.c2 = c2;
      this.c3 = c3;
      this.c4 = c4;
      this.c5 = c5;
      this.rh = rh;
      this.sigmaBay = sigmaBay;
      this.sigmaLs = sigmaLs;
    }

    /**
     *  Gets the name attribute of the BJF_1997_AttenRelCoefficients object
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
      b.append("\n  c1 = " + c1);
      b.append("\n  c2 = " + c2);
      b.append("\n  c3 = " + c3);
      b.append("\n  c4 = " + c4);
      b.append("\n  c5 = " + c5);
      b.append("\n  rh = " + rh);
      b.append("\n  sigmaBay = " + sigmaBay);
      b.append("\n  sigmaLs = " + sigmaLs);
      return b.toString();
    }
  }
}
