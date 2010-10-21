package org.opensha.sha.calc.groundMotionField;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.apache.commons.math.linear.BlockRealMatrix;
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
     * Intra-event residuals are calculated by generating Gaussian deviates from
     * a multivariate normal distribution using Cholesky factorization
     * (decompose covariance matrix, take lower triangular and multiply by a
     * vector of uncorrelated, standard Gaussian variables)
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
     *            : {@link Random} random number generator
     * @param inter_event
     *            : if true compute ground motion field using both inter- and
     *            intra-event residuals, if false use only intra-event residuals
     * @param Vs30Cluster
     *            : true if Vs30 values show clustering [compute correlation
     *            range according to case 2 of Jayaram&Baker paper], false if
     *            Vs30 values do not show clustering [compute correlation range
     *            according to case 1 of Jayaram&Baker paper]
     * @return
     */
    public static Map<Site, Double> getStochasticGroundMotionField_JB2009(
            ScalarIntensityMeasureRelationshipAPI attenRel, EqkRupture rup,
            List<Site> sites, Random rn, Boolean inter_event,
            Boolean Vs30Cluster) {

        validateInput(attenRel, rup, sites);

        if (rn == null)
            throw new IllegalArgumentException(
                    "Random number generator cannot be null");
        if (inter_event == null)
            throw new IllegalArgumentException(
                    "Usage of inter event residuals must be specified");
        if (Vs30Cluster == null)
            throw new IllegalArgumentException(
                    "Vs30 cluster option must be specified");
        if (inter_event == true
                && attenRel.getParameter(StdDevTypeParam.NAME).getConstraint()
                        .isAllowed(StdDevTypeParam.STD_DEV_TYPE_INTER) == false)
            throw new IllegalArgumentException(
                    "The specified attenuation relationship does not provide"
                            + " inter-event standard deviation");
        if (attenRel.getParameter(StdDevTypeParam.NAME).getConstraint()
                .isAllowed(StdDevTypeParam.STD_DEV_TYPE_INTRA) == false)
            throw new IllegalArgumentException(
                    "The specified attenuation relationship does not provide"
                            + " intra-event standard deviation");

        Map<Site, Double> groundMotionField = null;
        if (inter_event == true) {
            attenRel.getParameter(StdDevTypeParam.NAME).setValue(
                    StdDevTypeParam.STD_DEV_TYPE_INTER);
            groundMotionField =
                    getStochasticGroundMotionField(attenRel, rup, sites, rn);
        } else
            groundMotionField = getMeanGroundMotionField(attenRel, rup, sites);

        // compute intra-event residuals, by decomposing the covariance matrix
        // with cholesky decomposition, and by multiplying the lower triangular
        // matrix with a vector of univariate Gaussian deviates
        int numberOfSites = sites.size();
        double[] gaussianDeviates = new double[numberOfSites];
        for (int i = 0; i < numberOfSites; i++)
            gaussianDeviates[i] =
                    getGaussianDeviate(
                            1.0,
                            (Double) attenRel.getParameter(
                                    SigmaTruncLevelParam.NAME).getValue(),
                            (String) attenRel.getParameter(
                                    SigmaTruncTypeParam.NAME).getValue(), rn);
        BlockRealMatrix covarianceMatrix =
                getCovarianceMatrix_JB2009(attenRel, rup, sites, rn,
                        Vs30Cluster);
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
        double[] intraEventResiduals =
                cholDecomp.getL().operate(gaussianDeviates);
        int indexSite = 0;
        for (Site site : sites) {
            double val = groundMotionField.get(site);
            groundMotionField.put(site, val + intraEventResiduals[indexSite]);
            indexSite = indexSite + 1;
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

    /**
     * Calculates covariance matrix for intra-event residuals using correlation
     * model of Jayamram & Baker (2009):
     * "Correlation model for spatially distributed ground-motion intensities"
     * Nirmal Jayaram and Jack W. Baker, Earthquake Engng. Struct. Dyn (2009)
     * 
     * @param attenRel
     * @param rup
     * @param sites
     * @param rn
     * @param Vs30Cluster
     * @return
     */
    private static BlockRealMatrix getCovarianceMatrix_JB2009(
            ScalarIntensityMeasureRelationshipAPI attenRel, EqkRupture rup,
            List<Site> sites, Random rn, Boolean Vs30Cluster) {
        int numberOfSites = sites.size();
        BlockRealMatrix covarianceMatrix =
                new BlockRealMatrix(numberOfSites, numberOfSites);
        attenRel.setEqkRupture(rup);
        attenRel.getParameter(StdDevTypeParam.NAME).setValue(
                StdDevTypeParam.STD_DEV_TYPE_INTRA);
        double period =
                (Double) attenRel.getParameter(PeriodParam.NAME).getValue();
        double correlationRange = Double.NaN;
        if (period < 1 && Vs30Cluster == false)
            correlationRange = 8.5 + 17.2 * period;
        else if (period < 1 && Vs30Cluster == true)
            correlationRange = 40.7 - 15.0 * period;
        else if (period >= 1)
            correlationRange = 22.0 + 3.7 * period;
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
                                * Math.exp(-3 * (distance / correlationRange));
                covarianceMatrix.setEntry(index_i, index_j, covarianceValue);
                index_j = index_j + 1;
            }
            index_i = index_i + 1;
        }
        return covarianceMatrix;
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
