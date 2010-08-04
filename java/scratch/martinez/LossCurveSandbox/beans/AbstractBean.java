package scratch.martinez.LossCurveSandbox.beans;

import java.beans.PropertyChangeListener;
import java.beans.PropertyChangeSupport;
import java.beans.PropertyVetoException;
import java.beans.VetoableChangeListener;
import java.beans.VetoableChangeSupport;

import scratch.martinez.LossCurveSandbox.ui.BeanEditorAPI;

/**
 * This is the abstract parent class of all beans implemented in this package (
 * or sub-packages). For any &ldquo;get&rdquo; method defined below, an
 * implementing class should override the corresponding &ldquo;set&rdquo; 
 * method (following JavaBeans naming conventions of course). All set methods
 * should be implemented in a synchronized fashion to support multi-threading
 * and access. Thus (due to language construct limitations), any setter declared
 * here is specified as synchronized but is implemented to just throw an
 * unchecked runtime exception.
 * 
 * @author 
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 *
 */
public abstract class AbstractBean implements BeanAPI {
	
	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------
	
	//---------------------------- Constant Members ---------------------------//

	// Implementation side-effect for serialization.
	private static final long serialVersionUID = 0xF38BAC;
	
	//----------------------------  Static Members  ---------------------------//

	public static String EDITOR_PROPERTY = "AbstractBean::editor";
	
	//---------------------------- Instance Members ---------------------------//

	/**
	 * Utility to manage property listeners and fire changes notifications.
	 */
	protected PropertyChangeSupport propertyChanger = null;
	
	/**
	 * Utility to manage veto listeners and fire veto-able changes.
	 */
	protected VetoableChangeSupport vetoableChanger = null;
	
	//---------------------------------------------------------------------------
	// Abstract Methods
	//---------------------------------------------------------------------------

	
	//------------------------ Abstract Setter Methods ------------------------//
	
	
	//------------------------ Abstract Getter Methods ------------------------//

	/**
	 * @return The current editor the bean knows about that can be used to
	 * interact between the bean and the user.
	 */
	public abstract BeanEditorAPI getBeanEditor();
	
	//------------------------ Abstract Utility Methods -----------------------//
	
	//---------------------------------------------------------------------------
	// Implemented Public Methods
	//---------------------------------------------------------------------------
	
	//------------------------ Public Setter Methods --------------------------//
	
	/**
	 * <p>
	 * Sets the editor that this bean will use for call backs to interact with
	 * the user. Note that while the bean only know about a single editor at a
	 * time, this does not imply that only one editor will be manipulating it.
	 * One should listen to the <code>EDITOR_PROPERTY</code> of the bean to 
	 * be notified of changes to this property. This property is not constrained 
	 * beyond being required to be of the proper type.
	 * </p>
	 * <p>
	 * The initial implementation does nothing but throw a runtime exception. An
	 * implementing class should override this method.
	 * </p>
	 * 
	 * @param newEditor The new editor to use.
	 * @throws ClassCastException If an inappropriate editor is given as the
	 * <code>newEditor</code> for this bean.
	 */
	public synchronized void setBeanEditor(BeanEditorAPI newEditor) 
			throws ClassCastException {
		throw new RuntimeException("This method should be overriden by an " +
				"implementing sub class!");
	}
	
	//------------------------ Public Getter Methods --------------------------//
	
	//------------------------ Public Utility Methods -------------------------//
	
	/**
	 * Wrapper method to allow external objects to add listeners to this bean's
	 * property changes.
	 * 
	 * @param propertyName The name of the property of interest.
	 * @param listener The listener who is interested in changes.
	 */
	public void addPropertyChangeListener(String propertyName,
			PropertyChangeListener listener) {
		propertyChanger.addPropertyChangeListener(propertyName, listener);
	}
	
	/**
	 * Wrapper method to allow external objects to remove themselves as one of
	 * this bean's property change listeners.
	 * 
	 * @param propertyName The name of the property no longer of interest.
	 * @param listener The listener who is no longer interested in changes.
	 */
	public void removePropertyChangeListener(String propertyName,
			PropertyChangeListener listener) {
		propertyChanger.removePropertyChangeListener(propertyName, listener);
	}
	
	/**
	 * Wrapper method to allow external objects to add themselves as a listener
	 * and objector to changes on this bean's properties.
	 * 
	 * @param propertyName The name of the property to listen for changes to.
	 * @param listener The listener interested in changes.
	 */
	public void addVetoableChangeListener(String propertyName,
			VetoableChangeListener listener) {
		vetoableChanger.addVetoableChangeListener(propertyName, listener);
	}
	
	/**
	 * Wrapper method to allow external objects to remove themselves as a
	 * listener or objector to changes on this bean's properties.
	 * 
	 * @param propertyName The name of the property no longer of interest.
	 * @param listener The listener no longer interested in changes.
	 */
	public void removeVetoableChangeListener(String propertyName,
			VetoableChangeListener listener) {
		vetoableChanger.removeVetoableChangeListener(propertyName, listener);
	}
	
	/**
	 * Wrapper method to allow external objects (namely an editor) to fire
	 * property change events on this bean's properties. Note that this method
	 * should be triggered <em>after</em> the internal state of the bean is
	 * changed.
	 * 
	 * @param propertyName The name of the property that changed.
	 * @param oldValue The old value of the property.
	 * @param newValue The new value of the property.
	 */
	public void firePropertyChange(String propertyName, Object oldValue,
			Object newValue) {
		propertyChanger.firePropertyChange(propertyName, oldValue, newValue);
	}
	
	/**
	 * Wrapper method to allow external objects (namely an editor) to fire
	 * veto-able change events on this beans constrained properties. Note that
	 * this method is triggered <em>before</em> the internal state of the bean is
	 * changed, thus allowing a listener to veto the change via throwing a
	 * <code>PropertyVetoException</code>.
	 * 
	 * @param propertyName The name of the property we want to change.
	 * @param oldValue The old (current) value of the property.
	 * @param newValue The (potential) new value of the property. 
	 * @throws PropertyVetoException If a listener vetoes the prospective change.
	 */
	public void fireVetoableChange(String propertyName, Object oldValue,
			Object newValue) throws PropertyVetoException {
		vetoableChanger.fireVetoableChange(propertyName, oldValue, newValue);
	}	
	
}
