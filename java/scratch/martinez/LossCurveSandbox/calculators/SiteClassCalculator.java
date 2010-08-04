package scratch.martinez.LossCurveSandbox.calculators;

import java.util.ArrayList;

import org.opensha.commons.geo.Location;

/**
 * This abstract base class defines an API for sub classes to implement in order
 * to compute site class values for locations. This top level class does much
 * of the mapping between classes, descriptions, and vs30 values, so sub
 * classes need only worry about implementing the actual lookup method.
 * 
 * @author   
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 *
 */
public abstract class SiteClassCalculator {
	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------

	//---------------------------- Constant Members ---------------------------//

	// The total number of site classes we know about.
	private static final int SITE_CLASS_COUNT = 6;

	// String used to inform of a non-existent site class.
	protected static final String NO_SUCH_SITE_CLASS = "No such site class.";

	// The indices into the arrays identifying each site class index.
	protected static final int SC_A = 0;
	protected static final int SC_B = 1;
	protected static final int SC_C = 2;
	protected static final int SC_D = 3;
	protected static final int SC_E = 4;
	protected static final int SC_F = 5;

	// These are used for the index into the vs30 range array. MIN is the zeroth
	// index, MAX is the first index. These arrays are always of length 2.
	public static final int MIN = 0;
	public static final int MAX = 1;
	
	//----------------------------  Static Members  ---------------------------//
	
	// ::NOTE:: These arrays must align their indexed values to correspond. //
	
	// List of very primitive vs30 ranges that map to corresponding site classes.
	private static ArrayList<double[]> vs30Ranges = null;
	// List of site class names.
	private static ArrayList<String> siteClassNames = null;
	// List of site class description.
	private static ArrayList<String> siteClassDescs = null;
	
	//---------------------------- Instance Members ---------------------------//

	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------
	
	/**
	 * Static initializer called exactly once the very first time this class (or
	 * any sub class) is accessed in any way. This method property aligns the
	 * underlying site class array mappings to known site classes.
	 */
	static {
		double [] vs30Range = new double[2]; // A region array; always length 2.
		vs30Ranges = new ArrayList<double[]>(SITE_CLASS_COUNT);
		siteClassNames = new ArrayList<String>(SITE_CLASS_COUNT);
		siteClassDescs = new ArrayList<String>(SITE_CLASS_COUNT);
		
		/*
		 * The order these are added makes a difference. Do not change this.
		 */
		
		// Site Class A
		vs30Range[MIN] = 5000.0; vs30Range[MAX] = Double.MAX_VALUE;
		vs30Ranges.add(vs30Range);
		siteClassNames.add("Site Class A");
		siteClassDescs.add("Hard Rock");
		
		// Site Class B
		vs30Range[MIN] = 2500.0; vs30Range[MAX] = 5000.0;
		vs30Ranges.add(vs30Range);
		siteClassNames.add("Site Class B");
		siteClassDescs.add("Rock");
		
		// Site Class C
		vs30Range[MIN] = 1200.0; vs30Range[MAX] = 2500.0;
		vs30Ranges.add(vs30Range);
		siteClassNames.add("Site Class C");
		siteClassDescs.add("Very Dense Soil and Soft Rock");
		
		// Site Class D
		vs30Range[MIN] = 600.0; vs30Range[MAX] = 1200.0;
		vs30Ranges.add(vs30Range);
		siteClassNames.add("Site Class D");
		siteClassDescs.add("Stiff Soil");
		
		// Site Class E
		vs30Range[MIN] = 0.00; vs30Range[MAX] = 600;
		vs30Ranges.add(vs30Range);
		siteClassNames.add("Site Class E");
		siteClassDescs.add("Soft Clay Soil");
		
		// Site Class F
		vs30Range[MIN] = 0.00; vs30Range[MAX] = 0.00; // This is a a null range.
		vs30Ranges.add(vs30Range);
		siteClassNames.add("Site Class F");
		siteClassDescs.add("Soil Requires Analysis");
	}
	
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//------------------------- Public Setter Methods  ------------------------//

	//------------------------- Public Getter Methods  ------------------------//
	
	/**
	 * Gets a list of site class names associated with the given list of 
	 * <code>locations</code>.
	 * 
	 * @param locations The list of locations of interest.
	 * @return A list of site class names corresponding in a 1-1 relationship
	 * with the given list of <code>locations</code>. Each site class name must
	 * exist in the <code>siteClassNames</code> array or it will be invalid.
	 * @throws SiteClassException If an error occurs while looking up the site
	 * class exception. 
	 */
	public abstract ArrayList<String> getSiteClasses(
			ArrayList<Location> locations) throws SiteClassException;

	
	/**
	 * Gets the default site class to use if the lookup method fails to return
	 * a valid site class. This implementation assumes site class B for default
	 * but sub classes may change that.
	 */
	public String getDefaultSiteClass() {
		return siteClassNames.get(SC_B);
	}

	/**
	 * For a given <code>siteClassName</code> returns the corresponding ranges
	 * of vs30 values possible.
	 * 
	 * @param siteClassName The name of the site class of interest.
	 * @return The corresponding vs30 range. If no such site class exists, then
	 * <code>null</code> is returned.
	 */
	public double[] getVs30RangeForName(String siteClassName) {
		int index = siteClassNames.indexOf(siteClassName);
		double[] range = null;
		if(index != -1) {
			range = vs30Ranges.get(index);
		}
		return range;
	}
	
