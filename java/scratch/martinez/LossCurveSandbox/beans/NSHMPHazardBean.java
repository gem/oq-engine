package scratch.martinez.LossCurveSandbox.beans;

import java.beans.PropertyChangeEvent;
import java.beans.PropertyVetoException;
import java.util.Vector;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.nshmp.sha.data.HazardDataMinerServletMode;
import org.opensha.nshmp.util.GlobalConstants;

import scratch.martinez.LossCurveSandbox.ui.BeanEditorAPI;
import scratch.martinez.LossCurveSandbox.ui.HazardBeanEditor;

/**
 * Bean to calculator hazard curves using official USGS hazard models. These
 * curves are all pre-computed and are mined off of a remote data server. For
 * mining implementation details, see the various data mining calculators. An
 * NSHMP hazard bean allows users to specify a location along with site
 * conditions, imt, and data edition to have more granular control of the output
 * curve.
 * 
 * @author   
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 *
 */
public class NSHMPHazardBean extends AbstractHazardBean {
	
	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------
	
	//---------------------------- Constant Members ---------------------------//
	
	// Implementation side-effect for serialization.
	private static final long serialVersionUID = 0xF63553;
	
	/**
	 * A message displayed to the user when an attempt to change the data edition
	 * fails.
	 */
	protected static final String EDITION_CHANGE_VETOED = "The selected data " +
			"edition is currently unavailable.";
	
	/**
	 * A message displayed to the user when an attempt to change the location
	 * would result in a region change that fails.
	 */
	protected static final String REGION_CHANGE_VETOED = "The input location " +
			"would change to an invalid region.";
	
	/**
	 * The property name for the current region. Note this value is not directly
	 * set, but is computed based on the current location.
	 */
	public static final String REGION_PROPERTY = 
		"NSHMPHazardBean::geographicRegion";
	
	/**
	 * The property name for the current data edition for this bean.
	 */
	public static final String EDITION_PROPERTY = "NSHMPHazardBean::dataEdition";
	
	//----------------------------  Static Members  ---------------------------//
	
	// A shared instance of this bean to support the singleton structure.
	private static NSHMPHazardBean instance = null;
	
	// Region Bounds for the Possible Regions
	protected static Region STATES_REGION      = null;
	protected static Region ALASKA_REGION      = null;
	protected static Region HAWAII_REGION      = null;
	protected static Region PUERTO_RICO_REGION = null;
	protected static Region CULEBRA_REGION     = null;
	protected static Region ST_CROIX_REGION    = null;
	protected static Region ST_JOHN_REGION     = null;
	protected static Region ST_THOMAS_REGION   = null;
	protected static Region VIEQUES_REGION     = null;
	
	//---------------------------- Instance Members ---------------------------//

	/**
	 * The editor used to interact between the user and this bean.
	 */
	private HazardBeanEditor editor = null;
	
	/**
	 * The miner used to fetch curves from the server.
	 */
	private HazardDataMinerServletMode miner = null;
	
	/**
	 * The currently selected data edition to mine data from.
	 */
	protected String dataEdition = null;
	
	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------
	
	/**
	 * Default, no-arg constructor. Creates an instance of this bean. If a
	 * developer wishes to get a shared instance, then they should make a call
	 * to the static <code>getSharedInstance()</code> method rather than
	 * constructing a new instance here.
	 */
	public NSHMPHazardBean() {
		this(null);
	}
	
	/**
	 * Creates an instance of this bean. The default editor for this bean is set
	 * to the given editor. If a developer wishes to get a shared instance, then
	 * they should make a call to the static <code>getSharedInstance()</code>
	 * method rather than constructing a new instance here.
	 * 
	 * @param defaultEditor The editor to use.
	 */
	public NSHMPHazardBean(HazardBeanEditor defaultEditor) {
		dataEdition = getAvailableDataEditions(null).get(0);
		editor = defaultEditor;
		miner = new HazardDataMinerServletMode();
	}
	
