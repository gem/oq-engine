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
import java.util.ArrayList;
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
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FaultUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.calc.Wald_MMI_Calc;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.MMI_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;


/**
 * <b>Title:</b> ShakeMap_2003_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship used
 * by the ShakeMap group (2003), which is a hybrid of BJF (1997) and the low-
 * magnitude regression developed by Vincent Quitoriano (where the former is used
 * above mag=5.5, the latter is used below 5.0 and a linear-ramp average is used in between).
 * However, rather than using Vs30 as the site paremeter, this uses the Wills et al.
 * (2000, Bull. Seism. Soc. Am., 90, S187-S208) classification scheme and the
 * nonlinear amplification factors of Borcherdt (1994, Earthquake Spectra, 10, 617-654).
 * There is very little written documentation of this relationship, and what exists
 * is full of typos and outdated information.  This class was composed by Ned Field
 * based on numerous queries to David Wald, Vincent Quitoriano, and Bruce Worden. <p>
 *
 * Supported Intensity-Measure Parameters:
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>SAParam  - Spectral Acceleration at 0.0, 0.3, 1.0, and 3.0 second periods
 * <LI>pgvParam - Peak Ground Velocity (computed from 1-sec SA using the Newmark-Hall (1982) scalar)
 * <LI>mmiParam - Modified Mercalli Intensity computed from PGA and PGV as in Wald et al. (1999, Earthquake Spectra)
 * </UL><p>
 * Other Independent Parameters:
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceJBParam - closest distance to surface projection of fault
 * <LI>willsSiteParam - The site classes used in the Wills et al. (2000) map
 * <LI>fltTypeParam - Style of faulting
 * <LI>componentParam - Component of shaking (only one)
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL><p>
 * Important Notes:
 * <UL>
 * Because for the low-magnitude regression the different sigma estimates were
 * available only for PGA (only total sigma was available for PGV and SA), the different sigmas
 * represent those of PGA scaled by the relative difference of the totals.  Again, this
 * only applies at low maginitudes, and the approximated values should be very close to
 * the true values.<p>
 * This class supports a "Greater of Two Horz." component by multiplying the average horizontal
 * component  median by a factor of 1.15.  This value was taken directly from the official ShakeMap
 * documentation.  The standard deviation for this component is set the same as the average
 * horizontal (not sure if this is correct).  <p>
 * Regarding the Modified Mercalli Intensity (MMI) IMT, note that what is returned by
 * the getMean() method is the natural-log of MMI.  Although this is not technically
 * correct (since MMI is not log-normally distributed), it was the easiest way to implement
 * it for now.  Furthermore, because the probability distribution of MMI (computed from PGA
 * or PGV) is presently unknown, we cannot compute the standard deviation, probability of
 * exceedance, or the IML at any probability other than 0.5.  Therefore, a RuntimeException
 * is thrown if one tries any of these when the chosen IMT is MMI.  We can relax this when
 * someone comes up with the probability distribution (which can't be Gaussian because
 * MMI values below 1 and above 10 are not allowed).<p>
 *
 * @author     Edward H. Field
 * @created    April, 2003
 * @version    1.0
 */


