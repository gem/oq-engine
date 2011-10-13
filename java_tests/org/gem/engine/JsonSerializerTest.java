package org.gem.engine;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.apache.commons.lang.StringUtils;
import org.gem.JsonSerializer;
import org.gem.ScalarIMRJsonAdapter;
import org.gem.engine.hazard.redis.Cache;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CY_2008_AttenRel;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.reflect.TypeToken;

public class JsonSerializerTest {

    private ArrayList<GEMSourceData> sourceList;
    private static final String TEST_CURVE_JSON_1 = "[0.0,1.0]";
    private static final String TEST_CURVE_JSON_2 = "[2.0,3.0]";

    @Before
    public void setUp() {
        sourceList = new ArrayList<GEMSourceData>();
    }

    @Test
    public void testHazardCurvesToJson() {
        List<String> expectedResults = new ArrayList<String>();
        expectedResults.add(TEST_CURVE_JSON_1);
        expectedResults.add(TEST_CURVE_JSON_2);

        Site site1, site2;
        site1 = new Site();
        site2 = new Site();

        Location loc1, loc2;
        loc1 = new Location(34.12, -118.3); // lat, lon
        loc2 = new Location(33.88, -118.16);

        site1.setLocation(loc1);
        site2.setLocation(loc2);

        Map<Site, DiscretizedFuncAPI> testMap =
                new HashMap<Site, DiscretizedFuncAPI>();
        testMap.put(site1, new TestCurve(0.0, 1.0));
        testMap.put(site2, new TestCurve(2.0, 3.0));

        // order matters
        List<Site> siteList = new ArrayList<Site>();
        siteList.add(site1);
        siteList.add(site2);

        List<String> actualResults =
                JsonSerializer.hazardCurvesToJson(testMap, siteList);

        assertEquals(expectedResults, actualResults);
    }

    /**
     * Returns false of the two lists don't match (taking into account order).
     * Returns false if the test loop is not entered.
     *
     * @param expected
     * @param actual
     * @return
     */
    private static boolean hazCurvesJsonResultsAreEqual(List<String> expected,
            List<String> actual) {
        boolean match = false;
        for (int i = 0; i < expected.size(); i++) {
            match = expected.get(i).equals(actual.get(i));
        }
        return match;
    }

    @Test
    public void testOrdinatesToJsonElement() {
        DiscretizedFuncAPI curve = new TestCurve(0.0, 1.0);
        Gson gson = new Gson();
        JsonElement json = JsonSerializer.ordinatesToJsonElement(curve, gson);
        assertEquals(TEST_CURVE_JSON_1, json.toString());
    }

    /**
     * validates area source serialization
     */
    @Test
    public void areaSourceSerializationTest() {
        GEMAreaSourceData area = getAreaSource();
        sourceList.add(area);
        String json = JsonSerializer.getJsonSourceList(sourceList);
        validateAreaSourceSerialization(area, json);
    }

    @Test
    public void pointSourceSerializationTest() {
        GEMPointSourceData point = getPointSource();
        sourceList.add(point);
        String json = JsonSerializer.getJsonSourceList(sourceList);
        validatePointSourceSerialization(point, json);

    }

    @Test
    public void faultSourceSerializationTest() {
        GEMFaultSourceData fault = getFaultSource();
        sourceList.add(fault);
        String json = JsonSerializer.getJsonSourceList(sourceList);
        validateFaultSourceSerialization(fault, json);
    }

    @Test
    public void subductionSourceSerializationTest() {
        GEMSubductionFaultSourceData subduc = getSubductionSource();
        sourceList.add(subduc);
        String json = JsonSerializer.getJsonSourceList(sourceList);
        validateSubdcutionSerialization(subduc, json);
    }

