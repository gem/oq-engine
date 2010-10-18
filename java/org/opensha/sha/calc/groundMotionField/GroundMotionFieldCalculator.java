package org.opensha.sha.calc.groundMotionField;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.apache.commons.math.linear.Array2DRowRealMatrix;
import org.apache.commons.math.linear.CholeskyDecompositionImpl;
import org.apache.commons.math.linear.NonSquareMatrixException;
import org.apache.commons.math.linear.NotPositiveDefiniteMatrixException;
import org.apache.commons.math.linear.NotSymmetricMatrixException;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;

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
     * Compute stochastic ground motion field with spatial correlation using
     * correlation model from Jayamram & Baker (2009):
     * "Correlation model for spatially distributed ground-motion intensities"
     * Nirmal Jayaram and Jack W. Baker, Earthquake Engng. Struct. Dyn (2009)
     * The algorithm is structured according to the following steps: 1) Compute
     * mean ground motion values, 2) Stochastically generate inter-event
     * residuals (which follow a univariate normal distribution), 3)
     * Stochastically generate intra-event residuals (following the proposed
     * correlation model) 4) Combine the three terms generated in steps 1-3.
     * 
     * NOTE: The correlation model implemented here refers to the case 1 in
     * Jayamram & Baker (2009) paper, that is when Vs30 values do not show or
     * are not expected to show clustering (i.e. there are no cluster of sites
     * in which the geologic conditions of the soil are similar). The method
     * checks if the sites passed in contains Vs30 values, and if they are found
     * to vary it gives a warning.
     * 
     * Intra-event residuals are calculated by generating Gaussian deviates from
     * a multivariate normal distribution using Cholesky factorization following
     * the algorithm described in
     * "Computational Statistics Handbook with Matlab", Wendy L. Martinez &
     * Angel R. Martinez, CHAPMAN & HALL, pag. 97.
     * 
     * @param attenRel
     * @param rup
     * @param sites
     * @param rn
     * @return
     */
    public static Map<Site, Double> getStochasticGroundMotionField_JB2009(
            ScalarIntensityMeasureRelationshipAPI attenRel, EqkRupture rup,
            List<Site> sites, Random rn) {
        attenRel.setEqkRupture(rup);
        // compute ground motion field considering only inter-event residual
        attenRel.getParameter(StdDevTypeParam.NAME).setValue(
                StdDevTypeParam.STD_DEV_TYPE_INTER);
        Map<Site, Double> groundMotionField =
                getStochasticGroundMotionField(attenRel, rup, sites, rn);
        // compute covariance matrix considering only intra-event residual
        attenRel.getParameter(StdDevTypeParam.NAME).setValue(
                StdDevTypeParam.STD_DEV_TYPE_INTRA);
        int numberOfSites = sites.size();
        Array2DRowRealMatrix covarianceMatrix =
                new Array2DRowRealMatrix(numberOfSites, numberOfSites);
        double period =
                (Double) attenRel.getParameter(PeriodParam.NAME).getValue();
        double b = Double.NaN;
        if (period < 1)
            b = 8.5 + 17.2 * period;
        else if (period >= 1)
            b = 22.0 + 3.7 * period;
        double intraEventStd_i = Double.NaN;
        double intraEventStd_j = Double.NaN;
        double distance = Double.NaN;
        double covarianceValue = Double.NaN;
        int index_i = 0;
        for (Site site_i : sites) {
            attenRel.setSite(site_i);
            intraEventStd_i = attenRel.getStdDev();
            int index_j = 0;
            for (Site site_j : sites) {
                attenRel.setSite(site_j);
                intraEventStd_j = attenRel.getStdDev();
                distance =
                        LocationUtils.horzDistance(site_i.getLocation(),
                                site_j.getLocation());
                covarianceValue =
                        intraEventStd_i * intraEventStd_j
                                * Math.exp(-3 * (distance / b));
                covarianceMatrix.setEntry(index_i, index_j, covarianceValue);
                index_j = index_j + 1;
            }
            index_i = index_i + 1;
        }
        CholeskyDecompositionImpl cholDecomp = null;
        try {
            cholDecomp = new CholeskyDecompositionImpl(covarianceMatrix);
        } catch (NonSquareMatrixException e) {
            e.printStackTrace();
        } catch (NotSymmetricMatrixException e) {
            e.printStackTrace();
        } catch (NotPositiveDefiniteMatrixException e) {
            e.printStackTrace();
        }

        return null;
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
