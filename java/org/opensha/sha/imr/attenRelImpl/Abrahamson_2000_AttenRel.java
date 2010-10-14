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
import java.util.Enumeration;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.TreeSet;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.IMRException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FaultUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
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
 * <b>Title:</b> Abrahamson_2000_AttenRel
 * <p>
 * 
 * <b>Description:</b> This implements the Attenuation Relationship developed by
 * Abrahamson (2000, <i>Proc. of 6th Int. Conf. on Seismic Zonation, Palm
 * Springs</i>, Earthq. Eng. Res. Inst.). NOTE: This is only for strike-slip
 * earthquakes (even though Somerville et al. (1997) handles all types), and is
 * implemented only for the average horizontal component. One can easily add
 * fault normal and fault parallel components too, but the specs would have to
 * be obtained from Norm (the necessary info is not contained in the paper). SA
 * periods down to 0 are included even though the directivity effects are zero
 * below 0.6 sec (PGA is not an option for this reason).
 * <p>
 * 
 * Supported Intensity-Measure Parameters:
 * <p>
 * <UL>
 * <LI>saParam - Response Spectral Acceleration
 * </UL>
 * <p>
 * Other Independent Parameters:
 * <p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceRupParam - closest distance to surface projection of fault
 * <LI>siteTypeParam - "Rock/Shallow-Soil" versus "Deep-Soil"
 * <LI>fltTypeParam - Style of faulting
 * <LI>xDirParam - Directivity Parameter X
 * <LI>thetaDirParam - Directivity Parameter Theta
 * <LI>componentParam - Component of shaking
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL>
 * <p>
 * 
 * @author Edward H. Field
 * @created June, 2002
 * @version 1.0
 */

