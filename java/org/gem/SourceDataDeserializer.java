package org.gem;

import java.lang.reflect.Type;

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
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

import com.google.gson.JsonArray;
import com.google.gson.JsonDeserializationContext;
import com.google.gson.JsonDeserializer;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;

public class SourceDataDeserializer implements JsonDeserializer<GEMSourceData> {

    @Override
    public GEMSourceData deserialize(JsonElement arg0, Type arg1,
            JsonDeserializationContext arg2) throws JsonParseException {
        GEMSourceData sourceData = null;
        JsonObject obj = arg0.getAsJsonObject();
        // common data
        String id = obj.get("id").toString().replace("\"", "");
        String name = obj.get("name").toString().replace("\"", "");
        String trtName = obj.get("tectReg").toString().replace("\"", "");
        TectonicRegionType trt = getTectonicRegionType(trtName);

        if (obj.has("reg")) { // area source
            Region reg = getRegion(obj);
            MagFreqDistsForFocalMechs magfreqDistFocMech =
                    getMagFreqDistsForFocalMechs(obj);
            ArbitrarilyDiscretizedFunc aveRupTopVsMag = getAveRupTopVsMag(obj);
            double aveHypoDepth = obj.get("aveHypoDepth").getAsDouble();
            sourceData =
                    new GEMAreaSourceData(id, name, trt, reg,
                            magfreqDistFocMech, aveRupTopVsMag, aveHypoDepth);
        } else if (obj.has("hypoMagFreqDistAtLoc")) { // point source
            HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc =
                    getHypoMagFreqDistAtLoc(obj);
            ArbitrarilyDiscretizedFunc aveRupTopVsMag = getAveRupTopVsMag(obj);
            double aveHypoDepth = obj.get("aveHypoDepth").getAsDouble();
            sourceData =
                    new GEMPointSourceData(id, name, trt, hypoMagFreqDistAtLoc,
                            aveRupTopVsMag, aveHypoDepth);
        }
        if (obj.has("trace")) { // fault source
            JsonArray faultTrace = obj.get("trace").getAsJsonArray();
            FaultTrace trace = getFaultTrace(faultTrace);
            double dip = obj.get("dip").getAsDouble();
            double rake = obj.get("rake").getAsDouble();
            double seismDepthLow = obj.get("seismDepthLow").getAsDouble();
            double seismDepthUpp = obj.get("seismDepthUpp").getAsDouble();
            IncrementalMagFreqDist mfd =
                    getMagFreqDist(obj.get("mfd").getAsJsonObject());
            Boolean floatRuptureFlag =
                    obj.get("floatRuptureFlag").getAsBoolean();
            sourceData =
                    new GEMFaultSourceData(id, name, trt, mfd, trace, dip,
                            rake, seismDepthLow, seismDepthUpp,
                            floatRuptureFlag);
        }
        if (obj.has("topTrace")) { // subduction source
            JsonArray faultTrace = obj.get("topTrace").getAsJsonArray();
            FaultTrace topTrace = getFaultTrace(faultTrace);
            faultTrace = obj.get("bottomTrace").getAsJsonArray();
            FaultTrace bottomTrace = getFaultTrace(faultTrace);
            double rake = obj.get("rake").getAsDouble();
            IncrementalMagFreqDist mfd =
                    getMagFreqDist(obj.get("mfd").getAsJsonObject());
            Boolean floatRuptureFlag =
                    obj.get("floatRuptureFlag").getAsBoolean();
            sourceData =
                    new GEMSubductionFaultSourceData(id, name, trt, topTrace,
                            bottomTrace, rake, mfd, floatRuptureFlag);
        }
        return sourceData;
    }

    private FaultTrace getFaultTrace(JsonArray faultTrace) {
        FaultTrace trace = new FaultTrace("");
        for (int i = 0; i < faultTrace.size(); i++) {
            Location loc =
                    new Location(faultTrace.get(i).getAsJsonObject().get("lat")
                            .getAsDouble()
                            * (180 / Math.PI), faultTrace.get(i)
                            .getAsJsonObject().get("lon").getAsDouble()
                            * (180 / Math.PI), faultTrace.get(i)
                            .getAsJsonObject().get("depth").getAsDouble());
            trace.add(loc);
        }
        return trace;
    }

    private HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(JsonObject obj) {
        HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc = null;
        JsonObject location =
                obj.get("hypoMagFreqDistAtLoc").getAsJsonObject()
                        .get("location").getAsJsonObject();
        Location loc =
                new Location(location.get("lat").getAsDouble(), location.get(
                        "lon").getAsDouble());
        JsonArray mfdArray =
                obj.get("hypoMagFreqDistAtLoc").getAsJsonObject()
                        .get("magFreqDist").getAsJsonArray();
        JsonArray fmArray =
                obj.get("hypoMagFreqDistAtLoc").getAsJsonObject()
                        .get("focalMechanism").getAsJsonArray();
        IncrementalMagFreqDist[] magFreqDistArray =
                new IncrementalMagFreqDist[mfdArray.size()];
        FocalMechanism[] focMechArray = new FocalMechanism[mfdArray.size()];
        for (int i = 0; i < mfdArray.size(); i++) {
            JsonObject mfd = mfdArray.get(i).getAsJsonObject();
            JsonObject fm = fmArray.get(i).getAsJsonObject();
            magFreqDistArray[i] = getMagFreqDist(mfd);
            focMechArray[i] = getFocalMechanism(fm);
        }
        hypoMagFreqDistAtLoc =
                new HypoMagFreqDistAtLoc(magFreqDistArray, loc, focMechArray);
        return hypoMagFreqDistAtLoc;
    }

