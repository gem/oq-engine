package org.opensha.sha.calc.groundMotionField;

import static org.junit.Assert.assertEquals;

import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Iterator;
import java.util.Random;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.gem.GEM1.scratch.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

public class GroundMotionFieldCalculatorTest implements
		ParameterChangeWarningListener {

	private DiscretizedFuncAPI iml;
	private Site site;
	private ScalarIntensityMeasureRelationshipAPI imr;
	private EqkRupture rupture;
	
	// in percentage
	double tolerance = 1;

	@Test
	public void compareHazardCurvesForSingleEarthquakeRupture() {

		long seed = 123456789;
		int numRealizations = 50000;
		String truncationType = SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE;
		double truncationLevel = 1.0;

		setIml();
		setSite();
		setImr(truncationType, truncationLevel);
		setEqkRup();

		// calculate hazard curve following classical approach
		try {
			HazardCurveCalculator hcc = new HazardCurveCalculator();
			hcc.getHazardCurve(iml, site, imr, rupture);
		} catch (RemoteException e) {
			e.printStackTrace();
		}

		// calculate hazard curve by generating multiple ground motion fields
		Random rn = new Random(seed);
		ArrayList<Site> sites = new ArrayList<Site>();
		sites.add(site);
		ArrayList<Double> groundMotionValues = new ArrayList<Double>();
		for (int i = 0; i < numRealizations; i++)
			groundMotionValues.add(GroundMotionFieldCalculator
					.getStochasticGroundMotionField(imr, rupture, sites, rn)
					.get(site));
		Comparator comparator = Collections.reverseOrder();
		Collections.sort(groundMotionValues,comparator);
		double[] probabilityOfExceedenceVals = new double[iml.getNum()];
		for (int i = 0; i < iml.getNum(); i++)
			probabilityOfExceedenceVals[i] = 0.0;
		Iterator<Double> iterGMV = iml.getXValuesIterator();
		int indexGMV = 0;
		while (iterGMV.hasNext()) {
			double groundMotionValue = iterGMV.next();
			for (int i = 0; i < groundMotionValues.size(); i++)
				if (groundMotionValues.get(i) > groundMotionValue)
					probabilityOfExceedenceVals[indexGMV] = probabilityOfExceedenceVals[indexGMV] + 1;
				else break;
			indexGMV = indexGMV + 1;
		}
		for (int i = 0; i < iml.getNum(); i++)
			probabilityOfExceedenceVals[i] = probabilityOfExceedenceVals[i]
					/ numRealizations;
		
		for (int i = 0; i < iml.getNum(); i++){
			double expected = iml.getY(i);
			double computed = probabilityOfExceedenceVals[i];
			System.out.println("Expected: "+expected+" "+", computed: "+computed+", percentage difference: "+Math.abs((computed-expected)/expected)*100);
			//assertEquals(100, (computed / expected) * 100,
				//	tolerance);
		}

	}

	private void setIml() {
		this.iml = new ArbitrarilyDiscretizedFunc();
		this.iml.set(Math.log(0.005), 1.0);
		this.iml.set(Math.log(0.007), 1.0);
		this.iml.set(Math.log(0.0098), 1.0);
		this.iml.set(Math.log(0.0137), 1.0);
		this.iml.set(Math.log(0.0192), 1.0);
		this.iml.set(Math.log(0.0269), 1.0);
		this.iml.set(Math.log(0.0376), 1.0);
		this.iml.set(Math.log(0.0527), 1.0);
		this.iml.set(Math.log(0.0738), 1.0);
		this.iml.set(Math.log(0.103), 1.0);
		this.iml.set(Math.log(0.145), 1.0);
		this.iml.set(Math.log(0.203), 1.0);
		this.iml.set(Math.log(0.284), 1.0);
		this.iml.set(Math.log(0.397), 1.0);
		this.iml.set(Math.log(0.556), 1.0);
		this.iml.set(Math.log(0.778), 1.0);
		this.iml.set(Math.log(1.09), 1.0);
		this.iml.set(Math.log(1.52), 1.0);
		this.iml.set(Math.log(2.13), 1.0);
	}

	private void setSite() {
		Site site = new Site(new Location(33.8, -117.4));
		site.addParameter(new DoubleParameter(Vs30_Param.NAME, 760.0));
		this.site = site;
	}

	private void setImr(String truncationType, double truncationLevel) {
		this.imr = new BA_2008_AttenRel(this);
		this.imr.setParamDefaults();
		this.imr.getParameter(SigmaTruncTypeParam.NAME)
				.setValue(truncationType);
		this.imr.getParameter(SigmaTruncLevelParam.NAME).setValue(
				truncationLevel);
		this.imr.setIntensityMeasure(PGA_Param.NAME);
	}

	private void setEqkRup() {
		double aveDip = 90.0;
		double lowerSeisDepth = 13.0;
		double upperSeisDepth = 0.0;
		FaultTrace trace = new FaultTrace("Elsinore;GI");
		trace.add(new Location(33.82890, -117.59000));
		trace.add(new Location(33.81290, -117.54800));
		trace.add(new Location(33.74509, -117.46332));
		trace.add(new Location(33.73183, -117.44568));
		trace.add(new Location(33.71851, -117.42415));
		trace.add(new Location(33.70453, -117.40265));
		trace.add(new Location(33.68522, -117.37270));
		trace.add(new Location(33.62646, -117.27443));
		double gridSpacing = 1.0;
		double mag = 6.889;
		double aveRake = 0.0;
		Location hypo = new Location(33.73183, -117.44568, 6.5);
		this.rupture = getFiniteEqkRupture(aveDip, lowerSeisDepth,
				upperSeisDepth, trace, gridSpacing, mag, hypo, aveRake);
	}

	/*
	 * Creates an EqkRupture object for a finite source.
	 */
	private EqkRupture getFiniteEqkRupture(double aveDip,
			double lowerSeisDepth, double upperSeisDepth,
			FaultTrace faultTrace, double gridSpacing, double mag,
			Location hypo, double aveRake) {
		StirlingGriddedSurface rupSurf = new StirlingGriddedSurface(faultTrace,
				aveDip, upperSeisDepth, lowerSeisDepth, gridSpacing);
		EqkRupture rup = new EqkRupture(mag, aveRake, rupSurf, hypo);
		return rup;
	}

	public void parameterChangeWarning(ParameterChangeWarningEvent event) {
	}

}
