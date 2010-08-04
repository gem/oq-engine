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

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.InvalidPropertiesFormatException;
import java.util.Properties;

/**
 * This class provides static access to the properties listed in the
 * NSHMP_CONFIG file that gets placed in the user's home directory.
 * This file is not created until the user customizes some property.
 * We use the standard java.util.Properties class as the underlying
 * object and this class provides static wrappers to save time.
 * 
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 * @since 1.5.8
 */
public class AppProperties {
	/** Public variables (list of property keys) **/
	public static final String PROXY_HOST = "proxyHost";
	public static final String PROXY_PORT = "proxyPort";
	
	/** Private config variables **/
	private static final String SLASH          = System.getProperty("file.separator");
	private static final String CONFIG_DIR     = System.getProperty("user.home");
	private static final String CONFIG_FILE    = "GroundMotionParameterConf.xml";
	private static Properties DEFAULTS         = null;
	private static Properties PROPERTIES       = null;
	private static File CONFIG                 = null;
	
	/**
	 * Constructor is private because this class should
	 * only ever be accessed in a static way.  No object is
	 * ever needed.
	 */
	private AppProperties() {}

	/**
	 * A static block will be executed before any calls to these
	 * methods.  We use this block to initially load settings from
	 * a config file.
	 */
	static {
		DEFAULTS = new Properties();
		/** Set any default values here.  Currently none. **/
		
		PROPERTIES = new Properties(DEFAULTS);
		
		CONFIG = new File(CONFIG_DIR + SLASH + CONFIG_FILE);
		if(CONFIG.exists() && CONFIG.canRead()) {
			try {
				PROPERTIES.loadFromXML(new FileInputStream(CONFIG));
			} catch (InvalidPropertiesFormatException ipf) {
				System.err.println(ipf.getMessage());
			} catch (IOException iox) {
				System.err.println(iox.getMessage());
			} // END: try
			
		} // END: if
	} // END: static
	
	/**
	 * Sets some well known system properties via the System.setProperty() method.
	 * Only pre-determined variables will be set.  To set an additional variable,
	 * try using <code>setSystemProperty(String key)</code>
	 * 
	 * @see setSystemProperty(String key)
	 */
	public static void setSystemProperties() {
		
		// List of settings to set to the system
		String proxyHost = PROPERTIES.getProperty(PROXY_HOST);
		String proxyPort = PROPERTIES.getProperty(PROXY_PORT);
		
		if(proxyHost != null) {System.getProperties().setProperty(PROXY_HOST, proxyHost);}
		if(proxyPort != null) {System.getProperties().setProperty(PROXY_PORT, proxyPort);}
	}
	
	/**
	 * Sets the property identified by the <code>key</code> to the value
	 * of the property identified by the same key that is currently known 
	 * by the application.  If the <code>key</code> is not currently set
	 * (from a call to setProperty(String key, String value)), then nothing
	 * is done by calling this method.
	 * 
	 * @param key The name of the property to set.
	 */
	public static void setSystemProperty(String key) {
		String prop = PROPERTIES.getProperty(key);
		if(prop!=null){
			System.getProperties().setProperty(key, prop);}
	}
	
	/**
	 * Sets the property as specified by calling the <code>setProperty</code> method
	 * on the underlying <code>Properties</code> object.  The setting is then saved
	 * out to the config file for persistence. Note that this only sets the property
	 * for the application level.  If you require the property to exist at the System
	 * level as well, then you must also make a call to 
	 * <code>setSystemProperty(String key)</code>.
	 * 
	 * @param key The name of the property to set
	 * @param value The value of the property to set
	 * @throws NullPointerException if either <code>key</code> or <code>value</code> is null
	 * @see setSystemProperty
	 */
	public static void setProperty(String key, String value) {
		PROPERTIES.put(key, value);
		try {
			PROPERTIES.storeToXML(new FileOutputStream(CONFIG, false), null, "UTF-8");
		} catch (FileNotFoundException fnf) {
			System.err.println(fnf.getMessage());
		} catch (IOException iox) {
			System.err.println(iox.getMessage());
		}
	}
	
	public static void saveProperties() throws IOException {
		PROPERTIES.storeToXML(new FileOutputStream(CONFIG), null);
	}
	
	/**
	 * @param key The name of the property to fetch.
	 * @return The current value of the desired property or null
	 *         if that property is not currently set.
	 */
	public static String getProperty(String key) {
		return PROPERTIES.getProperty(key);
	}
}
