package scratch.martinez.util;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.nshmp.sha.calc.SDSsS1Calculator;
import org.opensha.nshmp.util.GlobalConstants;

public class SMTester implements Runnable {
	//--------------------------------------------------------------------------
	// Member Variables
	//--------------------------------------------------------------------------

	//---------------------------- Constant Members --------------------------//
	private static final String edition = GlobalConstants.NEHRP_2003;
	private static final String region  = GlobalConstants.CONTER_48_STATES;
	
	//----------------------------  Static Members  --------------------------//
	
	//---------------------------- Instance Members --------------------------//

	private String zipCode = null;
	private String siteClass = null;
	private SDSsS1Calculator calc = null;
	
	//--------------------------------------------------------------------------
	// Constructors/Initializers
	//--------------------------------------------------------------------------
	
	public SMTester(String zipCode, String siteClass) {
		this.calc = new SDSsS1Calculator();
		this.zipCode = zipCode;
		this.siteClass = siteClass;
	}
	
	public static void main(String [] args) {
		(
			new Thread(new SMTester("90401", GlobalConstants.SITE_CLASS_C))
		).start();
	}
	
	//--------------------------------------------------------------------------
	// Public Methods
	//--------------------------------------------------------------------------

	//------------------------- Public Setter Methods  -----------------------//

	//------------------------- Public Getter Methods  -----------------------//

	//------------------------- Public Utility Methods -----------------------//

	public void run() {
		ArbitrarilyDiscretizedFunc function = calc.calculateSDSsS1(edition,
				region,	zipCode, GlobalConstants.SITE_CLASS_C);
		System.out.println(function.getInfo());
	}
	
	//--------------------------------------------------------------------------
	// Private Methods
	//--------------------------------------------------------------------------
}
