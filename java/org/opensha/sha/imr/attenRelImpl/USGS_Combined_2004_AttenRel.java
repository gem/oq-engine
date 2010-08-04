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
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.calc.GaussianDistCalc;
import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.exceptions.IMRException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.faultSurface.PointSurface;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.calc.Borcherdt2004_SiteAmpCalc;
import org.opensha.sha.imr.attenRelImpl.calc.Wald_MMI_Calc;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.MMI_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceSeisParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <b>Title:</b> USGS_Combined_2004_AttenRel<p>
 *
 * <b>Description:</b> This attenuation relationship computes a mean IML, exceedance
 * probabilty at IML, or IML at exceedance probability that represents an average of
 * 3-4 previously published relationships (the ones used for California in the 2002
 * National Seismic Hazard Maps; these are listed below).  For each relationship,
 * the predicted rock-site mean is multiplied by Borcherdt's nonlinear amplification
 * factor (1994, Earthquake Spectra, Vol. 10, No. 4, 617-653) as described below.
 * That is, the original site effect model of each relationship is not used.  The
 * averaging is performed after the site-depenent value for each relationship is
 * computed.<p>
 *
 * Supported Intensity-Measure Parameters:
 * <UL>
 * <LI>Peak Ground Acceleration (PGA)
 * <LI>Spectral Acceleration (SA) at the following periods: 0.0, 0.1, 0.2 0.3, 0.4,
 * 0.5, 0.75 1.0, 1.5, 2.0, 3.0, and 4.0 seconds
 * <LI>Peak Ground Velocity (PGV) - computed from 1-sec SA using the Newmark-Hall (1982) scalar
 * (applied after the amplification)
 * <LI>Modified Mercalli Intensity (MMI) computed from PGA and PGV as in Wald et al.
 * (1999, Earthquake Spectra, Vol. 15, No. 3, 557-564))
 * </UL><p>
 *
 * Attenuation Relationships used for the average:
 * <UL>
 * <LI>Abrahamson & Silva (1997) with site type "Rock/Shallow-Soil"
 * <LI>Boore, Joyner & Fumal (1997) with Vs30 = 760 m/sec
 * <LI>Sadigh et al (1997) with site type "Rock"
 * <LI>Campbell and Bozorgnia (2003) with site type "BC_Boundary"
 * </UL><p>
 * Independent Parameters:
 * <UL>
 * <LI>vs30Param - The average 30-meter shear-wave velocity (m/sec)
 * <LI>componentParam - Component of shaking (either "Average Horizontal" or "Greater of Two Horz.")
 * <LI>stdDevTypeParam - The type of standard deviation (either "Total" or "None (zero)")
 * </UL><p>
 * Important Notes:
 * <UL>
 * The Borcherdt (1994) nonlinear amplification factors are applied as given in appendix-equations
 * 7a or 7b (for periods � 0.5 and  > 0.5 seconds, respectively) using a reference velocity of 760 m/sec
 * (and with the mv and ma coefficients linearly interpolated at intermediate input ground motions).
 * Applying the mid-period amplification factors above 2.0 seconds for SA may not be legitimate. <p>
 * For the one relationship that has a site-type dependent standard deviation
 * (Sadigh et al., 1997) only the rock-site value is used (the difference is minor). <p>
 * The Boore, Joyner & Fumal (1997) relationship is not included in the average for SA periods
 * above 2.0 seconds. <p>
 * For Boore, Joyner & Fumal (1997) the component is set as "Random Horizontal"
 * (rather than "Average Horizontal") to be consistent with how this was set in the
 * 2002 National Seismic Hazard Maps.  All others are set as "Average Horizontal". <p>
 * For Campbell and Bozorgnia (2003) the magnitude dependent standard deviation is used. <p>
 * This class supports a "Greater of Two Horz." component by multiplying the average horizontal
 * component  median by a factor of 1.15.  This value was taken directly from the official ShakeMap
 * documentation.  The standard deviation for this component is set the same as the average
 * horizontal (not sure if this is correct).  <p>
 * </UL><p>
 * Developer Notes:
 * <UL>
 * Regarding the Modified Mercalli Intensity (MMI) IMT, note that what is returned by
 * the getMean() method is the natural-log of MMI.  Although this is not technically
 * correct (since MMI is not log-normally distributed), it was the easiest way to implement
 * it for now.  Furthermore, because the probability distribution of MMI (computed from PGA
 * or PGV) is presently unknown, we cannot compute the standard deviation, probability of
 * exceedance, or the IML at any probability other than 0.5.  Therefore, a RuntimeException
 * is thrown if one tries any of these when the chosen IMT is MMI.  We can relax this when
 * someone comes up with the probability distribution (which can't be Gaussian because
 * MMI values below 1 and above 10 are not allowed).<p>
 * Several methods for this class have been overridden to throw Runtime Exceptions, either because
 * it was not clear what to return or because the info is complicated and not necessarily useful.
 * For example, it's not clear what to return from getStdDev(); one could return the
 * average of the std. dev. of the four relationships, but nothing actually uses such an average (the probability of exceedance calculation
 * uses the mean/stdDev for each relationship separately).  Another example is what to return
 * from the getPropagationEffectParamsIterator - all of the three distance measures
 * used by the four relationships? - this would lead to confusion and possible inconsistencies
 * in the AttenuationRelationshipApplet.  The bottom line is we've maintained the
 * IntensityMeasureRelationshipAPI, but not the AttenuationRelationshipAPI (so this
 * relationship cannot be added to the AttenuationRelationshipApplet).  This class could
 * simply be a subclass of IntensityMeasureRelationship.  however, it's not because it
 * uses some of the private methods of AttenuationRelationship. <p>
 *
 * TESTS:<p>
 * For pga, 0.3-sec SA, 1.0-sec SA, and 3.0-sec SA, I tested shakemaps with Vs30=760
 * at all sites against averaging rock-site maps for each attenuation relationship separately. <p>
 * I made sure that pgv predictions are 1.0-sec SA predictions multiplied by the correct
 * scaling factor. <p>
 * I confirmed that the "Greater of Two Horz." component is just 1.15* the average horizontal. <p>
 * MMI calculations generally look correct, and the object that does the actual calucation
 * (Wald_MMI_Calc) was independently validated. <p>
 * I checked that the amplification factors being applied are correct in two ways: 1) I divided map
 * data with site effects by a rock-site map (vs30=760), and then divided the log of this amp factor
 * by log(760/vs30), and confirmed that the result plotted versus rock-pga is close to the functional form
 * of ma (or mv for periods � 0.5) versus rock-pga in the Borcherdt2004_SiteAmpCalc (the match
 * is not exact because amp factors are applied to each relationship before taking the average);
 * 2) I wrote out the ma (or mv) and amp values in the Borcherdt2004_SiteAmpCalc to make sure they
 * are correct.  Everything looked good.
 *
 *
 * @author     Edward H. Field
 * @created    May, 2004
 * @version    1.0
 */


