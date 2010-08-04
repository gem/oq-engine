/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.nshmp.util;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import javax.swing.JOptionPane;

/**
 * <b>Description:</b> Class used to configure the application to run on the
 * client's machine.  All configuration options are set in a config file 
 * called NSHMP_CONFIG in the home directory of the Java installation
 * on the user's machine.  This directory is generally write protected
 * and thus one must be an administrator in order to set propertie(s)
 * to be consistent.  This prevents the average user from inputting
 * bad settings or otherwise messing up their machine.  Also, it is
 * one of few (and the least invasive of those) directories that is known
 * to exist and can be quickly and easily found from within the JRE.
 * <br /><br />
 * Initially this class only sets and reads proxy settings for users that
 * require such.  This can be expanded/subclassed to fully configure the
 * application.
 * <br /><br />
 * TODO: Allow further customization through the configurations.
 *
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 * @deprecated Use AppProperties
 */
public class AppConfigurer {
	// Okay, so not really "Java Home", but this is more suitable
	public static final String JAVA_HOME = System.getProperty("user.home"); 
	public static final String SLASH = System.getProperty("file.separator");
	private static final String CONFIG_FILE = JAVA_HOME + SLASH + "NSHMP_CONFIG"; 

	/**
	 * Attempts to read proxy settings from a config file.  If the config
	 * file does not exist or if an error occures while reading it, then
	 * it will prompt the user to input the desired proxy settings.
	 *
	 * @param save if true, then the configuration settings are saved for
	 *						 future use.  If false then not saved.
	 */
	public static void setProxyConfig(boolean save) {
		ArrayList proxySettings;

		proxySettings = getProxyFromConfigFile();
		if ( proxySettings == null )
			proxySettings = getProxyFromUser_GuiMode();

		// Here is where we actually set the proxy settings
		System.getProperties().put("proxyHost", (String) proxySettings.get(0));
		System.getProperties().put("proxyPort", (String) proxySettings.get(1));

		if (save)
			saveProxySettings( (String) proxySettings.get(0), 
												 (String) proxySettings.get(1));
	}

	/**
	 * Saves the config property key with the value.  There is no
	 * harm in saving random key/value pairs, but this should be
	 * avoided.  See Class level documentation for a list of
	 * valid keys to be used. Appropriate values should be
	 * intuitive.
	 *
	 * @param key The name of the configuration key to be saved
	 * @param value The value to assign to the key
	 */
	public static void saveConfig(String key, String value) {
		File f = new File(CONFIG_FILE);

		try {
			BufferedWriter bout = new BufferedWriter(new FileWriter(f, true));
			bout.write(key + value);
			bout.newLine();
			bout.close();
		} catch (Exception ex) {
			JOptionPane.showMessageDialog(null, "Couldn't save config settings. " +
				"Settings will expire when you close the application.  To save the " +
				"settings, please run this application as an administrator",
				"Settings loaded but not saved.", JOptionPane.ERROR_MESSAGE);
		}
	}	

	/**
	 * Saves the proxyHost and proxyPort configuration values to the
	 * proxy_host and proxy_port configuration keys respectively.
	 * 
	 * @param proxyHost The name of the proxy host to use
	 * @param proxyPort A string value representing the port number to use
	 *									with the corresponding proxyHost
	 */
	public static void saveProxySettings(String proxyHost, String proxyPort) {
		saveConfig("proxy_host:", proxyHost);
		saveConfig("proxy_port:", proxyPort);
	}

////////////////////////////////////////////////////////////////////////////////
//                            Private Functions                               //
////////////////////////////////////////////////////////////////////////////////
	/*
		Attempts to read the config file and return an array list with
		the first values (index 0) containing the proxyHost to use and
		the second value (index 1) containing the proxyPort to be used.
	*/
	@SuppressWarnings("finally")
	private static ArrayList<String> getProxyFromConfigFile() {
		File f  = new File(CONFIG_FILE);
		if (!f.exists()) { return null;}

		String line;
		String proxyHost = "";
		String proxyPort = "";
		ArrayList<String> arr = null;

		try {
			BufferedReader bin = new BufferedReader(new FileReader(f));
			while ( (line = bin.readLine() ) != null ) {
				if (line.startsWith("proxy_host:") )
					proxyHost = line.substring(11);
				if (line.startsWith("proxy_port:") )
					proxyPort = line.substring(11);
				if ( (proxyHost != "") && (proxyPort != "") ) {
					arr = new ArrayList<String>();
					break;
				}
			}

			bin.close();
	
			if (arr != null) {
				arr.add(proxyHost);
				arr.add(proxyPort);
			}
		} catch (IOException ex) {	
			System.out.println(ex.getMessage());
			ex.printStackTrace();
			askDeleteConfig( "An error occured while loading " + 
				"your custom configurations. To avoid this in the future it is\n" + 
				"recommended that you delete this configuration file.  Doing " +
				"so will remove all your configuration settings.\nWould you like to " + 
				"do this now?", ex.getMessage());
			arr = null;
		} finally {
			return arr;
		}
	} // End of function


	/*
		Prompts the user with two input boxes to get the proxyHost and
		proxyPort.  Then returns an array list with the 0 index containing the
		proxyHost and the 1 index containing the proxyPort.
	*/
	private static ArrayList<String> getProxyFromUser_GuiMode() {
		ArrayList<String> arr = new ArrayList<String>();
		String proxyHost = JOptionPane.showInputDialog(null, "Please enter the " +
			"name of the proxy server you wish to use.", "Proxy Host Name",
			JOptionPane.INFORMATION_MESSAGE);
		String proxyPort = JOptionPane.showInputDialog(null, "Please enter the " +
			"port number to use on this proxy.", "Proxy Port Number",
			JOptionPane.INFORMATION_MESSAGE);
		
		arr.add(proxyHost);
		arr.add(proxyPort);

		return arr;
	}

	/*
		Asks the user if they would like to delete the configuration file.
		If user answers yes, then the file is deleted (assuming proper priveliges.
	*/
	private static void askDeleteConfig(String prompt, String errMsg) {
		int ans = JOptionPane.showConfirmDialog(null, prompt + "\n\t(" + errMsg + ")\n",
			"Delete Config File", JOptionPane.YES_NO_OPTION,
			JOptionPane.QUESTION_MESSAGE);
		
		if (ans == JOptionPane.YES_OPTION) {
			try {
				(new File(CONFIG_FILE)).delete();
			} catch (SecurityException ex) {
				JOptionPane.showMessageDialog(null, ex.getMessage() + "\nPlease " +
					"manually delete the file: " + CONFIG_FILE, "Deletion Failed",
					JOptionPane.ERROR_MESSAGE);
			}
		}
	}

			
}


		