    @Test
    public void sourceDataFromCacheTest() {

        GEMSourceData area = getAreaSource();
        GEMSourceData point = getPointSource();
        GEMSourceData fault = getFaultSource();
        GEMSourceData subduc = getSubductionSource();
        sourceList.add(area);
        sourceList.add(point);
        sourceList.add(fault);
        sourceList.add(subduc);

        String json = JsonSerializer.getJsonSourceList(sourceList);
        Cache cache = new Cache("localhost", 6379);
        cache.set("KEY", json);

        List<GEMSourceData> sourceListDeserialized =
                JsonSerializer.getSourceListFromCache(cache, "KEY");

        compareSourceDataList(sourceListDeserialized);
    }

    private void compareSourceDataList(
            List<GEMSourceData> sourceListDeserialized) {
        for (int sourceIndex = 0; sourceIndex < sourceList.size(); sourceIndex++) {
            compareCommonParams(sourceListDeserialized, sourceIndex);
            if (sourceList.get(sourceIndex) instanceof GEMAreaSourceData) {
                GEMAreaSourceData srcOriginal =
                        (GEMAreaSourceData) sourceList.get(sourceIndex);
                GEMAreaSourceData srcDeserialized =
                        (GEMAreaSourceData) sourceListDeserialized
                                .get(sourceIndex);
                compareAreaSourceData(srcOriginal, srcDeserialized);
            } else if (sourceList.get(sourceIndex) instanceof GEMPointSourceData) {
                GEMPointSourceData srcOriginal =
                        (GEMPointSourceData) sourceList.get(sourceIndex);
                GEMPointSourceData srcDeserialized =
                        (GEMPointSourceData) sourceListDeserialized
                                .get(sourceIndex);
                comparePointSourceData(srcOriginal, srcDeserialized);
            } else if (sourceList.get(sourceIndex) instanceof GEMFaultSourceData) {
                GEMFaultSourceData srcOriginal =
                        (GEMFaultSourceData) sourceList.get(sourceIndex);
                GEMFaultSourceData srcDeserialized =
                        (GEMFaultSourceData) sourceListDeserialized
                                .get(sourceIndex);
                compareFaultSourceData(srcOriginal, srcDeserialized);
            } else if (sourceList.get(sourceIndex) instanceof GEMSubductionFaultSourceData) {
                GEMSubductionFaultSourceData srcOriginal =
                        (GEMSubductionFaultSourceData) sourceList
                                .get(sourceIndex);
                GEMSubductionFaultSourceData srcDeserialized =
                        (GEMSubductionFaultSourceData) sourceListDeserialized
                                .get(sourceIndex);
                compareSubductionFaultSourceData(srcOriginal, srcDeserialized);
            }

        }
    }

    private void compareCommonParams(
            List<GEMSourceData> sourceListDeserialized, int sourceIndex) {
        assertTrue(sourceList.get(sourceIndex).getID().equalsIgnoreCase(
                sourceListDeserialized.get(sourceIndex).getID()));
        assertTrue(sourceList.get(sourceIndex).getName().equalsIgnoreCase(
                sourceListDeserialized.get(sourceIndex).getName()));
        assertTrue(sourceList.get(sourceIndex).getTectReg().toString()
                .equalsIgnoreCase(
                        sourceListDeserialized.get(sourceIndex).getTectReg()
                                .toString()));
    }

    private void compareSubductionFaultSourceData(
            GEMSubductionFaultSourceData srcOriginal,
            GEMSubductionFaultSourceData srcDeserialized) {
        compareFaultTraces(srcOriginal.getTopTrace(), srcDeserialized
                .getTopTrace());
        compareFaultTraces(srcOriginal.getBottomTrace(), srcDeserialized
                .getBottomTrace());
        assertTrue(srcOriginal.getRake() == srcDeserialized.getRake());
        assertTrue(srcOriginal.getFloatRuptureFlag() == srcDeserialized
                .getFloatRuptureFlag());
        compareMagFreqDist(srcOriginal.getMfd(), srcDeserialized.getMfd());
    }

