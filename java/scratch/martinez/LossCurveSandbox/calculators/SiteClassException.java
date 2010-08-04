package scratch.martinez.LossCurveSandbox.calculators;

/**
 * Class indicating that the lookup of the site class using a site class
 * calculator failed for some reason.
 * 
 * @author  
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 */
public class SiteClassException extends Exception {
	
	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------

	//---------------------------- Constant Members ---------------------------//
	
	// Implementation side-effect for serialization.
	private static final long serialVersionUID = 0xD48626C;
	
	// Default error message for this exception type.
	private static final String DEFAULT_MESSAGE = "An error occured while " +
			"looking up the site class values.";
	
	//----------------------------  Static Members  ---------------------------//

	//---------------------------- Instance Members ---------------------------//

	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------
	
	/**
	 * Constructor for a new <code>SiteClassException</code> with the given
	 * <code>message</code> and <code>source</code>.
	 * 
	 * @param message The detailed message of this exception.
	 * @param source The underlying reason this exception was thrown.
	 */
	public SiteClassException(String message, Throwable source) {
		super(message, source);
	}
	
	/**
	 * Constructor for a new <code>SiteClassException</code> with the given
	 * <code>message</code>.
	 * 
	 * @param message The detailed message of this exception.
	 */
	public SiteClassException(String message) {
		super(message);
		fillInStackTrace();
	}
	
	/**
	 * Constructor for a new  <code>SiteClassException</code> with the given
	 * <code>source</code>.
	 * 
	 * @param source the underlying reason this exception was thrown.
	 */
	public SiteClassException(Throwable source) {
		super(DEFAULT_MESSAGE, source);
	}
	
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//------------------------- Public Setter Methods  ------------------------//

	//------------------------- Public Getter Methods  ------------------------//

	//------------------------- Public Utility Methods ------------------------//

	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------
}
