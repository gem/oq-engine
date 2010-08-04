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
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceSeisParameter;


/**
 * <b>Title:</b> Campbell_1997_AttenRel<p>
 *
 * <b>Description:</b> This implements the  Attenuation Relationship
 * developed by Campbell (1997, Seismological Research Letters, vol
 * 68, num 1, pp 154-179), as corrected in the Erratum (Campbell, 2000, Seismological
 * Research Letters, vol 71, num 3, pp 352-354)<p>
 *
 * Supported Intensity-Measure Parameters:<p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>pgvParam - Peak Ground Velocity
 * <LI>saParam - Response Spectral Acceleration
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceSeisParam - closest distance to seismogenic part of fault
 * <LI>basinDepthParam - basin depth
 * <LI>siteTypeParam - "Alluvium/Firm-Soil", "Soft Rock", "Hard Rock"
 * <LI>fltTypeParam - Style of faulting
 * <LI>componentParam - Component of shaking
 * <LI>stdDevTypeParam - The type of standard deviation (mag or PGA dependent)
 * </UL><p>
 *
 * @author     Edward H. Field
 * @created    February 27, 2002
 * @version    1.0
 */


public class Campbell_1997_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI {

  public final static String C = "Campbell_1997_AttenRel";
  private final static boolean D = false;
  public final static String NAME = "Campbell (1997) w/ erratum (2000) changes";
  public final static String SHORT_NAME = "Campbell_1997";
  private static final long serialVersionUID = 1234567890987654356L;


  // style of faulting options
  public final static String FLT_TYPE_REVERSE = "Reverse";
  public final static String FLT_TYPE_OTHER = "Other";
  public final static String FLT_TYPE_UNKNOWN = "Unknown";

  /**
   * Site Type Parameter ("Rock/Shallow-Soil" versus "Deep-Soil")
   */
  private StringParameter siteTypeParam = null;
  public final static String SITE_TYPE_NAME = "Campbell Site Type";
  // no units
  public final static String SITE_TYPE_INFO =
      "Geological conditions as the site";
  public final static String SITE_TYPE_FIRM_SOIL = "Firm-Soil";
  public final static String SITE_TYPE_SOFT_ROCK = "Soft-Rock";
  public final static String SITE_TYPE_HARD_ROCK = "Hard-Rock";
  public final static String SITE_TYPE_GEN_ROCK = "Generic-Rock";
  public final static String SITE_TYPE_GEN_SOIL = "Generic-Soil";
  public final static String SITE_TYPE_DEFAULT = "Firm-Soil";

  // warning constraints:
  protected final static Double MAG_WARN_MIN = new Double(5);
  protected final static Double MAG_WARN_MAX = new Double(8);
  protected final static Double DISTANCE_SEIS_WARN_MIN = new Double(3.0);
  protected final static Double DISTANCE_SEIS_WARN_MAX = new Double(60.0);
  // the minimum warning will get overridden by seisDepth is less than seisDepth

  // Override period default because 0.0 is not an option here
  protected final static Double PERIOD_DEFAULT = new Double(0.5);

  /**
   * Campbell's Basin-Depth Parameter, defined as depth (km) to Cretaceous, crystalline
   * basement, 5 km/sec P-wave velicity, or 3 km/sec S-wave velocity.
   */
  protected WarningDoubleParameter basinDepthParam = null;
  public final static String BASIN_DEPTH_NAME = "Campbell-Basin-Depth";
  public final static String BASIN_DEPTH_UNITS = "km";
  public final static String BASIN_DEPTH_INFO =
      "Depth to Cretaceous, crystalline basement, or 3 km/sec S-wave velocity";
  protected final static Double BASIN_DEPTH_DEFAULT = new Double(5.0);
  protected final static Double BASIN_DEPTH_MIN = new Double(0);
  protected final static Double BASIN_DEPTH_MAX = new Double(30);
  protected final static Double BASIN_DEPTH_WARN_MIN = new Double(0);
  protected final static Double BASIN_DEPTH_WARN_MAX = new Double(10);