public class Abrahamson_2000_AttenRel extends AttenuationRelationship implements
        ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI {

    private final static String C = "Abrahamson_2000_AttenRel";
    private final static boolean D = false;
    public final static String NAME = "Abrahamson (2000)";
    public final static String SHORT_NAME = "Abrahamson2000";
    private static final long serialVersionUID = 1234567890987654351L;

    // URL Info String
    private final static String URL_INFO_STRING =
            "http://www.opensha.org/documentation/modelsImplemented/attenRel/Abrahamson_2000.html";

    // style of faulting options
    // private final static String FLT_TYPE_REVERSE = "Reverse";
    // private final static String FLT_TYPE_REV_OBL = "Reverse-Oblique";
    // private final static String FLT_TYPE_OTHER = "Other";
    // private final static String FLT_TYPE_DEFAULT = "Other";
    public final static String FLT_TYPE_SS = "Strike Slip";

    /**
     * Site Type Parameter ("Rock/Shallow-Soil" versus "Deep-Soil")
     */
    private StringParameter siteTypeParam = null;
    public final static String SITE_TYPE_NAME = AS_1997_AttenRel.SITE_TYPE_NAME;
    // no units
    public final static String SITE_TYPE_INFO =
            "Geological conditions at the site";
    public final static String SITE_TYPE_ROCK = "Rock/Shallow-Soil";
    public final static String SITE_TYPE_SOIL = "Deep-Soil";
    public final static String SITE_TYPE_DEFAULT = SITE_TYPE_ROCK;

    /*
     * This is not needed here because only strike-slip events are supported
     * 
     * Specifies whether the site is directly over the rupture surface.<p> This
     * should really be a boolean sublcass of PropagationEffectParameter
     * 
     * private StringParameter isOnHangingWallParam = null; private final static
     * String IS_ON_HANGING_WALL_NAME = "On Hanging Wall"; private final static
     * String IS_ON_HANGING_WALL_INFO = "Is site directly over rupture?";
     * private final static String IS_ON_HANGING_WALL_TRUE = "Yes"; private
     * final static String IS_ON_HANGING_WALL_FALSE = "No"; private final static
     * String IS_ON_HANGING_WALL_DEFAULT = "No";
     */

    // these were given to Ned Field by Norm Abrahamson over the phone
    // (they're not given in their 1997 paper)
    protected final static Double MAG_WARN_MIN = new Double(4.5);
    protected final static Double MAG_WARN_MAX = new Double(8);
    protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
    protected final static Double DISTANCE_RUP_WARN_MAX = new Double(200.0);

    /**
     * theta directivity parameter.
     */
    protected DoubleParameter thetaDirParam = null;
    public final static String THETA_NAME = "theta";
    public final static String THETA_UNITS = "degrees";
    protected final static Double THETA_MIN = new Double(-90);
    protected final static Double THETA_MAX = new Double(90);
    protected final static Double THETA_DEFAULT = new Double(0);
    public final static String THETA_INFO =
            "Angle Between Fault & Ray Path Directivity Parameter";

    /**
     * "X" directivity parameter representing the length ratio, or fraction of
     * fault along strike that ruptures toward the site.
     */
    protected DoubleParameter xDirParam = null;
    public final static String X_NAME = "X";
    protected final static String X_UNITS = null;
    protected final static Double X_MIN = new Double(0);
    protected final static Double X_MAX = new Double(1);
    protected final static Double X_DEFAULT = new Double(1);
    public final static String X_INFO = "Length Ratio Directivity Parameter";

    /**
     * The current set of coefficients based on the selected intensityMeasure
     */
    private Abrahamson_2000_AttenRelCoefficients coeff = null;

    /**
     * Hashtable of coefficients for the supported intensityMeasures
     */
    protected Hashtable<String, Abrahamson_2000_AttenRelCoefficients> horzCoeffs =
            new Hashtable<String, Abrahamson_2000_AttenRelCoefficients>();

    // coefficients that don't depend on period (but do depend on component):
    private double a2, a4, a13, c1, c5, n;

    // for issuing warnings:
    private transient ParameterChangeWarningListener warningListener = null;

    /**
     * Determines the style of faulting from the rake angle (which comes from
     * the eqkRupture object) and fills in the value of the fltTypeParam; since
     * their paper does not quantify the distinction, Norm advised as follows:
     * Reverse if 67.5<rake<112.5; Oblique-Reverse if 22.5<rake<67.5 or
     * 112.5<rake<157.5; Other is rake is something else (strike slip and normal
     * faulting).
     * 
     * @param rake
     *            in degrees
     * @throws InvalidRangeException
     *             If not valid rake angle
     */
    protected void setFaultTypeFromRake(double rake)
            throws InvalidRangeException {
        FaultUtils.assertValidRake(rake);
        if ((rake < 22.5 && rake > -22.5) || (rake < -157.5 && rake > 157.5)) {
            fltTypeParam.setValue(FLT_TYPE_SS);
        } else {
            throw new InvalidRangeException(NAME
                    + " can only be used with strike-slip events"
                    + " (rake must be within 22.5 degrees of 0 or 180)");
        }
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
    @Override
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
     * @throws ParameterException
     *             Thrown if the Site object doesn't contain a Vs30 parameter
     */
    @Override
    public void setSite(Site site) throws ParameterException {

        siteTypeParam.setValue((String) site.getParameter(SITE_TYPE_NAME)
                .getValue());
        this.site = site;
        setPropagationEffectParams();
    }

    /**
     * This sets the site and eqkRupture, and the related parameters, from the
     * propEffect object passed in. Warning constrains are ingored.
     * 
     * @param propEffect
     * @throws ParameterExceptionThrown
     *             if the Site object doesn't contain a Vs30 parameter
     * @throws InvalidRangeException
     *             thrown if rake is out of bounds
     */
    @Override
    public void setPropagationEffect(PropagationEffect propEffect)
            throws ParameterException, InvalidRangeException {

        this.site = propEffect.getSite();
        this.eqkRupture = propEffect.getEqkRupture();

        // set the locat site-type param
        this.siteTypeParam.setValue((String) site.getParameter(SITE_TYPE_NAME)
                .getValue());

        magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
        setFaultTypeFromRake(eqkRupture.getAveRake());

        // set the distance param
        propEffect.setParamValue(distanceRupParam);

        // there is no hanging wall param here

        // set the directivity parameters
        setDirectivityParams();
    }

    /**
     * This calculates the distanceRupParam and isOnHangingWallParam values
     * based on the current site and eqkRupture.
     */
    @Override
    protected void setPropagationEffectParams() {

        if ((this.site != null) && (this.eqkRupture != null)) {

            distanceRupParam.setValue(eqkRupture, site);
            setDirectivityParams();

        }
    }

    /**
     * This computes the directivity parameters
     */
    protected void setDirectivityParams() {

        EvenlyGriddedSurfaceAPI surface = eqkRupture.getRuptureSurface();
        Location siteLoc = site.getLocation();
        Location hypLoc = eqkRupture.getHypocenterLocation();
        if (hypLoc == null) {
            throw new RuntimeException(
                    "The hypocenter has not been set for the earthquake rupture!");
        }

        int numTrPts = surface.getNumCols();

        if (numTrPts == 1) {
            throw new RuntimeException(
                    "Abrahamson 2000 attenuation cannot compute directivity for "
                            + "point source.");
        }

        // find the closest point on rupture trace
        double dist, closestDist = Double.MAX_VALUE;
        Location closestLoc = null;
        for (int c = 0; c < numTrPts; c++) {
            dist =
                    LocationUtils.horzDistance(siteLoc,
                            surface.getLocation(0, c));
            if (dist < closestDist) {
                closestDist = dist;
                closestLoc = surface.getLocation(0, c);
            }
        }

        // compute the distance between the closest point on the trace and the
        // hypocenter
        double s = LocationUtils.horzDistance(closestLoc, hypLoc);
        // get total length of rupture
        double L =
                LocationUtils.horzDistance(surface.getLocation(0, 0),
                        surface.getLocation(0, numTrPts - 1));
        double x = s / L;
        // make sure that x isn't slightly larger (due to numerical impecision)
        if (x > 1.0 & x < 1.001) {
            x = 1.0;
        }
        // now set the x parameter
        xDirParam.setValue(x);

        // get the angle diff (theta) if s is greater than ~zero
        // (this avoids the undefined angle problem when hypLoc=closestLoc)
        double angleDiff;
        if (s > 0.01) {
            LocationVector dir;
            dir = LocationUtils.vector(hypLoc, siteLoc);
            double angle1 = dir.getAzimuth();
            if (angle1 < 0) {
                angle1 += 360; // make it positive to avoid confusion
            }
            dir = LocationUtils.vector(hypLoc, closestLoc);
            double angle2 = dir.getAzimuth();
            if (angle2 < 0) {
                angle2 += 360; // make it positive to avoid confusion
            }
            angleDiff = angle2 - angle1;
            // fix if 0 or 360 is in between the two directions
            if (angleDiff < -90) {
                angleDiff += 360;
            } else if (angleDiff > 90) {
                angleDiff -= 360;
            }
            if (D) {
                System.out.println("hyp=" + (float) hypLoc.getLatitude() + ", "
                        + (float) hypLoc.getLongitude() + "; clLoc="
                        + (float) closestLoc.getLatitude() + ", "
                        + (float) closestLoc.getLongitude() + "; siteLoc="
                        + (float) siteLoc.getLatitude() + ", "
                        + (float) siteLoc.getLongitude() + "; angle1 = "
                        + (float) angle1 + "; angle2 = " + (float) angle2
                        + "; theta = " + (float) angleDiff + "; s = " + s);
            }
        } else {
            angleDiff = 90; // set as anything since s = 0
        }

        // now set the theta parameter
        thetaDirParam.setValue(angleDiff);

    }

    /**
     * This function determines which set of coefficients in the HashMap are to
     * be used given the current intensityMeasure (im) Parameter. The lookup is
     * done keyed on the name of the im, plus the period value if im.getName()
     * == "SA" (seperated by "/").
     * 
     * SWR: I choose the name <code>update</code> instead of set, because set is
     * so common to java bean fields, i.e. getters and setters, that set()
     * usually implies passing in a new value to the java bean field. I prefer
     * update or refresh to functions that change internal values internally
     */
    protected void updateCoefficients() throws ParameterException {

        // Check that parameter exists
        if (im == null) {
            throw new ParameterException(
                    C
                            + ": updateCoefficients(): "
                            + "The Intensity Measusre Parameter has not been set yet, unable to process.");
        }

        StringBuffer key = new StringBuffer(im.getName());
        if (im.getName().equalsIgnoreCase(SA_Param.NAME)) {
            key.append("/" + saPeriodParam.getValue());
        }

        // so far only the horizontal coeffs case
        a2 = 0.512;
        a4 = -0.144;
        a13 = 0.17;
        c1 = 6.4;
        c5 = 0.03;
        n = 2;
        if (horzCoeffs.containsKey(key.toString())) {
            coeff = horzCoeffs.get(key.toString());
        } else {
            throw new ParameterException(C + ": setIntensityMeasureType(): "
                    + "Unable to locate coefficients with key = " + key);
        }
    }

    /**
     * No-Arg constructor. This initializes several ParameterList objects.
     */
    public Abrahamson_2000_AttenRel(
            ParameterChangeWarningListener warningListener) {

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
     * Calculates the mean of the exceedence probability distribution.
     * <p>
     * 
     * @return The mean value
     */
    @Override
    public double getMean() throws IMRException {

        double mag, dist, mean, x, theta;
        String fltType, isHW, siteType, component;

        try {
            mag = (magParam.getValue()).doubleValue();
            dist = ((Double) distanceRupParam.getValue()).doubleValue();
            fltType = fltTypeParam.getValue().toString();
            siteType = siteTypeParam.getValue().toString();
            // isHW = isOnHangingWallParam.getValue().toString();
            component = componentParam.getValue().toString();
            x = (xDirParam.getValue()).doubleValue();
            theta = (thetaDirParam.getValue()).doubleValue();
        } catch (NullPointerException e) {
            throw new IMRException(C + ": getMean(): " + ERR);
        }

        // check if distance is beyond the user specified max
        if (dist > USER_MAX_DISTANCE) {
            return VERY_SMALL_MEAN;
        }

        double F, f5, rockMeanPGA, rockMean, td, tm, yDir, cosTheta;
        int HW;

        // if ( fltType.equals( FLT_TYPE_REVERSE ) ) F = 1.0;
        // else if ( fltType.equals( FLT_TYPE_REV_OBL ) ) F = 0.5;
        // else F = 0.0;
        // Only strike-slip supported:
        F = 0.0;

        // if ( isHW.equals( IS_ON_HANGING_WALL_TRUE ) ) HW = 1;
        // else HW = 0;
        // Only strike-slip supported:
        HW = 0;

        // Get PGA coefficients for ave horz comp
        a2 = 0.512;
        a4 = -0.144;
        a13 = 0.17;
        c1 = 6.4;
        c5 = 0.03;
        n = 2;
        coeff = horzCoeffs.get(PGA_Param.NAME);

        rockMeanPGA = calcRockMean(mag, dist, F, HW);

        // now set coefficients for the correct im and component
        updateCoefficients();

        rockMean = calcRockMean(mag, dist, F, HW);

        // Compute f5, the site response term
        if (siteType.equals(SITE_TYPE_SOIL)) {
            f5 = coeff.a10 + coeff.a11 * Math.log(Math.exp(rockMeanPGA) + c5);

            mean = rockMean + f5; // Norm's S=1
        } else {
            mean = rockMean; // Norm's S=0
        }

        // Add Directivity Effect

        if (dist <= 30) {
            td = 1.0;
        } else if (dist > 30 && dist <= 60) {
            td = 1.0 - (dist - 30.0) / 30.0;
        } else {
            td = 0;
        }

        if (mag <= 6) {
            tm = 0.0;
        } else if (mag > 6 && mag <= 6.5) {
            tm = 1.0 + (mag - 6.5) / 0.5;
        } else {
            tm = 1.0;
        }

        cosTheta = Math.cos(theta * Math.PI / 180);

        if (x <= 0.4) {
            yDir = coeff.c1 + 1.88 * coeff.c2 * x * cosTheta;
        } else {
            yDir = coeff.c1 + 0.75 * coeff.c2 * cosTheta;
        }

        mean += yDir * td * tm;

        // return the result
        return (mean);
    }

    /**
     * This calculates the mean (natural log) for a rock site
     * 
     * @param mag
     *            magnidue
     * @param dist
     *            distanceRup
     * @param F
     *            style of faulting factor (0, 0.5, or 1.0)
     * @param HW
     *            1 if on hanging wall; 0 otherwise
     * @return Mean for a rock site
     */
    private double calcRockMean(double mag, double dist, double F, int HW) {

        // Norm's sub-equation terms (all but f5):
        double f1, f3, f4, fHWM, fHWRrup;

        double R = Math.sqrt(dist * dist + coeff.c4 * coeff.c4);

        // Compute f1
        if (mag <= c1) {
            f1 =
                    coeff.a1 + a2 * (mag - c1) + coeff.a12
                            * Math.pow(8.5 - mag, n) + Math.log(R)
                            * (coeff.a3 + a13 * (mag - c1));
        } else {
            f1 =
                    coeff.a1 + a4 * (mag - c1) + coeff.a12
                            * Math.pow(8.5 - mag, n) + Math.log(R)
                            * (coeff.a3 + a13 * (mag - c1));
        }

        // Compute f3, the style of faulting factor
        if (mag <= 5.8) {
            f3 = coeff.a5;
        } else if (mag > 5.8 && mag < c1) {
            f3 = coeff.a5 + (coeff.a6 - coeff.a5) * (mag - 5.8) / (c1 - 5.8);
        } else {
            f3 = coeff.a6;
        }

        // Compute f4, compute the hanging wall effect

        // only do these calculations if it's not going to be zeroed out
        if (HW == 1) {
            if (mag <= 5.5) {
                fHWM = 0.0;
            } else if (mag > 5.5 && mag < 6.5) {
                fHWM = mag - 5.5;
            } else {
                fHWM = 1.0;
            }

            if (dist <= 4.0) {
                fHWRrup = 0;
            } else if (dist > 4 && dist <= 8) {
                fHWRrup = coeff.a9 * (dist - 4) / 4;
            } else if (dist > 8 && dist <= 18) {
                fHWRrup = coeff.a9;
            } else if (dist > 18 && dist <= 25) {
                fHWRrup = coeff.a9 * (1 - (dist - 18) / 7);
            } else {
                fHWRrup = 0;
            }

            // f4 = fHWM*fHWRrup;
            return f1 + F * f3 + fHWM * fHWRrup;
        } else {
            return f1 + F * f3;
        }
        // f4 = 0; // set it to anything since HW = 0

        // return f1 + F*f3 + HW*f4;
    }

    /**
     * @return The stdDev value
     */
    @Override
    public double getStdDev() throws IMRException {

        if (stdDevTypeParam.getValue()
                .equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) {
            return 0;
        } else {

            // this is inefficient if the im has not been changed in any way
            updateCoefficients();

            double sigma;

            // only horz case
            double mag = (magParam.getValue()).doubleValue();
            if (mag <= 5.0) {
                sigma = coeff.b5;
            } else if (mag > 5.0 && mag < 7.0) {
                sigma = coeff.b5 - coeff.b6 * (mag - 5.0);
            } else {
                sigma = coeff.b5 - 2 * coeff.b6;
            }

            // Now make directivity correction

            sigma -= 0.05 * coeff.c2 / 1.333;

            return (sigma);
        }
    }

    @Override
    public void setParamDefaults() {

        siteTypeParam.setValue(SITE_TYPE_DEFAULT);
        magParam.setValueAsDefault();
        fltTypeParam.setValueAsDefault();
        distanceRupParam.setValueAsDefault();
        saParam.setValueAsDefault();
        saPeriodParam.setValueAsDefault();
        saDampingParam.setValueAsDefault();
        componentParam.setValueAsDefault();
        stdDevTypeParam.setValueAsDefault();
        // isOnHangingWallParam.setValue( IS_ON_HANGING_WALL_DEFAULT );
        xDirParam.setValue(X_DEFAULT);
        thetaDirParam.setValue(THETA_DEFAULT);

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
        // meanIndependentParams.addParameter( isOnHangingWallParam );
        meanIndependentParams.addParameter(xDirParam);
        meanIndependentParams.addParameter(thetaDirParam);
        meanIndependentParams.addParameter(componentParam);

        // params that the stdDev depends upon
        stdDevIndependentParams.clear();
        stdDevIndependentParams.addParameter(stdDevTypeParam);
        stdDevIndependentParams.addParameter(magParam);
        stdDevIndependentParams.addParameter(componentParam);

        // params that the exceed. prob. depends upon
        exceedProbIndependentParams.clear();
        exceedProbIndependentParams.addParameter(distanceRupParam);
        exceedProbIndependentParams.addParameter(siteTypeParam);
        exceedProbIndependentParams.addParameter(magParam);
        exceedProbIndependentParams.addParameter(fltTypeParam);
        // exceedProbIndependentParams.addParameter( isOnHangingWallParam );
        exceedProbIndependentParams.addParameter(xDirParam);
        exceedProbIndependentParams.addParameter(thetaDirParam);
        exceedProbIndependentParams.addParameter(componentParam);
        exceedProbIndependentParams.addParameter(stdDevTypeParam);
        exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
        exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

        // params that the IML at exceed. prob. depends upon
        imlAtExceedProbIndependentParams
                .addParameterList(exceedProbIndependentParams);
        imlAtExceedProbIndependentParams.addParameter(exceedProbParam);

    }

    /**
     * Creates the Site-Type parameter and adds it to the siteParams list. Makes
     * the parameters noneditable.
     */
    @Override
    protected void initSiteParams() {

        StringConstraint siteConstraint = new StringConstraint();
        siteConstraint.addString(SITE_TYPE_ROCK);
        siteConstraint.addString(SITE_TYPE_SOIL);
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
    @Override
    protected void initEqkRuptureParams() {

        magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);

        // Fault type parameter
        StringConstraint constraint = new StringConstraint();
        constraint.addString(FLT_TYPE_SS);
        constraint.setNonEditable();
        fltTypeParam = new FaultTypeParam(constraint, FLT_TYPE_SS);

        eqkRuptureParams.clear();
        eqkRuptureParams.addParameter(magParam);
        eqkRuptureParams.addParameter(fltTypeParam);
    }

    /**
     * Creates the Propagation Effect parameters and adds them to the
     * propagationEffectParams list. Makes the parameters noneditable.
     */
    @Override
    protected void initPropagationEffectParams() {

        distanceRupParam = new DistanceRupParameter(0.0);
        distanceRupParam.addParameterChangeWarningListener(warningListener);
        DoubleConstraint warn =
                new DoubleConstraint(DISTANCE_RUP_WARN_MIN,
                        DISTANCE_RUP_WARN_MAX);
        warn.setNonEditable();
        distanceRupParam.setWarningConstraint(warn);
        distanceRupParam.setNonEditable();

        /*
         * NOT NEETED // create hanging wall parameter StringConstraint
         * HW_Constraint = new StringConstraint(); HW_Constraint.addString(
         * IS_ON_HANGING_WALL_TRUE ); HW_Constraint.addString(
         * IS_ON_HANGING_WALL_FALSE ); HW_Constraint.setNonEditable();
         * isOnHangingWallParam = new StringParameter( IS_ON_HANGING_WALL_NAME,
         * HW_Constraint, IS_ON_HANGING_WALL_DEFAULT);
         * isOnHangingWallParam.setInfo( IS_ON_HANGING_WALL_INFO );
         * isOnHangingWallParam.setNonEditable();
         */

        // create thetaDirParam:
        DoubleConstraint thetaDirConstraint =
                new DoubleConstraint(THETA_MIN, THETA_MAX);
        thetaDirConstraint.setNonEditable();
        thetaDirParam =
                new DoubleParameter(THETA_NAME, thetaDirConstraint, THETA_UNITS);
        thetaDirParam.setInfo(THETA_INFO);
        thetaDirParam.setNonEditable();

        // create xDirParam:
        DoubleConstraint xDirConstraint = new DoubleConstraint(X_MIN, X_MAX);
        xDirConstraint.setNonEditable();
        xDirParam = new DoubleParameter(X_NAME, xDirConstraint, X_UNITS);
        xDirParam.setInfo(X_INFO);
        xDirParam.setNonEditable();

        propagationEffectParams.addParameter(distanceRupParam);
        propagationEffectParams.addParameter(thetaDirParam);
        propagationEffectParams.addParameter(xDirParam);
        // propagationEffectParams.addParameter( isOnHangingWallParam );

        // This is needed to compute the isOn HangingWallParam; it does not
        // need to be added to any Param List
        // distanceJBParam = new DistanceJBParameter();
    }

    /**
     * Creates the supported IM parameter (only SA), as well as the
     * independenParameters of SA (periodParam and dampingParam) and adds it to
     * the supportedIMParams list. Makes the parameters noneditable.
     */
    @Override
    protected void initSupportedIntensityMeasureParams() {

        // NOTE: pga is not supported because it's no different than for
        // AS_1997_AttenRel

        // Create saParam's "Period" independent parameter:
        DoubleDiscreteConstraint periodConstraint =
                new DoubleDiscreteConstraint();
        TreeSet<Double> set = new TreeSet<Double>();
        Enumeration<String> keys = horzCoeffs.keys(); // same as for vertCoeffs
        while (keys.hasMoreElements()) {
            Abrahamson_2000_AttenRelCoefficients coeff =
                    horzCoeffs.get(keys.nextElement());
            if (coeff.period >= 0) {
                set.add(new Double(coeff.period));
            }
        }
        Iterator<Double> it = set.iterator();
        while (it.hasNext()) {
            periodConstraint.addDouble(it.next());
        }
        periodConstraint.setNonEditable();
        saPeriodParam = new PeriodParam(periodConstraint);
        saDampingParam = new DampingParam();
        saParam = new SA_Param(saPeriodParam, saDampingParam);
        saParam.setNonEditable();

        // Add the warning listeners:
        saParam.addParameterChangeWarningListener(warningListener);

        // Put parameters in the supportedIMParams list:
        supportedIMParams.clear();

        supportedIMParams.addParameter(saParam);

    }

    /**
     * Creates other Parameters that the mean or stdDev depends upon, such as
     * the Component or StdDevType parameters.
     */
    @Override
    protected void initOtherParams() {

        // init other params implemented in parent class
        super.initOtherParams();

        // the Component Parameter
        StringConstraint constraint = new StringConstraint();
        constraint.addString(componentParam.COMPONENT_AVE_HORZ);
        constraint.setNonEditable();
        componentParam =
                new ComponentParam(constraint,
                        componentParam.COMPONENT_AVE_HORZ);

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
     * This creates the hashtable of coefficients for the supported
     * intensityMeasures (im). The key is the im parameter name, plus the period
     * value for SA (separated by "/"). For example, the key for SA at 1.00
     * second period is "SA/1.00".
     */
    protected void initCoefficients() {

        String S = C + ": initCoefficients():";
        if (D) {
            System.out.println(S + "Starting");
        }

        horzCoeffs.clear();

        // PGA
        Abrahamson_2000_AttenRelCoefficients coeff =
                new Abrahamson_2000_AttenRelCoefficients(PGA_Param.NAME, 0,
                        5.6, 1.64, -1.145, 0.61, 0.26, 0.37, -0.417, -0.23, 0,
                        0.7, 0.135, 0, 0);

        // SA/5.00
        Abrahamson_2000_AttenRelCoefficients coeff0 =
                new Abrahamson_2000_AttenRelCoefficients(SA_Param.NAME + '/'
                        + (new Double("5.00")).doubleValue(), 5.00, 3.5, -1.46,
                        -0.725, 0.4, -0.2, 0, 0.664, 0.04, -0.215, 0.89, 0.087,
                        -0.797, 1.757);
        // SA/4.00
        Abrahamson_2000_AttenRelCoefficients coeff1 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("4.00")).doubleValue(), 4.00, 3.5, -1.13,
                        -0.725, 0.4, -0.2, 0.039, 0.64, 0.04, -0.1956, 0.88,
                        0.092, -0.713, 1.571);
        // SA/3.00
        Abrahamson_2000_AttenRelCoefficients coeff2 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("3.00")).doubleValue(), 3.00, 3.5, -0.69,
                        -0.725, 0.4, -0.156, 0.089, 0.63, 0.04, -0.1726, 0.87,
                        0.097, -0.605, 1.333);
        // SA/2.00
        Abrahamson_2000_AttenRelCoefficients coeff3 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("2.00")).doubleValue(), 2.00, 3.5, -0.15,
                        -0.725, 0.4, -0.094, 0.16, 0.61, 0.04, -0.14, 0.85,
                        0.105, -0.452, 0.998);
        // SA/1.50
        Abrahamson_2000_AttenRelCoefficients coeff4 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("1.50")).doubleValue(), 1.50, 3.55, 0.26,
                        -0.7721, 0.438, -0.049, 0.21, 0.6, 0.04, -0.12, 0.84,
                        0.11, -0.344, 0.759);
        // SA/1.00
        Abrahamson_2000_AttenRelCoefficients coeff5 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("1.00")).doubleValue(), 1.00, 3.7, 0.828,
                        -0.8383, 0.49, 0.013, 0.281, 0.423, 0, -0.102, 0.83,
                        0.118, -0.192, 0.423);
        // // SA/0.85 NOT SUPPORTED
        // Abrahamson_2000_AttenRelCoefficients coeff6 = new
        // Abrahamson_2000_AttenRelCoefficients( "SA/" +( new Double( "0.85" )
        // ).doubleValue() ,
        // 0.85, 3.81, 1.02, -0.8648, 0.512, 0.038, 0.309, 0.37, -0.028,
        // -0.0927, 0.82, 0.121, );
        // SA/0.75
        Abrahamson_2000_AttenRelCoefficients coeff7 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.75")).doubleValue(), 0.75, 3.9, 1.16,
                        -0.8852, 0.528, 0.057, 0.331, 0.32, -0.05, -0.0862,
                        0.81, 0.123, -0.084, 0.185);
        // SA/0.60
        Abrahamson_2000_AttenRelCoefficients coeff8 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.60")).doubleValue(), 0.60, 4.12,
                        1.428, -0.9218, 0.557, 0.091, 0.37, 0.194, -0.089,
                        -0.074, 0.81, 0.127, 0.0, 0.0);
        // SA/0.50
        Abrahamson_2000_AttenRelCoefficients coeff9 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.50")).doubleValue(), 0.50, 4.3, 1.615,
                        -0.9515, 0.581, 0.119, 0.37, 0.085, -0.121, -0.0635,
                        0.8, 0.13, 0.0, 0.0);
        // SA/0.46
        Abrahamson_2000_AttenRelCoefficients coeff10 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.46")).doubleValue(), 0.46, 4.38,
                        1.717, -0.9652, 0.592, 0.132, 0.37, 0.02, -0.136,
                        -0.0594, 0.8, 0.132, 0.0, 0.0);
        // SA/0.40
        Abrahamson_2000_AttenRelCoefficients coeff11 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.40")).doubleValue(), 0.40, 4.52, 1.86,
                        -0.988, 0.61, 0.154, 0.37, -0.065, -0.16, -0.0518,
                        0.79, 0.135, 0.0, 0.0);
        // SA/0.36
        Abrahamson_2000_AttenRelCoefficients coeff12 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.36")).doubleValue(), 0.36, 4.62,
                        1.955, -1.0052, 0.61, 0.17, 0.37, -0.123, -0.173,
                        -0.046, 0.79, 0.135, 0.0, 0.0);
        // SA/0.30
        Abrahamson_2000_AttenRelCoefficients coeff13 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.30")).doubleValue(), 0.30, 4.8, 2.114,
                        -1.035, 0.61, 0.198, 0.37, -0.219, -0.195, -0.036,
                        0.78, 0.135, 0.0, 0.0);
        // SA/0.24
        Abrahamson_2000_AttenRelCoefficients coeff14 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.24")).doubleValue(), 0.24, 4.97,
                        2.293, -1.079, 0.61, 0.232, 0.37, -0.35, -0.223,
                        -0.0238, 0.77, 0.135, 0.0, 0.0);
        // SA/0.20
        Abrahamson_2000_AttenRelCoefficients coeff15 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.20")).doubleValue(), 0.20, 5.1, 2.406,
                        -1.115, 0.61, 0.26, 0.37, -0.445, -0.245, -0.0138,
                        0.77, 0.135, 0.0, 0.0);
        // SA/0.17
        Abrahamson_2000_AttenRelCoefficients coeff16 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.17")).doubleValue(), 0.17, 5.19, 2.43,
                        -1.135, 0.61, 0.26, 0.37, -0.522, -0.265, -0.004, 0.76,
                        0.135, 0.0, 0.0);
        // SA/0.15
        Abrahamson_2000_AttenRelCoefficients coeff17 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.15")).doubleValue(), 0.15, 5.27,
                        2.407, -1.145, 0.61, 0.26, 0.37, -0.577, -0.28, 0.005,
                        0.75, 0.135, 0.0, 0.0);
        // SA/0.12
        Abrahamson_2000_AttenRelCoefficients coeff18 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.12")).doubleValue(), 0.12, 5.39,
                        2.272, -1.145, 0.61, 0.26, 0.37, -0.591, -0.28, 0.018,
                        0.75, 0.135, 0.0, 0.0);
        // SA/0.10
        Abrahamson_2000_AttenRelCoefficients coeff19 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.10")).doubleValue(), 0.10, 5.5, 2.16,
                        -1.145, 0.61, 0.26, 0.37, -0.598, -0.28, 0.028, 0.74,
                        0.135, 0.0, 0.0);
        // SA/0.09
        Abrahamson_2000_AttenRelCoefficients coeff20 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.09")).doubleValue(), 0.09, 5.54, 2.1,
                        -1.145, 0.61, 0.26, 0.37, -0.609, -0.28, 0.03, 0.74,
                        0.135, 0.0, 0.0);
        // SA/0.075
        Abrahamson_2000_AttenRelCoefficients coeff21 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.075")).doubleValue(), 0.075, 5.58,
                        2.037, -1.145, 0.61, 0.26, 0.37, -0.628, -0.28, 0.03,
                        0.73, 0.135, 0.0, 0.0);
        // SA/0.06
        Abrahamson_2000_AttenRelCoefficients coeff22 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.06")).doubleValue(), 0.06, 5.6, 1.94,
                        -1.145, 0.61, 0.26, 0.37, -0.665, -0.28, 0.03, 0.72,
                        0.135, 0.0, 0.0);
        // SA/0.05
        Abrahamson_2000_AttenRelCoefficients coeff23 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.05")).doubleValue(), 0.05, 5.6, 1.87,
                        -1.145, 0.61, 0.26, 0.37, -0.62, -0.267, 0.028, 0.71,
                        0.135, 0.0, 0.0);
        // SA/0.04
        Abrahamson_2000_AttenRelCoefficients coeff24 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.04")).doubleValue(), 0.04, 5.6, 1.78,
                        -1.145, 0.61, 0.26, 0.37, -0.555, -0.251, 0.0245, 0.71,
                        0.135, 0.0, 0.0);
        // SA/0.03
        Abrahamson_2000_AttenRelCoefficients coeff25 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.03")).doubleValue(), 0.03, 5.6, 1.69,
                        -1.145, 0.61, 0.26, 0.37, -0.47, -0.23, 0.0143, 0.7,
                        0.135, 0.0, 0.0);
        // SA/0.02
        Abrahamson_2000_AttenRelCoefficients coeff26 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.02")).doubleValue(), 0.02, 5.6, 1.64,
                        -1.145, 0.61, 0.26, 0.37, -0.417, -0.23, 0, 0.7, 0.135,
                        0.0, 0.0);
        // SA/0.01
        Abrahamson_2000_AttenRelCoefficients coeff27 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.01")).doubleValue(), 0.01, 5.6, 1.64,
                        -1.145, 0.61, 0.26, 0.37, -0.417, -0.23, 0, 0.7, 0.135,
                        0.0, 0.0);
        // SA/0.0 -- same as 0.01
        Abrahamson_2000_AttenRelCoefficients coeff28 =
                new Abrahamson_2000_AttenRelCoefficients("SA/"
                        + (new Double("0.0")).doubleValue(), 0.0, 5.6, 1.64,
                        -1.145, 0.61, 0.26, 0.37, -0.417, -0.23, 0, 0.7, 0.135,
                        0.0, 0.0);

        horzCoeffs.put(coeff.getName(), coeff);
        horzCoeffs.put(coeff0.getName(), coeff0);
        horzCoeffs.put(coeff1.getName(), coeff1);
        horzCoeffs.put(coeff2.getName(), coeff2);
        horzCoeffs.put(coeff3.getName(), coeff3);
        horzCoeffs.put(coeff4.getName(), coeff4);
        horzCoeffs.put(coeff5.getName(), coeff5);
        // horzCoeffs.put( coeff6.getName(), coeff6 );
        horzCoeffs.put(coeff7.getName(), coeff7);
        horzCoeffs.put(coeff8.getName(), coeff8);
        horzCoeffs.put(coeff9.getName(), coeff9);

        horzCoeffs.put(coeff10.getName(), coeff10);
        horzCoeffs.put(coeff11.getName(), coeff11);
        horzCoeffs.put(coeff12.getName(), coeff12);
        horzCoeffs.put(coeff13.getName(), coeff13);
        horzCoeffs.put(coeff14.getName(), coeff14);
        horzCoeffs.put(coeff15.getName(), coeff15);
        horzCoeffs.put(coeff16.getName(), coeff16);
        horzCoeffs.put(coeff17.getName(), coeff17);
        horzCoeffs.put(coeff18.getName(), coeff18);
        horzCoeffs.put(coeff19.getName(), coeff19);

        horzCoeffs.put(coeff20.getName(), coeff20);
        horzCoeffs.put(coeff21.getName(), coeff21);
        horzCoeffs.put(coeff22.getName(), coeff22);
        horzCoeffs.put(coeff23.getName(), coeff23);
        horzCoeffs.put(coeff24.getName(), coeff24);
        horzCoeffs.put(coeff25.getName(), coeff25);
        horzCoeffs.put(coeff26.getName(), coeff26);
        horzCoeffs.put(coeff27.getName(), coeff27);
        horzCoeffs.put(coeff28.getName(), coeff28);
    }

    /**
     * get the name of this IMR
     * 
     * @returns the name of this IMR
     */
    @Override
    public String getName() {
        return NAME;
    }

    /**
     * Returns the Short Name of each AttenuationRelationship
     * 
     * @return String
     */
    @Override
    public String getShortName() {
        return SHORT_NAME;
    }

    /**
     * <b>Title:</b> Abrahamson_2000_AttenRelCoefficients<br>
     * <b>Description:</b> This class encapsulates all the coefficients needed
     * to calculate the Mean and StdDev for the Abrahamson_2000_AttenRel. One
     * instance of this class holds the set of coefficients for each period (one
     * row of their tables 3/4 (horz) or 5/6 (vert)).<br>
     * <b>Copyright:</b> Copyright (c) 2001 <br>
     * <b>Company:</b> <br>
     * 
     * 
     * @author Steven W Rock
     * @created February 27, 2002
     * @version 1.0
     */

    class Abrahamson_2000_AttenRelCoefficients implements NamedObjectAPI {

        protected final static String C =
                "Abrahamson_2000_AttenRelCoefficients";
        protected final static boolean D = true;

        /** For serialization. */
        private static final long serialVersionUID = 1234567890987654321L;

        protected String name;
        protected double period = -1;
        protected double c4;
        protected double a1;
        protected double a3;
        protected double a5;
        protected double a6;
        protected double a9;
        protected double a10;
        protected double a11;
        protected double a12;
        protected double b5;
        protected double b6;
        protected double c1; // these are the new ones
        protected double c2; // these are the new ones

        /**
         * Constructor for the Abrahamson_2000_AttenRelCoefficients object
         * 
         * @param name
         *            Description of the Parameter
         */
        public Abrahamson_2000_AttenRelCoefficients(String name) {
            this.name = name;
        }

        /**
         * Constructor for the Abrahamson_2000_AttenRelCoefficients object that
         * sets all values at once
         * 
         * @param name
         *            Description of the Parameter
         */
        public Abrahamson_2000_AttenRelCoefficients(String name, double period,
                double c4, double a1, double a3, double a5, double a6,
                double a9, double a10, double a11, double a12, double b5,
                double b6, double c1, double c2) {
            this.name = name;
            this.period = period;
            this.c4 = c4;
            this.a1 = a1;
            this.a3 = a3;
            this.a5 = a5;
            this.a6 = a6;
            this.a9 = a9;
            this.a10 = a10;
            this.a11 = a11;
            this.a12 = a12;
            this.b5 = b5;
            this.b6 = b6;
            this.c1 = c1;
            this.c2 = c2;
        }

        /**
         * Gets the name attribute of the Abrahamson_2000_AttenRelCoefficients
         * object
         * 
         * @return The name value
         */
        @Override
        public String getName() {
            return name;
        }

        /**
         * Debugging - prints out all cefficient names and values
         * 
         * @return Description of the Return Value
         */
        @Override
        public String toString() {

            StringBuffer b = new StringBuffer();
            b.append(C);
            b.append("\n  Period = " + period);
            b.append("\n  c4 = " + c4);
            b.append("\n  a1 = " + a1);
            b.append("\n  a2 = " + a2);
            b.append("\n  a3 = " + a3);
            b.append("\n  a4 = " + a4);
            b.append("\n  a5 = " + a5);
            b.append("\n  a6 = " + a6);
            b.append("\n  a9 = " + a9);
            b.append("\n  a10 = " + a10);
            b.append("\n  a11 = " + a11);
            b.append("\n  a12 = " + a12);
            b.append("\n  a13 = " + a13);
            b.append("\n  c1 = " + c1);
            b.append("\n  c5 = " + c5);
            b.append("\n  n = " + n);
            b.append("\n  b5 = " + b5);
            b.append("\n  b6 = " + b6);
            b.append("\n  c1 = " + c1);
            b.append("\n  c2 = " + c2);
            return b.toString();
        }
    }

    /**
     * This provides a URL where more info on this model can be obtained
     * 
     * @throws MalformedURLException
     *             if returned URL is not a valid URL.
     * @returns the URL to the AttenuationRelationship document on the Web.
     */
    @Override
    public URL getInfoURL() throws MalformedURLException {
        return new URL(URL_INFO_STRING);
    }

}
