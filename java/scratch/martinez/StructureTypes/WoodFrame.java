package scratch.martinez.StructureTypes;

import java.util.ArrayList;

/**
 * A sample implementation of a <code>StructureType</code>.  This is a fairly simple
 * example, and a structure can have much more information about it. This class is not
 * currently used.
 * 
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 */
public class WoodFrame extends StructureType {
	public WoodFrame() {
		supportedTypes = new ArrayList<String>();
		supportedTypes.add("scratchJavaDevelopers.martinez.KLPGAVlnFn");
		register(supportedTypes);
	}
}
