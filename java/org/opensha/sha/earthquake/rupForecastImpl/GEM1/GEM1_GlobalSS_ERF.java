package org.opensha.sha.earthquake.rupForecastImpl.GEM1;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpCeusFaultData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpCeusGridData;
import org.opensha.gem.GEM1.calc.gemModelParsers.forecastML.ForecastML2GemSourceData;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class GEM1_GlobalSS_ERF extends GEM1ERF {

	private static final long serialVersionUID = 1L;

	public static final String NAME = "GEM1 Global Smoothed Seismicity ERF";

	public static final String inputFile = "/org/opensha/gem/GEM1/data/" +
	"global_smooth_seismicity/zechar.triple_s.global.rate_forecast.xml";

	public GEM1_GlobalSS_ERF() {
		this(null);
	}

	public GEM1_GlobalSS_ERF(CalculationSettings calcSet) {

		ArrayList<GEMSourceData> list=null;
		try {
			list = new ForecastML2GemSourceData(inputFile).getList();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		this.parseSourceListIntoDifferentTypes(list);
		
		this.initialize(calcSet);
	}


	@Override
	public String getName() {
		return NAME;
	}

	// this is temporary for testing purposes
	public static void main(String[] args) {
		double time = System.currentTimeMillis();
		System.out.println("Starting Data Creation");
		GEM1_GlobalSS_ERF erf = null;
		erf = new GEM1_GlobalSS_ERF();
		erf.updateForecast();
		double runtime = (System.currentTimeMillis() - time)/1000;
		System.out.println("Done with Data Creation in "+(float) runtime+" seconds)");
	}

}


