package org.gem.calc;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

import org.apache.commons.collections.Closure;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TectonicRegionType;
import static org.apache.commons.collections.CollectionUtils.forAllDo;

public class DisaggregationCalculator {

	private final Double[] latBinLims;
	private final Double[] lonBinLims;
	private final Double[] magBinLims;
	private final Double[] epsilonBinLims;
	private final Double[] distanceBinLims;
	private String[] tectonicRegionTypes; // these are hardcoded: TectonicRegionType.values();

	/**
	 * Used for checking that bin edge lists are not null;
	 */
	private static final Closure NOT_NULL = new Closure()
	{

		public void execute(Object o)
		{
			if (o == null)
			{
				throw new IllegalArgumentException("Bin edges should not be null");
			}
		}
	};

	/**
	 * Used for checking that bin edge lists have a length greater than or equal
	 * to 2.
	 */
	private static final Closure LEN_GE_2 = new Closure()
	{

		public void execute(Object o)
		{
			if (o instanceof Object[])
			{
				Object[] oArray = (Object[]) o;
				if (oArray.length < 2)
				{
					throw new IllegalArgumentException("Bin edge arrays must have a length >= 2");
				}
			}
		}
	};

	public DisaggregationCalculator(
			Double[] latBinEdges,
			Double[] lonBinEdges,
			Double[] magBinEdges,
			Double[] epsilonBinEdges,
			Double[] distanceBinEdges)
	{
		List binEdges = Arrays.asList(latBinEdges, lonBinEdges, magBinEdges,
				  epsilonBinEdges, distanceBinEdges);

		// Validation for the bin edges:
		forAllDo(binEdges, NOT_NULL); // TODO: need constructor test
		forAllDo(binEdges, LEN_GE_2); // TODO: need constructor test

		this.latBinLims = latBinEdges;
		this.lonBinLims = lonBinEdges;
		this.magBinLims = magBinEdges;
		this.epsilonBinLims = epsilonBinEdges;
		this.distanceBinLims = distanceBinEdges;
	}

	public double[][][][][] computeMatrix(
			Site site,
			EqkRupForecastAPI erf,
			Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap,
			double poe,
			DiscretizedFuncAPI hazardCurve) // or just pass a List<double> of IML values and compute the curve inside here?
	{
		/*

		disaggMatrix[][][][][]
		totalAnnualRate = 0.0

		for source in erf.sources:
			imr = imrMap.getIMR(source.getTRT())
			
			for rupture in source.ruptures:
				closestLoc = getClosestLoc(site, rupture.getSurfaces())
				
				lat = closestLoc.getLat()
				lon = closestLoc.getLon()
				mag = rupture.getMag()
				epsilon = imr.getEpsilon()
				trt = source.getTRT()

				// if the these values are outside the bin
				// ranges, 'continue' to the next loop iter

				// get the bin indices from these 5,
				// given the defined bin limits

				annualRate = totRate * imr.getExceedProb() * rup.getProbability()

				disaggMatrix[binIndices] += annualRate

				totalAnnualRate += annualRate

		// normalize the disagg matrix by the totalAnnualRate

		return disaggMatrix




		 */
		
		
		
		return null;
	}
}
