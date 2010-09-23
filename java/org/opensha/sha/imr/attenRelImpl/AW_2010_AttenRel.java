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
 * http://www.apache.org/licenses/LICENSE-2.0
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

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;

import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.MMI_Param;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceHypoParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

/**
 * <b>Title:</b> AW_2010_AttenRel
 * <p>
 * 
 * <b>Description:</b> This implements the Attenuation Relationship published by
 * Allen & Wald in 2010 TODO: Add correct equation reference (2010, "...
 * <p>
 * 
 * Supported Intensity-Measure Parameters:
 * <p>
 * <UL>
 * <LI>mmiParam - Modified Mercalli Intensity
 * </UL>
 * <p>
 * Other Independent Parameters:
 * <p>
 * <UL>
 * <LI>magParam - moment magnitude
 * <LI>distanceRupParam - closest distance to rupture km
 * <LI>stdDevTypeParam - the type of standard deviation
 * </UL>
 * </p>
 * <p>
 * NOTES:
 * <p>
 * Verification : Verification tables provided by Damiano using Excel spread
 * sheet
 * </p>
 * 
 * @authors		Aurea Moemke, Damiano Monelli
 * @created 	22 September 2010, Additional AW_2010 implementation
 * @version 	1.0
 */

public class AW_2010_AttenRel extends AttenuationRelationship implements
		ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI,
		ParameterChangeListener {

	// Debugging stuff
	private final static String C = "AW_2010_AttenRel";
	private final static boolean D = false;
	public final static String SHORT_NAME = "AW2010";
	private static final long serialVersionUID = 1234567890987654358L;

	// Name of IMR
	public final static String NAME = "Allen & Wald (2010)";

	// Equation constants for finite rupture
	private static final double c0FiniteRup = 3.154;
	private static final double c1FiniteRup = 1.03;
	private static final double c2FiniteRup = -1.113;
	private static final double c3FiniteRup = 0.722;
	private static final double s1FiniteRup = 0.66;
	private static final double s2FiniteRup = 0.31;
	private static final double s3FiniteRup = 39;
	private static final double sigma2FiniteRup = 0.21;

	// Equation constants for point rupture
	private static final double c0PointRup = 3.471;
	private static final double c1PointRup = 1.392;
	private static final double c2PointRup = -1.77;
	private static final double c4PointRup = 0.3699;
	private static final double m1PointRup = 2.389;
	private static final double m2PointRup = 1.508;
	private static final double s1PointRup = 0.75;
	private static final double s2PointRup = 0.43;
	private static final double s3PointRup = 29.6;
	private static final double sigma2PointRup = 0.4;

	// closest distance to rupture
	private double rRup;
	// hypocentral distance
	private double rHypo;
	// Rupture magnitude
	private double mag;
	// Standard Dev type
	private String stdDevType;

	private boolean parameterChange;

	// values for warning parameters
	protected final static Double MAG_WARN_MIN = new Double(5.0);
	protected final static Double MAG_WARN_MAX = new Double(8.0);
	protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
	protected final static Double DISTANCE_RUP_WARN_MAX = new Double(300.0);

	// for issuing warnings:
	private transient ParameterChangeWarningListener warningListener = null;

	/**
	 * This initializes several ParameterList objects.
	 */
	public AW_2010_AttenRel(ParameterChangeWarningListener warningListener) {

		super();

		this.warningListener = warningListener;
		initSupportedIntensityMeasureParams();
		initEqkRuptureParams();
		initPropagationEffectParams();
		initSiteParams();
		initOtherParams();
		initIndependentParamLists(); // This must be called after the above
		initParameterEventListeners(); // add the change listeners to the
		// parameters
	}

	/**
	 * Creates the supported IM parameter (MMI) and add it to the
	 * supportedIMParams list. Makes the parameters noneditable.
	 */
	protected void initSupportedIntensityMeasureParams() {
		// Create MMI Parameter (mmiParam):
		mmiParam = new MMI_Param();
		mmiParam.setNonEditable();
		// Add the warning listeners:
		mmiParam.addParameterChangeWarningListener(warningListener);
		// Put parameters in the supportedIMParams list:
		supportedIMParams.clear();
		supportedIMParams.addParameter(mmiParam);
	}

	/**
	 * Creates the single Potential Earthquake parameter (magParam) and and adds
	 * it to the eqkRuptureParams list. Makes the parameter noneditable.
	 */
	protected void initEqkRuptureParams() {
		magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);
		eqkRuptureParams.clear();
		eqkRuptureParams.addParameter(magParam);
	}

	/**
	 * Creates the Propagation Effect parameters and adds them to the
	 * propagationEffectParams list. Makes the parameters noneditable.
	 */
	protected void initPropagationEffectParams() {
		distanceRupParam = new DistanceRupParameter(0.0);
		DoubleConstraint warn = new DoubleConstraint(DISTANCE_RUP_WARN_MIN,
				DISTANCE_RUP_WARN_MAX);
		warn.setNonEditable();
		distanceRupParam.setWarningConstraint(warn);
		distanceRupParam.addParameterChangeWarningListener(warningListener);
		distanceRupParam.setNonEditable();

		propagationEffectParams.addParameter(distanceRupParam);

		distanceHypoParam = new DistanceHypoParameter(0.0);
		warn = new DoubleConstraint(DISTANCE_RUP_WARN_MIN,
				DISTANCE_RUP_WARN_MAX);
		warn.setNonEditable();
		distanceHypoParam.setWarningConstraint(warn);
		distanceHypoParam.addParameterChangeWarningListener(warningListener);
		distanceHypoParam.setNonEditable();

		propagationEffectParams.addParameter(distanceHypoParam);
	}

	/**
	 * Creates the Site-Type parameter and adds it to the siteParams list. Makes
	 * the parameters noneditable.
	 */
	protected void initSiteParams() {
		// no site params are needed by this equation
		siteParams.clear();
	}

	/**
	 * Creates other Parameters that the mean or stdDev depends upon, in this
	 * case the StdDevType parameter.
	 */
	protected void initOtherParams() {
		// init other params defined in parent class
		super.initOtherParams();
		// the stdDevType Parameter
		StringConstraint stdDevTypeConstraint = new StringConstraint();
		// the total std is the only one supported
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
		stdDevTypeConstraint.setNonEditable();
		stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);
		// add these to the list
		otherParams.addParameter(stdDevTypeParam);
	}

	/**
	 * This creates the lists of independent parameters that the various
	 * dependent parameters (mean, standard deviation, exceedance probability,
	 * and IML at exceedance probability) depend upon. NOTE: these lists do not
	 * include anything about the intensity-measure parameters or any of their
	 * internal independentParamaters.
	 */
	protected void initIndependentParamLists() {

		// params that the mean depends upon
		meanIndependentParams.clear();
		meanIndependentParams.addParameter(distanceRupParam);
		meanIndependentParams.addParameter(distanceHypoParam);
		meanIndependentParams.addParameter(magParam);

		// params that the stdDev depends upon
		stdDevIndependentParams.clear();
		stdDevIndependentParams.addParameterList(meanIndependentParams);
		stdDevIndependentParams.addParameter(stdDevTypeParam);

		// params that the exceed. prob. depends upon
		exceedProbIndependentParams.clear();
		exceedProbIndependentParams.addParameterList(stdDevIndependentParams);
		exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
		exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

		// params that the IML at exceed. prob. depends upon
		imlAtExceedProbIndependentParams
				.addParameterList(exceedProbIndependentParams);
		imlAtExceedProbIndependentParams.addParameter(exceedProbParam);
	}

	/**
	 * Adds the parameter change listeners. This allows to listen to when-ever
	 * the parameter is changed.
	 */
	protected void initParameterEventListeners() {
		distanceRupParam.addParameterChangeListener(this);
		distanceHypoParam.addParameterChangeListener(this);
		magParam.addParameterChangeListener(this);
		stdDevTypeParam.addParameterChangeListener(this);
	}

	public void setParamDefaults() {
		magParam.setValueAsDefault();
		distanceRupParam.setValueAsDefault();
		distanceHypoParam.setValueAsDefault();
		mmiParam.setValueAsDefault();
		stdDevTypeParam.setValueAsDefault();

		rRup = ((Double) distanceRupParam.getValue()).doubleValue();
		rHypo = ((Double) distanceHypoParam.getValue()).doubleValue();
		mag = ((Double) magParam.getValue()).doubleValue();
		stdDevType = (String) stdDevTypeParam.getValue();
	}

	/**
	 * This sets the eqkRupture related parameters (magParam) based on the
	 * eqkRupture passed in. The internally held eqkRupture object is also set
	 * as that passed in. Warning constraints are not ignored.
	 * 
	 * @param eqkRupture
	 *            The new eqkRupture value
	 */
	public void setEqkRupture(EqkRupture eqkRupture)
			throws InvalidRangeException {
		// set magnitude value
		magParam.setValue(new Double(eqkRupture.getMag()));
		// initialize earthquake object
		this.eqkRupture = eqkRupture;
		setPropagationEffectParams();
	}

	/**
	 * This sets the internally held Site object as that passed in.
	 * 
	 * @param site
	 *            The new site object
	 */
	public void setSite(Site site) throws ParameterException {
		this.site = site;
		setPropagationEffectParams();
	}

	/**
	 * This set the distance rupture param as closest distance to the rupture
	 */
	protected void setPropagationEffectParams() {
		if ((this.site != null) && (this.eqkRupture != null)) {
			distanceRupParam.setValue(eqkRupture, site);
			distanceHypoParam.setValue(eqkRupture, site);
		}
	}

	/**
	 * This returns the mean MMI value
	 * which depends on the rupture type finite or point source
	 * 
	 * @return The mean value
	 */

	public double getMean() {

		double mean = Double.NaN;

		EvenlyGriddedSurfaceAPI eqkSurf = eqkRupture.getRuptureSurface();

		if (eqkSurf.getNumCols() == 1 && eqkSurf.getNumRows() == 1) {
			// point rupture 
			mean = getMeanForPointRup(mag, rHypo, this.c0PointRup,
					this.c1PointRup, this.c2PointRup, this.c4PointRup,
					this.m1PointRup, this.m2PointRup);
		} else {
			// finite rupture
			mean = getMeanForFiniteRup(mag, rRup, this.c0FiniteRup,
					this.c1FiniteRup, this.c2FiniteRup, this.c3FiniteRup);
		}
		return mean;
	}

	/**
	 * This returns the standard deviation value
	 * which depends on the rupture type finite or point source
	 * 
	 * @return The standard deviation value
	 */

	public double getStdDev() {

		double stdDev = Double.NaN;

		if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) {
			stdDev = 0.0;
		} else {
			EvenlyGriddedSurfaceAPI eqkSurf = eqkRupture.getRuptureSurface();

			if (eqkSurf.getNumCols() == 1 && eqkSurf.getNumRows() == 1) {
				// point source
				stdDev = getStdDev(rHypo, this.s1PointRup, this.s2PointRup,
						this.s3PointRup, this.sigma2PointRup);
			} else {
				// finite source
				stdDev = getStdDev(rRup, this.s1FiniteRup, this.s2FiniteRup,
						this.s3FiniteRup, this.sigma2FiniteRup);
			}
		}
		return stdDev;
	}

	/**
	 * Returns the Mean MMI Value for finite ruptures given a
	 * set of parameters.
	 * 
	 * @param Mw
	 * @param Rrup
	 * @param c0
	 * @param c1
	 * @param c2
	 * @param c3
	 * @return
	 */
	public double getMeanForFiniteRup(double Mw, double Rrup, double c0,
			double c1, double c2, double c3) {

		double mmi = 0;
		mmi = c0
				+ c1
				* Mw
				+ c2
				* Math.log(Math.sqrt((Math.pow(Rrup, 2))
						+ Math.pow((1 + (c3 * Math.exp(Mw - 5))), 2)));

		return mmi;
	}

	/**
	 * Returns the Mean MMI Value for point ruptures given a
	 * set of parameters.
	 * 
	 * @param Mw
	 * @param Rhypo
	 * @param c0
	 * @param c1
	 * @param c2
	 * @param c4
	 * @param m1
	 * @param m2
	 * @return
	 */
	public double getMeanForPointRup(double Mw, double Rhypo, double c0,
			double c1, double c2, double c4, double m1, double m2) {

		double mmi = 0;
		double rm = 0;
		rm = m1 + m2 * Math.exp(Mw - 5);
		if (Rhypo <= 20) {
			mmi = c0 + c1 * Mw + c2
					* Math.log(Math.sqrt(Math.pow(Rhypo, 2) + Math.pow(rm, 2)));
		} else {
			mmi = c0 + c1 * Mw + c2
					* Math.log(Math.sqrt(Math.pow(Rhypo, 2) + Math.pow(rm, 2)))
					+ c4 * Math.log(Rhypo / 20);
		}
		return mmi;

	}

	/**
	 * Returns the Standard deviation for a set of parameters.
	 * 
	 * @param R (either Rrup for finite rupture OR Rhypo for Point rupture)
	 * @param s1
	 * @param s2
	 * @param s3
	 * @param sigma2
	 * @return double
	 */
	public double getStdDev(double R, double s1, double s2, double s3,
			double sigma2) {

		double sigma1 = s1 + (s2 / (1 + Math.pow((R / s3), 2)));
		double sigma = Math.sqrt(Math.pow(sigma1, 2) + Math.pow(sigma2, 2));
		return sigma;

	}

	/**
	 * Get the name of this IMR
	 * 
	 * @returns the name of this IMR
	 */
	public String getName() {
		return NAME;
	}

	/**
	 * Returns the Short Name of each AttenuationRelationship
	 * 
	 * @return String
	 */
	public String getShortName() {
		return SHORT_NAME;
	}

	/**
	 * This provides a URL where more info on this model can be obtained
	 * 
	 * @throws MalformedURLException
	 *             if returned URL is not a valid URL.
	 * @returns the URL to the AttenuationRelationship document on the Web.
	 */
	public URL getInfoURL() throws MalformedURLException {
		return null;
	}

	public void parameterChange(ParameterChangeEvent e) {
		String pName = e.getParameterName();
		Object val = e.getNewValue();
		parameterChange = true;
		if (pName.equals(DistanceRupParameter.NAME)) {
			rRup = ((Double) val).doubleValue();
		} else if (pName.equals(MagParam.NAME)) {
			mag = ((Double) val).doubleValue();
		} else if (pName.equals(StdDevTypeParam.NAME)) {
			stdDevType = (String) val;
		}

	}

	/**
	 * Allows to reset the change listeners on the parameters
	 */
	public void resetParameterEventListeners() {
		distanceRupParam.removeParameterChangeListener(this);
		magParam.removeParameterChangeListener(this);
		stdDevTypeParam.removeParameterChangeListener(this);

		this.initParameterEventListeners();
	}

	public double getMeanForFiniteRup(double Mw, double Rrup) {

		double mmi = 0;
		mmi = this.c0FiniteRup
				+ this.c1FiniteRup
				* Mw
				+ this.c2FiniteRup
				* Math.log(Math.sqrt((Math.pow(Rrup, 2))
						+ Math.pow((1 + (this.c3FiniteRup * Math.exp(Mw - 5))),
								2)));

		return mmi;
	}

	public double getMeanForPointRup(double Mw, double Rhypo) {

		double mmi = 0;
		double rm = 0;
		rm = this.m1PointRup + this.m2PointRup * Math.exp(Mw - 5);
		if (Rhypo <= 20) {
			mmi = this.c0PointRup + this.c1PointRup * Mw + this.c2PointRup
					* Math.log(Math.sqrt(Math.pow(Rhypo, 2) + Math.pow(rm, 2)));
		} else {
			mmi = this.c0PointRup + this.c1PointRup * Mw + this.c2PointRup
					* Math.log(Math.sqrt(Math.pow(Rhypo, 2) + Math.pow(rm, 2)))
					+ this.c4PointRup * Math.log(Rhypo / 20);
		}

		return mmi;
	}

	public double getStdDevForFiniteRup(double R) {

		double sigma1 = this.s1FiniteRup
				+ (this.s2FiniteRup / (1 + Math.pow((R / this.s3FiniteRup), 2)));
		double sigma = Math.sqrt(Math.pow(sigma1, 2)
				+ Math.pow(this.sigma2FiniteRup, 2));
		return sigma;

	}

	public double getStdDevForPointRup(double R) {

		double sigma1 = this.s1PointRup
				+ (this.s2PointRup / (1 + Math.pow((R / this.s3PointRup), 2)));
		double sigma = Math.sqrt(Math.pow(sigma1, 2)
				+ Math.pow(this.sigma2PointRup, 2));
		return sigma;

	}

}