    private void compareFaultSourceData(GEMFaultSourceData srcOriginal,
            GEMFaultSourceData srcDeserialized) {
        FaultTrace ftOriginal = srcOriginal.getTrace();
        FaultTrace ftDeserialized = srcDeserialized.getTrace();
        compareFaultTraces(ftOriginal, ftDeserialized);
        assertTrue(srcOriginal.getDip() == srcDeserialized.getDip());
        assertTrue(srcOriginal.getRake() == srcDeserialized.getRake());
        assertTrue(srcOriginal.getSeismDepthLow() == srcDeserialized
                .getSeismDepthLow());
        assertTrue(srcOriginal.getSeismDepthUpp() == srcDeserialized
                .getSeismDepthUpp());
        assertTrue(srcOriginal.getFloatRuptureFlag() == srcDeserialized
                .getFloatRuptureFlag());
        compareMagFreqDist(srcOriginal.getMfd(), srcDeserialized.getMfd());
    }

    private void compareFaultTraces(FaultTrace ftOriginal,
            FaultTrace ftDeserialized) {
        assertTrue(ftOriginal.size() == ftDeserialized.size());
        for (int i = 0; i < ftOriginal.size(); i++) {
            assertTrue(ftOriginal.get(i).equals(ftDeserialized.get(i)));
        }
    }

    private void comparePointSourceData(GEMPointSourceData srcOriginal,
            GEMPointSourceData srcDeserialized) {
        assertTrue(srcOriginal.getHypoMagFreqDistAtLoc().getLocation().equals(
                srcDeserialized.getHypoMagFreqDistAtLoc().getLocation()));
        assertTrue(srcOriginal.getHypoMagFreqDistAtLoc().getNumMagFreqDists() == srcDeserialized
                .getHypoMagFreqDistAtLoc().getNumMagFreqDists());
        assertTrue(srcOriginal.getHypoMagFreqDistAtLoc().getNumFocalMechs() == srcDeserialized
                .getHypoMagFreqDistAtLoc().getNumFocalMechs());
        for (int i = 0; i < srcOriginal.getHypoMagFreqDistAtLoc()
                .getNumMagFreqDists(); i++) {
            compareMagFreqDist(srcOriginal.getHypoMagFreqDistAtLoc()
                    .getMagFreqDist(i), srcDeserialized
                    .getHypoMagFreqDistAtLoc().getMagFreqDist(i));
            compareFocalMechanisms(srcOriginal.getHypoMagFreqDistAtLoc()
                    .getFocalMech(i), srcDeserialized.getHypoMagFreqDistAtLoc()
                    .getFocalMech(i));
        }
        compareRupDepthVsMagFunction(srcOriginal.getAveRupTopVsMag(),
                srcDeserialized.getAveRupTopVsMag());
        assertTrue(srcOriginal.getAveHypoDepth() == srcDeserialized
                .getAveHypoDepth());
    }

    private void compareAreaSourceData(GEMAreaSourceData srcOriginal,
            GEMAreaSourceData srcDeserialized) {
        LocationList borderOriginal = srcOriginal.getRegion().getBorder();
        LocationList borderDeserialized =
                srcDeserialized.getRegion().getBorder();
        assertTrue(borderOriginal.size() == borderDeserialized.size());
        for (int i = 0; i < borderOriginal.size(); i++)
            assertTrue(borderOriginal.get(i).equals(borderDeserialized.get(i)));
        // indirect way to compare regions.
        assertEquals(srcOriginal.getArea(), srcDeserialized.getArea(), 0.0001);
        assertTrue(srcOriginal.getMagfreqDistFocMech().getNumMagFreqDists() == srcDeserialized
                .getMagfreqDistFocMech().getNumMagFreqDists());
        assertTrue(srcOriginal.getMagfreqDistFocMech().getNumFocalMechs() == srcDeserialized
                .getMagfreqDistFocMech().getNumFocalMechs());
        for (int i = 0; i < srcOriginal.getMagfreqDistFocMech()
                .getNumFocalMechs(); i++) {
            compareMagFreqDist(srcOriginal.getMagfreqDistFocMech()
                    .getMagFreqDistList()[i], srcDeserialized
                    .getMagfreqDistFocMech().getMagFreqDistList()[i]);
            compareFocalMechanisms(srcOriginal.getMagfreqDistFocMech()
                    .getFocalMech(i), srcDeserialized.getMagfreqDistFocMech()
                    .getFocalMech(i));
        }
        compareRupDepthVsMagFunction(srcOriginal.getAveRupTopVsMag(),
                srcDeserialized.getAveRupTopVsMag());
        assertTrue(srcOriginal.getAveHypoDepth() == srcDeserialized
                .getAveHypoDepth());
    }

