package scratch.martinez.util;

import java.io.File;
import java.io.IOException;
import java.util.Hashtable;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.opensha.nshmp.sha.gui.beans.ExceptionBean;
import org.w3c.dom.DOMException;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;


/**
 * <strong>Title:</strong> PreferenceHandler<br />
 * <strong>Description:</strong> This interface provides a common
 * name for the file to store user preferences in when set by any
 * application in the OpenSha/OpenRisk/RiskAgora/jQuake programs.
 * <br /><br />
 * <strong>By convention, this file should be placed in the <code>java.home</code>
 * directory as specified by the Java System Properties.</code>
 * <br /><br />
 * The <code>java.home</code> property can be accessed with:
 * <pre>
 * 	String prefsDir = System.getProperty("java.home");
 * </pre>
 * Such a call would  return the fully qualified (absolute) path to the Java home
 * directory on the user's local machine.  However, since the file path separator
 * character varies by OS, it is important to finish with:
 * <pre>
 * 	String fileSeparator = System.getProperty("file.separator");
 * </pre>
 * Thus one might construct the fully qualified file name for the 
 * preferences file with something like this:
 * <pre>
 * 	String prefsDir = System.getProperty("java.home");
 * 	String fileSeparator = System.getProperty("file.separator");
 * 	String fullQualifiedName = prefsDir + fileSeparator + PREFERENCES_FILE_NAME;
 * </pre>
 * <hr />
 * In addition to the above, it is important to note the syntax of the preferences file.
 * The preferences file is an XML file that can be read using any XML reader you like.
 * XML was chosen since it is the standard format for passing data.  The syntax is as follows:
 * <pre>
 * 	&lt;?xml version='1.0' encoding='utf-8'&gt;
 * 	&lt;preferences&gt;
 * 		&lt;application name='appName'&gt;
 * 			&lt;param name='paramName'&gt;paramValue&lt;/param&gt;
 * 			&lt;param name='paramName2'&gt;paramValue2&lt;/param&gt;
 *		&lt;/application&gt;
 *
 *		&lt;application name='appName2'&gt;
 *			&lt;param name='paramName3'&gt;paramValue3&lt;/param&gt;
 *		&lt;/application&gt;
 * </pre>
 * **Note** There is a special application name called "any" which will apply
 * the params it contains to any application reading the xml file.  The &quot;any&quot;
 * app should always be listed first in the file.
 * 
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 */
public class PreferenceHandler {
	////////////////////////////////////////////////////////////////////////////////
	//                              PUBLIC VARIABLES                              //
	////////////////////////////////////////////////////////////////////////////////
	/**
	 * All applications should use this file (in the <code>java.home</code>
	 * directory) when reading or setting user preferences.
	 */
	public static final String PREFS_FILE_NAME = "OpenPrefs.xml";
	
	////////////////////////////////////////////////////////////////////////////////
	//                             PRIVATE VARIABLES                              //
	////////////////////////////////////////////////////////////////////////////////
	/** Path to the location where the preferences file is stored */
	private static String PREFS_FILE_PATH = System.getProperty("java.home");
	/** Character used on local file system for separating directorys (i.e. / or \ ) */
	private static String FILE_SEPARATOR = System.getProperty("file.separator");
	private static String PREFS_FILE = PREFS_FILE_PATH + FILE_SEPARATOR + PREFS_FILE_NAME;
	
	private String appName = "";
	private Hashtable<String, String> preferences= new Hashtable<String, String>();
	
	////////////////////////////////////////////////////////////////////////////////
	//                             PUBLIC CONSTRUCTORS                            //
	////////////////////////////////////////////////////////////////////////////////
	/**
	 * Default constructor.  This will only load up the preferences that are listed
	 * under the &quot;any&quot; application named in the preferences file.
	 */
	public PreferenceHandler() {
		this("");
	}
	
	/**
	 * This consturctor will load the preferences for the give <code>appName</code> as
	 * well as any preferences listed under the &quot;any&quot; application.
	 * 
	 * @param appName The name of the application to load preference settings for.
	 */
	public PreferenceHandler(String appName) {
		this.appName = appName;
		// The preferences are implicitly set within the function, but for clarity
		// we explicitely set it here as well.
		this.preferences = loadPreferences();
	}
	
	public PreferenceHandler(String appName, Hashtable<String, String> defaults) {
		
	}
	
	public String getAppName() { return appName; }
	public Hashtable<String, String> getPreferences() { return preferences; }
	/**
	 * Reads the local preferences file for the uers's settings and loads
	 * them into the preferences hashtable.
	 * @return The current <code>preferences</code> hashtable.
	 */
	public Hashtable<String, String> loadPreferences() {
		// Build an xml document parser to read the preferences file
		try {
			DocumentBuilder builder = 
				DocumentBuilderFactory.newInstance().newDocumentBuilder();
			Document document = builder.parse(new File(PREFS_FILE));
			document.normalize(); // Normalize the text
			
			// A list of all the applications in the preferences file
			NodeList applications = document.getElementsByTagName("application");
			int appCount = applications.getLength();
			// Load up the preferences for the application
			for(int i = 0; i < appCount; ++i) {
				String curAppName = applications.item(i).getAttributes()
					.getNamedItem("name").getNodeValue();
				// See if this application is "any" or the current application
				if(curAppName.equals("any") || (!appName.equals("") && appName.equals(curAppName))) {
					NodeList params = applications.item(i).getChildNodes();
					int paramCount = params.getLength();
					for(int j = 0; j < paramCount; ++j) {
						Node elmt = params.item(j);
						if(elmt.hasAttributes()) {
							String paramName = elmt.getAttributes().getNamedItem("name").getNodeValue();
							String paramValue = elmt.getFirstChild().getNodeValue();
							preferences.put(paramName, paramValue);
						}
					}
				}
			}
		} catch (ParserConfigurationException pce) {
			ExceptionBean.showSplashException("The parser configuration was not valid for creating a document builder.",
					"Parser Configuration Exception", pce);
		} catch (IOException iox) {
			ExceptionBean.showSplashException("An I/O error occurred!", "I/O Exception", iox);
		} catch (SAXException sxe) {
			ExceptionBean.showSplashException("A parse error occurred while reading the preferences file!", 
					"Parse Error", sxe);
		} catch (NullPointerException npe) {
			ExceptionBean.showSplashException("Tried to access a function on a null element!",
					"Null Pointer Exception", npe);
		} catch (DOMException dex) {
			ExceptionBean.showSplashException("Node value was too long!", "DOM Exception", dex);
		} catch (Exception ex) {
			// This is unexpected, so die, yes die.
			ex.printStackTrace();
			System.exit(1);
		}
		
		return preferences;
	}
	
	/**
	 * Sets the preference for the <code>key</code> to the <code>value</code>
	 * @param key The name of the preference you want to set.
	 * @param value The value you wish to set the above <code>key</code> to.
	 */
	public void setPreference(String key, String value) {
		preferences.put(key, value);
	}
	
	/**
	 * Dumps the current <code>preferences</code> hashtable back into the 
	 * preferences file.  This will only override the current application's
	 * preferences (i.e. not the &quot;any&quot; preferences).  If any of the current
	 * preferences in the <code>preferences</code> hashtable were originally
	 * obtained soley from the &quot;any&quot; application, then that preference
	 * is copied over to the current application's preferences section for future
	 * use.  This is does nothing if there is no <code>appName</code> specified.
	 */
	public void savePreferences() {
		if(appName == "" ) return; // We do not save preferences for an anonymous application
		try {
			File pFile = new File(PREFS_FILE);
			
		} catch (Exception iox) {
			
		}
	}
}
