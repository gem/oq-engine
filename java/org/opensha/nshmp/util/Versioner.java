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
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.net.URLConnection;

import javax.swing.JOptionPane;

import org.apache.commons.codec.binary.Base64;

public class Versioner {

	private static final String CLIENT_VERSION = GlobalConstants.getCurrentVersion();

	private static final String PATH = 
		"http://geohazards.usgs.gov/GroundMotionTool/version.html";
		
	private static final String GET_CHANGES = 
		"http://earthquake.usgs.gov/research/hazmaps/design/updates.php";

	private static String START_READ =
		"<!-- BEGIN RECENT REVISION -->";
	
	private static String END_READ = 
		"<!-- END RECENT REVISION -->";

	private static String START_READ_ALL =
		"<!-- BEGIN REVISION HISTORY -->";
	private static String END_READ_ALL = 
		"<!-- END REVISION HISTORY -->";

	private static String version = "UNKNOWN VERSION";
	private static String updates = "";
	private static String allUpdates = "";
	private static boolean connection = false;
////////////////////////////////////////////////////////////////////////////////////////////////////
//                                          CONSTRUCTORS                                          //
////////////////////////////////////////////////////////////////////////////////////////////////////
	/**
	 * Constructor: Sets the values of version, updates, and connection
	 */
	public Versioner() {
		connection = false;
		updates = "";
		allUpdates = "";
		version = "UNKNOWN VERSION";
		setConnection(); // Sets the version and connection status

		if (!connection) {
			// This method will interactively prompt the user for their proxy
			// settings and then re-set the connection.
			promptForProxy();
		}
		
		setUpdates();    // Sets the updates
		setAllUpdates();

	}

////////////////////////////////////////////////////////////////////////////////////////////////////
//                                       PUBLIC FUNCTIONS                                         //
////////////////////////////////////////////////////////////////////////////////////////////////////

	/**
	 * Returns the value of connection
	 * @returns connection boolean true if successfully connected to server, false otherwise
	 */
	public boolean check() {
		return connection;
	}

	/**
	 * Returns the HTML formatted list of recent updates
	 * @return updates String An HTML formatted list of recent updates
	 */
	public String getUpdates() {
		return updates;
	}

	/**
	 * Returns the HTML formatted list of all updates
	 * @return allUpdates String An HTML formatted list of all updates
	 */
	public String getAllUpdates() {
		return allUpdates;
	}

	/**
	 * Returns the full client version string.  This is
	 * something like 'Version: 5.X.X - mm/dd/yyyy'
	 * @return CLIENT_VERSION String The current version the user is running
	 */
	public String getClientVersion() {
		return CLIENT_VERSION;
	}

	/**
	 * Returns the full server version string.  This is
	 * something like 'Version: 5.X.X - mm/dd/yyyy'
	 * @return version String The current version known to the server
	 */
	public String getServerVersion() {
		return version;
	}

	/**
	 * Return the client version string without the 'Version: '
	 * prepended to the number
	 * @return versionNumber String The version number and release date of the current version the user is running
	 */
	public String getClientVersionNumber() {
		return CLIENT_VERSION.substring(9); // Something like 5.x.x - mm/dd/yyyy
	}

	/**
	 * Return the server version string without the 'Version: '
	 * prepended to the number
	 * @return versionNumber String The version number and release date of the current version known to the server
	 */
	public String getServerVersionNumber() {
		return version.substring(9); // Something like 5.x.x - mm/dd/yyyy
	}

	/**
	 * Checks the version of the client the user is running against what the server
	 * knows to be the most recent version and returns as appropriate
	 * @return isCurrent boolean True if the client and server version match, false otherwise
	 */
	public boolean versionCheck() {
		return CLIENT_VERSION.equals(version);
	}

	/**   
	 * Creates the message to give the user when their client is out of date
	 * @return infoMessage String An HTML formatted message informing the user of the need to update their client
	 */
	public String getUpdateMessage() {
		String info = "<p>It appears your version of this application is out of date.<br><br>" +
		"You are currently running: " + CLIENT_VERSION.substring(9) + "<br>" +
		"The new version available is:  " + version.substring(9) + "<br><br>" +
		"Below is a list of the changes that have been made in this revision:</p>\n\n";
		info += updates;
		return info;
	}
////////////////////////////////////////////////////////////////////////////////////////////////////
//                                       PRIVATE FUNCTIONS                                        //
////////////////////////////////////////////////////////////////////////////////////////////////////

