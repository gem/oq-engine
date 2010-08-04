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
 * <b>Title:</b> BA_2006_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship
 * developed by Boore (2006), as described at
 * http://peer.berkeley.edu/lifelines/nga_docs/nov_13_06/Boore-Atkinson-NGA_11-13-06.html <p>
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
 * <LI>vs30Param - 30-meter shear wave velocity
 * <LI>fltTypeParam - Style of faulting
 * <LI>componentParam - Component of shaking (only one)
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL></p>
 * 
 *<p>
 *
 * Verification:I just tested this model with the earlier model (BJF1997).I ran both models in AttenuationRelationship
 * application and checked if  they produce the similar results.
 * 
 *</p>
 *
 *
 * @author     Edward H. Field & Nitin Gupta
 * @created    November, 2006
 * @version    1.0
 */


public class BA_2006_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI, ParameterChangeListener {

  // Debugging stuff
  private final static String C = "BA_2006_AttenRel";
  private final static boolean D = false;
  public final static String SHORT_NAME = "Boore2006";
  private static final long serialVersionUID = 1234567890987654353L;


  // Name of IMR
  public final static String NAME = "Boore & Atkinson (2006)";

  // coefficients:
  // note that index 0 is for PGA4nl (rock-PGA for computing amp factor),
  //index 1 is for PGV and index 2 is for PGA
  double[] period= {-2,-1,0,0.05,0.1,0.2,0.3,0.5,1,2,3,4,5};
  double[] e01= {-0.96402,4.30814,-1.11599,-0.8604,-0.4966,-0.18575,-0.31699,-0.62784,-1.27487,-2.06005,-2.60576,-2.93734,-2.26498};
  double[] e02= {-0.96402,4.37031,-1.07915,-0.78212,-0.45054,-0.16733,-0.31009,-0.62094,-1.24033,-1.98637,-2.52057,-2.84754,-2.1913};
  double[] e03= {-0.96402,3.94064,-1.34556,-1.06833,-0.67845,-0.35388,-0.5065,-0.81194,-1.59746,-2.41603,-3.0071,-3.28664,-2.49017};
  double[] e04= {-0.96402,4.34942,-1.08589,-0.9418,-0.50546,-0.14161,-0.233,-0.54956,-1.19819,-2.10691,-2.69448,-3.07123,-2.39245};
  double[] e05= {0.29795,0.43312,0.38983,0.41009,0.21582,0.41055,0.5091,0.6514,0.69377,0.72117,0.74903,1.11952,0.10516};
  double[] e06= {-0.20341,-0.1128,-0.11736,-0.0957,-0.14218,-0.16809,-0.18428,-0.14354,-0.19885,-0.31499,-0.42298,-0.35897,-0.39006};
  double[] e07= {0,0,0,0.01804,0,0,0.00632,0,0.00058,0.32628,0.6963,0.68456,0};
  double[] e08= {0,0,0,0,0,0,0,0,0,0,0,0,0};
  double[] mh= {7,8.5,7,7,7,7,7,7,7,7,7,7,8.5};
  double[] c01= {-0.55,-0.7933,-0.6603,-0.5352,-0.6518,-0.5833,-0.5543,-0.6917,-0.8182,-0.8286,-0.7846,-0.6851,-0.5068};
  double[] c02= {0,0.1111,0.1196,0.1544,0.1188,0.04287,0.01955,0.06091,0.1027,0.09436,0.07288,0.03746,-0.02355};
  double[] c03= {-0.01151,-0.00622,-0.01151,-0.01873,-0.01367,-0.00952,-0.0075,-0.0054,-0.00334,-0.00217,-0.00191,-0.00191,-0.00202};
  double[] c04= {0,0,0,0,0,0,0,0,0,0,0,0,0};
  double[] mref= {6,4.5,4.5,4.5,4.5,4.5,4.5,4.5,4.5,4.5,4.5,4.5,4.5};
  double[] rref= {5,5,5,5,5,5,5,5,5,5,5,5,5};
  double[] h= {3,2.54,1.35,1.35,1.68,1.98,2.14,2.32,2.54,2.73,2.83,2.89,2.93};
  double[] blin= {0,-0.6,-0.36,-0.29,-0.25,-0.31,-0.44,-0.6,-0.7,-0.73,-0.74,-0.75,-0.75};
  double[] vref= {0,760,760,760,760,760,760,760,760,760,760,760,760};
  double[] b1= {0,-0.5,-0.64,-0.64,-0.6,-0.52,-0.52,-0.5,-0.44,-0.38,-0.34,-0.31,-0.3};
  double[] b2= {0,-0.06,-0.14,-0.11,-0.13,-0.19,-0.14,-0.06,0,0,0,0,0};
  double[] v1= {0,180,180,180,180,180,180,180,180,180,180,180,180};
  double[] v2= {0,300,300,300,300,300,300,300,300,300,300,300,300};
  double[] a1= {0,0.03,0.03,0.03,0.03,0.03,0.03,0.03,0.03,0.03,0.03,0.03,0.03};
  double[] pga_low= {0,0.06,0.06,0.06,0.06,0.06,0.06,0.06,0.06,0.06,0.06,0.06,0.06};
  double[] a2= {0,0.09,0.09,0.09,0.09,0.09,0.09,0.09,0.09,0.09,0.09,0.09,0.09};
  double[] sig1= {0,0.513,0.502,0.576,0.53,0.523,0.546,0.555,0.573,0.58,0.566,0.583,0.603};
  double[] sig2u= {0,0.286,0.262,0.368,0.325,0.286,0.269,0.262,0.313,0.396,0.41,0.389,0.414};
  double[] sigtu= {0,0.587,0.566,0.684,0.622,0.596,0.608,0.612,0.654,0.702,0.7,0.702,0.732};
  double[] sig2m= {0,0.256,0.256,0.366,0.327,0.288,0.269,0.262,0.297,0.389,0.401,0.38,0.437};
  double[] sigtm= {0,0.573,0.562,0.682,0.622,0.596,0.608,0.612,0.645,0.698,0.693,0.695,0.744};
  
  
  private HashMap indexFromPerHashMap;