    private void compareRupDepthVsMagFunction(
            ArbitrarilyDiscretizedFunc rupDepthVsMagOriginal,
            ArbitrarilyDiscretizedFunc rupDepthVsMagDeserialized) {
        assertTrue(rupDepthVsMagOriginal.getNum() == rupDepthVsMagDeserialized
                .getNum());
        for (int i = 0; i < rupDepthVsMagOriginal.getNum(); i++) {
            assertTrue(rupDepthVsMagOriginal.get(i).getX() == rupDepthVsMagDeserialized
                    .get(i).getX());
            assertTrue(rupDepthVsMagOriginal.get(i).getY() == rupDepthVsMagDeserialized
                    .get(i).getY());
        }
    }

    private void compareFocalMechanisms(FocalMechanism fmOriginal,
            FocalMechanism fmDeserialized) {
        assertTrue(fmOriginal.getStrike() == fmDeserialized.getStrike());
        assertTrue(fmOriginal.getDip() == fmDeserialized.getDip());
        assertTrue(fmOriginal.getRake() == fmDeserialized.getRake());
    }

    private void compareMagFreqDist(IncrementalMagFreqDist mfdOriginal,
            IncrementalMagFreqDist mfdDeserialized) {
        assertTrue(mfdOriginal.getNum() == mfdDeserialized.getNum());
        for (int j = 0; j < mfdOriginal.getNum(); j++) {
            assertTrue(mfdOriginal.get(j).getX() == mfdDeserialized.get(j)
                    .getX());
            assertTrue(mfdOriginal.get(j).getY() == mfdDeserialized.get(j)
                    .getY());
        }
    }

    @Test
    public void getGmpeMapFromCacheTest() {

        HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap =
                new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
        gmpeMap.put(TectonicRegionType.ACTIVE_SHALLOW, new BA_2008_AttenRel(
                null));
        gmpeMap.put(TectonicRegionType.STABLE_SHALLOW, new CY_2008_AttenRel(
                null));

        GsonBuilder gson = new GsonBuilder();
        gson.registerTypeAdapter(ScalarIntensityMeasureRelationshipAPI.class,
                new ScalarIMRJsonAdapter());
        Type hashType =
                new TypeToken<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>>() {
                }.getType();
        String json = gson.create().toJson(gmpeMap, hashType);
        Cache cache = new Cache("localhost", 6379);
        cache.set("KEY", json);

        HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMapDeserialized =
                JsonSerializer.getGmpeMapFromCache(cache, "KEY");

        HashMap<String, String> gmpeMapString = new HashMap<String, String>();
        for (TectonicRegionType trt : gmpeMap.keySet())
            gmpeMapString.put(trt.toString(), gmpeMap.get(trt).getClass()
                    .getCanonicalName());
        HashMap<String, String> gmpeMapDeserializedString =
                new HashMap<String, String>();
        for (TectonicRegionType trt : gmpeMapDeserialized.keySet())
            gmpeMapDeserializedString.put(trt.toString(), gmpeMapDeserialized
                    .get(trt).getClass().getCanonicalName());
        assertTrue(gmpeMapString.equals(gmpeMapDeserializedString));
    }

