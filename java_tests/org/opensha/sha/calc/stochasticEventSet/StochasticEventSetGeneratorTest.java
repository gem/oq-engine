package org.opensha.sha.calc.stochasticEventSet;

import static org.junit.Assert.assertEquals;

import java.util.ArrayList;
import java.util.Random;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class StochasticEventSetGeneratorTest {

	// in percent
	double tolerance = 5;

	@Test
	public void compareOccurrenceRatesWithGetStochasticEvenSetFromPoissonianERF() {

		/**
		 * This test compares the occurrence rates calculated from a set of
		 * stochastic events (each generated using the method
		 * getStochasticEvenSetFromPoissonianERF() called by the method
		 * getMultipleStochasticEvenSetsFromPoissonianERF()) with those given in
		 * input in the definition of the ERF. The outcome of the test depends
		 * on the number of stochastic sets generated (if the generator is
		 * correctly implemented, greater is the number of sets, better will be
		 * the consistency between expected and computed results) and on the
		 * seed number for the random number generator.
		 */

		int numStochasticEventSets = 50000;
		long seed = 123456789;

		// Define source
		GEMFaultSourceData src = getExampleFaultSource();

		// Define ERF
		double timeSpan = 50.0;
		ArrayList<GEMSourceData> faultSourceDataList = new ArrayList<GEMSourceData>();
		faultSourceDataList.add(src);
		GEM1ERF erf = getGEM1ERF(faultSourceDataList, timeSpan);

		// Calculate stochastic event sets
		Random rn = new Random(seed);
		ArrayList<ArrayList<ProbEqkRupture>> multiStochasticEventSets = StochasticEventSetGeneratorDamiano
				.getMultipleStochasticEvenSetsFromPoissonianERF(erf,
						numStochasticEventSets, rn);
		ArrayList<ProbEqkRupture> stochasticEventSet = new ArrayList<ProbEqkRupture>();
		for (ArrayList<ProbEqkRupture> ses : multiStochasticEventSets)
			stochasticEventSet.addAll(ses);

		// Compare rates
		IncrementalMagFreqDist mfd = src.getMfd();
		compareOccurrenceRates(mfd, stochasticEventSet, timeSpan,
				numStochasticEventSets);

	}
	
	@Test
	public void compareOccurrenceRatesWithGetStochasticEvenSetFromGEM1ERF() {

		/**
		 * This test compares the occurrence rates calculated from a set of
		 * stochastic events (each generated using the method
		 * getStochasticEvenSetFromGEM1ERF() called by the method
		 * getMultipleStochasticEvenSetsFromGEM1ERF()) with those given in
		 * input in the definition of the ERF. The outcome of the test depends
		 * on the number of stochastic sets generated (if the generator is
		 * correctly implemented, greater is the number of sets, better will be
		 * the consistency between expected and computed results) and on the
		 * seed number for the random number generator.
		 */

		int numStochasticEventSets = 10;//50000;
		long seed = 123456789;

		// Define source
		GEMFaultSourceData src = getExampleFaultSource();

		// Define ERF
		double timeSpan = 50.0;
		ArrayList<GEMSourceData> faultSourceDataList = new ArrayList<GEMSourceData>();
		faultSourceDataList.add(src);
		GEM1ERF erf = getGEM1ERF(faultSourceDataList, timeSpan);

		// Calculate stochastic event sets
		Random rn = new Random(seed);
		ArrayList<ArrayList<ProbEqkRupture>> multiStochasticEventSets = StochasticEventSetGeneratorDamiano
				.getMultipleStochasticEvenSetsFromGEM1ERF(erf,
						numStochasticEventSets, rn);
		ArrayList<ProbEqkRupture> stochasticEventSet = new ArrayList<ProbEqkRupture>();
		for (ArrayList<ProbEqkRupture> ses : multiStochasticEventSets)
			stochasticEventSet.addAll(ses);

		// Compare rates
		IncrementalMagFreqDist mfd = src.getMfd();
		compareOccurrenceRates(mfd, stochasticEventSet, timeSpan,
				numStochasticEventSets);

	}

	/**
	 * This method return an example of fault source (taken from California
	 * NSHMP Model, bFault_stitched_D2.1_GR0.in)
	 * 
	 * @return
	 */
	private GEMFaultSourceData getExampleFaultSource() {
		String id = "1";
		String name = "San Cayetano";
		TectonicRegionType tectReg = TectonicRegionType.ACTIVE_SHALLOW;
		double aVal = 2.4992683;
		double bVal = 0.8;
		double mMin = 6.5;
		double mMax = 7.2;
		double dM = 0.1;
		mMin = mMin + dM / 2;
		mMax = mMax - dM / 2;
		int numMag = (int) ((mMax - mMin) / dM + 1);
		double tmr = totMoRate(mMin, numMag, dM, aVal, bVal);
		GutenbergRichterMagFreqDist mfd = new GutenbergRichterMagFreqDist(mMin,
				numMag, dM);
		mfd.setAllButTotCumRate(mMin, mMax, tmr, bVal);
		FaultTrace trc = new FaultTrace(name);
		trc.add(new Location(34.43610, -118.76200));
		trc.add(new Location(34.40470, -118.83100));
		trc.add(new Location(34.40210, -118.86500));
		trc.add(new Location(34.41725, -118.91304));
		trc.add(new Location(34.42704, -118.92385));
		trc.add(new Location(34.44946, -118.92792));
		trc.add(new Location(34.44841, -118.94363));
		trc.add(new Location(34.42210, -118.97685));
		trc.add(new Location(34.42178, -119.00752));
		trc.add(new Location(34.42294, -119.03671));
		trc.add(new Location(34.43573, -119.08182));
		trc.add(new Location(34.43289, -119.10376));
		trc.add(new Location(34.44997, -119.15906));
		double dip = 42.0;
		double rake = 90.0;
		double seismDepthLow = 24.0;
		double seismDepthUpp = 0.0;
		boolean floatRuptureFlag = true;
		GEMFaultSourceData src = new GEMFaultSourceData(id, name, tectReg, mfd,
				trc, dip, rake, seismDepthLow, seismDepthUpp, floatRuptureFlag);
		return src;
	}

	/**
	 * This test provide a GEM1ERF given an array list of GEMSourceData
	 * 
	 * @param sourceDataList
	 * @param timeSpan
	 * @return
	 */
	private GEM1ERF getGEM1ERF(ArrayList<GEMSourceData> sourceDataList,
			double timeSpan) {
		TimeSpan tms = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
		tms.setDuration(timeSpan);
		GEM1ERF erf = new GEM1ERF(sourceDataList);
		erf.setTimeSpan(tms);
		erf.updateForecast();
		return erf;
	}

	/**
	 * compute total moment rate as done by NSHMP code
	 * 
	 * @param minMag
	 *            : minimum magnitude (rounded to multiple of deltaMag and moved
	 *            to bin center)
	 * @param numMag
	 *            : number of magnitudes
	 * @param deltaMag
	 *            : magnitude bin width
	 * @param aVal
	 *            : incremental a value (defined with respect to deltaMag)
	 * @param bVal
	 *            : b value
	 * @return
	 */

	private double totMoRate(double minMag, int numMag, double deltaMag,
			double aVal, double bVal) {
		double moRate = 0;
		double mag;
		for (int imag = 0; imag < numMag; imag++) {
			mag = minMag + imag * deltaMag;
			moRate += Math.pow(10, aVal - bVal * mag + 1.5 * mag + 9.05);
		}
		return moRate;
	}

	/**
	 * Compare occurrence rates with those calculated from multiple stochastic
	 * event sets
	 * 
	 * @param mfd
	 *            {@link IncrementalMagFreqDist} containing expected occurrence
	 *            rates
	 * @param stochasticEventSet
	 *            {@link ArrayList} of {@link ProbEqkRupture} containing events
	 *            from multiple stochastic event sets
	 * @param timeSpan
	 *            double time span of the ERF
	 * @param numStochasticEventSets
	 *            number of stochastic even sets generated
	 */
	private void compareOccurrenceRates(IncrementalMagFreqDist mfd,
			ArrayList<ProbEqkRupture> stochasticEventSet, double timeSpan,
			int numStochasticEventSets) {
		// Compare rates
		double mag = Double.NaN;
		double stochasticRate = Double.NaN;
		double stochasticRateExpected = Double.NaN;
		double percentageDifference = Double.NaN;
		for (int i = 0; i < mfd.getNum(); i++) {
			mag = mfd.getX(i);
			stochasticRate = 0;
			for (int j = 0; j < stochasticEventSet.size(); j++)
				if (stochasticEventSet.get(j).getMag() == mag)
					stochasticRate = stochasticRate + 1;
			stochasticRate = stochasticRate
					/ (timeSpan * numStochasticEventSets);
			stochasticRateExpected = mfd.getY(i);
			percentageDifference = Math
					.abs(((stochasticRateExpected - stochasticRate) / stochasticRateExpected) * 100);
			System.out.println("Expected: " + stochasticRateExpected
					+ ", calculated: " + stochasticRate
					+ ", percentage difference: " + percentageDifference);
			//assertEquals(100, (stochasticRate / stochasticRateExpected) * 100,
				//	tolerance);
		}
	}

}