public class USGS_Combined_2004_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI {

  // debugging stuff:
  private final static String C = "USGS_Combined_2004_AttenRel";
  private final static boolean D = false;
  public final static String NAME = "USGS Combined (2004)";
  public final static String SHORT_NAME = "USGS_2004";
  private static final long serialVersionUID = 1234567890987654370L;



  // attenuation relationships used.
  private final AS_1997_AttenRel as_1997_attenRel;
  private final CB_2003_AttenRel cb_2003_attenRel;
  private final SadighEtAl_1997_AttenRel scemy_1997_attenRel;
  private final BJF_1997_AttenRel bjf_1997_attenRel;

  private double vs30;
  private static final double VS30_REF = 760;

  private double SA10toPGV = Math.log(981.0 / (2.0 * Math.PI * 1.65));

  // The Borcherdt (2004) site amplification calculator
  Borcherdt2004_SiteAmpCalc borcherdtAmpCalc = new Borcherdt2004_SiteAmpCalc();

  // the site object for the BC boundary
  private Site site_BC;

  protected final static Double VS30_WARN_MIN = new Double(180.0);
  protected final static Double VS30_WARN_MAX = new Double(3500.0);

  /**
   * Their maximum horizontal component option.
   */
  public final static String COMPONENT_GREATER_OF_TWO_HORZ =
      "Greater of Two Horz.";

  /**
   * MMI parameter, the natural log of the "Modified Mercalli Intensity" IMT.
   */
  protected MMI_Param mmiParam = null;
  public final static String UNSUPPORTED_METHOD_ERROR =
      "This method is not supprted";

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   *  No-Arg constructor. This initializes several ParameterList objects.
   */
  public USGS_Combined_2004_AttenRel(ParameterChangeWarningListener
                                     warningListener) {

    super();

    this.warningListener = warningListener;

    initSupportedIntensityMeasureParams();
    initEqkRuptureParams();
    initPropagationEffectParams();
    initSiteParams();
    initOtherParams();
    initIndependentParamLists(); // Do this after the above

    // init the attenuation relationships
    as_1997_attenRel = new AS_1997_AttenRel(warningListener);
    cb_2003_attenRel = new CB_2003_AttenRel(warningListener);
    scemy_1997_attenRel = new SadighEtAl_1997_AttenRel(warningListener);
    bjf_1997_attenRel = new BJF_1997_AttenRel(warningListener);

    // init the BC boundary site object, and set it in the attenuation relationships:
    site_BC = new Site();
    this.propEffect = new PropagationEffect();

    as_1997_attenRel.getParameter(as_1997_attenRel.SITE_TYPE_NAME).setValue(
        as_1997_attenRel.SITE_TYPE_ROCK);
    site_BC.addParameter(as_1997_attenRel.getParameter(as_1997_attenRel.
        SITE_TYPE_NAME));

    cb_2003_attenRel.getParameter(cb_2003_attenRel.SITE_TYPE_NAME).setValue(
        cb_2003_attenRel.SITE_TYPE_NEHRP_BC);
    site_BC.addParameter(cb_2003_attenRel.getParameter(cb_2003_attenRel.
        SITE_TYPE_NAME));

    scemy_1997_attenRel.getParameter(scemy_1997_attenRel.SITE_TYPE_NAME).
        setValue(scemy_1997_attenRel.SITE_TYPE_ROCK);
    site_BC.addParameter(scemy_1997_attenRel.getParameter(scemy_1997_attenRel.
        SITE_TYPE_NAME));

    bjf_1997_attenRel.getParameter(Vs30_Param.NAME).setValue(new
        Double(760.0));
    site_BC.addParameter(bjf_1997_attenRel.getParameter(Vs30_Param.NAME));

    // set the components in the attenuation relationships
    as_1997_attenRel.getParameter(ComponentParam.NAME).setValue(ComponentParam.COMPONENT_AVE_HORZ);
    cb_2003_attenRel.getParameter(ComponentParam.NAME).setValue(ComponentParam.COMPONENT_AVE_HORZ);
    scemy_1997_attenRel.getParameter(ComponentParam.NAME).setValue(
    		ComponentParam.COMPONENT_AVE_HORZ);
    // the next one is different to be consistent with Frankel's implementation
    bjf_1997_attenRel.getParameter(ComponentParam.NAME).setValue(ComponentParam.COMPONENT_RANDOM_HORZ);

  }