  private int iper;
  private double vs30, rjb, mag;
  private String stdDevType, fltType;
  private boolean parameterChange;

  // ?????????????????????????????????????
  protected final static Double MAG_WARN_MIN = new Double(4.5);
  protected final static Double MAG_WARN_MAX = new Double(8.5);
  protected final static Double DISTANCE_JB_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_JB_WARN_MAX = new Double(200.0);
  protected final static Double VS30_WARN_MIN = new Double(120.0);
  protected final static Double VS30_WARN_MAX = new Double(2000.0);

  
  // style of faulting options
  public final static String FLT_TYPE_UNKNOWN = "Unknown";
  public final static String FLT_TYPE_STRIKE_SLIP = "Strike-Slip";
  public final static String FLT_TYPE_REVERSE = "Reverse";
  public final static String FLT_TYPE_NORMAL = "Normal";

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   *  This initializes several ParameterList objects.
   */
  public BA_2006_AttenRel(ParameterChangeWarningListener
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
	  double pga4nl = Math.exp(getMean(0, vs30, rjb, mag, fltType, 0.0));
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
    
    double magDiff = mag-mh[iper];
    if (mag <= mh[iper]) {
      Fm = e01[iper]*U + e02[iper]*S + e03[iper]*N + e04[iper]*R + 
      	   e05[iper]*magDiff+
      	   e06[iper]*magDiff*magDiff;
    }
    else {
      Fm = e01[iper]*U + e02[iper]*S + e03[iper]*N + e04[iper]*R +
      		e07[iper]*(mag-mh[iper]) + 
      		e08[iper]*magDiff*magDiff;
    }

    double r = Math.sqrt(rjb * rjb + h[iper] * h[iper]);
    Fd = (c01[iper] + c02[iper]*(mag-mref[iper]))*Math.log(r/rref[iper]) +
         (c03[iper] + c04[iper]*(mag-mref[iper]))*(r-rref[iper]);

    // site response term
    if(pga4nl ==0.0)
    		Fs =0; 
    else{
		double Flin = blin[iper]*Math.log(vs30/vref[iper]);	

		// compute bnl
		double bnl = 0;
	    if (vs30 <= v1[iper]) {
	      bnl = b1[iper];
	    }
	    else if (vs30 <= v2[iper] && vs30 > v1[iper]) {
	      bnl = (b1[iper] - b2[iper]) * Math.log(vs30 / v2[iper]) /
	          Math.log(v1[iper] / v2[iper]) + b2[iper];
	    }
	    else if (vs30 <= vref[iper] && vs30 > v2[iper]) {
	      bnl = b2[iper] * Math.log(vs30 / vref[iper]) /
	          Math.log(v2[iper] / vref[iper]);
	    }
	    else if (vs30 > vref[iper]) {
	      bnl = 0.0;
	    }   
	    
	    // compute c & d
	    double c, d, dX, dY;
	    dX = Math.log(a2[iper]/a1[iper]);
	    dY = bnl*Math.log(a2[iper]/pga_low[iper]);
	    c = (3*dY-bnl*dX)/(dX*dX);
	    d = -(2*dY-bnl*dX)/(dX*dX*dX);
	    
		
		double Fnl;
	    if(pga4nl <= a1[iper])
	    		Fnl = bnl*Math.log(pga_low[iper]/0.1);
	    else if (pga4nl <= a2[iper] & pga4nl > a1[iper])
	    		Fnl = bnl*Math.log(pga_low[iper]/0.1) + 
	    			c*Math.pow(Math.log(pga4nl/a1[iper]),2) +
	    			d*Math.pow(Math.log(pga4nl/a1[iper]),3);
	    else
	        Fnl = bnl*Math.log(pga4nl/0.1);
	    
	    Fs= Flin+Fnl;
    }
    return (Fm + Fd + Fs);
  }

  public double getStdDev(int iper, String stdDevType, String fltType) {
//	  sig1 = intra; sig2 = inter; sigt = total (where "u" is focal mech unspecified)
	  
	  if(fltType.equals(FLT_TYPE_UNKNOWN)) {
		  if(stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
			  return sigtu[iper];
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
			  return 0;
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
			  return sig2u[iper];
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
			  return sig1[iper];
		  else 
			  return Double.NaN;
	  }
	  else {
		  if(stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
			  return sigtm[iper];
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
			  return 0;
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
			  return sig2m[iper];
		  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
			  return sig1[iper];
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
   * 
   * @throws MalformedURLException if returned URL is not a valid URL.
   * @returns the URL to the AttenuationRelationship document on the Web.
   */
  public URL getInfoURL() throws MalformedURLException{
	  return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/BA_2006.html");
  }   
  
}
