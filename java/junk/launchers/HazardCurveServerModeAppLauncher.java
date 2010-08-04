package junk.launchers;

import java.util.ArrayList;


public class HazardCurveServerModeAppLauncher extends AppLauncher {
	private static String className = "org.opensha.sha.gui.HazardCurveServerModeApplication";
	private static ArrayList<String> requiredFiles = new ArrayList<String>();
	
	static {
		requiredFiles.add("HazardCurveApp.jar"); // This is the application jar and must be first
		requiredFiles.add("jpedal.jar");
		requiredFiles.add("itext-1.3.jar");
		requiredFiles.add("jcommon-1.0.5.jar");
		requiredFiles.add("jfreechart-1.0.2.jar");
		requiredFiles.add("poi-2.5.1-final-20040804.jar");
		requiredFiles.add("mysql-connector-java-3.1.6-bin.jar");
		requiredFiles.add("f2jutil.jar");
		requiredFiles.add("sdoapi.jar");
		requiredFiles.add("ojdbc14.jar");
	}
	
	public HazardCurveServerModeAppLauncher(String[] args) {
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
	 * Get a list of required jar files for running this application
	 * 
	 * @return
	 */
	public ArrayList<String> getRequiredFiles() {
		return requiredFiles;
	}
	
	/**
	 * Makes sure the appropriate files exist and class path is set correctly,
	 * then runs the application via a call to runApp.
	 */
	public static void main(String[] args) {
		new HazardCurveServerModeAppLauncher(args);
	} // END: main

} 