	/**
	 * A static initialization of static-only members. This is called only once
	 * the very first time this class is accessed in any way.
	 */
	static {
//		try {
			/* Initialize all the geographic regions for user later. */
			//STATES_REGION = new Region(24.7, 50, -125, -65);
			STATES_REGION = new Region(
					new Location(24.7, -125),
					new Location(50, -65));
			//ALASKA_REGION = new Region(48, 72, -200, -125);
			ALASKA_REGION = new Region(
					new Location(48, -200),
					new Location(72, -125));
			//HAWAII_REGION = new Region(18, 23, -161, -154);
			HAWAII_REGION = new Region(
					new Location(18, -161),
					new Location(23, -154));
//			PUERTO_RICO_REGION =
//				new Region(17.89, 18.55, -67.36, -65.47);
			PUERTO_RICO_REGION =
				new Region(
						new Location(17.89, -67.36),
						new Location(18.55, -65.47));
//			CULEBRA_REGION = 
//				new Region(17.67, 17.8, -64.93, -64.54);
			CULEBRA_REGION = 
				new Region(
						new Location(17.67, -64.93),
						new Location(17.8, -64.54));
//			ST_CROIX_REGION = 
//				new Region(18.27, 18.36, -65.39, -65.21);
			ST_CROIX_REGION = 
				new Region(
						new Location(18.27, -65.39),
						new Location(18.36, -65.21));
//			ST_JOHN_REGION = 
//				new Region(18.29, 18.38, -64.85, -64.65);
			ST_JOHN_REGION = 
				new Region(
						new Location(18.29, -64.85),
						new Location(18.38, -64.65));
//			ST_THOMAS_REGION = 
//				new Region(18.26, 18.43, -65.10, -64.80);
			ST_THOMAS_REGION = 
				new Region(
						new Location(18.26, -65.10),
						new Location(18.43, -64.80));
//			VIEQUES_REGION = 
//				new Region(18.07, 18.17, -65.6, -65.25);
			VIEQUES_REGION = 
				new Region(
						new Location(18.07, -65.6),
						new Location(18.17, -65.25));
//		} ca//		} catch (RegionConstraintException rcx) {
//			rcx.printStackTrace();
//		}
	}
	
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------
	
	//------------------------- Public Setter Methods -------------------------//

	/**
	 * Attempts to set the location property of the bean. Locations may be
	 * constrained in a variety of ways so this implementation allows for
	 * veto-able listeners to veto the change before it is made. To ensure the
	 * requested change is made or to check the resulting location the bean is
	 * using, one should listen to the <code>LOCATION_PROPERTY</code> of this
	 * bean. If the location change results in a change to the region as well,
	 * then a appropriate notifications will be fired for that as well. One
	 * should listen to the <code>REGION_PROPERTY</code> of this bean to be
	 * notified when this changes.
	 * 
	 * @param newLocation The new bean location to compute hazard curves for.
	 */
	public synchronized void setLocation(Location newLocation) {
		// Store away for later...
		Location oldLocation = getLocation();
		String oldRegion = getGeographicRegion(oldLocation);
		String newRegion = getGeographicRegion(newLocation);
		
		try {
			// Let listeners object...
			vetoableChanger.fireVetoableChange(LOCATION_PROPERTY, oldLocation,
					newLocation);
			vetoableChanger.fireVetoableChange(REGION_PROPERTY, oldRegion,
					newRegion);
			
			// Make the change...
			curLocation = newLocation;
			
			// Notify of the change...
			propertyChanger.firePropertyChange(LOCATION_PROPERTY, oldLocation,
					newLocation);
			propertyChanger.firePropertyChange(REGION_PROPERTY, oldRegion,
					newRegion);
		} catch (PropertyVetoException pvx) {
			getBeanEditor().infoPrompt(LOCATION_CHANGE_VETOED);
			// Somebody objected to the change. Undo.
			setLocation(curLocation);
		}
	}
	
	/**
	 * Attempts to set the data edition to the <code>newEdition</code>.
	 * Interested parties can listen to the <code>EDITION_PROPERTY</code>
	 * property to be informed of changes to this property. This property is
	 * both bound and constrained.
	 */
	public synchronized void setDataEdition(String newEdition) {
		// Store away for later...
		String oldEdition = dataEdition;
		try {
			// Let listeners object...
			vetoableChanger.fireVetoableChange(EDITION_PROPERTY, oldEdition,
					newEdition);
			
			// Make the change...
			dataEdition = newEdition;
			
			// Notify of the change...
			propertyChanger.firePropertyChange(EDITION_PROPERTY, oldEdition,
					newEdition);
		} catch (PropertyVetoException pvx) {
			getBeanEditor().infoPrompt(EDITION_CHANGE_VETOED);
			// Somebody objected to the change. Undo.
			setDataEdition(dataEdition);
		}
	}
	
