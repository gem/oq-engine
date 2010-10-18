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
import org.opensha.commons.param.StringParameter;
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
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

/**
 * <b>Title:</b> McVerryetal_2000_AttenRel
 * <p>
 * 
 * <b>Description:</b> This implements the Attenuation Relationship published by
 * McVerry et al (2000,
 * "Crustal and subduction zone attenuation relations for New Zealand Earthquakes"
 * , Proc 12th World conference on earthquake engineering </b> A more complete
 * description of the attenuation relation can be found at McVerry et al (2006,
 * "New Zealand Acceleration Response Spectrum Attenuation Relations for Crustal
 * and Subduction Zone Earthquakes", <it> Bulletin of the New Zealand Society of
 * Earthquake Engineering <it> Vol 39. No. 4 pp1-58)
 * 
 * 
 * Supported Intensity-Measure Parameters:
 * <p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration
 * </UL>
 * <p>
 * Other Independent Parameters:
 * <p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceRupParam - closest distance to fault surface
 * <LI>siteTypeParam - "A-Strong Rock", "B-Rock", "C-Shallow Soil",
 * "D-Deep or soft soil"
 * <LI>fltTypeParam - Style of faulting
 * <LI>componentTypeParam - Component of shaking (either geometric mean (not yet
 * implemented) or largest horizontal )
 * <LI>stdDevTypeParam - The type of standard deviation
 * <LI>Also have not yet implemented source type - crustal or subduction -
 * waiting on Ned (2 Jul 09)
 * </UL>
 * </p>
 * 
 * <p>
 * 
 * Verification - Compared with a Matlab implementation 2 July 2009
 * 
 * </p>
 * 
 * 
 * @author Brendon A. Bradley
 * @created June, 2009
 * @version 1.0
 */

