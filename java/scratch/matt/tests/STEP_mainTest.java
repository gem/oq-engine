package scratch.matt.tests;

import java.util.ArrayList;
import java.util.List;
import java.util.ListIterator;

import junit.framework.TestCase;

import org.apache.log4j.Logger;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupList;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupture;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

import scratch.matt.calc.RegionDefaults;
import scratch.matt.calc.STEP_main;

/**
 * test class for the class
 * scratchJavaDevelopers.matt.calc.STEP_main
 * 
 * merge.nts is the input catalog as defined in RegionDefaults.  Magnitude is in 
	column 48-49.  this is Mag*10.  This has only one M6.7 event in it.    
	merge_landers.nts has 3538 events in it with the first one being a M7.3 
	event.

 * 
 * @author baishan
 *
 */
public class STEP_mainTest extends TestCase {
	public static String cubeFilePath_TEST =  RegionDefaults.TEST_Path + "/events_nz_test.nts";
	public static String cubeFilePath_TEST_1 =  RegionDefaults.TEST_Path + "/merge_landers.nts";

	private static Logger logger = Logger.getLogger(STEP_mainTest.class);
	private STEP_main stepmain;// = new STEP_main();
	public STEP_mainTest() {		
		super();

	}

	protected void setUp() {
		RegionDefaults.setRegion(RegionDefaults.REGION_NZ);		
		//File datadir = new File(RegionDefaults.TEST_Path);
		//log("data dir  "  + datadir.getAbsolutePath() );
		stepmain = new STEP_main();
		stepmain.setEventsFilePath(cubeFilePath_TEST);
		//stepmain.setEventsFilePath(RegionDefaults.cubeFilePath);
		//set boundary to nz
		
	}

	public static  void log(String string) {
		logger.info(string);
		
	}

	protected void tearDown() {
	}

	/**
	 * load events from the file merge_landers.nts
	 * merge_landers.nts has 3538 events in it with the first one being a M7.3  event.
	 * 
	 */
	public void testLoadEvents() {		
		//this event are for california
		RegionDefaults.setRegion(RegionDefaults.REGION_CF);
		stepmain.setEventsFilePath(cubeFilePath_TEST_1);
		//double strike1=  -1.0;
		try {
			//set test event file path
			//stepmain.setEventsFilePath(cubeFilePath_TEST);			
			ObsEqkRupList   eqkRupList = stepmain.loadNewEvents();
			assertEquals("eqkRupList.size is 3538", 3538, eqkRupList.size()   );
			//assertTrue("Should throw Exception with strike : " + strike1,false);
			ListIterator <ObsEqkRupture> newIt = eqkRupList.listIterator ();
			ObsEqkRupture newEvent;
			int index = 0;
			while (newIt.hasNext()) {
				newEvent = (ObsEqkRupture) newIt.next();
				//double newMag = newEvent.getMag();
				if(index++ == 0){
					assertTrue(newEvent.getMag() == 7.3);
				}
				//log("newEvent " + newEvent.getInfo());
			}
			assertTrue(index == 3538);
		}
		catch(Exception e)
		{
			// System.err.println("Exception thrown as Expected:  "+e);
			e.printStackTrace();
		}
		
	}

	
	/**
	 * test the loadBgGrid method
	 */
	public void testLoadBgGrid() {
		ArrayList<HypoMagFreqDistAtLoc> hypList = stepmain.loadBgGrid();
		assertEquals("eqkRupList.size is 22400", 22400, hypList.size()   );
		//check locations
		assertHypoMagFreqDist(hypList, true);
	}
	
	
	/**
	 * test all the load process functions as in the 
	 * calc_STEP method in the STEP_main class
	 * as results of some methods are used in following method, it is impossible
	 * to do separate test for each method in STEP_main
	 */
	public void testCalc_STEP() {
		//double strike1=  -1.0;
		try {
			
			ObsEqkRupList   newObsEqkRuptureList = stepmain.loadNewEvents();
			
			//2. test load background
			ArrayList<HypoMagFreqDistAtLoc> hypList = stepmain.loadBgGrid();
		
			//hypList just initialized
			assertHypoMagFreqDist(hypList, true);

			//3. test process aftershocks
			tstProcessAfterShocks(newObsEqkRuptureList);

			//4.test forcasting
			tstProcessForcast(hypList);
			//test Mag Freq again, and freq value may be >0
			assertHypoMagFreqDist(hypList , false);

		}
		catch(Exception e)
		{
			// System.err.println("Exception thrown as Expected:  "+e);
			e.printStackTrace();
		}
	}

