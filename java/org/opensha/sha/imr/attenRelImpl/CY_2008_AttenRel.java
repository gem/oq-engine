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
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.AftershockParam;
import org.opensha.sha.imr.param.EqkRuptureParams.DipParam;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupTopDepthParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusDistX_OverRupParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusJB_OverRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.HangingWallFlagParam;
import org.opensha.sha.imr.param.SiteParams.DepthTo1pt0kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.imr.param.SiteParams.Vs30_TypeParam;

/**
 * <b>Title:</b> CY_2006_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship
 * developed by Chiou & Youngs (2008, Earthquake Spectra, Volume 24, No. 1, pages 173–215).  <p>
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
 * <LI>fltTypeParam - Style of faulting
 * <LI>rupTopDepthParam - depth to top of rupture
 * <LI>dipParam - rupture-surface dip
 * <LI>aftershockParam - indicates whether event is an aftershock
 * <LI>vs30Param - Vs-30 of the site
 * <LI>flagVSParam - indicates whether Vs30 is measured or estimated
 * <LI>depthTo1pt0kmPerSecParam - depth to where Vs is 1.0 km/sec
 * <LI>distanceRupParam - closest distance to surface projection of fault
 * <li>distRupMinusJB_OverRupParam - used to set distJB
 * <li>distRupMinusDistX_OverRupParam - used to set distX
 * <LI>hangingWallFlagParam - indicates whether site is on the hanging wall
 * <LI>componentParam - Component of shaking
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL></p>
 * 
 *<p>
 * NOTES: distRupMinusJB_OverRupParam is used rather than distancJBParameter because the latter 
 * should not be held constant when distanceRupParameter is changed (e.g., in the 
 * AttenuationRelationshipApplet).  The same is true for distRupMinusDistX_OverRupParam.
 * <p>
 * When setting parameters from a passed-in EqkRupture, aftershockParam is always set to false
 * (we could change this if aftershock info is added to an EqkRupture, but it's not clear this
 * is justified).
 * <p>
 * If depthTo1pt0kmPerSecParam is null, it is set from Vs30 using their equation (1).
 * <p>
 * Verification - This model has been tested against: 1) a verification file generated independently by Ken Campbell,
 * implemented in the JUnit test class CY_2008_test; and  2) by the test class NGA08_Site_EqkRup_Tests, which makes sure
 * parameters are set properly when Site and EqkRupture objects are passed in.
 * 
 * 
 * 
 *</p>
 * @author     Edward H. Field
 * @created    Feb, 2009
 * @version    1.0
 */


