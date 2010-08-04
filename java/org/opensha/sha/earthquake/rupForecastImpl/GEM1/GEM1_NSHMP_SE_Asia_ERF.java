package org.opensha.sha.earthquake.rupForecastImpl.GEM1;

import java.io.FileNotFoundException;
import java.io.IOException;

import org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_east_asia.NshmpSouthEastAsiaData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_east_asia.NshmpSouthEastAsiaFaultData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_east_asia.NshmpSouthEastAsiaGridData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_east_asia.NshmpSouthEastAsiaSubductionData;
import org.opensha.gem.GEM1.commons.CalculationSettings;

public class GEM1_NSHMP_SE_Asia_ERF extends GEM1ERF {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	public final static String NAME = "GEM1 GSHAP SE Asia ERF";
	
	private static double default_latmin = -55;
	private static double default_latmax = 15;
	private static double default_lonmin = -85;
	private static double default_lonmax = -30;
	
	public GEM1_NSHMP_SE_Asia_ERF() {
		this(null);
	}
	
	public GEM1_NSHMP_SE_Asia_ERF(CalculationSettings calcSet) {
		this(default_latmin,default_latmax,default_lonmin,default_lonmax, calcSet);
	}
	
	public GEM1_NSHMP_SE_Asia_ERF(double latmin, double latmax, double lonmin, double lonmax,
			CalculationSettings calcSet) {

		try {
			if (gemSourceDataList == null)
				this.faultSourceDataList = new NshmpSouthEastAsiaFaultData(latmin, latmax, lonmin, lonmax).getList();

			this.griddedSeisSourceDataList = new NshmpSouthEastAsiaGridData(latmin, latmax, lonmin, lonmax).getList();

			this.subductionSourceDataList = new NshmpSouthEastAsiaSubductionData(latmin, latmax, lonmin, lonmax).getList();

		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
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
		GEM1_NSHMP_SE_Asia_ERF erf = null;
		erf = new GEM1_NSHMP_SE_Asia_ERF();
		erf.updateForecast();
		double runtime = (System.currentTimeMillis() - time)/1000;
		System.out.println("Done with Data Creation in "+(float) runtime+" seconds)");
	}


}
