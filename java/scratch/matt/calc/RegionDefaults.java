package scratch.matt.calc;

import java.util.GregorianCalendar;



/**
 * <p>Title: </p>
 *
 * <p>Description: </p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 *
 * <p>Company: </p>
 *
 * @author not attributable
 * @version 1.0
 */
public class RegionDefaults {
  public RegionDefaults() {
  }

  /**
   * This class contains many of the variables that are specific
   * to a region.  Default values are set.
   * 
   * 
   */
  
  
  public static String TEST_Path = "data/mattg_test";
  
  public static int REGION_CF = 0;
  public static int REGION_NZ = 1;
  
  
  //input files
  public static String cubeFilePath =  TEST_Path + "/merge_NZ.nts"; //"/merge.nts", merge_synthNZ
  public static String backgroundHazardPath = TEST_Path +  "/STEP_NZHazProb.txt"; //STEP_NZHazProb.txt STEP_backGround
  public static String BACKGROUND_RATES_FILE_NAME =  TEST_Path +  "/NZdailyRates.txt"; //AllCal96ModelDaily.txt;//"org/opensha/sha/earthquake/rupForecastImpl/step/AllCal96ModelDaily.txt";
  
  //output files
  public static String outputHazardPath = TEST_Path + "/STEP_Probs.txt"; 
  public static String STEP_AftershockObjectFile = TEST_Path +  "/STEP_AftershockObj";
  public static String outputAftershockRatePath =  TEST_Path + "/TimeDepRates.txt";
  //this is for Damage States
  public static String outputHazCurvePath = TEST_Path + "/HazCurve_Probs.txt";
  //STEP_Rates
  public static String outputSTEP_Rates = TEST_Path + "/STEP_Rates.txt";
  
  public static double minMagForMainshock = 3.0;
  public static double minForecastMag = 4.0;
  public static double maxForecastMag = 8.0;
  public static double deltaForecastMag = 0.1;

  public static double forecastLengthDays = 1;
  public static boolean startForecastAtCurrentTime = true;
  public static GregorianCalendar forecastStartTime;  // set this if startForecastAtCurrentTime is False
  public static double daysFromQDM_Cat = 7;

  //California
  public final static double searchLatMin_CF = 32.0;
  public  final static double searchLatMax_CF = 42.2;
  public  final static double searchLongMin_CF = -124.6;
  public  final static double searchLongMax_CF = -112;
  //nz 
  public final static double searchLatMin_NZ = -47.95;
  public  final static double searchLatMax_NZ = -34.05;
  public  final static double searchLongMin_NZ = 164.05;
  public  final static double searchLongMax_NZ = 179.95; //-176
  
  public static double searchLatMin = searchLatMin_NZ;
  public static double searchLatMax = searchLatMax_NZ;
  public static double searchLongMin = searchLongMin_NZ;
  public static double searchLongMax = searchLongMax_NZ;

  public static double gridSpacing = 0.1;
  public static double gridPrecisionCF = 0.1;
  public static double gridPrecisionNZ = 0.01d;
  public static double gridPrecision  = gridPrecisionNZ;

  public static double addToMc = 0.02;

  // this is for defining the fault surface for the aftershock zone.
  // 2D for now so the values are the same.
  public static double lowerSeismoDepth = 10.0;
  public static double upperSeismoDepth = 10.0;

  public static boolean useFixed_cValue = true;
  
  // set the parameters for the AIC Calcs for the model elements
  public static int genNumFreeParams = 0;
  public static int seqNumFreeParams = 0;
  public static int spaNumFreeParams = 3;  // should be 4 if c is not fixed
  
  // the minimum mag to be used when comparing the cummulative of the 
  // background to that of an individual sequence
  public static int minCompareMag = 0;

  public static final double RAKE=0.0;
  public static final double DIP=90.0;
  
  /**
   * define the search boundary
   * used to switch regions (e.g. California, NZ)
 * @param minLat
 * @param maxLat
 * @param minLon
 * @param maxLon
 */
public static  synchronized void setBoundary(double minLat, double maxLat, double minLon, double maxLon){
	  searchLatMin = minLat;
	  searchLatMax = maxLat;
	  searchLongMin = minLon;
	  searchLongMax = maxLon;
  }

/**
 * set region default to CF or NZ
*/
public static  synchronized void setRegion(int regionNum){
	if(regionNum == REGION_CF){
		   cubeFilePath =  TEST_Path + "/merge.nts"; //"/merge.nts", merge_synthNZ
		   backgroundHazardPath = TEST_Path +  "/STEP_backGround.txt"; //STEP_NZHazProb.txt STEP_backGround
		   BACKGROUND_RATES_FILE_NAME =  TEST_Path +  "/AllCal96ModelDaily.txt"; //AllCal96ModelDaily.txt;//"org/opensha/sha/earthquake/rupForecastImpl/step/AllCal96ModelDaily.txt";
	
		   gridPrecision  = gridPrecisionCF;
		   
		   setBoundary(RegionDefaults.searchLatMin_CF, RegionDefaults.searchLatMax_CF,
					RegionDefaults.searchLongMin_CF, RegionDefaults.searchLongMax_CF);
		   
	}else if(regionNum == REGION_NZ){
		   cubeFilePath =  TEST_Path + "/merge_NZ.nts"; //"/merge.nts", merge_synthNZ
		   backgroundHazardPath = TEST_Path +  "/STEP_NZHazProb.txt"; //STEP_NZHazProb.txt STEP_backGround
		   BACKGROUND_RATES_FILE_NAME =  TEST_Path +  "/NZdailyRates.txt"; //AllCal96ModelDaily.txt;//"org/opensha/sha/earthquake/rupForecastImpl/step/AllCal96ModelDaily.txt";
		   
		   gridPrecision  = gridPrecisionNZ;
		   
		   setBoundary(RegionDefaults.searchLatMin_NZ, RegionDefaults.searchLatMax_NZ,
					RegionDefaults.searchLongMin_NZ, RegionDefaults.searchLongMax_NZ);
		   
	}
}

  
}
