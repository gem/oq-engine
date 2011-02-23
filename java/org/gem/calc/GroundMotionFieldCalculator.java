package org.gem.calc;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.commons.math.linear.BlockRealMatrix;
import org.apache.commons.math.linear.CholeskyDecompositionImpl;
import org.apache.commons.math.linear.OpenMapRealMatrix;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;

import cern.colt.matrix.tdouble.algo.decomposition.SparseDoubleCholeskyDecomposition;
import cern.colt.matrix.tdouble.impl.DenseDoubleMatrix1D;
import cern.colt.matrix.tdouble.impl.SparseCCDoubleMatrix2D;

/**
 * Class providing methods for ground motion field calculation
 */
public class GroundMotionFieldCalculator {

	private static Log logger = LogFactory.getLog(GroundMotionFieldCalculator.class);
    
    private ScalarIntensityMeasureRelationshipAPI attenRel;
    private EqkRupture rup;
    private List<Site> sites;
    private SparseCCDoubleMatrix2D covarianceMatrix;
    
    /**
     * Jayaram and Baker 2009 Vs30 cluster parameter. The default is false 
     * (no clustering in Vs30 distribution)
     */
    private boolean JB2009_Vs30ClusterParam = false;
    
    /**
     * if true compute correlated ground motion field using both inter- and
     * intra-event residuals, if false use only intra-event residuals
     * (NOTE: this option has been done mostly for testing purposes,
     * some tests put this flag to false to check that the
     * correlation in the intra-event residuals in the ground motion
     * fiels is correclty computed). Default is true.
     */
    private boolean interEvent = true; 
    
    /**
     * Defines truncation level for covariance matrix calculation.
     * If distance between sites is greater than 
     * correlationTruncationLevel*correlationRange then automatically
     * set to zero correlation value
     */
    private double correlationTruncationLevel = 2.0;
    
    /**
     * Defines a ground motion field calculator
     * @param attenRel
     *            : {@link ScalarIntensityMeasureRelationshipAPI} attenuation
     *            relationship used for ground motion field calculation
     * @param rup
     *            : {@link EqkRupture} earthquake rupture generating the ground
     *            motion field
     * @param sites
     *            : array list of {@link Site} where ground motion values have
     *            to be computed
     */
    public GroundMotionFieldCalculator(ScalarIntensityMeasureRelationshipAPI attenRel, EqkRupture rup,
            List<Site> sites){
        validateInput(attenRel, rup, sites);
    	this.attenRel = attenRel;
    	this.rup = rup;
    	this.sites = sites;
    	// covariance matrix is set to null and defined only if correlated 
    	// ground motion fields calculations are requested
    	covarianceMatrix = null;
    }

    /**
     * Computes mean ground motion for a list of sites.
     * @return : {@link Map} associating sites ({@link Site}) and ground motion
     *         values {@link Double}
     */
    public Map<Site, Double> getMeanGroundMotionField() {
    	
    	logger.debug("Computing mean ground motion field...");
    	// get current time
    	long start = System.currentTimeMillis();
        
    	Map<Site, Double> groundMotionMap = new HashMap<Site, Double>();
        attenRel.setEqkRupture(rup);
        for (Site site : sites) {
            attenRel.setSite(site);
            groundMotionMap.put(site, new Double(attenRel.getMean()));
        
        }
        
        getAndPrintElapsedTime(start);
        
        return groundMotionMap;
    }