  /**
   *  This sets the eqkRupture related parameters (magParam
   *  and fltTypeParam) based on the eqkRupture passed in.
   *  The internally held eqkRupture object is also set as that
   *  passed in.  Warning constrains are ingored.
   *
   * @param  eqkRupture  The new eqkRupture value
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Wills site parameter
   */
  public void setPropagationEffect(PropagationEffect propEffect) throws
      ParameterException {

    this.site = propEffect.getSite();
    this.eqkRupture = propEffect.getEqkRupture();

    this.propEffect.setEqkRupture(eqkRupture);

    vs30Param.setValueIgnoreWarning((Double)site.getParameter(Vs30_Param.NAME).getValue());

    // set the location of the BC bounday site object
    site_BC.setLocation(site.getLocation());
    this.propEffect.setSite(site_BC);

    as_1997_attenRel.setPropagationEffect(this.propEffect);
    bjf_1997_attenRel.setPropagationEffect(this.propEffect);
    scemy_1997_attenRel.setPropagationEffect(this.propEffect);
    cb_2003_attenRel.setPropagationEffect(this.propEffect);
  }

  /**
   *  This sets the eqkRupture.
   *
   * @param  eqkRupture
   */
  public void setEqkRupture(EqkRupture eqkRupture) {

    // Set the eqkRupture
    this.eqkRupture = eqkRupture;

    this.propEffect.setEqkRupture(eqkRupture);
    if (propEffect.getSite() != null) {
      as_1997_attenRel.setPropagationEffect(propEffect);
      bjf_1997_attenRel.setPropagationEffect(propEffect);
      scemy_1997_attenRel.setPropagationEffect(propEffect);
      cb_2003_attenRel.setPropagationEffect(propEffect);
    }
  }

  /**
   *  This sets the site-related parameter (vs30Param) based on what is in
   *  the Site object passed in (the Site object must have a parameter with
   *  the same name as that in willsSiteParam).  This also sets the internally held
   *  Site object as that passed in.  Warning constrains are ingored.
   *
   * @param  site             The new site value which contains a Wills site Param.
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Wills site parameter
   */
  public void setSite(Site site) throws ParameterException {

    vs30Param.setValueIgnoreWarning((Double)site.getParameter(Vs30_Param.NAME).getValue());
    this.site = site;

    // set the location of the BC bounday site object
    site_BC.setLocation(site.getLocation());

    this.propEffect.setSite(site_BC);
    if (this.eqkRupture != null) {
      as_1997_attenRel.setPropagationEffect(propEffect);
      bjf_1997_attenRel.setPropagationEffect(propEffect);
      scemy_1997_attenRel.setPropagationEffect(propEffect);
      cb_2003_attenRel.setPropagationEffect(propEffect);
    }
  }

  /**
   * This override is needed to deal with the site_BC and propEffect
   */
  public void setSiteLocation(Location loc) {
    //if site is null create a new Site
    if (site == null) {
      site = new Site();
    }
    site.setLocation(loc);
    site_BC.setLocation(loc);
    this.propEffect.setSite(site_BC);
    if (this.eqkRupture != null) {
      as_1997_attenRel.setPropagationEffect(propEffect);
      bjf_1997_attenRel.setPropagationEffect(propEffect);
      scemy_1997_attenRel.setPropagationEffect(propEffect);
      cb_2003_attenRel.setPropagationEffect(propEffect);
    }
  }

