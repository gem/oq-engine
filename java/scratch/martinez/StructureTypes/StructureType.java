package scratch.martinez.StructureTypes;

import java.util.ArrayList;
import java.util.TreeMap;

import scratch.martinez.Trackable;

/**
 * This class serves as the base class for all other structure types.  All structure
 * types must be <code>Trackable</code> in order that we might maintain a relationship
 * between supported vulnerabilities/structure types.
 * 
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 */
public abstract class StructureType implements Trackable {
	private static ArrayList<Trackable> registeredTypes = new ArrayList<Trackable>();
	private static TreeMap<String, ArrayList<Trackable>> tracker = new TreeMap<String, ArrayList<Trackable>>();
	// A list of fully qualified class names that the implementing StructureType Supports (i.e. Vulnerabilities)
	protected ArrayList<String> supportedTypes = null;
	
	////////////////////////////////////////////////////////////////////////////////
	//                    Minimum Functions to Implement Trackable                //
	////////////////////////////////////////////////////////////////////////////////
	/**
	 * See the generic contract in Trackable.
	 * @see Trackable
	 */
	public ArrayList<Trackable> getRegisteredTypes() {
		return registeredTypes;
	}

	/**
	 * See the generic contract in Trackable.
	 * @see Trackable
	 */
	public ArrayList<Trackable> getSupportedTypes(Trackable obj) {
		String tId = obj.getTrackableId();
		ArrayList<Trackable> rtn = null;
		if(tracker.containsKey(tId)) {
			rtn = tracker.get(tId);
		}
		return rtn;
	}

	/**
	 * See the generic contract in Trackable.
	 * @see Trackable
	 */
	public String getTrackableId() {
		String str = (this.getClass()).toString();
		return str.substring(6);
	}

	/**
	 * See the generic contract in Trackable.
	 * @see Trackable
	 */
	public void register(ArrayList<String> types) {
		Trackable t = (Trackable) this;
		
		// Add this to the list of known registered types.
		if(registeredTypes.indexOf(t) == -1)
			registeredTypes.add(t);
		
		// Add all the supported types to the tracker
		for(int i = 0; i < types.size(); ++i) {
			String type = types.get(i);
			ArrayList<Trackable> supported = tracker.get(type);
			if(supported == null)
				supported = new ArrayList<Trackable>();
			supported.add(t);
			tracker.put(type, supported);
		}
	}
	
	/**
	 * See the generic contract in Trackable.
	 * @see Trackable
	 */
	public boolean equals(Object o) {
		if(o == null) return false;
		if(! (o instanceof StructureType) ) return false;
		String tId = this.getTrackableId();
		String oId = (o.getClass().toString()).substring(6);
		return tId.equals(oId);
	}
	
	
	////////////////////////////////////////////////////////////////////////////////
	//                               Public Functions                             //
	////////////////////////////////////////////////////////////////////////////////
	
	/**
	 * @return An <code>ArrayList</code> of currently registered <code>StructureTypes</code>
	 */
	public ArrayList<StructureType> getLibraryOfTypes() {
		ArrayList<StructureType> st = new ArrayList<StructureType>();
		for(int i = 0; i < registeredTypes.size(); ++i) {
			st.add( ( (StructureType) registeredTypes.get(i) ) );
		}
		return st;
	}
	
	/**
	 * @return An <code>ArrayList</code> of types that are supported by the implementing <code>StructureType</code>
	 */
	public ArrayList<String> getSupportedTypes() {
		return supportedTypes;
	}
}
