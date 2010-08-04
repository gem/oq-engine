package scratch.matt.tests;

import java.util.ListIterator;

import junit.framework.TestCase;

import org.apache.log4j.Logger;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.imr.AttenuationRelationship;

import scratch.matt.calc.STEP_HazardDataSet;
import scratch.matt.calc.STEP_main;

/**
 * 
 *  backgroundHazardPath is defined in RegionDefaults as STEP_backGround.txt and 
	the file is attached.  This is the back ground Probability file.  This is the 
	probability of exceeding MMI VI.  The file above is the RATE of M>4 
	earthquakes in all Magnitude bins.	
	
 * @author baishan
 *
 */
public class STEP_HazardDataSetTest  extends TestCase {
	private static Logger logger = Logger.getLogger(BackGroundRatesGridTest.class);
	private STEP_main stepmain  ;
	private STEP_HazardDataSet step_HazardDataSet;
	
	
	protected void setUp() {
		step_HazardDataSet = new STEP_HazardDataSet(false);
		step_HazardDataSet.runStepmain();		
		step_HazardDataSet.createShakeMapAttenRelInstance();
		//logger.info("IML_VALUE " + "removed STEP_HazardDataSet.IML_VALUE - was generating error");//STEP_HazardDataSet.IML_VALUE);
	}

	protected void tearDown() {
	}
	
	/**
	 * attenuation relationship, test initial params
	 * 
	 */
	public void testAttenRel() {
		AttenuationRelationship attenrel = step_HazardDataSet.getAttenRel();
		ListIterator itSite = attenrel.getSiteParamsIterator();
		
		while(itSite.hasNext()){
			//adding the clone of the site parameters to the list
			ParameterAPI param = (ParameterAPI)((ParameterAPI)itSite.next());
			assertNotNull("site param is not null",param.getValue() );
			//logger.info("site param " +  param.getInfo() + " = " + param.getValue() );			
		}
		
		ListIterator itRupt = attenrel.getEqkRuptureParamsIterator();
		while(itRupt.hasNext()){
			//adding the clone of the site parameters to the list
			ParameterAPI param = (ParameterAPI)((ParameterAPI)itRupt.next());
			assertNotNull("rupture param is not null", param.getValue() );
			//logger.info("rupture param " +  param.getInfo() + " = " + param.getValue()  );			
		}
		
		ListIterator itOther = attenrel.getOtherParamsIterator();
		while(itOther.hasNext()){
			//adding the clone of the site parameters to the list
			ParameterAPI param = (ParameterAPI)((ParameterAPI)itOther.next());
			//assertNotNull("other param is not null", param.getValue() );				
		}
		
		ListIterator itExceed = attenrel.getExceedProbIndependentParamsIterator();
		while(itExceed.hasNext()){
			//adding the clone of the site parameters to the list
			ParameterAPI param = (ParameterAPI)((ParameterAPI)itExceed.next());
			//assertNotNull("ExceedProbIndependent param should not be null", param.getValue() );
					
		}
		
		ListIterator itIML = attenrel.getIML_AtExceedProbIndependentParamsIterator();
		while(itIML.hasNext()){
			//adding the clone of the site parameters to the list
			ParameterAPI param = (ParameterAPI)((ParameterAPI)itIML.next());
			//logger.info("IML_AtExceedProbIndependent param " +  param.getInfo()  + " = " + param.getValue() );			
		}
		
		ListIterator itPropagation = attenrel.getPropagationEffectParamsIterator();
		while(itPropagation.hasNext()){
			//adding the clone of the site parameters to the list
			ParameterAPI param = (ParameterAPI)((ParameterAPI)itPropagation.next());
			assertNotNull("PropagationEffect param is not null", param.getValue() );
			//logger.info("PropagationEffect param " +  param.getInfo()  + " = " + param.getValue() );			
		}
		
		/// .....
		
		
	}
	
	/**
	 *  test calculating step probabilties
	 * 
	 */
	public void testCalcStepProbValues() {
		//logger.info("testCalcStepProbValues " );
		SitesInGriddedRegion sites = step_HazardDataSet.getDefaultRegion();//
		//logger.info("region.getNumGridLocs " + region.getNumGridLocs());
//		double[] bgVals = step_HazardDataSet.getBGVals(region , RegionDefaults.backgroundHazardPath);
		double[] stepBothProbVals = step_HazardDataSet.calcStepProbValues(sites);
		//logger.info("stepBothProbVals "  + stepBothProbVals.length);		
		int num = stepBothProbVals.length;
		assertTrue(num == sites.getRegion().getNodeCount());
		for(int i = 0 ; i < num; i++){
			double totalVal = stepBothProbVals[i];
			double bgVal = stepBothProbVals[i];
			//logger.info("bgVal "  + bgVal);
			//logger.info("totalVal "  + totalVal);
			assertTrue(totalVal>=0 && totalVal <=1);
			assertTrue(totalVal>=bgVal );
		}
	}
	
	//public void testSTEP_AftershockForecastListFromFile(){
	  //stepAftershockList
	  //Object stepAftershockListObj = step_HazardDataSet.readSTEP_AftershockForecastListFromFile();
	  //logger.info("stepAftershockListObj " + stepAftershockListObj.getClass());
	//}


}
