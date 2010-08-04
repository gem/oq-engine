package scratch.martinez.LossCurveSandbox.beans;

import java.beans.PropertyChangeEvent;
import java.beans.PropertyChangeSupport;
import java.beans.PropertyVetoException;
import java.beans.VetoableChangeListener;
import java.beans.VetoableChangeSupport;

import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.Location;

import scratch.martinez.LossCurveSandbox.ui.BeanEditorAPI;
import scratch.martinez.LossCurveSandbox.ui.LocationBeanEditor;

/**
 * This class represents the idea of a geographic location.  A location consists
 * of a latitude and longitude. Many larger beans might use a location bean
 * as a component since locations are quite common. This bean will fire
 * property change and vetoable change notifications on its
 * <code>LOCATION_PROPERTY</code> property for interested listeners.
 * 
 * @author  
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 */
public class LocationBean extends AbstractBean
		implements VetoableChangeListener {

	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------

	//---------------------------- Constant Members ---------------------------//

	// Implementation side-effect for serialization.
	private static final long serialVersionUID = 0x73BDEAC;
	
	/**
	 * Message displayed when a <code>null</code> editor or a non-LocationBean
	 * editor is attempted be used as this bean's editor.
	 */
	protected static final String EDITOR_VETOED_MESSAGE = "Attempted to set " +
			"editor of this bean to a null or otherwise inappropriate editor.";
	
	/**
	 * Message displayed when the location specified is non-geographic.
	 */
	protected static final String NON_GEOGRAPHIC_LOCATION_MESSAGE = "The " +
			"input location was non-geographic.";
	/**
	 * Name of property storing the current location.
	 */
	public static final  String LOCATION_PROPERTY = "LocationBean::location";
	
	//----------------------------  Static Members  ---------------------------//

	/**
	 * The shared instance of this class. This instance is returned from a call
	 * to the <code>getSharedInstance()</code> method.
	 */
	private static LocationBean instance = null;
	
	//---------------------------- Instance Members ---------------------------//

	/**
	 * Editor used to manipulate this bean.
	 */
	private LocationBeanEditor editor = null;
	
	/**
	 * The composite location property for this bean.
	 */
	private Location location = null;
	
	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------

	/**
	 * Default, no-arg constructor. Creates a new instance of a location bean
	 * with no associated editor. One should explicitly set the editor later with
	 * a call to <code>setEditor(LocationBeanEditor)</code>.
	 */
	public LocationBean() {
		// Create the property change managers.
		propertyChanger = new PropertyChangeSupport(this);
		vetoableChanger = new VetoableChangeSupport(this);
		
		// This bean constrains its editor to non-null and of appropriate type.
		addVetoableChangeListener(EDITOR_PROPERTY, this);
	}
	
	/**
	 * Creates a new instance of a location bean with the
	 * <code>defaultEditor</code> as the current editor.
	 * 
	 * @param defaultEditor The editor used to manipulate this bean.
	 */
	public LocationBean(LocationBeanEditor defaultEditor) {
		this();
		setEditor(defaultEditor);
	}
	
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//------------------------- Public Setter Methods  ------------------------//
	
	/**
	 * Preferred way to set the location (latitude and longitude) of this bean.
	 * Listeners interested in changes to this property should listen to the
	 * <code>LocationBean.LOCATION_PROPERTY</code> property of this class. Note
	 * that while a location is composed of a latitude and longitude value, one
	 * may only listen to changes made to the location as a whole and not the
	 * individual values. One should never object to a <code>null</code> location
	 * change since this is essentially just clearing the change.
	 *  
	 * @param newLocation The new location to use for this bean.
	 */
	public synchronized void setLocation(double latitude, double longitude) {
		// Store away for later.
		Location oldLocation = location;
		
		try {
			Location newLocation = null;
			if(!Double.isNaN(latitude) && !Double.isNaN(longitude)) {
				newLocation = new Location(latitude, longitude, 0.0);
			}
			
			// Let listeners veto the change....
			vetoableChanger.fireVetoableChange(LOCATION_PROPERTY, 
					oldLocation, newLocation);
			
			// Make the change...
			location = newLocation;
			
			// Notify listeners of the change...
			propertyChanger.firePropertyChange(LOCATION_PROPERTY,
					oldLocation, newLocation);
			
		} catch (PropertyVetoException pvx) {
			// Somebody objected, stick with old location and notify.
			editor.infoPrompt(pvx.getMessage() + "\nReverting to old value.");
			setLocation(oldLocation.getLatitude(), oldLocation.getLongitude());
		} catch (InvalidRangeException irx) {
			// Location was non-geographic.
			editor.infoPrompt(NON_GEOGRAPHIC_LOCATION_MESSAGE + "\nReverting to " +
					"old values.");
			setLocation(oldLocation.getLatitude(), oldLocation.getLongitude());
		}
		
	}
	
	/**
	 * Clears this beans current location. A call to this method will properly
	 * notify all listeners (vetoes and otherwise), of this beans
	 * <code>LOCATION_PROPERTY</code> property, but this change should never be
	 * vetoed to.
	 */
	public synchronized void clearLocation() {
		setLocation(Double.NaN, Double.NaN);
	}
	
	/**
	 * Method to update the editor used to manipulate this bean instance. Note
	 * that while a bean may only know about one editor at a time, there can be
	 * many editors manipulating this bean. For this reason, each editor should
	 * listen to property change events for any properties that they edit to
	 * ensure they always know about the most current values.
	 * 
	 * @param newEditor The new editor used to communicate with the user.
	 */
	public synchronized void setEditor(LocationBeanEditor newEditor) {
		// Store away for later.
		LocationBeanEditor oldEditor = editor;
		
		try {
			// Let listeners veto the change....
			vetoableChanger.fireVetoableChange(EDITOR_PROPERTY, 
					oldEditor, newEditor);
			
			// Make the change...
			editor = newEditor;
			
			// Notify listeners of the change...
			propertyChanger.firePropertyChange(LOCATION_PROPERTY,
					oldEditor, newEditor);
			
		} catch (PropertyVetoException pvx) {
			// Somebody objected, stick with old location and notify.
			System.err.println(pvx.getMessage() + "\nReverting to old value.");
			setEditor(oldEditor);
		}
		
	}
	
	//------------------------- Public Getter Methods  ------------------------//
	
	/**
	 * @return A shared instance of this bean class. This is useful if a parent
	 * application would like to have a common instance (singleton) of this bean
	 * to share throughout the application.
	 */
	public synchronized static LocationBean getSharedInstance() {
		return getSharedInstance(null);
	}
	
	/**
	 * @param defaultEditor The default editor to use with this instance.
	 * @return A shared instance of this bean class. This is useful if a parent
	 * application would like to have a common instance (singleton) of this bean
	 * to share throughout the application.
	 */
	public synchronized static LocationBean getSharedInstance(
			LocationBeanEditor defaultEditor) {

		// Instantiate the instance if it has not been done yet.
		if(instance == null) {
			instance = new LocationBean();
		}
		
		// Update the instance editor if non-null
		if(defaultEditor != null) {
			instance.setEditor(defaultEditor);
		}
		
		return instance;
	}
	
	/**
	 * See the general contract defined in <code>AbstractBean</code>.
	 */
	public BeanEditorAPI getBeanEditor() {
		return editor;
	}
	
	/**
	 * @return The current location for this location bean. May be null if
	 * location has not yet been set.
	 */
	public synchronized Location getLocation() { return location; }
	
	/**
	 * Checks if this beans location has been properly set.
	 * @return <code>true</code> if this bean has a location, <code>false</code>
	 * otherwise.
	 */
	public synchronized boolean locationReady() {
		return (location != null);
	}
	
	//------------------------- Public Utility Methods ------------------------//

	/**
	 * <p>
	 * Validates property changes for this bean. The following properties are
	 * internally validated by this bean.
	 * </p>
	 * <ul>
	 * <li><strong>EDITOR_PROPERTY</strong>: Validates the editor is non-null and
	 * appropriate for this bean. See the general contract defined in
	 * <code>VetoableChangeListener</code>.
	 * </li>
	 * 
	 * </ul>
	 * 
	 * @param evt The <code>PropertyChangeEvent</code> that triggered this
	 * method.
	 * @throws PropertyVetoException If the new value of the property identified
	 * by the <code>evt</code> specifies an invalid value.
	 */
	public void vetoableChange(PropertyChangeEvent evt) 
			throws PropertyVetoException {
		String propertyName = evt.getPropertyName();
		
		if(EDITOR_PROPERTY.equals(propertyName)) {
			Object obj = evt.getNewValue();
			if(obj == null || !(obj instanceof LocationBeanEditor)) {
				PropertyVetoException pvx = new PropertyVetoException(
						EDITOR_VETOED_MESSAGE, evt);
				pvx.fillInStackTrace();
				throw pvx;				
			}
		}
	}
	
	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------
}
