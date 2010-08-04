/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.io.FileWriter;

import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2;

import scratch.vipin.relm.RELM_ERF_ToGriddedHypoMagFreqDistForecast;

/**
 * This class generates Statewide Rates files that are used to plot Statewide maps.
 * These maps were made for UCERF2 report. The steps to create the maps were sent
 * to Ned in an email (The email that listed the steps to make each figure in 
 * UCERF2 report).
 * 
 *  
 * @author vipingupta
 *
 */
public class GenerateFilesForHypoRatesMaps {
	
	public static void main(String[] args) {
		int duration = 30;
		String probModel = UCERF2.PROB_MODEL_POISSON;

		// region to view the rates
		CaliforniaRegions.RELM_TESTING_GRIDDED evenlyGriddedRegion  = new CaliforniaRegions.RELM_TESTING_GRIDDED();
/*
	Location locOfInterest = new Location(37,-121.4);
	int indexOfInterest = evenlyGriddedRegion.getNearestLocationIndex(locOfInterest);
	System.out.println("indexOfInterest= "+indexOfInterest+"\t"+locOfInterest.toString()+"\t"+
			evenlyGriddedRegion.getGridLocation(indexOfInterest));
*/	
		// UCERF 2
System.out.println("UCERF2");
		MeanUCERF2 meanUCERF2 = new MeanUCERF2();
	    // include background sources as point sources
		meanUCERF2.setParameter(UCERF2.RUP_OFFSET_PARAM_NAME, new Double(10.0));
		meanUCERF2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(probModel);
		meanUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_INCLUDE);
		meanUCERF2.setParameter(UCERF2.BACK_SEIS_RUP_NAME, UCERF2.BACK_SEIS_RUP_POINT);

		meanUCERF2.getTimeSpan().setDuration(duration);
		meanUCERF2.updateForecast();
		// min mag, maxMag, These are Centers of first and last bin
		double minMag=5.0, maxMag=9.00;
		int numMag = 41; // number of Mag bins
		//	 make GriddedHypoMFD Forecast from the EqkRupForecast

		RELM_ERF_ToGriddedHypoMagFreqDistForecast griddedHypoMagFeqDistForecast1 =
			new RELM_ERF_ToGriddedHypoMagFreqDistForecast(meanUCERF2, evenlyGriddedRegion,
					minMag, maxMag, numMag, duration); 

		// minLat=31.5, maxLat=43.0, minLon=-125.4, MaxLon=-113.1
		generateNedsBulgeFiles("UCERF2", griddedHypoMagFeqDistForecast1);

		// NSHMP 2002
System.out.println("NSHMP02");
		EqkRupForecast nshmp2002 = new Frankel02_AdjustableEqkRupForecast();
	    // include background sources as point sources
		nshmp2002.setParameter(Frankel02_AdjustableEqkRupForecast.RUP_OFFSET_PARAM_NAME,
	                                new Double(10.0));
		nshmp2002.setParameter(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_NAME,
	                                Frankel02_AdjustableEqkRupForecast.BACK_SEIS_INCLUDE);
		nshmp2002.setParameter(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_RUP_NAME,
	                               Frankel02_AdjustableEqkRupForecast.BACK_SEIS_RUP_POINT);
		nshmp2002.getTimeSpan().setDuration(duration);
		nshmp2002.updateForecast();
		//		 make GriddedHypoMFD Forecast from the EqkRupForecast
		RELM_ERF_ToGriddedHypoMagFreqDistForecast griddedHypoMagFeqDistForecast2 =
			new RELM_ERF_ToGriddedHypoMagFreqDistForecast(nshmp2002, evenlyGriddedRegion,
					minMag, maxMag, numMag, duration); 
		//	minLat=31.5, maxLat=43.0, minLon=-125.4, MaxLon=-113.1
	