public class McVerryetal_2000_AttenRel extends AttenuationRelationship
        implements ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI,
        ParameterChangeListener {

    // Debugging stuff
    private final static String C = "McVerryetal_2000_AttenRel";
    private final static boolean D = false;
    public final static String SHORT_NAME = "McVerryetal2000";
    private static final long serialVersionUID = 1234567890987654353L;

    // Name of IMR
    public final static String NAME = "McVerry et al (2000)";

    // URL Info String
    private final static String URL_INFO_STRING =
            "http://www.opensha.org/documentation/modelsImplemented/attenRel/McVerryetal_2000.html";

    // Note unlike the NGA equations period=-1 here gives the 'primed'
    // coefficients
    double[] period = { -1.0, 0.0, 0.075, 0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0,
            1.5, 2.0, 3.0 };
    // coefficients: these are for the larger horizontal component (i.e. _lh
    // subscript)
    double[] C1_lh =
            { 0.28815, 0.1813, 1.36561, 1.77717, 1.39535, 0.44591, 0.01645,
                    0.14826, -0.21246, -0.10451, -0.48665, -0.77433, -1.30916 };
    double[] C3AS_lh = { 0.0, 0.0, 0.03, 0.028, -0.0138, -0.036, -0.0518,
            -0.0635, -0.0862, -0.102, -0.12, -0.12, -0.1726 };
    double C4AS_lh = -0.144;
    double[] C5_lh = { -0.00967, -0.00846, -0.00889, -0.00837, -0.0094,
            -0.00987, -0.00923, -0.00823, -0.00738, -0.00588, -0.0063, -0.0063,
            -0.00553 };
    double C6AS_lh = 0.17;
    double[] C8_lh = { -0.70494, -0.75519, -0.94568, -1.01852, -0.78199,
            -0.56098, -0.51281, -0.56716, -0.55384, -0.65892, -0.58222,
            -0.58222, -0.57009 };
    double[] C10AS_lh = { 5.6, 5.6, 5.58, 5.5, 5.1, 4.8, 4.52, 4.3, 3.9, 3.7,
            3.55, 3.55, 3.5 };
    double[] C11_lh = { 8.68354, 8.10697, 8.68782, 9.37929, 10.61479, 9.40776,
            8.50343, 8.46463, 7.30176, 7.08727, 6.93264, 6.64496, 5.05488 };
    double C12y_lh = 1.414;
    double[] C13y_lh = { 0.0, 0.0, 0.0, -0.0011, -0.0027, -0.0036, -0.0043,
            -0.0048, -0.0057, -0.0064, -0.0073, -0.0073, -0.0089 };
    double[] C15_lh = { -2.552, -2.552, -2.707, -2.655, -2.528, -2.454, -2.401,
            -2.36, -2.286, -2.234, -2.16, -2.16, -2.033 };
    double[] C17_lh = { -2.56727, -2.48795, -2.54215, -2.60945, -2.70851,
            -2.47668, -2.36895, -2.4063, -2.26512, -2.27668, -2.28347,
            -2.28347, -2.0305 };
    double C18y_lh = 1.7818;
    double C19y_lh = 0.554;
    double[] C20_lh = { 0.0155, 0.01622, 0.0185, 0.0174, 0.01542, 0.01278,
            0.01426, 0.01287, 0.0108, 0.00946, 0.00788, 0.00788, -0.00265 };
    double[] C24_lh = { -0.50962, -0.41369, -0.48652, -0.61973, -0.67672,
            -0.59339, -0.30579, -0.24839, -0.01298, 0.06672, -0.02289,
            -0.02289, -0.20537 };
    double[] C29_lh = { 0.30206, 0.44307, 0.31139, 0.34059, 0.37235, 0.56648,
            0.69911, 0.63188, 0.51577, 0.34048, 0.12468, 0.12468, 0.14593 };
    double[] C30AS_lh = { -0.23, -0.23, -0.28, -0.28, -0.245, -0.195, -0.16,
            -0.121, -0.05, 0.0, 0.04, 0.04, 0.04 };
    double C32_lh = -0.2;
    double[] C33AS_lh = { 0.26, 0.26, 0.26, 0.26, 0.26, 0.198, 0.154, 0.119,
            0.057, 0.013, -0.049, -0.049, -0.156 };
    double[] C43_lh = { -0.31769, -0.29648, -0.29648, -0.43854, -0.29906,
            -0.05184, 0.20301, 0.37026, 0.73517, 0.87764, 0.75438, 0.75438,
            0.61545 };
    double[] C46_lh = { -0.03279, -0.03301, -0.03452, -0.03595, -0.03853,
            -0.03604, -0.03364, -0.0326, -0.02877, -0.02561, -0.02034,
            -0.02034, -0.01673 };
    double[] sigma6_lh = { 0.0, 0.4865, 0.5281, 0.5398, 0.5703, 0.5505, 0.5627,
            0.568, 0.5562, 0.5629, 0.5394, 0.5394, 0.5701 };
    double[] sigSlope_lh = { 0.0, -0.1261, -0.097, -0.0673, -0.0243, -0.0861,
            -0.1405, -0.1444, -0.0932, -0.0749, -0.0056, -0.0056, 0.0934 };
    double[] tau_lh = { 0.0, 0.2687, 0.3217, 0.3088, 0.2726, 0.2112, 0.2005,
            0.1476, 0.1794, 0.2053, 0.2411, 0.2411, 0.2406 };
    // coefficients: these are for the (unrotated) geometric mean component
    // (i.e. _gm subscript)
    double[] C1_gm = { 0.14274, 0.07713, 1.22050, 1.53365, 1.22565, 0.21124,
            -0.10541, -0.14260, -0.65968, -0.51404, -0.95399, -1.24167,
            -1.56570 };
    double[] C3AS_gm = { 0.0, 0.0, 0.03, 0.028, -0.0138, -0.036, -0.0518,
            -0.0635, -0.0862, -0.102, -0.12, -0.12, -0.17260 };
    double C4AS_gm = -0.144;
    double[] C5_gm = { -0.00989, -0.00898, -0.00914, -0.00903, -0.00975,
            -0.01032, -0.00941, -0.00878, -0.00802, -0.00647, -0.00713,
            -0.00713, -0.00623 };
    double C6AS_gm = 0.17;
    double[] C8_gm = { -0.68744, -0.73728, -0.93059, -0.96506, -0.75855,
            -0.52400, -0.50802, -0.52214, -0.47264, -0.58672, -0.49268,
            -0.49268, -0.52257 };
    double[] C10AS_gm = { 5.6, 5.6, 5.58, 5.5, 5.1, 4.8, 4.52, 4.3, 3.9, 3.7,
            3.55, 3.55, 3.5 };
    double[] C11_gm = { 8.57343, 8.08611, 8.69303, 9.30400, 10.41628, 9.21783,
            8.0115, 7.87495, 7.26785, 6.98741, 6.77543, 6.48775, 5.05424 };
    double C12y_gm = 1.414;
    double[] C13y_gm = { 0.0, 0.0, 0.0, -0.0011, -0.0027, -0.0036, -0.0043,
            -0.0048, -0.0057, -0.0064, -0.0073, -0.0073, -0.0089 };
    double[] C15_gm = { -2.552, -2.552, -2.707, -2.655, -2.528, -2.454, -2.401,
            -2.36, -2.286, -2.234, -2.16, -2.16, -2.033 };
    double[] C17_gm = { -2.56592, -2.49894, -2.55903, -2.61372, -2.70038,
            -2.47356, -2.30457, -2.31991, -2.28460, -2.28256, -2.27895,
            -2.27895, -2.05560 };
    double C18y_gm = 1.7818;
    double C19y_gm = 0.554;
    double[] C20_gm = { 0.01545, 0.0159, 0.01821, 0.01737, 0.01531, 0.01304,
            0.01426, 0.01277, 0.01055, 0.00927, 0.00748, 0.00748, -0.00273 };
    double[] C24_gm = { -0.49963, -0.43223, -0.52504, -0.61452, -0.65966,
            -0.56604, -0.33169, -0.24374, -0.01583, 0.02009, -0.07051,
            -0.07051, -0.23967 };
    double[] C29_gm = { 0.27315, 0.38730, 0.27879, 0.28619, 0.34064, 0.53213,
            0.63272, 0.58809, 0.50708, 0.33002, 0.07445, 0.07445, 0.09869 };
    double[] C30AS_gm = { -0.23, -0.23, -0.28, -0.28, -0.245, -0.195, -0.16,
            -0.121, -0.05, 0.0, 0.04, 0.04, 0.04 };
    double C32_gm = -0.2;
    double[] C33AS_gm = { 0.26, 0.26, 0.26, 0.26, 0.26, 0.198, 0.154, 0.119,
            0.057, 0.013, -0.049, -0.049, -0.156 };
    double[] C43_gm = { -0.33716, -0.31036, -0.49068, -0.46604, -0.31282,
            -0.07565, 0.17615, 0.34775, 0.72380, 0.89239, 0.77743, 0.77743,
            0.60938 };
    double[] C46_gm = { -0.03255, -0.0325, -0.03441, -0.03594, -0.03823,
            -0.03535, -0.03354, -0.03211, -0.02857, -0.025, -0.02008, -0.02008,
            -0.01587 };
    double[] sigma6_gm = { 0.4871, 0.5099, 0.5297, 0.5401, 0.5599, 0.5456,
            0.5556, 0.5658, 0.5611, 0.5573, 0.5419, 0.5419, 0.5809 };
    double[] sigSlope_gm =
            { -0.1011, -0.0259, -0.0703, -0.0292, 0.0172, -0.0566, -0.1064,
                    -0.1123, -0.0836, -0.0620, 0.0385, 0.0385, 0.1403 };
    double[] tau_gm = { 0.2677, 0.2469, 0.3139, 0.3017, 0.2583, 0.1967, 0.1802,
            0.1440, 0.1871, 0.2073, 0.2405, 0.2405, 0.2053 };

    private HashMap indexFromPerHashMap;

    private int iper;
    private double rRup, mag;
    private String stdDevType, fltType, component;
    private boolean parameterChange;

    private PropagationEffect propagationEffect;

    protected final static Double MAG_WARN_MIN = new Double(5.0);
    protected final static Double MAG_WARN_MAX = new Double(8.5);
    protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
    protected final static Double DISTANCE_RUP_WARN_MAX = new Double(400.0);

    /**
     * Site Type Parameter ("Rock/Shallow-Soil" versus "Deep-Soil")
     */
    private StringParameter siteTypeParam = null;
    public final static String SITE_TYPE_NAME = "McVerryetal Site Type";
    // no units
    public final static String SITE_TYPE_INFO =
            "Geological conditions at the site";
    public final static String SITE_TYPE_A = "A-Strong-Rock";
    public final static String SITE_TYPE_B = "B-Rock";
    public final static String SITE_TYPE_C = "C-Shallow-Soil";
    public final static String SITE_TYPE_D = "D-Soft-or-Deep-Soil";
    public final static String SITE_TYPE_DEFAULT = SITE_TYPE_A;

    // style of faulting options
    public final static String FLT_TYPE_STRIKE_SLIP = "Strike-Slip";
    public final static String FLT_TYPE_REVERSE = "Reverse";
    public final static String FLT_TYPE_REVERSE_OBLIQUE = "Oblique-Reverse";
    public final static String FLT_TYPE_NORMAL = "Normal";
    public final static String FLT_TYPE_INTERFACE = "Subduction-Interface";
    public final static String FLT_TYPE_DEEP_SLAB = "Subduction-Deep-Slab";

    // change component default from that of parent
    public final static String COMPONENT_GEOMEAN =
            ComponentParam.COMPONENT_AVE_HORZ;
    public final static String COMPONENT_LARGERHORIZ =
            ComponentParam.COMPONENT_GREATER_OF_TWO_HORZ;

    // for issuing warnings:
    private transient ParameterChangeWarningListener warningListener = null;

    /**
     * This initializes several ParameterList objects.
     */
    public McVerryetal_2000_AttenRel(
            ParameterChangeWarningListener warningListener) {

        super();

        this.warningListener = warningListener;

        initSupportedIntensityMeasureParams();
        indexFromPerHashMap = new HashMap();
        for (int i = 1; i < period.length; i++) {
            indexFromPerHashMap.put(new Double(period[i]), new Integer(i));
        }

        initEqkRuptureParams();
        initPropagationEffectParams();
        initSiteParams();
        initOtherParams();

        initIndependentParamLists(); // This must be called after the above
        initParameterEventListeners(); // add the change listeners to the
                                       // parameters

        propagationEffect = new PropagationEffect();
    }

    /**
     * This sets the eqkRupture related parameters (magParam and fltTypeParam)
     * based on the eqkRupture passed in. The internally held eqkRupture object
     * is also set as that passed in. Warning constrains are ingored.
     * 
     * @param eqkRupture
     *            The new eqkRupture value
     * @throws InvalidRangeException
     *             thrown if rake is out of bounds
     */
    public void setEqkRupture(EqkRupture eqkRupture)
            throws InvalidRangeException {

        magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
        setFaultTypeFromRake(eqkRupture.getAveRake());
        this.eqkRupture = eqkRupture;
        setPropagationEffectParams();

    }

    /**
     * This sets the site-related parameter (siteTypeParam) based on what is in
     * the Site object passed in (the Site object must have a parameter with the
     * same name as that in siteTypeParam). This also sets the internally held
     * Site object as that passed in.
     * 
     * @param site
     *            The new site object
     */
    public void setSite(Site site) throws ParameterException {

        siteTypeParam.setValue((String) site.getParameter(SITE_TYPE_NAME)
                .getValue());
        this.site = site;
        setPropagationEffectParams();

    }

    /**
     * This sets the propagation-effect parameter (distanceRupParam) based on
     * the current site and eqkRupture.
     */
    protected void setPropagationEffectParams() {

        if ((this.site != null) && (this.eqkRupture != null)) {

            propagationEffect.setAll(this.eqkRupture, this.site); // use this
                                                                  // for
                                                                  // efficiency
            distanceRupParam.setValueIgnoreWarning(propagationEffect
                    .getParamValue(distanceRupParam.NAME)); // this sets rRup
                                                            // too
        }
    }

    /**
     * This function returns the array index for the coeffs corresponding to the
     * chosen IMT
     */
    protected void setCoeffIndex() throws ParameterException {

        // Check that parameter exists
        if (im == null) {
            throw new ParameterException(
                    C
                            + ": updateCoefficients(): "
                            + "The Intensity Measusre Parameter has not been set yet, unable to process.");
        }
        if (im.getName().equalsIgnoreCase(PGA_Param.NAME)) {
            iper = 1;
        } else {
            iper =
                    ((Integer) indexFromPerHashMap
                            .get(saPeriodParam.getValue())).intValue();
        }

        parameterChange = true;
        intensityMeasureChanged = false;

    }

    /**
     * Calculates the mean of the exceedence probability distribution.
     * <p>
     * 
     * @return The mean value
     */
    public double getMean() {

        // check if distance is beyond the user specified max
        if (rRup > USER_MAX_DISTANCE) {
            return VERY_SMALL_MEAN;
        }

        if (intensityMeasureChanged) {
            setCoeffIndex(); // intensityMeasureChanged is set to false in this
                             // method
        }

        double pga =
                Math.exp(getMean(0, siteTypeParam, rRup, mag, fltType,
                        component));
        double pga_prime =
                Math.exp(getMean(1, siteTypeParam, rRup, mag, fltType,
                        component));
        double sa_prime =
                Math.exp(getMean(iper, siteTypeParam, rRup, mag, fltType,
                        component));
        return Math.log(sa_prime * pga / pga_prime);
    }

    /**
     * @return The stdDev value
     */
    public double getStdDev() {
        if (intensityMeasureChanged) {
            setCoeffIndex();// intensityMeasureChanged is set to false in this
                            // method
        }
        return getStdDev(iper, stdDevType, component);
    }

    /**
     * Determines the style of faulting from the rake angle. Their report is not
     * explicit, so these ranges come from an email that told us to decide, but
     * that within 30-degrees of horz for SS was how the NGA data were defined.
     * 
     * @param rake
     *            in degrees
     * @throws InvalidRangeException
     *             If not valid rake angle
     */
    protected void setFaultTypeFromRake(double rake)
            throws InvalidRangeException {
        if (rake <= 33 && rake >= -33)
            fltTypeParam.setValue(FLT_TYPE_STRIKE_SLIP);
        else if (rake <= -147 || rake >= 147)
            fltTypeParam.setValue(FLT_TYPE_STRIKE_SLIP);
        else if (rake > 33 && rake < 66)
            fltTypeParam.setValue(FLT_TYPE_REVERSE_OBLIQUE);
        else if (rake > 123 && rake < 147)
            fltTypeParam.setValue(FLT_TYPE_REVERSE_OBLIQUE);
        else if (rake > 66 && rake < 123)
            fltTypeParam.setValue(FLT_TYPE_REVERSE);
        else if (rake > -147 && rake < -33)
            fltTypeParam.setValue(FLT_TYPE_NORMAL);
        // NEED ADDITIONAL LINES HERE FOR THE SUBDUCTION SOURCE TYPES
    }

    /**
     * Allows the user to set the default parameter values for the selected
     * Attenuation Relationship.
     */
    public void setParamDefaults() {

        siteTypeParam.setValue(SITE_TYPE_DEFAULT);
        magParam.setValueAsDefault();
        distanceRupParam.setValueAsDefault();
        fltTypeParam.setValueAsDefault();
        saParam.setValueAsDefault();
        saPeriodParam.setValueAsDefault();
        saDampingParam.setValueAsDefault();
        pgaParam.setValueAsDefault();
        stdDevTypeParam.setValueAsDefault();
        componentParam.setValueAsDefault();

        mag = ((Double) magParam.getValue()).doubleValue();
        fltType = (String) fltTypeParam.getValue();
        stdDevType = (String) stdDevTypeParam.getValue();
        component = (String) componentParam.getValue();
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
        meanIndependentParams.addParameter(distanceRupParam);
        meanIndependentParams.addParameter(siteTypeParam);
        meanIndependentParams.addParameter(magParam);
        meanIndependentParams.addParameter(fltTypeParam);
        meanIndependentParams.addParameter(componentParam);

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

    protected void initSiteParams() {

        StringConstraint siteConstraint = new StringConstraint();
        siteConstraint.addString(SITE_TYPE_A);
        siteConstraint.addString(SITE_TYPE_B);
        siteConstraint.addString(SITE_TYPE_C);
        siteConstraint.addString(SITE_TYPE_D);
        siteConstraint.setNonEditable();
        siteTypeParam =
                new StringParameter(SITE_TYPE_NAME, siteConstraint, null);
        siteTypeParam.setInfo(SITE_TYPE_INFO);
        siteTypeParam.setNonEditable();

        siteParams.clear();
        siteParams.addParameter(siteTypeParam);
    }

    /**
     * Creates the two Potential Earthquake parameters (magParam and
     * fltTypeParam) and adds them to the eqkRuptureParams list. Makes the
     * parameters noneditable.
     */
    protected void initEqkRuptureParams() {

        magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);

        StringConstraint constraint = new StringConstraint();
        constraint.addString(FLT_TYPE_STRIKE_SLIP);
        constraint.addString(FLT_TYPE_REVERSE);
        constraint.addString(FLT_TYPE_REVERSE_OBLIQUE);
        constraint.addString(FLT_TYPE_NORMAL);
        constraint.addString(FLT_TYPE_INTERFACE);
        constraint.addString(FLT_TYPE_DEEP_SLAB);
        constraint.setNonEditable();
        fltTypeParam = new FaultTypeParam(constraint, FLT_TYPE_STRIKE_SLIP);

        eqkRuptureParams.clear();
        eqkRuptureParams.addParameter(magParam);
        eqkRuptureParams.addParameter(fltTypeParam);
    }

    /**
     * Creates the Propagation Effect parameters and adds them to the
     * propagationEffectParams list. Makes the parameters noneditable.
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
    }

    /**
     * Creates the two supported IM parameters (PGA and SA), as well as the
     * independenParameters of SA (periodParam and dampingParam) and adds them
     * to the supportedIMParams list. Makes the parameters noneditable.
     */
    protected void initSupportedIntensityMeasureParams() {

        // Create saParam:
        DoubleDiscreteConstraint periodConstraint =
                new DoubleDiscreteConstraint();
        for (int i = 2; i < period.length; i++) {
            periodConstraint.addDouble(new Double(period[i]));
        }
        periodConstraint.setNonEditable();
        saPeriodParam = new PeriodParam(periodConstraint);
        saDampingParam = new DampingParam();
        saParam = new SA_Param(saPeriodParam, saDampingParam);
        saParam.setNonEditable();

        // Create PGA Parameter (pgaParam):
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
     * Creates other Parameters that the mean or stdDev depends upon, such as
     * the Component or StdDevType parameters.
     */
    protected void initOtherParams() {

        // init other params defined in parent class
        super.initOtherParams();

        // the Component Parameter
        StringConstraint componentConstraint = new StringConstraint();
        componentConstraint.addString(ComponentParam.COMPONENT_AVE_HORZ);
        componentConstraint
                .addString(ComponentParam.COMPONENT_GREATER_OF_TWO_HORZ);
        componentConstraint.setNonEditable();
        componentParam =
                new ComponentParam(componentConstraint,
                        ComponentParam.COMPONENT_AVE_HORZ);

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
     * 
     * @return String
     */
    public String getShortName() {
        return SHORT_NAME;
    }

    public double getMean(int iper, StringParameter siteTypeParam, double rRup,
            double mag, String fltType, String component) {

        // initialise dummy variables
        double CN = 0.0, CR = 0.0, SI = 0.0, DS = 0.0, deltaC = 0.0, deltaD =
                0.0;
        String siteType = siteTypeParam.getValue().toString();
        double lnSA_AB, lnSA_CD;
        double rVol = 0.0, hc = 0.0; // need to change value of rVol and Hc in
                                     // future

        // allocate dummy fault variables
        if (fltType.equals(FLT_TYPE_NORMAL)) {
            CN = -1.0;
        } else if (fltType.equals(FLT_TYPE_REVERSE)) {
            CR = 1.0;
        } else if (fltType.equals(FLT_TYPE_REVERSE_OBLIQUE)) {
            CR = 0.5;
        } else if (fltType.equals(FLT_TYPE_INTERFACE)) {
            SI = 1.0;
        } else if (fltType.equals(FLT_TYPE_DEEP_SLAB)) {
            DS = 1.0;
        }

        // allocate dummy site variables
        if (siteType.equals(SITE_TYPE_C)) {
            deltaC = 1.0;
        } else if (siteType.equals(SITE_TYPE_D)) {
            deltaD = 1.0;
        }

        // Key attenuation code
        if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
            // Crustal attenuation relation
            lnSA_AB =
                    C1_gm[iper]
                            + C4AS_gm
                            * (mag - 6.)
                            + C3AS_gm[iper]
                            * Math.pow(8.5 - mag, 2)
                            + C5_gm[iper]
                            * rRup
                            + (C8_gm[iper] + C6AS_gm * (mag - 6.))
                            * Math.log(Math.sqrt(Math.pow(rRup, 2.)
                                    + Math.pow(C10AS_gm[iper], 2.)))
                            + C46_gm[iper] * rVol + C32_gm * CN
                            + C33AS_gm[iper] * CR;

            // Subduction attenuation relation
            // lnSA_AB=C11_gm[iper]+(C12y_gm+(C15_gm[iper]-C17_gm[iper])*C19y_gm)*(mag-6)+C13y_gm[iper]*Math.pow(10-mag,3.)+C17_gm[iper]*Math.log(rRup+C18y_gm*Math.exp(C19y_gm*mag))+C20[iper]*hc+C24_gm[iper]*SI+C46_gm[iper]*rVol*(1-DS);

            // site terms
            lnSA_CD =
                    lnSA_AB
                            + C29_gm[iper]
                            * deltaC
                            + (C30AS_gm[iper]
                                    * Math.log(Math.exp(lnSA_AB) + 0.03) + C43_gm[iper])
                            * deltaD;
        } else { // i.e. component.equals(COMPONENT_LARGERHORIZ)
            // Crustal attenuation relation
            lnSA_AB =
                    C1_lh[iper]
                            + C4AS_lh
                            * (mag - 6.)
                            + C3AS_lh[iper]
                            * Math.pow(8.5 - mag, 2)
                            + C5_lh[iper]
                            * rRup
                            + (C8_lh[iper] + C6AS_lh * (mag - 6.))
                            * Math.log(Math.sqrt(Math.pow(rRup, 2.)
                                    + Math.pow(C10AS_lh[iper], 2.)))
                            + C46_lh[iper] * rVol + C32_lh * CN
                            + C33AS_lh[iper] * CR;

            // Subduction attenuation relation
            // lnSA_AB=C11_lh[iper]+(C12y_lh+(C15_lh[iper]-C17_lh[iper])*C19y_lh)*(mag-6)+C13y_lh[iper]*Math.pow(10-mag,3.)+C17_lh[iper]*Math.log(rRup+C18y_lh*Math.exp(C19y_lh*mag))+C20[iper]*hc+C24_lh[iper]*SI+C46_lh[iper]*rVol*(1-DS);

            // site terms
            lnSA_CD =
                    lnSA_AB
                            + C29_lh[iper]
                            * deltaC
                            + (C30AS_lh[iper]
                                    * Math.log(Math.exp(lnSA_AB) + 0.03) + C43_lh[iper])
                            * deltaD;
        }

        double lnSA = lnSA_CD;

        return lnSA;
    }

    public double getStdDev(int iper, String stdDevType, String component) {

        if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) {
            return 0.0;
        } else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER)) {
            double sigmaInter;
            if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
                sigmaInter = tau_gm[iper];
            } else {
                sigmaInter = tau_lh[iper];
            }
            return (sigmaInter);
        } else {
            double sigmaIntra;
            if (mag <= 5.0) {
                if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
                    sigmaIntra = sigma6_gm[iper] - sigSlope_gm[iper];
                } else {
                    sigmaIntra = sigma6_lh[iper] - sigSlope_lh[iper];
                }
            } else if (mag >= 7.0) {
                if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
                    sigmaIntra = sigma6_gm[iper] + sigSlope_gm[iper];
                } else {
                    sigmaIntra = sigma6_lh[iper] + sigSlope_lh[iper];
                }
            } else {
                if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
                    sigmaIntra =
                            sigma6_gm[iper] + sigSlope_gm[iper] * (mag - 6.);
                } else {
                    sigmaIntra =
                            sigma6_lh[iper] + sigSlope_lh[iper] * (mag - 6.);
                }
            }

            if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA)) {
                return sigmaIntra;
            } else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL)) {
                double sigmaInter;
                if (component.equals(ComponentParam.COMPONENT_AVE_HORZ)) {
                    sigmaInter = tau_gm[iper];
                } else {
                    sigmaInter = tau_lh[iper];
                }
                double sigmaTotal =
                        Math.sqrt(Math.pow(sigmaIntra, 2.)
                                + Math.pow(sigmaInter, 2.));
                return (sigmaTotal);
            } else {
                return Double.NaN;
            }
        }
    }

    /**
     * This listens for parameter changes and updates the primitive parameters
     * accordingly
     * 
     * @param e
     *            ParameterChangeEvent
     */
    public void parameterChange(ParameterChangeEvent e) {

        String pName = e.getParameterName();
        Object val = e.getNewValue();
        parameterChange = true;
        if (pName.equals(DistanceRupParameter.NAME)) {
            rRup = ((Double) val).doubleValue();
        } else if (pName.equals(magParam.NAME)) {
            mag = ((Double) val).doubleValue();
        } else if (pName.equals(StdDevTypeParam.NAME)) {
            stdDevType = (String) val;
        } else if (pName.equals(FaultTypeParam.NAME)) {
            fltType = (String) fltTypeParam.getValue();
        } else if (pName.equals(ComponentParam.NAME)) {
            component = (String) val;
        } else if (pName.equals(PeriodParam.NAME)) {
            intensityMeasureChanged = true;
        }
    }

    /**
     * Allows to reset the change listeners on the parameters
     */
    public void resetParameterEventListeners() {
        distanceRupParam.removeParameterChangeListener(this);
        siteTypeParam.removeParameterChangeListener(this);
        magParam.removeParameterChangeListener(this);
        fltTypeParam.removeParameterChangeListener(this);
        stdDevTypeParam.removeParameterChangeListener(this);
        componentParam.removeParameterChangeListener(this);
        saPeriodParam.removeParameterChangeListener(this);

        this.initParameterEventListeners();
    }

    /**
     * Adds the parameter change listeners. This allows to listen to when-ever
     * the parameter is changed.
     */
    protected void initParameterEventListeners() {

        distanceRupParam.addParameterChangeListener(this);
        siteTypeParam.addParameterChangeListener(this);
        magParam.addParameterChangeListener(this);
        fltTypeParam.addParameterChangeListener(this);
        stdDevTypeParam.addParameterChangeListener(this);
        componentParam.addParameterChangeListener(this);
        saPeriodParam.addParameterChangeListener(this);
    }

    /**
     * This provides a URL where more info on this model can be obtained
     * 
     * @throws MalformedURLException
     *             if returned URL is not a valid URL.
     * @returns the URL to the AttenuationRelationship document on the Web.
     */
    public URL getInfoURL() throws MalformedURLException {
        return new URL(
                "http://www.opensha.org/documentation/modelsImplemented/attenRel/McVerryetal_2000.html");
    }
}
