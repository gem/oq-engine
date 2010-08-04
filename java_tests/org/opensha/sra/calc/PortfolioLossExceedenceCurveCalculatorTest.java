package org.opensha.sra.calc;


import java.util.ListIterator;

import org.junit.BeforeClass;
import org.junit.Test;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.earthquake.ERFTestSubset;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_AdjustableEqkRupForecast;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sra.asset.Asset;
import org.opensha.sra.asset.AssetCategory;
import org.opensha.sra.asset.MonetaryHighLowValue;
import org.opensha.sra.asset.MonetaryValue;
import org.opensha.sra.asset.Portfolio;
import org.opensha.sra.vulnerability.Vulnerability;
import org.opensha.sra.vulnerability.models.servlet.VulnerabilityServletAccessor;

public class PortfolioLossExceedenceCurveCalculatorTest {

	private static EqkRupForecastAPI erf;
	private static ScalarIntensityMeasureRelationshipAPI imr;
	private static Portfolio portfolio;
	
	private static boolean smallERF = true;
	
	@BeforeClass
	public static void setUp() throws Exception {
		if (smallERF) {
			ERFTestSubset erf = new ERFTestSubset(new Frankel96_AdjustableEqkRupForecast());
			erf.updateForecast();
			erf.includeSource(0);
			erf.includeSource(1);
			erf.includeSource(2);
			erf.includeSource(3);
			erf.includeSource(4);
			erf.includeSource(5);
			erf.includeSource(6);
			erf.includeSource(7);
			erf.includeSource(8);
			erf.includeSource(9);
			PortfolioLossExceedenceCurveCalculatorTest.erf = erf;
		} else {
			Frankel96_AdjustableEqkRupForecast erf = new Frankel96_AdjustableEqkRupForecast();
			erf.updateForecast();
			PortfolioLossExceedenceCurveCalculatorTest.erf = erf;
		}

		
		int rupCount = 0;
		for (int sourceID=0; sourceID<erf.getNumSources(); sourceID++) {
			rupCount += erf.getNumRuptures(sourceID);
		}
		
		System.out.println("num sources: " + erf.getNumSources() + ", num rups: " + rupCount);
		
		imr = new CB_2008_AttenRel(null);
		imr.setParamDefaults();
		
		portfolio = new Portfolio("Test Portfolio");
		
		VulnerabilityServletAccessor accessor = new VulnerabilityServletAccessor();
		
		MonetaryValue value1 = new MonetaryHighLowValue(220000.0, 330000.0, 110000.0, 2007);
		Site site1 = new Site(new Location(33.15, -118.12));
		Vulnerability vuln1 = accessor.getVuln("C1H-h-AGR1-DF");
		
		MonetaryValue value2 = new MonetaryHighLowValue(200000.0, 300000.0, 100000.0, 2004);
		Site site2 = new Site(new Location(33.11, -118.19));
		Vulnerability vuln2 = accessor.getVuln("C1H-h-COM10-DF");
		
		ListIterator<ParameterAPI<?>> it = imr.getSiteParamsIterator();
		while (it.hasNext()) {
			ParameterAPI<?> param = it.next();
			site1.addParameter((ParameterAPI)param.clone());
			site2.addParameter((ParameterAPI)param.clone());
		}
		
		Asset asset1 = new Asset(0, "House 1", AssetCategory.BUILDING, value1, vuln1, site1);
		portfolio.add(asset1);
		Asset asset2 = new Asset(1, "House 2", AssetCategory.BUILDING, value2, vuln2, site2);
		portfolio.add(asset2);
	}
	
	@Test
	public void testCalc() {
		PortfolioLossExceedenceCurveCalculator calc = new PortfolioLossExceedenceCurveCalculator();
		
		ArbitrarilyDiscretizedFunc curve = calc.calcProbabilityOfExceedanceCurve(imr, erf, portfolio, null);
		System.out.println(curve);
	}

}