    //createStepSources
	public void testCreateStepSources() {
		ArrayList<HypoMagFreqDistAtLoc> hypList = stepmain.loadBgGrid();	
		ObsEqkRupList   newObsEqkRuptureList = stepmain.loadNewEvents();		
		stepmain.processAfterShocks(stepmain.getCurrentTime(), newObsEqkRuptureList);
		stepmain.processForcasts(hypList );			
		stepmain.createStepSources(hypList);
		ArrayList<PointEqkSource> sourceList = stepmain.getSourceList();
		assertTrue("sourceList smaller than hypList", sourceList.size() <=  hypList.size());
		log("sourceList " + sourceList.size());
		for(PointEqkSource src:sourceList){
			assertTrue("sourceList smaller than hypList", src.getRupture(0).getProbability() > 0d);
		}
		
	}
	
	//isObsEqkRupEventEqual
	public void testIsObsEqkRupEventEqual() {
		ObsEqkRupList   newObsEqkRuptureList = stepmain.loadNewEvents();
		
		assertTrue("event 1 & 2 equal",  stepmain.isObsEqkRupEventEqual(newObsEqkRuptureList.getObsEqkRuptureAt(0), newObsEqkRuptureList.getObsEqkRuptureAt(1)));
		
		assertFalse("event 1 & 3 not equal", 
				stepmain.isObsEqkRupEventEqual(newObsEqkRuptureList.getObsEqkRuptureAt(0), newObsEqkRuptureList.getObsEqkRuptureAt(2)));
		
		
	}

	/**
	 * process aftershocks
	 * this need be run after events loaded
	 * @return
	 */
	private void tstProcessAfterShocks(ObsEqkRupList newObsEqkRuptureList) {
		//double strike1=  -1.0;
		try {
			List stepAfterShocks = stepmain.getSTEP_AftershockForecastList();
			int numBefore = stepAfterShocks.size();
			//log("1 numBefore " + numBefore);

			stepmain.processAfterShocks(stepmain.getCurrentTime(), newObsEqkRuptureList);
			stepAfterShocks = stepmain.getSTEP_AftershockForecastList();
			int numAfter = stepAfterShocks.size();
			//log("2 numAfter " + numAfter);

			assertTrue("should be more stepAfterShocks after processing", numAfter > numBefore);
		}
		catch(Exception e)
		{
			// System.err.println("Exception thrown as Expected:  "+e);
			logger.error(e);
		}
	}

	/**
	 * process broadscasting
	 * this need be run after eq events, bgGrid loaded, and aftershock processed
	 * @return
	 */
	private void tstProcessForcast(ArrayList<HypoMagFreqDistAtLoc>  hypList) {
		//double strike1=  -1.0;
		try {
			//assertTrue(true);
			stepmain.processForcasts(hypList );			
		}
		catch(Exception e)
		{
			// System.err.println("Exception thrown as Expected:  "+e);
			e.printStackTrace();
		}
	}


	/**
	 * @param hypList
	 * @param init
	 */
	private void assertHypoMagFreqDist(ArrayList<HypoMagFreqDistAtLoc>  hypList, boolean init) {
		LocationList bgLocList = stepmain.getBgGrid().getRegion().getNodeList();
		ArrayList<HypoMagFreqDistAtLoc> hypForecastList = stepmain.getBgGrid().getMagDistList();

		//LocationList aftershockZoneList = forecastModel.getAfterShockZone().getGridLocationsList();

		int bgRegionSize = bgLocList.size();
		// int asZoneSize = aftershockZoneList.size();
		log("bgRegionSize " + bgRegionSize);
		//2. test locations size
		assertEquals( "hypList has same size as bgLocList", bgRegionSize, hypList.size());

		for(int k=0;k < bgRegionSize;++k){
			Location bgLoc = bgLocList.get(k);		    	 
			//log("loc index " + k);
			//log("bgLoc " + bgLoc.toString());		    	
			HypoMagFreqDistAtLoc hypoMagDistAtLoc= hypList.get(k);
			if(hypoMagDistAtLoc != null){
				Location hyploc= hypoMagDistAtLoc.getLocation();
				 //log("hyploc " + hyploc.toString());
				//3. test locations equal
				assertEquals("HypoMagFreqDistAtLoc and bgLocation must be the same", hyploc, bgLoc);	
				//4.test mag freq value
				double maxFreqVal = getMaxHypoMagFreqDistVal(hypoMagDistAtLoc );
				//log("maxFreqVal " + maxFreqVal);
				if(init){//at init state all  freq value is 0
					assertEquals(0d, maxFreqVal );
				}else{//value no longer 0, as some events added
					assertTrue(maxFreqVal >= 0d);
				}
			}
		} 

	}

	private double getMaxHypoMagFreqDistVal(HypoMagFreqDistAtLoc hypoMagDistAtLoc ) {
		IncrementalMagFreqDist[] magFreqDists = hypoMagDistAtLoc.getMagFreqDistList();
		double maxVal = 0;
		for(IncrementalMagFreqDist magFreqDist:magFreqDists){
			int num = magFreqDist.getNum();
			for( int index=0; index < num; index++){
				double mag = magFreqDist.getX(index);
				double val = magFreqDist.getY(index);
				if(val > maxVal){
					maxVal = val;
				}
			}					  
		}	
		return maxVal;		
	}
}