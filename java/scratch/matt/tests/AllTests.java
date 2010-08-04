package scratch.matt.tests;


import junit.framework.Test;
import junit.framework.TestCase;
import junit.framework.TestSuite;

public class AllTests extends TestCase {
	 public static Test suite() {
		    TestSuite suite = new TestSuite();
		    suite.addTest(new TestSuite(STEP_mainTest.class));
		   // suite.addTest(new TestSuite(BackGroundRatesGridTest.class));
		    //suite.addTest(new TestSuite(STEP_HazardDataSetTest.class));
		    return suite;	
		  }

}