    /**
     * Computes uncorrelated ground motion field by adding to the mean ground
     * motion field Gaussian deviates which takes into account the truncation
     * level and the truncation type. If the attenuation relationship supports
     * inter and intra event standard deviations, the method computes ground
     * motion field by first generating the inter-event residual (same for all
     * the sites) and then sum the intra-event residuals (different for each
     * site), otherwise generate residuals for each site according to the total
     * standard deviation
     * @param rn
     *            : {@link Random} random number generator for Gaussian deviate
     *            calculation
     * @return: {@link Map} associating sites ({@link Site}) and ground motion
     *          values {@link Double}
     */
    public Map<Site, Double> getUncorrelatedGroundMotionField(Random rn) {
    	
    	logger.debug("Computing uncorrelated ground motion field...");
    	// get current time
    	long start = System.currentTimeMillis();
    	
        checkRandomNumberIsNotNull(rn);
        Map<Site, Double> groundMotionField =
                getMeanGroundMotionField();
        if (attenRel.getParameter(StdDevTypeParam.NAME).getConstraint()
                .isAllowed(StdDevTypeParam.STD_DEV_TYPE_INTER)
                && attenRel.getParameter(StdDevTypeParam.NAME).getConstraint()
                        .isAllowed(StdDevTypeParam.STD_DEV_TYPE_INTRA)) {
            computeAndAddInterEventResidual(rn,groundMotionField);
            computeAndAddSiteDependentResidual(rn,
                    groundMotionField,StdDevTypeParam.STD_DEV_TYPE_INTRA);
        } else {
            computeAndAddSiteDependentResidual(rn,
                    groundMotionField,StdDevTypeParam.STD_DEV_TYPE_TOTAL);
        }
        
        getAndPrintElapsedTime(start);
        
        return groundMotionField;
    }

    /**
     * Set GMPE standard deviation to inter-event, then stochastically generate
     * a single inter-event residual, and add this value to the already computed
     * ground motion values
     */
    private void computeAndAddInterEventResidual(
            Random rn, Map<Site, Double> groundMotionField) {
    	
    	logger.debug("Computing and adding inter event residual...");
    	// get current time
    	long start = System.currentTimeMillis();
    	
        attenRel.getParameter(StdDevTypeParam.NAME).setValue(
                StdDevTypeParam.STD_DEV_TYPE_INTER);
        double interEventResidual =
                getGaussianDeviate(attenRel.getStdDev(), (Double) attenRel
                        .getParameter(SigmaTruncLevelParam.NAME).getValue(),
                        (String) attenRel
                                .getParameter(SigmaTruncTypeParam.NAME)
                                .getValue(), rn);
        for (Site site : sites) {
            double val = groundMotionField.get(site);
            groundMotionField.put(site, val + interEventResidual);
        }
        
        getAndPrintElapsedTime(start);
    }

    /**
     * For each site stochastically generate deviate according to GMPE standard
     * deviation type (the site and earthquake information are also set because
     * the standard deviation may depend on the site-rupture distance, rupture
     * magnitude,..), and add to the already computed ground motion value
     */
    private void computeAndAddSiteDependentResidual(
            Random rn, Map<Site, Double> groundMotionField,
            String stdType) {
    	
    	logger.debug("Computing and adding "+stdType+" residual...");
    	// get current time
    	long start = System.currentTimeMillis();
    	
        attenRel.getParameter(StdDevTypeParam.NAME).setValue(stdType);
        attenRel.setEqkRupture(rup);
        for (Site site : sites) {
            attenRel.setSite(site);
            Double val = groundMotionField.get(site);
            double deviate =
                    getGaussianDeviate(
                            attenRel.getStdDev(),
                            (Double) attenRel.getParameter(
                                    SigmaTruncLevelParam.NAME).getValue(),
                            (String) attenRel.getParameter(
                                    SigmaTruncTypeParam.NAME).getValue(), rn);
            val = val + deviate;
            groundMotionField.put(site, val);
        }
        getAndPrintElapsedTime(start);
    }

