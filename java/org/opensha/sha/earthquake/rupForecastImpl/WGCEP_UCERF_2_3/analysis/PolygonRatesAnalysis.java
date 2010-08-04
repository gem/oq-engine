/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.calc.ERF2GriddedSeisRatesCalc;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_TypeB_EqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UnsegmentedSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.A_Faults.A_FaultSegmentedSourceGenerator;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data.EmpiricalModelDataFetcher;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.griddedSeis.NSHMP_GridSourceGenerator;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

/**
 * Analyze the rate in various polygons as defined in Appendix I of UCERF2 report
 * 
 * @author vipingupta
 *
 */
public class PolygonRatesAnalysis {

	private UCERF2 ucerf2;
	private CaliforniaRegions.RELM_GRIDDED relmRegion = new CaliforniaRegions.RELM_GRIDDED();
	private EmpiricalModelDataFetcher empiricalModelFetcher = new EmpiricalModelDataFetcher();
	private ERF2GriddedSeisRatesCalc erf2GriddedSeisRatesCalc = new ERF2GriddedSeisRatesCalc(); 
	private final static double MIN_MAG = 5.0;
	private final static String PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/";
	private final static String A_FAULT_FILENAME = PATH+"A_FaultsPolygonFractions.txt";
	private final static String B_FAULT_FILENAME = PATH+"B_FaultsPolygonFractions.txt";
	private final static String NON_CA_B_FAULT_FILENAME = PATH+"NonCA_B_FaultsPolygonFractions.txt";
	private final static String C_ZONES_FILENAME = PATH+"C_ZonesPolygonFractions.txt";
	
	private double  totPointsInRELM_Region;
	public PolygonRatesAnalysis() {
		ucerf2 = new UCERF2();
		ucerf2.setParameter(UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_EMPIRICAL);
		ucerf2.updateForecast();
	}		

