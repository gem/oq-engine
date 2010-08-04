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
import org.opensha.commons.param.StringParameter;
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
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;


/**
 * <b>Title:</b> SCEMY_1997_AttenRel<p>
 *
 * <b>Description:</b> This implements the  Attenuation Relationship
 * developed by Sadigh et al. (1997, Seismological Research Letters, vol
 * 68, num 1, pp 180-189) <p>
 *
 * Supported Intensity-Measure Parameters:<p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceRupParam - closest distance to surface projection of fault
 * <LI>siteTypeParam - "Rock" versus "Deep-Soil"
 * <LI>fltTypeParam - Style of faulting ("Reverse" or "Other")
 * <LI>componentParam - Component of shaking (only one)
 * <LI>stdDevTypeParam - The type of standard deviation (only one)
 * </UL><p>
 *
 * @author     Edward (Ned) Field
 * @created    February 27, 2002
 * @version    1.0
 */


public class SadighEtAl_1997_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI {

  private final static String C = "SCEMY_1997_AttenRel";
  private final static boolean D = false;
  public final static String NAME = "Sadigh et al (1997)";
  public final static String SHORT_NAME = "SadighEtAl1997";
  private static final long serialVersionUID = 1234567890987654366L;


  // style of faulting options
  public final static String FLT_TYPE_OTHER = "Other";
  public final static String FLT_TYPE_REVERSE = "Reverse";

  /**
   * Site Type Parameter ("Rock/Shallow-Soil" versus "Deep-Soil")
   */
  private StringParameter siteTypeParam = null;
  public final static String SITE_TYPE_NAME = "Sadigh Site Type";
  // no units
  public final static String SITE_TYPE_INFO =
      "Geological conditions as the site";
  public final static String SITE_TYPE_ROCK = "Rock";
  public final static String SITE_TYPE_SOIL = "Deep-Soil";
  public final static String SITE_TYPE_DEFAULT = "Deep-Soil";

  // warning constraints:
  protected final static Double MAG_WARN_MIN = new Double(4);
  protected final static Double MAG_WARN_MAX = new Double(8.25);
  protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_RUP_WARN_MAX = new Double(100.0);

