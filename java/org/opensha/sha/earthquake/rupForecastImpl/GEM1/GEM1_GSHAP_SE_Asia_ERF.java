package org.opensha.sha.earthquake.rupForecastImpl.GEM1;

import java.io.FileNotFoundException;
import java.io.IOException;

import org.opensha.gem.GEM1.calc.gemModelParsers.gshap.south_east_asia.GshapSEAsia2GemSourceData;
import org.opensha.gem.GEM1.commons.CalculationSettings;

public class GEM1_GSHAP_SE_Asia_ERF extends GEM1ERF {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	public final static String NAME = "GEM1 GSHAP SE Asia ERF";
	
	
	public GEM1_GSHAP_SE_Asia_ERF() {
		this(null);
	}
	
	public GEM1_GSHAP_SE_Asia_ERF(CalculationSettings calcSet) {
		try {
			this.areaSourceDataList = new GshapSEAsia2GemSourceData().getList();
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
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
		GEM1_GSHAP_SE_Asia_ERF erf = null;
		erf = new GEM1_GSHAP_SE_Asia_ERF();
		erf.updateForecast();
		double runtime = (System.currentTimeMillis() - time)/1000;
		System.out.println("Done with Data Creation in "+(float) runtime+" seconds)");
	}


}
