package scratch.martinez.LossCurveSandbox.beans;

import java.beans.PropertyChangeEvent;
import java.beans.PropertyChangeSupport;
import java.beans.PropertyVetoException;
import java.beans.VetoableChangeListener;
import java.beans.VetoableChangeSupport;

import scratch.martinez.LossCurveSandbox.ui.BeanEditorAPI;
import scratch.martinez.LossCurveSandbox.ui.IMTBeanEditor;

/**
 * This bean provides a basic component for applications to store instensity
 * measure types (IMT). Common intensity measure types include:
 * <ul style="list-style:none;">
 * <li>Peak Ground Acceleration (PGA)</li>
 * <li>Spectral Acceleration (with various frequencies)</li>
 * </ul>
 * Keep in mind that different IMT values might make sense for other hazards
 * outside of seismic hazards.
 * 
 * @author 
 * <a href="mailto:emartinez@usgs.gov?subject=OpenSHA%20Code%20Question">
 * Eric Martinez
 * </a>
 */
public class IMTBean extends AbstractBean
		implements BeanAPI, VetoableChangeListener {

	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------
	
	//---------------------------- Constant Members ---------------------------//

	// Implementation side effect for serialization.
	private static final long serialVersionUID = 0x33D5B64;
	
	/**
	 * Name of the Intensity Measure Type property to listen for changes to.
	 */
	public static final String IMT_PROPERTY = "IMTBean::imt";
	
	//----------------------------- Static Members ----------------------------//
	
	/**
	 * Name of the editor property to listen for changes to.
	 */
	public static String EDITOR_PROPERTY = "IMTBean::editor";
	
	//---------------------------- Instance Members ---------------------------//

	/**
	 * This is the current intensity measure type to use.
	 */
	private String imt = null;
	
	/**
	 * This is the current editor being used to manipulate this bean.
	 */
	private IMTBeanEditor editor = null;
	
	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------
	
	/**
	 * Default no-arg constructor. Instantiates a new instance of this bean with
	 * a <code>null</code> editor. One should not attempt to use this instance
	 * before setting the editors as bad things may happen.
	 */
	public IMTBean() {
		// Create the property change managers.
		propertyChanger = new PropertyChangeSupport(this);
		vetoableChanger = new VetoableChangeSupport(this);
		
		// This bean constrains its editor to non-null and of appropriate type.
		addVetoableChangeListener(EDITOR_PROPERTY, this);
	}
	
	public IMTBean(IMTBeanEditor defaultEditor) {
		this();
		setEditor(defaultEditor);
	}
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//----------------------------- Public Setters ----------------------------//

	/**
	 * Sets the current intensity measure type to the given <code>newType</code>.
	 * This property is both bound and may be constrained, interested parties
	 * should listen to- and check for- changes to the <code>IMT_PROPERTY</code>
	 * of this bean.
	 * 
	 * @param newType The new IMT description string to use.
	 */
	public synchronized void setIMT(String newType) {
		// Store away for later.
		String oldType = imt;
		
		try {
			// Give listeners the change to veto.
			vetoableChanger.fireVetoableChange(IMT_PROPERTY, oldType, newType);
			
			// No one vetoed, so make the change.
			imt = newType;
			
			// Notify listeners of the change.
			propertyChanger.firePropertyChange(IMT_PROPERTY, oldType, newType);
		} catch (PropertyVetoException pvx) {
			// Somebody objected, so notify and revert back.
			getBeanEditor().infoPrompt(pvx.getMessage());
			setIMT(oldType);
		}
	}
	
	/**
	 * Updates the current editor used to manipulate this bean. Note that while
	 * the bean may only be aware of a single editor at one time, multiple
	 * editors may be used to manipulate the bean, thus different editors should
	 * listen to this bean's properties to be sure the current value is always
	 * displayed. Interested objects can listen to this bean's
	 * <code>EDITOR_PROPERTY</code> property to be notified of changes to this
	 * bean's editor. This property is bound but not constrained.
	 * 
	 * @param newEditor The new editor to use.
	 */
	public synchronized void setEditor(IMTBeanEditor newEditor) {
		// Store away for later.
		IMTBeanEditor oldEditor = editor;
		
		// This property is not constrained, so no need to offer a veto. Just make
		// the change and notify.
		editor = newEditor;
		
		// Notify listeners of the change.
		propertyChanger.firePropertyChange(EDITOR_PROPERTY, oldEditor, newEditor);
	}
	
	//----------------------------- Public Getters ----------------------------//
	
	/**
	 * See the general contract defined in <code>AbstractBean</code>.
	 */
	public synchronized BeanEditorAPI getBeanEditor() {
		return editor;
	}
	
	/**
	 * @return The current intensity measure type.
	 */
	public synchronized String getIMT() {
		return imt;
	}
	
	//---------------------------- Public Utilities ---------------------------//

	/**
	 * Implements the <code>VetoableChangeListener</code> interface.
	 *
	 * @param evt The event that triggered this call.
	 * @throws PropertyVetoException If the evt indicates a property change that
	 * this bean does not approve of.
	 */
	public void vetoableChange(PropertyChangeEvent evt)
			throws PropertyVetoException {
		
	}
	
	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------

}
