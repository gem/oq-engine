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

package org.opensha.gem.GEM1.scratch;

import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.ListIterator;
import java.util.Map;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.ArbitrarilyDiscretizedFuncParameter;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.calc.HazardCurveCalculatorAPI;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
// import
// org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_EqkRupForecast;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BJF_1997_AttenRel;
import org.opensha.sha.imr.param.OtherParams.TectonicRegionTypeParam;
import org.opensha.sha.util.TRTUtils;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <p>
 * Title: HazardCurveCalculator
 * </p>
 * <p>
 * Description: This class calculates the Hazard curve based on the input
 * parameters imr, site and eqkRupforecast or eqkRupture (for probabilistic or
 * deterministic, respectively)
 * </p>
 * <p>
 * Copyright: Copyright (c) 2002
 * </p>
 * <p>
 * Company:
 * </p>
 * 
 * @author : Ned Field & Nitin Gupta & Vipin Gupta
 * @date Oct 28, 2002
 * @version 1.0
 */

public class HazardCurveCalculator extends UnicastRemoteObject implements
        HazardCurveCalculatorAPI, ParameterChangeWarningListener {

    protected final static String C = "HazardCurveCalculator";
    protected final static boolean D = false;

    // Info for parameter that sets the maximum distance considered
    private DoubleParameter maxDistanceParam;
    public final static String MAX_DISTANCE_PARAM_NAME = "Maximum Distance";
    public final String MAX_DISTANCE_PARAM_UNITS = "km";
    public final String MAX_DISTANCE_PARAM_INFO =
            "Earthquake Ruptures beyond this distance are ignored";
    public final double MAX_DISTANCE_PARAM_MIN = 0;
    public final double MAX_DISTANCE_PARAM_MAX = 40000;
    public final static Double MAX_DISTANCE_DEFAULT = new Double(200);

    // Info for parameter tells whether to apply a magnitude-dependent distance
    // cutoff
    private BooleanParameter includeMagDistFilterParam;
    public final static String INCLUDE_MAG_DIST_FILTER_PARAM_NAME =
            "Use Mag-Distance Filter?";
    public final String INCLUDE_MAG_DIST_FILTER_PARAM_INFO =
            "This specifies whether to apply the magnitude-distance filter";
    public final boolean INCLUDE_MAG_DIST_FILTER_PARAM_DEFAULT = false;

    // Info for parameter that specifies a magnitude-dependent distance cutoff
    // (distance on x-axis and mag on y-axis)
    private ArbitrarilyDiscretizedFuncParameter magDistCutoffParam;
    public final static String MAG_DIST_CUTOFF_PARAM_NAME =
            "Mag-Dist Cutoff Function";
    public final String MAG_DIST_CUTOFF_PARAM_INFO =
            "Distance cutoff is a function of mag (the function here, linearly interpolated)";
    double[] defaultCutoffMags = { 0, 5.25, 5.75, 6.25, 6.75, 7.25, 9 };
    double[] defaultCutoffDists = { 0, 25, 40, 60, 80, 100, 500 };

    // Info for parameter that sets the maximum distance considered
    private IntegerParameter numStochEventSetRealizationsParam;
    public final static String NUM_STOCH_EVENT_SETS_PARAM_NAME =
            "Num Event Sets";
    public final String NUM_STOCH_EVENT_SETS_PARAM_INFO =
            "Number of stochastic event sets for those types of calculations";
    public final int NUM_STOCH_EVENT_SETS_PARAM_MIN = 1;
    public final int NUM_STOCH_EVENT_SETS_PARAM_MAX = Integer.MAX_VALUE;
    public final static Integer NUM_STOCH_EVENT_SETS_PARAM_DEFAULT =
            new Integer(1);

    private ParameterList adjustableParams;

    // misc counting and index variables
    protected int currRuptures = -1;
    protected int totRuptures = 0;
    protected int sourceIndex;
    protected int numSources;

    /**
     * creates the HazardCurveCalculator object
     * 
     * @throws java.rmi.RemoteException
     */
    public HazardCurveCalculator() throws java.rmi.RemoteException {

        // Create adjustable parameters and add to list

        // Max Distance Parameter
        maxDistanceParam =
                new DoubleParameter(MAX_DISTANCE_PARAM_NAME,
                        MAX_DISTANCE_PARAM_MIN, MAX_DISTANCE_PARAM_MAX,
                        MAX_DISTANCE_PARAM_UNITS, MAX_DISTANCE_DEFAULT);
        maxDistanceParam.setInfo(MAX_DISTANCE_PARAM_INFO);

        // Include Mag-Distance Filter Parameter
        includeMagDistFilterParam =
                new BooleanParameter(INCLUDE_MAG_DIST_FILTER_PARAM_NAME,
                        INCLUDE_MAG_DIST_FILTER_PARAM_DEFAULT);
        includeMagDistFilterParam.setInfo(INCLUDE_MAG_DIST_FILTER_PARAM_INFO);

        // Mag-Distance Cutoff Parameter
        ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
        func.setName("mag-dist function");
        for (int i = 0; i < defaultCutoffMags.length; i++)
            func.set(defaultCutoffDists[i], defaultCutoffMags[i]);
        magDistCutoffParam =
                new ArbitrarilyDiscretizedFuncParameter(
                        MAG_DIST_CUTOFF_PARAM_NAME, func);
        magDistCutoffParam.setInfo(MAG_DIST_CUTOFF_PARAM_INFO);

        // Max Distance Parameter
        numStochEventSetRealizationsParam =
                new IntegerParameter(NUM_STOCH_EVENT_SETS_PARAM_NAME,
                        NUM_STOCH_EVENT_SETS_PARAM_MIN,
                        NUM_STOCH_EVENT_SETS_PARAM_MAX,
                        NUM_STOCH_EVENT_SETS_PARAM_DEFAULT);
        numStochEventSetRealizationsParam
                .setInfo(NUM_STOCH_EVENT_SETS_PARAM_INFO);

        adjustableParams = new ParameterList();
        adjustableParams.addParameter(maxDistanceParam);
        adjustableParams.addParameter(numStochEventSetRealizationsParam);
        adjustableParams.addParameter(includeMagDistFilterParam);
        adjustableParams.addParameter(magDistCutoffParam);

    }

    /**
     * This sets the maximum distance of sources to be considered in the
     * calculation. Sources more than this distance away are ignored. This is
     * simply a direct way of setting the parameter. Default value is 250 km.
     * 
     * @param distance
     *            : the maximum distance in km
     */
    public void setMaxSourceDistance(double distance)
            throws java.rmi.RemoteException {
        maxDistanceParam.setValue(distance);
    }

    public void setNumStochEventSetRealizations(int numRealizations) {
        numStochEventSetRealizationsParam.setValue(numRealizations);
    }

    /**
     * This is a direct way of getting the distance cutoff from that parameter
     */
    public double getMaxSourceDistance() throws java.rmi.RemoteException {
        return maxDistanceParam.getValue().doubleValue();
    }

    /**
     * This sets the mag-dist filter function (distance on x-axis and mag on
     * y-axis), and also sets the value of includeMagDistFilterParam as true.
     * 
     * @param magDistfunc
     */
    public void setMagDistCutoffFunc(ArbitrarilyDiscretizedFunc magDistfunc)
            throws java.rmi.RemoteException {
        includeMagDistFilterParam.setValue(true);
        magDistCutoffParam.setValue(magDistfunc);
    }

    public void setIncludeMagDistCutoff(boolean include)
            throws java.rmi.RemoteException {
        this.includeMagDistFilterParam.setValue(include);
    }

    /**
     * This gets the mag-dist filter function (distance on x-axis and mag on
     * y-axis), returning null if the includeMagDistFilterParam has been set to
     * false.
     */
    public ArbitrarilyDiscretizedFunc getMagDistCutoffFunc()
            throws java.rmi.RemoteException {
        if (includeMagDistFilterParam.getValue())
            return magDistCutoffParam.getValue();
        else
            return null;
    }

    /**
     * This returns the annualized-rate function for the hazard curve and
     * duration passed in.
     * 
     * @param hazFunction
     *            Discretized Hazard Function
     * @return DiscretizedFuncAPI Annualized Rate Curve
     */
    public DiscretizedFuncAPI getAnnualizedRates(
            DiscretizedFuncAPI hazFunction, double years)
            throws java.rmi.RemoteException {
        DiscretizedFuncAPI annualizedRateFunc = hazFunction.deepClone();
        int size = annualizedRateFunc.getNum();
        for (int i = 0; i < size; ++i) {
            annualizedRateFunc.set(i, -Math.log(1 - annualizedRateFunc.getY(i))
                    / years);
        }
        return annualizedRateFunc;
    }

    /**
     * This function computes a hazard curve for the given Site, IMR, ERF, and
     * discretized function, where the latter supplies the x-axis values (the
     * IMLs) for the computation, and the result (probability) is placed in the
     * y-axis values of this function. This always applies a source and rupture
     * distance cutoff using the value of the maxDistanceParam parameter (set to
     * a very high value if you don't want this). It also applies a
     * magnitude-dependent distance cutoff on the sources if the value of
     * includeMagDistFilterParam is "true" and using the function in
     * magDistCutoffParam.
     * 
     * @param hazFunction
     *            : This function is where the hazard curve is placed
     * @param site
     *            : site object
     * @param imr
     *            : selected IMR object
     * @param eqkRupForecast
     *            : selected Earthquake rup forecast
     * @return
     */
    public DiscretizedFuncAPI getHazardCurve(DiscretizedFuncAPI hazFunction,
            Site site, ScalarIntensityMeasureRelationshipAPI imr,
            EqkRupForecastAPI eqkRupForecast) throws java.rmi.RemoteException {

        // make hashtable with single IMR (so we can use the other method)
        Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap =
                new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
        imrMap.put(TectonicRegionType.ACTIVE_SHALLOW, imr); // The type of
                                                            // tectonic region
                                                            // here is of no
                                                            // consequence (it
                                                            // just a dummy
                                                            // value)
        return getHazardCurve(hazFunction, site, imrMap, eqkRupForecast);
    }

    /**
     * This function computes a hazard curve for the given Site, imrMap, ERF,
     * and discretized function, where the latter supplies the x-axis values
     * (the IMLs) for the computation, and the result (probability) is placed in
     * the y-axis values of this function. This always applies a source and
     * rupture distance cutoff using the value of the maxDistanceParam parameter
     * (set to a very high value if you don't want this). It also applies a
     * magnitude-dependent distance cutoff on the sources if the value of
     * includeMagDistFilterParam is "true" and using the function in
     * magDistCutoffParam.
     * 
     * @param hazFunction
     *            : This function is where the hazard curve is placed
     * @param site
     *            : site object
     * @param imrMap
     *            : this Hashtable<TectonicRegionType,
     *            ScalarIntensityMeasureRelationshipAPI> specifies which IMR to
     *            use with each tectonic region. If only one exists in the
     *            Hashtable then the associated TectonicRegionType is ignored
     *            and this IRM is used with all sources. If multiple IMRs exist,
     *            then we set the TectonicRegionTypeParameter in the IMR to the
     *            associated value in case the IMR supports multiple
     *            TectonicRegionTypes. If the IMR does not support the assigned
     *            TectonicRegionType (which is allowed for flexibility) then we
     *            set the TectonicRegionTypeParameter to it's default value
     *            (since it may support more than one other type).
     * @param eqkRupForecast
     *            : selected Earthquake rup forecast
     * @return
     */
    public
            DiscretizedFuncAPI
            getHazardCurve(
                    DiscretizedFuncAPI hazFunction,
                    Site site,
                    Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap,
                    EqkRupForecastAPI eqkRupForecast)
                    throws java.rmi.RemoteException {

        // System.out.println("Haz Curv Calc: maxDistanceParam.getValue()="+maxDistanceParam.getValue().toString());
        // System.out.println("Haz Curv Calc: numStochEventSetRealizationsParam.getValue()="+numStochEventSetRealizationsParam.getValue().toString());
        // System.out.println("Haz Curv Calc: includeMagDistFilterParam.getValue()="+includeMagDistFilterParam.getValue().toString());
        if (includeMagDistFilterParam.getValue())
            System.out.println("Haz Curv Calc: magDistCutoffParam.getValue()="
                    + magDistCutoffParam.getValue().toString());

        this.currRuptures = -1;

        /*
         * this determines how the calucations are done (doing it the way it's
         * outlined in our original SRL paper gives probs greater than 1 if the
         * total rate of events for the source exceeds 1.0, even if the rates of
         * individual ruptures are << 1).
         */
        boolean poissonSource = false;

        ArbitrarilyDiscretizedFunc condProbFunc =
                (ArbitrarilyDiscretizedFunc) hazFunction.deepClone();
        ArbitrarilyDiscretizedFunc sourceHazFunc =
                (ArbitrarilyDiscretizedFunc) hazFunction.deepClone();

        // declare some varibles used in the calculation
        double qkProb, distance;
        int k;

        // get the number of points
        int numPoints = hazFunction.getNum();

        // define distance filtering stuff
        double maxDistance = maxDistanceParam.getValue();
        boolean includeMagDistFilter = includeMagDistFilterParam.getValue();
        double magThresh = 0.0;

        // initialize IMRs w/ max distance, site, and reset parameter listeners
        // (the latter allows server versions to listen to parameter changes)
        for (ScalarIntensityMeasureRelationshipAPI imr : imrMap.values()) {
            imr.resetParameterEventListeners();
            imr.setUserMaxDistance(maxDistance);
            imr.setSite(site);
        }

        // get total number of sources
        numSources = eqkRupForecast.getNumSources();
        // System.out.println("Number of Sources: "+numSources);
        // System.out.println("ERF info: "+
        // eqkRupForecast.getClass().getName());

        // compute the total number of ruptures for updating the progress bar
        totRuptures = 0;
        sourceIndex = 0;
        // for(sourceIndex=0;sourceIndex<numSources;++sourceIndex)
        // totRuptures+=eqkRupForecast.getSource(sourceIndex).getNumRuptures();
        // System.out.println("Total number of ruptures:"+ totRuptures);

        // init the current rupture number (also for progress bar)
        currRuptures = 0;
        int numRupRejected = 0;

        // initialize the hazard function to 1.0
        initDiscretizeValues(hazFunction, 1.0);

        // this boolean will tell us whether a source was actually used
        // (e.g., all sources could be outside MAX_DISTANCE, leading to
        // numerical problems)
        boolean sourceUsed = false;

        if (D)
            System.out.println(C + ": starting hazard curve calculation");

        // loop over sources
        for (sourceIndex = 0; sourceIndex < numSources; sourceIndex++) {

            // get the ith source
            ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);

            // set the IMR according to the tectonic region of the source (if
            // there is more than one)
            TectonicRegionType trt = source.getTectonicRegionType();
            ScalarIntensityMeasureRelationshipAPI imr =
                    TRTUtils.getIMRForTRT(imrMap, trt);

            // compute the source's distance from the site and skip if it's too
            // far away
            distance = source.getMinDistance(site);

            // apply distance cutoff to source
            if (distance > maxDistance) {
                currRuptures += source.getNumRuptures(); // update progress bar
                                                         // for skipped ruptures
                continue;
            }

            // get magThreshold if we're to use the mag-dist cutoff filter
            if (includeMagDistFilter) {
                magThresh =
                        magDistCutoffParam.getValue()
                                .getInterpolatedY(distance);
            }

            // determine whether it's poissonian (calcs depend on this)
            poissonSource = source.isSourcePoissonian();

            // initialize the source hazard function to 0.0 if it's a
            // non-poisson source
            if (!poissonSource)
                initDiscretizeValues(sourceHazFunc, 0.0);

            // get the number of ruptures for the current source
            int numRuptures = source.getNumRuptures();

            // loop over these ruptures
            for (int n = 0; n < numRuptures; n++, ++currRuptures) {

                EqkRupture rupture = source.getRupture(n);

                // -------------------------------------------------------------------------
                // MD 2010.03.22
                // compute the rupture's distance from the site and skip if it's
                // too far away

                double jbDist = getJBdist(rupture, site);

                // apply distance cutoff to source
                if (jbDist > maxDistance) {
                    currRuptures += source.getNumRuptures(); // update progress
                                                             // bar for skipped
                                                             // ruptures
                    continue;
                }

                // get magThreshold if we're to use the mag-dist cutoff filter
                if (includeMagDistFilter) {
                    magThresh =
                            magDistCutoffParam.getValue().getInterpolatedY(
                                    jbDist);
                }
                // -------------------------------------------------------------------------
                // MD 2010.03.22

                // get the rupture probability
                qkProb = ((ProbEqkRupture) rupture).getProbability();

                // apply magThreshold if we're to use the mag-dist cutoff filter
                if (includeMagDistFilter && rupture.getMag() < magThresh) {
                    numRupRejected += 1;
                    continue;
                }

                // indicate that a source has been used (put here because of
                // above filter)
                sourceUsed = true;

                // set the EqkRup in the IMR
                imr.setEqkRupture(rupture);

                // get the conditional probability of exceedance from the IMR
                condProbFunc =
                        (ArbitrarilyDiscretizedFunc) imr
                                .getExceedProbabilities(condProbFunc);

                // For poisson source
                if (poissonSource) {
                    /*
                     * First make sure the probability isn't 1.0 (or too close);
                     * otherwise rates are infinite and all IMLs will be
                     * exceeded (because of ergodic assumption). This can happen
                     * if the number of expected events (over the timespan)
                     * exceeds ~37, because at this point 1.0-Math.exp(-num) =
                     * 1.0 by numerical precision (and thus, an infinite number
                     * of events). The number 30 used in the check below
                     * provides a safe margin.
                     */
                    if (Math.log(1.0 - qkProb) < -30.0)
                        throw new RuntimeException(
                                "Error: The probability for this ProbEqkRupture ("
                                        + qkProb
                                        + ") is too high for a Possion source (~infinite number of events) "
                                        + source.getName() + " idx: "
                                        + sourceIndex);

                    for (k = 0; k < numPoints; k++)
                        hazFunction.set(
                                k,
                                hazFunction.getY(k)
                                        * Math.pow(1 - qkProb,
                                                condProbFunc.getY(k)));
                }
                // For non-Poissin source
                else
                    for (k = 0; k < numPoints; k++)
                        sourceHazFunc.set(k, sourceHazFunc.getY(k) + qkProb
                                * condProbFunc.getY(k));
            }
            // for non-poisson source:
            if (!poissonSource)
                for (k = 0; k < numPoints; k++)
                    hazFunction.set(k,
                            hazFunction.getY(k) * (1 - sourceHazFunc.getY(k)));
        }

        int i;
        // finalize the hazard function
        if (sourceUsed)
            for (i = 0; i < numPoints; ++i)
                hazFunction.set(i, 1 - hazFunction.getY(i));
        else
            this.initDiscretizeValues(hazFunction, 0.0);

        if (D)
            System.out.println(C + "hazFunction.toString"
                    + hazFunction.toString());

        // System.out.println("numRupRejected="+numRupRejected);

        return hazFunction;
    }

    /**
     * This function computes an average hazard curve from a number of
     * stochastic event sets for the given Site, IMR, eqkRupForecast, where the
     * number of event-set realizations is specified as the value in
     * numStochEventSetRealizationsParam. The passed in discretized function
     * supplies the x-axis values (the IMLs) for the computation, and the result
     * (probability) is placed in the y-axis values of this function. This
     * always applies a rupture distance cutoff using the value of the
     * maxDistanceParam parameter (set to a very high value if you don't want
     * this). This does not (yet?) apply the magnitude-dependent distance cutoff
     * represented by includeMagDistFilterParam and magDistCutoffParam.
     * 
     * @param hazFunction
     *            : This function is where the hazard curve is placed
     * @param site
     *            : site object
     * @param imr
     *            : selected IMR object
     * @param eqkRupForecast
     *            : selected Earthquake rup forecast
     * @return
     */
    public DiscretizedFuncAPI getAverageEventSetHazardCurve(
            DiscretizedFuncAPI hazFunction, Site site,
            ScalarIntensityMeasureRelationshipAPI imr,
            EqkRupForecastAPI eqkRupForecast) throws java.rmi.RemoteException {

        System.out.println("Haz Curv Calc: maxDistanceParam.getValue()="
                + maxDistanceParam.getValue().toString());
        System.out
                .println("Haz Curv Calc: numStochEventSetRealizationsParam.getValue()="
                        + numStochEventSetRealizationsParam.getValue()
                                .toString());
        System.out
                .println("Haz Curv Calc: includeMagDistFilterParam.getValue()="
                        + includeMagDistFilterParam.getValue().toString());
        if (includeMagDistFilterParam.getValue())
            System.out.println("Haz Curv Calc: magDistCutoffParam.getValue()="
                    + magDistCutoffParam.getValue().toString());

        int numEventSets = numStochEventSetRealizationsParam.getValue();
        DiscretizedFuncAPI hazCurve;
        hazCurve = hazFunction.deepClone();
        initDiscretizeValues(hazFunction, 0);
        int numPts = hazCurve.getNum();
        // for progress bar
        currRuptures = 0;
        // totRuptures=numEventSets;

        for (int i = 0; i < numEventSets; i++) {
            ArrayList<EqkRupture> events = eqkRupForecast.drawRandomEventSet();
            if (i == 0)
                totRuptures = events.size() * numEventSets; // this is an
                                                            // approximate total
                                                            // number of events
            currRuptures += events.size();
            getEventSetHazardCurve(hazCurve, site, imr, events, false);
            for (int x = 0; x < numPts; x++)
                hazFunction.set(x, hazFunction.getY(x) + hazCurve.getY(x));
        }
        for (int x = 0; x < numPts; x++)
            hazFunction.set(x, hazFunction.getY(x) / numEventSets);
        return hazFunction;
    }

    /**
     * This function computes a hazard curve for the given Site, IMR, and event
     * set (eqkRupList), where it is assumed that each of the events occur
     * (probability of each is 1.0). The passed in discretized function supplies
     * the x-axis values (the IMLs) for the computation, and the result
     * (probability) is placed in the y-axis values of this function. This
     * always applies a rupture distance cutoff using the value of the
     * maxDistanceParam parameter (set to a very high value if you don't want
     * this). This does not (yet?) apply the magnitude-dependent distance cutoff
     * represented by includeMagDistFilterParam and magDistCutoffParam.
     * 
     * @param hazFunction
     *            : This function is where the hazard curve is placed
     * @param site
     *            : site object
     * @param imr
     *            : selected IMR object
     * @param eqkRupForecast
     *            : selected Earthquake rup forecast
     * @param updateCurrRuptures
     *            : tells whether to update current ruptures (for the
     *            getCurrRuptures() method used for progress bars)
     * @return
     */
    public DiscretizedFuncAPI getEventSetHazardCurve(
            DiscretizedFuncAPI hazFunction, Site site,
            ScalarIntensityMeasureRelationshipAPI imr,
            ArrayList<EqkRupture> eqkRupList, boolean updateCurrRuptures)
            throws java.rmi.RemoteException {

        ArbitrarilyDiscretizedFunc condProbFunc =
                (ArbitrarilyDiscretizedFunc) hazFunction.deepClone();

        // resetting the Parameter change Listeners on the
        // AttenuationRelationship
        // parameters. This allows the Server version of our application to
        // listen to the
        // parameter changes.
        ((AttenuationRelationship) imr).resetParameterEventListeners();

        // declare some varibles used in the calculation
        double distance;
        int k;

        // get the number of points
        int numPoints = hazFunction.getNum();

        // define distance filtering stuff
        double maxDistance = maxDistanceParam.getValue();
        boolean includeMagDistFilter = includeMagDistFilterParam.getValue();

        // set the maximum distance in the attenuation relationship
        imr.setUserMaxDistance(maxDistance);

        int totRups = eqkRupList.size();
        // progress bar stuff
        if (updateCurrRuptures) {
            totRuptures = totRups;
            currRuptures = 0;
        }

        int numRupRejected = 0;

        // initialize the hazard function to 1.0 (initial total non-exceedance
        // probability)
        initDiscretizeValues(hazFunction, 1.0);

        // set the Site in IMR
        imr.setSite(site);

        if (D)
            System.out.println(C + ": starting hazard curve calculation");

        // System.out.println("totRuptures="+totRuptures);

        // loop over ruptures
        for (int n = 0; n < totRups; n++) {

            if (updateCurrRuptures)
                ++currRuptures;

            EqkRupture rupture = eqkRupList.get(n);

            /*
             * // apply mag-dist cutoff filter if(includeMagDistFilter) {
             * //distance=??; // NEED TO COMPUTE THIS DISTANCE
             * if(rupture.getMag() <
             * magDistCutoffParam.getValue().getInterpolatedY(distance) {
             * numRupRejected += 1; continue; }
             */

            // set the EqkRup in the IMR
            imr.setEqkRupture(rupture);

            // get the conditional probability of exceedance from the IMR
            condProbFunc =
                    (ArbitrarilyDiscretizedFunc) imr
                            .getExceedProbabilities(condProbFunc);

            // multiply this into the total non-exceedance probability
            // (get the product of all non-eceedance probabilities)
            for (k = 0; k < numPoints; k++)
                hazFunction.set(k,
                        hazFunction.getY(k) * (1.0 - condProbFunc.getY(k)));

        }

        // System.out.println(C+"hazFunction.toString"+hazFunction.toString());

        // now convert from total non-exceed prob to total exceed prob
        for (int i = 0; i < numPoints; ++i)
            hazFunction.set(i, 1.0 - hazFunction.getY(i));

        // System.out.println(C+"hazFunction.toString"+hazFunction.toString());

        // System.out.println("numRupRejected="+numRupRejected);

        return hazFunction;
    }

    /**
     * This computes the "deterministic" exceedance curve for the given Site,
     * IMR, and ProbEqkrupture (conditioned on the event actually occurring).
     * The hazFunction passed in provides the x-axis values (the IMLs) and the
     * result (probability) is placed in the y-axis values of this function.
     * 
     * @param hazFunction
     *            : This function is where the deterministic hazard curve is
     *            placed
     * @param site
     *            : site object
     * @param imr
     *            : selected IMR object
     * @param rupture
     *            : Single Earthquake Rupture
     * @return
     */
    public DiscretizedFuncAPI getHazardCurve(DiscretizedFuncAPI hazFunction,
            Site site, ScalarIntensityMeasureRelationshipAPI imr,
            EqkRupture rupture) throws java.rmi.RemoteException {

        System.out.println("Haz Curv Calc: maxDistanceParam.getValue()="
                + maxDistanceParam.getValue().toString());
        System.out
                .println("Haz Curv Calc: numStochEventSetRealizationsParam.getValue()="
                        + numStochEventSetRealizationsParam.getValue()
                                .toString());
        System.out
                .println("Haz Curv Calc: includeMagDistFilterParam.getValue()="
                        + includeMagDistFilterParam.getValue().toString());
        if (includeMagDistFilterParam.getValue())
            System.out.println("Haz Curv Calc: magDistCutoffParam.getValue()="
                    + magDistCutoffParam.getValue().toString());

        // resetting the Parameter change Listeners on the
        // AttenuationRelationship parameters,
        // allowing the Server version of our application to listen to the
        // parameter changes.
        ((AttenuationRelationship) imr).resetParameterEventListeners();

        // set the Site in IMR
        imr.setSite(site);

        if (D)
            System.out.println(C + ": starting hazard curve calculation");

        // set the EqkRup in the IMR
        imr.setEqkRupture(rupture);

        // get the conditional probability of exceedance from the IMR
        hazFunction =
                (ArbitrarilyDiscretizedFunc) imr
                        .getExceedProbabilities(hazFunction);

        if (D)
            System.out.println(C + "hazFunction.toString"
                    + hazFunction.toString());

        return hazFunction;
    }

    /**
     * 
     * @returns the current rupture being traversed
     * @throws java.rmi.RemoteException
     */
    public int getCurrRuptures() throws java.rmi.RemoteException {
        return this.currRuptures;
    }

    /**
     * 
     * @returns the total number of ruptures in the earthquake rupture forecast
     *          model
     * @throws java.rmi.RemoteException
     */
    public int getTotRuptures() throws java.rmi.RemoteException {
        return this.totRuptures;
    }

    /**
     * stops the Hazard Curve calculations.
     * 
     * @throws java.rmi.RemoteException
     */
    public void stopCalc() throws java.rmi.RemoteException {
        sourceIndex = numSources;
    }

    /**
     * Initialize the prob as 1 for the Hazard function
     * 
     * @param arb
     */
    protected void initDiscretizeValues(DiscretizedFuncAPI arb, double val) {
        int num = arb.getNum();
        for (int i = 0; i < num; ++i)
            arb.set(i, val);
    }

    /**
     * 
     * @returns the adjustable ParameterList
     */
    public ParameterList getAdjustableParams() throws java.rmi.RemoteException {
        return this.adjustableParams;
    }

    /**
     * 
     * @returns This was created so new instances of this calculator could be
     *          given pointers to a set of parameter that already exist.
     */
    public void setAdjustableParams(ParameterList paramList)
            throws java.rmi.RemoteException {
        this.adjustableParams = paramList;
        this.maxDistanceParam =
                (DoubleParameter) paramList
                        .getParameter(this.MAX_DISTANCE_PARAM_NAME);
        this.numStochEventSetRealizationsParam =
                (IntegerParameter) paramList
                        .getParameter(NUM_STOCH_EVENT_SETS_PARAM_NAME);
        this.includeMagDistFilterParam =
                (BooleanParameter) paramList
                        .getParameter(INCLUDE_MAG_DIST_FILTER_PARAM_NAME);
        this.magDistCutoffParam =
                (ArbitrarilyDiscretizedFuncParameter) paramList
                        .getParameter(MAG_DIST_CUTOFF_PARAM_NAME);
    }

    /**
     * get the adjustable parameters
     * 
     * @return
     */
    public ListIterator getAdjustableParamsIterator()
            throws java.rmi.RemoteException {
        return adjustableParams.getParametersIterator();
    }

    /**
     * This tests whether the average over many curves from getEventSetCurve
     * equals what is given by getHazardCurve.
     */
    // public void testEventSetHazardCurve(int numIterations) {
    // // set distance filter large since these are handled slightly differently
    // in each calc
    // maxDistanceParam.setValue(300);
    // // do not apply mag-dist fileter
    // includeMagDistFilterParam.setValue(false);
    // numStochEventSetRealizationsParam.setValue(numIterations);
    //
    // ScalarIntensityMeasureRelationshipAPI imr = new BJF_1997_AttenRel(this);
    // imr.setParamDefaults();
    // imr.setIntensityMeasure("PGA");
    //
    // Site site = new Site();
    // ListIterator it = imr.getSiteParamsIterator();
    // while(it.hasNext())
    // site.addParameter((ParameterAPI)it.next());
    // site.setLocation(new Location(34,-118));
    //
    // EqkRupForecast eqkRupForecast = new Frankel96_EqkRupForecast();
    // eqkRupForecast.updateForecast();
    //
    // ArbitrarilyDiscretizedFunc hazCurve = new ArbitrarilyDiscretizedFunc();
    // hazCurve.set(-3.,1); // log(0.001)
    // hazCurve.set(-2.,1);
    // hazCurve.set(-1.,1);
    // hazCurve.set(1.,1);
    // hazCurve.set(2.,1); // log(10)
    //
    // hazCurve.setName("Hazard Curve");
    //
    // try {
    // this.getHazardCurve(hazCurve, site, imr, eqkRupForecast);
    // } catch (RemoteException e) {
    // // TODO Auto-generated catch block
    // e.printStackTrace();
    // }
    //
    // System.out.println(hazCurve.toString());
    //
    // ArbitrarilyDiscretizedFunc aveCurve = hazCurve.deepClone();
    // try {
    // getAverageEventSetHazardCurve(aveCurve,site, imr,eqkRupForecast);
    // } catch (RemoteException e1) {
    // // TODO Auto-generated catch block
    // e1.printStackTrace();
    // }
    //
    // /*
    // this.initDiscretizeValues(aveCurve, 0.0);
    // ArbitrarilyDiscretizedFunc curve = hazCurve.deepClone();
    // for(int i=0; i<numIterations;i++) {
    // try {
    // getEventSetHazardCurve(curve, site, imr,
    // eqkRupForecast.drawRandomEventSet());
    // for(int x=0; x<curve.getNum();x++) aveCurve.set(x,
    // aveCurve.getY(x)+curve.getY(x));
    // } catch (RemoteException e) {
    // // TODO Auto-generated catch block
    // e.printStackTrace();
    // }
    // }
    // for(int x=0; x<curve.getNum();x++) aveCurve.set(x,
    // aveCurve.getY(x)/numIterations);
    // */
    //
    // aveCurve.setName("Ave from "+numIterations+" event sets");
    // System.out.println(aveCurve.toString());
    //
    // }

    // added this and the associated API implementation to instantiate
    // BJF_1997_AttenRel in the above
    public void parameterChangeWarning(ParameterChangeWarningEvent event) {
    };

    /*
	 * 
	 */
    private double getJBdist(EqkRupture rup, Site site) {
        EvenlyGriddedSurfaceAPI rupSurf = rup.getRuptureSurface();
        Location loc = site.getLocation();

        double minDis = 1e20;

        // Loop over the left side of the rupture
        for (int i = 0; i < rupSurf.getNumRows(); i++) {
            double dis =
                    LocationUtils.horzDistance(loc, rupSurf.getLocation(i, 0));
            if (minDis > dis)
                minDis = dis;
        }
        // Loop over the bottom side of the rupture
        for (int i = 0; i < rupSurf.getNumCols(); i++) {
            double dis =
                    LocationUtils.horzDistance(loc,
                            rupSurf.getLocation(rupSurf.getNumRows() - 1, i));
            if (minDis > dis)
                minDis = dis;
        }
        // Loop over the right side of the rupture
        for (int i = 0; i < rupSurf.getNumRows(); i++) {
            double dis =
                    LocationUtils.horzDistance(loc,
                            rupSurf.getLocation(i, rupSurf.getNumCols() - 1));
            if (minDis > dis)
                minDis = dis;
        }
        // Loop over the top side of the rupture
        for (int i = 0; i < rupSurf.getNumCols(); i++) {
            double dis =
                    LocationUtils.horzDistance(loc, rupSurf.getLocation(0, i));
            if (minDis > dis)
                minDis = dis;
        }
        return minDis;
    }

    // // this is temporary for testing purposes
    // public static void main(String[] args) {
    // HazardCurveCalculator calc;
    // try {
    // calc = new HazardCurveCalculator();
    // calc.testEventSetHazardCurve(1000);
    // } catch (RemoteException e) {
    // // TODO Auto-generated catch block
    // e.printStackTrace();
    // }
    //
    // /*
    // double temp1, temp2, temp3, temp4;
    // boolean OK;
    // for(double n=1; n<2;n += 0.02) {
    // temp1 = Math.pow(10,n);
    // temp2 = 1.0-Math.exp(-temp1);
    // temp3 = Math.log(1.0-temp2);
    // temp4 = (temp3+temp1)/temp1;
    // OK = temp1<=30;
    // System.out.println((float)n+"\t"+temp1+"\t"+temp2+"\t"+temp3+"\t"+temp4+"\t"+OK);
    // }
    // */
    // }
}
