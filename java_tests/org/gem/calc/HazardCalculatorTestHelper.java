package org.gem.calc;

import static org.gem.calc.CalcTestHelper.mapLog;

import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.calc.magScalingRelations.MagScalingRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.PEER_testsMagAreaRelationship;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultSource;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class HazardCalculatorTestHelper
{
    public static final Double [] IMLS = mapLog(
            new Double[] {0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35,
                    0.4, 0.45, 0.5, 0.55, 0.6, 0.7});
    public static final double MAX_DISTANCE = 200.0;  // km

    public static DiscretizedFuncAPI expectedHazardCurve()
    {
//        Double[] poes = {4.00E-02, 4.00E-02, 4.00E-02, 3.99E-02, 3.46E-02,
//                         2.57E-02, 1.89E-02, 1.37E-02, 9.88E-03, 6.93E-03,
//                         4.84E-03, 3.36E-03, 2.34E-03, 1.52E-03, 5.12E-04};
        Double[] poes = new Double [] {0.04,
                0.04,
                0.04,
                0.0399,
                0.0346,
                0.0257,
                0.0189,
                0.0137,
                0.00988,
                0.00693,
                0.00484,
                0.00336,
                0.00234,
                0.00152,
                0.000512};

        ArbitrarilyDiscretizedFunc curve = 
                new ArbitrarilyDiscretizedFunc();
        for (int i = 0; i < IMLS.length; i++) {
            curve.set(IMLS[i], poes[i]);
        }

        return curve;
    }

    public static FloatingPoissonFaultSource testSource()
    {
        double aValue = 3.1292;
        double bValue = 0.9;
        double min = 5.0;
        double max = 6.5;
        double delta = 0.1;
        int num = (int) Math.round((max - min)/delta + 1);
        double totCumRate = Math.pow(10.0, aValue - bValue * min) -
                            Math.pow(10.0, aValue - bValue * max);
        IncrementalMagFreqDist magDist =
            new GutenbergRichterMagFreqDist(bValue, totCumRate,
                    min+delta/2, max-delta/2, num);
        FaultTrace faultTrace = new FaultTrace("");
        faultTrace.add(new Location(38.00000,-122.00000,0.0));
        faultTrace.add(new Location(38.22480,-122.00000,0.0));
        double aveDip = 90.0;
        double upperSeismogenicDepth = 0.0;
        double lowerSeismogenicDepth = 12.0;
        double gridSpacing = 1.0;
        StirlingGriddedSurface faultSurface =
            new StirlingGriddedSurface(faultTrace, aveDip,
                    upperSeismogenicDepth, lowerSeismogenicDepth, gridSpacing);
        MagScalingRelationship magScalingRel =
            new PEER_testsMagAreaRelationship();
        double magScalingSigma = 0.0;
        double rupAspectRatio = 2.0;
        double rupOffset = 1.0;
        double rake = 0.0;
        double duration = 1.0;
        double minMag = 0.0;
        int floatTypeFlag = 1;
        double fullFaultRupMagThresh = 12.0;
        FloatingPoissonFaultSource src = new FloatingPoissonFaultSource(magDist, faultSurface,
                magScalingRel, magScalingSigma, rupAspectRatio,
                rupOffset, rake, duration, minMag, floatTypeFlag,
                fullFaultRupMagThresh);
        src.setTectonicRegionType(TectonicRegionType.ACTIVE_SHALLOW);

        return src;
    }

    public static Site testSite()
    {
        StringParameter sadighSiteType = new StringParameter("Sadigh Site Type");
        sadighSiteType.setValue("Rock");
        Site site = new Site(new Location(38.113,-122.000));
        site.addParameter(sadighSiteType);

        return site;
    }

    public static ScalarIntensityMeasureRelationshipAPI testGMPE()
    {
        ScalarIntensityMeasureRelationshipAPI gmpe = new SadighEtAl_1997_AttenRel(null);
        gmpe.setParamDefaults();
        gmpe.setIntensityMeasure(PGA_Param.NAME);
        gmpe.getParameter(StdDevTypeParam.NAME).setValue(
                StdDevTypeParam.STD_DEV_TYPE_NONE);

        return gmpe;
    }

    public static EqkRupForecastAPI testERF()
    {
        return new EqkRupForecastAPI() {

            private FloatingPoissonFaultSource src = testSource();

            public String getName() {
                return null;
            }

            public void updateForecast() {}

            public String updateAndSaveForecast() {
                return null;
            }

            public void setTimeSpan(TimeSpan time) {}

            public boolean setParameter(String name, Object value) {
                return false;
            }

            public boolean isLocWithinApplicableRegion(Location loc) {
                return false;
            }

            public TimeSpan getTimeSpan() {
                return null;
            }

            public ArrayList<TectonicRegionType> getIncludedTectonicRegionTypes() {
                return null;
            }

            public Region getApplicableRegion() {
                return null;
            }

            public ListIterator<ParameterAPI> getAdjustableParamsIterator() {
                return null;
            }

            public ParameterList getAdjustableParameterList() {
                return null;
            }

            public ArrayList getSourceList() {
                ArrayList sourceList = new ArrayList<ProbEqkSource>();
                sourceList.add(src);
                return null;
            }

            public ProbEqkSource getSource(int iSource) {
                return src;
            }

            public ProbEqkRupture getRupture(int iSource, int nRupture) {
                return src.getRupture(nRupture);
            }

            public int getNumSources() {
                return 1;
            }

            public int getNumRuptures(int iSource) {
                return src.getNumRuptures();
            }

            public ArrayList<EqkRupture> drawRandomEventSet() {
                return null;
            }
        };
    }
}