  /**
   * The current set of coefficients based on the selected intensityMeasure
   */
  private SCEMY_1997_AttenRelCoefficients coeff = null;

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
   * or "Other" otherwise.
   *
   * @param rake                      in degrees
   * @throws InvalidRangeException    If not valid rake angle
   */
  protected void setFaultTypeFromRake(double rake) throws InvalidRangeException {
    FaultUtils.assertValidRake(rake);
    if (rake > 45 && rake < 135) {
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
   * @throws InvalidRangeException    If not valid rake angle
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

    siteTypeParam.setValue((String)site.getParameter(SITE_TYPE_NAME).getValue());
    this.site = site;
    setPropagationEffectParams();

  }

  /**
   * This sets the site and eqkRupture, and the related parameters,
   *  from the propEffect object passed in. Warning constrains are ingored.
   * @param propEffect
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   * @throws InvalidRangeException    If not valid rake angle
   */
  public void setPropagationEffect(PropagationEffect propEffect) throws
      ParameterException, InvalidRangeException {

    this.site = propEffect.getSite();
    this.eqkRupture = propEffect.getEqkRupture();

    siteTypeParam.setValue((String)site.getParameter(SITE_TYPE_NAME).getValue());

    magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
    setFaultTypeFromRake(eqkRupture.getAveRake());

    // set the distance param
    propEffect.setParamValue(distanceRupParam);

  }

  /**
   * This calculates the distanceRupParam value based on the current
   * site and eqkRupture. <P>
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
      coeff = (SCEMY_1997_AttenRelCoefficients) coefficients.get(key.toString());
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
  public SadighEtAl_1997_AttenRel(ParameterChangeWarningListener warningListener) {

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
   * Calculates the mean of the exceedence probability distribution <p>
   *
   * @return    The mean value
   */
  public double getMean() throws IMRException {

    double mag, dist;
    String fltType, siteType, component;

    try {
      mag = ( (Double) magParam.getValue()).doubleValue();
      dist = ( (Double) distanceRupParam.getValue()).doubleValue();
      fltType = fltTypeParam.getValue().toString();
      siteType = siteTypeParam.getValue().toString();
      component = componentParam.getValue().toString();
    }
    catch (NullPointerException e) {
      throw new IMRException(C + ": getMean(): " + ERR);
    }

    // check if distance is beyond the user specified max
    if (dist > USER_MAX_DISTANCE) {
      return VERY_SMALL_MEAN;
    }

//System.out.println("Dist_Rup = " + dist);

    // the following is inefficient if the im Parameter has not been changed in any way
    updateCoefficients();

    // Coefficients that do not depend on intensity measure:
    // NOTE: HARD CODE THESE IN WHEN I KNOW IT'S WORKING
    double c2_rlt = 1.0; // c2 for rock, mag\uFFFD6.5
    double c2_rgt = 1.1; // c2 for rock, mag>6.5
    double c5_rlt = 1.29649;
    double c5_rgt = -0.48451;
    double c6_rlt = 0.250;
    double c6_rgt = 0.524;

    double c1_s_ss = -2.17; // c1 for soil, strike-slip (and normal)
    double c1_s_rv = -1.92; // c1 for soil, reverse faulting
    double c2_s = 1.0;
    double c3_s = 1.7;
    double c4_slt = 2.1863; // soil, mag\uFFFD6.5
    double c4_sgt = 0.3825; // soil, mag>6.5
    double c5_slt = 0.32;
    double c5_sgt = 0.5882;

    double mean;

    // if Site Type is Rock:
    if (siteType.equals(SITE_TYPE_ROCK)) {
      if (mag <= 6.5) {
        mean = coeff.c1_rlt + c2_rlt * mag +
            coeff.c3 * (Math.pow( (8.5 - mag), 2.5)) +
            coeff.c4 * (Math.log(dist + Math.exp(c5_rlt + c6_rlt * mag))) +
            coeff.c7_r * (Math.log(dist + 2));
      }
      else {
        mean = coeff.c1_rgt + c2_rgt * mag +
            coeff.c3 * (Math.pow( (8.5 - mag), 2.5)) +
            coeff.c4 * (Math.log(dist + Math.exp(c5_rgt + c6_rgt * mag))) +
            coeff.c7_r * (Math.log(dist + 2));
      }
      // apply 1.2 factor for reverse faults (ln(1.2)=0.1823)
      if (fltType.equals(FLT_TYPE_REVERSE)) {
        mean = mean + 0.1823;
      }

      // if Site Type is Deep Soil
    }
    else {
      if (mag <= 6.5) {
        mean = c2_s * mag -
            c3_s * Math.log(dist + c4_slt * Math.exp(c5_slt * mag)) +
            coeff.c7_s * Math.pow(8.5 - mag, 2.5);
      }
      else {
        mean = c2_s * mag -
            c3_s * Math.log(dist + c4_sgt * Math.exp(c5_sgt * mag)) +
            coeff.c7_s * Math.pow(8.5 - mag, 2.5);
      }
      // apply fault-type dependent terms:
      if (fltType.equals(FLT_TYPE_REVERSE)) {
        mean += c1_s_rv + coeff.c6_s_rv;
      }
      else {
        mean += c1_s_ss + coeff.c6_s_ss;
      }
    }

    // No longer part of out framework. Always deal with log space
    // Convert back to normal value
    // mean = Math.exp(mean);

    // return the result
    return (mean);
  }

  /**
   * @return    The stdDev value
   */
  public double getStdDev() throws IMRException {

    if (stdDevTypeParam.getValue().equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) {
      return 0;
    }
    else {

      String siteType;
      double mag;

      try {
        siteType = siteTypeParam.getValue().toString();
        mag = ( (Double) magParam.getValue()).doubleValue();
      }
      catch (NullPointerException e) {
        throw new IMRException(C + ": getMean(): " + ERR);
      }

      // this is inefficient if the im has not been changed in any way
      updateCoefficients();

      if (siteType.equals(SITE_TYPE_ROCK)) {
        if (mag <= 7.21) {
          return (coeff.sigma_ri - mag * 0.14);
        }
        else {
          return (coeff.sigma_ri - 1.01); // 1.01=7.21*0.14
        }
      }
      else {
        if (mag <= 7.0) {
          return (coeff.sigma_si - mag * 0.16);
        }
        else {
          return (coeff.sigma_si - 1.12); // 1.12=7.0*0.16
        }
      }
    }
  }

  public void setParamDefaults() {

    siteTypeParam.setValue(SITE_TYPE_DEFAULT);
    magParam.setValueAsDefault();
    fltTypeParam.setValueAsDefault();
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
    meanIndependentParams.clear();
    meanIndependentParams.addParameter(distanceRupParam);
    meanIndependentParams.addParameter(siteTypeParam);
    meanIndependentParams.addParameter(magParam);
    meanIndependentParams.addParameter(fltTypeParam);
    meanIndependentParams.addParameter(componentParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    stdDevIndependentParams.addParameter(stdDevTypeParam);
    stdDevIndependentParams.addParameter(siteTypeParam);
    stdDevIndependentParams.addParameter(magParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    exceedProbIndependentParams.addParameter(distanceRupParam);
    exceedProbIndependentParams.addParameter(siteTypeParam);
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
   *  Creates the site-type parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  /**
   *  Creates the Site-Type parameter and adds it to the siteParams list.
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

    // Create fault-type parameter
    StringConstraint constraint = new StringConstraint();
    constraint.addString(FLT_TYPE_REVERSE);
    constraint.addString(FLT_TYPE_OTHER);
    constraint.setNonEditable();
    fltTypeParam = new FaultTypeParam(constraint,FLT_TYPE_OTHER);

    eqkRuptureParams.clear();
    eqkRuptureParams.addParameter(magParam);
    eqkRuptureParams.addParameter(fltTypeParam);

  }

  /**
   *  Creates the single Propagation Effect parameter and adds it to the
   *  propagationEffectParams list.
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

	  // Create saParam:
    DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
    TreeSet set = new TreeSet();
    Enumeration keys = coefficients.keys();
    while (keys.hasMoreElements()) {
      SCEMY_1997_AttenRelCoefficients coeff = (SCEMY_1997_AttenRelCoefficients)
          coefficients.get(keys.nextElement());
      if (coeff.period >= 0) {
        set.add(new Double(coeff.period));
      }
    }
    Iterator it = set.iterator();
    while (it.hasNext()) {
      periodConstraint.addDouble( (Double) it.next());
    }
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
    constraint.addString(ComponentParam.COMPONENT_AVE_HORZ);
    constraint.setNonEditable();
    componentParam = new ComponentParam(constraint,ComponentParam.COMPONENT_AVE_HORZ);

    // the stdDevType Parameter
    StringConstraint stdDevTypeConstraint = new StringConstraint();
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
    stdDevTypeConstraint.setNonEditable();
    stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);

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
    SCEMY_1997_AttenRelCoefficients coeff = new SCEMY_1997_AttenRelCoefficients(
        PGA_Param.NAME,
        0., -0.624, -1.274, 0.000, -2.100, 0.0, 0.0, 0.0, 0.0, 1.39, 1.52);
    // SA/0.0
    SCEMY_1997_AttenRelCoefficients coeff0 = new
        SCEMY_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                        (new Double("0.0")).doubleValue(),
                                        0.0, -0.624, -1.274, 0.000, -2.100, 0.0,
                                        0.0, 0.0, 0.0, 1.39, 1.52);

    /*        // only for comparing with their figures - 0.03 SA = PGA
            SCEMY_1997_AttenRelCoefficients coeffTEMP = new SCEMY_1997_AttenRelCoefficients( SA_Param.NAME + '/' +( new Double( "0.03" ) ).doubleValue() ,
     0.03, -0.624, -1.274, 0.000, -2.100, 0.0, 0.0, 0.0, 0.0, 1.39, 1.52);
     */
    // SA/0.075
    SCEMY_1997_AttenRelCoefficients coeff1 = new
        SCEMY_1997_AttenRelCoefficients("SA/" +
                                        (new Double("0.075")).doubleValue(),
                                        0.075, 0.110, -0.540, 0.006, -2.128,
                                        -0.082, 0.4572, 0.4572, 0.005, 1.40,
                                        1.54);
    // SA/0.1
    SCEMY_1997_AttenRelCoefficients coeff2 = new
        SCEMY_1997_AttenRelCoefficients("SA/" + (new Double("0.1")).doubleValue(),
                                        0.1, 0.275, -0.375, 0.006, -2.148,
                                        -0.041, 0.6395, 0.6395, 0.005, 1.41,
                                        1.54);
    // SA/0.2
    SCEMY_1997_AttenRelCoefficients coeff3 = new
        SCEMY_1997_AttenRelCoefficients("SA/" + (new Double("0.2")).doubleValue(),
                                        0.2, 0.153, -0.497, -0.004, -2.080, 0.0,
                                        0.9187, 0.9187, -0.004, 1.43, 1.565);
    // SA/0.3
    SCEMY_1997_AttenRelCoefficients coeff4 = new
        SCEMY_1997_AttenRelCoefficients("SA/" + (new Double("0.3")).doubleValue(),
                                        0.3, -0.057, -0.707, -0.017, -2.028,
                                        0.0, 0.9547, 0.9547, -0.014, 1.45, 1.58);
    // SA/0.4
    SCEMY_1997_AttenRelCoefficients coeff5 = new
        SCEMY_1997_AttenRelCoefficients("SA/" + (new Double("0.4")).doubleValue(),
                                        0.4, -0.298, -0.948, -0.028, -1.990,
                                        0.0, 0.9251, 0.9005, -0.024, 1.48,
                                        1.595);
    // SA/0.5
    SCEMY_1997_AttenRelCoefficients coeff6 = new
        SCEMY_1997_AttenRelCoefficients("SA/" + (new Double("0.5")).doubleValue(),
                                        0.5, -0.588, -1.238, -0.040, -1.945,
                                        0.0, 0.8494, 0.8285, -0.033, 1.50, 1.61);
    // SA/0.75
    SCEMY_1997_AttenRelCoefficients coeff7 = new
        SCEMY_1997_AttenRelCoefficients("SA/" +
                                        (new Double("0.75")).doubleValue(),
                                        0.75, -1.208, -1.858, -0.050, -1.865,
                                        0.0, 0.7010, 0.6802, -0.051, 1.52,
                                        1.635);
    // SA/1.0
    SCEMY_1997_AttenRelCoefficients coeff8 = new
        SCEMY_1997_AttenRelCoefficients("SA/" + (new Double("1.0")).doubleValue(),
                                        1.0, -1.705, -2.355, -0.055, -1.800,
                                        0.0, 0.5665, 0.5075, -0.065, 1.53, 1.66);
    // SA/1.5
    SCEMY_1997_AttenRelCoefficients coeff9 = new
        SCEMY_1997_AttenRelCoefficients("SA/" + (new Double("1.5")).doubleValue(),
                                        1.5, -2.407, -3.057, -0.065, -1.725,
                                        0.0, 0.3235, 0.2215, -0.090, 1.53, 1.69);
    // SA/2.0
    SCEMY_1997_AttenRelCoefficients coeff10 = new
        SCEMY_1997_AttenRelCoefficients("SA/" + (new Double("2.0")).doubleValue(),
                                        2.0, -2.945, -3.595, -0.070, -1.670,
                                        0.0, 0.1001, -0.0526, -0.108, 1.53,
                                        1.70);
    // SA/3.0
    SCEMY_1997_AttenRelCoefficients coeff11 = new
        SCEMY_1997_AttenRelCoefficients("SA/" + (new Double("3.0")).doubleValue(),
                                        3.0, -3.700, -4.350, -0.080, -1.610,
                                        0.0, -0.2801, -0.4905, -0.139, 1.53,
                                        1.71);
    // SA/4.0
    SCEMY_1997_AttenRelCoefficients coeff12 = new
        SCEMY_1997_AttenRelCoefficients("SA/" + (new Double("4.0")).doubleValue(),
                                        4.0, -4.230, -4.880, -0.100, -1.570,
                                        0.0, -0.6274, -0.8907, -0.160, 1.53,
                                        1.71);

    coefficients.put(coeff.getName(), coeff);
    coefficients.put(coeff0.getName(), coeff0);
//        coefficients.put( coeffTEMP.getName(), coeffTEMP);    // only for comparing with their figures
    coefficients.put(coeff1.getName(), coeff1);
    coefficients.put(coeff2.getName(), coeff2);
    coefficients.put(coeff3.getName(), coeff3);
    coefficients.put(coeff4.getName(), coeff4);
    coefficients.put(coeff5.getName(), coeff5);
    coefficients.put(coeff6.getName(), coeff6);
    coefficients.put(coeff7.getName(), coeff7);
    coefficients.put(coeff8.getName(), coeff8);
    coefficients.put(coeff9.getName(), coeff9);
    coefficients.put(coeff10.getName(), coeff10);
    coefficients.put(coeff11.getName(), coeff11);
    coefficients.put(coeff12.getName(), coeff12);
  }

  /**
   *  <b>Title:</b> SCEMY_1997_AttenRelCoefficients<br>
   *  <b>Description:</b> This class encapsulates all the
   *  coefficients needed to calculate the Mean and StdDev for
   *  the SCEMY_1997_AttenRel.  One instance of this class holds the set of
   *  coefficients for each period (one row of their table 8).<br>
   *  <b>Copyright:</b> Copyright (c) 2001 <br>
   *  <b>Company:</b> <br>
   *
   *
   * @author     Steven W Rock
   * @created    February 27, 2002
   * @version    1.0
   */

  class SCEMY_1997_AttenRelCoefficients
      implements NamedObjectAPI {

    /*     Coefficient Naming Convention:
             \uFFFDrlt\uFFFD = rock, less than 6.5
             \uFFFDrgt\uFFFD = rock, greater than 6.5
             "s_ss" = soil, strike slip
             "s_rv" = soil, reverse
             "sigma_ri" = slope for rock intercept
             "sigma_si" = slope for soil intercept
     */

    protected final static String C = "SCEMY_1997_AttenRelCoefficients";
    protected final static boolean D = true;
    /** For serialization. */
    private static final long serialVersionUID = 1234567890987654328L;


    protected String name;
    protected double period = -1;
    protected double c1_rlt;
    protected double c1_rgt;
    protected double c3;
    protected double c4;
    protected double c7_r;
    protected double c6_s_ss;
    protected double c6_s_rv;
    protected double c7_s;
    protected double sigma_ri;
    protected double sigma_si;

    /**
     *  Constructor for the SCEMY_1997_AttenRelCoefficients object
     *
     * @param  name  Description of the Parameter
     */
    public SCEMY_1997_AttenRelCoefficients(String name) {
      this.name = name;
    }

    /**
     *  Constructor for the SCEMY_1997_AttenRelCoefficients object that sets all values at once
     *
     * @param  name  Description of the Parameter
     */
    public SCEMY_1997_AttenRelCoefficients(String name, double period,
                                           double c1_rlt, double c1_rgt,
                                           double c3, double c4, double c7_r,
                                           double c6_s_ss, double c6_s_rv,
                                           double c7_s, double sigma_ri,
                                           double sigma_si) {
      this.name = name;
      this.period = period;
      this.c1_rlt = c1_rlt;
      this.c1_rgt = c1_rgt;
      this.c3 = c3;
      this.c4 = c4;
      this.c7_r = c7_r;
      this.c6_s_ss = c6_s_ss;
      this.c6_s_rv = c6_s_rv;
      this.c7_s = c7_s;
      this.sigma_ri = sigma_ri;
      this.sigma_si = sigma_si;
    }

    /**
     *  Gets the name attribute of the SCEMY_1997_AttenRelCoefficients object
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
      b.append("\n  c1_rlt = " + c1_rlt);
      b.append("\n  c1_rgt = " + c1_rgt);
      b.append("\n  c3 = " + c3);
      b.append("\n  c4 = " + c4);
      b.append("\n  c7_r = " + c7_r);
      b.append("\n  c6_s_ss = " + c6_s_ss);
      b.append("\n  c6_s_rv = " + c6_s_rv);
      b.append("\n c7_s = " + c7_s);
      b.append("\n  sigma_ri = " + sigma_ri);
      b.append("\n  sigma_si = " + sigma_si);
      return b.toString();
    }
  }
  
  /**
   * This provides a URL where more info on this model can be obtained
   * @throws MalformedURLException if returned URL is not a valid URL.
   * @returns the URL to the AttenuationRelationship document on the Web.
   */
  public URL getInfoURL() throws MalformedURLException{
	  return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/SadighEtAl_1997.html");
  }

  
}
