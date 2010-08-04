package junk.launchers;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;


public abstract class AppLauncher {
	private static ArrayList<String> requiredFiles;
	private static int reqFileLen = 0;
	private static String CP = "java.class.path";
	private static String PS = "path.separator";
	private static String FS = "file.separator";
	private static String UH = "user.home";
	private static String PATH_SEPARATOR = System.getProperty(PS);
	private static String CLASS_PATH = System.getProperty(CP);
	private static String FILE_SEPARATOR = System.getProperty(FS);
	private static String USER_HOME = System.getProperty(UH);
	private static String fsBaseDir = USER_HOME + FILE_SEPARATOR + "OpenSHA";
	private static String fsAppDir = fsBaseDir + FILE_SEPARATOR
			+ "HazardCurveCalculatorLocal";
	private static String fsLibDir = fsBaseDir + FILE_SEPARATOR + "lib";
	private static String rsAppDir = "/app";
	private static String rsLibDir = "/lib";

	public AppLauncher(String[] args) {
		requiredFiles = getRequiredFiles();
		reqFileLen = requiredFiles.size();
		createRequiredPaths();
		try {
			runApp(args);
		} catch (Exception ex) {
			ex.printStackTrace();
		}
	}
	

	/**
	 * Class name that contains the main() method, to be run on launching the application
	 * @return
	 */
	public abstract String getClassName();
	
	/**
	 * Get a list of required jar files for running this application
	 * 
	 * @return
	 */
	public abstract ArrayList<String> getRequiredFiles();
	
	

	/**
	 * Runs the application.
	 */
	private  void runApp(String[] args) throws Exception {
		URL[] jars = new URL[reqFileLen];
		String fsName = fsAppDir + FILE_SEPARATOR + requiredFiles.get(0);
		URL url = (new File(fsName)).toURI().toURL();
		jars[0] = url;

		for (int i = 1; i < requiredFiles.size(); ++i) {
			fsName = fsLibDir + FILE_SEPARATOR + requiredFiles.get(i);
			url = (new File(fsName)).toURI().toURL();
			jars[i] = url;
		}

		ClassLoader loader = new URLClassLoader(jars, ClassLoader
				.getSystemClassLoader());

		Class<?> theClass = loader.loadClass(getClassName());
		Object objParams[] = { args };
		Class<?> classParams[] = { objParams[0].getClass() };
		Method mainMethod = theClass.getDeclaredMethod("main", classParams);
		mainMethod.invoke(null, objParams);
	}

	/**
	 * Creates the required path(s) and/or places required jar files in the
	 * user's file system.
	 */
	private  void createRequiredPaths() {
		try {
			// Make sure the app dir exists in the file system
			File fsFile = new File(fsAppDir);
			if (!fsFile.exists()) {
				fsFile.mkdirs();
			}

			// Make sure the lib dir exists in the file system
			fsFile = new File(fsLibDir);
			if (!fsFile.exists()) {
				fsFile.mkdirs();
			}

			// Make sure the data dir exists in the file system
			// fsFile = new File(fsDataDir);
			// if(!fsFile.exists()) { fsFile.mkdirs(); }

			// Make sure the app jar file exists in the file system
			String fsName = fsAppDir + FILE_SEPARATOR + requiredFiles.get(0);
			String rsName = rsAppDir + "/" + requiredFiles.get(0);
			fsFile = new File(fsName);
			// Always copy the app file over (in case it might be new)
			copyFile(rsName, fsName);

			// Make sure the lib jar files exist in the file system
			for (int i = 1; i < requiredFiles.size(); ++i) {
				fsName = fsLibDir + FILE_SEPARATOR + requiredFiles.get(i);
				rsName = rsLibDir + "/" + requiredFiles.get(i);
				fsFile = new File(fsName);
				if (!fsFile.exists()) {
					copyFile(rsName, fsName);
				}
			} // END: for(...)

			// Make sure the data files exist in the file system
			/*
			 * Not needed... for(int i = 0; i < dataFiles.size(); ++i) { fsName =
			 * fsDataDir + FILE_SEPARATOR + dataFiles.get(i); rsName = rsDataDir +
			 * "/" + dataFiles.get(i); fsFile = new File(fsName);
			 * if(!fsFile.exists()) { copyFile(rsName, fsName); } } // END:
			 * for(...)
			 */

		} catch (NullPointerException npx) {
			System.err.println(npx.getMessage() + " :: createRequiredPaths(1)");
		}
	} // END: createRequiredPaths()

	/**
	 * Moves the rsFile to the fsFile. The rsFile should be an absolute path to
	 * a file stored within this jar file. The fsFile should be an absolute path
	 * to a file somewhere on the user's file system. This is a blind copy and
	 * will halt program execution on error.
	 */
	private  void copyFile(String rsFile, String fsFile) {
		try {
			InputStream is = HazardCurveLocalModeAppLauncher.class
					.getResourceAsStream(rsFile);
			FileOutputStream os = new FileOutputStream(fsFile);
			byte[] buf = new byte[1024];
			int totalCopied = 0;
			while (true) {
				int len = is.read(buf);
				totalCopied += len;
				if (len < 0) {
					break;
				}
				os.write(buf, 0, len);
			} // END: while
			System.err.println("Copied " + rsFile + " from jar file to "
					+ fsFile + " in the file system.  (" + totalCopied
					+ " bytes).");
			is.close();
			os.close();
		} catch (FileNotFoundException fnf) {
			System.err.println(fnf.getMessage() + " -- 1");
		} catch (IOException iox) {
			System.err.println(iox.getMessage() + " -- 2");
		} catch (NullPointerException npx) {
			// A dummy catch
		}
	}

} // END: GroundMotionParameter (class)
