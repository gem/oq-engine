package org.gem.calc;

import static org.junit.Assert.assertEquals;

import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.apache.commons.math.linear.RealMatrix;
import org.apache.commons.math.stat.correlation.Covariance;
import org.apache.commons.math.stat.correlation.PearsonsCorrelation;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

public class GroundMotionFieldCalculatorTest implements
        ParameterChangeWarningListener {

    private DiscretizedFuncAPI iml;
    private Site site;
    private List<Site> siteList;
    private ScalarIntensityMeasureRelationshipAPI imr;
    private EqkRupture rupture;

    double tolerance = 1e-2;
    long seed = 123456789;
    int numRealizations = 3000;

    @Before
    public void setUp() {
        setIml();
        setSite();
        setSiteList();
        setEqkRup();
    }

    @Test(expected = IllegalArgumentException.class)
    public void nullArrayOfSites() {

        ArrayList<Site> sites = null;

        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);

        Random rn = new Random();
        GroundMotionFieldCalculator.getStochasticGroundMotionField(imr,
                rupture, sites, rn);
    }

    @Test(expected = IllegalArgumentException.class)
    public void emptyArrayOfSites() {

        ArrayList<Site> sites = new ArrayList<Site>();

        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);

        Random rn = new Random();
        GroundMotionFieldCalculator.getStochasticGroundMotionField(imr,
                rupture, sites, rn);
    }

    @Test(expected = IllegalArgumentException.class)
    public void nullImr() {

        BA_2008_AttenRel attenRel = null;

        ArrayList<Site> sites = new ArrayList<Site>();
        sites.add(site);

        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);

        Random rn = new Random();
        GroundMotionFieldCalculator.getStochasticGroundMotionField(attenRel,
                rupture, sites, rn);

    }

    @Test(expected = IllegalArgumentException.class)
    public void nullEqkRupture() {

        EqkRupture rup = null;

        ArrayList<Site> sites = new ArrayList<Site>();
        sites.add(site);

        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);

        Random rn = new Random();
        GroundMotionFieldCalculator.getStochasticGroundMotionField(imr, rup,
                sites, rn);
    }

    @Test(expected = IllegalArgumentException.class)
    public void nullRandomNumberGenerator() {

        Random rn = null;

        ArrayList<Site> sites = new ArrayList<Site>();
        sites.add(site);

        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);

        GroundMotionFieldCalculator.getStochasticGroundMotionField(imr,
                rupture, sites, rn);
    }

    @Test
    public void compareHazCurvesForSingleEqkRuptureWithNoTruncation() {

        /**
         * This test compares hazard curves calculated with the classical
         * approach and by generating multiple ground motion fields. No
         * truncation is assumed for the GMPE.
         */
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 2.0;
        compareHazardCurveForSingleEarthquake(truncationType, truncationLevel);
    }

    @Test
    public void compareHazCurvesForSingleEqkRuptureWith2SidedTruncation() {

        /**
         * This test compares hazard curves calculated with the classical
         * approach and by generating multiple ground motion fields. No
         * truncation is assumed for the GMPE.
         */
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED;
        double truncationLevel = 2.0;
        compareHazardCurveForSingleEarthquake(truncationType, truncationLevel);
    }

    @Test
    public void compareHazCurvesForSingleEqkRuptureWith1SidedTruncation() {

        /**
         * This test compares hazard curves calculated with the classical
         * approach and by generating multiple ground motion fields. 1 sided
         * truncation is assumed for the GMPE.
         */
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED;
        double truncationLevel = 2.0;
        compareHazardCurveForSingleEarthquake(truncationType, truncationLevel);
    }

    @Test
    public void correlatedGroundMotion_JB2009() {

        /**
         * Compares correlation matrix derived by multiple ground motion field
         * realizations (each calculated using the
         * getStochasticGroundMotionField_JB2009 method and considering only
         * intra-event residuals and no vs30 clustering) with the theoretical
         * correlation matrix.
         */
        Random rn = new Random(seed);
        int numRealizations = 10000;// 50000;

        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);

        Boolean inter_event = false;
        Boolean vs30Cluster = false;
        double[][] observedGroundMotionFields =
                getGroundMotionFieldRealizations(rn, inter_event, vs30Cluster,
                        numRealizations);

        RealMatrix correlationMatrix =
                new PearsonsCorrelation(observedGroundMotionFields)
                        .getCorrelationMatrix();

        validateCorrelation(correlationMatrix);
    }

    private void validateCorrelation(RealMatrix correlationMatrix) {
        double period = (Double) imr.getParameter(PeriodParam.NAME).getValue();
        double correlationRange = Double.NaN;
        double distance = Double.NaN;
        double predictedCorrelation = Double.NaN;
        double observedCorrelation = Double.NaN;
        if (period < 1)
            correlationRange = 8.5 + 17.2 * period;
        else if (period >= 1)
            correlationRange = 22.0 + 3.7 * period;
        int index_i = 0;
        for (Site site_i : siteList) {
            int index_j = 0;
            for (Site site_j : siteList) {
                distance =
                        LocationUtils.horzDistance(site_i.getLocation(),
                                site_j.getLocation());
                predictedCorrelation =
                        Math.exp(-3 * (distance / correlationRange));
                observedCorrelation =
                        correlationMatrix.getEntry(index_i, index_j);
                String message =
                        "CORRELATION. Predicted: " + predictedCorrelation
                                + ", observed: " + observedCorrelation;
                assertEquals(message, predictedCorrelation,
                        observedCorrelation, tolerance);
                index_j = index_j + 1;
            }
            index_i = index_i + 1;
        }
    }

    @Test
    public void correlatedGroundMotion_JB2009_InterEvent() {

        /**
         * Compares covariance values, from covariance matrix derived by
         * multiple ground motion field realizations (each calculated using the
         * getStochasticGroundMotionField_JB2009 method and considering both
         * inter- and intra-event residuals and no vs30 clustering) with
         * covariance values obtained multiplying correlation values (obtained
         * from the same set of ground motion realizations) with total standard
         * deviations for the site of interest. That is validate the following
         * equality:
         * 
         * cov_ij = corr_ij * totalStd_i * totalStd_j,
         * 
         * cov_ij = covariance value between site i and j, corr_ij = correlation
         * value between site i and j, totalStd_i and totalStd_j are the total
         * standard deviations for sites i and j
         */
        Random rn = new Random(seed);
        int numRealizations = 10000;

        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);

        Boolean inter_event = true;
        Boolean vs30Cluster = false;
        double[][] observedGroundMotionFields =
                getGroundMotionFieldRealizations(rn, inter_event, vs30Cluster,
                        numRealizations);

        RealMatrix covarianceMatrix =
                new Covariance(observedGroundMotionFields)
                        .getCovarianceMatrix();
        RealMatrix correlationMatrix =
                new PearsonsCorrelation(observedGroundMotionFields)
                        .getCorrelationMatrix();

        validateCovariance(covarianceMatrix, correlationMatrix);
    }

    private void validateCovariance(RealMatrix covarianceMatrix,
            RealMatrix correlationMatrix) {
        imr.getParameter(StdDevTypeParam.NAME).setValue(
                StdDevTypeParam.STD_DEV_TYPE_TOTAL);
        double observedCovariance = Double.NaN;
        double expectedCovariance = Double.NaN;
        double totalStd_i = Double.NaN;
        double totalStd_j = Double.NaN;
        int index_i = 0;
        for (Site site_i : siteList) {
            imr.setSite(site_i);
            totalStd_i = imr.getStdDev();
            int index_j = 0;
            for (Site site_j : siteList) {
                imr.setSite(site_j);
                totalStd_j = imr.getStdDev();
                observedCovariance =
                        covarianceMatrix.getEntry(index_i, index_j);
                expectedCovariance =
                        correlationMatrix.getEntry(index_i, index_j)
                                * (totalStd_i) * (totalStd_j);
                String message =
                        "COVARIANCE. Expected: " + expectedCovariance
                                + ", observed: " + observedCovariance;
                assertEquals(message, observedCovariance, expectedCovariance,
                        tolerance);
                index_j = index_j + 1;
            }
            index_i = index_i + 1;
        }
    }

    @Test(expected = IllegalArgumentException.class)
    public void correlatedGroundMotion_JB2009_NullImr() {
        /**
         * Check the behaviour when a null imr is passed
         */
        Random rn = new Random(seed);
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);
        ScalarIntensityMeasureRelationshipAPI imr = null;
        Map<Site, Double> map =
                GroundMotionFieldCalculator
                        .getStochasticGroundMotionField_JB2009(imr, rupture,
                                siteList, rn, true, false);
    }

    @Test(expected = IllegalArgumentException.class)
    public void correlatedGroundMotion_JB2009_NullRupture() {
        /**
         * Check the behaviour when a null rupture is passed
         */
        Random rn = new Random(seed);
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);
        EqkRupture rupture = null;
        Map<Site, Double> map =
                GroundMotionFieldCalculator
                        .getStochasticGroundMotionField_JB2009(imr, rupture,
                                siteList, rn, true, false);
    }

    @Test(expected = IllegalArgumentException.class)
    public void correlatedGroundMotion_JB2009_NullListOfSites() {
        /**
         * Check the behaviour when a null list of sites is passed
         */
        Random rn = new Random(seed);
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);
        List<Site> siteList = null;
        Map<Site, Double> map =
                GroundMotionFieldCalculator
                        .getStochasticGroundMotionField_JB2009(imr, rupture,
                                siteList, rn, true, false);
    }

    @Test(expected = IllegalArgumentException.class)
    public void correlatedGroundMotion_JB2009_EmptyListOfSites() {
        /**
         * Check the behaviour when an empty list of sites is passed
         */
        Random rn = new Random(seed);
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);
        List<Site> siteList = new ArrayList<Site>();
        Map<Site, Double> map =
                GroundMotionFieldCalculator
                        .getStochasticGroundMotionField_JB2009(imr, rupture,
                                siteList, rn, true, false);
    }

    @Test(expected = IllegalArgumentException.class)
    public void correlatedGroundMotion_JB2009_NullRandomNumberGenerator() {
        /**
         * Check the behaviour when a null random number generator is passed
         */
        Random rn = null;
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);
        List<Site> siteList = new ArrayList<Site>();
        Map<Site, Double> map =
                GroundMotionFieldCalculator
                        .getStochasticGroundMotionField_JB2009(imr, rupture,
                                siteList, rn, true, false);
    }

    @Test(expected = IllegalArgumentException.class)
    public void correlatedGroundMotion_JB2009_NullInterEvent() {
        /**
         * Check the behaviour when a null flag for inter-event residuals is
         * passed
         */
        Random rn = new Random(seed);
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);
        List<Site> siteList = new ArrayList<Site>();
        Map<Site, Double> map =
                GroundMotionFieldCalculator
                        .getStochasticGroundMotionField_JB2009(imr, rupture,
                                siteList, rn, null, false);
    }

    @Test(expected = IllegalArgumentException.class)
    public void correlatedGroundMotion_JB2009_NullVs30() {
        /**
         * Check the behaviour when a null flag for Vs30 is passed
         */
        Random rn = new Random(seed);
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        setImr(truncationType, truncationLevel);
        List<Site> siteList = new ArrayList<Site>();
        Map<Site, Double> map =
                GroundMotionFieldCalculator
                        .getStochasticGroundMotionField_JB2009(imr, rupture,
                                siteList, rn, true, null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void correlatedGroundMotion_JB2009_NoInterEvent() {
        /**
         * Check the behaviour when an attenuation relationship without
         * inter-event standard deviation is passed
         */
        Random rn = new Random(seed);
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        ScalarIntensityMeasureRelationshipAPI imr = new AS_1997_AttenRel(this);
        imr.setParamDefaults();
        imr.getParameter(SigmaTruncTypeParam.NAME).setValue(truncationType);
        imr.getParameter(SigmaTruncLevelParam.NAME).setValue(truncationLevel);
        imr.setIntensityMeasure(PGA_Param.NAME);
        List<Site> siteList = new ArrayList<Site>();
        Map<Site, Double> map =
                GroundMotionFieldCalculator
                        .getStochasticGroundMotionField_JB2009(imr, rupture,
                                siteList, rn, true, false);
    }

    @Test(expected = IllegalArgumentException.class)
    public void correlatedGroundMotion_JB2009_NoItraEvent() {
        /**
         * Check the behaviour when an attenuation relationship without
         * intra-event standard deviation is passed
         */
        Random rn = new Random(seed);
        String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
        double truncationLevel = 1.0;
        ScalarIntensityMeasureRelationshipAPI imr = new AS_1997_AttenRel(this);
        imr.setParamDefaults();
        imr.getParameter(SigmaTruncTypeParam.NAME).setValue(truncationType);
        imr.getParameter(SigmaTruncLevelParam.NAME).setValue(truncationLevel);
        imr.setIntensityMeasure(PGA_Param.NAME);
        List<Site> siteList = new ArrayList<Site>();
        Map<Site, Double> map =
                GroundMotionFieldCalculator
                        .getStochasticGroundMotionField_JB2009(imr, rupture,
                                siteList, rn, false, false);
    }

    private double[][] getGroundMotionFieldRealizations(Random rn,
            Boolean inter_event, Boolean vs30Cluster, int numRealizations) {
        double[][] observedGroundMotionFields =
                new double[numRealizations][siteList.size()];
        Map<Site, Double> map = null;
        for (int i = 0; i < numRealizations; i++) {
            map =
                    GroundMotionFieldCalculator
                            .getStochasticGroundMotionField_JB2009(imr,
                                    rupture, siteList, rn, inter_event,
                                    vs30Cluster);
            int indexSite = 0;
            for (Site site : siteList) {
                observedGroundMotionFields[i][indexSite] = map.get(site);
                indexSite = indexSite + 1;
            }
        }
        return observedGroundMotionFields;
    }

    private void compareHazardCurveForSingleEarthquake(String truncationType,
            double truncationLevel) {

        setImr(truncationType, truncationLevel);

        // calculate hazard curve following classical approach
        try {
            HazardCurveCalculator hcc = new HazardCurveCalculator();
            hcc.getHazardCurve(iml, site, imr, rupture);
        } catch (RemoteException e) {
            e.printStackTrace();
        }

        // calculate hazard curve by generating multiple ground motion fields
        Random rn = new Random(seed);
        double[] probabilityOfExceedenceVals =
                getHazardCurveFromMultipleGroundMotionFields(numRealizations,
                        rn);

        for (int i = 0; i < iml.getNum(); i++) {
            double expected = iml.getY(i);
            double computed = probabilityOfExceedenceVals[i];
            System.out.println("Expected: " + expected + " " + ", computed: "
                    + computed);
            assertEquals(expected, computed, tolerance);
        }
    }

    private void setIml() {
        this.iml = new ArbitrarilyDiscretizedFunc();
        this.iml.set(Math.log(0.005), 1.0);
        this.iml.set(Math.log(0.007), 1.0);
        this.iml.set(Math.log(0.0098), 1.0);
        this.iml.set(Math.log(0.0137), 1.0);
        this.iml.set(Math.log(0.0192), 1.0);
        this.iml.set(Math.log(0.0269), 1.0);
        this.iml.set(Math.log(0.0376), 1.0);
        this.iml.set(Math.log(0.0527), 1.0);
        this.iml.set(Math.log(0.0738), 1.0);
        this.iml.set(Math.log(0.103), 1.0);
        this.iml.set(Math.log(0.145), 1.0);
        this.iml.set(Math.log(0.203), 1.0);
        this.iml.set(Math.log(0.284), 1.0);
        this.iml.set(Math.log(0.397), 1.0);
        this.iml.set(Math.log(0.556), 1.0);
        this.iml.set(Math.log(0.778), 1.0);
        this.iml.set(Math.log(1.09), 1.0);
    }

    private void setSite() {
        Site site = new Site(new Location(33.8, -117.4));
        site.addParameter(new DoubleParameter(Vs30_Param.NAME, 760.0));
        this.site = site;
    }

    private void setSiteList() {
        siteList = new ArrayList<Site>();
        double latMin = 33.5;
        double latMax = 33.5;
        double lonMin = -118.0;
        double lonMax = -117.8;
        double gridSpacing = 0.1;
        List<Site> sites = new ArrayList<Site>();
        int numLat = (int) ((latMax - latMin) / gridSpacing + 1);
        int numLon = (int) ((lonMax - lonMin) / gridSpacing + 1);
        for (int i = 0; i < numLat; i++) {
            for (int j = 0; j < numLon; j++) {
                Site site =
                        new Site(new Location(latMin + i * gridSpacing, lonMin
                                + j * gridSpacing));
                site.addParameter(new DoubleParameter(Vs30_Param.NAME, 760.0));
                siteList.add(site);
            }
        }
    }

    private void setImr(String truncationType, double truncationLevel) {
        this.imr = new BA_2008_AttenRel(this);
        this.imr.setParamDefaults();
        this.imr.getParameter(SigmaTruncTypeParam.NAME)
                .setValue(truncationType);
        this.imr.getParameter(SigmaTruncLevelParam.NAME).setValue(
                truncationLevel);
        this.imr.setIntensityMeasure(PGA_Param.NAME);
    }

    private void setEqkRup() {
        double avgDip = 90.0;
        double lowerSeisDepth = 13.0;
        double upperSeisDepth = 0.0;
        FaultTrace trace = new FaultTrace("Elsinore;GI");
        trace.add(new Location(33.82890, -117.59000));
        trace.add(new Location(33.81290, -117.54800));
        trace.add(new Location(33.74509, -117.46332));
        trace.add(new Location(33.73183, -117.44568));
        trace.add(new Location(33.71851, -117.42415));
        trace.add(new Location(33.70453, -117.40265));
        trace.add(new Location(33.68522, -117.37270));
        trace.add(new Location(33.62646, -117.27443));
        double gridSpacing = 1.0;
        double mag = 6.889;
        double avgRake = 0.0;
        Location hypo = new Location(33.73183, -117.44568, 6.5);
        this.rupture =
                getFiniteEqkRupture(avgDip, lowerSeisDepth, upperSeisDepth,
                        trace, gridSpacing, mag, hypo, avgRake);
    }

    private double[] getHazardCurveFromMultipleGroundMotionFields(
            int numRealizations, Random rn) {
        double[] probabilityOfExceedenceVals = new double[iml.getNum()];
        ArrayList<Site> sites = new ArrayList<Site>();
        sites.add(site);
        ArrayList<Double> groundMotionValues = new ArrayList<Double>();
        for (int i = 0; i < numRealizations; i++)
            groundMotionValues.add(GroundMotionFieldCalculator
                    .getStochasticGroundMotionField(imr, rupture, sites, rn)
                    .get(site));
        Comparator comparator = Collections.reverseOrder();
        Collections.sort(groundMotionValues, comparator);
        for (int i = 0; i < iml.getNum(); i++)
            probabilityOfExceedenceVals[i] = 0.0;
        Iterator<Double> iterGMV = iml.getXValuesIterator();
        int indexGMV = 0;
        while (iterGMV.hasNext()) {
            double groundMotionValue = iterGMV.next();
            for (int i = 0; i < groundMotionValues.size(); i++)
                if (groundMotionValues.get(i) > groundMotionValue)
                    probabilityOfExceedenceVals[indexGMV] =
                            probabilityOfExceedenceVals[indexGMV] + 1;
                else
                    break;
            indexGMV = indexGMV + 1;
        }
        for (int i = 0; i < iml.getNum(); i++)
            probabilityOfExceedenceVals[i] =
                    probabilityOfExceedenceVals[i] / numRealizations;
        return probabilityOfExceedenceVals;
    }

    /*
     * Creates an EqkRupture object for a finite source.
     */
    private EqkRupture getFiniteEqkRupture(double aveDip,
            double lowerSeisDepth, double upperSeisDepth,
            FaultTrace faultTrace, double gridSpacing, double mag,
            Location hypo, double aveRake) {
        StirlingGriddedSurface rupSurf =
                new StirlingGriddedSurface(faultTrace, aveDip, upperSeisDepth,
                        lowerSeisDepth, gridSpacing);
        EqkRupture rup = new EqkRupture(mag, aveRake, rupSurf, hypo);
        return rup;
    }

    @Override
    public void parameterChangeWarning(ParameterChangeWarningEvent event) {
    }

}
