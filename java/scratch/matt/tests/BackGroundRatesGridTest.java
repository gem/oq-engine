package scratch.matt.tests;

import java.util.List;

import junit.framework.TestCase;

import org.apache.log4j.Logger;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

import scratch.matt.calc.BackGroundRatesGrid;
import scratch.matt.calc.RegionDefaults;

/**
 * test the BackGroundRatesGrid class
 * 
 * N.B.
 * it is an assumption for the hypoMagFreqDistAtLoc list to contain the same number and order of locations as 
 * those in the region grid list, but this is not true for california, may be a map should be used to store the 
 * hypoMagFreqDist
 * 
 * @author baishan
 *
 */
public class BackGroundRatesGridTest  extends TestCase {
	private static Logger logger = Logger.getLogger(BackGroundRatesGridTest.class);
	private BackGroundRatesGrid bgGrid1; //California
	private BackGroundRatesGrid bgGrid2; //california
	private BackGroundRatesGrid bgGrid3; //NZ
	protected void setUp() {
		//simple bg grid as in STEP_Main, with only one mag freq value
		RegionDefaults.setRegion(RegionDefaults.REGION_CF);
		bgGrid1 = new BackGroundRatesGrid(0,0,0);
		bgGrid1.setBgGridFilename(RegionDefaults.TEST_Path + "/AllCal96ModelDaily.txt");
		bgGrid1.initialize();	
		//RegionDefaults.TEST_Path + "/AllCal96ModelDaily.txt"
		//BackGroundRatesGrid with a range of mag freq values
		bgGrid2 = new BackGroundRatesGrid(4, 8, 0.1);
		//bgGrid2.setBgGridFilename(RegionDefaults.TEST_Path + "/AllCal96ModelDaily.txt");
		//NZ grid
		RegionDefaults.setRegion(RegionDefaults.REGION_NZ);
		bgGrid3 = new BackGroundRatesGrid(RegionDefaults.TEST_Path + "/NZdailyRates.txt");
			
	}

	protected void tearDown() {
	}
	
	/**
	 * test if BackGrount already initilized
	 * and bgGrid values etc.
	 */
	public void testInitialize() {	
		//asert bgGridRates
		assertBgGrid1();
		assertBgGrid2();
		assertBgGrid3();
	}
	
	/**
	 * test the checkLocaionEquals method
	 */
	public void testCheckLocaionEquals() {	
		Location loc1 = new Location(-47.05, 175.10, 0d);
		Location loc2 = new Location(-47.05, 175.102, 0d);
		assertTrue(bgGrid1.checkLocaionEquals(loc1, loc2, 0.01));
		assertFalse(bgGrid1.checkLocaionEquals(loc1, loc2, 0.001));		
	}
	
	/**
	 * test the getKey4Location method
	 */
	public void testGetKey4Location() {	
		Location loc = new Location(-47.053333, 175.1011, 0d);
		assertEquals("-4705_17510", bgGrid1.getKey4Location(loc));
		loc = new Location(32.1555, 175.1011, 0d);
		assertEquals("3216_17510", bgGrid1.getKey4Location(loc));
	}
	
	/**
	 * Grid1--California
	 * 
	 */
	private void assertBgGrid1() {
		logger.info(">>>> testBgRatesGrid1 " );
		int start1 = bgGrid1.getForecastMagStart(); 
		assertEquals(0, start1 );	
		assertTrue(bgGrid1.isBackgroundRatesFileAlreadyRead());
		assertTrue(bgGrid1.isBackgroundSourcesAlreadyMade());
		
		assertBgGridLocations(bgGrid1);
		
		//get MagFreqDistList for first location
		HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc0 = bgGrid1.getHypoMagFreqDistAtLoc(0);
		IncrementalMagFreqDist[]  hypoMagFreqDist = hypoMagFreqDistAtLoc0.getMagFreqDistList();
		logger.info("hypoMagFreqDist.length " +  hypoMagFreqDist.length);
		 //1. there is only 1 mag freq dist
		assertEquals("hypoMagFreqDist has one record", 1,hypoMagFreqDist.length);	
		 
		//get first mag freq distrribution
		IncrementalMagFreqDist hypoMagFreqDist0 = hypoMagFreqDist[0];
		int num = hypoMagFreqDist0.getNum(); //1
		//logger.info("num " +  num);
		//2. there is only 1 mag 
		assertEquals("there is only 1 mag ", 1,num );
		logger.info("hypoMagFreqDist0 " +  hypoMagFreqDist0);
		org.opensha.commons.data.DataPoint2D point = hypoMagFreqDist0.get(0);
		//3. the mag==0
		assertEquals("x==0", 0d, point.getX() );
		
		//4. test SeqIndAtNode
		assertEquals("getNumHypoLocs == sequences", bgGrid1.getSeqIndAtNode().length ,bgGrid1.getNumHypoLocs());
		//logger.info("bgGrid1.getSeqIndAtNode() "  + bgGrid1.getSeqIndAtNode().length);
		for(double val:bgGrid1.getSeqIndAtNode()){
			assertEquals("getSeqIndAtNode==-1", -1d,val);
		}
		logger.info("<<<< testBgRatesGrid1" );
	}
		

