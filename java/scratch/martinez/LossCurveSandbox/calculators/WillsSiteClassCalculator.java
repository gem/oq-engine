package scratch.martinez.LossCurveSandbox.calculators;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

/**
 * <p>
 * Calculator used to compute site class condition values for locations in
 * California. This connects to a remote server for looking up the values. If
 * the server cannot find the value for whatever reason, (likely the location
 * was not in California), then the default site class is used instead.
 * </p>
 * <p>
 * This implementation closely follows that as found in the 
 * <code>WillsSiteClassApp</code> application, but this provides for use in a
 * larger application and plugs into the site class calculator api.
 * </p>
 * 
 * @author   
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 *
 */
public class WillsSiteClassCalculator extends SiteClassCalculator {

	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------

	//---------------------------- Constant Members ---------------------------//

	// Default server to connect to.
	private static final String DEFAULT_SERVLET_URL = "http://gravity.usc.edu/" +
			"OpenSHA/servlet/WillsSiteClassForGriddedRegionServlet";
	
	//----------------------------  Static Members  ---------------------------//

	//---------------------------- Instance Members ---------------------------//
	
	/**
	 * The URL used to open a connection to mine site class data.
	 */
	private URL servletURL =  null;
	
	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------

	/**
	 * Default, no-arg constructor. Creates a new
	 * <code>WillsSiteClassCalculator</code> that connects to the default server.
	 * 
	 * @throws MalformedURLException If the default servlet URL is poorly formed.
	 */
	public WillsSiteClassCalculator() throws MalformedURLException {
		this(DEFAULT_SERVLET_URL);
	}
	
	/**
	 * Creates a new <code>WillsSiteClassCalculator</code> that connects to the
	 * servlet specified by the given <code>servletURI</code>.
	 * 
	 * @param servletURL The string representation of the servlet URL.
	 * @throws MalformedURLException If the given <code>servletURI</code> is
	 * poorly formed.
	 */
	public WillsSiteClassCalculator(String servletURL) 
			throws MalformedURLException {
		this.servletURL = new URL(servletURL);
	}
	
	/**
	 * Creates a new <code>WillsSiteClassCalculator</code> that connects to the
	 * servlet specified by the given <code>servletURI</code>.
	 * 
	 * @param servletURL The servlet URL to connect to.
	 */
	public WillsSiteClassCalculator(URL servletURL) {
		this.servletURL = servletURL;
	}
	
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//------------------------- Public Setter Methods  ------------------------//

	//------------------------- Public Getter Methods  ------------------------//
	

	/**
	 * Uses the Wills et. al. database for California regions to look up the site
	 * class names. If the point is not in California or otherwise cannot be
	 * looked up using this method, then the default site class is used.
	 * 
	 * @param locations The list of locations to look up the site class names
	 * for.
	 * @return A list of site class names.
	 */
	public ArrayList<String> getSiteClasses(ArrayList<Location> locations)
			throws SiteClassException {
		
		ArrayList<String> siteClasses = null;
		try {
			siteClasses = lookupClassNamesFromServer(locations);
			siteClasses = convertToDisplayableSiteClasses(siteClasses);
		} catch (IOException iox) {
			throw new SiteClassException(iox);
		} catch (ClassNotFoundException cnf) {
			throw new SiteClassException(cnf);
		}
		
		return siteClasses;
	}
	
	//------------------------- Public Utility Methods ------------------------//

	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------
	
	/**
	 * Implementation following that found in
	 * <code>ConnectToCVM.getWillsSiteTypeFromCVM</code>. Looks up values from
	 * server and returns a list of raw values returned from server. The calling
	 * method should modify these values to ensure they meet with specifications
	 * of the public methods.
	 * 
	 * @param locations The list of locations to look for.
	 * @return A list of raw site class values returned from the server.
	 * @throws IOException If an I/O error occurs.
	 * @throws ClassNotFoundException  If the class of the serialized object
	 * cannot be found.
	 */
	@SuppressWarnings("unchecked") // Suppress warnings for cast of read object.
	private ArrayList<String> lookupClassNamesFromServer(
			ArrayList<Location> locations) throws IOException, 
			ClassNotFoundException {
		
		ArrayList<String> rawNames = null;
		
		// Open a connection to the server.
		URLConnection connection = servletURL.openConnection();
		connection.setDoOutput(true);
		connection.setUseCaches(false);
		connection.setDefaultUseCaches(false);
		connection.setRequestProperty("Content-Typ", "application/octet-stream");
		
		// Send the request to the server.
		ObjectOutputStream os =  new ObjectOutputStream(
				connection.getOutputStream());
		
		os.writeObject(convertToLocationList(locations));
		os.flush();
		os.close();
		
		// Receive the response from the server.
		ObjectInputStream is = new ObjectInputStream(connection.getInputStream());
		rawNames = (ArrayList<String>) is.readObject();
		is.close();
		
		return rawNames;
	}
	
	/**
	 * For a given list of <code>locations</code>, converts the list to an
	 * actual <code>LocationList</code> object for compatibility with the server.
	 * 
	 * @param locations The list of locations.
	 * @return A <code>LocationList</code> object with the same set of locations.
	 */
	private LocationList convertToLocationList(ArrayList<Location> locations) {
		LocationList list = new LocationList();
		for(int i = 0; i < locations.size(); ++i) {
			list.add(locations.get(i));
		}
		return list;
	}
	
	/**
	 * For a list of site class values returned from the server, translates them
	 * into appropriate strings for display. If a site class is not found for any
	 * given location, then the default site class is used instead.
	 */
	private ArrayList<String> convertToDisplayableSiteClasses(
			ArrayList<String> rawStrings) {
		ArrayList<String> formattedStrings =
			new ArrayList<String>(rawStrings.size());
		for(int i = 0; i < rawStrings.size(); ++i) {
			formattedStrings.add(convertToDisplayableSiteClass(rawStrings.get(i)));
		}
		return formattedStrings;
	}
	
	/**
	 * For a site class value returned from the server, translates it into a
	 * string appropriate for display. If the site class was not found (likely
	 * because the location was not in California, then it returns the default
	 * site class.
	 * 
	 * @param rawString The raw
	 */
	private String convertToDisplayableSiteClass(String rawString) {
		if("A".equalsIgnoreCase(rawString)) {
			return getSiteClassNames().get(SC_A);
		} else if("B".equalsIgnoreCase(rawString)) {
			return getSiteClassNames().get(SC_B);
		} else if("C".equalsIgnoreCase(rawString)) {
			return getSiteClassNames().get(SC_C);
		} else if("D".equalsIgnoreCase(rawString)) {
			return getSiteClassNames().get(SC_D);
		} else if("E".equalsIgnoreCase(rawString)) {
			return getSiteClassNames().get(SC_E);
		} else if("F".equalsIgnoreCase(rawString)) {
			return getSiteClassNames().get(SC_F);
		} else {
			return getDefaultSiteClass();
		}
	}
}
