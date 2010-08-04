package scratch.martinez.LossCurveSandbox.vulnerability;

/**
 * This interface defines what it means for a class to be considered a
 * vulnerability model. Currently nothing is specified by this interface but it
 * was created for a proper inheritance structure. As more insight is gained as
 * to the variety of forms a vulnerability can take then we may be able to add
 * usefulness to this interface. As it stands, this is mostly a place holder for
 * future work.
 * 
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 * @TODO
 */
public interface VulnerabilityModel extends Comparable<VulnerabilityModel> {

	/**
	 * This returns the name of this vulnerability model. It does not need to be
	 * human readable since there is also a "display name" which is human
	 * readable. By definition this will never return <code>null</code>.
	 * 
	 * @return The name of this vulnerability model. This does not need to be
	 * human readable but can be.
	 */
	public String getName();
	
	/**
	 * This returns the name of this vulnerability model in a &ldquo;human
	 * readable&rdquo; format. No parsing, capitalization, or string replacement
	 * should be required for this value to be displayed on the web, command
	 * line, documentation, or application interfaces. By definition this will
	 * never return <code>null</code>.
	 * 
	 * @return A human readable name appropriate for display.
	 */
	public String getDisplayName();
	
	/**
	 * This returns the long-text description for this vulnerability model
	 * and is generally written by the engineer who designed the model. If the
	 * model follows a probability distribution, the distribution and its 
	 * parameters should be identified as well as anything else the designer
	 * feels is appropriate. This textual description will be used in the help
	 * text for the applications using this vulnerability.
	 * 
	 * @return The long-text description of this vulnerability model.
	 */
	public String getDescription();
	
	/**
	 * <p>
	 * This returns an array of strings identifying which structures are
	 * supported by this vulnerability model. That is, which structures it makes
	 * sense to use this vulnerability model for such that output results are
	 * reasonable to some degree of accuracy. This will never return 
	 * <code>null</code> but may return an empty string array.
	 * </p>
	 * <p>
	 * At this point these strings are for human consumption only and as such
	 * should be presented in a human-friendly (readable) syntax (i.e. spacing,
	 * capitalization, punctuation etc...).
	 * </p>
	 * 
	 * @return An array of supported structure types (as strings).
	 */
	public String [] getSupportedStructures();
}