    private void validateSubdcutionSerialization(
            GEMSubductionFaultSourceData subduc, String json) {
        validateCommonParamsSerialization(subduc, json);
        validateGutenbergRichterSerialization(
                (GutenbergRichterMagFreqDist) subduc.getMfd(), json);
        validateTraceSerialization("topTrace", subduc.getTopTrace(), json);
        validateTraceSerialization("bottomTrace", subduc.getBottomTrace(), json);
        assertTrue(json.contains("\"rake\":" + subduc.getRake()));
        assertTrue(json.contains("\"floatRuptureFlag\":"
                + subduc.getFloatRuptureFlag()));
    }

    private void validateFaultSourceSerialization(GEMFaultSourceData fault,
            String json) {
        validateCommonParamsSerialization(fault, json);
        validateGutenbergRichterSerialization(
                (GutenbergRichterMagFreqDist) fault.getMfd(), json);
        validateTraceSerialization("trace", fault.getTrace(), json);
        assertTrue(json.contains("\"dip\":" + fault.getDip()));
        assertTrue(json.contains("\"rake\":" + fault.getRake()));
        assertTrue(json.contains("\"seismDepthLow\":"
                + fault.getSeismDepthLow()));
        assertTrue(json.contains("\"seismDepthUpp\":"
                + fault.getSeismDepthUpp()));
        assertTrue(json.contains("\"floatRuptureFlag\":"
                + fault.getFloatRuptureFlag()));
    }

    private void validatePointSourceSerialization(GEMPointSourceData point,
            String json) {
        validateCommonParamsSerialization(point, json);
        validateGutenbergRichterSerialization(
                (GutenbergRichterMagFreqDist) point.getHypoMagFreqDistAtLoc()
                        .getFirstMagFreqDist(), json);
        validateFocalMechanismSerialization(point.getHypoMagFreqDistAtLoc()
                .getFirstFocalMech(), json);
        validateLocationSerialization(point.getHypoMagFreqDistAtLoc()
                .getLocation(), json);
        validateAveRupTopVsMagSerialization(point.getAveRupTopVsMag(), json);
        validateHypocentralDepthSerialization(point.getAveHypoDepth(), json);
    }

    private void validateAreaSourceSerialization(GEMAreaSourceData area,
            String json) {
        validateCommonParamsSerialization(area, json);
        validateRegionSerialization(area.getRegion(), json);
        validateGutenbergRichterSerialization(
                (GutenbergRichterMagFreqDist) area.getMagfreqDistFocMech()
                        .getFirstMagFreqDist(), json);
        validateFocalMechanismSerialization(area.getMagfreqDistFocMech()
                .getFirstFocalMech(), json);
        validateAveRupTopVsMagSerialization(area.getAveRupTopVsMag(), json);
        validateHypocentralDepthSerialization(area.getAveHypoDepth(), json);
    }

    private void validateCommonParamsSerialization(GEMSourceData point,
            String json) {
        assertTrue(json.contains("\"id\":\"" + point.getID() + "\""));
        assertTrue(json.contains("\"name\":\"" + point.getName() + "\""));
        assertTrue(json.contains("\"tectReg\":\"" + point.getTectReg().name()
                + "\""));
    }

    private void validateRegionSerialization(Region reg, String json) {
        ArrayList<String> locations = new ArrayList<String>();
        for (Location loc : reg.getBorder())
            locations.add("{\"lat\":" + loc.getLatRad() + ",\"lon\":"
                    + loc.getLonRad() + ",\"depth\":" + loc.getDepth() + "}");
        String locationsString = StringUtils.join(locations, ",");
        assertTrue(json.contains("\"border\":[" + locationsString + "]"));
    }

    private void validateGutenbergRichterSerialization(
            GutenbergRichterMagFreqDist mfd, String json) {
        assertTrue(json.contains("\"minX\":" + mfd.getMinX() + ""));
        assertTrue(json.contains("\"maxX\":" + mfd.getMaxX() + ""));
        assertTrue(json.contains("\"num\":" + mfd.getNum() + ""));
        assertTrue(json.contains("\"bValue\":" + mfd.get_bValue() + ""));
        ArrayList<String> points = new ArrayList<String>();
        for (int i = 0; i < mfd.getNum(); i++)
            points.add(Double.toString(mfd.getY(i)));
        String pointsString = StringUtils.join(points, ",");
        pointsString = "\"points\":[" + pointsString + "]";
        assertTrue(json.contains(pointsString));
    }

