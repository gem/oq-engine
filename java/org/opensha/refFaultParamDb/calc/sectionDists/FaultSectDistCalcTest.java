package org.opensha.refFaultParamDb.calc.sectionDists;

import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.HashMap;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.util.FileUtils;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelPrefDataFinal;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.FrankelGriddedSurface;
import org.opensha.sha.faultSurface.SimpleFaultData;

public class FaultSectDistCalcTest {
	
	static DecimalFormat df = new DecimalFormat("0.00");
	
	static long distCalcs = 0;
	
	public static String getTime(long start, long end) {
		double secs = (double)(end - start) / 1000d;
		if (secs < 60)
			return df.format(secs) + " secs";
		double mins = secs / 60d;
		return df.format(mins) + " mins";
	}
	
	public static void printDistCalcTimes(long start, long end) {
		double secs = (double)(end - start) / 1000d;
		double cps = distCalcs / secs;
		System.out.println("Distance calcs: " + distCalcs + ", " + df.format(cps) + " calcs/sec");
	}
	
	public static String getHash(int id1, int id2) {
		if (id1 < id2)
			return id1+"_"+id2;
		else
			return id2+"_"+id1;
	}
	
	public static int[] decodeHash(String hash) {
		String[] split = hash.split("_");
		int[] ints = { Integer.parseInt(split[0]), Integer.parseInt(split[1]) };
		return ints;
	}
	
	public static double getSurfaceDist(FrankelGriddedSurface surface1, FrankelGriddedSurface surface2, boolean fast) {
		double minDist = Double.MAX_VALUE;
		for (Location loc1 : surface1) {
			for (Location loc2 : surface2) {
				double dist;
				if (fast)
					dist = LocationUtils.linearDistanceFast(loc1, loc2);
				else
					dist = LocationUtils.linearDistance(loc1, loc2);
				if (dist < minDist)
					minDist = dist;
				distCalcs++;
			}
		}
		
		return minDist;
	}

	/**
	 * @param args
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
		int deformationModelId = 82;
		DecimalFormat pdf = new DecimalFormat("0.00%");
		
		double disc = 1.0;
		
		System.out.println("Discretization: " + disc + " KM");
		
		DeformationModelPrefDataFinal deformationModelPrefDB = new DeformationModelPrefDataFinal();
		ArrayList<FaultSectionPrefData> data =
			deformationModelPrefDB.getAllFaultSectionPrefData(deformationModelId);
		
		ArrayList<FrankelGriddedSurface> surfaces = new ArrayList<FrankelGriddedSurface>();
		
		int num = data.size();
		String outputString = new String();
		outputString += "Section Distances\n";
		
//		double thresh = 10.0;
		
		int combos = 0;
		long startTrace = System.currentTimeMillis();
		HashMap<String, Double> traceDists = new HashMap<String, Double>();
		for (FaultSectionPrefData data1 : data) {
			for (FaultSectionPrefData data2 : data) {
				if (data1 == data2)
					continue;
				String hash = getHash(data1.getSectionId(), data2.getSectionId());
				if (traceDists.containsKey(hash))
					continue;
				FaultTrace trace1 = data1.getFaultTrace();
				FaultTrace trace2 = data2.getFaultTrace();
				
				double minDist = trace2.getMinDistance(trace1, disc);
//				System.out.println("trace min dist: " + minDist);
				combos++;
				traceDists.put(hash, minDist);
			}
		}
		long endTrace = System.currentTimeMillis();
		FileUtils.saveObjectInFile("traceDists.obj", traceDists);
		
		System.out.println("There are " + num + " fault sections, and " + combos + " combinations");
		System.out.println("took " + getTime(startTrace, endTrace) + " to calc with traces");
		System.exit(0);
		
		long startFullFast = System.currentTimeMillis();
		System.out.println("Creating fault surfaces");
		for(int i=0;i<num;i++) {
			FaultSectionPrefData data1 = data.get(i);
			SimpleFaultData simpleFaultData = data1.getSimpleFaultData(false);
			FrankelGriddedSurface surface = new FrankelGriddedSurface(simpleFaultData, disc);
			
			surfaces.add(surface);
		}
		
		System.out.println("Calculating distances");
		HashMap<String, Double> fullDistsFast = new HashMap<String, Double>();
		int count = 0;
		distCalcs = 0;
		for (int i=0; i<surfaces.size(); i++) {
			FrankelGriddedSurface surface1 = surfaces.get(i);
			for (int j=0; j<surfaces.size(); j++) {
				FrankelGriddedSurface surface2 = surfaces.get(j);
				if (surface1 == surface2)
					continue;
				String hash = getHash(data.get(i).getSectionId(), data.get(j).getSectionId());
				if (fullDistsFast.containsKey(hash))
					continue;
				double minDist = getSurfaceDist(surface1, surface2, true);
				count++;
				if (count % ((int)(combos/4)) == 0) {
					double pDone = (double)count / combos;
					System.out.println(count + "/" + combos + " ("
							+ getTime(startFullFast, System.currentTimeMillis()) + " " + pdf.format(pDone) + ")");
				}
				
				fullDistsFast.put(hash, minDist);
//				System.out.println("min dist: " + minDist);
			}
		}
		long endFullFast = System.currentTimeMillis();
		FileUtils.saveObjectInFile("fullDistsFast.obj", fullDistsFast);
		
		System.out.println("took " + getTime(startFullFast, endFullFast) + " to calc with surface points, fast dist");
		printDistCalcTimes(startFullFast, endFullFast);
		
		long startFull = System.currentTimeMillis();
		System.out.println("Creating fault surfaces");
		surfaces.clear();
		for(int i=0;i<num;i++) {
			FaultSectionPrefData data1 = data.get(i);
			SimpleFaultData simpleFaultData = data1.getSimpleFaultData(false);
			FrankelGriddedSurface surface = new FrankelGriddedSurface(simpleFaultData, disc);
			
			surfaces.add(surface);
		}
		
		HashMap<String, Double> fullDists = new HashMap<String, Double>();
		System.out.println("Calculating distances");
		count = 0;
		distCalcs = 0;
		for (int i=0; i<surfaces.size(); i++) {
			FrankelGriddedSurface surface1 = surfaces.get(i);
			for (int j=0; j<surfaces.size(); j++) {
				FrankelGriddedSurface surface2 = surfaces.get(j);
				if (surface1 == surface2)
					continue;
				String hash = getHash(data.get(i).getSectionId(), data.get(j).getSectionId());
				if (fullDists.containsKey(hash))
					continue;
				double minDist = getSurfaceDist(surface1, surface2, false);
				count++;
				if (count % ((int)(combos/4)) == 0) {
					double pDone = (double)count / combos;
					System.out.println(count + "/" + combos + " ("
							+ getTime(startFull, System.currentTimeMillis()) + " " + pdf.format(pDone) + ")");
				}
				fullDists.put(hash, minDist);
//				System.out.println("min dist: " + minDist);
			}
		}
		long endFull = System.currentTimeMillis();
		FileUtils.saveObjectInFile("fullDists.obj", fullDists);
		
		System.out.println("took " + getTime(startFull, endFull) + " to calc with surface points");
		printDistCalcTimes(startFull, endFull);
	}

}
