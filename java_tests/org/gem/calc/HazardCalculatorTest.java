package org.gem.calc;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.assertEquals;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;

import junit.framework.Assert;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.engine.hazard.redis.Cache;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagLengthRelationship;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultSource;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class HazardCalculatorTest {

    private static List<Site> siteList;
    private static EqkRupForecastAPI erf;
    private static Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap;
    private static List<Double> imlVals;
    private static double integrationDistance = 200.0;
    private static Random rn = new Random();
    private static Boolean correlationFlag = false;
    // for memcache tests:
    private static final int PORT = 6379;
    private static final String LOCALHOST = "localhost";
    private Cache cache;

    @Before
    public void setUp() throws IOException {
        setUpSites();
        setUpErf();
        setUpGmpeMap();
        setUpImlValues();
        try {
            setUpMemcache();
        } catch (IOException e) {
            tearDown();
            throw e;
        }
    }

    @After
    public void tearDown() {
        siteList = null;
        erf = null;
        gmpeMap = null;
        imlVals = null;
        if (cache != null) {
            cache.flush();
            cache = null;
        }
    }

    /**
     * Check that hazard curves stored in map are exactly those calculated from
     * the method getHazardCurve in {@link HazardCurveCalculator}
     * 
     * @throws Exception
     */
    @Test
    public void checkHazardCurves() throws Exception {
        Map<Site, DiscretizedFuncAPI> results =
                HazardCalculator.getHazardCurves(siteList, erf, gmpeMap,
                        imlVals, integrationDistance);
        HazardCurveCalculator hazCurveCal = null;
        DiscretizedFuncAPI hazCurve = new ArbitrarilyDiscretizedFunc();
        for (Double val : imlVals) {
            hazCurve.set(val, 1.0);
        }

        hazCurveCal = new HazardCurveCalculator();
        hazCurveCal.setMaxSourceDistance(integrationDistance);
        for (Site site : siteList) {
            hazCurveCal.getHazardCurve(hazCurve, site, gmpeMap, erf);
            assertTrue(hazCurve.equals(results.get(site)));
        }
    }

    /**
     * Test getHazardCurves when a null list of site is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getHazardCurvesNullSiteList() {
        ArrayList<Site> siteList = null;
        HazardCalculator.getHazardCurves(siteList, erf, gmpeMap, imlVals,
                integrationDistance);
    }

    /**
     * Test getHazardCurves when an empty list of site is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getHazardCurvesEmptySiteList() {
        ArrayList<Site> siteList = new ArrayList<Site>();
        HazardCalculator.getHazardCurves(siteList, erf, gmpeMap, imlVals,
                integrationDistance);
    }

    /**
     * Test getHazardCurves when a null earthquake rupture forecast is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getHazardCurvesNullErf() {
        EqkRupForecastAPI erf = null;
        HazardCalculator.getHazardCurves(siteList, erf, gmpeMap, imlVals,
                integrationDistance);
    }

    /**
     * Test getHazardCurves when a null gmpe map is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getHazardCurvesNullGmpeMap() {
        Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap =
                null;
        HazardCalculator.getHazardCurves(siteList, erf, gmpeMap, imlVals,
                integrationDistance);
    }

    /**
     * Test getHazardCurves when an empty gmpe map is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getHazardCurvesEmptyGmpeMap() {
        Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap =
                new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
        HazardCalculator.getHazardCurves(siteList, erf, gmpeMap, imlVals,
                integrationDistance);
    }

    /**
     * Test getHazardCurves when a null intensity measure levels array is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getHazardCurvesNullImlLevelsList() {
        List<Double> imlVals = null;
        HazardCalculator.getHazardCurves(siteList, erf, gmpeMap, imlVals,
                integrationDistance);
    }

    /**
     * Test getHazardCurves when an empty intensity measure levels array is
     * passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getHazardCurvesEmptyImlLevelsList() {
        List<Double> imlVals = new ArrayList<Double>();
        HazardCalculator.getHazardCurves(siteList, erf, gmpeMap, imlVals,
                integrationDistance);
    }

    /**
     * Test getGroundMotionFields when a null list of site is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getGroundMotionFieldsNullSiteList() {
        ArrayList<Site> siteList = null;
        HazardCalculator.getGroundMotionFields(siteList, erf, gmpeMap, rn,
                correlationFlag);
    }

    /**
     * Test getGroundMotionFields when an empty list of site is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getGroundMotionFieldsEmptySiteList() {
        ArrayList<Site> siteList = new ArrayList<Site>();
        HazardCalculator.getGroundMotionFields(siteList, erf, gmpeMap, rn,
                correlationFlag);
    }

    /**
     * Test getGroundMotionFields when a null earthquake rupture forecast is
     * passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getGroundMotionFieldsNullErf() {
        EqkRupForecastAPI erf = null;
        HazardCalculator.getGroundMotionFields(siteList, erf, gmpeMap, rn,
                correlationFlag);
    }

    /**
     * Test getGroundMotionFields when a null gmpe map is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getGroundMotionFieldsNullGmpeMap() {
        Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap =
                null;
        HazardCalculator.getGroundMotionFields(siteList, erf, gmpeMap, rn,
                correlationFlag);
    }

    /**
     * Test getGroundMotionFields when an empty gmpe map is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getGroundMotionFieldsEmptyGmpeMap() {
        Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap =
                new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
        HazardCalculator.getGroundMotionFields(siteList, erf, gmpeMap, rn,
                correlationFlag);
    }

    /**
     * Test getGroundMotionFields when null random number is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void getGroundMotionFieldsNullRandomNumberGenerator() {
        Random rn = null;
        HazardCalculator.getGroundMotionFields(siteList, erf, gmpeMap, rn,
                correlationFlag);
    }

    private Map<EqkRupture, Map<Site, Double>> createGroundMotionFields()
    {
        int maxTries = 111;
        Map<EqkRupture, Map<Site, Double>> groundMotionFields = null;
        while (maxTries > 0 && groundMotionFields == null
                || groundMotionFields.values().size() == 0) {
            --maxTries;
            // HazardCalculator does not return ground motion fields in more
            // than 50% of the runs. Is it possible that this
            // has to do with the random seed? (That is the parameter that
            // changes for each call.)
            groundMotionFields =
                    HazardCalculator.getGroundMotionFields(siteList, erf,
                            gmpeMap, rn, correlationFlag);

        }
        if (groundMotionFields == null
                || groundMotionFields.values().size() == 0) {
            Assert.fail("HazardCalculator did not return ground motion fields after "
                    + maxTries + " runs." + groundMotionFields.toString());

        }

        return groundMotionFields;
    }

    private String[] getRuptureIds(Map<EqkRupture, Map<Site, Double>> groundMotionFields)
    {
        String[] eqkRuptureIds = new String[groundMotionFields.values().size()];
        for (int i = 0; i < eqkRuptureIds.length; ++i) {
            eqkRuptureIds[i] = "eqkRupture_id_" + i;
        }

        return eqkRuptureIds;
    }

    private String[] getSiteIds(Map<EqkRupture, Map<Site, Double>> groundMotionFields)
    {
        Map<Site, Double> firstGmf =
                groundMotionFields.values().iterator().next();
        String[] siteIds = new String[firstGmf.size()];
        for (int i = 0; i < siteIds.length; ++i) {
            siteIds[i] = "site_id_" + i;
        }

        return siteIds;
    }

    @Test
    public void gmfToJsonTest() {
        Map<EqkRupture, Map<Site, Double>> groundMotionFields = createGroundMotionFields();
        String[] eqkRuptureIds = getRuptureIds(groundMotionFields);
        String[] siteIds = getSiteIds(groundMotionFields);

        String jsonString =
                HazardCalculator.gmfToJson("gmf_id", eqkRuptureIds, siteIds,
                        groundMotionFields);
        assertNotNull("jsonString is expected to not to be null", jsonString);
    }

    /**
     * Test that gmfToJson output is not locale-dependent
     */
    @Test
    public void gmfToJsonLocale() {
        Map<EqkRupture, Map<Site, Double>> groundMotionFields = createGroundMotionFields();
        String[] eqkRuptureIds = getRuptureIds(groundMotionFields);
        String[] siteIds = getSiteIds(groundMotionFields);

        String jsonString =
                HazardCalculator.gmfToJson("gmf_id", eqkRuptureIds, siteIds,
                        groundMotionFields);

        Locale currentDefault = Locale.getDefault();

        try {
            // test all locales
            for (Locale l : Locale.getAvailableLocales())
            {
                Locale.setDefault(l);

                String jsonStringL =
                        HazardCalculator.gmfToJson("gmf_id", eqkRuptureIds, siteIds,
                            groundMotionFields);

                assertEquals("gmfToJson is locale-independent for locale " + l.toString(), jsonString, jsonStringL);
            }
        }
        finally {
            Locale.setDefault(currentDefault);
        }
    }

    @Test
    public void gmfToMemcacheTest() {
        int maxTries = 111;
        Map<EqkRupture, Map<Site, Double>> groundMotionFields = null;
        while (maxTries > 0 && groundMotionFields == null
                || groundMotionFields.values().size() == 0) {
            --maxTries;
            // HazardCalculator does not return ground motion fields in more
            // than 50% of the runs. Is it possible that this
            // has to do with the random seed? (That is the parameter that
            // changes for each call.)
            groundMotionFields =
                    HazardCalculator.getGroundMotionFields(siteList, erf,
                            gmpeMap, rn, correlationFlag);

        }
        if (groundMotionFields == null
                || groundMotionFields.values().size() == 0) {
            Assert.fail("HazardCalculator did not return ground motion fields after "
                    + maxTries + " runs." + groundMotionFields.toString());

        }
        Map<Site, Double> firstGmf =
                groundMotionFields.values().iterator().next();
        String[] eqkRuptureIds = new String[groundMotionFields.values().size()];
        for (int i = 0; i < eqkRuptureIds.length; ++i) {
            eqkRuptureIds[i] = "eqkRupture_id_" + i;
        }
        String[] siteIds = new String[firstGmf.size()];
        for (int i = 0; i < siteIds.length; ++i) {
            siteIds[i] = "site_id_" + i;
        }
        String gmfsId = "gmfs_id";
        String memCacheKey = "memCache_key";
        // this is what we expect to find in memcache later
        String jsonFromGmf =
                HazardCalculator.gmfToJson("gmf_id", eqkRuptureIds, siteIds,
                        groundMotionFields);
        // converts the groundmotion fields to json and stores them in the cache
        HazardCalculator.gmfToMemcache(cache, memCacheKey, gmfsId,
                eqkRuptureIds, siteIds, groundMotionFields);
        String jsonFromMemcache = (String) cache.get(memCacheKey);
        assertNotNull("test gmfToMemcacheTest: no value returned from cache",
                jsonFromMemcache);
        assertTrue(jsonFromGmf.compareTo(jsonFromGmf) == 0);
    }

    /**
     * Set up list of sites
     */
    private static void setUpSites() {
        siteList = new ArrayList<Site>();
        LocationList border = new LocationList();
        border.add(new Location(35.0, 35.0));
        border.add(new Location(35.0, 38.0));
        border.add(new Location(38.0, 38.0));
        border.add(new Location(38.0, 35.0));
        Region reg = new Region(border, BorderType.MERCATOR_LINEAR);
        double spacing = 1.0;
        GriddedRegion griddedReg = new GriddedRegion(reg, spacing, null);
        for (Location loc : griddedReg.getNodeList()) {
            Site site = new Site(loc);
            site.addParameter(new DoubleParameter(Vs30_Param.NAME, 760.0));
            siteList.add(site);
        }
    }

    /**
     * Set up ERF
     */
    private void setUpErf() {
        erf = new EqkRupForecast() {

            @Override
            public String getName() {
                return new String(
                        "Earthquake rupture forecast for testing pourpose");
            }

            @Override
            public void updateForecast() {
            }

            @Override
            public ArrayList getSourceList() {
                ArrayList<ProbEqkSource> list = new ArrayList<ProbEqkSource>();
                list.add(getFloatingPoissonFaultSource());
                return list;
            }

            @Override
            public ProbEqkSource getSource(int iSource) {
                return getFloatingPoissonFaultSource();
            }

            @Override
            public int getNumSources() {
                return 1;
            }
        };
    }

    /**
     * Set up gmpe map
     */
    private void setUpGmpeMap() {
        gmpeMap =
                new Hashtable<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
        ParameterChangeWarningListener warningListener = null;
        BA_2008_AttenRel imr = new BA_2008_AttenRel(warningListener);
        imr.setParamDefaults();
        imr.getParameter(StdDevTypeParam.NAME).setValue(
                StdDevTypeParam.STD_DEV_TYPE_TOTAL);
        imr.getParameter(SigmaTruncTypeParam.NAME).setValue(
                SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED);
        imr.getParameter(SigmaTruncLevelParam.NAME).setValue(3.0);
        imr.setIntensityMeasure(PGA_Param.NAME);
        imr.getParameter(ComponentParam.NAME).setValue(
                ComponentParam.COMPONENT_GMRotI50);
        gmpeMap.put(TectonicRegionType.ACTIVE_SHALLOW, imr);
    }

    /**
     * Set up intensity measure levels
     */
    private void setUpImlValues() {
        imlVals = new ArrayList<Double>();
        imlVals.add(Math.log(0.005));
        imlVals.add(Math.log(0.007));
        imlVals.add(Math.log(0.0098));
        imlVals.add(Math.log(0.0137));
        imlVals.add(Math.log(0.0192));
        imlVals.add(Math.log(0.0269));
        imlVals.add(Math.log(0.0376));
        imlVals.add(Math.log(0.0527));
        imlVals.add(Math.log(0.0738));
        imlVals.add(Math.log(0.103));
        imlVals.add(Math.log(0.145));
        imlVals.add(Math.log(0.203));
        imlVals.add(Math.log(0.284));
        imlVals.add(Math.log(0.397));
        imlVals.add(Math.log(0.556));
        imlVals.add(Math.log(0.778));
        imlVals.add(Math.log(1.09));
    }

    /**
     * Set up the cache to access the same host/port.
     * 
     * @throws IOException
     */
    private void setUpMemcache() throws IOException {
        cache = new Cache(LOCALHOST, PORT);
    }

    /**
     * Defines fault source (data taken from Turkey model)
     * 
     * @return
     */
    private static FloatingPoissonFaultSource getFloatingPoissonFaultSource() {
        FaultTrace trace = new FaultTrace("trf41");
        trace.add(new Location(37.413314, 36.866757));
        trace.add(new Location(37.033241, 36.640297));
        trace.add(new Location(36.608673, 36.431566));
        trace.add(new Location(36.488077, 36.375783));
        trace.add(new Location(35.677685, 36.271872));
        double occurrenceRate = 0.017;
        double beta = 2.115;
        double mMin = 6.8;
        double mMax = 7.9;
        double mfdBinWidth = 0.1;
        int num = (int) ((mMax - mMin) / mfdBinWidth + 1);
        GutenbergRichterMagFreqDist mfd =
                new GutenbergRichterMagFreqDist(mMin, mMax, num);
        mfd.setAllButTotMoRate(mMin, mMax, occurrenceRate, beta / Math.log(10));
        double dip = 90.0;
        double rake = 0.0;
        double upperSeismogenicDepth = 0.0;
        double lowerSeismogenicDepth = 0.0;
        double gridSpacing = 1.0;
        StirlingGriddedSurface surf =
                new StirlingGriddedSurface(trace, dip, upperSeismogenicDepth,
                        lowerSeismogenicDepth, gridSpacing);
        FloatingPoissonFaultSource src =
                new FloatingPoissonFaultSource(mfd, surf,
                        new WC1994_MagLengthRelationship(), 0.0, 1.5, 1.0,
                        rake, 50.0, mMin, 1, 12.0);
        src.setTectonicRegionType(TectonicRegionType.ACTIVE_SHALLOW);
        return src;
    }
}
