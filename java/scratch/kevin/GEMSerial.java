package scratch.kevin;

import java.io.IOException;

import org.opensha.commons.util.FileUtils;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_america.NshmpSouthAmericaData;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1SouthAmericaERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1_CEUS_ERF;

public class GEMSerial {
	
	private static void printERF(EqkRupForecastAPI erf) {
		System.out.println("# sources: " + erf.getNumSources());
		System.out.println("src0 class: " + erf.getSource(0).getClass().getName());
		System.out.println("TectonicRegionType src0: " + erf.getSource(0).getTectonicRegionType());
		System.out.println("Prob src0 rup0: " + erf.getSource(0).getRupture(0).getProbability());
		System.out.println("Mag src0 rup0: " + erf.getSource(0).getRupture(0).getMag());
	}

	/**
	 * @param args
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
//		double latmin = -55;
//		double latmax = 15;
//		double lonmin = -85;
//		double lonmax = -30;
		double latmin = 24.6;
	    double latmax = 50.0;
	    double lonmin = -100.0;
	    double lonmax = -65.0;
//		NshmpSouthAmericaData model = new NshmpSouthAmericaData(latmin,latmax,lonmin,lonmax);
//		GEM1ERF modelERF = new GEM1SouthAmericaERF();
	    CalculationSettings calcSet = new CalculationSettings();
	    calcSet.setSourceCache(true);
		GEM1ERF modelERF = new GEM1_CEUS_ERF(calcSet);
		modelERF.updateForecast();
		for (int i=0; i<modelERF.getNumSources(); i++)
			modelERF.getSource(i);
		String fname = "/tmp/gemerf.obj";
		System.out.println("*********** SAVING ************");
		FileUtils.saveObjectInFile(fname, modelERF);
		System.out.println("*********** LOADING ************");
		EqkRupForecast fileERF = (EqkRupForecast)FileUtils.loadObject(fname);
//		System.out.println("Before serialization");
		printERF(modelERF);
		System.out.println("Loaded from file");
		printERF(fileERF);
		System.exit(0);
	}

}