  /**
   * The current set of coefficients based on the selected intensityMeasure
   */
  private Campbell_1997_AttenRelCoefficients coeff = null;

  /**
   *  Hashtable of coefficients for the supported intensityMeasures
   */
  protected Hashtable coefficients = new Hashtable();

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   * Determines the style of faulting from the rake angle (which
   * comes from the eqkRupture object) and fills in the
   * value of the fltTypeParam.  Options are "Reverse" if 157.5>rake>22.5
   * or "Other" otherwise.
   *
   * @param rake                      in degrees
   * @throws InvalidRangeException    If not valid rake angle
   */
  protected void setFaultTypeFromRake(double rake) throws InvalidRangeException {
    FaultUtils.assertValidRake(rake);
    if (rake >= 22.5 && rake <= 157.5) {
      fltTypeParam.setValue(FLT_TYPE_REVERSE);
    }
    else {
      fltTypeParam.setValue(FLT_TYPE_OTHER);
    }
//        NOTE: FLT_TYPE_UNKNOWN is not possible unless rake can == null, which it can't
//        because rake is a double in EqkRupture (although it could equal NaN);
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
   *  This sets the site-type and basin-depth parameters based on what is in
   *  the Site object passed in (the Site object must have these parameters in it).
   *  This also sets the internally held Site object as that passed in.
   * WarningExceptions are ingored.
   *
   * @param  site             The new site object which contains the
   * "Campbell Site Type" and "Campbell Basin Depth" Parameters
   * @throws ParameterException Thrown if the Site object doesn't contain
   * either of these parameters.
   */
  public void setSite(Site site) throws ParameterException {

    siteTypeParam.setValue((String)site.getParameter(SITE_TYPE_NAME).getValue());
    basinDepthParam.setValueIgnoreWarning((Double)site.getParameter(BASIN_DEPTH_NAME).
                                          getValue());
    this.site = site;
    setPropagationEffectParams();

  }

  /**
   * This sets the site and eqkRupture, and the related parameters,
   * from the propEffect object passed in. Warning constrains are ingored.
   * @param propEffect
   * @throws ParameterException : Thrown if the Site object doesn't contain
   * "Campbell Site Type" and "Campbell Basin Depth" Parameters
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setPropagationEffect(PropagationEffect propEffect) throws
      ParameterException, InvalidRangeException {

    this.site = propEffect.getSite();
    this.eqkRupture = propEffect.getEqkRupture();

    siteTypeParam.setValue((String)site.getParameter(SITE_TYPE_NAME).getValue());
    basinDepthParam.setValueIgnoreWarning((Double)site.getParameter(BASIN_DEPTH_NAME).
                                          getValue());

    magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
    setFaultTypeFromRake(eqkRupture.getAveRake());

    propEffect.setParamValue(distanceSeisParam);

  }

  /**
   * This sets the DistanceSeis propagation effect parameter based on the current
   * site and eqkRupture. <P>
   */
  protected void setPropagationEffectParams() {

    if ( (this.site != null) && (this.eqkRupture != null)) {
      distanceSeisParam.setValue(eqkRupture, site);
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

    // Only SA coefficients here (PGA and PGV are hard coded because they're different)
    StringBuffer key = new StringBuffer(im.getName() + "/" +
                                        saPeriodParam.getValue());
    if (coefficients.containsKey(key.toString())) {
      coeff = (Campbell_1997_AttenRelCoefficients) coefficients.get(key.
          toString());
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
  public Campbell_1997_AttenRel(ParameterChangeWarningListener warningListener) {

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
   * @return    The mean value
   */
  public double getMean() throws IMRException {

    double mag, dist, depth, F, mean, lnPGA;
    String fltType, siteType, component, im_name;

    Double tempDepth;

    // default is alluvium
    double S_sr = 0.0;
    double S_hr = 0.0;

    try {
      mag = ( (Double) magParam.getValue()).doubleValue();
      dist = ( (Double) distanceSeisParam.getValue()).doubleValue();
      tempDepth = (Double) basinDepthParam.getValue();
      fltType = fltTypeParam.getValue().toString();
      siteType = siteTypeParam.getValue().toString();
      component = componentParam.getValue().toString();
      im_name = im.getName();
    }
    catch (NullPointerException e) {
      throw new IMRException(C + ": getMean(): " + ERR);
    }

    // check if distance is beyond the user specified max
    if (dist > USER_MAX_DISTANCE) {
      return VERY_SMALL_MEAN;
    }

    if (fltType.equals(FLT_TYPE_REVERSE)) {
      F = 1.0;
    }
    else if (fltType.equals(FLT_TYPE_OTHER)) {
      F = 0.0;
    }
    else {
      F = 0.5; // if "Unknown"
    }

    if (siteType.equals(SITE_TYPE_SOFT_ROCK)) {
      S_sr = 1.0;
    }
    else if (siteType.equals(SITE_TYPE_HARD_ROCK)) {
      S_hr = 1.0;
    }
    else if (siteType.equals(SITE_TYPE_GEN_ROCK)) {
      S_sr = 1.0; // S_hr = stays zero
    }
    // both stay zero if SITE_TYPE_FIRM_SOIL or SITE_TYPE_GEN_SOIL

    // set basin depth
    if (tempDepth != null) {
      depth = tempDepth.doubleValue();
    }
    else {
      if (S_hr == 1.0) {
        depth = 0;
      }
      else if (S_sr == 1.0) {
        depth = 1.0;
      }
      else {
        depth = 5.0;
      }
    }

    // Override basin depth if it's generic rock or generic soil
    if (siteType.equals(SITE_TYPE_GEN_ROCK)) {
      depth = 1;
    }
    if (siteType.equals(SITE_TYPE_GEN_SOIL)) {
      depth = 5;
    }

    // Get horizontal PGA (which all depend on):
    lnPGA = -3.512 + 0.904 * mag -
        1.328 * 0.5 * Math.log(dist * dist + 0.0222 * Math.exp(1.294 * mag)) +
        (1.125 - 0.112 * Math.log(dist) - 0.0957 * mag) * F +
        (0.44 - 0.171 * Math.log(dist)) * S_sr +
        (0.405 - 0.222 * Math.log(dist)) * S_hr;
    if (depth <= 1.0) {
      lnPGA += (0.405 - 0.222 * Math.log(dist) -
                (0.44 - 0.171 * Math.log(dist)) * S_sr) * (1.0 - depth) *
          (1.0 - S_hr);
    }

    // Do PGA first:
    if (im_name.equals(PGA_Param.NAME)) {
      if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
        mean = lnPGA;
      }
      else { // vertical component
        mean = lnPGA - 1.58 - 0.1 * mag -
            1.5 * Math.log(dist + 0.079 * Math.exp(0.661 * mag)) +
            1.89 * Math.log(dist + 0.361 * Math.exp(0.576 * mag)) -
            0.11 * F;
      }
    }

    // Now do SA:
    else if (im_name.equals(SA_Param.NAME)) {

      //check whether it's the zero period case (for which there are not coeffs)
      double period = ( (Double) saPeriodParam.getValue()).doubleValue();

      if (period == 0.0) { // do same as for PGA
        if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
          mean = lnPGA;
        }
        else { // vertical component
          mean = lnPGA - 1.58 - 0.1 * mag -
              1.5 * Math.log(dist + 0.079 * Math.exp(0.661 * mag)) +
              1.89 * Math.log(dist + 0.361 * Math.exp(0.576 * mag)) -
              0.11 * F;
        }
      }
      else {
        // compute Horizontal case:
        updateCoefficients();
        mean = lnPGA + coeff.c1_h + coeff.c2_h * tanh(coeff.c3_h * (mag - 4.7)) +
            (coeff.c4_h + coeff.c5_h * mag) * dist + 0.5 * coeff.c6 * S_sr +
            coeff.c6 * S_hr +
            coeff.c7 * tanh(coeff.c8 * depth) * (1 - S_hr);
        if (depth < 1.) {
          mean += coeff.c6 * (1.0 - depth) * (1.0 - 0.5 * S_sr) * (1.0 - S_hr);
        }

        // check if vertical component desired
        if (component.equals(ComponentParam.COMPONENT_VERT)) {
          mean += coeff.c1_v - 0.1 * mag + coeff.c2_v * tanh(0.71 * (mag - 4.7)) +
              coeff.c3_v * tanh(0.66 * (mag - 4.7)) -
              1.50 * Math.log(dist + 0.079 * Math.exp(0.661 * mag)) +
              1.89 * Math.log(dist + 0.361 * Math.exp(0.576 * mag)) - 0.11 * F +
              (coeff.c4_v * tanh(0.51 * depth) + coeff.c5_v * tanh(0.57 * depth)) *
              (1 - S_hr);
        }
      }
    }

    // Now do PGV:
    else {
      // compute horizontal case
      mean = lnPGA + 0.26 + 0.29 * mag -
          1.44 * Math.log(dist + 0.0203 * Math.exp(0.958 * mag)) +
          1.89 * Math.log(dist + 0.361 * Math.exp(0.576 * mag)) +
          (0.0001 - 0.000565 * mag) * dist - 0.12 * F - 0.15 * S_sr -
          0.30 * S_hr + 0.75 * tanh(0.51 * depth) * (1 - S_hr);
      if (depth < 1.) {
        mean -= 0.3 * (1.0 - depth) * (1.0 - 0.5 * S_sr) * (1.0 - S_hr);
      }
      // check if vertical component desired
      if (component.equals(ComponentParam.COMPONENT_VERT)) {
        mean += -2.15 + 0.07 * mag -
            1.24 * Math.log(dist + 0.00394 * Math.exp(1.17 * mag)) +
            1.44 * Math.log(dist + 0.0203 * Math.exp(0.958 * mag)) + 0.1 * F +
            (0.46 * tanh(2.68 * depth) - 0.53 * tanh(0.47 * depth)) * (1 - S_hr);
      }
    }

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

      String fltType, siteType, component, im_name, stdevType;
      double mag, dist, sigma, pga, depth, F;

      double S_hr = 0;
      double S_sr = 0;

      try {
        mag = ( (Double) magParam.getValue()).doubleValue();
        component = componentParam.getValue().toString();
        im_name = im.getName();
        stdevType = stdDevTypeParam.getValue().toString();
      }
      catch (NullPointerException e) {
        throw new IMRException(C + ": getMean(): " + ERR);
      }

      // First find Horz PGA sigma:

      // mag dependent case:
      if (stdevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL_MAG_DEP)) {
        if (mag < 7.4) {
          sigma = 0.889 - 0.0691 * mag;
        }
        else {
          sigma = 0.38;
        }
      }

      // PGA dependent case:
      else {
        try {
          dist = ( (Double) distanceSeisParam.getValue()).doubleValue();
          depth = ( (Double) basinDepthParam.getValue()).doubleValue();
          fltType = fltTypeParam.getValue().toString();
          siteType = siteTypeParam.getValue().toString();
        }
        catch (NullPointerException e) {
          throw new IMRException(C + ": getMean(): " + ERR);
        }

        if (fltType.equals(FLT_TYPE_REVERSE)) {
          F = 1.0;
        }
        else if (fltType.equals(FLT_TYPE_OTHER)) {
          F = 0.0;
        }
        else {
          F = 0.0; // if "Unknown"
        }

        if (siteType.equals(SITE_TYPE_SOFT_ROCK)) {
          S_sr = 1.0;
        }
        else if (siteType.equals(SITE_TYPE_HARD_ROCK)) {
          S_hr = 1.0;
        }

        // Get horz PGA (which all depend on):
        pga = -3.512 + 0.904 * mag -
            1.328 * 0.5 * Math.log(dist * dist + 0.0222 * Math.exp(1.294 * mag)) +
            (1.125 - 0.112 * Math.log(dist) - 0.0957 * mag) * F +
            (0.44 - 0.171 * Math.log(dist)) * S_sr +
            (0.405 - 0.222 * Math.log(dist)) * S_hr;
        if (depth <= 1.0) {
          pga += (0.405 - 0.222 * Math.log(dist) -
                  (0.44 - 0.171 * Math.log(dist)) * S_sr) * (1.0 - depth) *
              (1.0 - S_hr);
        }

        pga = Math.exp(pga);

        // now set sigma
        if (pga < 0.068) {
          sigma = 0.55;
        }
        else if (pga >= 0.068 && pga < 0.21) {
          sigma = 0.173 - 0.140 * Math.log(pga);
        }
        else {
          sigma = 0.39;
        }
      }

      // now return value depending on component and im_name

      // Do PGA first:
      if (im_name.equals(PGA_Param.NAME)) {
        if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
          return (sigma);
        }
        else { // vertical component
          return (Math.pow(sigma * sigma + 0.1296, 0.5));
        }
      }

      // Now do SA:
      else if (im_name.equals(SA_Param.NAME)) {
        // make same as PGA if period = zero
        double period = ( (Double) saPeriodParam.getValue()).doubleValue();
        if (period == 0) {
          if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
            return (sigma);
          }
          else { // vertical component
            return (Math.pow(sigma * sigma + 0.1296, 0.5));
          }
        }
        else {
          // compute horz comp SA sigma:
          sigma = Math.pow(sigma * sigma + 0.0729, 0.5);
          if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
            return (sigma);
          }
          else { // vertical component
            return (Math.pow(sigma * sigma + 0.1521, 0.5));
          }
        }
      }

