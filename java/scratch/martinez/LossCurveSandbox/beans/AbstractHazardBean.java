package scratch.martinez.LossCurveSandbox.beans;

import java.beans.PropertyVetoException;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;

/**
 * This abstract definition defines the minimum functionality required for a
 * class to be considered a hazard bean. Implementations can use whichever
 * algorithm or computation method to produce the resulting hazard curves, but
 * they must all support this very basic method of retrieving a hazard curve.
 * 
 * @author 
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 */
public abstract class AbstractHazardBean extends AbstractBean {

	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------
	
	//---------------------------- Constant Members ---------------------------//

	// Implementation side effect for serialization.
	private static final long serialVersionUID = 0x0637D1;
	
	//----------------------------  Static Members  ---------------------------//

	/**
	 * A message displayed to users when they attempt to set the bean's current
	 * location and a listener vetoes the change.
	 */
	protected static final String LOCATION_CHANGE_VETOED = "The given " +
			"location did not fall in a known geographic region or was otherwise" +
			" invalid.";
	
	/**
	 * A message displayed to users when they attempt to set the bean's current
	 * IMT and a listener vetoes the change.
	 */
	protected static final String IMT_CHANGE_VETOED = "The given intensity " +
			"mesaure type is not supported or otherwise invalid.";
	
	/**
	 * The name of the property storing the bean's geographic location to compute
	 * hazard curves for.
	 */
	public static final String LOCATION_PROPERTY = 
		"AbstractHazardBean::curLocation";
	
	/**
	 * The name of the property storing the bean's current intensity measure
	 * type (IMT).
	 */
	public static final String IMT_PROPERTY = "AbstractHazardBean::imt";
	
	//---------------------------- Instance Members ---------------------------//
	
	/**
	 * The current location property.
	 */
	protected Location curLocation = null;
	
	/**
	 * The intensity measure type to use when mining the hazard curve.
	 */
	protected String imt =  null;
	
	
	//---------------------------------------------------------------------------
	// Abstract Methods
	//---------------------------------------------------------------------------
	
	/**
	 * Computes a hazard curve for the current settings of this beans internal
	 * state. If the bean is not properly configured (and consequently cannot
	 * properly compute a hazard curve), then <code>null</code> is returned.
	 * 
	 * @return A hazard curve created for the current bean properties.
	 */
	public abstract ArbitrarilyDiscretizedFunc getHazardCurve();	
	
	//---------------------------------------------------------------------------
	// Implemented Public Methods
	//---------------------------------------------------------------------------
	
	//------------------------ Public Setter Methods --------------------------//
	
	/**
	 * Attempts to set the location property of the bean. Locations may be
	 * constrained in a variety of ways so this implementation allows for
	 * veto-able listeners to veto the change before it is made. To ensure the
	 * requested change is made or to check the resulting location the bean is
	 * using, one should listen to the <code>LOCATION_PROPERTY</code> of this
	 * bean.
	 * 
	 * @param newLocation The new bean location to compute hazard curves for.
	 */
	public synchronized void setLocation(Location newLocation) {
		// Store away for later...
		Location oldLocation = curLocation;
		
		try {
			// Let listeners object...
			vetoableChanger.fireVetoableChange(LOCATION_PROPERTY, oldLocation,
					newLocation);
			
			// Make the change...
			curLocation = newLocation;
			
			// Notify of the change...
			propertyChanger.firePropertyChange(LOCATION_PROPERTY, oldLocation,
					newLocation);
		} catch (PropertyVetoException pvx) {
			getBeanEditor().infoPrompt(LOCATION_CHANGE_VETOED);
			// Somebody objected to the change. Undo.
			setLocation(curLocation);
		}
	}
	
	/**
	 * Attempts to set the intensity measure type (IMT) property of this bean.
	 * Listeners should listen to the <code>IMT_PROPERTY</code> to be notified of
	 * changes. This property is both constrained and bound.
	 * 
	 * @param newImt The new IMT value to use.
	 */
	public synchronized void setImt(String newImt) {
		// Store away for later...
		String oldImt = imt;
		
		try {
			// Let listeners object...
			vetoableChanger.fireVetoableChange(IMT_PROPERTY, oldImt, newImt);
			
			// Make the change...
			imt = newImt;
			
			// Notify of the change...
			propertyChanger.firePropertyChange(IMT_PROPERTY, oldImt, newImt);
		} catch (PropertyVetoException pvx) {
			getBeanEditor().infoPrompt(IMT_CHANGE_VETOED);
			// Somebody objected to the change. Undo.
			setImt(imt);
		}
		
	}
	
	//------------------------ Public Getter Methods --------------------------//
	
	/**
	 * @return The current location property for this hazard bean.
	 */
	public synchronized Location getLocation() { return curLocation; }
	
	/**
	 * @return The current IMT property for this hazard bean.
	 */
	public synchronized String getImt() { return imt; }

	//------------------------ Public Utility Methods -------------------------//

}