	/**
	 * For a given <code>siteClassDescription</code> returns the corresponding
	 * ranges of vs30 values possible.
	 * 
	 * @param siteClassName The name of the site class of interest.
	 * @return The corresponding vs30 range. If no such site class exists, then
	 * <code>null</code> is returned.
	 */
	public double[] getVs30RangeForDescription(String siteClassDescription) {
		int index = siteClassDescs.indexOf(siteClassDescription);
		double[] range = null;
		if(index != -1) {
			range = vs30Ranges.get(index);
		}
		return range;
	}
	
	/**
	 * Gets the site class for the given location. Depending on implementation
	 * this may be a hard-coded selection, a default value, a looked-up value,
	 * or a manually selected value.
	 * 
	 * @param location The location to get the site class for.
	 * @return The site class name of the site conditions at the given
	 * <code>location</code>. This value MUST appear in the 
	 * <code>siteClassNames</code> array or it will be invalid.
	 * @throws SiteClassException If an error occurs while looking up the site
	 * class exception. 
	 */
	public String getSiteClassName(Location location) throws SiteClassException {
		ArrayList<Location> locations = new ArrayList<Location>();
		locations.add(location);
		return getSiteClasses(locations).get(0);
	}
	
	/**
	 * Gets the site class for the given <code>description</code>. If no such
	 * description is found, then <code>NO_SUCH_SITE_CLASS</code> is returned.
	 * 
	 * @param description The description to get the site class for.
	 * @return The site class name of the site conditions for the given
	 * <code>description</code>. This value MUST appear in the 
	 * <code>siteClassNames</code> array or it will be invalid.
	 */
	public  String getSiteClassName(String description) {
		int index = siteClassNames.indexOf(description);
		String name = NO_SUCH_SITE_CLASS;
		if(index != -1) {
			name = siteClassNames.get(index);
		}
		return name;
	}
	
	/**
	 * Gets the site class for the given <code>vs30</code>. If no such vs30 is
	 * found, then <code>NO_SUCH_SITE_CLASS</code> is returned.
	 * 
	 * @param vs30 The vs30 to get the site class for.
	 * @return The site class name of the site conditions for the given
	 * <code>vs30</code>. This value MUST appear in the 
	 * <code>siteClassNames</code> array or it will be invalid.
	 */
	public String getSiteClassName(double vs30) {
		int index = getVs30Index(vs30);
		String name = NO_SUCH_SITE_CLASS;
		if(index != -1) {
			name = siteClassNames.get(index);
		}
		return name;
	}
	
	/**
	 * Gets the site class description for the given <code>location</code>.
	 * 
	 * @param location The location to get the site class for.
	 * @return The site class description of the site conditions at the given
	 * <code>location</code>. This value MUST appear in the 
	 * <code>siteClassDescs</code> array or it will be invalid.
	 * @throws SiteClassException If an error occurs while looking up the site
	 * class exception. 
	 */
	public String getSiteClassDescription(Location location) 
			throws SiteClassException {
		return getSiteClassDescription(getSiteClassName(location));
	}
	
	/**
	 * For a given <code>siteClassName</code> returns the corresponding
	 * suitable for display.
	 * 
	 * @param siteClassName The name of the site class of interest.
	 * @return The corresponding site class description.
	 */
	public String getSiteClassDescription(String siteClassName) {
		int index = siteClassNames.indexOf(siteClassName);
		String description = NO_SUCH_SITE_CLASS;
		if(index != -1) {
			description = siteClassDescs.get(index);
		}
		return description;
	}
	
	/**
	 * Gets the site class description for the given <code>vs30</code>. If no
	 * such vs30 is found, then <code>NO_SUCH_SITE_CLASS</code> is returned.
	 * 
	 * @param vs30 The vs30 to get the site class description for.
	 * @return The site class description of the site conditions for the given
	 * <code>vs30</code>. This value MUST appear in the 
	 * <code>siteClassDescs</code> array or it will be invalid.
	 */
	public String getSiteClassDescription(double vs30) {
		int index = getVs30Index(vs30);
		String description = NO_SUCH_SITE_CLASS;
		if(index != -1) {
			description = siteClassDescs.get(index);
		}
		return description;
	}
	
	/**
	 * @return The list of known site class names.
	 */
	public ArrayList<String> getSiteClassNames() { return siteClassNames; }
	
	/**
	 * @return The list of known site class descriptions.
	 */
	public ArrayList<String> getSiteClassDescriptions(){ return siteClassDescs; }
	
	/**
	 * @return The list of known site class vs30 ranges. Use the <code>MIN</code>
	 * / <code>MAX</code> indexes to access the simple range bounds.
	 */
	public ArrayList<double[]> getVs30Ranges() { return vs30Ranges; }
	
	//------------------------- Public Utility Methods ------------------------//

	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------
	
	/**
	 * Searches the <code>vs30Ranges</code> list for the range that contains the
	 * given <code>vs30</code>. This is search considers the value to be 
	 * contained if <code>rangeMin &le; vs30 &lt; rangeMax</code>. If the given
	 * <code>vs30</code> falls outside all known ranges, then -1 is returned.
	 * 
	 * @param vs30 The vs30 value to look for.
	 * @return The index of that vs30 value or -1 if it is not found.
	 */
	protected int getVs30Index(double vs30) {
		// Set the default return value if not found.
		int index = -1;
		
		// Search for the index.
		for(int i = 0; i < vs30Ranges.size(); ++i) {
			double [] range = vs30Ranges.get(i);
			if(range[MIN] <= vs30 && vs30 < range[MAX]) {
				// We've found it!
				index = i;
				break;
			}
		}
		
		return index;
	}
}
