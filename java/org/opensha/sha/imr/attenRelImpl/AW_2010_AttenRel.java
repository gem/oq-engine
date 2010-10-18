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
 * <b>Description:</b> This class implements the Allen and Wald 2010 intensity
 * prediction equation (IPE): "Prediction of macroseismic intensities for global
 * active crustal earthquakes", J.Seismol. At the time of this implementation,
 * the paper is not yet published. The current implementation is based on the
 * Perl module that implements this equation in the ShakeMap software (the
 * module was provided by Georgia Cua to Damiano Monelli). Verification tables
 * have been provided by Damiano Monelli as an Excel spreadsheet. According to
 * Georgia's comments, the IPE is technically designed for 5 < M < 7.9,
 * intensity > 2, and R < 300 kms. TODO: Once the paper is published, revise the
 * implementation and possibly ask for verification tables directly from the
 * original authors.
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
 * </p>
 * 
 * @authors Aurea Moemke, Damiano Monelli
 * @created 22 September 2010
 * @version 1.0
 */

public class AW_2010_AttenRel extends AttenuationRelationship implements
        ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI,
        ParameterChangeListener {

    private final static String C = "AW_2010_AttenRel";
    private final static boolean D = false;
    public final static String SHORT_NAME = "AW2010";
    private static final long serialVersionUID = 1234567890987654358L;

    // IPE full name
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

    // Closest distance to rupture
    private double rRup;
    // Hypocentral distance
    private double rHypo;
    // Rupture magnitude
    private double mag;
    // Standard Dev type
    private String stdDevType;

    private boolean parameterChange;

    // Values for warning parameters
    protected final static Double MAG_WARN_MIN = new Double(5.0);
    protected final static Double MAG_WARN_MAX = new Double(8.0);
    protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
    protected final static Double DISTANCE_RUP_WARN_MAX = new Double(300.0);

    // For issuing warnings:
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
        initIndependentParamLists();
        initParameterEventListeners();
    }

    /**
     * Creates the supported IM parameter (MMI Parameter) and add it to the
     * supportedIMParams list. Makes the parameters noneditable.
     * 
     */
    protected void initSupportedIntensityMeasureParams() {
        mmiParam = new MMI_Param();
        mmiParam.setNonEditable();
        mmiParam.addParameterChangeWarningListener(warningListener);
        supportedIMParams.clear();
        supportedIMParams.addParameter(mmiParam);
    }

    /**
     * Creates magnitude parameter and adds it to the eqkRuptureParams list.
     * Makes the parameter noneditable.
     * 
     */
    protected void initEqkRuptureParams() {
        magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);
        eqkRuptureParams.clear();
        eqkRuptureParams.addParameter(magParam);
    }

    /**
     * Creates the Propagation Effect parameters and adds them to the
     * propagationEffectParams list. These are the distanceRupParam (closest
     * distance to rupture, used for finite ruptures), and distanceHypoParam
     * (hypocentral distance, used for point ruptures). Make the parameters
     * noneditable.
     * 
     */
    protected void initPropagationEffectParams() {
        distanceRupParam = new DistanceRupParameter(0.0);
        DoubleConstraint warn =
                new DoubleConstraint(DISTANCE_RUP_WARN_MIN,
                        DISTANCE_RUP_WARN_MAX);
        warn.setNonEditable();
        distanceRupParam.setWarningConstraint(warn);
        distanceRupParam.addParameterChangeWarningListener(warningListener);
        distanceRupParam.setNonEditable();
        propagationEffectParams.addParameter(distanceRupParam);

        distanceHypoParam = new DistanceHypoParameter(0.0);
        warn =
                new DoubleConstraint(DISTANCE_RUP_WARN_MIN,
                        DISTANCE_RUP_WARN_MAX);
        warn.setNonEditable();
        distanceHypoParam.setWarningConstraint(warn);
        distanceHypoParam.addParameterChangeWarningListener(warningListener);
        distanceHypoParam.setNonEditable();
        propagationEffectParams.addParameter(distanceHypoParam);
    }

    /**
     * Creates the Site-Type parameter and adds it to the siteParams list. Makes
     * the parameters noneditable. For this equation, no site parameters are
     * needed.
     * 
     */
    protected void initSiteParams() {
        siteParams.clear();
    }

    /**
     * Creates other Parameters that the mean or stdDev depends upon, in this
     * case, the StdDevType parameter. Only STD_DEV_TYPE_TOTAL is supported.
     * 
     */
    protected void initOtherParams() {
        super.initOtherParams();
        StringConstraint stdDevTypeConstraint = new StringConstraint();
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
        stdDevTypeConstraint.setNonEditable();
        stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);
        otherParams.addParameter(stdDevTypeParam);
    }

    /**
     * Creates the lists of independent parameters that the various dependent
     * parameters (mean, standard deviation, exceedance probability, and IML at
     * exceedance probability) depends upon. NOTE: these lists do not include
     * anything about the intensity-measure parameters or any of their internal
     * independentParamaters.
     * 
     */
    protected void initIndependentParamLists() {

        meanIndependentParams.clear();
        meanIndependentParams.addParameter(distanceRupParam);
        meanIndependentParams.addParameter(distanceHypoParam);
        meanIndependentParams.addParameter(magParam);

        stdDevIndependentParams.clear();
        stdDevIndependentParams.addParameterList(meanIndependentParams);
        stdDevIndependentParams.addParameter(stdDevTypeParam);

        exceedProbIndependentParams.clear();
        exceedProbIndependentParams.addParameterList(stdDevIndependentParams);
        exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
        exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

        imlAtExceedProbIndependentParams
                .addParameterList(exceedProbIndependentParams);
        imlAtExceedProbIndependentParams.addParameter(exceedProbParam);
    }

    /**
     * Adds the parameter change listeners. This allows to listen to when-ever
     * the parameter is changed.
     * 
     */
    protected void initParameterEventListeners() {
        distanceRupParam.addParameterChangeListener(this);
        distanceHypoParam.addParameterChangeListener(this);
        magParam.addParameterChangeListener(this);
        stdDevTypeParam.addParameterChangeListener(this);
    }

    /**
     * Sets parameter defaults.
     * 
     */
    public void setParamDefaults() {
        magParam.setValueAsDefault();
        distanceRupParam.setValueAsDefault();
        distanceHypoParam.setValueAsDefault();
        mmiParam.setValueAsDefault();
        stdDevTypeParam.setValueAsDefault();
    }

    /**
     * Sets the eqkRupture related parameters (magParam) based on the passed
     * eqkRupture. The internally held eqkRupture object is set to the passed
     * parameter. Warning constraints are not ignored.
     * 
     * @param eqkRupture
     * 
     */
    public void setEqkRupture(EqkRupture eqkRupture)
            throws InvalidRangeException {
        magParam.setValue(new Double(eqkRupture.getMag()));
        this.eqkRupture = eqkRupture;
        setPropagationEffectParams();
    }

    /**
     * Sets the internally held Site object to the passed site parameter.
     * 
     * @param site
     * 
     */
    public void setSite(Site site) throws ParameterException {
        this.site = site;
        setPropagationEffectParams();
    }

    /**
     * Sets the distance rupture parameter as the closest distance to the
     * rupture.
     * 
     */
    protected void setPropagationEffectParams() {
        if ((this.site != null) && (this.eqkRupture != null)) {
            distanceRupParam.setValue(eqkRupture, site);
            distanceHypoParam.setValue(eqkRupture, site);
        }
    }

    /**
     * Returns the mean MMI value depending on the rupture type (finite or
     * point). Earthquake rupture surfaces containing only one Location (numCols
     * and numRows equal 1) are point sources, and finite sources otherwise.
     * 
     * @return double
     * 
     */
    public double getMean() {
        double mean = Double.NaN;
        EvenlyGriddedSurfaceAPI eqkSurf = eqkRupture.getRuptureSurface();
        if (eqkSurf.getNumCols() == 1 && eqkSurf.getNumRows() == 1) {
            mean = getMeanForPointRup(mag, rHypo);
        } else {
            mean = getMeanForFiniteRup(mag, rRup);
        }
        return mean;
    }

    /**
     * Returns the standard deviation value depending on the rupture type
     * (finite or point). Earthquake rupture surfaces containing only one
     * Location (numCols and numRows equal 1) are point sources, and finite
     * sources otherwise.
     * 
     * @return double
     * 
     */
    public double getStdDev() {
        double stdDev = Double.NaN;
        if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) {
            stdDev = 0.0;
        } else {
            EvenlyGriddedSurfaceAPI eqkSurf = eqkRupture.getRuptureSurface();
            if (eqkSurf.getNumCols() == 1 && eqkSurf.getNumRows() == 1) {
                stdDev = getStdDevForPointRup(rHypo);
            } else {
                stdDev = getStdDevForFiniteRup(rRup);
            }
        }
        return stdDev;
    }

    /**
     * Returns the name of this IMR
     * 
     * @return String
     * 
     */
    public String getName() {
        return NAME;
    }

    /**
     * Returns the Short Name of the Attenuation Relationship
     * 
     * @return String
     * 
     */
    public String getShortName() {
        return SHORT_NAME;
    }

    /**
     * Returns a URL where more information on this model may be obtained.
     * 
     * @throws MalformedURLException
     *             , if returned URL is not a valid URL.
     * @returns the URL to the AttenuationRelationship document on the Web.
     * 
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
        } else if (pName.equals(DistanceHypoParameter.NAME)) {
            rHypo = ((Double) val).doubleValue();
        } else if (pName.equals(MagParam.NAME)) {
            mag = ((Double) val).doubleValue();
        } else if (pName.equals(StdDevTypeParam.NAME)) {
            stdDevType = (String) val;
        }
    }

    /**
     * Resets the change listeners on the parameters.
     * 
     */
    public void resetParameterEventListeners() {
        distanceRupParam.removeParameterChangeListener(this);
        distanceHypoParam.removeParameterChangeListener(this);
        magParam.removeParameterChangeListener(this);
        stdDevTypeParam.removeParameterChangeListener(this);
        this.initParameterEventListeners();
    }

    /**
     * Calculates mean MMI for finite rupture.
     * 
     * @param Mw
     *            , moment magnitude
     * @param Rrup
     *            , closest distance to rupture (km)
     * @return double
     * 
     */
    public double getMeanForFiniteRup(double Mw, double Rrup) {
        double mmi = 0;
        mmi =
                c0FiniteRup
                        + c1FiniteRup
                        * Mw
                        + c2FiniteRup
                        * Math.log(Math.sqrt((Math.pow(Rrup, 2))
                                + Math.pow(
                                        (1 + (c3FiniteRup * Math.exp(Mw - 5))),
                                        2)));
        return mmi;
    }

    /**
     * Calculates mean MMI for point rupture. Function is different for
     * hypocentral distance <= 20 kms and > 20 kms.
     * 
     * @param Mw
     *            , moment magnitude
     * @param Rhypo
     *            , hypocentral distance (km)
     * @return double
     * 
     */
    public double getMeanForPointRup(double Mw, double Rhypo) {
        double mmi = 0;
        double rm = 0;
        rm = m1PointRup + m2PointRup * Math.exp(Mw - 5);
        if (Rhypo <= 20) {
            mmi =
                    c0PointRup
                            + c1PointRup
                            * Mw
                            + c2PointRup
                            * Math.log(Math.sqrt(Math.pow(Rhypo, 2)
                                    + Math.pow(rm, 2)));
        } else {
            mmi =
                    c0PointRup
                            + c1PointRup
                            * Mw
                            + c2PointRup
                            * Math.log(Math.sqrt(Math.pow(Rhypo, 2)
                                    + Math.pow(rm, 2))) + c4PointRup
                            * Math.log(Rhypo / 20);
        }
        return mmi;
    }

    /**
     * Calculates standard deviation for finite ruptures.
     * 
     * @param Rrup
     *            , closest distance to rupture (km)
     * @return double
     * 
     */
    public double getStdDevForFiniteRup(double Rrup) {
        double sigma1 =
                s1FiniteRup
                        + (s2FiniteRup / (1 + Math.pow((Rrup / s3FiniteRup), 2)));
        double sigma =
                Math.sqrt(Math.pow(sigma1, 2) + Math.pow(sigma2FiniteRup, 2));
        return sigma;
    }

    /**
     * Calculates standard deviation for point rupture.
     * 
     * @param Rhypo
     *            , hypocentral distance
     * @return double
     * 
     */
    public double getStdDevForPointRup(double Rhypo) {
        double sigma1 =
                s1PointRup
                        + (s2PointRup / (1 + Math.pow((Rhypo / s3PointRup), 2)));
        double sigma =
                Math.sqrt(Math.pow(sigma1, 2) + Math.pow(sigma2PointRup, 2));
        return sigma;
    }

}