public class CY_2008_AttenRel
extends AttenuationRelationship implements
ScalarIntensityMeasureRelationshipAPI,
NamedObjectAPI, ParameterChangeListener {

	// Debugging stuff
	private final static String C = "CY_2008_AttenRel";
	private final static boolean D = false;

	// Name of IMR
	public final static String NAME = "Chiou & Youngs (2008)";
	public final static String SHORT_NAME = "CY2008";
//	private static final long serialVersionUID = 1234567890987654360L;


	// coefficients (index 22 is PGA and 23 is PGV):
	private static final double[] period = {0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5, 7.5, 10, 0, -1};
	private static final double[] c1 = {-1.2687, -1.2515, -1.1744, -1.0671, -0.9464, -0.7051, -0.5747, -0.5309, -0.6352, -0.7766, -0.9278, -1.2176, -1.4695, -1.9278, -2.2453, -2.7307, -3.1413, -3.7413, -4.1814, -4.5187, -5.1224, -5.5872, -1.2687, 2.2884};
	private static final double[] c1a = {0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.0999, 0.0997, 0.0991, 0.0936, 0.0766, 0.0022, -0.0591, -0.0931, -0.0982, -0.0994, -0.0999, -0.1, 0.1, 0.1094};
	private static final double[] c1b = {-0.255, -0.255, -0.255, -0.255, -0.255, -0.254, -0.253, -0.25, -0.2449, -0.2382, -0.2313, -0.2146, -0.1972, -0.162, -0.14, -0.1184, -0.11, -0.104, -0.102, -0.101, -0.101, -0.1, -0.255, -0.0626};
	private static final double[] cn = {2.996, 3.292, 3.514, 3.563, 3.547, 3.448, 3.312, 3.044, 2.831, 2.658, 2.505, 2.261, 2.087, 1.812, 1.648, 1.511, 1.47, 1.456, 1.465, 1.478, 1.498, 1.502, 2.996, 1.648};
	private static final double[] cm = {4.184, 4.1879, 4.1556, 4.1226, 4.1011, 4.086, 4.103, 4.1717, 4.2476, 4.3184, 4.3844, 4.4979, 4.5881, 4.7571, 4.882, 5.0697, 5.2173, 5.4385, 5.5977, 5.7276, 5.9891, 6.193, 4.184, 4.2979};
	private static final double[] c5 = {6.16, 6.158, 6.155, 6.1508, 6.1441, 6.12, 6.085, 5.9871, 5.8699, 5.7547, 5.6527, 5.4997, 5.4029, 5.29, 5.248, 5.2194, 5.2099, 5.204, 5.202, 5.201, 5.2, 5.2, 6.16, 5.17};
	private static final double[] c6 = {0.4893, 0.4892, 0.489, 0.4888, 0.4884, 0.4872, 0.4854, 0.4808, 0.4755, 0.4706, 0.4665, 0.4607, 0.4571, 0.4531, 0.4517, 0.4507, 0.4504, 0.4501, 0.4501, 0.45, 0.45, 0.45, 0.4893, 0.4407};
	private static final double[] c7 = {0.0512, 0.0512, 0.0511, 0.0508, 0.0504, 0.0495, 0.0489, 0.0479, 0.0471, 0.0464, 0.0458, 0.0445, 0.0429, 0.0387, 0.035, 0.028, 0.0213, 0.0106, 0.0041, 0.001, 0, 0, 0.0512, 0.0207};
	private static final double[] c7a = {0.086, 0.086, 0.086, 0.086, 0.086, 0.086, 0.086, 0.086, 0.086, 0.086, 0.086, 0.085, 0.083, 0.069, 0.045, 0.0134, 0.004, 0.001, 0, 0, 0, 0, 0.086, 0.0437};
	private static final double[] c9 = {0.79, 0.8129, 0.8439, 0.874, 0.8996, 0.9442, 0.9677, 0.966, 0.9334, 0.8946, 0.859, 0.8019, 0.7578, 0.6788, 0.6196, 0.5101, 0.3917, 0.1244, 0.0086, 0, 0, 0, 0.79, 0.3079};
	private static final double[] c9a = {1.5005, 1.5028, 1.5071, 1.5138, 1.523, 1.5597, 1.6104, 1.7549, 1.9157, 2.0709, 2.2005, 2.3886, 2.5, 2.6224, 2.669, 2.6985, 2.7085, 2.7145, 2.7164, 2.7172, 2.7177, 2.718, 1.5005, 2.669};
	private static final double[] c10 = {-0.3218, -0.3323, -0.3394, -0.3453, -0.3502, -0.3579, -0.3604, -0.3565, -0.347, -0.3379, -0.3314, -0.3256, -0.3189, -0.2702, -0.2059, -0.0852, 0.016, 0.1876, 0.3378, 0.4579, 0.7514, 1.1856, -0.3218, -0.1166};
	private static final double[] cg1 = {-0.00804, -0.00811, -0.00839, -0.00875, -0.00912, -0.00973, -0.00975, -0.00883, -0.00778, -0.00688, -0.00612, -0.00498, -0.0042, -0.00308, -0.00246, -0.0018, -0.00147, -0.00117, -0.00107, -0.00102, -0.00096, -0.00094, -0.00804, -0.00275};
	private static final double[] cg2 = {-0.00785, -0.00792, -0.00819, -0.00855, -0.00891, -0.0095, -0.00952, -0.00862, -0.00759, -0.00671, -0.00598, -0.00486, -0.0041, -0.00301, -0.00241, -0.00176, -0.00143, -0.00115, -0.00104, -0.00099, -0.00094, -0.00091, -0.00785, -0.00625};
	private static final double[] phi1 = {-0.4417, -0.434, -0.4177, -0.4, -0.3903, -0.404, -0.4423, -0.5162, -0.5697, -0.6109, -0.6444, -0.6931, -0.7246, -0.7708, -0.799, -0.8382, -0.8663, -0.9032, -0.9231, -0.9222, -0.8346, -0.7332, -0.4417, -0.7861};
	private static final double[] phi2 = {-0.1417, -0.1364, -0.1403, -0.1591, -0.1862, -0.2538, -0.2943, -0.3113, -0.2927, -0.2662, -0.2405, -0.1975, -0.1633, -0.1028, -0.0699, -0.0425, -0.0302, -0.0129, -0.0016, 0, 0, 0, -0.1417, -0.0699};
	private static final double[] phi3 = {-0.00701, -0.007279, -0.007354, -0.006977, -0.006467, -0.005734, -0.005604, -0.005845, -0.006141, -0.006439, -0.006704, -0.007125, -0.007435, -0.00812, -0.008444, -0.007707, -0.004792, -0.001828, -0.001523, -0.00144, -0.001369, -0.001361, -0.00701, -0.008444};
	private static final double[] phi4 = {0.102151, 0.10836, 0.119888, 0.133641, 0.148927, 0.190596, 0.230662, 0.266468, 0.255253, 0.231541, 0.207277, 0.165464, 0.133828, 0.085153, 0.058595, 0.031787, 0.019716, 0.009643, 0.005379, 0.003223, 0.001134, 0.000515, 0.102151, 5.41};
	private static final double[] phi5 = {0.2289, 0.2289, 0.2289, 0.2289, 0.229, 0.2292, 0.2297, 0.2326, 0.2386, 0.2497, 0.2674, 0.312, 0.361, 0.4353, 0.4629, 0.4756, 0.4785, 0.4796, 0.4799, 0.4799, 0.48, 0.48, 0.2289, 0.2899};
	private static final double[] phi6 = {0.014996, 0.014996, 0.014996, 0.014996, 0.014996, 0.014996, 0.014996, 0.014988, 0.014964, 0.014881, 0.014639, 0.013493, 0.011133, 0.006739, 0.005749, 0.005544, 0.005521, 0.005517, 0.005517, 0.005517, 0.005517, 0.005517, 0.014996, 0.006718};
	private static final double[] phi7 = {580, 580, 580, 579.9, 579.9, 579.6, 579.2, 577.2, 573.9, 568.5, 560.5, 540, 512.9, 441.9, 391.8, 348.1, 332.5, 324.1, 321.7, 320.9, 320.3, 320.1, 580, 459};
	private static final double[] phi8 = {0.07, 0.0699, 0.0701, 0.0702, 0.0701, 0.0686, 0.0646, 0.0494, -0.0019, -0.0479, -0.0756, -0.096, -0.0998, -0.0765, -0.0412, 0.014, 0.0544, 0.1232, 0.1859, 0.2295, 0.266, 0.2682, 0.07, 0.1138};
	private static final double[] tau1 = {0.3437, 0.3471, 0.3603, 0.3718, 0.3848, 0.3878, 0.3835, 0.3719, 0.3601, 0.3522, 0.3438, 0.3351, 0.3353, 0.3429, 0.3577, 0.3769, 0.4023, 0.4406, 0.4784, 0.5074, 0.5328, 0.5542, 0.3437, 0.2539};
	private static final double[] tau2 = {0.2637, 0.2671, 0.2803, 0.2918, 0.3048, 0.3129, 0.3152, 0.3128, 0.3076, 0.3047, 0.3005, 0.2984, 0.3036, 0.3205, 0.3419, 0.3703, 0.4023, 0.4406, 0.4784, 0.5074, 0.5328, 0.5542, 0.2637, 0.2381};
	private static final double[] sig1 = {0.4458, 0.4458, 0.4535, 0.4589, 0.463, 0.4702, 0.4747, 0.4798, 0.4816, 0.4815, 0.4801, 0.4758, 0.471, 0.4621, 0.4581, 0.4493, 0.4459, 0.4433, 0.4424, 0.442, 0.4416, 0.4414, 0.4458, 0.4496};
	private static final double[] sig2 = {0.3459, 0.3459, 0.3537, 0.3592, 0.3635, 0.3713, 0.3769, 0.3847, 0.3902, 0.3946, 0.3981, 0.4036, 0.4079, 0.4157, 0.4213, 0.4213, 0.4213, 0.4213, 0.4213, 0.4213, 0.4213, 0.4213, 0.3459, 0.3554};
	private static final double[] sig3 = {0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.7999, 0.7997, 0.7988, 0.7966, 0.7792, 0.7504, 0.7136, 0.7035, 0.7006, 0.7001, 0.7, 0.7, 0.7, 0.8, 0.7504};
	private static final double[] sig4 = {0.0663, 0.0663, 0.0663, 0.0663, 0.0663, 0.0663, 0.0663, 0.0612, 0.053, 0.0457, 0.0398, 0.0312, 0.0255, 0.0175, 0.0133, 0.009, 0.0068, 0.0045, 0.0034, 0.0027, 0.0018, 0.0014, 0.0663, 0.0133};
	private static final double c2 = 1.06;
	private static final double c3 = 3.45;
	private static final double c4 = -2.1;
	private static final double c4a = -0.5;
	private static final double crb = 50;
	private static final double chm = 3;
	private static final double cg3 = 4;

	protected final static Double PERIOD_DEFAULT = new Double(1.0);
	private HashMap indexFromPerHashMap;

	private int iper;
	private double vs30, rRup, distRupMinusJB_OverRup, dip, mag, f_rv, f_nm, depthTop;
	private double distRupMinusDistX_OverRup, aftershock, f_meas, f_hw;
	private String stdDevType;
	private boolean parameterChange;
	private double depthTo1pt0kmPerSec;  // defined this way to support null values
	private double lnYref;
	private boolean lnYref_is_not_fresh;

	// from page 66 of their report
	protected final static Double MAG_WARN_MIN = new Double(4.);
	protected final static Double MAG_WARN_MAX = new Double(8.5);
	protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
	protected final static Double DISTANCE_RUP_WARN_MAX = new Double(200.0);
	protected final static Double DISTANCE_MINUS_WARN_MIN = new Double(0.0);
	protected final static Double DISTANCE_MINUS_WARN_MAX = new Double(50.0);
	protected final static Double DISTANCE_X_WARN_MIN = new Double(-500.0);
	protected final static Double DISTANCE_X_WARN_MAX = new Double(500.0);
	protected final static Double VS30_WARN_MIN = new Double(150.0);
	protected final static Double VS30_WARN_MAX = new Double(1500.0);
	protected final static Double RUP_TOP_WARN_MIN = new Double(0);
	protected final static Double RUP_TOP_WARN_MAX = new Double(20);
	protected final static Double DEPTH_1pt0_WARN_MIN = new Double(0);
	protected final static Double DEPTH_1pt0_WARN_MAX = new Double(10000);


	// style of faulting options
	public final static String FLT_TYPE_STRIKE_SLIP = "Strike-Slip";
	public final static String FLT_TYPE_REVERSE = "Reverse";
	public final static String FLT_TYPE_NORMAL = "Normal";
	
	// this is for computing distance metrics efficiently
	private PropagationEffect propagationEffect;

	// for issuing warnings:
	private transient ParameterChangeWarningListener warningListener = null;


	/**
	 *  This initializes several ParameterList objects.
	 */
	public CY_2008_AttenRel(ParameterChangeWarningListener warningListener) {

		super();

		this.warningListener = warningListener;

		initSupportedIntensityMeasureParams();
		indexFromPerHashMap = new HashMap();
		for (int i = 0; i < period.length-2; i++) {  // subtract two for PGA and PGV (last two indices)
			indexFromPerHashMap.put(new Double(period[i]), new Integer(i));
		}

		initEqkRuptureParams();
		initSiteParams();
		initPropagationEffectParams();
		initOtherParams();

		initIndependentParamLists(); // This must be called after the above
		initParameterEventListeners(); //add the change listeners to the parameters
		
	    propagationEffect = new PropagationEffect();
	    propagationEffect.fixDistanceJB(true); // this ensures that it's exatly zero over the discretized rupture surfaces


	}

	/**
	 *  This sets the eqkRupture related parameters (magParam
	 *  and fltTypeParam) based on the eqkRupture passed in.
	 *  The internally held eqkRupture object is also set as that
	 *  passed in.  Note that this sets the aftershock parameter as
	 *  false (since that info is not yet part of and EkqRupture).  
	 *  Warning constrains are ignored.
	 *
	 * @param  eqkRupture  The new eqkRupture value
	 * @throws InvalidRangeException thrown if rake is out of bounds
	 */
	public void setEqkRupture(EqkRupture eqkRupture) throws InvalidRangeException {

		magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));

		double rake = eqkRupture.getAveRake();
		if(rake >= 30 && rake <= 150) {
			fltTypeParam.setValue(FLT_TYPE_REVERSE);
		}
		else if(rake >= -120 && rake <= -60) {
			fltTypeParam.setValue(FLT_TYPE_NORMAL);
		}
		else { // strike slip
			fltTypeParam.setValue(FLT_TYPE_STRIKE_SLIP);
		}    

		EvenlyGriddedSurfaceAPI surface = eqkRupture.getRuptureSurface();
		dipParam.setValue(surface.getAveDip());
		double depth = surface.getLocation(0, 0).getDepth();
		rupTopDepthParam.setValue(depth);
		aftershockParam.setValue(false);
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
		depthTo1pt0kmPerSecParam.setValue((Double)site.getParameter(DepthTo1pt0kmPerSecParam.NAME).getValue());
		vs30_TypeParam.setValue((String)site.getParameter(Vs30_TypeParam.NAME).getValue());
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

			propagationEffect.setAll(this.eqkRupture, this.site); // use this for efficiency
			distanceRupParam.setValueIgnoreWarning(propagationEffect.getDistanceRup()); // this sets rRup too
			double dist_jb = propagationEffect.getDistanceJB();
			double distX = propagationEffect.getDistanceX();
			if(rRup>0.0) {
				distRupMinusJB_OverRupParam.setValueIgnoreWarning((rRup-dist_jb)/rRup);
				if(distX >= 0.0) {  // sign determines whether it's on the hanging wall (distX is always >= 0 in distRupMinusDistX_OverRupParam)
					distRupMinusDistX_OverRupParam.setValue((rRup-distX)/rRup);
					hangingWallFlagParam.setValue(true);
				}
				else {
					distRupMinusDistX_OverRupParam.setValue((rRup+distX)/rRup);  // switch sign of distX here
					hangingWallFlagParam.setValue(false);
				}
			}
			else {
				distRupMinusJB_OverRupParam.setValueIgnoreWarning(0);
				distRupMinusDistX_OverRupParam.setValue(0);
				hangingWallFlagParam.setValue(true);
			}
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

		if (im.getName().equalsIgnoreCase(SA_Param.NAME))
			iper = ( (Integer) indexFromPerHashMap.get(saPeriodParam.getValue())).intValue();
		else if (im.getName().equalsIgnoreCase(PGA_Param.NAME))
			iper = 22;
		else
			iper = 23; // PGV

		parameterChange = true;
		intensityMeasureChanged = false;

	}

	/**
	 * Calculates the mean value. <p>
	 * @return    The mean value
	 */
	public double getMean() {

		// check if distance is beyond the user specified max
		if (rRup > USER_MAX_DISTANCE) {
			return VERY_SMALL_MEAN;
		}

		if (intensityMeasureChanged) {
			setCoeffIndex();// intensityMeasureChanged is set to false in this method
			lnYref_is_not_fresh = true;
		}


		return getMean(iper, vs30, f_rv, f_nm, rRup, distRupMinusJB_OverRup, depthTo1pt0kmPerSec, distRupMinusDistX_OverRup, f_hw, dip, 
				mag, depthTop, aftershock);
	}

	/**
	 * @return    The stdDev value
	 */
	public double getStdDev() {
		if (intensityMeasureChanged) {
			setCoeffIndex();// intensityMeasureChanged is set to false in this method
			lnYref_is_not_fresh = true;
		}

		return getStdDev(iper, vs30, f_rv, f_nm, rRup, distRupMinusJB_OverRup, distRupMinusDistX_OverRup, f_hw, dip, mag, depthTop, aftershock, stdDevType, f_meas);
	}

	/**
	 * Allows the user to set the default parameter values for the selected Attenuation
	 * Relationship.
	 */
	public void setParamDefaults() {

		magParam.setValueAsDefault();
		fltTypeParam.setValueAsDefault();
		rupTopDepthParam.setValueAsDefault();
		dipParam.setValueAsDefault();
		aftershockParam.setValueAsDefault();

		vs30Param.setValueAsDefault();
		vs30_TypeParam.setValue(Vs30_TypeParam.VS30_TYPE_INFERRED);
		depthTo1pt0kmPerSecParam.setValueAsDefault();

		distanceRupParam.setValueAsDefault();
		distRupMinusJB_OverRupParam.setValueAsDefault();
		distRupMinusDistX_OverRupParam.setValueAsDefault();
		hangingWallFlagParam.setValueAsDefault();

		componentParam.setValueAsDefault();
	    stdDevTypeParam.setValueAsDefault();
		
		saParam.setValueAsDefault();
		saPeriodParam.setValueAsDefault();
		saDampingParam.setValueAsDefault();
		pgaParam.setValueAsDefault();

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
		meanIndependentParams.addParameter(magParam);
		meanIndependentParams.addParameter(fltTypeParam);
		meanIndependentParams.addParameter(rupTopDepthParam);
		meanIndependentParams.addParameter(dipParam);
		meanIndependentParams.addParameter(aftershockParam);
		meanIndependentParams.addParameter(vs30Param);
		meanIndependentParams.addParameter(depthTo1pt0kmPerSecParam);
		meanIndependentParams.addParameter(distanceRupParam);
		meanIndependentParams.addParameter(distRupMinusJB_OverRupParam);
		meanIndependentParams.addParameter(distRupMinusDistX_OverRupParam);
		meanIndependentParams.addParameter(hangingWallFlagParam);
		meanIndependentParams.addParameter(componentParam);

		// params that the stdDev depends upon
		stdDevIndependentParams.clear();
		stdDevIndependentParams.addParameter(magParam);
		stdDevIndependentParams.addParameter(fltTypeParam);
		stdDevIndependentParams.addParameter(rupTopDepthParam);
		stdDevIndependentParams.addParameter(dipParam);
		stdDevIndependentParams.addParameter(aftershockParam);
		stdDevIndependentParams.addParameter(vs30Param);
		stdDevIndependentParams.addParameter(vs30_TypeParam);
		stdDevIndependentParams.addParameter(distanceRupParam);
		stdDevIndependentParams.addParameter(distRupMinusJB_OverRupParam);
		stdDevIndependentParams.addParameter(distRupMinusDistX_OverRupParam);
		stdDevIndependentParams.addParameter(hangingWallFlagParam);
		stdDevIndependentParams.addParameter(componentParam);
		stdDevIndependentParams.addParameter(stdDevTypeParam);

		// params that the exceed. prob. depends upon
		exceedProbIndependentParams.clear();
		exceedProbIndependentParams.addParameterList(meanIndependentParams);
		exceedProbIndependentParams.addParameter(vs30_TypeParam);
		exceedProbIndependentParams.addParameter(stdDevTypeParam);
		exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
		exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

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
	    vs30_TypeParam = new Vs30_TypeParam();
		depthTo1pt0kmPerSecParam = new DepthTo1pt0kmPerSecParam(DEPTH_1pt0_WARN_MIN, DEPTH_1pt0_WARN_MAX);

		siteParams.clear();
		siteParams.addParameter(vs30Param);
		siteParams.addParameter(vs30_TypeParam);
		siteParams.addParameter(depthTo1pt0kmPerSecParam);

	}

	/**
	 *  Creates the two Potential Earthquake parameters (magParam and
	 *  fltTypeParam) and adds them to the eqkRuptureParams
	 *  list. Makes the parameters noneditable.
	 */
	protected void initEqkRuptureParams() {

		magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);
	    
		aftershockParam = new AftershockParam();
		
		dipParam = new DipParam();
		
		rupTopDepthParam = new RupTopDepthParam(RUP_TOP_WARN_MIN, RUP_TOP_WARN_MAX);

		StringConstraint constraint = new StringConstraint();
		constraint.addString(FLT_TYPE_STRIKE_SLIP);
		constraint.addString(FLT_TYPE_NORMAL);
		constraint.addString(FLT_TYPE_REVERSE);
		constraint.setNonEditable();
	    fltTypeParam = new FaultTypeParam(constraint,FLT_TYPE_STRIKE_SLIP);

		eqkRuptureParams.clear();
		eqkRuptureParams.addParameter(magParam);
		eqkRuptureParams.addParameter(fltTypeParam);
		eqkRuptureParams.addParameter(rupTopDepthParam);
		eqkRuptureParams.addParameter(dipParam);
		eqkRuptureParams.addParameter(aftershockParam);
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
		DoubleConstraint warn2 = new DoubleConstraint(DISTANCE_MINUS_WARN_MIN, DISTANCE_MINUS_WARN_MAX);
		distRupMinusJB_OverRupParam.addParameterChangeWarningListener(warningListener);
		warn.setNonEditable();
		distRupMinusJB_OverRupParam.setWarningConstraint(warn2);
		distRupMinusJB_OverRupParam.setNonEditable();

		distRupMinusDistX_OverRupParam = new DistRupMinusDistX_OverRupParam();
		
	    // create hanging wall parameter
	    hangingWallFlagParam = new HangingWallFlagParam();

		propagationEffectParams.addParameter(distanceRupParam);
		propagationEffectParams.addParameter(distRupMinusJB_OverRupParam);
		propagationEffectParams.addParameter(distRupMinusDistX_OverRupParam);
		propagationEffectParams.addParameter(hangingWallFlagParam);

	}

	/**
	 *  Creates the two supported IM parameters (PGA and SA), as well as the
	 *  independenParameters of SA (periodParam and dampingParam) and adds
	 *  them to the supportedIMParams list. Makes the parameters noneditable.
	 */
	protected void initSupportedIntensityMeasureParams() {

		// Create saParam:
		DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
		for (int i = 0; i < period.length-2; i++) {  // subtract two for PGA and PGV (last two indices)
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

	/**
	 * This gets the mean for specific parameter settings.  We might want another 
	 * version that takes the actual SA period rather than the period index.
	 * @param iper
	 * @param vs30
	 * @param f_rv
	 * @param f_nm
	 * @param rRup
	 * @param distRupMinusJB_OverRup
	 * @param depthTo1pt0kmPerSec
	 * @param distRupMinusDistX_OverRup
	 * @param f_hw
	 * @param dip
	 * @param mag
	 * @param depthTop
	 * @param aftershock
	 * @return
	 */
	public double getMean(int iper, double vs30, double f_rv, double f_nm, double rRup, double distRupMinusJB_OverRup,
			double depthTo1pt0kmPerSec, double distRupMinusDistX_OverRup, double f_hw, double dip, double mag, double depthTop, double aftershock) {
			

		if(lnYref_is_not_fresh)
			compute_lnYref(iper, f_rv, f_nm, rRup, distRupMinusJB_OverRup, distRupMinusDistX_OverRup, f_hw, dip, mag, depthTop, aftershock);

		
		// set basinDepth default if depthTo1pt0kmPerSec is NaN 
		double basinDepth;
		if(Double.isNaN(depthTo1pt0kmPerSec))
			basinDepth = Math.exp(28.5 - 3.82*Math.log(Math.pow(vs30,8)+Math.pow(378.7,8))/8);
		else
			basinDepth = depthTo1pt0kmPerSec;

		double exp1 = Math.exp(phi3[iper]*(Math.min(vs30,1130)-360));
		double exp2 = Math.exp(phi3[iper]*(1130-360));

		double lnY = 	lnYref + phi1[iper]*Math.min(Math.log(vs30/1130), 0) +

		phi2[iper]*(exp1-exp2)*Math.log((Math.exp(lnYref)+phi4[iper])/phi4[iper]) +

		phi5[iper]*(1.0 - 1.0/Math.cosh(phi6[iper]*Math.max(0.0, basinDepth-phi7[iper]))) +

		phi8[iper]/Math.cosh(0.15*Math.max(0.0,basinDepth-15.0));

		return lnY;
	}


	/**
	 * This method returns lnYref (equation 13a in their paper).  This could test whether parameters have changed, and only
	 * update lnYref if so (more efficient since it's compute for both mean and stddev)
	 * 
	 * @param iper
	 * @param f_rv
	 * @param f_nm
	 * @param rRup
	 * @param distRupMinusJB_OverRup
	 * @param distRupMinusDistX_OverRup
	 * @param f_hw
	 * @param dip
	 * @param mag
	 * @param depthTop
	 * @param aftershock
	 * @return
	 */
	private void compute_lnYref(int iper, double f_rv, double f_nm, double rRup, double distRupMinusJB_OverRup,
								double distRupMinusDistX_OverRup, double f_hw, double dip, double mag, double depthTop, double aftershock) {
		// compute rJB
		double distanceJB = rRup - distRupMinusJB_OverRup*rRup;
		double distX  = rRup - distRupMinusDistX_OverRup*rRup;
// System.out.println(depthTop);
				
		double cosDelta = Math.cos(dip*Math.PI/180);
		double altDist = Math.sqrt(distanceJB*distanceJB+depthTop*depthTop);

		lnYref = 	c1[iper] + (c1a[iper]*f_rv+c1b[iper]*f_nm+c7[iper]*(depthTop-4.0))*(1-aftershock) +

		(c10[iper]+c7a[iper]*(depthTop-4.0))*aftershock +

		c2*(mag-6.0) + ((c2-c3)/cn[iper])*Math.log(1.0 + Math.exp(cn[iper]*(cm[iper]-mag))) +

		c4*Math.log(rRup+c5[iper]*Math.cosh(c6[iper]*Math.max(mag-chm,0))) +

		(c4a-c4)*0.5*Math.log(rRup*rRup+crb*crb) + 

		(cg1[iper] + cg2[iper]/Math.cosh(Math.max(mag-cg3,0.0)))*rRup +

		c9[iper] * f_hw * Math.tanh(distX*cosDelta*cosDelta/c9a[iper]) * (1-altDist/(rRup+0.001));
		
		lnYref_is_not_fresh = false;
	
		
//		System.out.println(rRup+"\t"+distanceJB+"\t"+distX+"\t"+f_hw+"\t"+lnYref);

	}


	/**
	 * This gets the standard deviation for specific parameter settings.  We might want another 
	 * version that takes the actual SA period rather than the period index.
	 * @param iper
	 * @param vs30
	 * @param f_rv
	 * @param f_nm
	 * @param rRup
	 * @param distRupMinusJB_OverRup
	 * @param distRupMinusDistX_OverRup
	 * @param f_hw
	 * @param dip
	 * @param mag
	 * @param depthTop
	 * @param aftershock
	 * @param stdDevType
	 * @param f_meas
	 * @return
	 */
	public double getStdDev(int iper, double vs30, double f_rv, double f_nm, double rRup, double distRupMinusJB_OverRup,
			double distRupMinusDistX_OverRup, double f_hw, double dip, double mag, double depthTop, double aftershock, String stdDevType, double f_meas) {

		double magTest = Math.min(Math.max(mag, 5.0), 7.0) - 5.0;

		double tau = tau1[iper] + (tau2[iper]-tau1[iper])/2 * magTest;

		if(lnYref_is_not_fresh)
			compute_lnYref(iper, f_rv, f_nm, rRup, distRupMinusJB_OverRup, distRupMinusDistX_OverRup, f_hw, dip, mag, depthTop, aftershock);

		double b = phi2[iper]*(Math.exp(phi3[iper]*(Math.min(vs30, 1130)-360)) - Math.exp(phi3[iper]*(1130-360)));  // Equation 10
		double c = phi4[iper];   // Equation 10
		double NLo = b*Math.exp(lnYref)/(Math.exp(lnYref)+c);
		double sigma = sig1[iper] + 0.5*(sig2[iper]-sig1[iper])*magTest + sig4[iper]*aftershock;
		sigma *= Math.sqrt((sig3[iper]*(1-f_meas)+0.7*f_meas)+(1+NLo)*(1+NLo));

		if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
			return Math.sqrt((1+NLo)*(1+NLo)*tau*tau + sigma*sigma);
		else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
			return 0;
		else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
			return sigma;
		else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
			return (1+NLo)*tau;  // not completely sure if this is the right thing to return here
		else 
			return Double.NaN;
	}

	/**
	 * This listens for parameter changes and updates the primitive parameters accordingly
	 * @param e ParameterChangeEvent
	 */
	public void parameterChange(ParameterChangeEvent e) {

		String pName = e.getParameterName();
		Object val = e.getNewValue();
		parameterChange = true;
		lnYref_is_not_fresh = true;  // this could be placed below, only where really needed.
		
		if (pName.equals(magParam.NAME)) {
			mag = ( (Double) val).doubleValue();
		}
		else if (pName.equals(FaultTypeParam.NAME)) {
			String fltType = (String)fltTypeParam.getValue();
			if (fltType.equals(FLT_TYPE_NORMAL)) {
				f_rv = 0 ;
				f_nm = 1;
			}
			else if (fltType.equals(FLT_TYPE_REVERSE)) {
				f_rv = 1;
				f_nm = 0;
			}
			else {
				f_rv =0 ;
				f_nm = 0;
			}
		}
		else if (pName.equals(RupTopDepthParam.NAME)) {
			depthTop = ( (Double) val).doubleValue();
		}
		else if (pName.equals(DipParam.NAME)) {
			dip = ( (Double) val).doubleValue();
		}
		else if (pName.equals(AftershockParam.NAME)) {
			if(((Boolean)val).booleanValue())
				aftershock = 1;
			else
				aftershock = 0;
		}
		else if (pName.equals(Vs30_Param.NAME)) {
			vs30 = ( (Double) val).doubleValue();
		}
		else if (pName.equals(Vs30_TypeParam.NAME)) {
			if(((String)val).equals(Vs30_TypeParam.VS30_TYPE_MEASURED)) {
				f_meas = 1;  // Bob Youngs confirmed by email that this is correct (f_meas=1-f_inf)
			}
			else {
				f_meas = 0;
			}
		}
		else if(pName.equals(DepthTo1pt0kmPerSecParam.NAME)){
			if(val == null)
				depthTo1pt0kmPerSec = Double.NaN;
			else
				depthTo1pt0kmPerSec = ((Double)val).doubleValue();
		}
		else if (pName.equals(DistanceRupParameter.NAME)) {
			rRup = ( (Double) val).doubleValue();
		}
		else if (pName.equals(DistRupMinusJB_OverRupParameter.NAME)) {
			distRupMinusJB_OverRup = ( (Double) val).doubleValue();
		}
		else if(pName.equals(distRupMinusDistX_OverRupParam.getName())){
			distRupMinusDistX_OverRup = ((Double)val).doubleValue();
		}
		else if (pName.equals(HangingWallFlagParam.NAME)) {
			if(((Boolean)val)) {
				f_hw = 1.0;
			}
			else {
				f_hw = 0.0;
			}
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
		magParam.removeParameterChangeListener(this);
		fltTypeParam.removeParameterChangeListener(this);
		rupTopDepthParam.removeParameterChangeListener(this);
		dipParam.removeParameterChangeListener(this);
		aftershockParam.removeParameterChangeListener(this);
		vs30Param.removeParameterChangeListener(this);
		vs30_TypeParam.removeParameterChangeListener(this);
		depthTo1pt0kmPerSecParam.removeParameterChangeListener(this);
		distanceRupParam.removeParameterChangeListener(this);
		distRupMinusJB_OverRupParam.removeParameterChangeListener(this);
		distRupMinusDistX_OverRupParam.removeParameterChangeListener(this);
		hangingWallFlagParam.removeParameterChangeListener(this);
		stdDevTypeParam.removeParameterChangeListener(this);
		saPeriodParam.removeParameterChangeListener(this);
		this.initParameterEventListeners();
	}

	/**
	 * Adds the parameter change listeners. This allows to listen to when-ever the
	 * parameter is changed.
	 */
	protected void initParameterEventListeners() {

		magParam.addParameterChangeListener(this);
		fltTypeParam.addParameterChangeListener(this);
		rupTopDepthParam.addParameterChangeListener(this);
		dipParam.addParameterChangeListener(this);
		aftershockParam.addParameterChangeListener(this);
		vs30Param.addParameterChangeListener(this);
		vs30_TypeParam.addParameterChangeListener(this);
		depthTo1pt0kmPerSecParam.addParameterChangeListener(this);
		distanceRupParam.addParameterChangeListener(this);
		distRupMinusJB_OverRupParam.addParameterChangeListener(this);
		distRupMinusDistX_OverRupParam.addParameterChangeListener(this);
		hangingWallFlagParam.addParameterChangeListener(this);
		stdDevTypeParam.addParameterChangeListener(this);
		saPeriodParam.addParameterChangeListener(this);
	}
	
	  
	  /**
	   * This provides a URL where more info on this model can be obtained
	   * @throws MalformedURLException if returned URL is not a valid URL.
	   * @returns the URL to the AttenuationRelationship document on the Web.
	   */
	  public URL getInfoURL() throws MalformedURLException{
		  return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/CY_2008.html");
	  }

}