    private void validateFocalMechanismSerialization(FocalMechanism fm,
            String json) {
        assertTrue(json.contains("\"strike\":" + fm.getStrike() + ",\"dip\":"
                + fm.getDip() + ",\"rake\":" + fm.getRake()));
    }

    private void validateAveRupTopVsMagSerialization(
            ArbitrarilyDiscretizedFunc aveRupTopVsMagFunc, String json) {
        ArrayList<String> aveRupTopVsMag = new ArrayList<String>();
        for (int i = 0; i < aveRupTopVsMagFunc.getNum(); i++) {
            aveRupTopVsMag.add("[" + aveRupTopVsMagFunc.getX(i) + ","
                    + aveRupTopVsMagFunc.getY(i) + "]");
        }
        String aveRupTopVsMagString = StringUtils.join(aveRupTopVsMag, ",");
        aveRupTopVsMagString =
                "\"aveRupTopVsMag\":[" + aveRupTopVsMagString + "]";
        assertTrue(json.contains(aveRupTopVsMagString));
    }

    private void validateHypocentralDepthSerialization(double aveHypoDepth,
            String json) {
        assertTrue(json.contains("\"aveHypoDepth\":" + aveHypoDepth));
    }

    private void validateTraceSerialization(String traceName, FaultTrace trace,
            String json) {
        ArrayList<String> traceCoords = new ArrayList<String>();
        for (int i = 0; i < trace.getNumLocations(); i++) {
            traceCoords.add("{" + "\"lat\":" + trace.get(i).getLatRad()
                    + ",\"lon\":" + trace.get(i).getLonRad() + ",\"depth\":"
                    + trace.get(i).getDepth() + "}");
        }
        String traceCoordsString = StringUtils.join(traceCoords, ",");
        traceCoordsString = "\"" + traceName + "\":[" + traceCoordsString + "]";
        assertTrue(json.contains(traceCoordsString));
    }

    private void validateLocationSerialization(Location loc, String json) {
        assertTrue(json.contains("\"location\":{" + "\"lat\":"
                + loc.getLatRad() + ",\"lon\":" + loc.getLonRad()
                + ",\"depth\":" + loc.getDepth() + "}"));
    }

    private GEMAreaSourceData getAreaSource() {
        // area source data
        String id = "src01";
        String name = "Quito";
        TectonicRegionType tectReg = TectonicRegionType.ACTIVE_SHALLOW;
        LocationList border = new LocationList();
        border.add(new Location(37.5, -122.5));
        border.add(new Location(37.5, -121.5));
        border.add(new Location(38.5, -121.5));
        border.add(new Location(38.5, -122.5));
        Region reg = new Region(border, BorderType.GREAT_CIRCLE);
        GutenbergRichterMagFreqDist magDist =
                new GutenbergRichterMagFreqDist(1.0, 0.5, 5.0, 6.0, 10);
        FocalMechanism focalMechanism = new FocalMechanism(0.0, 90.0, 0.0);
        MagFreqDistsForFocalMechs magfreqDistFocMech =
                new MagFreqDistsForFocalMechs(magDist, focalMechanism);
        ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                new ArbitrarilyDiscretizedFunc();
        aveRupTopVsMag.set(5.0, 4.0);
        aveRupTopVsMag.set(6.0, 2.0);
        aveRupTopVsMag.set(7.0, 0.0);
        double aveHypoDepth = 6.0;
        GEMAreaSourceData area =
                new GEMAreaSourceData(id, name, tectReg, reg,
                        magfreqDistFocMech, aveRupTopVsMag, aveHypoDepth);
        return area;
    }

