package org.gem.calc;

import java.rmi.RemoteException;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

import org.apache.commons.collections.Closure;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.DepthTo1pt0kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.DepthTo2pt5kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.imr.param.SiteParams.Vs30_TypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_TypeParam.Vs30Type;
import org.opensha.sha.util.TectonicRegionType;
import static org.gem.Utils.digitize;
import static org.gem.calc.CalcUtils.assertPoissonian;
import static org.gem.calc.CalcUtils.getGMV;
import static org.gem.calc.CalcUtils.notNull;
import static org.gem.calc.CalcUtils.isSorted;
import static org.gem.calc.CalcUtils.lenGE;
import static org.apache.commons.collections.CollectionUtils.forAllDo;

import org.gem.calc.DisaggregationResult;

public class DisaggregationCalculator {

    /**
     * Dataset for the full disagg matrix (for HDF5 ouput).
     */
    public static final String FULLDISAGGMATRIX = "fulldisaggmatrix";
    private final Double[] latBinLims;
    private final Double[] lonBinLims;
    private final Double[] magBinLims;
    private final Double[] epsilonBinLims;
    private static final TectonicRegionType[] tectonicRegionTypes = TectonicRegionType.values();
    /**
     * Dimensions for matrices produced by this calculator, based on the length
     * of the bin limits passed to the constructor.
     */
    private final long[] dims;

    public DisaggregationCalculator(
            Double[] latBinEdges,
            Double[] lonBinEdges,
            Double[] magBinEdges,
            Double[] epsilonBinEdges)
    {
        List binEdges = Arrays.asList(latBinEdges, lonBinEdges, magBinEdges,
                  epsilonBinEdges);

        // Validation for the bin edges:
        forAllDo(binEdges, notNull);
        forAllDo(binEdges, lenGE(2));
        forAllDo(binEdges, isSorted);

        this.latBinLims = latBinEdges;
        this.lonBinLims = lonBinEdges;
        this.magBinLims = magBinEdges;
        this.epsilonBinLims = epsilonBinEdges;

        this.dims = new long[5];
        this.dims[0] = this.latBinLims.length - 1;
        this.dims[1] = this.lonBinLims.length - 1;
        this.dims[2] = this.magBinLims.length - 1;
        this.dims[3] = this.epsilonBinLims.length - 1;
        this.dims[4] = tectonicRegionTypes.length;
    }

    /**
     * Simplified computeMatrix method for convenient calls from the Python
     * code.
     */
    public DisaggregationResult computeMatrix(
            double lat,
            double lon,
            GEM1ERF erf,
            Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap,
            double poe,
            List<Double> imls,
            String vs30Type,
            double vs30Value,
            double depthTo1pt0KMPS,
            double depthTo2pt5KMPS)
    {
        assertVs30TypeIsValid(vs30Type);
        Site site = new Site(new Location(lat, lon));
        site.addParameter(new StringParameter(Vs30_TypeParam.NAME, vs30Type));
        site.addParameter(new DoubleParameter(Vs30_Param.NAME, vs30Value));
        site.addParameter(new DoubleParameter(DepthTo1pt0kmPerSecParam.NAME, depthTo1pt0KMPS));
        site.addParameter(new DoubleParameter(DepthTo2pt5kmPerSecParam.NAME, depthTo2pt5KMPS));

        DiscretizedFuncAPI hazardCurve = new ArbitrarilyDiscretizedFunc();
        // initialize the hazard curve with the number of points == the number of IMLs
        for (double d : imls)
        {
            hazardCurve.set(d, 1.0);
        }

        try
        {
            HazardCurveCalculator hcc = new HazardCurveCalculator();
            hcc.getHazardCurve(hazardCurve, site, imrMap, erf);
        } 
        catch (RemoteException e)
        {
            throw new RuntimeException(e);
        }

        double minMag = (Double) erf.getParameter(GEM1ERF.MIN_MAG_NAME).getValue();

        return computeMatrix(site, erf, imrMap, poe, hazardCurve, minMag);
    }

