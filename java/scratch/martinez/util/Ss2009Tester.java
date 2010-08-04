package scratch.martinez.util;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.nshmp.sha.calc.SsS1Calculator;
import org.opensha.nshmp.util.GlobalConstants;

public class Ss2009Tester {
	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------

	//---------------------------- Constant Members ---------------------------//

	//----------------------------  Static Members  ---------------------------//

	//---------------------------- Instance Members ---------------------------//

	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------

	public static void main(String [] args) {
		double latitude = 39.0; double longitude = -105.0;
		String edition = GlobalConstants.NEHRP_2009;
		String region = GlobalConstants.CONTER_48_STATES;
		
		SsS1Calculator calc = new SsS1Calculator();
		
		ArbitrarilyDiscretizedFunc func = calc.getSsS1(region, edition,
				latitude, longitude);
		
		System.out.println(func.getInfo());
	}
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//------------------------- Public Setter Methods  ------------------------//

	//------------------------- Public Getter Methods  ------------------------//

	//------------------------- Public Utility Methods ------------------------//

	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------
}
