package org.opensha.sha.calc.groundMotionField;

import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.opensha.commons.data.Site;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;

public class GroundMotionFieldCalculator {

	/**
	 * Computes mean ground motion
	 * 
	 * @param attenRel
	 * @param rup
	 * @param sites
	 * @return
	 */
	public static Map<Site, Double> getMeanGroundMotionField(
			ScalarIntensityMeasureRelationshipAPI attenRel, EqkRupture rup,
			List<Site> sites) {
		Map<Site, Double> groundMotionMap = new HashMap<Site, Double>();
		double meanGroundMotion = Double.NaN;
		attenRel.setEqkRupture(rup);
		for (Site site : sites) {
			attenRel.setSite(site);
			meanGroundMotion = attenRel.getMean();
			groundMotionMap.put(site, new Double(meanGroundMotion));
		}
		return groundMotionMap;
	}

	/**
	 * Compute stochastic ground motion field
	 * 
	 * @param attenRel
	 * @param rup
	 * @param sites
	 * @param rn
	 * @return
	 */
	public static Map<Site, Double> getStochasticGroundMotionField(
			ScalarIntensityMeasureRelationshipAPI attenRel, EqkRupture rup,
			List<Site> sites, Random rn) {
		Map<Site, Double> stochasticGroundMotionField = new HashMap<Site, Double>();
		Map<Site, Double> meanGroundMotion = getMeanGroundMotionField(
				attenRel, rup, sites);
		double standardDeviation = (Double) attenRel.getParameter(
				StdDevTypeParam.NAME).getValue();
		double truncationLevel = (Double) attenRel.getParameter(
				SigmaTruncLevelParam.NAME).getValue();
		String truncationType = (String) attenRel.getParameter(
				SigmaTruncTypeParam.NAME).getValue();
		Iterator<Site> iter = meanGroundMotion.keySet().iterator();
		while (iter.hasNext()) {
			Site site = iter.next();
			Double val = meanGroundMotion.get(site);
			double deviate = getGaussianDeviate(standardDeviation,
					truncationLevel, truncationType, rn);
			val = val + deviate;
			stochasticGroundMotionField.put(site, val);
		}
		return stochasticGroundMotionField;
	}

	private static double getGaussianDeviate(double standardDeviation,
			double truncationLevel, String truncationType, Random rn) {
		double dev = Double.NaN;
		if (truncationType
				.equalsIgnoreCase(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE)) {
			dev = standardDeviation * rn.nextGaussian();
		} else if (truncationType
				.equalsIgnoreCase(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED)) {
			dev = rn.nextGaussian();
			while (dev < -truncationLevel || dev > truncationLevel) {
				dev = rn.nextGaussian();
			}
			dev = dev * standardDeviation;
		} else if (truncationType
				.equalsIgnoreCase(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED)) {
			dev = rn.nextGaussian();
			while (dev > truncationLevel) {
				dev = rn.nextGaussian();
			}
			dev = dev * standardDeviation;
		}
		return dev;
	}

}
