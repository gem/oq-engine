package scratch.marco;

import java.awt.geom.Area;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.SourceType;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class TestFhcc {
	
	private static boolean CLASSIC = true;

	/**
	 * @param args
	 * @throws RemoteException 
	 */
	public static void main(String[] args) throws RemoteException {
		
		ArrayList<GEMSourceData> lst = new ArrayList<GEMSourceData>();
		
		double lonMin = 10.0;
		double latMin = 45.0;
		double lonMax = 11.0;
		double latMax = 46.0;
		
		double gmVal;
		double gmMin = 0.0;
		double gmMax = 2.0;
		double gmWdt = 0.1;
		
		// Dummy variables for a simple area source
		Region reg = new Region(new Location(latMin,lonMin),new Location(latMax,latMax));
		FocalMechanism[] focmecArr = new FocalMechanism[1];
		focmecArr[0] = new FocalMechanism(90.0,90.0,90.0);
		
		IncrementalMagFreqDist[] magDistArr = new IncrementalMagFreqDist[1];
		double mtot = 1e7;
		magDistArr[0] = new GutenbergRichterMagFreqDist(1.0,mtot,5.0,7.0,11);
		MagFreqDistsForFocalMechs mfdffm = new MagFreqDistsForFocalMechs(magDistArr[0],focmecArr[0]);
		ArbitrarilyDiscretizedFunc depTopRup = new ArbitrarilyDiscretizedFunc();
		depTopRup.set(8.0,0.0);
		
		// Create the GEMAreaSourceData
		GEMAreaSourceData areaData01 = new GEMAreaSourceData("pippo", "pluto", 
				TectonicRegionType.ACTIVE_SHALLOW,reg, mfdffm, depTopRup, 5.0);
		GEMAreaSourceData areaData02 = new GEMAreaSourceData("pippo", "pluto", 
				TectonicRegionType.ACTIVE_SHALLOW,reg, mfdffm, depTopRup, 5.0);
		lst.add(areaData01);
//		lst.add(areaData02);
		
		// Calculation settings
		CalculationSettings calcSett = new CalculationSettings();
		HashMap<SourceType,HashMap<String,Object>> erfSett = calcSett.getErf();
		HashMap<String,Object> areaSourceCalcSet = erfSett.get(SourceType.AREA_SOURCE);
		areaSourceCalcSet.put(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME.toString(),0.1);
		erfSett.put(SourceType.AREA_SOURCE,areaSourceCalcSet);
		calcSett.setErf(erfSett);
		
		// Create the GEM1ERF
		GEM1ERF erf = new GEM1ERF(lst,calcSett);
		erf.updateForecast();
		
		// Create the ArrayList of sites
		ArrayList<Site> siteList = new ArrayList<Site>();
		double dlt = 0.25;
		double lon = lonMin - 0.5;
		while (lon <= lonMax+0.5){
			double lat = latMin - 0.5;
			while (lat <= latMax){
				Site site = new Site(new Location(lat,lon));
				site.addParameter(new DoubleParameter("Vs30", 760.0));
				siteList.add(site);
				lat = lat + dlt;
			}
			lon = lon + dlt;
		}
		
		// Create the imrMap
		Map<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI> imrMap = 
			new HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>();
		BA_2008_AttenRel imr = new BA_2008_AttenRel(null);   
        imr.setParamDefaults();
        imr.setIntensityMeasure("PGA");
        imrMap.put(TectonicRegionType.ACTIVE_SHALLOW,imr);
		
		// Calculate hazard map
        System.out.printf("Number of sites: %4d \n",siteList.size());
        System.out.println("---- Starting calculation");
        long start = System.currentTimeMillis();
		Fhcc calculator = new Fhcc(siteList, imrMap, erf);
		HashMap<Integer,double[]> maps = calculator.getMaps();
		long end = System.currentTimeMillis();
		long tme = end-start; System.out.println("Time [s]: "+tme/1000.0);
		System.out.println("---- End of calculation");
		
		System.out.println("Site "+siteList.get(0).getLocation().getLongitude()
				+" "+siteList.get(0).getLocation().getLatitude());
		
		// Calculate the complementary cumulative distribution function
		double sum = 0.0;
		int idxSite = 0;
		double[] ccf = new double[maps.get(idxSite).length];
		for (int i=0; i < maps.get(idxSite).length; i++){
			for (int j=i; j < maps.get(idxSite).length; j++){
				ccf[i] = ccf[i] + maps.get(idxSite)[j];
			}
		}
		gmVal = 0.0;
		for (int j=0; j < maps.get(0).length; j++){
			System.out.printf(" %7.5f %7.5e %7.5e \n",gmVal,maps.get(idxSite)[j],ccf[j]);
			sum = sum + maps.get(idxSite)[j];
			gmVal = gmVal + gmWdt;
		}
		System.out.printf(" sum %7.5e \n",sum);
		
		// Compute hazard using the classical approach
		if (CLASSIC){
			System.out.println("---- Starting calculation: CLASSIC");

			start = System.currentTimeMillis();
//			for (int i=0; i < siteList.size(); i++){
			for (int i=idxSite; i < idxSite+1; i++){	
				Site site = siteList.get(i);
				HazardCurveCalculator hcc = new HazardCurveCalculator();
				ArbitrarilyDiscretizedFunc hazFun = new ArbitrarilyDiscretizedFunc();
				double gm = gmMin; int cnt = 0;
				while (gm <= gmMax){
					hazFun.set(gm, 1.0);
					gm = gm + gmWdt;
				}
				hcc.getHazardCurve(hazFun, site, imrMap, erf);
				if (i == idxSite){
					System.out.println("Site "+site.getLocation().getLongitude()
							+" "+site.getLocation().getLatitude());
					for (int j=0; j < hazFun.getNum(); j++){
						System.out.printf(" %6.2f %7.5e \n",hazFun.getX(j),hazFun.getY(j));
					}
				}
			}
			end = System.currentTimeMillis();
			tme = end-start; System.out.println("Time: "+tme);
			System.out.println("---- End of calculation: CLASSIC");
		}
		// Info
		System.out.println("End of TestFhcc");
		System.exit(0);
		
	}

}