  /**
   * Note that for MMI this returns the natural log of MMI (this should be changed later)
   * @return
   * @throws IMRException
   */
  public double getMean() throws IMRException {

    vs30 = ( (Double) vs30Param.getValue()).doubleValue();

    // set the IMT in the various relationships
    setAttenRelsIMT();

    String imt = (String) im.getName();
    double per = ( (Double) saPeriodParam.getValue()).doubleValue();
    double mean = 0;
    if (imt.equals(SA_Param.NAME) && (per >= 3.0)) {
      mean += getMean(as_1997_attenRel);
      mean += getMean(cb_2003_attenRel);
      mean += getMean(scemy_1997_attenRel);
      return mean / 3.0;
    }
    else {
      mean += getMean(as_1997_attenRel);
      mean += getMean(cb_2003_attenRel);
      mean += getMean(bjf_1997_attenRel);
      mean += getMean(scemy_1997_attenRel);
      return mean / 4.0;
    }
  }

  /**
   * This assumes that vs30 has been set, and that the setAttenRelsStdDevTypes()
   * and setAttenRelsIMT() methods have already been called.
   * @param attenRel
   * @param iml
   * @return
   */
  private double getExceedProbability(AttenuationRelationship attenRel,
                                      double iml) {

    double mean = getMean(attenRel);
    double stdDev = attenRel.getStdDev();
    return getExceedProbability(mean, stdDev, iml);

  }


  /**
 * This assumes that vs30 has been set, and that the setAttenRelsStdDevTypes()
 * and setAttenRelsIMT() methods have already been called.
 * @param attenRel
 * @param iml
 * @return
 */
private double getEpsilon(AttenuationRelationship attenRel,
                                    double iml) {

  double mean = getMean(attenRel);
  double stdDev = attenRel.getStdDev();
  return (iml-mean)/stdDev;

}


  /**
   * This returns the mean for the given attenuation relationship after assigning
   * the Borcherdt amplification factor.  This assumes that vs30 has been set and that
   * the setAttenRelsIMT(*) method has been called.
   * @param attenRel
   * @return
   */
  private double getMean(AttenuationRelationship attenRel) {

    double ave_bc, pga_bc, amp, mean;

    String imt = im.getName();

    if (imt.equals(PGA_Param.NAME)) {
      pga_bc = attenRel.getMean();
      amp = borcherdtAmpCalc.getShortPeriodAmp(vs30, VS30_REF, Math.exp(pga_bc));
      mean = pga_bc + Math.log(amp);
    }
    else if (imt.equals(SA_Param.NAME)) {
      ave_bc = attenRel.getMean();
      // now get PGA for amp factor
      attenRel.setIntensityMeasure(PGA_Param.NAME);
      pga_bc = attenRel.getMean();
      attenRel.setIntensityMeasure(SA_Param.NAME); // revert back
      double per = ( (Double) saPeriodParam.getValue()).doubleValue();
      if (per <= 0.5) {
        amp = borcherdtAmpCalc.getShortPeriodAmp(vs30, VS30_REF,
                                                 Math.exp(pga_bc));
      }
      else {
        amp = borcherdtAmpCalc.getMidPeriodAmp(vs30, VS30_REF, Math.exp(pga_bc));
      }
      mean = ave_bc + Math.log(amp);
    }
    else if (imt.equals(PGV_Param.NAME)) {
      ave_bc = attenRel.getMean();
      // now get PGA for amp factor
      attenRel.setIntensityMeasure(PGA_Param.NAME);
      pga_bc = attenRel.getMean();
      attenRel.setIntensityMeasure(SA_Param.NAME); // revert back
      amp = borcherdtAmpCalc.getMidPeriodAmp(vs30, VS30_REF, Math.exp(pga_bc));
      mean = ave_bc + Math.log(amp) + SA10toPGV; // last term is the PGV conversion
    }
    else { // it must be MMI
      // here we must set the imt because it wasn't done in the setAttenRelsIMT(*) method
      attenRel.setIntensityMeasure(SA_Param.NAME);
      attenRel.getParameter(PeriodParam.NAME).setValue(new Double(1.0));
      ave_bc = attenRel.getMean();
      attenRel.setIntensityMeasure(PGA_Param.NAME);
      pga_bc = attenRel.getMean();
      amp = borcherdtAmpCalc.getMidPeriodAmp(vs30, VS30_REF, pga_bc);
      double pgv = ave_bc + Math.log(amp) + Math.log(37.27 * 2.54);
      amp = borcherdtAmpCalc.getShortPeriodAmp(vs30, VS30_REF, Math.exp(pga_bc));
      double pga = pga_bc + Math.log(amp);
      double mmi = Wald_MMI_Calc.getMMI(Math.exp(pga), Math.exp(pgv));
      mean = Math.log(mmi);
    }

    // correct for component if necessary
    String comp = (String) componentParam.getValue();
    if (comp.equals(COMPONENT_GREATER_OF_TWO_HORZ)) {
      mean += 0.139762; // add ln(1.15)
    }

    return mean;

  }