    private ArbitrarilyDiscretizedFunc getAveRupTopVsMag(JsonObject obj) {
        ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                new ArbitrarilyDiscretizedFunc();
        JsonArray aveRupTopDepthVsMag =
                obj.get("aveRupTopVsMag").getAsJsonArray();
        for (int i = 0; i < aveRupTopDepthVsMag.size(); i++) {
            double x =
                    aveRupTopDepthVsMag.get(i).getAsJsonArray().get(0)
                            .getAsDouble();
            double y =
                    aveRupTopDepthVsMag.get(i).getAsJsonArray().get(1)
                            .getAsDouble();
            aveRupTopVsMag.set(x, y);
        }
        return aveRupTopVsMag;
    }

    private MagFreqDistsForFocalMechs getMagFreqDistsForFocalMechs(
            JsonObject obj) {
        JsonArray mfdList =
                obj.get("magfreqDistFocMech").getAsJsonObject()
                        .get("magFreqDist").getAsJsonArray();
        JsonArray fmList =
                obj.get("magfreqDistFocMech").getAsJsonObject()
                        .get("focalMechanism").getAsJsonArray();
        JsonObject mfd = null;
        JsonObject fm = null;
        IncrementalMagFreqDist[] mfdArray =
                new IncrementalMagFreqDist[mfdList.size()];
        FocalMechanism[] fmArray = new FocalMechanism[mfdList.size()];
        for (int i = 0; i < mfdList.size(); i++) {
            // magnitude frequency distribution
            mfd = mfdList.get(i).getAsJsonObject();
            IncrementalMagFreqDist magFreqDist = getMagFreqDist(mfd);
            mfdArray[i] = magFreqDist;
            // focal mechanism
            fm = fmList.get(i).getAsJsonObject();
            FocalMechanism focMech = getFocalMechanism(fm);
            fmArray[i] = focMech;
        }
        MagFreqDistsForFocalMechs magfreqDistFocMech =
                new MagFreqDistsForFocalMechs(mfdArray, fmArray);
        return magfreqDistFocMech;
    }

    private FocalMechanism getFocalMechanism(JsonObject fm) {
        double strike = fm.get("strike").getAsDouble();
        double dip = fm.get("dip").getAsDouble();
        double rake = fm.get("rake").getAsDouble();
        FocalMechanism focMech = new FocalMechanism(strike, dip, rake);
        return focMech;
    }

    private IncrementalMagFreqDist getMagFreqDist(JsonObject mfd) {
        double minX = mfd.get("minX").getAsDouble();
        double maxX = mfd.get("maxX").getAsDouble();
        int num = mfd.get("num").getAsInt();
        JsonArray mfdValues = mfd.get("points").getAsJsonArray();
        IncrementalMagFreqDist magFreqDist =
                new IncrementalMagFreqDist(minX, maxX, num);
        for (int j = 0; j < mfdValues.size(); j++) {
            magFreqDist.set(j, mfdValues.get(j).getAsDouble());
        }
        return magFreqDist;
    }

    private Region getRegion(JsonObject obj) {
        JsonArray border =
                obj.get("reg").getAsJsonObject().get("border").getAsJsonArray();
        LocationList borderLocs = new LocationList();
        for (int i = 0; i < border.size(); i++) {
            Location loc =
                    new Location(border.get(i).getAsJsonObject().get("lat")
                            .getAsDouble()
                            * (180 / Math.PI), border.get(i).getAsJsonObject()
                            .get("lon").getAsDouble()
                            * (180 / Math.PI));
            borderLocs.add(loc);
        }
        Region reg = new Region(borderLocs, BorderType.GREAT_CIRCLE);
        return reg;
    }

    private TectonicRegionType getTectonicRegionType(String trtName) {
        TectonicRegionType trt = null;
        if (trtName.equalsIgnoreCase("ACTIVE_SHALLOW")) {
            trt = TectonicRegionType.ACTIVE_SHALLOW;
        } else if (trtName.equalsIgnoreCase("STABLE_SHALLOW")) {
            trt = TectonicRegionType.STABLE_SHALLOW;
        } else if (trtName.equalsIgnoreCase("SUBDUCTION_INTERFACE")) {
            trt = TectonicRegionType.SUBDUCTION_INTERFACE;
        } else if (trtName.equalsIgnoreCase("SUBDUCTION_SLAB")) {
            trt = TectonicRegionType.SUBDUCTION_SLAB;
        } else if (trtName.equalsIgnoreCase("VOLCANIC")) {
            trt = TectonicRegionType.VOLCANIC;
        }
        return trt;
    }
}
