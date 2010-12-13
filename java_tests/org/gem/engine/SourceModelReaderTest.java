package org.gem.engine;

import java.util.ArrayList;

import org.junit.Test;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class SourceModelReaderTest {

    @Test
    public void readSourceModel() {

        ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();

        GEMFaultSourceData faultSrc = getFaultSourceData();
        srcList.add(faultSrc);

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
        // GEMSubductionFaultSourceData complexFaultSrc = new
        // GEMSubductionFaultSourceData(FaultTrace TopTrace, FaultTrace
        // BottomTrace,
        // double rake, IncrementalMagFreqDist mfd, boolean floatRuptureFlag);

        // GEMAreaSourceData areaSrc = new GEMAreaSourceData(String id, String
        // name, TectonicRegionType tectReg,
        // Region reg, MagFreqDistsForFocalMechs magfreqDistFocMech,
        // ArbitrarilyDiscretizedFunc aveRupTopVsMag, double aveHypoDepth);

        // GEMPointSourceData pointSrc = new GEMPointSourceData(String id,
        // String name, TectonicRegionType tectReg,
        // HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc,
        // ArbitrarilyDiscretizedFunc aveRupTopVsMag, double aveHypoDepth);

        SourceModelReader srcModelReader =
                new SourceModelReader("java_tests/data/source_model.xml", 0.1);
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
                        trace, dip, rake, upperSeismogenicDepth,
                        lowerSeismogenicDepth, floatRuptureFlag);
        return faultSrc;
    }
}