	/**
	 * Grid2--not initialized
	 * 
	 */
	private void assertBgGrid2() {
		//bgGrid2 is not initialized yet
		assertFalse(bgGrid2.isBackgroundRatesFileAlreadyRead());
		assertFalse(bgGrid2.isBackgroundSourcesAlreadyMade());
		int start2 = bgGrid2.getForecastMagStart();
		assertEquals(20, start2 );
		
	}
	

	/**
	 * NZ grid, initialized
	 */
	private void assertBgGrid3() {
		logger.info(">>>> testBgRatesGrid3 " );
		int start3 = bgGrid3.getForecastMagStart();
		assertEquals(20, start3  );		
		//NZ Grid
		assertTrue(bgGrid3.isBackgroundRatesFileAlreadyRead());
		assertTrue(bgGrid3.isBackgroundSourcesAlreadyMade());
				
		assertBgGridLocations(bgGrid3);
		
		HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc0 = bgGrid3.getHypoMagFreqDistAtLoc(0);
		IncrementalMagFreqDist[]  hypoMagFreqDist = hypoMagFreqDistAtLoc0.getMagFreqDistList();
		logger.info("hypoMagFreqDist.length " +  hypoMagFreqDist.length);
		 //1. there is only 1 mag freq dist
		assertEquals("hypoMagFreqDist has one record", 1,hypoMagFreqDist.length );	
		 
		//get first mag freq distrribution
		IncrementalMagFreqDist hypoMagFreqDist0 = hypoMagFreqDist[0];
		int num = hypoMagFreqDist0.getNum(); //1
		logger.info("num " +  num);
		//2. there is only 1 mag 
		assertEquals("there are 41 mag ", 41,num );
		logger.info("hypoMagFreqDist0 " +  hypoMagFreqDist0);
		org.opensha.commons.data.DataPoint2D point = hypoMagFreqDist0.get(0);
		//3. the mag==0
		//assertTrue( point.getX()  == 0);
		 assertTrue( point.getX() >=4 && point.getX() <= 8);		     
		
		//4. test SeqIndAtNode		
		 assertEquals("getNumHypoLocs == sequences", bgGrid3.getSeqIndAtNode().length , bgGrid3.getNumHypoLocs());
		//logger.info("bgGrid3.getSeqIndAtNode() "  + bgGrid3.getSeqIndAtNode().length);
		for(double val:bgGrid3.getSeqIndAtNode()){
			assertEquals("getSeqIndAtNode==-1", -1d,val);
		}
	}
	
	
	/**
	 * check the number and order of locations in region grid and hypoMagFreqDistAtLoc list
	 *  match each other
	 *  it is a requirement that the hypoMagFreqDistAtLoc list contain the same number and order of locations as 
	 * those in the region grid list 
	 * @param bgGrid
	 */
	private void assertBgGridLocations(BackGroundRatesGrid bgGrid ) {
		List<HypoMagFreqDistAtLoc>  hypoMagFreqDistAtLoc = bgGrid.getHypoMagFreqDist();		
		//check grid locations
		
		GriddedRegion region = bgGrid.getRegion();
		//SitesInGriddedRegion sites  = (SitesInGriddedRegion) bgGrid.getRegion();
		//logger.info("hypoMagFreqDistAtLoc.size()=" +  hypoMagFreqDistAtLoc.size() + " region locs=" + region.getNumGridLocs());
		
		assertEquals("number of locations in hypoMagFreqDistAtLoc should match grid locations",
				region.getNodeCount(), hypoMagFreqDistAtLoc.size() );
		for (int i = 0; i < region.getNodeCount(); i++){
			Location loc = region.locationForIndex(i);
			if(hypoMagFreqDistAtLoc.get(i) != null){
				assertEquals("locations in hypoMagFreqDistAtLoc should match grid locations", loc, hypoMagFreqDistAtLoc.get(i).getLocation());
			}
		}
	}
	
}
