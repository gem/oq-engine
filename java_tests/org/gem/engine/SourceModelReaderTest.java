package org.gem.engine;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.util.ArrayList;
import java.util.List;

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
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class SourceModelReaderTest {

    @Test
    public void readSourceModel() {

        List<GEMSourceData> srcList = new ArrayList<GEMSourceData>();
        srcList.add(getFaultSourceData());
        srcList.add(getComplexFaultData());
        srcList.add(getAreaSourceData());
        srcList.add(getPointSourceData());

        SourceModelReader srcModelReader =
                new SourceModelReader("java_tests/data/source_model.xml", 0.1);

        assertEquals(srcList.size(), srcModelReader.getSourceList().size());
        for (int i = 0; i < srcList.size(); i++) {
            assertTrue(srcModelReader.getSourceList().get(i)
                    .equals(srcList.get(i)));
        }

    }

    private GEMPointSourceData getPointSourceData() {
        String ID = "src04";
        String name = "point";
        TectonicRegionType tectReg = TectonicRegionType.ACTIVE_SHALLOW;
        Location loc = new Location(38.0, -122.0);
        IncrementalMagFreqDist[] magDists = new IncrementalMagFreqDist[1];
        double bValue = 0.8;
        double aValueCumulative = 0.5;
        double min = 5.0;
        double max = 7.0;
        double delta = 0.1;
        IncrementalMagFreqDist magFreqDist =
                getGutenbergRichterMagFreqDist(bValue, aValueCumulative, min,
                        max, delta);
        magDists[0] = magFreqDist;
        FocalMechanism[] focMechs = new FocalMechanism[1];
        double strike = 0.0;
        double dip = 90.0;
        double rake = 0.0;
        FocalMechanism focMech = new FocalMechanism(strike, dip, rake);
        focMechs[0] = focMech;
        HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc =
                new HypoMagFreqDistAtLoc(magDists, loc, focMechs);
        ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                new ArbitrarilyDiscretizedFunc();
        aveRupTopVsMag.set(6.0, 5.0);
        aveRupTopVsMag.set(6.5, 3.0);
        aveRupTopVsMag.set(7.0, 0.0);
        double aveHypoDepth = 5.0;
        return new GEMPointSourceData(ID, name, tectReg, hypoMagFreqDistAtLoc,
                aveRupTopVsMag, aveHypoDepth);

    }

    private GEMAreaSourceData getAreaSourceData() {
        String ID = "src03";
        String name = "Quito";
        TectonicRegionType tectReg = TectonicRegionType.ACTIVE_SHALLOW;
        LocationList regionBoundary = new LocationList();
        regionBoundary.add(new Location(37.5, -122.5));
        regionBoundary.add(new Location(37.5, -121.5));
        regionBoundary.add(new Location(38.5, -121.5));
        regionBoundary.add(new Location(38.5, -122.5));
        Region reg = new Region(regionBoundary, BorderType.GREAT_CIRCLE);
        double bValue = 0.8;
        double aValueCumulative = 5.0;
        double min = 5.0;
        double max = 7.0;
        double delta = 0.1;
        IncrementalMagFreqDist[] magFreqDistList =
                new IncrementalMagFreqDist[2];
        FocalMechanism[] focMechList = new FocalMechanism[2];
        magFreqDistList[0] =
                getGutenbergRichterMagFreqDist(bValue, aValueCumulative, min,
                        max, delta);
        magFreqDistList[1] =
                getGutenbergRichterMagFreqDist(bValue, aValueCumulative, min,
                        max, delta);
        double strike = 0.0;
        double dip = 90.0;
        double rake = 0.0;
        focMechList[0] = new FocalMechanism(strike, dip, rake);
        strike = 90.0;
        focMechList[1] = new FocalMechanism(strike, dip, rake);
        MagFreqDistsForFocalMechs magfreqDistFocMech =
                new MagFreqDistsForFocalMechs(magFreqDistList, focMechList);
        ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                new ArbitrarilyDiscretizedFunc();
        aveRupTopVsMag.set(6.0, 5.0);
        aveRupTopVsMag.set(6.5, 3.0);
        aveRupTopVsMag.set(7.0, 0.0);
        double aveHypoDepth = 5.0;
        GEMAreaSourceData areaSrc =
                new GEMAreaSourceData(ID, name, tectReg, reg,
                        magfreqDistFocMech, aveRupTopVsMag, aveHypoDepth);
        return areaSrc;
    }

    private GEMSubductionFaultSourceData getComplexFaultData() {
        String name = "Cascadia Megathrust";
        String ID = "src02";
        TectonicRegionType tectRegType =
                TectonicRegionType.SUBDUCTION_INTERFACE;
        FaultTrace topTrace = new FaultTrace("");
        topTrace.add(new Location(40.363, -124.704, 0.5493260E+01));
        topTrace.add(new Location(41.214, -124.977, 0.4988560E+01));
        topTrace.add(new Location(42.096, -125.140, 0.4897340E+01));
        topTrace.add(new Location(42.965, -125.219, 0.4847610E+01));
        topTrace.add(new Location(43.852, -125.257, 0.4871280E+01));
        topTrace.add(new Location(44.718, -125.313, 0.4782420E+01));
        topTrace.add(new Location(45.458, -125.416, 0.4410880E+01));
        topTrace.add(new Location(46.337, -125.623, 0.4028170E+01));
        topTrace.add(new Location(46.642, -125.746, 0.3797400E+01));
        topTrace.add(new Location(46.965, -125.874, 0.3649880E+01));
        topTrace.add(new Location(47.289, -126.015, 0.3650670E+01));
        topTrace.add(new Location(47.661, -126.240, 0.3675160E+01));
        topTrace.add(new Location(47.994, -126.422, 0.3907950E+01));
        topTrace.add(new Location(48.287, -126.660, 0.4125160E+01));
        topTrace.add(new Location(48.711, -127.037, 0.4583670E+01));
        topTrace.add(new Location(49.279, -127.605, 0.4761580E+01));
        FaultTrace bottomTrace = new FaultTrace("");
        bottomTrace.add(new Location(40.347, -123.829, 0.2038490E+02));
        bottomTrace.add(new Location(41.218, -124.137, 0.1741390E+02));
        bottomTrace.add(new Location(42.115, -124.252, 0.1752740E+02));
        bottomTrace.add(new Location(42.984, -124.313, 0.1729190E+02));
        bottomTrace.add(new Location(43.868, -124.263, 0.1856200E+02));
        bottomTrace.add(new Location(44.740, -124.213, 0.1977810E+02));
        bottomTrace.add(new Location(45.494, -124.099, 0.2230320E+02));
        bottomTrace.add(new Location(46.369, -123.853, 0.2575860E+02));
        bottomTrace.add(new Location(46.811, -123.644, 0.2711490E+02));
        bottomTrace.add(new Location(47.300, -123.423, 0.2761730E+02));
        bottomTrace.add(new Location(47.792, -123.440, 0.2750930E+02));
        bottomTrace.add(new Location(48.221, -124.075, 0.2602160E+02));
        bottomTrace.add(new Location(48.560, -124.773, 0.2572870E+02));
        bottomTrace.add(new Location(48.873, -125.409, 0.2544710E+02));
        bottomTrace.add(new Location(49.244, -126.117, 0.2471340E+02));
        bottomTrace.add(new Location(49.687, -126.911, 0.2275770E+02));
        double rake = 0.0;
        double bValue = 0.8;
        double aValueCumulative = 1.0;
        double min = 6.5;
        double max = 9.0;
        double delta = 0.1;
        IncrementalMagFreqDist magFreqDist =
                getGutenbergRichterMagFreqDist(bValue, aValueCumulative, min,
                        max, delta);
        boolean floatRuptureFlag = true;
        GEMSubductionFaultSourceData complexFaultSrc =
                new GEMSubductionFaultSourceData(ID, name, tectRegType,
                        topTrace, bottomTrace, rake, magFreqDist,
                        floatRuptureFlag);
        return complexFaultSrc;
    }

    private GutenbergRichterMagFreqDist getGutenbergRichterMagFreqDist(
            double bValue, double aValueCumulative, double min, double max,
            double delta) {
        double totCumRate =
                Math.pow(10, aValueCumulative - bValue * min)
                        - Math.pow(10, aValueCumulative - bValue * max);
        min = min + delta / 2;
        max = max - delta / 2;
        int num = (int) Math.round((max - min) / delta + 1);
        return new GutenbergRichterMagFreqDist(bValue, totCumRate, min, max,
                num);
    }

    private GEMFaultSourceData getFaultSourceData() {
        String name = "Mount Diablo Thrust";
        String ID = "src01";
        TectonicRegionType tectRegType = TectonicRegionType.ACTIVE_SHALLOW;
        IncrementalMagFreqDist magFreqDist =
                new IncrementalMagFreqDist(6.55, 5, 0.1);
        magFreqDist.add(0, 0.0010614989);
        magFreqDist.add(1, 8.8291627E-4);
        magFreqDist.add(2, 7.3437777E-4);
        magFreqDist.add(3, 6.108288E-4);
        magFreqDist.add(4, 5.080653E-4);
        FaultTrace trace = new FaultTrace("");
        trace.add(new Location(37.73010, -121.82290, 0.0));
        trace.add(new Location(37.87710, -122.03880, 0.0));
        double dip = 38.0;
        double rake = 90.0;
        double upperSeismogenicDepth = 8.0;
        double lowerSeismogenicDepth = 13.0;
        boolean floatRuptureFlag = true;
        GEMFaultSourceData faultSrc =
                new GEMFaultSourceData(ID, name, tectRegType, magFreqDist,
                        trace, dip, rake, lowerSeismogenicDepth,
                        upperSeismogenicDepth, floatRuptureFlag);
        return faultSrc;
    }
}
