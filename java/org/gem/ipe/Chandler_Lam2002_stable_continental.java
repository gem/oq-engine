package org.gem.ipe;

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
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.MMI_Param;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceEpicentralParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

/**
 * <b>Title:</b> BW_1997_AttenRel
 * <p>
 * 
 * <b>Description:</b> This implements the Attenuation Relationship published by
 * 
 * 
 * Verification tables have been provided by Damiano Monelli as an Excel
 * spreadsheet.
 * 
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
 * <LI>magParam - moment Magnitude
 * <LI>distanceEpiParam - epicentral distance
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL>
 * </p>
 * 
 * <p>
 * Verification - This model has been tested against: Verification table
 * implemented in the JUnit test Chandler_Lam2002_stable_continental_test.
 * 
 * </p>
 * 
 * 
 * @author Roland Siegert, Damiano Monelli
 * @created November, 2010
 * @version 0.1
 */
public class Chandler_Lam2002_stable_continental extends
        AttenuationRelationship implements
        ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI,
        ParameterChangeListener {
    private final double totalStandardDeviation = 0.7d;
    private static final Double DISTANCE_EPI_WARN_MIN = 0.0;
    private static final Double DISTANCE_EPI_WARN_MAX = 300.0;
    private static final Double MAG_WARN_MIN = 3.3;
    private static final Double MAG_WARN_MAX = 8.0;
    // epicentral distance - never read just defined to comply with the
    // "analogous" implemented classes ("parameterChange()"). -> refactor!
    double rEpi;
    // Rupture magnitude - never read just defined to comply with the
    // "analogous" implemented classes ("parameterChange()"). -> refactor!
    private double mag;
    // stdDevType - is only set by the ParameterChangeListener like in the
    // "analogous" implemented IPE classes ("parameterChange()"). -> refactor!
    private String stdDevType;
    // By now the calculator does not observe parameter changes.
    // So this is a UI listener that is only introduced for consistency.
    private ParameterChangeWarningListener warningListener = null;
    // also unused UI stuff
    private boolean parameterChange;

    public Chandler_Lam2002_stable_continental(ParameterChangeWarningListener wl) {
        super();
        this.warningListener = wl;
        initSupportedIntensityMeasureParams();
        initEqkRuptureParams();
        initPropagationEffectParams();
        initSiteParams();
        initOtherParams();
        initParameterEventListeners();
    } // constructor

    @Override
    protected void initSupportedIntensityMeasureParams() {
        mmiParam = new MMI_Param();
        mmiParam.setNonEditable();
        mmiParam.addParameterChangeWarningListener(warningListener);
        /*
         * "supportedIMParams" is defined and initialised in class
         * IntensityMeasureRelationship. -> It is save to use it here.
         * Suggestion for an OpenSha refactoring: TODO: Avoid uncontrolled
         * access by the subclasses. Set these members private in the super
         * class and provide access via setters and getters with lazy init.
         */
        getSupportedIntensityMeasuresList().clear();
        // supportedIMParams.clear();
        getSupportedIntensityMeasuresList().addParameter(mmiParam);
        // supportedIMParams.addParameter(mmiParam);
    }

    @Override
    protected void initEqkRuptureParams() {
        magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);
        /*
         * eqkRuptureParams is defined and initialised in class
         * IntensityMeasureRelationship. -> It is save to use it here.
         * Suggestion for an OpenSha refactoring: TODO: Avoid uncontrolled
         * access by the subclasses. Set these members private in the super
         * class and provide access via setters and getters with lazy init.
         */
        getEqkRuptureParamsList().clear();
        // eqkRuptureParams.clear();
        getEqkRuptureParamsList().addParameter(magParam);
        // eqkRuptureParams.addParameter(magParam);
    }

    @Override
    protected void initPropagationEffectParams() {
        distanceEpicentralParameter = new DistanceEpicentralParameter(0.0);
        distanceEpicentralParameter
                .addParameterChangeWarningListener(warningListener);
        DoubleConstraint warn =
                new DoubleConstraint(DISTANCE_EPI_WARN_MIN,
                        DISTANCE_EPI_WARN_MAX);
        warn.setNonEditable();
        distanceEpicentralParameter.setWarningConstraint(warn);
        distanceEpicentralParameter.setNonEditable();
        /*
         * "propagationEffectParams" is defined and initialised in class
         * IntensityMeasureRelationship. -> It is save to use it here.
         * Suggestion for an OpenSha refactoring: TODO: Avoid uncontrolled
         * access by the subclasses. Set these members private in the super
         * class and provide access via getters and setters and let the lazy
         * init!.
         */
        getPropagationEffectParamsList().addParameter(
                distanceEpicentralParameter);
    } // initPropagationEffectParams()

    @Override
    protected void initSiteParams() {
        getSiteParamsList().clear();
        // siteParams.clear();
    }

    @Override
    protected void initOtherParams() {
        super.initOtherParams();
        stdDevTypeParam = createStdDevTypeParam();
        otherParams.addParameter(stdDevTypeParam);
    }

    /**
     * Adds the parameter change listeners. This allows to listen to when-ever
     * the parameter is changed.
     * 
     */
    @Override
    protected void initParameterEventListeners() {
        distanceEpicentralParameter.addParameterChangeListener(this);
        magParam.addParameterChangeListener(this);
        stdDevTypeParam.addParameterChangeListener(this);
    }

    private StdDevTypeParam createStdDevTypeParam() {
        StringConstraint stdDevTypeConstraint = new StringConstraint();
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
        stdDevTypeConstraint.setNonEditable();
        /*
         * Note: Using the single argument constructor results in an error,
         * because the constructor sets a different default value:
         * StdDevTypeParam stdDev = new StdDevTypeParam(stdDevTypeConstraint);
         */
        return new StdDevTypeParam(stdDevTypeConstraint,
                StdDevTypeParam.STD_DEV_TYPE_TOTAL);
    }

    @Override
    protected void setPropagationEffectParams() {
        if ((this.site != null) && (this.eqkRupture != null)) {
            distanceEpicentralParameter.setValue(eqkRupture, site);
        }
    }

    @Override
    public double getMean() {
        double epicentralDistance =
                (Double) distanceEpicentralParameter.getValue();
        return getMean(magParam.getValue(), epicentralDistance);
    } // getMean()

    /**
     * Sets the eqkRupture related parameters (magParam) based on the passed
     * eqkRupture. The internally held eqkRupture object is set to the passed
     * parameter. Warning constraints are not ignored.
     * 
     * @param eqkRupture
     * 
     */
    @Override
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
    @Override
    public void setSite(Site site) throws ParameterException {
        this.site = site;
        setPropagationEffectParams();
    }

    @Override
    public String getShortName() {
        return null;
    }

    @Override
    public void setParamDefaults() {
        magParam.setValueAsDefault();
        distanceEpicentralParameter.setValueAsDefault();
        mmiParam.setValueAsDefault();
        /*
         * This call (getStdDevTypeParam()) initialises stdDevTypeParam. This
         * method (setParamDefaults()) is public. The init method for
         * stdDevTypeParam is called in the constructor though...
         */
        getStdDevTypeParam().setValueAsDefault();
    }

    /**
     * Method to be implemented by listeners of ParameterChangeEvents.
     */
    @Override
    public void parameterChange(ParameterChangeEvent event) {
        String pName = event.getParameterName();
        Object val = event.getNewValue();
        parameterChange = true;
        if (pName.equals(DistanceRupParameter.NAME)) {
            rEpi = ((Double) val).doubleValue();
        } else if (pName.equals(DistanceEpicentralParameter.NAME)) {
            rEpi = ((Double) val).doubleValue();
        } else if (pName.equals(MagParam.NAME)) {
            mag = ((Double) val).doubleValue();
        } else if (pName.equals(StdDevTypeParam.NAME)) {
            stdDevType = (String) val;
        }
    }

    /**
     * Name of equation: Chandler and Lam (2002) [stable continental region]<br>
     * <br>
     * Formula:<br>
     * dist < 45 km: I_mmi = -0.8919 + 1.4798*magnitude -
     * 0.0193*log((dist+dist_0)/dist_0) - 0.0354*dist<br>
     * <br>
     * 
     * 45 km < dist < 75 km:<br>
     * I_mmi = -0.8919 + 1.4798*magnitude - 0.0193*log((dist+dist_0)/dist_0) -
     * 0.0354*dist + 0.0193(dist-45)<br>
     * <br>
     * 
     * dist > 75 km: I_mmi = -0.8919 + 1.4798*magnitude -
     * 0.0193*log((dist+dist_0)/dist_0) - 0.0354*dist + 0.0193(dist-45) +
     * 0.0085(dist-75)<br>
     * <br>
     * 
     * magnitude_w:<br>
     * 3.3 <= magnitude_w <= 8 <br>
     * <br>
     * 
     * distance:<br>
     * dist is the epicentral distance:<br>
     * dist < 300 km <br>
     * dist_0 = (10^(0.74*magnitude-3.55))/2 <br>
     * <br>
     * 
     * standard deviation sigma ~0.7<br>
     * 
     * 
     * @param magnitude
     *            3.3 <= magnitude <= 8
     * @param epicentralDistance
     *            distance from the epicenter, less or equal to 300 km
     * @return mean MMI predicted by the equation
     *         ("Intensity mercalli_modified_intensity")
     */
    public double getMean(double magnitude, double epicentralDistance) {
        // these boundaries could be passed in as parameters. Though the formula
        // is so elaborate that this seems unnecessary.
        int epicentralDistanceBoundary1 = 45;
        int epicentralDistanceBoundary2 = 75;
        // coefficients for all distance ranges, also less than 45 km
        final double offset = -0.8919;
        final double coefficient1 = 1.4798;
        final double coefficient2 = 0.1311;
        final double coefficient3 = 0.0364;
        // coefficients for distance range between 45 and 75 km
        final double coefficient4DistanceFrom45To75 = 0.0193;
        // coefficients for distance range greater than 75 km
        final double coefficient5DistanceGreater75 = 0.0085;
        final double dist0 = Math.pow(10, (0.74 * magnitude - 3.55)) / 2;
        double result =
                offset + coefficient1 * magnitude - coefficient2
                        * Math.log((epicentralDistance + dist0) / dist0)
                        - coefficient3 * epicentralDistance;
        if (epicentralDistance >= epicentralDistanceBoundary1) {
            // + 0.0193(dist-45)
            result +=
                    coefficient4DistanceFrom45To75
                            * (epicentralDistance - epicentralDistanceBoundary1);
            if (epicentralDistance >= epicentralDistanceBoundary2) {
                // + 0.0085(dist-75)
                result +=
                        coefficient5DistanceGreater75
                                * (epicentralDistance - epicentralDistanceBoundary2);
            }
        }
        return result;
    } // getMean()

    /**
     * TODO: Refactor this: "stdDevType" is set by parameterChange(). But if
     * this method is called before a ParameterChangeEvent was ever fired, this
     * will cause an Exception.
     * 
     * @return The standard deviation value
     */
    @Override
    public double getStdDev() {
        double stdDev = Double.NaN;
        if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) {
            stdDev = 0.0;
        } else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL)) {
            stdDev = totalStandardDeviation;
        }
        return stdDev;
    } // getStdDev()

    private StdDevTypeParam getStdDevTypeParam() {
        if (stdDevTypeParam == null) {
            stdDevTypeParam = createStdDevTypeParam();
        }
        return stdDevTypeParam;
    } // getStdDevTypeParam

} // class Chandler_Lam2002_stable_continental
