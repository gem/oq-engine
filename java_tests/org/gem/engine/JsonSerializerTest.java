package org.gem.engine;

import static org.junit.Assert.assertTrue;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Properties;

import org.apache.commons.configuration.ConfigurationException;
import org.apache.commons.lang.StringUtils;
import org.gem.JsonSerializer;
import org.gem.ScalarIMRJsonAdapter;
import org.gem.engine.hazard.memcached.Cache;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
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
import org.opensha.sha.util.TectonicRegionType;

import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;

public class JsonSerializerTest {

    private ArrayList<GEMSourceData> sourceList;

    @Before
    public void setUp() {
        sourceList = new ArrayList<GEMSourceData>();
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
    public void gemSourceDataFromCacheTest() {
        GEMSourceData area = getAreaSource();
        GEMSourceData point = getPointSource();
        GEMSourceData fault = getFaultSource();
        GEMSourceData subduc = getSubductionSource();
        sourceList.add(area);
        sourceList.add(point);
        sourceList.add(fault);
        sourceList.add(subduc);
        String json = JsonSerializer.getJsonSourceList(sourceList);
        System.out.println("Json string: " + json);

        Cache cache = new Cache("localhost", 11211);
        cache.set("KEY", json);

        List<GEMSourceData> sourceListDeserialized =
                JsonSerializer.getSourceListFromCache(cache, "KEY");
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
        Cache cache = new Cache("localhost", 11211);
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

    @Test
    public void getConfigurationPropertiesFromCacheTest()
            throws ConfigurationException {

        CommandLineCalculator clc =
                new CommandLineCalculator("CalculatorConfig.properties");

        Cache cache = new Cache("localhost", 11211);

        // serialize configuration file
        JsonSerializer.serializeConfigurationFile(cache, "KEY",
                clc.getConfigurationProperties());
        // read configuration from cache
        Properties prop =
                JsonSerializer
                        .getConfigurationPropertiesFromCache(cache, "KEY");
        assertTrue(prop.equals(clc.getConfigurationProperties()));

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
}
