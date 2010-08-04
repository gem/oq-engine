package scratch.martinez.LossCurveSandbox.beans;

import java.beans.PropertyChangeEvent;
import java.beans.PropertyChangeListener;
import java.beans.PropertyChangeSupport;
import java.beans.VetoableChangeSupport;

import org.opensha.commons.geo.Location;

import scratch.martinez.LossCurveSandbox.calculators.SiteClassCalculator;
import scratch.martinez.LossCurveSandbox.ui.BeanEditorAPI;
import scratch.martinez.LossCurveSandbox.ui.SiteBeanEditor;

/**
 * This class represents a site object. A site consists of a geographic location
 * and site soil conditions. Both are important for calculating risk/loss. Sub
 * classes may consider adding structures to the site but this most basic
 * site does not include that information.
 * 
 * @author  
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 */
public class SiteBean extends AbstractBean
		implements PropertyChangeListener {

	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------

	//---------------------------- Constant Members ---------------------------//

	// Implementation side-effect for serialization.
	private static final long serialVersionUID = 0x62EACA5;
	
	//----------------------------  Static Members  ---------------------------//

	//---------------------------- Instance Members ---------------------------//

	/**
	 * The editor this bean currently considers its bean editor.
	 */
	private SiteBeanEditor editor = null;
	
	/**
	 * The shared instance  of this bean. Usefull if a parent application would
	 * like to utilize a singleton structure.
	 */
	private static SiteBean instance = null;
	
	/**
	 * The location bean associated with this site. Any interaction with
	 * location properties will be passed off to this bean. Note this bean is
	 * itself not a property of the bean and can only be defined at time of
	 * instantiation.
	 */
	private LocationBean locationBean = null;
	
	/**
	 * The name of the current site class. If the location bean does not have
	 * a location, then this will display the default site class for the current
	 * site class calculator.
	 */
	private String siteClassName = null;
	
	/**
	 * The site class calculator used to look up site class values.
	 */
	private SiteClassCalculator siteClassCalc = null;
	
	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------

	/**
	 * Default no-arg constructor. Uses the
	 * <code>LocationBean.getSharedInstance()</code> location as its associated
	 * location bean. The location bean can only be set at time of instantiation
	 * and cannot be later changed.
	 */
	public SiteBean() {
		this(LocationBean.getSharedInstance());
	}
	
	/**
	 * Creates a new <code>SiteBean</code> using the given
	 * <code>defaultLocBean</code> as the associated location bean for this
	 * bean. The location bean can only be set at time of instantiation and
	 * cannot be later changed.
	 * 
	 * @param defaultLocBean The location bean to use. This should not be
	 * <code>null</code> and one should consider using the no-arg version for
	 * such cases.
	 */
	public SiteBean(LocationBean defaultLocBean) {
		locationBean = defaultLocBean;
		
		propertyChanger = new PropertyChangeSupport(this);
		vetoableChanger = new VetoableChangeSupport(this);
		
		// Listen for changes to the location so we can update the site soil
		// conditions.
		locationBean.addPropertyChangeListener(
				LocationBean.LOCATION_PROPERTY, this);
	}
	
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//------------------------- Public Setter Methods  ------------------------//

	//------------------------- Public Getter Methods  ------------------------//

	/**
	 * See the general contract specified in <code>AbstractBean</code>.
	 */
	public BeanEditorAPI getBeanEditor() {
		return editor;
	}
	
	/**
	 * @return The shared instance of this bean that can be used in a singleton
	 * structured application.
	 */
	public static SiteBean getSharedInstance() {
		if(instance == null) {
			instance = new SiteBean();
		}
		return instance;
	}
	
	/**
	 * Retrieves the nested location bean.
	 * @return The current location bean.
	 */
	public LocationBean getLocationBean() { return locationBean; }

	/**
	 * Retrieves the current location stored in the underlying bean.
	 * @return The current location.
	 */
	public Location getLocation() { return  locationBean.getLocation(); }
	
	/**
	 * @return The name of the current site class.
	 */
	public String getSiteClassName() { return siteClassName; }
	
	/**
	 * @return The description of the current site class.
	 */
	public String getSiteClassDescription() {
		return siteClassCalc.getSiteClassDescription(siteClassName);
	}
	
	//------------------------- Public Utility Methods ------------------------//

	/**
	 * <p>
	 * Method to implement the <code>PropertyChangeListener</code> interface.
	 * This listener listens to the following properties:
	 * </p>
	 * <ul>
	 * <li>
	 * <strong>LocationBean.LOCATION_PROPERTY</strong>: Updates the site soil
	 * conditions when the location changes.
	 * </li>
	 * </ul>
	 * 
	 * @param evt The <code>PropertyChangeEvent</code> that triggered this call.
	 */
	public void propertyChange(PropertyChangeEvent evt) {
		String propName = evt.getPropertyName();
		
		if(LocationBean.LOCATION_PROPERTY.equals(propName)) {
			updateSiteConditions();
		}
	}
	
	/**
	 * This method wraps the underlying bean such that an external object can
	 * request to be added to a nested bean's property through a direct request
	 * to this bean.
	 * 
	 * @param propertyName The name of the property to listen for.
	 * @param listener The listener interested in changes.
	 */
	public void addPropertyChangeListener(String propertyName,
			PropertyChangeListener listener) {
		
		if(LocationBean.LOCATION_PROPERTY.equals(propertyName)) {
			// Request is to listen for location property, so pass that off to the
			// nested location bean.
			locationBean.addPropertyChangeListener(propertyName, listener);
		} else {
			// Request is for one of our properties, so add it.
			propertyChanger.addPropertyChangeListener(propertyName, listener);
		}
	}
	
	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------

	/**
	 * Updates the site conditions in whichever manner is currently preferred.
	 * The default method is to look up site conditions for sites located in
	 * California using the <code>WillsSiteClassCalc</code>. Future 
	 * implementations may also support a global option (possibly using Wald et
	 * al.) or other lookup methods. The user can also manually set a site class
	 * value. If the site class cannot be looked up and is not explicitly set,
	 * the site class defaults to the B/C boundary.
	 */
	private void updateSiteConditions() {
		
	}
}
