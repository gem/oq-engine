package org.opensha.sha.calc.groundMotionField;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.opensha.commons.data.Site;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;

public class GroundMotionFieldCalculator {

    /**
     * Computes mean ground motion for a list of sites.
     * 
     * @param attenRel
     *            : {@link ScalarIntensityMeasureRelationshipAPI} attenuation
     *            relationship used for ground motion field calculation
     * @param rup
     *            : {@link EqkRupture} earthquake rupture generating the ground
     *            motion field
     * @param sites
     *            : array list of {@link Site} where ground motion values have
     *            to be computed
     * @return : {@link Map} associating sites ({@link Site}) and ground motion
     *         values {@link Double}
     */
    public static Map<Site, Double> getMeanGroundMotionField(
            ScalarIntensityMeasureRelationshipAPI attenRel, EqkRupture rup,
            List<Site> sites) {
        validateInput(attenRel, rup, sites);
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
     * Compute stochastic ground motion field by adding to the mean ground
     * motion field Gaussian deviates which takes into account the truncation
     * level and the truncation type.
     * 
     * @param attenRel
     *            : {@link ScalarIntensityMeasureRelationshipAPI} attenuation
     *            relationship used for ground motion field calculation
     * @param rup
     *            : {@link EqkRupture} earthquake rupture generating the ground
     *            motion field
     * @param sites
     *            : array list of {@link Site} where ground motion values have
     *            to be computed
     * @param rn
     *            : {@link Random} random number generator for Gaussian deviate
     *            calculation
     * @return: {@link Map} associating sites ({@link Site}) and ground motion
     *          values {@link Double}
     */
    public static Map<Site, Double> getStochasticGroundMotionField(
            ScalarIntensityMeasureRelationshipAPI attenRel, EqkRupture rup,
            List<Site> sites, Random rn) {
        if (rn == null)
            throw new IllegalArgumentException(
                    "Random number generator cannot be null");
        validateInput(attenRel, rup, sites);
        Map<Site, Double> groundMotionField =
                getMeanGroundMotionField(attenRel, rup, sites);
        attenRel.setEqkRupture(rup);
        double standardDeviation = Double.NaN;
        double truncationLevel =
                (Double) attenRel.getParameter(SigmaTruncLevelParam.NAME)
                        .getValue();
        String truncationType =
                (String) attenRel.getParameter(SigmaTruncTypeParam.NAME)
                        .getValue();
        for (Site site : sites) {
            attenRel.setSite(site);
            standardDeviation = attenRel.getStdDev();
            Double val = groundMotionField.get(site);
            double deviate =
                    getGaussianDeviate(standardDeviation, truncationLevel,
                            truncationType, rn);
            val = val + deviate;
            groundMotionField.put(site, val);
        }
        return groundMotionField;
    }

    /**
     * Generate Gaussian deviate (mean zero, standard deviation =
     * standardDeviation)
     * 
     * @param standardDeviation
     *            : double standard deviation
     * @param truncationLevel
     *            : double truncation level (in units of standard deviation)
     * @param truncationType
     *            : String type of truncation defined by the
     *            {@link SigmaTruncTypeParam}
     * @param rn
     *            : random number generator
     * @return : double
     */
    private static double getGaussianDeviate(double standardDeviation,
            double truncationLevel, String truncationType, Random rn) {
        double dev = rn.nextGaussian();
        if (truncationType
                .equalsIgnoreCase(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED)) {
            while (dev < -truncationLevel || dev > truncationLevel) {
                dev = rn.nextGaussian();
            }
        } else if (truncationType
                .equalsIgnoreCase(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED)) {
            while (dev > truncationLevel) {
                dev = rn.nextGaussian();
            }
        }
        return dev * standardDeviation;
    }

    private static Boolean validateInput(
            ScalarIntensityMeasureRelationshipAPI attenRel, EqkRupture rup,
            List<Site> sites) {
        if (attenRel == null) {
            throw new IllegalArgumentException(
                    "Attenuation relationship cannot be null");
        }

        if (rup == null) {
            throw new IllegalArgumentException(
                    "Earthquake rupture cannot be null");
        }

        if (sites == null) {
            throw new IllegalArgumentException(
                    "Array list of sites cannot be null");
        }

        if (sites.isEmpty()) {
            throw new IllegalArgumentException(
                    "Array list of sites must contain at least one site");
        }

        return true;
    }

}
