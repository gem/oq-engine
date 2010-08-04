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

package org.opensha.sha.imr.attenRelImpl.depricated;

import java.util.HashMap;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.DipParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RakeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupTopDepthParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusJB_OverRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <b>Title:</b> AS_2005_prelim_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship
 * developed by Abrahmson and Silva (2005 <p>
 *
 * Supported Intensity-Measure Parameters:  BELOW NEEDS TO BE UPDATED<p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceRupParam - closest distance to surface projection of fault
 * <LI>siteTypeParam - "Rock/Shallow-Soil" versus "Deep-Soil"
 * <LI>fltTypeParam - Style of faulting
 * <LI>isOnHangingWallParam - tells if site is directly over the rupture surface
 * <LI>componentParam - Component of shaking (only one)
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL><p>
 *
 * @author     Edward H. Field
 * @created    April, 2002
 * @version    1.0
 */


public class AS_2005_prelim_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI, ParameterChangeListener {

  // Debugging stuff
  private final static String C = "AS_2005_prelim_AttenRel";
  private final static boolean D = false;
  public final static String SHORT_NAME = "AS2005";
  private static final long serialVersionUID = 1234567890987654352L;

 

  // Name of IMR
  public final static String NAME = "Abrahamson & Silva (2005 prelim)";

  // coefficients:

  private static double[] period = {
      0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25,
      0.3, 0.4, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5};
  private static double[] vref = {
      865.1, 865.1, 865.1, 907.8, 994.5, 1053.5, 1085.7, 1032.5, 877.6, 748.2,
      654.3, 587.1, 503, 456.6, 410.5, 400, 400, 400, 400, 400, 400};
  private static double[] b_soil = {
      -1.186, -1.186, -1.219, -1.273, -1.308, -1.346, -1.471, -1.624, -1.931,
      -2.188, -2.381, -2.518, -2.657, -2.669, -2.401, -1.955, -1.025, -0.299, 0,
      0, 0};
  private static double[] c0 = {
      6.4, 6.7, 6.6, 6.4, 6.7, 7.1, 8.3, 9.6, 10.3, 9.5, 8.7, 7.3, 6.8, 6.1,
      3.8, 3.6,
      2.7, 2.4, 3.9, 5.1, 6.1};
  private static double[] c1 = {
      1.283, 1.2474, 1.2808, 1.3632, 1.4936, 1.6645, 2.1555, 2.5918, 2.87,
      2.7123,
      2.5164, 2.2411, 2.0442, 1.9085, 1.3589, 1.0968, 0.5499, 0.0308, -0.0884,
      -0.2875, -0.3686};
  private static double[] c2 = {
      -0.9841, -0.9704, -0.9771, -0.9969, -1.0286, -1.0637, -1.1423, -1.2036,
      -1.1957, -1.1051, -1.0301, -0.9411, -0.883, -0.8539, -0.7629, -0.7397,
      -0.6657, -0.6195, -0.7102, -0.7218, -0.7683};
  private static double[] c3 = {
      -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2,
      -0.2,
      -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2};
  private static double[] c5 = {
      0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
      0.05,
      0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05};
  private static double[] c6 = {
      0.01, 0.0112, 0.0118, 0.0131, 0.0163, 0.0194, 0.0281, 0.0282, 0.0218,
      0.0068,
      -0.0056, -0.0158, -0.0293, -0.0469, -0.0687, -0.0874, -0.1146, -0.1282,
      -0.1574, -0.1916, -0.1994};
  private static double[] c7 = {
      0.2601, 0.2491, 0.2511, 0.2512, 0.236, 0.2297, 0.1891, 0.1719, 0.1894,
      0.2071, 0.2327, 0.2282, 0.22, 0.2364, 0.2589, 0.268, 0.2012, 0.2527,
      0.2511, 0.1449, 0.0998};
  private static double[] c8 = {
      -0.09, -0.09, -0.09, -0.09, -0.09, -0.09, -0.09, -0.09, -0.09, -0.09,
      -0.09, -0.09, -0.09, -0.09, -0.09, -0.09, -0.09, -0.09, -0.09, -0.09,
      -0.09};
  private static double[] c9 = {
      0.213, 0.1986, 0.2084, 0.2389, 0.2495, 0.2748, 0.2351, 0.2122, 0.1978,
      0.1531, 0.0514, -0.0102, -0.0246, -0.0299, -0.0193, 0.0178, -0.0019,
      0.0336, 0.1418, 0.321, 0.2559};
  private static double[] c10 = {
      0.9475, 0.949, 0.9898, 1.054, 1.0943, 1.1456, 1.3126, 1.4806, 1.8391,
      2.1163, 2.319, 2.4505, 2.5833, 2.558, 2.1441, 1.533, 0.3399, -0.5625,
      -0.8821, -0.8508, -0.7994};
  private static double[] c11 = {
      0.0647, 0.0546, 0.0557, 0.0583, 0.064, 0.0694, 0.0628, 0.0566, 0.0458,
      0.0286, 0.0511, 0.05, 0.0491, 0.0385, 0.0227, 0.0294, 0.0222, 0.0667,
      0.0262, 0.0272, 0.0073};
  private static double[] c12 = {
      0.0245, 0.0245, 0.0248, 0.0254, 0.0259, 0.0274, 0.0291, 0.0291,
      0.0314, 0.029, 0.0288, 0.0277, 0.0181, 0.019, 0.0077, -0.003, -0.0189,
      -0.0264, -0.0275, -0.0385, -0.0377};
  private static double[] sigma0 = {
      0.5065, 0.509, 0.5106, 0.5176, 0.5249, 0.5313, 0.5476, 0.558, 0.556,
      0.5465, 0.5458,
      0.5521, 0.5499, 0.5604, 0.5809, 0.598, 0.6156, 0.6159, 0.5719, 0.58,
      0.5889};
  private static double[] tau0 = {
      0.3281, 0.326, 0.3304, 0.3443, 0.3573, 0.3796, 0.4044, 0.4008, 0.3929,
      0.3657,
      0.3507, 0.336, 0.3504, 0.377, 0.3535, 0.3614, 0.3795, 0.4161, 0.4935,
      0.4882, 0.5652};
  private static double[] tauCorr = {
      1.0, 0.99, 0.99, 0.98, 0.97, 0.95, 0.93, 0.92, 0.92, 0.92, 0.91, 0.89,
      0.85, 0.82,
      0.68, 0.57, 0.45, 0.28, 0.28, 0.17, 0.17};

  private static double n = 1.18, c = 1.88;

  private HashMap indexFromPerHashMap;

  private int iper;
  private double vs30, rjb, rRup, distRupJB_Fraction, aspectratio, rake, dip,
      mag, srcSiteA, depthTop;
  private String stdDevType;
  private boolean parameterChange;
  private double mean, stdDev;

  // ?????????????????????????????????????
  protected final static Double MAG_WARN_MIN = new Double(4.5);
  protected final static Double MAG_WARN_MAX = new Double(8.5);
  protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_RUP_WARN_MAX = new Double(200.0);
  protected final static Double VS30_WARN_MIN = new Double(180.0);
  protected final static Double VS30_WARN_MAX = new Double(3500.0);

  /**
   * srcSiteAngle parameter - .  This is created in the
   * initPropEffectParams method.
   */
  protected DoubleParameter srcSiteAngleParam = null;
  public final static String SRC_SITE_ANGLE_NAME = "Source_Site Angle";
  public final static String SRC_SITE_ANGLE_UNITS = "degrees";
  public final static String SRC_SITE_ANGLE_INFO =
      "Difference between directions defined by closest point" +
      " on trace to site and the average strike of fault";
  public final static Double SRC_SITE_ANGLE_DEFAULT = new Double(90);
  protected final static Double SRC_SITE_ANGLE_MIN = new Double( -360);
  protected final static Double SRC_SITE_ANGLE_MAX = new Double(360);

  /**
   * aspectRatio parameter - Rupture aspect ratio.  This is created in the
   * initEqkRuptureParams method.
   */
  protected DoubleParameter aspectRatioParam = null;
  public final static String ASPECT_RATIO_NAME = "Rupture Apsect Ratio";
  public final static String ASPECT_RATIO_INFO =
      "Rupture length over down-dip width";
  public final static Double ASPECT_RATIO_DEFAULT = new Double(1);
  protected final static Double ASPECT_RATIO_MIN = new Double(Double.MIN_VALUE);
  protected final static Double ASPECT_RATIO_MAX = new Double(200);

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   *  This initializes several ParameterList objects.
   */
  public AS_2005_prelim_AttenRel(ParameterChangeWarningListener warningListener) {

    super();

    this.warningListener = warningListener;

    initSupportedIntensityMeasureParams();
    indexFromPerHashMap = new HashMap();
    for (int i = 0; i < period.length; i++) {
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
    rakeParam.setValue(eqkRupture.getAveRake());
    EvenlyGriddedSurfaceAPI surface = eqkRupture.getRuptureSurface();
    dipParam.setValue(surface.getAveDip());
    double depth = surface.getLocation(0, 0).getDepth();
    rupTopDepthParam.setValue(depth);
    // for point surface
    if (surface.size() == 1) {
      aspectRatioParam.setValue(1.0);
    }
    else {
      aspectRatioParam.setValue(surface.getSurfaceLength() /
                                surface.getSurfaceWidth());
    }

//    setFaultTypeFromRake(eqkRupture.getAveRake());
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
   * This sets the two propagation-effect parameters (distanceRupParam and
   * isOnHangingWallParam) based on the current site and eqkRupture.  The
   * hanging-wall term is rake independent (i.e., it can apply to strike-slip or
   * normal faults as well as reverse and thrust).  However, it is turned off if
   * the dip is greater than 70 degrees.  It is also turned off for point sources
   * regardless of the dip.  These specifications were determined from a series of
   * discussions between Ned Field, Norm Abrahamson, and Ken Campbell.
   */
  protected void setPropagationEffectParams() {

    if ( (this.site != null) && (this.eqkRupture != null)) {

      distanceRupParam.setValue(eqkRupture, site);
      distRupMinusJB_OverRupParam.setValue(eqkRupture, site);

      // set the srcSiteAngle parameter (could make a subclass of
      // PropagationEffectParameter later if others use this
      EvenlyGriddedSurfaceAPI surface = eqkRupture.getRuptureSurface();
      Location fltLoc1 = surface.getLocation(0, 0);
      Location fltLoc2 = surface.getLocation(0, surface.getNumCols() - 1);
      double angle1 = LocationUtils.azimuth(fltLoc1, fltLoc2);
      double minDist = Double.MAX_VALUE, dist;
      int minDistLocIndex = -1;
      for (int i = 0; i < surface.getNumCols(); i++) {
        dist = LocationUtils.horzDistanceFast(site.getLocation(),
            surface.getLocation(0, i));
        if (dist < minDist) {
          minDist = dist;
          minDistLocIndex = i;
        }
      }
      double angle2 = LocationUtils.azimuth(surface.getLocation(0,
          minDistLocIndex), site.getLocation());
      srcSiteAngleParam.setValue(angle2 - angle1);

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

    if (im.getName().equalsIgnoreCase(SA_Param.NAME)) {
      iper = ( (Integer) indexFromPerHashMap.get(saPeriodParam.getValue())).
          intValue();
    }
    else {
      iper = 0;
    }
    parameterChange = true;
    intensityMeasureChanged = false;

  }

  /**
   * Calculates the mean of the exceedence probability distribution. <p>
   * @return    The mean value
   */
  public double getMean() {
    if (intensityMeasureChanged) {
      setCoeffIndex();
    }

    // check if distance is beyond the user specified max
    if (rRup > USER_MAX_DISTANCE) {
      return VERY_SMALL_MEAN;
    }

    if (parameterChange) {
      calcMeanStdDev();
    }
    return mean;
  }

  /**
   * @return    The stdDev value
   */
  public double getStdDev() {
    if (intensityMeasureChanged) {
      setCoeffIndex();
    }

    if (parameterChange) {
      calcMeanStdDev();
    }
    return stdDev;
  }

  /**
   * Allows the user to set the default parameter values for the selected Attenuation
   * Relationship.
   */
  public void setParamDefaults() {

    vs30Param.setValueAsDefault();
    magParam.setValueAsDefault();
    rakeParam.setValueAsDefault();
	dipParam.setValueAsDefault();
    aspectRatioParam.setValue(ASPECT_RATIO_DEFAULT);
    rupTopDepthParam.setValueAsDefault();
    distanceRupParam.setValueAsDefault();
    distRupMinusJB_OverRupParam.setValueAsDefault();
    saParam.setValueAsDefault();
    saPeriodParam.setValueAsDefault();
    saDampingParam.setValueAsDefault();
    pgaParam.setValueAsDefault();
    componentParam.setValueAsDefault();
    stdDevTypeParam.setValueAsDefault();
    srcSiteAngleParam.setValue(SRC_SITE_ANGLE_DEFAULT);

    vs30 = ( (Double) vs30Param.getValue()).doubleValue();
    rjb = ( (Double) distRupMinusJB_OverRupParam.getValue()).doubleValue();
    rRup = ( (Double) distanceRupParam.getValue()).doubleValue();
    aspectratio = ( (Double) aspectRatioParam.getValue()).doubleValue();
    rake = ( (Double) rakeParam.getValue()).doubleValue();
    dip = ( (Double) dipParam.getValue()).doubleValue();
    mag = ( (Double) magParam.getValue()).doubleValue();
    srcSiteA = ( (Double) srcSiteAngleParam.getValue()).doubleValue();
    depthTop = ( (Double) rupTopDepthParam.getValue()).doubleValue();
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
    meanIndependentParams.addParameter(distanceRupParam);
    meanIndependentParams.addParameter(distRupMinusJB_OverRupParam);
    meanIndependentParams.addParameter(vs30Param);
    meanIndependentParams.addParameter(magParam);
    meanIndependentParams.addParameter(rakeParam);
    meanIndependentParams.addParameter(dipParam);
    meanIndependentParams.addParameter(componentParam);
    meanIndependentParams.addParameter(aspectRatioParam);
    meanIndependentParams.addParameter(rupTopDepthParam);
    meanIndependentParams.addParameter(srcSiteAngleParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    stdDevIndependentParams.addParameter(stdDevTypeParam);
    stdDevIndependentParams.addParameterList(meanIndependentParams);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    exceedProbIndependentParams.addParameterList(stdDevIndependentParams);
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
	rakeParam = new RakeParam();
	dipParam = new DipParam();
	rupTopDepthParam = new RupTopDepthParam();


	  
    // create aspectRatioParam
    DoubleConstraint c2 = new DoubleConstraint(ASPECT_RATIO_MIN,
                                               ASPECT_RATIO_MAX);
    aspectRatioParam = new DoubleParameter(ASPECT_RATIO_NAME, c2);
    aspectRatioParam.setInfo(ASPECT_RATIO_INFO);
    aspectRatioParam.setNonEditable();

    eqkRuptureParams.clear();
    eqkRuptureParams.addParameter(magParam);
    eqkRuptureParams.addParameter(rakeParam);
    eqkRuptureParams.addParameter(dipParam);
    eqkRuptureParams.addParameter(rupTopDepthParam);
    eqkRuptureParams.addParameter(aspectRatioParam);
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

    //create distRupMinusJB_OverRupParam
    distRupMinusJB_OverRupParam = new DistRupMinusJB_OverRupParameter(0.0);
    distRupMinusJB_OverRupParam.setNonEditable();

    // create srcSiteAngleParam
    DoubleConstraint c3 = new DoubleConstraint(SRC_SITE_ANGLE_MIN,
                                               SRC_SITE_ANGLE_MAX);
    srcSiteAngleParam = new DoubleParameter(SRC_SITE_ANGLE_NAME, c3,
                                            SRC_SITE_ANGLE_UNITS);
    srcSiteAngleParam.setInfo(SRC_SITE_ANGLE_INFO);
    srcSiteAngleParam.setNonEditable();

    propagationEffectParams.addParameter(distanceRupParam);
    propagationEffectParams.addParameter(distRupMinusJB_OverRupParam);
    propagationEffectParams.addParameter(srcSiteAngleParam);

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

  /**
   * This function calculates the Std-Dev and Mean together so pgaRock is not
   * computed twice
   */
  private void calcMeanStdDev() {
    double pgaRock = Math.exp(calcMean(0, 0.0, 1100));
    if (D) {
      System.out.println("PGA-Rock = " + pgaRock);
    }
    mean = calcMean(iper, pgaRock, vs30);
    if (D) {
      System.out.println("Mean = " + mean);
    }
    stdDev = calcStdDev(iper, pgaRock, vs30);
    if (D) {
      System.out.println("Std Dev = " + stdDev);
    }
    parameterChange = false;
  }

  private double calcMean(int iper, double pgaRock, double vs30) {

    double Frv, Fn, r, sum, taperM1, taperM2, ar1, hw1, t_hw, dAmp_dPGA;

    rjb = rRup - distRupJB_Fraction * rRup;

    if (D) {
      System.out.println("Before Mechanism");
      System.out.println("Vs30 = " + vs30 + " PGA-Rock =" + pgaRock + " Mag = " +
                         mag + " rRup = "
                         + rRup + " rake = " + rake);
      System.out.println("iPer = " + iper);
    }
    //       Mechanism
    if (rake > 22.5 && rake < 157.5) {
      Frv = 1.0;
    }
    else {
      Frv = 0.0;
    }
    if (rake < -22.5 && rake > -157.5) {
      Fn = 1.0;
    }
    else {
      Fn = 0.0;
    }

    //     Base Model
    r = Math.sqrt(rRup * rRup + c0[iper] * c0[iper]);
    sum = c1[iper] + (c2[iper] + c3[iper] * (7.5 - mag)) * Math.log(r) +
        c5[iper] * (mag - 6.) + c6[iper] * (8.5 - mag) * (8.5 - mag);

    if (D) {
      System.out.println("BaseModel");
      System.out.println("Sum = " + sum + " rRup =" + rRup + " r =" + r +
                         " c0[iper] =" + c0[iper]);

    }

    //     Mech model
    sum += c7[iper] * Frv + c9[iper] * Fn;

    if (D) {
      System.out.println("Mech Model");
      System.out.println("Sum = " + sum + " Frv = " + Frv + " Fn =" + Fn);
    }

    //     Set Taper 1
    if (mag > 7.) {
      taperM1 = 1.0;
    }
    else if (mag > 6.5) {
      taperM1 = (mag - 6.5) * 2.0;
    }
    else {
      taperM1 = 0.0;
    }

    //     Set Taper 2
    if (mag > 6.5) {
      taperM2 = 1.0;
    }
    else if (mag > 6.0) {
      taperM2 = (mag - 6.0) * 2.0;
    }
    else {
      taperM2 = 0.0;
    }

//     Aspect ratio model
    ar1 = aspectratio;
    if (ar1 > 20.) {
      ar1 = 20.;
    }
    else if (ar1 < 1.5) {
      ar1 = 1.5;
    }

    sum = sum + c8[iper] * (Math.log(ar1) - Math.log(1.5)) * taperM1;
    if (D) {
      System.out.println("Aspect Ratio");
      System.out.println("Sum = " + sum + " AR1 = " + ar1 +
                         " c8(iper)*(slog(ar1)-alog(1.5)) =" +
                         (c8[iper] * (Math.log(ar1) - Math.log(1.5))) +
                         " TaperM1 = " + taperM1);
    }
//     soil
    double soilamp;
    if (vs30 < vref[iper]) {
      soilamp = c10[iper] * Math.log(vs30 / vref[iper]) -
          b_soil[iper] * Math.log(c + pgaRock) +
          b_soil[iper] * Math.log(pgaRock + c * Math.pow(vs30 / vref[iper], n));
    }
    else {
      soilamp = (c10[iper] + b_soil[iper] * n) * Math.log(vs30 / vref[iper]);
    }

    sum = sum + soilamp;

//     HW model
    double angle1, taperTheta, t_fw;
    hw1 = 0.0;
    angle1 = Math.abs(srcSiteA);
    if (angle1 > 90.) {
      angle1 = 180. - srcSiteA;
    }

    if (angle1 < 20.) {
      taperTheta = angle1 / 20.0;
    }
    else {
      taperTheta = 1.0;
    }

    t_hw = (30. - rjb) / 30. * (90. - dip) / 45. * taperM2;
    if (depthTop == 0.) {
      t_fw = 0.;
    }
    else {
      t_fw = 1. - rjb / (2. * depthTop + 1.);
    }

    if (srcSiteA > 0. && rjb < 30.) {
      hw1 = c11[iper] * (t_hw * taperTheta + t_fw * (1. - taperTheta));
    }
    else if (srcSiteA < 0. && rjb < 2. * depthTop) {
      hw1 = c11[iper] * t_fw;
    }
    else {
      hw1 = 0.;
    }

    sum = sum + hw1;

    if (D) {
      System.out.println("HW1 - Sum =" + sum);
    }

//         depth of rupture term
    if (mag < 6.5) {
      sum = sum + c12[iper] * (depthTop - 5.) * (1. - taperM2);
    }

    if (D) {
      System.out.println("Depth of Rupture Term");
      System.out.println("Sum = " + sum);
    }
    return sum;
  }

  private double calcStdDev(int iper, double pgaRock, double vs30) {
    double sigma, tau;
    sigma = sigma0[iper];
    tau = tau0[iper];

    if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) {
      return 0;
    }
    else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA)) {
      return sigma;
    }
    else {
      double dAmp_dPGA;
      //     Compute parital derivative of ln(soil amp) w.r.t. ln(rock PGA)
      if (vs30 >= vref[iper]) {
        dAmp_dPGA = 0.;
      }
      else {
        dAmp_dPGA = b_soil[iper] * pgaRock *
            ( -1. / (pgaRock + 1.) + 1. / (pgaRock + vs30 / vref[iper]));
      }
      //     Set the tau for Sa including the effect of rockPGA tau
      tau = Math.sqrt(tau0[iper] * tau0[iper] + Math.pow(dAmp_dPGA * tau0[0], 2) +
                      2. * dAmp_dPGA * tau0[0] * tau0[iper] * tauCorr[iper]);

      if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER)) {
        return tau;
      }

      else {
        return Math.sqrt(sigma * sigma + tau * tau);
      }
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
    if (pName.equals(DistanceRupParameter.NAME)) {
      rRup = ( (Double) val).doubleValue();
    }
    else if (pName.equals(DistRupMinusJB_OverRupParameter.NAME)) {
      distRupJB_Fraction = ( (Double) val).doubleValue();
    }
    else if (pName.equals(Vs30_Param.NAME)) {
      vs30 = ( (Double) val).doubleValue();
    }
    else if (pName.equals(MagParam.NAME)) {
      mag = ( (Double) val).doubleValue();
    }
    else if (pName.equals(DipParam.NAME)) {
      dip = ( (Double) val).doubleValue();
    }
    else if (pName.equals(RakeParam.NAME)) {
      rake = ( (Double) val).doubleValue();
    }
    else if (pName.equals(this.ASPECT_RATIO_NAME)) {
      aspectratio = ( (Double) val).doubleValue();
    }
    else if (pName.equals(this.SRC_SITE_ANGLE_NAME)) {
      srcSiteA = ( (Double) val).doubleValue();
    }
    else if (pName.equals(RupTopDepthParam.NAME)) {
      depthTop = ( (Double) val).doubleValue();
    }
    else if (pName.equals(StdDevTypeParam.NAME)) {
      stdDevType = (String) val;
    }
    else if (pName.equals(PeriodParam.NAME) && intensityMeasureChanged) {
      setCoeffIndex();
    }
  }

  /**
   * Allows to reset the change listeners on the parameters
   */
  public void resetParameterEventListeners(){
    distanceRupParam.removeParameterChangeListener(this);
    distRupMinusJB_OverRupParam.removeParameterChangeListener(this);
    vs30Param.removeParameterChangeListener(this);
    magParam.removeParameterChangeListener(this);
    rakeParam.removeParameterChangeListener(this);
    dipParam.removeParameterChangeListener(this);
    aspectRatioParam.removeParameterChangeListener(this);
    rupTopDepthParam.removeParameterChangeListener(this);
    srcSiteAngleParam.removeParameterChangeListener(this);
    stdDevTypeParam.removeParameterChangeListener(this);
    saPeriodParam.removeParameterChangeListener(this);

    this.initParameterEventListeners();

  }

  /**
   * Adds the parameter change listeners. This allows to listen to when-ever the
   * parameter is changed.
   */
  protected void initParameterEventListeners() {

    distanceRupParam.addParameterChangeListener(this);
    distRupMinusJB_OverRupParam.addParameterChangeListener(this);
    vs30Param.addParameterChangeListener(this);
    magParam.addParameterChangeListener(this);
    rakeParam.addParameterChangeListener(this);
    dipParam.addParameterChangeListener(this);
    aspectRatioParam.addParameterChangeListener(this);
    rupTopDepthParam.addParameterChangeListener(this);
    srcSiteAngleParam.addParameterChangeListener(this);
    stdDevTypeParam.addParameterChangeListener(this);
    saPeriodParam.addParameterChangeListener(this);
  }

}
