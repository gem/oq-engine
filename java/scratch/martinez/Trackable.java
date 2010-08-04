package scratch.martinez;

import java.util.ArrayList;

/**
 * This interface specifies the minimum set of functions required for a class to
 * implement to be considered "trackable".  The interface was developed specifically
 * for the Residential Risk application developed under the OpenRisk effort, however
 * it should be general enough to be used in other applications.
 * 
 * The Trackable interface allows for developer-defined depenencies between classes.
 * As was initially intended for OpenRisk software, we have two basic classes, a 
 * VulnerabilityModel, and a StructureType.  These classes exist in a many to many
 * relationship, and this interface allows them to be aware of which counterparts
 * are currently available for a given class.
 * 
 * While in principle the implementing class can be concrete, this interface is most
 * useful when the implementing class is abstract and multiple subclasses have varying
 * interdependencies.
 * 
 * @version 1.0
 * @author <a href="mailto:emartinez@usgs.gov>Eric Martinez</a>
 *
 */
public interface Trackable {
	
	/**
	 * This function registers the implementing object as an available type,
	 * and specifies which counterpart objects this object will support.  For
	 * example, the "Wesson et al." vulnerability model is only valid for
	 * wood frame housing.  So a call to register by a "Wesson et al."
	 * object will register "Wesson et al." as an available VulnerabilityModel,
	 * and also register it as supporting the "Wood Frame" StructureType.
	 *
	 * @param types An <code>ArrayList</code> of Strings naming the classes
	 * that are supported by this trackable object.
	 */
	public void register(ArrayList<String> types);
	
	/**
	 * Checks the list of known classes available to be instantiated that
	 * suppport the <code>obj</code>.  Returns an <code>ArrayList</code> of
	 * strings representing the supported classes that are available for use.
	 * For example: If the "Wesson et al." VulnerabilityModel calls this function
	 * on the <code>StructureType</code>, then only "Wood Frame" will be returned
	 * since that is the only type of structure that is supported by "Wesson et al."
	 * So after a sequence like:
	 * <code>
	 * 	VulnerabilityModel vm = new Wesson();
	 * 	vm.register();
	 * 	ArrayList<String> st = vm.getSupportedTypes(new StructureType());
	 * </code>
	 * The <code>st</code> would have a single entry of "WoodFrame".
	 * 
	 * @param obj The class of supported objects to get.
	 * @return An <code>ArrayList</code> of strings representing the supported classes.
	 * 
	 */
	public ArrayList<Trackable> getSupportedTypes(Trackable obj);
	
	/**
	 * Gets all the [sub-]classes that have registered with the [base] class.
	 * @return An <code>ArrayList</code> of strings representing the registered classes.
	 */
	public ArrayList<Trackable> getRegisteredTypes();
	
	/**
	 * Returns a unique id that other <code>Trackable</code> objects can know about
	 * in advance that is used to uniquely identify the implementing class.  If the
	 * implementing class does not follow the accepted convention for producing this
	 * unique id, then it should publish its id in the documentation.
	 * 
	 * @return A unique id that identifies the implementing class.  As convention, this
	 * should be the fully-qualified name of the class, but that is not a strict rule.
	 */
	public String getTrackableId();
	
	/**
	 * A standard equals functionality.  By convention, checks if the two values returened
	 * by getTrackableId() are equal and returns appropriately.
	 * 
	 * @param obj The (Trackable) object to test against.
	 * @return True if Strings returned by getTrackableId() match, false otherwise.
	 */
	public boolean equals(Object obj);
}
