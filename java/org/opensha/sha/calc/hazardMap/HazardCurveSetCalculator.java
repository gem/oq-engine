package org.opensha.sha.calc.hazardMap;

import java.io.IOException;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.ListIterator;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.calc.hazardMap.components.CalculationSettings;
import org.opensha.sha.calc.hazardMap.components.CurveMetadata;
import org.opensha.sha.calc.hazardMap.components.CurveResultsArchiver;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TRTUtils;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This class calculates a set of hazard curves, typically for use in Condor.
 * 
 * @author kevin
 *
 */
public class HazardCurveSetCalculator {
	
	private EqkRupForecastAPI erf;
	private List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps;
	private List<DependentParameterAPI<Double>> imts;
	private CurveResultsArchiver archiver;
	private CalculationSettings calcSettings;
	private HazardCurveCalculator calc;
	
	public HazardCurveSetCalculator(EqkRupForecastAPI erf,
			List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps,
			CurveResultsArchiver archiver,
			CalculationSettings calcSettings) {
		this(erf, imrMaps, null, archiver, calcSettings);
	}
	
	public HazardCurveSetCalculator(EqkRupForecastAPI erf,
			List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps,
			List<DependentParameterAPI<Double>> imts,
			CurveResultsArchiver archiver,
			CalculationSettings calcSettings) {
		this.erf = erf;
		this.imrMaps = imrMaps;
		this.imts = imts;
		this.archiver = archiver;
		this.calcSettings = calcSettings;
		
		if (imts != null && imts.size() != imrMaps.size())
			throw new IllegalArgumentException("If IMTs are specified for each IMR map, there must me exactly one" +
					" for every IMR map.");
		
		try {
			this.calc = new HazardCurveCalculator();
		} catch (RemoteException e) {
			throw new RuntimeException(e);
		}
		
		erf.updateForecast();
	}
	
	public void calculateCurves(List<Site> sites) throws IOException {
		System.out.println("Calculating " + sites.size() + " hazard curves");
		System.out.println("ERF: " + erf.getName());
		System.out.println("Num IMR Maps: " + imrMaps.size());
		calc.setMaxSourceDistance(calcSettings.getMaxSourceDistance());
		System.out.println("Max Source Cutoff: " + calcSettings.getMaxSourceDistance());
		// looop over all sites
		int siteCount = 0;
		for (Site site : sites) {
			siteCount++;
			if (siteCount % 10 == 0)
				System.gc();
			int imrMapCount = 0;
			for (HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap : imrMaps) {
				if (imts != null) {
					// if a different IMT has been specified for each imr map then we must set it
					DependentParameterAPI<Double> newIMT = imts.get(imrMapCount);
//					System.out.println("Setting IMT to " + newIMT.getName());
					for (TectonicRegionType trt : imrMap.keySet()) {
						ScalarIntensityMeasureRelationshipAPI imr = imrMap.get(trt);
						imr.setIntensityMeasure(newIMT.getName());
						DependentParameterAPI<Double> imt = (DependentParameterAPI<Double>) imr.getIntensityMeasure();
						ListIterator<ParameterAPI<?>> it = newIMT.getIndependentParametersIterator();
						while (it.hasNext()) {
							ParameterAPI<?> depParam = it.next();
							imt.getIndependentParameter(depParam.getName()).setValue(depParam.getValue());
						}
					}
				}
				imrMapCount++;
				String imt = TRTUtils.getFirstIMR(imrMap).getIntensityMeasure().getName();
				System.out.println("Calculating curve(s) for site " + siteCount + "/" + sites.size()
						+ " IMR Map " + imrMapCount + "/" + imrMaps.size() + " IMT: " + imt);
				CurveMetadata meta = new CurveMetadata(site, imrMap, "imrs" + imrMapCount);
				if (archiver.isCurveCalculated(meta, calcSettings.getXValues(imt))) {
					System.out.println("Curve already calculated, skipping...");
					continue;
				}
				ArbitrarilyDiscretizedFunc calcFunction;
				boolean logSpace = calcSettings.isCalcInLogSpace();
				if (logSpace)
					calcFunction = getLogFunction(calcSettings.getXValues(imt));
				else
					calcFunction = calcSettings.getXValues(imt).deepClone();
				System.out.println("Calculating Hazard Curve. timestamp=" + System.currentTimeMillis());
				// actually calculate the curve from the log hazard function, site, IMR, and ERF
				calc.getHazardCurve(calcFunction,site,imrMap,erf);
				System.out.println("Calculated a curve! timestamp=" + System.currentTimeMillis());
				ArbitrarilyDiscretizedFunc hazardCurve;
				if (logSpace)
					hazardCurve = unLogFunction(calcSettings.getXValues(imt), calcFunction);
				else
					hazardCurve = calcFunction;
				// archive the curve;
				archiver.archiveCurve(hazardCurve, meta);
			}
		}
		System.out.println("DONE!");
	}
	
	/**
	 * Takes the log of the X-values of the given function
	 * @param arb
	 * @return A function with points (Log(x), 1)
	 */
	public static ArbitrarilyDiscretizedFunc getLogFunction(DiscretizedFuncAPI arb) {
		ArbitrarilyDiscretizedFunc new_func = new ArbitrarilyDiscretizedFunc();
		// TODO: we need to check if the log should be taken for all IMTs GEM will be using!
		// take log only if it is PGA, PGV or SA
//		if (this.xLogFlag) {
			for (int i = 0; i < arb.getNum(); ++i)
				new_func.set(Math.log(arb.getX(i)), 1);
			return new_func;
//		}
//		else
//			throw new RuntimeException("Unsupported IMT");
	}
	
	public static ArbitrarilyDiscretizedFunc unLogFunction(
			ArbitrarilyDiscretizedFunc oldHazFunc, ArbitrarilyDiscretizedFunc logHazFunction) {
		int numPoints = oldHazFunc.getNum();
		ArbitrarilyDiscretizedFunc hazFunc = new ArbitrarilyDiscretizedFunc();
		// take log only if it is PGA, PGV or SA
//		if (this.xLogFlag) {
			for (int i = 0; i < numPoints; ++i) {
				hazFunc.set(oldHazFunc.getX(i), logHazFunction.getY(i));
			}
			return hazFunc;
//		}
//		else
//			throw new RuntimeException("Unsupported IMT");
	}

}