  /**
   * This sets the intensity measure for each of the four relationships.  This doesn nothing
   * if imt = MMI.
   */
  private void setAttenRelsIMT() {
    String imt = im.getName();
    if (imt.equals(PGA_Param.NAME)) {
      as_1997_attenRel.setIntensityMeasure(PGA_Param.NAME);
      scemy_1997_attenRel.setIntensityMeasure(PGA_Param.NAME);
      cb_2003_attenRel.setIntensityMeasure(PGA_Param.NAME);
      bjf_1997_attenRel.setIntensityMeasure(PGA_Param.NAME);
    }
    else if (imt.equals(SA_Param.NAME)) {
      Double per = (Double) saPeriodParam.getValue();
      as_1997_attenRel.setIntensityMeasure(SA_Param.NAME);
      as_1997_attenRel.getParameter(PeriodParam.NAME).setValue(per);
      scemy_1997_attenRel.setIntensityMeasure(SA_Param.NAME);
      scemy_1997_attenRel.getParameter(PeriodParam.NAME).setValue(per);
      cb_2003_attenRel.setIntensityMeasure(SA_Param.NAME);
      cb_2003_attenRel.getParameter(PeriodParam.NAME).setValue(per);
      if (per.doubleValue() <= 2.0) {
        bjf_1997_attenRel.setIntensityMeasure(SA_Param.NAME);
        bjf_1997_attenRel.getParameter(PeriodParam.NAME).setValue(per);
      }
    }
    else if (imt.equals(PGV_Param.NAME)) {
      Double per = new Double(1.0);
      as_1997_attenRel.setIntensityMeasure(SA_Param.NAME);
      as_1997_attenRel.getParameter(PeriodParam.NAME).setValue(per);
      scemy_1997_attenRel.setIntensityMeasure(SA_Param.NAME);
      scemy_1997_attenRel.getParameter(PeriodParam.NAME).setValue(per);
      cb_2003_attenRel.setIntensityMeasure(SA_Param.NAME);
      cb_2003_attenRel.getParameter(PeriodParam.NAME).setValue(per);
      if (per.doubleValue() <= 2.0) {
        bjf_1997_attenRel.setIntensityMeasure(SA_Param.NAME);
        bjf_1997_attenRel.getParameter(PeriodParam.NAME).setValue(per);
      }
    }
  }