    private GEMPointSourceData getPointSource() {
        String id = "src01";
        String name = "Point1";
        TectonicRegionType tectReg = TectonicRegionType.ACTIVE_SHALLOW;
        GutenbergRichterMagFreqDist magDist =
                new GutenbergRichterMagFreqDist(1.0, 0.5, 5.0, 6.0, 10);
        FocalMechanism focalMechanism = new FocalMechanism(0.0, 90.0, 0.0);
        Location loc = new Location(38.0, -122.0);
        HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc =
                new HypoMagFreqDistAtLoc(magDist, loc, focalMechanism);
        ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                new ArbitrarilyDiscretizedFunc();
        aveRupTopVsMag.set(5.0, 4.0);
        aveRupTopVsMag.set(6.0, 2.0);
        aveRupTopVsMag.set(7.0, 0.0);
        double aveHypoDepth = 6.0;
        GEMPointSourceData point =
                new GEMPointSourceData(id, name, tectReg, hypoMagFreqDistAtLoc,
                        aveRupTopVsMag, aveHypoDepth);
        return point;
    }

    private GEMFaultSourceData getFaultSource() {
        String id = "src01";
        String name = "Mount Diablo Thrust";
        TectonicRegionType tectReg = TectonicRegionType.ACTIVE_SHALLOW;
        GutenbergRichterMagFreqDist magDist =
                new GutenbergRichterMagFreqDist(1.0, 0.5, 5.0, 6.0, 10);
        FaultTrace trc = new FaultTrace(name);
        trc.add(new Location(37.73010, -121.82290));
        trc.add(new Location(37.87710, -122.03880));
        double dip = 38.0;
        double rake = 90.0;
        double seismDepthLow = 13.0;
        double seismDepthUp = 8.0;
        boolean floatRuptureFlag = false;
        GEMFaultSourceData fault =
                new GEMFaultSourceData(id, name, tectReg, magDist, trc, dip,
                        rake, seismDepthLow, seismDepthUp, floatRuptureFlag);
        return fault;
    }

    private GEMSubductionFaultSourceData getSubductionSource() {
        String id = "src01";
        String name = "Cascadia Megathrust";
        TectonicRegionType tectReg = TectonicRegionType.SUBDUCTION_INTERFACE;
        FaultTrace topTrc = new FaultTrace(name);
        topTrc.add(new Location(40.363, -124.704, 0.5493260E+01));
        topTrc.add(new Location(49.279, -127.605, 0.4761580E+01));
        FaultTrace bottomTrc = new FaultTrace(name);
        bottomTrc.add(new Location(40.347, -123.829, 0.2038490E+02));
        bottomTrc.add(new Location(49.687, -126.911, 0.2275770E+02));
        GutenbergRichterMagFreqDist magDist =
                new GutenbergRichterMagFreqDist(1.0, 0.5, 5.0, 6.0, 10);
        double rake = 0.0;
        Boolean floatRuptureFlag = true;
        GEMSubductionFaultSourceData subduc =
                new GEMSubductionFaultSourceData(id, name, tectReg, topTrc,
                        bottomTrc, rake, magDist, floatRuptureFlag);
        return subduc;
    }

    /**
     * Test implementation of Discretized FuncAPI. This is a partial
     * implementation including only what we need for tests.
     *
     * @author larsbutler
     *
     */
    static class TestCurve extends ArbitrarilyDiscretizedFunc {

        static final double[] X_VALS = { -5.2983174, 0.756122 };
        double[] y_vals = { 0.0, 1.0 };

        public TestCurve(double y0, double y1) {
            y_vals[0] = y0;
            y_vals[1] = y1;
        }

        @Override
        public Iterator<DataPoint2D> getPointsIterator() {
            return new Iterator<DataPoint2D>() {

                private int count = 0;

                @Override
                public boolean hasNext() {
                    return count < X_VALS.length;
                }

                @Override
                public DataPoint2D next() {
                    DataPoint2D point =
                            new DataPoint2D(X_VALS[count], y_vals[count]);
                    count++;
                    return point;
                }

                @Override
                public void remove() {
                    // TODO Auto-generated method stub

                }
            };
        }

    }
}
