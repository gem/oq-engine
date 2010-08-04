package org.opensha.sha.earthquake.rupForecastImpl.GEM1;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_america.NshmpSouthAmericaData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_america.NshmpSouthAmericaFaultData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_america.NshmpSouthAmericaGridData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_america.NshmpSouthAmericaSubductionData;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpUsData;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

public class GEM1SouthAmericaERF extends GEM1ERF {

	private static final long serialVersionUID = 1L;

	public final static String NAME = "GEM1 South America ERF";

	private static double default_latmin = -55;
	private static double default_latmax = 15;
	private static double default_lonmin = -85;
	private static double default_lonmax = -30;

	public GEM1SouthAmericaERF() {
		this(null);
	}

	public GEM1SouthAmericaERF(CalculationSettings calcSet) {
		this(default_latmin,default_latmax,default_lonmin,default_lonmax, calcSet);
	}

	public GEM1SouthAmericaERF(double latmin, double latmax, double lonmin, double lonmax, CalculationSettings calcSet) {
		try {
			faultSourceDataList = new NshmpSouthAmericaFaultData(latmin,latmax,lonmin,lonmax).getList();
			griddedSeisSourceDataList = new NshmpSouthAmericaGridData(latmin,latmax,lonmin,lonmax).getList();
			subductionSourceDataList = new NshmpSouthAmericaSubductionData(latmin,latmax,lonmin,lonmax).getList();			
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

		initialize(calcSet);
	}


	@Override
	public String getName() {
		return NAME;
	}
	
	// this is temporary for testing purposes
	public static void main(String[] args) {
		double time = System.currentTimeMillis();
		System.out.println("Starting Data Creation");
		GEM1SouthAmericaERF saerf = null;
		saerf = new GEM1SouthAmericaERF();
		
		saerf.setParameter(GRIDDED_SEIS_RUP_TYPE_NAME, GRIDDED_SEIS_RUP_TYPE_LINE);
		saerf.updateForecast();
		double runtime = (System.currentTimeMillis() - time)/1000;
		System.out.println("Done with Data Creation in "+(float) runtime+" seconds)");

		System.out.println("NumSources = "+saerf.getNumSources());
		System.out.println("Starting Rupture Count");
		int num =0;
		for(int i=0;i<saerf.getNumSources();i++) num += saerf.getSource(i).getNumRuptures();
		System.out.println("Done with Rupture Count; numRup = "+num);
		runtime = (System.currentTimeMillis() - time)/1000;
		System.out.println("Total Runtime = "+runtime);
/*			for(int s=0;s<saerf.getNumSources();s++){
				ProbEqkSource src = saerf.getSource(s);
//				System.out.println(src.getTectonicRegionType());
				for(int r=0; r<src.getNumRuptures();r++) {
					EvenlyGriddedSurfaceAPI surface = saerf.getRupture(s, r).getRuptureSurface();
					double depth = surface.getLocation(0, 0).getDepth();	
					if(depth>100) System.out.println("depth="+(float)depth+"\tfor r="+r+" & s="+s+"\t"+src.getName());
				}
			}
*/

	}


}