	//------------------------- Public Getter Methods -------------------------//
	
	/**
	 * See the general contract specified in <code>AbstractBean</code>.
	 */
	public BeanEditorAPI getBeanEditor() {	return editor; }
	
	/**
	 * @return The current data edition to mine hazard curve for.
	 */
	public String getDataEdition() { return dataEdition; }
	
	/**
	 * @return The &ldquo;singleton&rdquo; shared instance of this bean.
	 */
	public static NSHMPHazardBean getSharedInstance() {
		if(instance == null) {
			instance = new NSHMPHazardBean();
		}
		return instance;
	}
	
	/**
	 * Determines the current geographic region name based on the input location
	 * properties.
	 * 
	 * @return The name of the current geographic region.
	 */
	public String getGeographicRegion(Location location) {
		// The region for the current location...
		String regionName = null;
		
		if(STATES_REGION.contains(location)) {
			regionName = GlobalConstants.CONTER_48_STATES;
		} else if (ALASKA_REGION.contains(location)) {
			regionName = GlobalConstants.ALASKA;
		} else if (HAWAII_REGION.contains(location)) {
			regionName = GlobalConstants.HAWAII;
		} else if (PUERTO_RICO_REGION.contains(location)) {
			regionName = GlobalConstants.PUERTO_RICO;
		} else if (CULEBRA_REGION.contains(location)) {
			regionName = GlobalConstants.CULEBRA;
		} else if (ST_CROIX_REGION.contains(location)) {
			regionName = GlobalConstants.ST_CROIX;
		} else if (ST_JOHN_REGION.contains(location)) {
			regionName = GlobalConstants.ST_JOHN;
		} else if (ST_THOMAS_REGION.contains(location)) {
			regionName = GlobalConstants.ST_THOMAS;
		} else if (VIEQUES_REGION.contains(location)) {
			regionName = GlobalConstants.VIEQUES;
		}
		return  regionName;
	}
	
	//------------------------- Public Utility Methods ------------------------//

	/**
	 * Retrieves an NSHMP Hazard Curve by mining the data from pre-computed
	 * hazard curve files. The specific file used to mine data from depends on
	 * the input location, data edition, and curve type. For more details on this
	 * method, see the parent signature in <code>AbstractHazardBean</code>.
	 */
	public ArbitrarilyDiscretizedFunc getHazardCurve() {
		// Gather our parameters...
		Location curLoc       = getLocation();
		String currentRegion  = getGeographicRegion(curLoc);
		String currentEdition = getDataEdition();
		String curveType      = getImt();
		double latitude       = curLoc.getLatitude();
		double longitude      = curLoc.getLongitude();
		
		// Check our parameters...
		if(currentRegion == null || "".equals(currentRegion) ||
				currentEdition == null || "".equals(currentEdition) ||
				curveType == null || "".equals(curveType) ||
				Double.isNaN(latitude) || Double.isNaN(longitude) 
			) {
			throw new IllegalStateException("The bean is not ready to  compute " +
					"a hazard curve at this time.");
		}
		// Get the curve to return...
		return miner.getBasicHazardcurve(currentRegion, currentEdition, latitude,
				longitude, curveType);
	}
	
	/**
	 * Builds a list of available data editions based on the given
	 * <code>regionName</code>. If <code>regionName</code> is <code>null</code>
	 * then all editions are available by default.
	 * 
	 * @param currentRegion The region to get available editions for. Can be
	 * <code>null</code> and if so, then the bean uses its current location to
	 * determine the region.
	 * @return A list of currently available data editions. This will never be
	 * <code>null</code> or empty, if no region is specified then all editions
	 * are available by default.
	 */
	public Vector<String> getAvailableDataEditions(String regionName) {
		// Create the object to return.
		Vector<String> editions = new Vector<String>();
		
		if(GlobalConstants.CONTER_48_STATES.equals(regionName)) {
			editions.add(GlobalConstants.data_2002);
			editions.add(GlobalConstants.data_1996);
		} else if (GlobalConstants.ALASKA.equals(regionName) ||
				GlobalConstants.HAWAII.equals(regionName) ) {
			editions.add(GlobalConstants.data_1998);
		} else if (GlobalConstants.PUERTO_RICO.equals(regionName) ||
				GlobalConstants.CULEBRA.equals(regionName) ||
				GlobalConstants.ST_CROIX.equals(regionName) ||
				GlobalConstants.ST_JOHN.equals(regionName) ||
				GlobalConstants.ST_THOMAS.equals(regionName) ||
				GlobalConstants.VIEQUES.equals(regionName) ) {
			editions.add(GlobalConstants.data_2003);
		} else {
			// Add all editions by default (in a specific order).
			editions.add(GlobalConstants.data_2002);
			editions.add(GlobalConstants.data_1996);
			editions.add(GlobalConstants.data_1998);
			editions.add(GlobalConstants.data_2003);
		}
		return editions;
	}
	