	/**
	 * Checks with the server and compares the client version
	 * with what the server knows to be the most recent version.
	 * @return connection boolean, true if connected successfully, else false
	 */
	private static void setConnection() {

		// Set these such that the application has the best chance at succeeding
		// These will set the application proxy host and port properties into the
		// system so the java runtime will use them to connect.
		AppProperties.setSystemProperty(AppProperties.PROXY_HOST);
		AppProperties.setSystemProperty(AppProperties.PROXY_PORT);
		try {
			URL url = new URL(PATH);
			URLConnection conn = url.openConnection();
			
		 // Optionally use authentication.
	     // At this time, user must specify authentication manually in config file.
	     	if(AppProperties.getProperty("useAuth") != null) {
	     		String username = AppProperties.getProperty("username");
	     		String password = AppProperties.getProperty("password");
	     		
	     		String asciiAuth = username + ":" + password;
	     	
	     		System.err.println("Setting proxy authentication: " + asciiAuth);
	     		
	     		String enc64Auth = new String(
	     				Base64.encodeBase64(asciiAuth.getBytes())
	     			);
	     		
	     		conn.setRequestProperty("Proxy-Authorization", "Basic " +
	     				enc64Auth);
	     	}
		     	
		     	
			System.err.println("Connecting to server: " + PATH);
			BufferedReader bin = new BufferedReader(
												new InputStreamReader(
												conn.getInputStream()));
			
			System.err.println("Communitcating with server...");
			while ( (version = bin.readLine()) != null ) {
				System.err.println("  Server says, \"" + version + "\"");
				connection = true; // if we are reading the file, then connection succeeded.
				if (version.startsWith("<!-- Version:")) {
					int len = version.length();
					int start = 5;
					int end = len - 4;
					version = version.substring(start, end);
					break;
				}
			}
			if(version == null) {
				promptForProxy();
			}
			bin.close();
			
			System.err.println("\nAfter reading the server, version= \"" + version 
					+ "\"");
		} catch (Exception ex) {
			System.out.println(ex.getMessage());
			connection = false;
		} 
	}

	/**
	 * Gets an HTML formatted list of the most recent
	 * changes made to the application
	 */
	private static void setUpdates() {
		try {
			URL url = new URL(GET_CHANGES);
			BufferedReader bin = new BufferedReader(
											new InputStreamReader(
												url.openStream() ));

			String line;
			boolean reading = false;

			while( (line = bin.readLine()) != null) {
				if (line.equals(END_READ) )
					break;
				if ( reading ) 
					updates += line;
				if (line.equals(START_READ) )
					reading = true;
			}
		} catch (Exception ex) {
			System.out.println(ex.getMessage() + "Versioner::setUpdates()");
		}
	}


	/**
	 * Gets an HTML formatted list of all the the revisions made to this
	 * application since its Java release of 5.0.0
	 */
	private static void setAllUpdates() {
		try {
			URL url = new URL(GET_CHANGES);
			BufferedReader bin = new BufferedReader(
											new InputStreamReader(
												url.openStream() ));

			String line;
			boolean reading = false;

			while( (line = bin.readLine()) != null) {
				if (line.equals(END_READ_ALL) )
					break;
				if ( reading ) 
					allUpdates += line;
				if (line.equals(START_READ_ALL) )
					reading = true;
			}
		} catch (Exception ex) {
			System.out.println(ex.getMessage() + "Versioner::setAllUpdates()");
		}
	}

	private static void promptForProxy() {
		// Ask if they would like to try to use a proxy
		int ans = JOptionPane.showConfirmDialog(null, "Could not establish a " +
			"connection to the server.\nIf you use a proxy to connect and would " +
			"like to configure it now please click OK below.", "Connection Failure",
			JOptionPane.OK_CANCEL_OPTION, JOptionPane.ERROR_MESSAGE);

		// If yes, then configure the proxy settings and try to connect again
		if (ans == JOptionPane.OK_OPTION) {
			
			String proxyHost = JOptionPane.showInputDialog(null, "Please enter the " +
					"name of the proxy server you wish to use.", "Proxy Host Name",
					JOptionPane.INFORMATION_MESSAGE);
			String proxyPort = JOptionPane.showInputDialog(null, "Please enter the " +
				"port number to use on this proxy.", "Proxy Port Number",
				JOptionPane.INFORMATION_MESSAGE);
			
			AppProperties.setProperty(AppProperties.PROXY_HOST, proxyHost);
			AppProperties.setProperty(AppProperties.PROXY_PORT, proxyPort);
			try {
				AppProperties.saveProperties();
			} catch (IOException iox) {
				// Saving settings failed. Oh well, nothing lost nothing gained.
				System.err.println("An I/O Exception occurred while attempting to " +
						"save your connection settings.\n" + iox.getMessage());
			}
			setConnection();
		}
	}
} // End of Class