		generateNedsBulgeFiles("NSHMP2002", griddedHypoMagFeqDistForecast2);
		generateRatioFiles("UCERF2", griddedHypoMagFeqDistForecast1, griddedHypoMagFeqDistForecast2);
	  }
	
	
	/**
	 * It generates 2 files:
	 * 1. File that has ratio of cumulative rates at Mag 5 for each location
	 * 2. File that has ratio of cumulative rates at Mag 6.5 for each location
	 * 
	 * @param fileNamePrefix
	 * @param griddedHypoMagFeqDistForecast1
	 * @param griddedHypoMagFeqDistForecast2
	 */
	public static void generateRatioFiles(String fileNamePrefix, 
			  RELM_ERF_ToGriddedHypoMagFreqDistForecast griddedHypoMagFeqDistForecast1,
			  RELM_ERF_ToGriddedHypoMagFreqDistForecast griddedHypoMagFeqDistForecast2 ) {
		
		 try {
			  FileWriter fwRatio5 = new FileWriter(fileNamePrefix+"_UCERF2_NSHMP2002_Ratio5.txt"); // predicted rates at Mag 5
			  FileWriter fwRatio6_5 = new FileWriter(fileNamePrefix+"_UCERF2_NSHMP2002_Ratio6_5.txt"); // predicted rates at Mag 6.5
			 
			  int numLocs = griddedHypoMagFeqDistForecast1.getNumHypoLocs();
			  for(int i=0; i<numLocs; ++i) {
				  HypoMagFreqDistAtLoc mfdAtLoc1 = griddedHypoMagFeqDistForecast1.getHypoMagFreqDistAtLoc(i);
				  EvenlyDiscretizedFunc cumDist1  = mfdAtLoc1.getFirstMagFreqDist().getCumRateDist();
				  
				  HypoMagFreqDistAtLoc mfdAtLoc2 = griddedHypoMagFeqDistForecast2.getHypoMagFreqDistAtLoc(i);
				  EvenlyDiscretizedFunc cumDist2  = mfdAtLoc2.getFirstMagFreqDist().getCumRateDist();

				  Location loc = mfdAtLoc1.getLocation();
				  
				  double val1 = cumDist1.getInterpolatedY(5.0);
				  double val2 = cumDist2.getInterpolatedY(5.0);
				  double ratio=0;
				  if(val2!=0) ratio = val1/val2;
				  fwRatio5.write((float)loc.getLatitude()+"\t"+(float)loc.getLongitude()+"\t"+(float)ratio+"\n");
				  
				  val1 = cumDist1.getInterpolatedY(6.5);
				  val2 = cumDist2.getInterpolatedY(6.5);
				  ratio=0;
				  if(val2!=0) ratio = val1/val2;
				  fwRatio6_5.write((float)loc.getLatitude()+"\t"+(float)loc.getLongitude()+"\t"+(float)ratio+"\n");
			  }
			
			  // close files
			  fwRatio5.close();
			  fwRatio6_5.close();
		  }catch(Exception e) {
			  e.printStackTrace();
		  }
	}
	
	/**
	   * This function generates 4 files:
	   * 1. Lat/Lon/Pred(5.0)
	   * 2. Lat/Lon/Pred(6.5)
	   * 3. Lat/Lon/Extrapolated(6.5)
	   * 4. Lat/Lon/Ratio of Pred(6.5) and Extrapolated(6.5)
	   * It assumes a B-value of 0.8 
	   */
	  public  static void generateNedsBulgeFiles(String fileNamePrefix, 
			  RELM_ERF_ToGriddedHypoMagFreqDistForecast griddedHypoMagFeqDistForecast) {
		  try {
			  FileWriter fwPred5 = new FileWriter(fileNamePrefix+"_Pred5.txt"); // predicted rates at Mag 5
			  FileWriter fwPred6_5 = new FileWriter(fileNamePrefix+"_Pred6_5.txt"); // predicted rates at Mag 6.5
			  FileWriter fwExtrap6_5 = new FileWriter(fileNamePrefix+"_Extrap6_5.txt"); // Extrapolated rates at Mag 6.5
			  FileWriter fwRatio = new FileWriter(fileNamePrefix+"_PredExp6_5Ratio.txt"); // Ratio of Pred and Extrapolated Rates at 6.5
			  double totRate = 0;
			  // Do for each location
			  double pred5, pred6_5, extrap6_5, ratio;
			  double multiFactor = Math.pow(10, -0.8*(6.5-5));
			  int numLocs = griddedHypoMagFeqDistForecast.getNumHypoLocs();
			  for(int i=0; i<numLocs; ++i) {
				  HypoMagFreqDistAtLoc mfdAtLoc = griddedHypoMagFeqDistForecast.getHypoMagFreqDistAtLoc(i);
				  Location loc = mfdAtLoc.getLocation();
				  EvenlyDiscretizedFunc cumDist  = mfdAtLoc.getFirstMagFreqDist().getCumRateDist();
				  totRate+=cumDist.getY(0);
				  pred5 = cumDist.getInterpolatedY(5.0);
				  pred6_5 = cumDist.getInterpolatedY(6.5);
				  extrap6_5 = pred5 * multiFactor;
				  if(extrap6_5!=0)
					  ratio = pred6_5/extrap6_5;
				  else ratio = 0;
				  fwPred5.write((float)loc.getLatitude()+"\t"+(float)loc.getLongitude()+"\t"+(float)pred5+"\n");
				  fwPred6_5.write((float)loc.getLatitude()+"\t"+(float)loc.getLongitude()+"\t"+(float)pred6_5+"\n");
				  fwExtrap6_5.write((float)loc.getLatitude()+"\t"+(float)loc.getLongitude()+"\t"+(float)extrap6_5+"\n");
				  fwRatio.write((float)loc.getLatitude()+"\t"+(float)loc.getLongitude()+"\t"+(float)ratio+"\n");
			  }
			  //System.out.println("Total Rate:"+totRate);
			  // close files
			  fwPred5.close();
			  fwPred6_5.close();
			  fwExtrap6_5.close();
			  fwRatio.close();
		  }catch(Exception e) {
			  e.printStackTrace();
		  }
	  }
}