  /**
   * This sets the standard deviation type for all the attenuation relations.
   * Note that truncations are dealt with in the parent method
   */
  private void setAttenRelsStdDevTypes() {

    // set the stdDevTypes
    String stdTyp = (String) stdDevTypeParam.getValue();

    as_1997_attenRel.getParameter(StdDevTypeParam.NAME).setValue(stdTyp);
    scemy_1997_attenRel.getParameter(StdDevTypeParam.NAME).setValue(stdTyp);
    bjf_1997_attenRel.getParameter(StdDevTypeParam.NAME).setValue(stdTyp);
    if (stdTyp.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL)) {
      cb_2003_attenRel.getParameter(StdDevTypeParam.NAME).setValue(
    		  StdDevTypeParam.STD_DEV_TYPE_TOTAL_MAG_DEP);
    }
    else {
      cb_2003_attenRel.getParameter(StdDevTypeParam.NAME).setValue(
    		  StdDevTypeParam.STD_DEV_TYPE_NONE);
    }
  }

  /**
   *  This overrides the parent class method.
   *
   * @return                         The intensity-measure level
   * @exception  ParameterException  Description of the Exception
   */
  public double getIML_AtExceedProb() throws ParameterException {

    if ( (exceedProbParam == null) || (exceedProbParam.getValue() == null)) {
      throw new ParameterException(C +
                                   ": getIML_AtExceedProb(): " +
          "exceedProbParam or its value is null, unable to run this calculation."
          );
    }

    double exceedProb = ( (Double) ( (ParameterAPI) exceedProbParam).getValue()).
        doubleValue();
    double stRndVar;
    String sigTrType = (String) sigmaTruncTypeParam.getValue();

    // compute the iml from exceed probability based on truncation type:

    // check for the simplest, most common case (median from symmectric truncation)
    if (!sigTrType.equals(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED) && exceedProb == 0.5) {
      return getMean();
    }
    else {
      //  throw exception if it's MMI
      if (im.getName().equals(MMI_Param.NAME)) {
        throw new RuntimeException(MMI_Param.MMI_ERROR_STRING);
      }

      // get the stRndVar dep on sigma truncation type and level
      if (sigTrType.equals(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE)) {
        stRndVar = GaussianDistCalc.getStandRandVar(exceedProb, 0, 0, 1e-6);
      }
      else {
        double numSig = ( (Double) ( (ParameterAPI) sigmaTruncLevelParam).
                         getValue()).doubleValue();
        if (sigTrType.equals(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED)) {
          stRndVar = GaussianDistCalc.getStandRandVar(exceedProb, 1, numSig,
              1e-6);
        }
        else {
          stRndVar = GaussianDistCalc.getStandRandVar(exceedProb, 2, numSig,
              1e-6);
        }
      }

      // now comput the average IML over all the attenuation relationships
      double ave_iml = 0;
      vs30 = ( (Double) vs30Param.getValue()).doubleValue();
      setAttenRelsStdDevTypes();
      setAttenRelsIMT();

      String imt = (String) im.getName();
      double per = ( (Double) saPeriodParam.getValue()).doubleValue();
      if (imt.equals(SA_Param.NAME) && (per >= 3.0)) {
        ave_iml += getMean(as_1997_attenRel) +
            stRndVar * as_1997_attenRel.getStdDev();
        ave_iml += getMean(scemy_1997_attenRel) +
            stRndVar * scemy_1997_attenRel.getStdDev();
        ave_iml += getMean(cb_2003_attenRel) +
            stRndVar * cb_2003_attenRel.getStdDev();
        return ave_iml / 3.0;
      }
      else {
        ave_iml += getMean(as_1997_attenRel) +
            stRndVar * as_1997_attenRel.getStdDev();
        ave_iml += getMean(scemy_1997_attenRel) +
            stRndVar * scemy_1997_attenRel.getStdDev();
        ave_iml += getMean(bjf_1997_attenRel) +
            stRndVar * bjf_1997_attenRel.getStdDev();
        ave_iml += getMean(cb_2003_attenRel) +
            stRndVar * cb_2003_attenRel.getStdDev();
        return ave_iml / 4.0;
      }
    }
  }

  /**
   * This returns the average rock-site stdDev.  This was implemented
   * so disaggregation could be conducted (not used locally in this class).
   *
   */
  public double getStdDev() throws IMRException {
//    throw new RuntimeException(UNSUPPORTED_METHOD_ERROR);
    if (stdDevTypeParam.getValue().equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) {
      return 0;
    }
    else {
      vs30 = ( (Double) vs30Param.getValue()).doubleValue();

      // set the IMT in the various relationships
      setAttenRelsIMT();
      setAttenRelsStdDevTypes();

      String imt = (String) im.getName();
      double per = ( (Double) saPeriodParam.getValue()).doubleValue();
      double std = 0;
      if (imt.equals(SA_Param.NAME) && (per >= 3.0)) {
        std += as_1997_attenRel.getStdDev();
        std += cb_2003_attenRel.getStdDev();
        std += scemy_1997_attenRel.getStdDev();
        return std / 3.0;
      }
      else {
        std += as_1997_attenRel.getStdDev();
        std += cb_2003_attenRel.getStdDev();
        std += bjf_1997_attenRel.getStdDev();
        std += scemy_1997_attenRel.getStdDev();
        return std / 4.0;
      }
    }
  }

  /**
   *  This calculates the probability that the given iml will be exceeded.
   * This assumes that vs30 has been set, and that the setAttenRelsStdDevTypes()
   * and setAttenRelsIMT() methods have already been called.
   *
   * @return                         The exceedProbability value
   * @exception  ParameterException  Description of the Exception
   * @exception  IMRException        Description of the Exception
   */
  private double getCombinedExceedProbability(double iml) throws
      ParameterException, IMRException {

    double per = ( (Double) saPeriodParam.getValue()).doubleValue();
    double prob = 0;
    if (im.getName().equals(SA_Param.NAME) && (per >= 3.0)) {
      prob += getExceedProbability(as_1997_attenRel, iml);
      prob += getExceedProbability(cb_2003_attenRel, iml);
      prob += getExceedProbability(scemy_1997_attenRel, iml);
      return prob / 3.0;
    }
    else {
      prob += getExceedProbability(as_1997_attenRel, iml);
      prob += getExceedProbability(cb_2003_attenRel, iml);
      prob += getExceedProbability(bjf_1997_attenRel, iml);
      prob += getExceedProbability(scemy_1997_attenRel, iml);
      return prob / 4.0;
    }
  }


  /**
   * This calculates the combined epsilon given iml (weighted by prob).
   * This assumes that vs30 has been set, and that the setAttenRelsStdDevTypes()
   * and setAttenRelsIMT() methods have already been called.
   *
   * @return                         The exceedProbability value
   * @exception  ParameterException  Description of the Exception
   * @exception  IMRException        Description of the Exception
   */
  private double getCombinedEpsilon(double iml) throws
      ParameterException, IMRException {

    double per = ( (Double) saPeriodParam.getValue()).doubleValue();
    double prob;
    double wt = 0, epsilon=0;

    prob = getExceedProbability(as_1997_attenRel, iml);
    epsilon += prob * getEpsilon(as_1997_attenRel, iml);
    wt += prob;
    prob = getExceedProbability(cb_2003_attenRel, iml);
    epsilon += prob * getEpsilon(cb_2003_attenRel, iml);
    wt += prob;
    prob = getExceedProbability(scemy_1997_attenRel, iml);
    epsilon += prob * getEpsilon(scemy_1997_attenRel, iml);
    wt += prob;

    if (im.getName().equals(SA_Param.NAME) && (per >= 3.0)) {
      return epsilon / wt;
    }
    else {
      prob = getExceedProbability(bjf_1997_attenRel, iml);
      epsilon += prob * getEpsilon(bjf_1997_attenRel, iml);
      wt += prob;

      return epsilon / wt;
    }
  }



  /**
   *  This calculates the probability that the intensity-measure level
   *  (the value in the Intensity-Measure Parameter) will be exceeded
   *  given the mean and stdDev computed from current independent parameter
   *  values.  Note that the answer is not stored in the internally held
   *  exceedProbParam (this latter param is used only for the
   *  getIML_AtExceedProb() method).
   *
   * @return                         The exceedProbability value
   * @exception  ParameterException  Description of the Exception
   * @exception  IMRException        Description of the Exception
   */
  public double getExceedProbability() throws ParameterException, IMRException {

    // throw exception if MMI was chosen
    if (im.getName().equals(MMI_Param.NAME)) {
      throw new RuntimeException(MMI_Param.MMI_ERROR_STRING);
    }

    // set vs30
    vs30 = ( (Double) vs30Param.getValue()).doubleValue();

    // set the standard deviation types
    setAttenRelsStdDevTypes();

    // set the IMT in the various relationships
    setAttenRelsIMT();

    return getCombinedExceedProbability( ( (Double) im.getValue()).doubleValue());
  }




  /**
 *  This calculates a weighted average epsilon for the iml value in the Intensity-
 * Measure Parameter). Note that this returns NaN if the prob. of exceedance is zero.
 *
 * @return                         The epsilon value
 * @exception  ParameterException  Description of the Exception
 * @exception  IMRException        Description of the Exception
 */