    /**
     * Compute ground motion field with spatial correlation using
     * correlation model from Jayamram & Baker (2009):
     * "Correlation model for spatially distributed ground-motion intensities"
     * Nirmal Jayaram and Jack W. Baker, Earthquake Engng. Struct. Dyn (2009)
     * The algorithm is structured according to the following steps: 1) Compute
     * mean ground motion values, 2) Stochastically generate inter-event
     * residual (which follow a univariate normal distribution), 3)
     * Stochastically generate intra-event residuals (following the proposed
     * correlation model) 4) Combine the three terms generated in steps 1-3.
     * 
     * Intra-event residuals are calculated by generating Gaussian deviates from
     * a multivariate normal distribution using Cholesky factorization
     * (decompose covariance matrix, take lower triangular and multiply by a
     * vector of uncorrelated, standard Gaussian variables)

     * @param rn
     *            : {@link Random} random number generator
     * @return: {@link Map} associating sites ({@link Site}) and ground motion
     *          values {@link Double}
     */
    public Map<Site, Double> getCorrelatedGroundMotionField_JB2009(Random rn) {
    	
    	logger.debug("Computing correlated (JB2009) ground motion field...");
    	// get current time
    	long start = System.currentTimeMillis();
    	
        checkRandomNumberIsNotNull(rn);
        validateInputCorrelatedGmfCalc(attenRel);
        
        // covariance matrix is computed only once.
        // So if multiple ground motion fields are needed for 
        // the same rupture, the covariance matrix is not recomputed every time
        if(covarianceMatrix==null){
        	covarianceMatrix =
                getCovarianceMatrix_JB2009();
        }

        Map<Site, Double> groundMotionField =
                getMeanGroundMotionField();

        if (interEvent == true) {
            computeAndAddInterEventResidual(rn,groundMotionField);
        }

        computeAndAddCorrelatedIntraEventResidual(rn,
                groundMotionField);

        getAndPrintElapsedTime(start);

        return groundMotionField;
    }

    /**
     * Compute intra-event residuals, by decomposing the covariance matrix with
     * cholesky decomposition, and by multiplying the lower triangular matrix
     * with a vector of univariate Gaussian deviates
     */
    private void computeAndAddCorrelatedIntraEventResidual(
            Random rn, Map<Site, Double> groundMotionField) {
    	
    	logger.debug("Compute and add correlated and intra-event residuals...");
    	// get current time
    	long start = System.currentTimeMillis();

        int numberOfSites = sites.size();
        double[] gaussianDeviates = new double[numberOfSites];
        for (int i = 0; i < numberOfSites; i++) {
            gaussianDeviates[i] =
                    getGaussianDeviate(
                            1.0,
                            (Double) attenRel.getParameter(
                                    SigmaTruncLevelParam.NAME).getValue(),
                            (String) attenRel.getParameter(
                                    SigmaTruncTypeParam.NAME).getValue(), rn);
        }

        SparseDoubleCholeskyDecomposition cholDecomp = new SparseDoubleCholeskyDecomposition(covarianceMatrix, 0);
        DenseDoubleMatrix1D z = new DenseDoubleMatrix1D(gaussianDeviates.length);
        cholDecomp.getL().zMult(new DenseDoubleMatrix1D(gaussianDeviates), z);
        double[] intraEventResiduals = z.toArray();

        int indexSite = 0;
        for (Site site : sites) {
            double val = groundMotionField.get(site);
            groundMotionField.put(site, val + intraEventResiduals[indexSite]);
            indexSite = indexSite + 1;
        }

        getAndPrintElapsedTime(start);
    }

	private void
            validateInputCorrelatedGmfCalc(
                    ScalarIntensityMeasureRelationshipAPI attenRel) {
        if (attenRel.getParameter(StdDevTypeParam.NAME).getConstraint()
                        .isAllowed(StdDevTypeParam.STD_DEV_TYPE_INTER) == false) {
            throw new IllegalArgumentException(
                    "The specified attenuation relationship does not provide"
                            + " inter-event standard deviation");
        }
        if (attenRel.getParameter(StdDevTypeParam.NAME).getConstraint()
                .isAllowed(StdDevTypeParam.STD_DEV_TYPE_INTRA) == false) {
            throw new IllegalArgumentException(
                    "The specified attenuation relationship does not provide"
                            + " intra-event standard deviation");
        }
    }

