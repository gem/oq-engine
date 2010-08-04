package scratch.martinez.util;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Map;
import java.util.Properties;

import org.opensha.nshmp.sha.gui.beans.ExceptionBean;


public class PropertyHandler {
	private String prefsFile = "";
	Properties properties = null;
	Properties defaults = null;
	
	/** The private instance of this class */
	private static PropertyHandler instance = null;
	/** The static name of the current application */
	private static String applicationName = "";
	
	/** Empty constructor.  Exists only to enforce singleton model */
	private PropertyHandler() {}
	
	/**
	 * The constructor is private.  This provides for the
	 * singleton model to be implemented.  This is important so that
	 * any class in the application can get a <code>PropertyHandler</code>
	 * and they will all be looking at the same object.
	 */
	private PropertyHandler(Properties defaults) {
		prefsFile = System.getProperty("user.dir") + System.getProperty("file.separator") + 
			applicationName + "_Prefs.txt";
		if(defaults == null)
			this.defaults = new Properties();
		else
			this.defaults = defaults;
		properties = new Properties(this.defaults);
			try {
				properties.loadFromXML(new FileInputStream(prefsFile));
			} catch (IllegalArgumentException iax) {
				iax.printStackTrace();
			} catch (IOException iox) {
				ExceptionBean.showSplashException(iox.getMessage(), "I/O Exception", iox);
			}
		
	}
	
	/**
	 * Gets or creates the instance of the property handler.  Since this
	 * is modeled as a singleton class, users should always use this method
	 * rather than the constructor (which is private anyway).  Only the
	 * initial call to this funtion will use the passed parameters to create
	 * the object.  All subsequent calls with simple return the existing
	 * instance.  For convenience a user can also make a call to the 
	 * <code>getInstance()</code> function to retrieve the instance once it
	 * has been created.
	 * 
	 * @param appName The name of the current application
	 * @param defaults The default properties to use
	 * @return The instance of this class
	 * @see PropertyHandler#getInstance;
	 */
	public static PropertyHandler createPropertyHandler(
			String appName, Properties defaults) {
		if(instance == null) {
			applicationName = appName;
			instance = new PropertyHandler(defaults);
		}
		return instance;
	}
	
	/**
	 * A convenience wrapper function.  This function will return the created
	 * instance of this class.  Note however that the instance might be null,
	 * so a user should check the return before trying to use the object for
	 * anything meaningful.
	 * @return The singleton instance of this class.
	 */
	public static PropertyHandler getInstance() { return instance; }
	
	/**
	 * Saves the current settings for later use.  These get put back
	 * into the user preference file for the current application.  
	 *
	 */
	public void save() {
		try {
			properties.storeToXML(new FileOutputStream(prefsFile), null);
		} catch (FileNotFoundException fnf) {
			ExceptionBean.showSplashException("Unable to access: " + applicationName + "_Prefs.txt", 
					"Preferences Not Saved", fnf);
		} catch (IOException iox) {
			iox.printStackTrace();
		}
	}
	
	public String getProperty(String key) {return (String) properties.get(key);}
	
	public String setProperty(String key, String value) {return (String) properties.put(key, value);}
	
	public String getAppName() {return applicationName;}
	
	public void setDefaultProperties(Map<String, String> newDefaults) {defaults.putAll(newDefaults);}
}	