      // Now do PGV:
      else {
        // compute horz comp PGV sigma:
        sigma = Math.pow(sigma * sigma + 0.0036, 0.5);
        if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
          return (sigma);
        }
        else { // vertical component
          return (Math.pow(sigma * sigma + 0.09, 0.5));
        }
      }
    }
  }

  // Hyperbolic funtion
  private double tanh(double x) {
    return (Math.exp(x) - Math.exp( -x)) / (Math.exp(x) + Math.exp( -x));
  }

  public void setParamDefaults() {

    siteTypeParam.setValue(SITE_TYPE_DEFAULT);
    magParam.setValueAsDefault();
    fltTypeParam.setValueAsDefault();
    distanceSeisParam.setValueAsDefault();
    basinDepthParam.setValue(BASIN_DEPTH_DEFAULT);
    saParam.setValueAsDefault();
    saPeriodParam.setValueAsDefault();
    saDampingParam.setValueAsDefault();
    pgaParam.setValueAsDefault();
    pgvParam.setValueAsDefault();
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
    meanIndependentParams.addParameter(distanceSeisParam);
    meanIndependentParams.addParameter(siteTypeParam);
    meanIndependentParams.addParameter(basinDepthParam);
    meanIndependentParams.addParameter(magParam);
    meanIndependentParams.addParameter(fltTypeParam);
    meanIndependentParams.addParameter(componentParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    stdDevIndependentParams.addParameter(stdDevTypeParam);
    stdDevIndependentParams.addParameter(distanceSeisParam);
    stdDevIndependentParams.addParameter(siteTypeParam);
    stdDevIndependentParams.addParameter(basinDepthParam);
    stdDevIndependentParams.addParameter(magParam);
    stdDevIndependentParams.addParameter(fltTypeParam);
    stdDevIndependentParams.addParameter(componentParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    exceedProbIndependentParams.addParameter(distanceSeisParam);
    exceedProbIndependentParams.addParameter(siteTypeParam);
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
   *  Creates the Site-Type parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {

    StringConstraint siteConstraint = new StringConstraint();
    siteConstraint.addString(SITE_TYPE_FIRM_SOIL);
    siteConstraint.addString(SITE_TYPE_SOFT_ROCK);
    siteConstraint.addString(SITE_TYPE_HARD_ROCK);
    siteConstraint.addString(SITE_TYPE_GEN_ROCK);
    siteConstraint.addString(SITE_TYPE_GEN_SOIL);
    siteConstraint.setNonEditable();
    siteTypeParam = new StringParameter(SITE_TYPE_NAME, siteConstraint, null);
    siteTypeParam.setInfo(SITE_TYPE_INFO);
    siteTypeParam.setNonEditable();

    DoubleConstraint basinDepthConstraint = new DoubleConstraint(
        BASIN_DEPTH_MIN, BASIN_DEPTH_MAX);
    basinDepthConstraint.setNullAllowed(true);
    basinDepthConstraint.setNonEditable();
    basinDepthParam = new WarningDoubleParameter(BASIN_DEPTH_NAME,
                                                 basinDepthConstraint,
                                                 BASIN_DEPTH_UNITS);
    basinDepthParam.setInfo(BASIN_DEPTH_INFO);
    basinDepthParam.setNonEditable();

    siteParams.clear();
    siteParams.addParameter(siteTypeParam);
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
    constraint.addString(FLT_TYPE_REVERSE);
    constraint.addString(FLT_TYPE_OTHER);
    constraint.addString(FLT_TYPE_UNKNOWN);
    constraint.setNonEditable();
    fltTypeParam = new FaultTypeParam(constraint,FLT_TYPE_OTHER);

    eqkRuptureParams.clear();
    eqkRuptureParams.addParameter(magParam);
    eqkRuptureParams.addParameter(fltTypeParam);

  }

  /**
   *  Creates the Propagation Effect parameters and adds them to the
   *  propagationEffectParams list. Makes the parameters noneditable.
   */
  protected void initPropagationEffectParams() {

    distanceSeisParam = new DistanceSeisParameter(3.0);
    distanceSeisParam.addParameterChangeWarningListener(warningListener);
    DoubleConstraint warn = new DoubleConstraint(DISTANCE_SEIS_WARN_MIN,
                                                 DISTANCE_SEIS_WARN_MAX);
    warn.setNonEditable();
    distanceSeisParam.setWarningConstraint(warn);
    distanceSeisParam.setNonEditable();
    propagationEffectParams.addParameter(distanceSeisParam);
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
    Enumeration keys = coefficients.keys(); // same as for vertCoeffs
    while (keys.hasMoreElements()) {
      Campbell_1997_AttenRelCoefficients coeff = (
          Campbell_1997_AttenRelCoefficients) coefficients.get(keys.nextElement());
      if (coeff.period >= 0) {
        set.add(new Double(coeff.period));
      }
    }
    // add the zero period by hand since there are no corresponding coefficients
    periodConstraint.addDouble(new Double(0.0));
    // now add the list of periods from the coefficients
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
    constraint.addString(ComponentParam.COMPONENT_VERT);
    constraint.setNonEditable();
    componentParam = new ComponentParam(constraint,componentParam.COMPONENT_AVE_HORZ);

    // the stdDevType Parameter
    StringConstraint stdDevTypeConstraint = new StringConstraint();
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL_MAG_DEP);
    stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL_PGA_DEP);
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
   *  at 1.00 second period is "SA/1.00".
   */
  protected void initCoefficients() {

    String S = C + ": initCoefficients():";
    if (D) {
      System.out.println(S + "Starting");
    }

    coefficients.clear();

    // There are no coefficients for PGA or PGV because these are hard wired in the code
    // SA/0.05
    Campbell_1997_AttenRelCoefficients coeff0 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("0.05")).doubleValue(),
                                           0.05, 0.05, 0.0, 0.0, -0.0011,
                                           0.000055, 0.20, 0.0, 0.0, -1.32, 0.0,
                                           0.0, 0.0, 0.0);
    // SA/0.075
    Campbell_1997_AttenRelCoefficients coeff1 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("0.075")).doubleValue(),
                                           0.075, 0.27, 0.0, 0.0, -0.0024,
                                           0.000095, 0.22, 0.0, 0.0, -1.21, 0.0,
                                           0.0, 0.0, 0.0);
    // SA/0.1
    Campbell_1997_AttenRelCoefficients coeff2 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("0.1")).doubleValue(),
                                           0.1, 0.48, 0.0, 0.0, -0.0024,
                                           0.000007, 0.14, 0.0, 0.0, -1.29, 0.0,
                                           0.0, 0.0, 0.0);
    // SA/0.15
    Campbell_1997_AttenRelCoefficients coeff3 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("0.15")).doubleValue(),
                                           0.15, 0.72, 0.0, 0.0, -0.0010,
                                           -0.00027, -0.02, 0.0, 0.0, -1.57,
                                           0.0, 0.0, 0.0, 0.0);
    // SA/0.2
    Campbell_1997_AttenRelCoefficients coeff4 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("0.2")).doubleValue(),
                                           0.2, 0.79, 0.0, 0.0, 0.0011,
                                           -0.00053, -0.18, 0.0, 0.0, -1.73,
                                           0.0, 0.0, 0.0, 0.0);
    // SA/0.3
    Campbell_1997_AttenRelCoefficients coeff5 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("0.3")).doubleValue(),
                                           0.3, 0.77, 0.0, 0.0, 0.0035,
                                           -0.00072, -0.40, 0.0, 0.0, -1.98,
                                           0.0, 0.0, 0.0, 0.0);
    // SA/0.5
    Campbell_1997_AttenRelCoefficients coeff6 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("0.5")).doubleValue(),
                                           0.5, -0.28, 0.74, 0.66, 0.0068,
                                           -0.001, -0.42, 0.25, 0.62, -2.03,
                                           0.46, -0.74, 0.0, 0.0);
    // SA/0.75
    Campbell_1997_AttenRelCoefficients coeff7 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("0.75")).doubleValue(),
                                           0.75, -1.08, 1.23, 0.66, 0.0077,
                                           -0.001, -0.44, 0.37, 0.62, -1.79,
                                           0.67, -1.23, 0.0, 0.0);
    // SA/1.0
    Campbell_1997_AttenRelCoefficients coeff8 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("1.0")).doubleValue(),
                                           1.0, -1.79, 1.59, 0.66, 0.0085,
                                           -0.001, -0.38, 0.57, 0.62, -1.82,
                                           1.13, -1.59, 0.18, -0.18);
    // SA/1.5
    Campbell_1997_AttenRelCoefficients coeff9 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("1.5")).doubleValue(),
                                           1.5, -2.65, 1.98, 0.66, 0.0094,
                                           -0.001, -0.32, 0.72, 0.62, -1.81,
                                           1.52, -1.98, 0.57, -0.49);
    // SA/2.0
    Campbell_1997_AttenRelCoefficients coeff10 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("2.0")).doubleValue(),
                                           2.0, -3.28, 2.23, 0.66, 0.0100,
                                           -0.001, -0.36, 0.83, 0.62, -1.65,
                                           1.65, -2.23, 0.61, -0.63);
    // SA/3.0
    Campbell_1997_AttenRelCoefficients coeff11 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("3.0")).doubleValue(),
                                           3.0, -4.07, 2.39, 0.66, 0.0108,
                                           -0.001, -0.22, 0.86, 0.62, -1.31,
                                           1.28, -2.39, 1.07, -0.84);
    // SA/4.0
    Campbell_1997_AttenRelCoefficients coeff12 = new
        Campbell_1997_AttenRelCoefficients(SA_Param.NAME + '/' +
                                           (new Double("4.0")).doubleValue(),
                                           4.0, -4.26, 2.03, 0.66, 0.0112,
                                           -0.001, -0.30, 1.05, 0.62, -1.35,
                                           1.15, -2.03, 1.26, -1.17);

    coefficients.put(coeff0.getName(), coeff0);
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
   *  <b>Title:</b> Campbell_1997_AttenRelCoefficients<br>
   *  <b>Description:</b> This class encapsulates all the
   *  coefficients needed to calculate the Mean and StdDev for
   *  the Campbell_1997_AttenRel.  One instance of this class holds the set of
   *  coefficients for each period (one row of his table 5 & 6).<br>
   *  <b>Copyright:</b> Copyright (c) 2001 <br>
   *  <b>Company:</b> <br>
   *
   *
   * @author     Steven W Rock
   * @created    February 27, 2002
   * @version    1.0
   */

  class Campbell_1997_AttenRelCoefficients
      implements NamedObjectAPI {

    protected final static String C = "Campbell_1997_AttenRelCoefficients";
    protected final static boolean D = true;
    /** For serialization. */
    private static final long serialVersionUID = 1234567890987654324L;


    protected String name;
    protected double period = -1;
    protected double c1_h;
    protected double c2_h;
    protected double c3_h;
    protected double c4_h;
    protected double c5_h;
    protected double c6;
    protected double c7;
    protected double c8;
    protected double c1_v;
    protected double c2_v;
    protected double c3_v;
    protected double c4_v;
    protected double c5_v;

    /**
     *  Constructor for the Campbell_1997_AttenRelCoefficients object
     *
     * @param  name  Description of the Parameter
     */
    public Campbell_1997_AttenRelCoefficients(String name) {
      this.name = name;
    }

    /**
     *  Constructor for the Campbell_1997_AttenRelCoefficients object that sets all values at once
     *
     * @param  name  Description of the Parameter
     */
    public Campbell_1997_AttenRelCoefficients(String name, double period,
                                              double c1_h, double c2_h,
                                              double c3_h, double c4_h,
                                              double c5_h,
                                              double c6, double c7, double c8,
                                              double c1_v, double c2_v,
                                              double c3_v, double c4_v,
                                              double c5_v) {
      this.period = period;
      this.name = name;
      this.c1_h = c1_h;
      this.c2_h = c2_h;
      this.c3_h = c3_h;
      this.c4_h = c4_h;
      this.c5_h = c5_h;
      this.c6 = c6;
      this.c7 = c7;
      this.c8 = c8;
      this.c1_v = c1_v;
      this.c2_v = c2_v;
      this.c3_v = c3_v;
      this.c4_v = c4_v;
      this.c5_v = c5_v;
    }

    /**
     *  Gets the name attribute of the Campbell_1997_AttenRelCoefficients object
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
      b.append("\n  c1_h = " + c1_h);
      b.append("\n  c2_h = " + c2_h);
      b.append("\n  c3_h = " + c3_h);
      b.append("\n  c4_h = " + c4_h);
      b.append("\n  c5_h = " + c5_h);
      b.append("\n  c6 = " + c6);
      b.append("\n  c7 = " + c7);
      b.append("\n  c8 = " + c8);
      b.append("\n  c1_v = " + c1_v);
      b.append("\n  c2_v = " + c2_v);
      b.append("\n  c3_v = " + c3_v);
      b.append("\n  c4_v = " + c4_v);
      b.append("\n  c5_v = " + c5_v);
      return b.toString();
    }
  }
  
  /**
   * This provides a URL where more info on this model can be obtained
   * @throws MalformedURLException if returned URL is not a valid URL.
   * @returns the URL to the AttenuationRelationship document on the Web.
   */
  public URL getInfoURL() throws MalformedURLException{
	  return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/Campbell_1997.html");
  }
    
}