	/**
	 * Implements the <code>VetoableChangeListener</code> to listen for changes
	 * to the geographic region and data edition properties. When changes to
	 * either of these properties are attempted, they are first validated here.
	 * 
	 * @param evt The property change event that triggered this call.
	 * @throws PropertyVetoException If the property is trying to be changed to
	 * an invalid value.
	 */
	public void vetoableChange(PropertyChangeEvent evt) 
			throws PropertyVetoException {
		String propertyName = evt.getPropertyName();
		
		if(EDITION_PROPERTY.equals(propertyName)) {
			validateNewEdition(evt, (String) evt.getNewValue());
		} else if (REGION_PROPERTY.equals(propertyName)) {
			// If the region changes, we want to automatically update the data
			// edition to something that is appropriate/available.
			validateNewRegion((String) evt.getNewValue());
		} else if (LOCATION_PROPERTY.equals(propertyName)) {
			validateNewLocation(evt, (Location) evt.getNewValue());
		}
	}
	
	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------
	
	/**
	 * Checks the current settings of this beans properties to make sure the new
	 * region is currently valid. If the region not valid for the data edition,
	 * then the data edition is changed to reflect a corresponding edition that
	 * is valid for this region.
	 * 
	 * @param regionName The new region name.
	 */
	public void validateNewRegion(String regionName) {
		
		if (GlobalConstants.CONTER_48_STATES.equals(regionName)) {

			// Make sure we have an appropriate data edition.
			if(!GlobalConstants.data_2002.equals(dataEdition) &&
					!GlobalConstants.data_1996.equals(dataEdition)) {
				// Set the data edition to appropriate.
				setDataEdition(GlobalConstants.data_2002);
			}
			
		} else if (GlobalConstants.ALASKA.equals(regionName) ||
				GlobalConstants.HAWAII.equals(regionName)) {
			
			// Make sure we have an appropriate data edition.
			if(!GlobalConstants.data_1998.equals(dataEdition)) {
				// Set the data edition to appropriate.
				setDataEdition(GlobalConstants.data_1998);
			}
			
		} else {
			
			// Make sure we have an appropriate data edition.
			if(!GlobalConstants.data_2003.equals(dataEdition)) {
				// Set the data edition to appropriate.
				setDataEdition(GlobalConstants.data_2003);
			}
			
		}
	}
	
	/**
	 * Checks the current settings of this beans properties to make sure the new
	 * data edition is valid.
	 * 
	 * @param editionName The new edition name.
	 * @throws PropertyVetoException If the new data edition is not currently
	 * valid.
	 */
	private void validateNewEdition(PropertyChangeEvent evt, String editionName)
			throws PropertyVetoException {
		// Get a list of available editions.
		Vector<String> availEditions = getAvailableDataEditions(
				getGeographicRegion(getLocation())
			);
		
		// Check our list against what we received.
		if(! availEditions.contains(editionName)) {
			PropertyVetoException pvx = new PropertyVetoException(
					EDITION_CHANGE_VETOED, evt);
			pvx.fillInStackTrace();
			throw pvx;
		}
	}

	/**
	 * Checks the current settings of this beans properties to make sure the new
	 * location is valid.
	 * 
	 * @param location The new input location.
	 * @throws PropertyVetoException If the new location does not fall within a
	 * known geographic region.
	 */
	public void validateNewLocation(PropertyChangeEvent evt, Location location)
			throws PropertyVetoException {
		if(getGeographicRegion(location) == null) {
			PropertyVetoException pvx = new PropertyVetoException(
					LOCATION_CHANGE_VETOED, evt);
			pvx.fillInStackTrace();
			throw pvx;
		}
	}
}