    public DisaggregationResult computeMatrix(
            Site site,
            EqkRupForecastAPI erf,
            Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap,
            double poe,
            DiscretizedFuncAPI hazardCurve,
            double minMag)
    {

        assertPoissonian(erf);
        assertNonZeroStdDev(imrMap);

        double disaggMatrix[][][][][] =
                new double[(int) dims[0]]
                          [(int) dims[1]]
                          [(int) dims[2]]
                          [(int) dims[3]]
                          [(int) dims[4]];

        // value by which to normalize the final matrix
        double totalAnnualRate = 0.0;

        double logGMV = getGMV(hazardCurve, poe);

        for (int srcCnt = 0; srcCnt < erf.getNumSources(); srcCnt++)
        {
            ProbEqkSource source = erf.getSource(srcCnt);

            double totProb = source.computeTotalProbAbove(minMag);
            double totRate = -Math.log(1 - totProb);

            TectonicRegionType trt = source.getTectonicRegionType();

            ScalarIntensityMeasureRelationshipAPI imr = imrMap.get(trt);
            imr.setSite(site);
            imr.setIntensityMeasureLevel(logGMV);

            for(int rupCnt = 0; rupCnt < source.getNumRuptures(); rupCnt++)
            {
                ProbEqkRupture rupture = source.getRupture(rupCnt);
                imr.setEqkRupture(rupture);

                Location location = closestLocation(rupture.getRuptureSurface().getLocationList(), site.getLocation());

                double lat, lon, mag, epsilon;
                lat = location.getLatitude();
                lon = location.getLongitude();
                mag = rupture.getMag();
                epsilon = imr.getEpsilon();

                if (!allInRange(lat, lon, mag, epsilon))
                {
                    // one or more of the parameters is out of range;
                    // skip this rupture
                    continue;
                }

                int[] binIndices = getBinIndices(lat, lon, mag, epsilon, trt);

                double annualRate = totRate
                        * imr.getExceedProbability()
                        * rupture.getProbability();

                disaggMatrix[binIndices[0]][binIndices[1]][binIndices[2]][binIndices[3]][binIndices[4]] += annualRate;
                totalAnnualRate += annualRate;
            }  // end rupture loop
        }  // end source loop

        disaggMatrix = normalize(disaggMatrix, totalAnnualRate);

        DisaggregationResult daResult = new DisaggregationResult();
        daResult.setGMV(Math.exp(logGMV));
        daResult.setMatrix(disaggMatrix);
        return daResult;
    }

    public boolean allInRange(
            double lat, double lon, double mag, double epsilon)
    {
        return inRange(this.latBinLims, lat)
                && inRange(this.lonBinLims, lon)
                && inRange(this.magBinLims, mag)
                && inRange(this.epsilonBinLims, epsilon);
    }

    public static void assertNonZeroStdDev(
            Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap)
    {
        for (ScalarIntensityMeasureRelationshipAPI imr : imrMap.values())
        {
            String stdDevType =
                    (String) imr.getParameter(StdDevTypeParam.NAME).getValue();
            if (stdDevType.equalsIgnoreCase(StdDevTypeParam.STD_DEV_TYPE_NONE))
            {
                throw new RuntimeException(
                        "Attenuation relationship must have a non-zero standard deviation.");
            }
        }
    }

    public static void assertVs30TypeIsValid(String vs30Type) {
        try {
            Vs30Type.valueOf(vs30Type);
        }
        catch (IllegalArgumentException e) {
            throw new RuntimeException(e);
        }
    }

    public static boolean inRange(Double[] bins, Double value)
    {
        return value >= bins[0] && value < bins[bins.length - 1];
    }

    /**
     * Figure out which bins each input parameter fits into. The returned array
     * of indices represent the 5 dimensional coordinates in the disaggregation
     * matrix.
     * @param lat
     * @param lon
     * @param mag
     * @param epsilon
     * @param trt
     */
    public int[] getBinIndices(
            double lat, double lon, double mag,
            double epsilon, TectonicRegionType trt)
    {
        int[] result = new int[5];
        result[0] = digitize(this.latBinLims, lat);
        result[1] = digitize(this.lonBinLims, lon);
        result[2] = digitize(this.magBinLims, mag);
        result[3] = digitize(this.epsilonBinLims, epsilon);
        result[4] = Arrays.asList(TectonicRegionType.values()).indexOf(trt);

        return result;
    }

    /**
     * Given a LocationList and a Location target, get the Location in the
     * LocationList which is closest to the target Location.
     * @param list
     * @param target
     * @return closest Location (in the input ListLocation) to the target
     */
    public static Location closestLocation(LocationList list, Location target)
    {
        Location closest = null;

        double minDistance = Double.MAX_VALUE;

        for (Location loc : list)
        {
            double horzDist = LocationUtils.horzDistance(loc, target);
            double vertDist = LocationUtils.vertDistance(loc, target);
            double distance = Math.sqrt(Math.pow(horzDist, 2) + Math.pow(vertDist, 2));
            if (distance < minDistance)
            {
                minDistance = distance;
                closest = loc;
            }
        }
        return closest;
    }

    /**
     * Normalize a 5D matrix by the given value.
     * @param matrix
     * @param normFactor
     */
    public static double[][][][][] normalize(double[][][][][] matrix, double normFactor)
    {
        for (int i = 0; i < matrix.length; i++)
        {
            for (int j = 0; j < matrix[i].length; j++)
            {
                for (int k = 0; k < matrix[i][j].length; k++)
                {
                    for (int l = 0; l < matrix[i][j][k].length; l++)
                    {
                        for (int m = 0; m < matrix[i][j][k][l].length; m++)
                        {
                            matrix[i][j][k][l][m] /= normFactor;
                        }
                    }
                }
            }
        }
        return matrix;
    }
}