public double getEpsilon() {

  // throw exception if MMI was chosen
  if (im.getName().equals(MMI_Param.NAME)) {
    throw new RuntimeException(MMI_Param.MMI_ERROR_STRING);
  }

  // set vs30
  vs30 = ( (Double) vs30Param.getValue()).doubleValue();

  // set the standard deviation types
  setAttenRelsStdDevTypes();

  // set the IMT in the various relationships
  setAttenRelsIMT();

  return this.getCombinedEpsilon(((Double) im.getValue()).doubleValue());
}





  /**
   *  This fills in the exceedance probability for multiple intensityMeasure
   *  levels (often called a "hazard curve"); the levels are obtained from
   *  the X values of the input function, and Y values are filled in with the
   *  asociated exceedance probabilities. NOTE: THE PRESENT IMPLEMENTATION IS
   *  STRANGE IN THAT WE DON'T NEED TO RETURN ANYTHING SINCE THE FUNCTION PASSED
   *  IN IS WHAT CHANGES (SHOULD RETURN NULL?).
   *
   * @param  intensityMeasureLevels  The function to be filled in
   * @return                         The function filled in
   * @exception  ParameterException  Description of the Exception
   */
  public DiscretizedFuncAPI getExceedProbabilities(
      DiscretizedFuncAPI intensityMeasureLevels
      ) throws ParameterException {

    // throw exception if MMI was chosen
    if (im.getName().equals(MMI_Param.NAME)) {
      throw new RuntimeException(MMI_Param.MMI_ERROR_STRING);
    }

    DataPoint2D point;

    // set vs30
    vs30 = ( (Double) vs30Param.getValue()).doubleValue();

    // set the standard deviation types in the various relationships
    setAttenRelsStdDevTypes();

    // set the IMT in the various relationships
    setAttenRelsIMT();

    Iterator it = intensityMeasureLevels.getPointsIterator();
    while (it.hasNext()) {
      point = (DataPoint2D) it.next();
      point.setY(getCombinedExceedProbability(point.getX()));
    }
    return intensityMeasureLevels;

  }

  public void setParamDefaults() {

    //((ParameterAPI)this.iml).setValue( IML_DEFAULT );
    vs30Param.setValueAsDefault();
    saParam.setValueAsDefault();
    saPeriodParam.setValueAsDefault();
    saDampingParam.setValueAsDefault();
    pgaParam.setValueAsDefault();
    pgvParam.setValueAsDefault();
    mmiParam.setValue(MMI_Param.DEFAULT);
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
    meanIndependentParams.addParameter(vs30Param);
    meanIndependentParams.addParameter(componentParam);

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    stdDevIndependentParams.addParameter(stdDevTypeParam);
    stdDevIndependentParams.addParameter(componentParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    exceedProbIndependentParams.addParameter(vs30Param);
    exceedProbIndependentParams.addParameter(componentParam);
    exceedProbIndependentParams.addParameter(stdDevTypeParam);
    exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
    exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

    // params that the IML at exceed. prob. depends upon
    imlAtExceedProbIndependentParams.addParameterList(
        exceedProbIndependentParams);
    imlAtExceedProbIndependentParams.addParameter(exceedProbParam);

  }

  /**
   *  Creates the willsSiteParam site parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {

	vs30Param = new Vs30_Param(VS30_WARN_MIN, VS30_WARN_MAX);

    // add it to the siteParams list:
    siteParams.clear();
    siteParams.addParameter(vs30Param);
  }

  /**
   *  This does nothing
   */
  protected void initEqkRuptureParams() {
  }

  /**
   *  This does nothing
   */
  protected void initPropagationEffectParams() {
  }

  /**
   *  Creates the supported IM parameters (PGA, PGV, MMI and SA), as well as the
   *  independenParameters of SA (periodParam and dampingParam) and adds
   *  them to the supportedIMParams list. Makes the parameters noneditable.
   */
  protected void initSupportedIntensityMeasureParams() {

    // Create saParam's "Period" independent parameter:
    DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
    periodConstraint.addDouble(0.0);
    periodConstraint.addDouble(0.1);
    periodConstraint.addDouble(0.2);
    periodConstraint.addDouble(0.3);
    periodConstraint.addDouble(0.4);
    periodConstraint.addDouble(0.5);
    periodConstraint.addDouble(0.75);
    periodConstraint.addDouble(1.0);
    periodConstraint.addDouble(1.5);
    periodConstraint.addDouble(2.0);
    periodConstraint.addDouble(3.0);
    periodConstraint.addDouble(4.0);
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

    // The MMI parameter
    mmiParam = new MMI_Param();
    
    // Add the warning listeners:
    saParam.addParameterChangeWarningListener(warningListener);
    pgaParam.addParameterChangeWarningListener(warningListener);
    pgvParam.addParameterChangeWarningListener(warningListener);

    
    // Put parameters in the supportedIMParams list:
    supportedIMParams.clear();
    supportedIMParams.addParameter(saParam);
    supportedIMParams.addParameter(pgaParam);
    supportedIMParams.addParameter(pgvParam);
    supportedIMParams.addParameter(mmiParam);

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
    constraint.addString(ComponentParam.COMPONENT_GREATER_OF_TWO_HORZ);
    constraint.setNonEditable();
    componentParam = new ComponentParam(constraint,componentParam.COMPONENT_AVE_HORZ);

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

  // this method, required by the API, does nothing here (it's not needed).
  protected void initCoefficients() {

  }

  // this method, required by the API, does nothing here (it's not needed).
  protected void setPropagationEffectParams() {

  }

  /**
   *  This is overridden to throw a runtine exception (the method is not supported).
   */
  public ListIterator getEqkRuptureParamsIterator() {
    throw new RuntimeException(UNSUPPORTED_METHOD_ERROR);
  }

  /**
   *  This is overridden to throw a runtine exception (the method is not supported).
   */
  public ListIterator getPropagationEffectParamsIterator() {
    throw new RuntimeException(UNSUPPORTED_METHOD_ERROR);
  }

  /**
   *  This is overridden to throw a runtine exception (the method is not supported).
   */
  public ListIterator getExceedProbIndependentParamsIterator() {
    throw new RuntimeException(UNSUPPORTED_METHOD_ERROR);
  }

  /**
   *  This is overridden to throw a runtine exception (the method is not supported).
   */
  public ListIterator getMeanIndependentParamsIterator() {
    throw new RuntimeException(UNSUPPORTED_METHOD_ERROR);
  }

  /**
   *  This is overridden to throw a runtine exception (the method is not supported).
   */
  public ListIterator getStdDevIndependentParamsIterator() {
    throw new RuntimeException(UNSUPPORTED_METHOD_ERROR);
  }

  /**
   *  This is overridden to throw a runtine exception (the method is not supported).
   */
  public ListIterator getIML_AtExceedProbIndependentParamsIterator() {
    throw new RuntimeException(UNSUPPORTED_METHOD_ERROR);
  }

  // this is temporary for testing purposes
  public static void main(String[] args) {
    USGS_Combined_2004_AttenRel ar = new USGS_Combined_2004_AttenRel(null);
    ar.setParamDefaults();
    Site site = new Site(new Location(34,-117,0));
    site.addParameter(ar.getParameter(Vs30_Param.NAME));
    ProbEqkRupture qk = new ProbEqkRupture(6.25, 0, 8.27442E-4, new PointSurface(34.0,-117,0.0), null);
    ar.setEqkRupture(qk);
    ar.setSite(site);
    ar.setIntensityMeasure(PGA_Param.NAME);
    System.out.println(ar.getMean());
    System.out.println(ar.getStdDev());
    PropagationEffect pe = new PropagationEffect();
    pe.setAll(qk,site);
    System.out.println(pe.getParamValue(DistanceSeisParameter.NAME));
    System.out.println(ar.getMean());
    System.out.println(ar.getStdDev());

  }

  
  /**
   * This provides a URL where more info on this model can be obtained
   * @throws MalformedURLException if returned URL is not a valid URL.
   * @returns the URL to the AttenuationRelationship document on the Web.
   */
  public URL getInfoURL() throws MalformedURLException{
	  return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/USGS_Combined_2004.html");
  }

  
}
