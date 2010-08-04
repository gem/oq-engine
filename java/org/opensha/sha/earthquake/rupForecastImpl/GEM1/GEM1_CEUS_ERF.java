package org.opensha.sha.earthquake.rupForecastImpl.GEM1;

import java.io.FileNotFoundException;
import java.io.IOException;

import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpCascadiaSubductionData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpCeusFaultData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpCeusGridData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpUsData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpWusFaultData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpWusGridData;
import org.opensha.gem.GEM1.commons.CalculationSettings;

public class GEM1_CEUS_ERF extends GEM1ERF {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	public final static String NAME = "GEM1 CEUS ERF";
	
	private static double default_latmin = 24.6;
	private static double default_latmax = 50.0;
	private static double default_lonmin = -100.0;
	private static double default_lonmax = -65.0;
	
	public GEM1_CEUS_ERF() {
		this(null);
	}
	
	public GEM1_CEUS_ERF(CalculationSettings calcSet) {
		this(default_latmin,default_latmax,default_lonmin,default_lonmax, calcSet);
	}

	public GEM1_CEUS_ERF(double latmin, double latmax, double lonmin, double lonmax,
			CalculationSettings calcSet) {

		try {
			// Central and Eastern United States fault model (stable shallow tectonics)
			faultSourceDataList = new NshmpCeusFaultData(latmin,latmax,lonmin,lonmax).getList();
			
			// Central and Eastern United States grid model (stable shallow tectonics)
			griddedSeisSourceDataList = new NshmpCeusGridData(latmin,latmax,lonmin,lonmax).getList();

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
		GEM1_CEUS_ERF erf = null;
		erf = new GEM1_CEUS_ERF();
		erf.updateForecast();
		double runtime = (System.currentTimeMillis() - time)/1000;
		System.out.println("Done with Data Creation in "+(float) runtime+" seconds)");
	}

}
