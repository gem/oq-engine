package org.opensha.sha.earthquake.rupForecastImpl.GEM1;

import java.io.FileNotFoundException;
import java.io.IOException;

import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpCascadiaSubductionData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpUsData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpWusFaultData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpWusGridData;
import org.opensha.gem.GEM1.commons.CalculationSettings;

public class GEM1_WEUS_ERF extends GEM1ERF {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	public final static String NAME = "GEM1 WEUS ERF";
	
	private static double default_latmin = 24.6;
	private static double default_latmax = 50.0;
	private static double default_lonmin = -126.0;
	private static double default_lonmax = -100.0;
	
	public GEM1_WEUS_ERF() {
		this(null);
	}
	
	public GEM1_WEUS_ERF(CalculationSettings calcSet) {
		this(default_latmin,default_latmax,default_lonmin,default_lonmax, calcSet);
	}
	

	public GEM1_WEUS_ERF(double latmin, double latmax, double lonmin, double lonmax,
			CalculationSettings calcSet) {

		try {
			// Western United States fault model (active shallow tectonics)
			faultSourceDataList =  new NshmpWusFaultData(latmin,latmax,lonmin,lonmax).getList();
			
			// Western United States grid model (active shallow and subduction intraslab)
			griddedSeisSourceDataList = new NshmpWusGridData(latmin,latmax,lonmin,lonmax).getList();
			
			// Western United States Cascadia subduction model (subduction interface)
			subductionSourceDataList = new NshmpCascadiaSubductionData(latmin,latmax,lonmin,lonmax).getList();
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
		GEM1_WEUS_ERF erf = null;
		erf = new GEM1_WEUS_ERF();
		erf.updateForecast();
		double runtime = (System.currentTimeMillis() - time)/1000;
		System.out.println("Done with Data Creation in "+(float) runtime+" seconds)");
	}


}
