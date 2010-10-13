/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.sha.imr.attenRelImpl;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.IMRException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FaultUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

/**
 * <b>Title:</b> WC94_DisplMagRel
 * <p>
 * 
 * <b>Description:</b> This implements the Wells and Coppersmith average
 * displacement versus magnitude relationship in their table 2B (1994, Bulletin
 * of the Seismological Society of America, vol 84, pp 974-1002). This
 * relationship assumes the site is right on the fault where the event occurs
 * (i.e., the Site object is irrelevant and is ignored). This is a quick and
 * dirty implementation done for Lucy Jones' Alaskan Pipeline problem
 * <p>
 * 
 * Supported Intensity-Measure Parameters:
 * <p>
 * <UL>
 * <LI>faultDisplParam - Fault Displacement (average)
 * </UL>
 * <p>
 * Other Independent Parameters:
 * <p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>fltTypeParam - Style of faulting
 * <LI>distanceRupParam - closest distance to surface projection of fault
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL>
 * <p>
 * 
 * @author Edward H. Field
 * @created May, 2003
 * @version 1.0
 */

public class WC94_DisplMagRel extends AttenuationRelationship implements
        ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI {

    // debugging stuff:
    private final static String C = "WC94_DisplMagRel";
    private final static boolean D = false;
    public final static String NAME = "Wells & Coppersmith (1994)";
    public final static String SHORT_NAME = "WC_1994";
    private static final long serialVersionUID = 1234567890987654371L;

    /**
     * maximum rupture distance (rupture distances greater than this will always
     * return ln(mean_slip) that is negative infinity (slip that is zero)
     */
    private final static double MAX_DIST = 1.0;

    // supported IMT is fault displacement
    /**
     * fault displacement Intensity-Measure parameter (actually natural log
     * thereof)
     */
    protected WarningDoubleParameter faultDisplParam = null;
    public final static String FAULT_DISPL_NAME = "Fault Displacement";
    public final static String FAULT_DISPL_UNITS = "m";
    protected final static Double FAULT_DISPL_DEFAULT = new Double(
            Math.log(1.0));
    public final static String FAULT_DISPL_INFO = "Average Fault Displacement";
    protected final static Double FAULT_DISPL_MIN = new Double(
            Math.log(Double.MIN_VALUE));
    protected final static Double FAULT_DISPL_MAX =
            new Double(Double.MAX_VALUE);
    protected final static Double FAULT_DISPL_WARN_MIN = new Double(
            Math.log(Double.MIN_VALUE));
    protected final static Double FAULT_DISPL_WARN_MAX = new Double(
            Math.log(50.0));

    // style of faulting options
    public final static String FLT_TYPE_SS = "Strike Slip";
    public final static String FLT_TYPE_ALL = "Any Type";

    // warning constraint fields:
    protected final static Double MAG_WARN_MIN = new Double(5.0);
    protected final static Double MAG_WARN_MAX = new Double(9.0);
    protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
    protected final static Double DISTANCE_RUP_WARN_MAX = new Double(200.0);

    // for issuing warnings:
    private transient ParameterChangeWarningListener warningListener = null;

    /**
     * Determines the style of faulting from the rake angle (which comes from
     * the eqkRupture object) and fills in the value of the fltTypeParam.
     * 
     * @param rake
     *            in degrees
     * @throws InvalidRangeException
     *             If not valid rake angle
     */
    protected void setFaultTypeFromRake(double rake)
            throws InvalidRangeException {
        FaultUtils.assertValidRake(rake);
        if (rake >= 45 && rake <= 135) {
            fltTypeParam.setValue(FLT_TYPE_ALL);
        } else if (rake <= -45 && rake >= -135) {
            fltTypeParam.setValue(FLT_TYPE_ALL);
        } else {
            fltTypeParam.setValue(FLT_TYPE_SS);
        }
    }

    /**
     * this does nothing
     */
    protected void initCoefficients() {

    }

    /**
     * This sets the eqkRupture related parameters (magParam and fltTypeParam)
     * based on the eqkRupture passed in. The internally held eqkRupture object
     * is also set as that passed in. Warning constrains are ingored.
     * 
     * @param eqkRupture
     *            The new eqkRupture value
     * @throws InvalidRangeException
     *             If not valid rake angle
     */
    public void setEqkRupture(EqkRupture eqkRupture)
            throws InvalidRangeException {

        magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
        setFaultTypeFromRake(eqkRupture.getAveRake());
        this.eqkRupture = eqkRupture;
        setPropagationEffectParams();

    }

    /**
     * This sets the site object.
     * 
     * @param site
     */
    public void setSite(Site site) {

        this.site = site;
        setPropagationEffectParams();

    }

    /**
     * This calculates the DistanceRup propagation effect parameter based on the
     * current site and eqkRupture.
     * <P>
     */
    protected void setPropagationEffectParams() {

        if ((this.site != null) && (this.eqkRupture != null)) {
            distanceRupParam.setValue(eqkRupture, site);
        }

    }

    /**
     * This does nothing
     */
    protected void updateCoefficients() throws ParameterException {

    }

    /**
     * No-Arg constructor. This initializes several ParameterList objects.
     */
    public WC94_DisplMagRel(ParameterChangeWarningListener warningListener) {

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
     * No-Arg constructor. This initializes several ParameterList objects.
     */
    public WC94_DisplMagRel() {

        super();

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
     * 
     * @return String
     */
    public String getShortName() {
        return SHORT_NAME;
    }

    /**
     * Calculates the mean of the exceedence probability distribution.
     * <p>
     * 
     * @return The mean value
     */
    public double getMean() throws IMRException {

        double mag, dist;
        String fltTypeValue;

        try {
            mag = ((Double) magParam.getValue()).doubleValue();
            dist = ((Double) distanceRupParam.getValue()).doubleValue();
            fltTypeValue = fltTypeParam.getValue().toString();
        } catch (NullPointerException e) {
            throw new IMRException(C + ": getMean(): " + ERR);
        }

        // check if distance is beyond the user specified max
        if (dist > USER_MAX_DISTANCE) {
            return VERY_SMALL_MEAN;
        }

        double mean;

        if (dist < MAX_DIST) {
            if (fltTypeValue.equals(FLT_TYPE_SS)) {
                mean = 0.9 * mag - 6.32;
            } else {
                mean = 0.69 * mag - 4.8;
            }
        } else {
            return FAULT_DISPL_MIN.doubleValue();
        }

        // convert log10 to natural log
        mean *= 2.3026;

        // return the result
        return (mean);
    }

    /**
     * @return The stdDev value
     */
    public double getStdDev() throws IMRException {
        String fltTypeValue;
        String stdDevType = stdDevTypeParam.getValue().toString();

        try {
            fltTypeValue = fltTypeParam.getValue().toString();
        } catch (NullPointerException e) {
            throw new IMRException(C + ": getStdDev(): " + ERR);
        }

        if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) {
            return 0.0;
        } else {
            // first term below is stddev from WC94, second term converts this
            // from log10 to ln,
            // and the last term is an attemp to account for the intra-event
            // variability
            if (fltTypeValue.equals(FLT_TYPE_SS)) {
                return 0.28 * 2.3026 * 2.0; // last term to convert from log10
                                            // to ln
            } else {
                return 0.36 * 2.3026 * 2.0;
            }
        }

    }

    public void setParamDefaults() {

        magParam.setValueAsDefault();
        fltTypeParam.setValue(FLT_TYPE_SS);
        distanceRupParam.setValueAsDefault();
        faultDisplParam.setValue(FAULT_DISPL_DEFAULT);
        stdDevTypeParam.setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
    }

    /**
     * This creates the lists of independent parameters that the various
     * dependent parameters (mean, standard deviation, exceedance probability,
     * and IML at exceedance probability) depend upon. NOTE: these lists do not
     * include anything about the intensity-measure parameters or any of thier
     * internal independentParamaters.
     */
    protected void initIndependentParamLists() {

        // params that the mean depends upon
        meanIndependentParams.clear();
        meanIndependentParams.addParameter(magParam);
        meanIndependentParams.addParameter(fltTypeParam);
        meanIndependentParams.addParameter(distanceRupParam);

        // params that the stdDev depends upon
        stdDevIndependentParams.clear();
        stdDevIndependentParams.addParameter(fltTypeParam);
        stdDevIndependentParams.addParameter(stdDevTypeParam);

        // params that the exceed. prob. depends upon
        exceedProbIndependentParams.clear();
        exceedProbIndependentParams.addParameter(magParam);
        exceedProbIndependentParams.addParameter(fltTypeParam);
        exceedProbIndependentParams.addParameter(distanceRupParam);
        exceedProbIndependentParams.addParameter(stdDevTypeParam);
        exceedProbIndependentParams.addParameter(this.sigmaTruncTypeParam);
        exceedProbIndependentParams.addParameter(this.sigmaTruncLevelParam);

        // params that the IML at exceed. prob. depends upon
        imlAtExceedProbIndependentParams
                .addParameterList(exceedProbIndependentParams);
        imlAtExceedProbIndependentParams.addParameter(exceedProbParam);

    }

    /**
     * does nothing.
     */
    protected void initSiteParams() {

    }

    /**
     * Creates the two Potential Earthquake parameters (magParam and
     * fltTypeParam) and adds them to the eqkRuptureParams list. Makes the
     * parameters noneditable.
     */
    protected void initEqkRuptureParams() {

        magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);

        StringConstraint constraint = new StringConstraint();
        constraint.addString(FLT_TYPE_SS);
        constraint.addString(FLT_TYPE_ALL);
        constraint.setNonEditable();
        fltTypeParam = new FaultTypeParam(constraint, FLT_TYPE_SS);

        eqkRuptureParams.clear();
        eqkRuptureParams.addParameter(magParam);
        eqkRuptureParams.addParameter(fltTypeParam);

    }

    /**
   *
   */
    protected void initPropagationEffectParams() {
        distanceRupParam = new DistanceRupParameter(0.0);
        distanceRupParam.addParameterChangeWarningListener(warningListener);
        DoubleConstraint warn =
                new DoubleConstraint(DISTANCE_RUP_WARN_MIN,
                        DISTANCE_RUP_WARN_MAX);
        warn.setNonEditable();
        distanceRupParam.setWarningConstraint(warn);
        distanceRupParam.setNonEditable();

        propagationEffectParams.addParameter(distanceRupParam);

    }

    /**
     * Creates the one supported IM parameter.
     */
    protected void initSupportedIntensityMeasureParams() {

        // Create FAULT_DISPL Parameter
        DoubleConstraint fDisplConstraint =
                new DoubleConstraint(FAULT_DISPL_MIN, FAULT_DISPL_MAX);
        fDisplConstraint.setNonEditable();
        faultDisplParam =
                new WarningDoubleParameter(FAULT_DISPL_NAME, fDisplConstraint,
                        FAULT_DISPL_UNITS);
        faultDisplParam.setInfo(FAULT_DISPL_INFO);
        DoubleConstraint warn2 =
                new DoubleConstraint(FAULT_DISPL_WARN_MIN, FAULT_DISPL_WARN_MAX);
        warn2.setNonEditable();
        faultDisplParam.setWarningConstraint(warn2);
        faultDisplParam.setNonEditable();

        // Add the warning listeners:
        faultDisplParam.addParameterChangeWarningListener(warningListener);

        // Put parameters in the supportedIMParams list:
        supportedIMParams.clear();
        supportedIMParams.addParameter(faultDisplParam);
    }

    /**
     * Creates other Parameters that the mean or stdDev depends upon, such as
     * the Component or StdDevType parameters.
     */
    protected void initOtherParams() {

        // init other params defined in parent class
        super.initOtherParams();

        // the stdDevType Parameter
        StringConstraint stdDevTypeConstraint = new StringConstraint();
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
        stdDevTypeConstraint.setNonEditable();
        stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);

        otherParams.addParameter(stdDevTypeParam);

    }

    public static void main(String[] args) {
        WC94_DisplMagRel testRel = new WC94_DisplMagRel();
        testRel.setIntensityMeasure("Fault Displacement");

        Site site = new Site(new Location(30.01, 30.0), "test");
        testRel.setSite(site);

        EqkRupture rup = new EqkRupture();
        rup.setPointSurface(new Location(30.0, 30.0), 90.0);
        rup.setAveRake(0.0);

        rup.setMag(5);
        testRel.setEqkRupture(rup);
        System.out.println("Mag 5: " + testRel.getMean() + "; "
                + testRel.getStdDev());

        rup.setMag(6);
        testRel.setEqkRupture(rup);
        System.out.println("Mag 6: " + testRel.getMean() + "; "
                + testRel.getStdDev());

        rup.setMag(7);
        testRel.setEqkRupture(rup);
        System.out.println("Mag 7: " + testRel.getMean() + "; "
                + testRel.getStdDev());

        rup.setMag(8);
        testRel.setEqkRupture(rup);
        System.out.println("Mag 8: " + testRel.getMean() + "; "
                + testRel.getStdDev());

        rup.setMag(9);
        testRel.setEqkRupture(rup);
        System.out.println("Mag 9: " + testRel.getMean() + "; "
                + testRel.getStdDev());

        rup.setAveRake(90);

        rup.setMag(5);
        testRel.setEqkRupture(rup);
        System.out.println("Mag 5: " + testRel.getMean() + "; "
                + testRel.getStdDev());

        rup.setMag(6);
        testRel.setEqkRupture(rup);
        System.out.println("Mag 6: " + testRel.getMean() + "; "
                + testRel.getStdDev());

        rup.setMag(7);
        testRel.setEqkRupture(rup);
        System.out.println("Mag 7: " + testRel.getMean() + "; "
                + testRel.getStdDev());

        rup.setMag(8);
        testRel.setEqkRupture(rup);
        System.out.println("Mag 8: " + testRel.getMean() + "; "
                + testRel.getStdDev());

        rup.setMag(9);
        testRel.setEqkRupture(rup);
        System.out.println("Mag 9: " + testRel.getMean() + "; "
                + testRel.getStdDev());
    }

}
