package org.gem.calc;

import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.DepthTo1pt0kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.DepthTo2pt5kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.imr.param.SiteParams.Vs30_TypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_TypeParam.Vs30Type;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class CalcTestHelper
{
    public static final Double[] IMLS = new Double[] {
        0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269,
        0.0376, 0.0527, 0.0738, 0.103, 0.145, 0.203,
        0.284, 0.397, 0.556, 0.778, 1.09, 1.52, 2.13};

    public static final List<Double> LOG_IMLS = 
            Arrays.asList(mapLog(IMLS));

    /**
     * Map the Math.log() method to each element in the input list
     * to create a new list.
     */
    private static Double[] mapLog(Double[] list)
    {
        Double[] result = new Double[list.length];
        for (int i = 0; i < list.length; i++)
        {
            result[i] = Math.log(list[i]);
        }
        return result;
    }

	public static Site makeTestSite()
	{
		Site site = new Site(new Location(0.0, 0.0));
		site.addParameter(new StringParameter(Vs30_TypeParam.NAME, Vs30Type.Measured.toString()));
		site.addParameter(new DoubleParameter(Vs30_Param.NAME, 760.0));
		site.addParameter(new DoubleParameter(DepthTo1pt0kmPerSecParam.NAME, 100.0));
		site.addParameter(new DoubleParameter(DepthTo2pt5kmPerSecParam.NAME, 1.0));
		return site;
	}

	public static Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> makeTestImrMap()
	{
		Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap = new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		imrMap.put(TectonicRegionType.ACTIVE_SHALLOW, getTestIMRActiveShallow());
		return imrMap;
	}

	public static Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> makeTestImrMapZeroStdDev()
	{
		Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap = new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		ScalarIntensityMeasureRelationshipAPI imr = new BA_2008_AttenRel(null);
		imr.getParameter(StdDevTypeParam.NAME).setValue(
				StdDevTypeParam.STD_DEV_TYPE_NONE);
		imrMap.put(TectonicRegionType.ACTIVE_SHALLOW, imr);
		return imrMap;
	}

	private static ScalarIntensityMeasureRelationshipAPI getTestIMRActiveShallow()
	{
		ScalarIntensityMeasureRelationshipAPI imr = new BA_2008_AttenRel(null);
		setDefaultImrParams(imr);
		return imr;
	}

	private static ScalarIntensityMeasureRelationshipAPI getTestIMRStableContinental()
	{
		ScalarIntensityMeasureRelationshipAPI imr = new CB_2008_AttenRel(null);
		setDefaultImrParams(imr);
		return imr;
	}

	private static void setDefaultImrParams(ScalarIntensityMeasureRelationshipAPI imr)
	{
		imr.setIntensityMeasure(PGA_Param.NAME);
		imr.getParameter(StdDevTypeParam.NAME).setValue(
				StdDevTypeParam.STD_DEV_TYPE_TOTAL);
		imr.getParameter(SigmaTruncTypeParam.NAME).setValue(
				SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED);
		imr.getParameter(SigmaTruncLevelParam.NAME).setValue(3.0);
		imr.getParameter(ComponentParam.NAME).setValue(
				ComponentParam.COMPONENT_GMRotI50);
	}

	public static GEM1ERF makeTestERF(double areaSrcDiscretization, int numMfdPts, BorderType borderType)
	{
		ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();
		srcList.add(makeTestSourceDataActiveShallow(numMfdPts, borderType));

		double timeSpan = 50.0;
		GEM1ERF erf = GEM1ERF.getGEM1ERF(srcList, timeSpan);
		erf.getParameter(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME).setValue(areaSrcDiscretization);
		erf.updateForecast();
		return erf;
	}

	private static GEMSourceData makeTestSourceDataActiveShallow(int numMfdPts, BorderType borderType)
	{
		String id = "src1";
		String name = "testSource";
		TectonicRegionType tectReg = TectonicRegionType.ACTIVE_SHALLOW;

		LocationList border = new LocationList();
		border.add(new Location(-0.5, -0.5));
		border.add(new Location(0.5, -0.5));
		border.add(new Location(0.5, 0.5));
		border.add(new Location(-0.5, 0.5));
		Region reg = new Region(border, borderType);

		double bValue = 1.0;
		double totCumRate = 0.2;
		double min = 5.05;
		double max = 8.95;
		GutenbergRichterMagFreqDist magDist = new GutenbergRichterMagFreqDist(
				bValue, totCumRate, min, max, numMfdPts);

		double strike = 0.0;
		double dip = 90.0;
		double rake = 0.0;
		FocalMechanism focalMechanism = new FocalMechanism(strike, dip, rake);

		MagFreqDistsForFocalMechs magfreqDistFocMech = new MagFreqDistsForFocalMechs(
				magDist, focalMechanism);

		ArbitrarilyDiscretizedFunc aveRupTopVsMag = new ArbitrarilyDiscretizedFunc();
		double magThreshold = 6.5;
		double topOfRuptureDepth = 0.0;
		aveRupTopVsMag.set(magThreshold, topOfRuptureDepth);
		double aveHypoDepth = 5.0;

		GEMSourceData srcData = new GEMAreaSourceData(id, name, tectReg, reg,
				magfreqDistFocMech, aveRupTopVsMag, aveHypoDepth);
		return srcData;
	}

	private static GEMSourceData makeTestSourceDataStableCrust()
	{
		String id = "src1";
		String name = "testSource";
		TectonicRegionType tectReg = TectonicRegionType.STABLE_SHALLOW;

		LocationList border = new LocationList();
		border.add(new Location(-0.5, 0.5));
		border.add(new Location(0.5, 0.5));
		border.add(new Location(0.5, 1.5));
		border.add(new Location(-0.5, 1.5));
		Region reg = new Region(border, BorderType.GREAT_CIRCLE);

		double bValue = 1.0;
		double totCumRate = 0.2;
		double min = 5.05;
		double max = 8.95;
		int num = 41;
		GutenbergRichterMagFreqDist magDist = new GutenbergRichterMagFreqDist(
				bValue, totCumRate, min, max, num);

		double strike = 0.0;
		double dip = 90.0;
		double rake = 0.0;
		FocalMechanism focalMechanism = new FocalMechanism(strike, dip, rake);

		MagFreqDistsForFocalMechs magfreqDistFocMech = new MagFreqDistsForFocalMechs(
				magDist, focalMechanism);

		ArbitrarilyDiscretizedFunc aveRupTopVsMag = new ArbitrarilyDiscretizedFunc();
		double magThreshold = 6.5;
		double topOfRuptureDepth = 0.0;
		aveRupTopVsMag.set(magThreshold, topOfRuptureDepth);
		double aveHypoDepth = 5.0;

		GEMSourceData srcData = new GEMAreaSourceData(id, name, tectReg, reg,
				magfreqDistFocMech, aveRupTopVsMag, aveHypoDepth);
		return srcData;
	}

	public static DiscretizedFuncAPI makeHazardCurve(List<Double> imls, double areaSrcDiscretization, EqkRupForecastAPI erf)
	{
		DiscretizedFuncAPI hazardCurve = new ArbitrarilyDiscretizedFunc();
		// initialize the curve our defined list of IMLs,
		// set the corresponding PoEs to 0.0
		for (double d : imls)
		{
			hazardCurve.set(d, 0.0);
		}
		try {
			HazardCurveCalculator hcc = new HazardCurveCalculator();
			hcc.getHazardCurve(hazardCurve, makeTestSite(), makeTestImrMap(), erf);
		} catch (RemoteException e) {
			throw new RuntimeException(e);
		}
		return hazardCurve;
	}

}