	/**
	 * Calculate rates in polygons
	 *
	 */
	public void calcRatesInPolygons() {
		double totRate = erf2GriddedSeisRatesCalc.getTotalSeisRateInRegion(MIN_MAG, ucerf2, relmRegion);
		int numPolygons = empiricalModelFetcher.getNumRegions();
		System.out.println("Total rate in RELM region:"+totRate);
		double rateInPoly;
		double rateRestOfRegion = totRate;
		for(int regionIndex=0; regionIndex<numPolygons; ++regionIndex) {
			Region polygon = empiricalModelFetcher.getRegion(regionIndex);
			if(polygon.getBorder()==null) continue;
			rateInPoly = erf2GriddedSeisRatesCalc.getTotalSeisRateInRegion(MIN_MAG, ucerf2, polygon);
			rateRestOfRegion-=rateInPoly;
			System.out.println("Rate in region "+polygon.getName()+" is\t\t"+rateInPoly);
		}
		System.out.println("Rate in rest of region is "+rateRestOfRegion);
	}
	
	
	/**
	 * For each A-Fault, find the fraction that lies in each polygon
	 */
	public void mkA_SourcesFile() {
		ArrayList aFaultGenerators = ucerf2.get_A_FaultSourceGenerators();
		int numA_Faults = aFaultGenerators.size();
		
		try {
			FileWriter fw = new FileWriter(A_FAULT_FILENAME);
			fw.write(getFileHeader());
			int index=0;
			// iterate over all source generators
			for(int i=0; i<numA_Faults; ++i) {
			
				// for segmented source
				if(aFaultGenerators.get(i) instanceof A_FaultSegmentedSourceGenerator) {
					A_FaultSegmentedSourceGenerator srcGen = (A_FaultSegmentedSourceGenerator)aFaultGenerators.get(i);
					ArrayList<FaultRuptureSource> aFaultSources = srcGen.getTimeIndependentSources(1.0);
					int numSrc = aFaultSources.size();
					// iterate over all sources
					for(int srcIndex=0; srcIndex<numSrc; ++srcIndex) {
						FaultRuptureSource faultRupSrc = aFaultSources.get(srcIndex);
						EvenlyGriddedSurfaceAPI surface  = faultRupSrc.getSourceSurface();
						writeFractonOfPointsInFile(fw, srcGen.getFaultSegmentData().getFaultName(), index++, surface);
					}
				} else { // unsegmented source
					UnsegmentedSource unsegmentedSource = (UnsegmentedSource)aFaultGenerators.get(i);
					EvenlyGriddedSurfaceAPI surface  = unsegmentedSource.getSourceSurface();
					writeFractonOfPointsInFile(fw, unsegmentedSource.getName(), i, surface);
				}
			}
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * Header to be written in file
	 * @return
	 */
	private String getFileHeader() {
		String header = "#FaultName, Index, RELM Region";
		int numPolygons = empiricalModelFetcher.getNumRegions();
		for(int regionIndex=0; regionIndex<numPolygons; ++regionIndex) {
			Region polygon = empiricalModelFetcher.getRegion(regionIndex);
			header+=","+polygon.getName();
		}
		header+="\n";
		return header;
	}
	
	
	/**
	 * For each B-Fault, find the fraction that lies in each polygon
	 *
	 */
	public void mkB_SourcesFile() {
		ArrayList bFaultSources = ucerf2.get_B_FaultSources();
		int numB_Faults = bFaultSources.size();
		
		try {
			FileWriter fw = new FileWriter(B_FAULT_FILENAME);
			fw.write(getFileHeader());
			// iterate over all sources
			for(int i=0; i<numB_Faults; ++i) {
				UnsegmentedSource unsegmentedSource = (UnsegmentedSource)bFaultSources.get(i);
				EvenlyGriddedSurfaceAPI surface  = unsegmentedSource.getSourceSurface();
				writeFractonOfPointsInFile(fw, unsegmentedSource.getName(), i, surface);
			}
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * For each B-Fault, find the fraction that lies in each polygon
	 *
	 */
	public void mkNonCA_B_SourcesFile() {
		ArrayList nonCA_B_FaultSources = ucerf2.getNonCA_B_FaultSources();
		int numNonCA_B_Faults = nonCA_B_FaultSources.size();
		
		try {
			FileWriter fw = new FileWriter(NON_CA_B_FAULT_FILENAME);
			fw.write(getFileHeader());
			// iterate over all sources
			for(int i=0; i<numNonCA_B_Faults; ++i) {
				ProbEqkSource probEqkSrc = (ProbEqkSource)nonCA_B_FaultSources.get(i);
				EvenlyGriddedSurfaceAPI surface  = null;
				if(probEqkSrc instanceof FaultRuptureSource) surface = ((FaultRuptureSource)probEqkSrc).getRupture(0).getRuptureSurface();
				else surface = ((Frankel02_TypeB_EqkSource)probEqkSrc).getSourceSurface();
				writeFractonOfPointsInFile(fw, probEqkSrc.getName(), i, surface);
			}
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	
	/**
	 * For each C-zone, find the fraction that lies in each polygon
	 *
	 */
	public void mkC_ZonesFile() {
		NSHMP_GridSourceGenerator nshmpGridSrcGen = new NSHMP_GridSourceGenerator();
		String PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/griddedSeis/";
		try {
			FileWriter fw = new FileWriter(C_ZONES_FILENAME);
			fw.write(getFileHeader());
			double [] area1new_agrid  = nshmpGridSrcGen.readGridFile(PATH+"area1new.agrid.asc",true);
			int cZoneIndex=0;
			calcFractionC_Zone(nshmpGridSrcGen, fw, "Area 1", area1new_agrid, cZoneIndex);
			double [] area2new_agrid = nshmpGridSrcGen.readGridFile(PATH+"area2new.agrid.asc",true);
			calcFractionC_Zone(nshmpGridSrcGen, fw, "Area 2", area2new_agrid, ++cZoneIndex);
			double [] area3new_agrid = nshmpGridSrcGen.readGridFile(PATH+"area3new.agrid.asc",true);
			calcFractionC_Zone(nshmpGridSrcGen, fw, "Area 3", area3new_agrid, ++cZoneIndex);
			double [] area4new_agrid = nshmpGridSrcGen.readGridFile(PATH+"area4new.agrid.asc",true);
			calcFractionC_Zone(nshmpGridSrcGen, fw, "Area 4", area4new_agrid, ++cZoneIndex);
			double [] mojave_agrid = nshmpGridSrcGen.readGridFile(PATH+"mojave.agrid.asc",true);
			calcFractionC_Zone(nshmpGridSrcGen, fw, "Mojave", mojave_agrid, ++cZoneIndex);
			double [] sangreg_agrid = nshmpGridSrcGen.readGridFile(PATH+"sangreg.agrid.asc",true);
			calcFractionC_Zone(nshmpGridSrcGen, fw, "San Gregonio", sangreg_agrid, ++cZoneIndex);
			fw.close();
		} catch (Exception e){
			e.printStackTrace();
		}
		

	}

	private void calcFractionC_Zone(NSHMP_GridSourceGenerator nshmpGridSrcGen, FileWriter fw, String cZoneName, double[] area1new_agrid, int cZoneIndex) throws IOException {
		int numPolygons = empiricalModelFetcher.getNumRegions();
		int []pointInEachPolygon = new int[numPolygons];
		int totPointsInRELM_Region = 0;
		for(int i=0; i<area1new_agrid.length; ++i) {
			if(area1new_agrid[i]==0) continue; // if the rate is 0 at this location
			++totPointsInRELM_Region;
			Location loc = nshmpGridSrcGen.getGriddedRegion().locationForIndex(i);
			for(int regionIndex=0; regionIndex<numPolygons; ++regionIndex) {
				Region polygon = empiricalModelFetcher.getRegion(regionIndex);
				if(polygon.getBorder()==null) continue;
				if(polygon.contains(loc)) {
					++pointInEachPolygon[regionIndex];
					break;
				}
			}
		}
		fw.write(cZoneName+","+cZoneIndex+","+ 
				totPointsInRELM_Region/(float)totPointsInRELM_Region);	
		int pointsOutsidePolygon = totPointsInRELM_Region;
		for(int regionIndex=0; regionIndex<numPolygons; ++regionIndex) {
			Region polygon = empiricalModelFetcher.getRegion(regionIndex);
			pointsOutsidePolygon-=pointInEachPolygon[regionIndex];
			if(polygon.getBorder()!=null)
				fw.write(","+pointInEachPolygon[regionIndex]/(float)totPointsInRELM_Region);
		}
		fw.write(","+pointsOutsidePolygon/(float)totPointsInRELM_Region+"\n");
	}

	/**
	 * Find the fraction of points in each polygon and then write in a file.
	 * This is used for A-Faults and B-Faults only.
	 * 
	 * @param fw
	 * @param srcIndex
	 * @param surface
	 * @throws IOException
	 */
	private void writeFractonOfPointsInFile(FileWriter fw, String faultName, int srcIndex, EvenlyGriddedSurfaceAPI surface) throws IOException {
		double []pointInEachPolygon = findFractionOfPointsInPolygons(surface);
		fw.write(faultName+","+srcIndex+","+(float)this.totPointsInRELM_Region);	
		for(int regionIndex=0; regionIndex<pointInEachPolygon.length; ++regionIndex) {
				fw.write(","+(float)pointInEachPolygon[regionIndex]);
		}
		fw.write("\n");
	}
	
	/**
	 * It returns the fraction of points in each polygon and the last element contains the
	 * fraction of points in rest of California
	 * @param surface
	 * @return
	 */
	private double[] findFractionOfPointsInPolygons(EvenlyGriddedSurfaceAPI surface) {
		int numPolygons = empiricalModelFetcher.getNumRegions();
		double []pointInEachPolygon = new double[numPolygons];
		int numPoints = surface.getNumCols();
		totPointsInRELM_Region = 0;
		// iterate over all surface point locations
		for(int ptIndex=0; ptIndex<numPoints; ++ptIndex) {
			Location loc = surface.getLocation(0, ptIndex);
			if(this.relmRegion.contains(loc)) ++totPointsInRELM_Region;
			for(int regionIndex=0; regionIndex<numPolygons; ++regionIndex) {
				Region polygon = empiricalModelFetcher.getRegion(regionIndex);
				if(polygon.getBorder()==null) continue;
				if(polygon.contains(loc)) {
					++pointInEachPolygon[regionIndex];
					break;
				}
			}
		}	
		// find the points in Rest of California and also calculate the fraction of points in each polygon
		int pointsOutsidePolygon =(int) Math.round(totPointsInRELM_Region);
		for(int regionIndex=0; regionIndex<numPolygons; ++regionIndex) {
			pointsOutsidePolygon-=pointInEachPolygon[regionIndex];
			// calculate fraction of points in each polygon
			pointInEachPolygon[regionIndex] = pointInEachPolygon[regionIndex]/(float)numPoints;
		}
		// fraction in rest of California (it is assumed that last index contains rest of California)
		pointInEachPolygon[numPolygons-1] = pointsOutsidePolygon/(float)numPoints;
		totPointsInRELM_Region = totPointsInRELM_Region/(float)numPoints;
		return pointInEachPolygon;
	}



	
	public static void main(String[] args) {
		PolygonRatesAnalysis polygonRatesAnalysis = new PolygonRatesAnalysis();
		//polygonRatesAnalysis.mkA_SourcesFile();
		//polygonRatesAnalysis.mkB_SourcesFile();
		//polygonRatesAnalysis.mkC_ZonesFile();
		//polygonRatesAnalysis.mkNonCA_B_SourcesFile();
		polygonRatesAnalysis.calcRatesInPolygons();
	}



}