    private void checkRandomNumberIsNotNull(Random rn) {
        if (rn == null) {
            throw new IllegalArgumentException(
                    "Random number generator cannot be null");
        }
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
    private double getGaussianDeviate(double standardDeviation,
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

     * @return covariance matrix as {@link SparseCCDoubleMatrix2D}
     */
    private SparseCCDoubleMatrix2D getCovarianceMatrix_JB2009() {
    	
    	logger.debug("Compute covariance matrix...");
    	// get current time
    	long start = System.currentTimeMillis();
    	
        int numberOfSites = sites.size();
        SparseCCDoubleMatrix2D covarianceMatrix = new SparseCCDoubleMatrix2D(numberOfSites, numberOfSites);
        attenRel.setEqkRupture(rup);
        attenRel.getParameter(StdDevTypeParam.NAME).setValue(
                StdDevTypeParam.STD_DEV_TYPE_INTRA);

        // default value for period is zero. Only if spectral acceleration
        // calculation is requested, the value of the period variable is
        // obtained from the attenRel object
        double period = 0.0;
        if (attenRel.getIntensityMeasure().getName()
                .equalsIgnoreCase(SA_Param.NAME)) {
            period =
                    (Double) attenRel.getParameter(PeriodParam.NAME).getValue();
        }

        double correlationRange = Double.NaN;
        if (period < 1 && JB2009_Vs30ClusterParam == false)
            correlationRange = 8.5 + 17.2 * period;
        else if (period < 1 && JB2009_Vs30ClusterParam == true)
            correlationRange = 40.7 - 15.0 * period;
        else if (period >= 1)
            correlationRange = 22.0 + 3.7 * period;
        double intraEventStd_i = Double.NaN;
        double intraEventStd_j = Double.NaN;
        double distance = Double.NaN;
        double covarianceValue = Double.NaN;
        for (int i=0;i<numberOfSites;i++) {
        	Site site_i = sites.get(i);
            attenRel.setSite(site_i);
            intraEventStd_i = attenRel.getStdDev();
            logger.debug("Covariance matrix row: "+(i+1)+" of "+numberOfSites);
            for (int j=i;j<numberOfSites;j++) {
            	Site site_j = sites.get(j);
                distance =
                    LocationUtils.horzDistance(site_i.getLocation(),
                            site_j.getLocation());
                if(distance>correlationTruncationLevel*correlationRange){
                	continue;
                }
                attenRel.setSite(site_j);
                intraEventStd_j = attenRel.getStdDev();
                covarianceValue =
                        intraEventStd_i * intraEventStd_j
                                * Math.exp(-3 * (distance / correlationRange));
                covarianceMatrix.setQuick(i, j, covarianceValue);
                covarianceMatrix.setQuick(j, i, covarianceValue);
            }
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

    public boolean isJB2009_Vs30ClusterParam() {
		return JB2009_Vs30ClusterParam;
	}

	public void setJB2009_Vs30ClusterParam(boolean jB2009_Vs30ClusterParam) {
		JB2009_Vs30ClusterParam = jB2009_Vs30ClusterParam;
	}

	public boolean isInterEvent() {
		return interEvent;
	}

	public void setInterEvent(boolean interEvent) {
		this.interEvent = interEvent;
	}	

    public double getCorrelationTruncationLevel() {
		return correlationTruncationLevel;
	}

	public void setCorrelationTruncationLevel(double correlationTruncationLevel) {
		this.correlationTruncationLevel = correlationTruncationLevel;
	}

	
	private void getAndPrintElapsedTime(long start) {
		// get elapsed time in milliseconds
        long elapsedTimeMillis = System.currentTimeMillis()-start;
        // get elapsed time in seconds
        float elapsedTimeSec = elapsedTimeMillis/1000F;
        // get elapsed time in minutes
        float elapsedTimeMin = elapsedTimeMillis/(60*1000F);
        logger.debug("Elapsed time (s): "+elapsedTimeSec);
        logger.debug("Elapsed time (min): "+elapsedTimeMin+"\n");
	}

}
