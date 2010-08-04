package junk.launchers;



public class CEA_HazardCurveCalcLauncher extends HazardCurveLocalModeAppLauncher {
	private static String className = "org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.gui.CEA_HazardCurveLocalModeApp";
	
	public CEA_HazardCurveCalcLauncher(String[] args) {
		super(args);
	}

	/**
	 * Class name that contains the main() method, to be run on launching the application
	 * @return
	 */
	public  String getClassName() {
		return className;
	}
	
	/**
	 * Makes sure the appropriate files exist and class path is set correctly,
	 * then runs the application via a call to runApp.
	 */
	public static void main(String[] args) {
		new CEA_HazardCurveCalcLauncher(args);
	} // END: main

} 
