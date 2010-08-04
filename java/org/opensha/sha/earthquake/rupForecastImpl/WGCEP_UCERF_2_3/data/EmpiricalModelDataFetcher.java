/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data;

import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.util.FileUtils;

/**
 * This class reads EmpiricalModelData.txt for time dependent forecast.
 * This txt file was made based on Karen Felzer's appendix for UCERF2 report.
 * 
 * 
 * @author vipingupta
 *
 */
public class EmpiricalModelDataFetcher  implements java.io.Serializable {
	public static String FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/EmpiricalModelData.txt";
	private ArrayList<Region> geographicRegionList = new ArrayList<Region>();
	private ArrayList<Double> rates = new ArrayList<Double>();
	private ArrayList<Double> stdDevs = new ArrayList<Double>();
	
	/**
	 * Read EmpiricalModelData.txt file 
	 *
	 */
	public EmpiricalModelDataFetcher() {
		try {
			ArrayList<String> fileLines = FileUtils.loadJarFile(FILE_NAME);
			int numLines = fileLines.size();
			Region region;
			for(int i=0; i<numLines; ++i) {
				String line = fileLines.get(i);
				if(line.startsWith("#")) continue; // ignore comment lines
				if(line.startsWith("-")) {
					 //region = new Region();
					 String regionName = line.substring(1).trim(); 
					 //region.setName(regionName);
					 ++i;
					 StringTokenizer rateTokenizer = new StringTokenizer(fileLines.get(i),",");
					 rates.add(Double.parseDouble(rateTokenizer.nextToken()));
					 stdDevs.add(Double.parseDouble(rateTokenizer.nextToken()));
					 ++i;
					 int numLocPoints = Integer.parseInt(fileLines.get(i));
					 LocationList locList = new LocationList();
					 for(int locIndex=0; locIndex<numLocPoints; ++locIndex) {
						 ++i;
						 StringTokenizer locTokenizer = new StringTokenizer(fileLines.get(i),",");
						 double latitude = Double.parseDouble(locTokenizer.nextToken());
						 double longitude = Double.parseDouble(locTokenizer.nextToken());
						 locList.add(new Location(latitude, longitude));
					 }
					 if(locList.size()!=0) {
						 region = new Region(
								 locList,BorderType.MERCATOR_LINEAR);
						 region.setName(regionName);
						 //region.createGeographicRegion(locList);
						 geographicRegionList.add(region);
					 }
					//geographicRegionList.add(region);
				}
			}
		} catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * Get the number of polygons
	 * 
	 * @return
	 */
	public int getNumRegions() {
		return this.geographicRegionList.size();
	}
	
	/**
	 * Get region at specified index
	 * 
	 * @param index
	 * @return
	 */
	public Region getRegion(int index) {
		return this.geographicRegionList.get(index);
	}
	
	/**
	 * Get the rate for region at specified index
	 * 
	 * @param index
	 * @return
	 */
	public double getRate(int index) {
		return this.rates.get(index);
	}
	
	/**
	 * Get uncertanity for region at specified index
	 * 
	 * @param index
	 * @return
	 */
	public double getStdDev(int index) {
		return this.stdDevs.get(index);
	}
	
	public static void main(String args[]) {
		EmpiricalModelDataFetcher empModelDataFetcher = new EmpiricalModelDataFetcher();
		int numRegions = empModelDataFetcher.getNumRegions();
		System.out.println(numRegions);
		for(int i=0; i<numRegions; ++i) {
			System.out.println(empModelDataFetcher.getRegion(i).getName());
			System.out.println(empModelDataFetcher.getRate(i));
			System.out.println(empModelDataFetcher.getStdDev(i));
		}
	}
	
}
