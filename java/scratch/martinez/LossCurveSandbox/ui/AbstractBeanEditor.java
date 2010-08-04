package scratch.martinez.LossCurveSandbox.ui;

/**
 * This is a base-class for editors of any form. It is not required for an
 * editor to extend this class, but this provides useful methods that may be
 * handy when interacting with the user. Methods here should be useful for any
 * type of deployment (gui, text, web, etc...).
 * 
 * @author  
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 */
public abstract class AbstractBeanEditor implements BeanEditorAPI {

	// Implementation side-effect for serialization.
	private static final long serialVersionUID = 0x0A7FB1D;
	
	/**
	 * Inserts new line characters at the nearest white-space character before
	 * the given <code>wrapPoint</code>. If no white-space is found, then the
	 * string will wrap using a hyphen at exactly the <code>wrapPoint</code>.
	 * 
	 * @param str The string to wrap.
	 * @param wrapPoint The length at which to wrap the string.
	 * @return The wrapped string.
	 */
	protected String wrapString(String str, int wrapPoint) {
		int breakPoint = 0;
		StringBuffer buf = new StringBuffer();
		
		// Wrap the question with a new line every 50 characters.
		while(str.length() > wrapPoint) {
			// Find a nice wrapping point
			breakPoint = str.lastIndexOf(" ", wrapPoint);
			if(breakPoint == -1) {
				// No space found before the wrap point, so use a hyphen break
				buf.append(str.substring(0, wrapPoint - 1));
				buf.append("-\n");
				str = str.substring(wrapPoint - 1);
			} else {
				// Append the sub string
				buf.append(str.substring(0, breakPoint));
				buf.append("\n");

				// Trim the question for the next iteration.
				str = str.substring(breakPoint);
			}
		}
		// Append the rest of the question.
		buf.append(str);
		
		return buf.toString();
	}

	/**
	 * Reverts the displayed property values to those currently used by the
	 * underlying bean. If any bean value is not currently valid, then the
	 * displayed values are simply cleared. After resetting the values they are
	 * considered to be &ldquo;unchanged&rduo; from the beans values. 
	 * Implementations of this method should be synchronized.
	 */
	protected abstract void updateValuesFromBean();
	
	/**
	 * Starts listening to changes from the current <code>bean</code> object.
	 * This is called at time of instantiation or after the user changes the bean
	 * to modify with this editor.
	 */
	protected abstract void startListening();
	
	/**
	 * Stops listening to changes from the current <code>bean</code> object. This
	 * is called before the user changes the bean to modify with this editor.
	 */
	protected abstract void stopListening();
}