public class ShakeMap_2003_AttenRel
extends AttenuationRelationship implements
ScalarIntensityMeasureRelationshipAPI,
NamedObjectAPI {

	// debugging stuff:
	private final static String C = "ShakeMap_2003_AttenRel";
	private final static boolean D = false;
	public final static String NAME = "ShakeMap (2003)";
	public final static String SHORT_NAME = "ShakeMap2003";
	private static final long serialVersionUID = 1234567890987654368L;


	// PGA thresholds for computing amp factors (convert from gals to g)
	private final static double pga_low = -1.87692; // Math.log(150/980);
	private final static double pga_mid = -1.36609; // Math.log(250/980);
	private final static double pga_high = -1.02962; // Math.log(350/980);

	// style of faulting options
	public final static String FLT_TYPE_UNKNOWN = "Unknown";
	public final static String FLT_TYPE_STRIKE_SLIP = "Strike-Slip";
	public final static String FLT_TYPE_REVERSE = "Reverse";

	// warning constraint fields:
	protected final static Double MAG_WARN_MIN = new Double(3.3);
	protected final static Double MAG_WARN_MAX = new Double(7.5);


	// Joyner-Boore Distance parameter
	protected final static Double DISTANCE_JB_WARN_MIN = new Double(0.0);
	protected final static Double DISTANCE_JB_WARN_MAX = new Double(80.0);

	private StringParameter willsSiteParam = null;
	public final static String WILLS_SITE_NAME = "Wills Site Class";
	public final static String WILLS_SITE_INFO =
		"Site classification defined by Wills et al. (2000, BSSA)";
	public final static String WILLS_SITE_B = "B";
	public final static String WILLS_SITE_BC = "BC";
	public final static String WILLS_SITE_C = "C";
	public final static String WILLS_SITE_CD = "CD";
	public final static String WILLS_SITE_D = "D";
	public final static String WILLS_SITE_DE = "DE";
	public final static String WILLS_SITE_E = "E";
	public final static String WILLS_SITE_DEFAULT = WILLS_SITE_BC;

	/**
	 * MMI parameter, the natural log of the "Modified Mercalli Intensity" IMT.
	 */
	protected MMI_Param mmiParam = null;

	/**
	 * The current set of coefficients based on the selected intensityMeasure
	 */
	private BJF_1997_AttenRelCoefficients coeffBJF = null;
	private BJF_1997_AttenRelCoefficients coeffSM = null;

	/**
	 *  Hashtable of coefficients for the supported intensityMeasures
	 */
	protected Hashtable coefficientsBJF = new Hashtable();
	protected Hashtable coefficientsSM = new Hashtable();

	// for issuing warnings:
	private transient ParameterChangeWarningListener warningListener = null;

	/**
	 * Determines the style of faulting from the rake angle (which
	 * comes from the eqkRupture object) and fills in the
	 * value of the fltTypeParam.  Options are "Reverse" if 150>rake>30,
	 * "Strike-Slip" if rake is within 30 degrees of 0 or 180, and "Unkown"
	 * otherwise (which means normal-faulting events are assigned as "Unkown";
	 * confirmed by David Boore via email as being correct).
	 *
	 * @param rake                      in degrees
	 * @throws InvalidRangeException    If not valid rake angle
	 */
	protected void setFaultTypeFromRake(double rake) throws InvalidRangeException {
		FaultUtils.assertValidRake(rake);
		if (Math.abs(Math.sin(rake * Math.PI / 180)) <= 0.5) {
			fltTypeParam.setValue(FLT_TYPE_STRIKE_SLIP); // 0.5 = sin(30)
		}
		else if (rake >= 30 && rake <= 150) {
			fltTypeParam.setValue(FLT_TYPE_REVERSE);
		}
		else {
			fltTypeParam.setValue(FLT_TYPE_UNKNOWN);
		}
	}

	/**
	 *  No-Arg constructor. This initializes several ParameterList objects.
	 */
	public ShakeMap_2003_AttenRel(ParameterChangeWarningListener warningListener) {

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
	 *  This sets the site-related parameter (willsSiteParam) based on what is in
	 *  the Site object passed in (the Site object must have a parameter with
	 *  the same name as that in willsSiteParam).  This also sets the internally held
	 *  Site object as that passed in.
	 *
	 * @param  site             The new site value which contains a Wills site Param.
	 * @throws ParameterException Thrown if the Site object doesn't contain a
	 * Wills site parameter
	 */
	public void setSite(Site site) throws ParameterException {

		willsSiteParam.setValue((String)site.getParameter(WILLS_SITE_NAME).getValue());
		this.site = site;
		setPropagationEffectParams();

	}

	/**
	 * This sets the site and eqkRupture, and the related parameters,
	 *  from the propEffect object passed in. Warning constrains are ingored.
	 * @param propEffect
	 * @throws ParameterException Thrown if the Site object doesn't contain a
	 * Wills site parameter
	 * @throws InvalidRangeException thrown if rake is out of bounds
	 */
	public void setPropagationEffect(PropagationEffect propEffect) throws
	ParameterException, InvalidRangeException {

		this.site = propEffect.getSite();
		this.eqkRupture = propEffect.getEqkRupture();

		willsSiteParam.setValue((String)site.getParameter(this.WILLS_SITE_NAME).getValue());

		magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
		setFaultTypeFromRake(eqkRupture.getAveRake());

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

		StringBuffer key = new StringBuffer(im.getName());
		if (im.getName().equalsIgnoreCase(SA_Param.NAME)) {
			key.append("/" + saPeriodParam.getValue());
		}
		if (coefficientsBJF.containsKey(key.toString())) {
			coeffBJF = (BJF_1997_AttenRelCoefficients) coefficientsBJF.get(key.
					toString());
			coeffSM = (BJF_1997_AttenRelCoefficients) coefficientsSM.get(key.toString());
		}
		else {
			throw new ParameterException(C + ": setIntensityMeasureType(): " +
					"Unable to locate coefficients with key = " +
					key);
		}
	}

	/**
	 * Note that for MMI this returns the natural log of MMI (this should be changed later)
	 * @return
	 * @throws IMRException
	 */
	public double getMean() throws IMRException {

		String imt = im.getName();
		if (!imt.equals(MMI_Param.NAME)) {
			updateCoefficients();
			double b_mean = getRockMean();
			if (imt.equals(PGA_Param.NAME)) {
				return b_mean + Math.log(getAmpFactor(im.getName(), b_mean));
			}
			else {
				return b_mean + Math.log(getAmpFactor(im.getName()));
			}
		}
		else {
			return Math.log(getMMI()); // return the log for now (until I figure a better way)
		}

	}

	/**
	 * This computes the nonlinear amplification factor according to the Wills site class,
	 * IMT, and BC_PGA.
	 * @return
	 */
	private double getAmpFactor(String imt) {

		String S = ".getAmpFactor()";

		// get the PGA for B category
		coeffBJF = (BJF_1997_AttenRelCoefficients) coefficientsBJF.get(PGA_Param.NAME);
		coeffSM = (BJF_1997_AttenRelCoefficients) coefficientsSM.get(PGA_Param.NAME);
		return getAmpFactor(imt, getRockMean());
	}

	private double getAmpFactor(String imt, double b_pga) {

		String S = ".getAmpFactor()";

		// figure out whether we need short-period or mid-period amps
		boolean shortPeriod;
		if (imt.equals(PGA_Param.NAME)) {
			shortPeriod = true;
		}
		else if (imt.equals(PGV_Param.NAME)) {
			shortPeriod = false;
		}
		else if (imt.equals(SA_Param.NAME)) {
			double per = ( (Double) saPeriodParam.getValue()).doubleValue();
			if (per <= 0.45) {
				shortPeriod = true;
			}
			else {
				shortPeriod = false;
			}
		}
		else {
			throw new RuntimeException(C + "IMT not supported");
		}

		if (D) {
			System.out.println(C + S + " shortPeriod = " + shortPeriod);
		}

		//now get the amp factor
		// These are from an email from Bruce Worden on 12/04/03
		// (also sent by Vince in an email earlier)
		String sType = (String) willsSiteParam.getValue();
		double amp = 0;
		if (shortPeriod) {
			if (b_pga <= pga_low) {
				if (sType.equals(WILLS_SITE_E)) {
					amp = 1.65;
				}
				else if (sType.equals(WILLS_SITE_DE)) {
					amp = 1.34;
				}
				else if (sType.equals(WILLS_SITE_D)) {
					amp = 1.33;
				}
				else if (sType.equals(WILLS_SITE_CD)) {
					amp = 1.24;
				}
				else if (sType.equals(WILLS_SITE_C)) {
					amp = 1.15;
				}
				else if (sType.equals(WILLS_SITE_BC)) {
					amp = 0.98;
				}
				else if (sType.equals(WILLS_SITE_B)) {
					amp = 1.00;
				}
			}
			else if (b_pga <= pga_mid) {
				if (sType.equals(WILLS_SITE_E)) {
					amp = 1.43;
				}
				else if (sType.equals(WILLS_SITE_DE)) {
					amp = 1.23;
				}
				else if (sType.equals(WILLS_SITE_D)) {
					amp = 1.23;
				}
				else if (sType.equals(WILLS_SITE_CD)) {
					amp = 1.17;
				}
				else if (sType.equals(WILLS_SITE_C)) {
					amp = 1.10;
				}
				else if (sType.equals(WILLS_SITE_BC)) {
					amp = 0.99;
				}
				else if (sType.equals(WILLS_SITE_B)) {
					amp = 1.00;
				}
			}
			else if (b_pga <= pga_high) {
				if (sType.equals(WILLS_SITE_E)) {
					amp = 1.15;
				}
				else if (sType.equals(WILLS_SITE_DE)) {
					amp = 1.09;
				}
				else if (sType.equals(WILLS_SITE_D)) {
					amp = 1.09;
				}
				else if (sType.equals(WILLS_SITE_CD)) {
					amp = 1.06;
				}
				else if (sType.equals(WILLS_SITE_C)) {
					amp = 1.04;
				}
				else if (sType.equals(WILLS_SITE_BC)) {
					amp = 0.99;
				}
				else if (sType.equals(WILLS_SITE_B)) {
					amp = 1.00;
				}
			}
			else {
				if (sType.equals(WILLS_SITE_E)) {
					amp = 0.93;
				}
				else if (sType.equals(WILLS_SITE_DE)) {
					amp = 0.96;
				}
				else if (sType.equals(WILLS_SITE_D)) {
					amp = 0.96;
				}
				else if (sType.equals(WILLS_SITE_CD)) {
					amp = 0.97;
				}
				else if (sType.equals(WILLS_SITE_C)) {
					amp = 0.98;
				}
				else if (sType.equals(WILLS_SITE_BC)) {
					amp = 1.00;
				}
				else if (sType.equals(WILLS_SITE_B)) {
					amp = 1.00;
				}
			}
		}
		else {
			if (b_pga <= pga_low) {
				if (sType.equals(WILLS_SITE_E)) {
					amp = 2.55;
				}
				else if (sType.equals(WILLS_SITE_DE)) {
					amp = 1.72;
				}
				else if (sType.equals(WILLS_SITE_D)) {
					amp = 1.71;
				}
				else if (sType.equals(WILLS_SITE_CD)) {
					amp = 1.49;
				}
				else if (sType.equals(WILLS_SITE_C)) {
					amp = 1.29;
				}
				else if (sType.equals(WILLS_SITE_BC)) {
					amp = 0.97;
				}
				else if (sType.equals(WILLS_SITE_B)) {
					amp = 1.00;
				}
			}
			else if (b_pga <= pga_mid) {
				if (sType.equals(WILLS_SITE_E)) {
					amp = 2.37;
				}
				else if (sType.equals(WILLS_SITE_DE)) {
					amp = 1.65;
				}
				else if (sType.equals(WILLS_SITE_D)) {
					amp = 1.64;
				}
				else if (sType.equals(WILLS_SITE_CD)) {
					amp = 1.44;
				}
				else if (sType.equals(WILLS_SITE_C)) {
					amp = 1.26;
				}
				else if (sType.equals(WILLS_SITE_BC)) {
					amp = 0.97;
				}
				else if (sType.equals(WILLS_SITE_B)) {
					amp = 1.00;
				}
			}
			else if (b_pga <= pga_high) {
				if (sType.equals(WILLS_SITE_E)) {
					amp = 2.14;
				}
				else if (sType.equals(WILLS_SITE_DE)) {
					amp = 1.56;
				}
				else if (sType.equals(WILLS_SITE_D)) {
					amp = 1.55;
				}
				else if (sType.equals(WILLS_SITE_CD)) {
					amp = 1.38;
				}
				else if (sType.equals(WILLS_SITE_C)) {
					amp = 1.23;
				}
				else if (sType.equals(WILLS_SITE_BC)) {
					amp = 0.97;
				}
				else if (sType.equals(WILLS_SITE_B)) {
					amp = 1.00;
				}
			}
			else {
				if (sType.equals(WILLS_SITE_E)) {
					amp = 1.91;
				}
				else if (sType.equals(WILLS_SITE_DE)) {
					amp = 1.46;
				}
				else if (sType.equals(WILLS_SITE_D)) {
					amp = 1.45;
				}
				else if (sType.equals(WILLS_SITE_CD)) {
					amp = 1.32;
				}
				else if (sType.equals(WILLS_SITE_C)) {
					amp = 1.19;
				}
				else if (sType.equals(WILLS_SITE_BC)) {
					amp = 0.98;
				}
				else if (sType.equals(WILLS_SITE_B)) {
					amp = 1.00;
				}
			}
		}

		if (D) {
			System.out.println(C + S + "amp = " + amp);
		}

		// return the value
		return amp;

	}

	/**
	 * This computes MMI (from PGA and PGV) using the relationship given by
	 * Wald et al. (1999, Earthquake Spectra).  The code is a modified version
	 * of what Bruce Worden sent me (Ned) on 12/04/03.  This could be a separate
	 * utility (that takes pgv and pga as arguments) since others might want to use it.
	 * @return
	 */
	private double getMMI() {
		double pgv, pga;
		String S = ".getMMI()";

		// get PGA
		coeffBJF = (BJF_1997_AttenRelCoefficients) coefficientsBJF.get(PGA_Param.NAME);
		coeffSM = (BJF_1997_AttenRelCoefficients) coefficientsSM.get(PGA_Param.NAME);
		double b_pga = getRockMean();
		pga = b_pga + Math.log(getAmpFactor(PGA_Param.NAME));
		// Convert to linear domain
		pga = Math.exp(pga);

		if (D) {
			System.out.println(C + S + " pga = " + (float) pga);
		}

		// get PGV
		coeffBJF = (BJF_1997_AttenRelCoefficients) coefficientsBJF.get(PGV_Param.NAME);
		coeffSM = (BJF_1997_AttenRelCoefficients) coefficientsSM.get(PGV_Param.NAME);
		double b_pgv = getRockMean();
		pgv = b_pgv + Math.log(getAmpFactor(PGV_Param.NAME));
		// Convert to linear domain (what's needed below)
		pgv = Math.exp(pgv);

		if (D) {
			System.out.println(" pgv = " + (float) pgv);
		}

		return Wald_MMI_Calc.getMMI(pga, pgv);

	}

	/**
	 * Calculates the mean for Rock using whatever set of coefficients were
	 * set before this method was called.
	 * The exact formula is: <p>
	 *
	 * double mean = b1 + <br>
	 * coeff.b2 * ( mag - 6 ) + <br>
	 * coeff.b3 * ( Math.pow( ( mag - 6 ), 2 ) ) +  <br>
	 * coeff.b5 * ( Math.log( Math.pow( ( distanceJB * distanceJB  + coeff.h * coeff.h  ), 0.5 ) ) ) + <br>
	 * coeff.bv * ( Math.log( rockVs30 / coeff.va ) ) <br>
	 * @return    The mean value
	 */
	private double getRockMean() {

		double mag, distanceJB;
		String fltTypeValue, willsSite;
		double rockVs30_SM = 620; // these values are from their code
		double rockVs30_BJF = 724;

		try {
			mag = ( (Double) magParam.getValue()).doubleValue();
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

		// Get b1 based on fault type
		double b1_BJF, b1_SM;
		if (fltTypeValue.equals(FLT_TYPE_STRIKE_SLIP)) {
			b1_BJF = coeffBJF.b1ss;
			b1_SM = coeffSM.b1ss;
		}
		else if (fltTypeValue.equals(FLT_TYPE_REVERSE)) {
			b1_BJF = coeffBJF.b1rv;
			b1_SM = coeffSM.b1rv;
		}
		else if (fltTypeValue.equals(FLT_TYPE_UNKNOWN)) {
			b1_BJF = coeffBJF.b1all;
			b1_SM = coeffSM.b1all;
		}
		else {
			throw new ParameterException(C +
					": getMean(): Invalid EqkRupture Parameter value for : FaultType");
		}

		// Calculate the log rock-site mean for BJF
		double meanBJF = b1_BJF +
		coeffBJF.b2 * (mag - 6) +
		coeffBJF.b3 * (Math.pow( (mag - 6), 2)) +
		coeffBJF.b5 *
		(Math.log(Math.pow( (distanceJB * distanceJB + coeffBJF.h * coeffBJF.h),
				0.5))) +
				coeffBJF.bv * (Math.log(rockVs30_BJF / coeffBJF.va));

		// Calculate the log rock-site mean for SM
		double meanSM = b1_SM +
		coeffSM.b2 * (mag - 6) +
		coeffSM.b3 * (Math.pow( (mag - 6), 2)) +
		coeffSM.b5 *
		(Math.log(Math.pow( (distanceJB * distanceJB + coeffSM.h * coeffSM.h),
				0.5))) +
				coeffSM.bv * (Math.log(rockVs30_SM / coeffSM.va));

		//correct it max horizontal is desired
		String component = (String) componentParam.getValue();
		if (component.equals(ComponentParam.COMPONENT_GREATER_OF_TWO_HORZ)) {
			meanSM += 0.139762; // add ln(1.15)
			meanBJF += 0.139762;
		}

		// now return the appropriate mean
		if (mag <= 5) {
			return meanSM;
		}
		else if (mag <= 5.5) {
			return meanBJF + (mag - 5.5) * (meanBJF - meanSM) / 0.5;
		}
		else {
			return meanBJF;
		}
	}

	/**
	 *  This overides the parent to take care if MMI is the chosen IMT.
	 *
	 * @return                         The intensity-measure level
	 * @exception  ParameterException  Description of the Exception
	 */
	public double getIML_AtExceedProb() throws ParameterException {

		if (im.getName().equals(MMI_Param.NAME)) {
			double exceedProb = ( (Double) ( (ParameterAPI) exceedProbParam).getValue()).
			doubleValue();
			if (exceedProb == 0.5) {
				if (sigmaTruncTypeParam.getValue().equals(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED)) {
					throw new RuntimeException(MMI_Param.MMI_ERROR_STRING);
				}
				else {
					return getMean();
				}
			}
			else {
				throw new RuntimeException(MMI_Param.MMI_ERROR_STRING);
			}
		}
		else {
			return super.getIML_AtExceedProb();
		}
	}

	/**
	 * @return    The stdDev value
	 */
	public double getStdDev() throws IMRException {

		// throw a runtime exception if trying for MMI
		if (im.getName().equals(MMI_Param.NAME)) {
			throw new RuntimeException(MMI_Param.MMI_ERROR_STRING);
		}

		String stdDevType = stdDevTypeParam.getValue().toString();
		String component = componentParam.getValue().toString();

		// get the magnitude
		double mag;
		try {
			mag = ( (Double) magParam.getValue()).doubleValue();
		}
		catch (NullPointerException e) {
			throw new IMRException(C + ": getMean(): " + ERR);
		}

		// this is inefficient if the im has not been changed in any way
		updateCoefficients();

		double stdevBJF, stdevSM;
		// set the correct standard deviation depending on component and type
		if (component.equals(ComponentParam.COMPONENT_AVE_HORZ) ||
				component.equals(ComponentParam.COMPONENT_GREATER_OF_TWO_HORZ)) {

			if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL)) { // "Total"
				stdevBJF = Math.pow( (coeffBJF.sigmaE * coeffBJF.sigmaE +
						coeffBJF.sigma1 * coeffBJF.sigma1), 0.5);
				stdevSM = Math.pow( (coeffSM.sigmaE * coeffSM.sigmaE +
						coeffSM.sigma1 * coeffSM.sigma1), 0.5);
			}
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER)) { // "Inter-Event"
				stdevBJF = coeffBJF.sigmaE;
				stdevSM = coeffSM.sigmaE;
			}
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA)) { // "Intra-Event"
				stdevBJF = (coeffBJF.sigma1);
				stdevSM = (coeffSM.sigma1);
			}
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) { // "None (zero)"
				stdevBJF = 0;
				stdevSM = 0;
			}
			else {
				throw new ParameterException(C + ": getStdDev(): Invalid StdDevType");
			}
		}
		else if (component.equals(ComponentParam.COMPONENT_RANDOM_HORZ)) {

			if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL)) { // "Total"
				stdevBJF = (coeffBJF.sigmaLnY);
				stdevSM = (coeffSM.sigmaLnY);
			}
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER)) { // "Inter-Event"
				stdevBJF = (coeffBJF.sigmaE);
				stdevSM = (coeffSM.sigmaE);
			}
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA)) { // "Intra-Event"
				stdevBJF = (coeffBJF.sigmaR);
				stdevSM = (coeffSM.sigmaR);
			}
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) { // "None (zero)"
				stdevBJF = 0;
				stdevSM = 0;
			}
			else {
				throw new ParameterException(C + ": getStdDev(): Invalid StdDevType");
			}
		}
		else {
			throw new ParameterException(C + ": getStdDev(): Invalid component type");
		}

		// now return the appropriate mean
		if (mag <= 5) {
			return stdevSM;
		}
		else if (mag <= 5.5) {
			return stdevBJF + (mag - 5.5) * (stdevBJF - stdevSM) / 0.5;
		}
		else {
			return stdevBJF;
		}

	}

	public void setParamDefaults() {

		//((ParameterAPI)this.iml).setValue( IML_DEFAULT );
		willsSiteParam.setValue(WILLS_SITE_DEFAULT);
		magParam.setValueAsDefault();
		fltTypeParam.setValueAsDefault();
		distanceJBParam.setValueAsDefault();
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
		meanIndependentParams.addParameter(distanceJBParam);
		meanIndependentParams.addParameter(willsSiteParam);
		meanIndependentParams.addParameter(magParam);
		meanIndependentParams.addParameter(fltTypeParam);
		meanIndependentParams.addParameter(componentParam);

		// params that the stdDev depends upon
		stdDevIndependentParams.clear();
		stdDevIndependentParams.addParameter(stdDevTypeParam);
		stdDevIndependentParams.addParameter(componentParam);
		stdDevIndependentParams.addParameter(magParam);

		// params that the exceed. prob. depends upon
		exceedProbIndependentParams.clear();
		exceedProbIndependentParams.addParameter(distanceJBParam);
		exceedProbIndependentParams.addParameter(willsSiteParam);
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
	 *  Creates the willsSiteParam site parameter and adds it to the siteParams list.
	 *  Makes the parameters noneditable.
	 */
	protected void initSiteParams() {

		// create and add the warning constraint:
		ArrayList willsSiteTypes = new ArrayList();
		willsSiteTypes.add(WILLS_SITE_B);
		willsSiteTypes.add(WILLS_SITE_BC);
		willsSiteTypes.add(WILLS_SITE_C);
		willsSiteTypes.add(WILLS_SITE_CD);
		willsSiteTypes.add(WILLS_SITE_D);
		willsSiteTypes.add(WILLS_SITE_DE);
		willsSiteTypes.add(WILLS_SITE_E);

		willsSiteParam = new StringParameter(WILLS_SITE_NAME, willsSiteTypes,
				WILLS_SITE_DEFAULT);
		willsSiteParam.setInfo(WILLS_SITE_INFO);
		willsSiteParam.setNonEditable();

		// add it to the siteParams list:
			siteParams.clear();
			siteParams.addParameter(willsSiteParam);

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
		constraint.addString(FLT_TYPE_REVERSE);
		constraint.setNonEditable();
		fltTypeParam = new FaultTypeParam(constraint,FLT_TYPE_UNKNOWN);

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
		Enumeration keys = coefficientsBJF.keys();
		while (keys.hasMoreElements()) {
			BJF_1997_AttenRelCoefficients coeff = (BJF_1997_AttenRelCoefficients)
			coefficientsBJF.get(keys.nextElement());
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

		// The MMI parameter
		mmiParam = new MMI_Param();

		// Add the warning listeners:
		saParam.addParameterChangeWarningListener(warningListener);
		pgaParam.addParameterChangeWarningListener(warningListener);
		pgvParam.addParameterChangeWarningListener(warningListener);

		// create supported list
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
		constraint.addString(ComponentParam.COMPONENT_RANDOM_HORZ);
		constraint.addString(ComponentParam.COMPONENT_GREATER_OF_TWO_HORZ);
		constraint.setNonEditable();
		componentParam = new ComponentParam(constraint,componentParam.COMPONENT_AVE_HORZ);

		// the stdDevType Parameter
		StringConstraint stdDevTypeConstraint = new StringConstraint();
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTER);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTRA);
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

		// Make the ShakeMap coefficients
		coefficientsSM.clear();
		// Note that the coefficients in "the APPENDIX" that David Wald sent to me (Ned) on 8/27/07
		// assume that all logs in their equation are base-10 (in spite of their using "ln" for
		// two of the terms).  Thus, thier B1, B2, and Sigma values need to be multiplied by 2.3025.
		// Also, since their units are gals their B1 needs to have ln(980) subtracted from it
		// (except for PGV).
		// PGA
		BJF_1997_AttenRelCoefficients coeffSM0 = new BJF_1997_AttenRelCoefficients(
				PGA_Param.NAME,
				-1, 2.408, 2.408, 2.408, 1.3171, 0.000, -1.757, -0.473, 760, 6.0,
				0.660, 0.328, 0.737, 0.3948, 0.836);
		// SA/0.00
		BJF_1997_AttenRelCoefficients coeffSM1 = new BJF_1997_AttenRelCoefficients(
				SA_Param.NAME + '/' + (new Double("0.00")).doubleValue(),
				0.00, 2.408, 2.408, 2.408, 1.3171, 0.000, -1.757, -0.473, 760, 6.0,
				0.660, 0.328, 0.737, 0.3948, 0.836);
		// Note: no sigma values were available for those below (Vince needs to recompute them)
		//       (those above came from Vince via personal communication)
		//       therefore, I multiplied those above by ratio of the sigmas given in the table in
		//       "the APPENDIX" David sent to me (Ned).  These are labeled as "Sigma" in their table
		//       with no further explanation; using the ratios seems reasonable.
		// SA/0.30
		BJF_1997_AttenRelCoefficients coeffSM2 = new BJF_1997_AttenRelCoefficients(
				"SA/" + (new Double("0.30")).doubleValue(),
				0.30, 0.835318, 0.835318, 0.835318, 1.71773, 0.000, -1.827, -0.608, 760,
				6.0,
				(0.842 / 0.836) * 0.660, (0.842 / 0.836) * 0.328,
				(0.842 / 0.836) * 0.737, (0.842 / 0.836) * 0.3948,
				(0.842 / 0.836) * 0.836);
		// SA/1.00
		BJF_1997_AttenRelCoefficients coeffSM3 = new BJF_1997_AttenRelCoefficients(
				"SA/" + (new Double("1.00")).doubleValue(),
				1.00, -1.82877, -1.82877, -1.82877, 2.20818, 0.000, -1.211, -0.974, 760,
				6.0,
				(0.988 / 0.836) * 0.660, (0.988 / 0.836) * 0.328,
				(0.988 / 0.836) * 0.737, (0.988 / 0.836) * 0.3948,
				(0.988 / 0.836) * 0.836);
		// SA/3.00 - actually these are BJF's 2-second values
		BJF_1997_AttenRelCoefficients coeffSM4 = new BJF_1997_AttenRelCoefficients(
				"SA/" + (new Double("3.00")).doubleValue(),
				3.00, -4.63102, -4.63102, -4.63102, 2.09305, 0.000, -0.848, -0.890, 760,
				6.0,
				(1.082 / 0.836) * 0.660, (1.082 / 0.836) * 0.328,
				(1.082 / 0.836) * 0.737, (1.082 / 0.836) * 0.3948,
				(1.082 / 0.836) * 0.836);
		// PGV - They actually give PGV coeffs so no scaling of 1-sec SA is needed.
		BJF_1997_AttenRelCoefficients coeffSM5 = new BJF_1997_AttenRelCoefficients(
				PGV_Param.NAME,
				-1, 5.1186, 5.1186, 5.1186, 1.70391, 0.000, -1.386, -0.668, 760, 6.0,
				(0.753 / 0.836) * 0.660, (0.753 / 0.836) * 0.328,
				(0.753 / 0.836) * 0.737, (0.753 / 0.836) * 0.3948,
				(0.753 / 0.836) * 0.836);

		// add these to the list
		coefficientsSM.put(coeffSM0.getName(), coeffSM0);
		coefficientsSM.put(coeffSM1.getName(), coeffSM1);
		coefficientsSM.put(coeffSM2.getName(), coeffSM2);
		coefficientsSM.put(coeffSM3.getName(), coeffSM3);
		coefficientsSM.put(coeffSM4.getName(), coeffSM4);
		coefficientsSM.put(coeffSM5.getName(), coeffSM5);

		// Now make the original BJF 1997 coefficients
		coefficientsBJF.clear();
		// PGA
		BJF_1997_AttenRelCoefficients coeff0 = new BJF_1997_AttenRelCoefficients(
				PGA_Param.NAME,
				-1, -0.313, -0.117, -0.242, 0.527, 0.000, -0.778, -0.371, 1396, 5.57,
				0.431, 0.226, 0.486, 0.184, 0.520);
		// SA/0.00
		BJF_1997_AttenRelCoefficients coeff1 = new BJF_1997_AttenRelCoefficients(
				SA_Param.NAME + '/' + (new Double("0.00")).doubleValue(),
				0.00, -0.313, -0.117, -0.242, 0.527, 0, -0.778, -0.371, 1396, 5.57,
				0.431, 0.226, 0.486, 0.184, 0.520);
		// SA/0.30
		BJF_1997_AttenRelCoefficients coeff2 = new BJF_1997_AttenRelCoefficients(
				"SA/" + (new Double("0.30")).doubleValue(),
				0.30, 0.598, 0.803, 0.7, 0.769, -0.161, -0.893, -0.401, 2133, 5.94,
				0.440, 0.276, 0.519, 0.048, 0.522);
		// SA/1.00
		BJF_1997_AttenRelCoefficients coeff3 = new BJF_1997_AttenRelCoefficients(
				"SA/" + (new Double("1.00")).doubleValue(),
				1.00, -1.133, -1.009, -1.08, 1.036, -0.032, -0.798, -0.698, 1406, 2.9,
				0.474, 0.325, 0.575, 0.214, 0.613);
		// SA/3.00 - actually these are BJF's 2-second values
		BJF_1997_AttenRelCoefficients coeff4 = new BJF_1997_AttenRelCoefficients(
				"SA/" + (new Double("3.00")).doubleValue(),
				3.00, -1.699, -1.801, -1.743, 1.085, -0.085, -0.812, -0.655, 1795, 5.85,
				0.495, 0.362, 0.613, 0.276, 0.672);
		// PGV - these are actually from 1-sec SA using the Newmark & Hall (1982).  According to the ShakeMap docs this
		// scaling factor is PGV = (37.27*2.54)*SA1.0
		// The following formula is slightly more accurate (from Ken Campbell)
		double SA10toPGV = Math.log(981.0 / (2.0 * Math.PI * 1.65));
		BJF_1997_AttenRelCoefficients coeff5 = new BJF_1997_AttenRelCoefficients(
				PGV_Param.NAME,
				-1, -1.133 + SA10toPGV, -1.009 + SA10toPGV, -1.08 + SA10toPGV, 1.036,
				-0.032, -0.798, -0.698, 1406, 2.9, 0.474, 0.325, 0.575, 0.214, 0.613);

		// add these to the list
		coefficientsBJF.put(coeff0.getName(), coeff0);
		coefficientsBJF.put(coeff1.getName(), coeff1);
		coefficientsBJF.put(coeff2.getName(), coeff2);
		coefficientsBJF.put(coeff3.getName(), coeff3);
		coefficientsBJF.put(coeff4.getName(), coeff4);
		coefficientsBJF.put(coeff5.getName(), coeff5);

	}

	/**
	 *  <b>Title:</b> BJF_1997_AttenRelCoefficients<br>
	 *  <b>Description:</b> This class encapsulates all the
	 *  coefficients needed to calculate the Mean and StdDev for
	 *  the BJF_1997_AttenRel.  One instance of this class holds the set of
	 *  coefficients for each period (one row of their table 8).<br>
	 *  <b>Copyright:</b> Copyright (c) 2001 <br>
	 *  <b>Company:</b> <br>
	 *
	 *
	 * @author     Steven W Rock
	 * @created    February 27, 2002
	 * @version    1.0
	 */

	class BJF_1997_AttenRelCoefficients
	implements NamedObjectAPI {

		protected final static String C = "BJF_1997_AttenRelCoefficients";
		protected final static boolean D = false;
		/** For serialization. */
		private static final long serialVersionUID = 1234567890987654320L;


		protected String name;
		protected double period = -1;
		protected double b1all;
		protected double b1ss;
		protected double b1rv;
		protected double b2;
		protected double b3;
		protected double b5;
		protected double bv;
		protected int va;
		protected double h;
		protected double sigma1;
		protected double sigmaC;
		protected double sigmaR;
		protected double sigmaE;
		protected double sigmaLnY;

		/**
		 *  Constructor for the BJF_1997_AttenRelCoefficients object
		 *
		 * @param  name  Description of the Parameter
		 */
		public BJF_1997_AttenRelCoefficients(String name) {
			this.name = name;
		}

		/**
		 *  Constructor for the BJF_1997_AttenRelCoefficients object that sets all values at once
		 *
		 * @param  name  Description of the Parameter
		 */
		public BJF_1997_AttenRelCoefficients(String name, double period,
				double b1ss, double b1rv, double b1all,
				double b2, double b3,
				double b5, double bv, int va, double h,
				double sigma1, double sigmaC,
				double sigmaR, double sigmaE,
				double sigmaLnY
		) {
			this.period = period;
			this.b1ss = b1ss;
			this.b1rv = b1rv;
			this.b1all = b1all;
			this.b2 = b2;
			this.b3 = b3;
			this.b5 = b5;
			this.bv = bv;
			this.va = va;
			this.h = h;
			this.name = name;
			this.sigma1 = sigma1;
			this.sigmaC = sigmaC;
			this.sigmaR = sigmaR;
			this.sigmaE = sigmaE;
			this.sigmaLnY = sigmaLnY;
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
			b.append("\n  b1all = " + b1all);
			b.append("\n  b1ss = " + b1ss);
			b.append("\n  b1rv = " + b1rv);
			b.append("\n  b2 = " + b2);
			b.append("\n  b3 = " + b3);
			b.append("\n  b5 = " + b5);
			b.append("\n  bv = " + bv);
			b.append("\n va = " + va);
			b.append("\n  h = " + h);
			b.append("\n  sigma1 = " + sigma1);
			b.append("\n  sigmaC = " + sigmaC);
			b.append("\n  sigmaR = " + sigmaR);
			b.append("\n  sigmaE = " + sigmaE);
			b.append("\n  sigmaLnY = " + sigmaLnY);
			return b.toString();
		}
	}

	// this is temporary for testing purposes
	public static void main(String[] args) {
		System.out.println( (981.0 / (2.0 * Math.PI * 1.65)));
		new ShakeMap_2003_AttenRel(null);
	}

	/**
	 * This provides a URL where more info on this model can be obtained
	 * @throws MalformedURLException if returned URL is not a valid URL.
	 * @returns the URL to the AttenuationRelationship document on the Web.
	 */
	public URL getInfoURL() throws MalformedURLException{
		return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/ShakeMap_2003.html");
	}

}
