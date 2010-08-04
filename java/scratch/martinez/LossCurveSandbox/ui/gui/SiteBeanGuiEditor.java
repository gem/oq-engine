package scratch.martinez.LossCurveSandbox.ui.gui;

import java.beans.PropertyChangeEvent;
import java.util.TreeMap;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenuItem;
import javax.swing.JPanel;

import scratch.martinez.LossCurveSandbox.beans.BeanAPI;
import scratch.martinez.LossCurveSandbox.beans.LocationBean;
import scratch.martinez.LossCurveSandbox.beans.SiteBean;
import scratch.martinez.LossCurveSandbox.ui.SiteBeanEditor;

/**
 * This editor allows an application to manipulate a <code>SiteBean</code> in a
 * graphical manner. This editor is a composite editor that utilizes a 
 * <code>LocationBeanGuiEditor</code> in addition to primitive Swing components.
 * 
 * @author   
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 *
 */
public class SiteBeanGuiEditor extends AbstractGuiEditor implements
		SiteBeanEditor {

	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------

	//---------------------------- Constant Members ---------------------------//

	// Implementation side-effect for serialization.
	private static final long serialVersionUID = 0x2571DB1;
	
	//----------------------------  Static Members  ---------------------------//

	//---------------------------- Instance Members ---------------------------//

	/**
	 * The underlying location bean editor used to manipulate the location of
	 * this bean.
	 */
	private LocationBeanGuiEditor locEditor = null;
	
	/**
	 * The label that displays the current site class.
	 */
	private JLabel siteClassDisplay = null;
	
	/**
	 * The underlying site bean associated with this editor.
	 */
	private SiteBean bean = null;
	
	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------

	/**
	 * Default no-arg constructor. Uses the shared instance of the underlying
	 * <code>SiteBean</code> as its bean. This can later be changed.
	 */
	public SiteBeanGuiEditor() {
		this(SiteBean.getSharedInstance());
	}
	
	/**
	 * Creates a new <code>SiteBeanGuiEditor</code> using the given
	 * <code>siteBean</code> as the bean to modify.
	 * 
	 * @param siteBean The bean to manipulate with this editor.
	 */
	public SiteBeanGuiEditor(SiteBean siteBean) {
		bean = siteBean;
		initGuiEditors();
		bean.setBeanEditor(this);
		updateValuesFromBean();
		startListening();
	}
	
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//------------------------- Public Setter Methods  ------------------------//

	/**
	 * See the general contract specified in <code>BeanEditorAPI</code>. This is
	 * neither bound nor constrained beyond the class casting ability required.
	 */
	public void setBean(BeanAPI newBean) throws ClassCastException {
		
		// Make the change.
		bean = (SiteBean) newBean;
		
		// Update the nested editor as well.
		locEditor.setBean(bean.getLocationBean());
		

	}

	//------------------------- Public Getter Methods  ------------------------//

	/**
	 * See the general contract specified in <code>AbstractGuiEditor</code>.
	 */
	public TreeMap<String, JMenuItem> getMenuOptions() {
		// TODO Auto-generated method stub
		return null;
	}

	/**
	 * See the general contract specified in <code>AbstractGuiEditor</code>.
	 */
	public JPanel getPanelEditor() {
		// TODO Auto-generated method stub
		return null;
	}

	/**
	 * See the general contract specified in <code>AbstractGuiEditor</code>.
	 */
	public JFrame getWindowEditor() {
		// TODO Auto-generated method stub
		return null;
	}

	//------------------------- Public Utility Methods ------------------------//

	/**
	 * Implements the property change listener.
	 */
	public void propertyChange(PropertyChangeEvent evt) {
		String propName = evt.getPropertyName();
		
		// Update the site class (conditionally) if the location changed.
		if(LocationBean.LOCATION_PROPERTY.equals(propName)) {
			updateValuesFromBean();
		}
		
	}
	
	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------

	/**
	 * Initializes the panel and window editors for this bean editor. Since this
	 * is a composite bean, much of the GUI work is handled by component editors.
	 */
	protected void initGuiEditors() {
		// TODO
	}
	
	/**
	 * Updates displayed location and site conditions parameters.
	 */
	protected void updateValuesFromBean() {
		
		// The location editor will have already caught the location change, so
		// just update the displayed site conditions. Since the location changed
		// this involves looking up the new values.
		siteClassDisplay.setText(bean.getSiteClassDescription());
		siteClassDisplay.setToolTipText(bean.getSiteClassName());

	}
	
	/**
	 * Starts listening to changes from the current <code>bean</code> object.
	 * This is called at time of instantiation or after the user changes the bean
	 * to modify with this editor.
	 */
	protected void startListening() {
		// Make sure this stays in sync with the "start listening" method.
		bean.addPropertyChangeListener(LocationBean.LOCATION_PROPERTY, this);
	}
	
	/**
	 * Stops listening to changes from the current <code>bean</code> object. This
	 * is called before the user changes the bean to modify with this editor.
	 */
	protected void stopListening() {
		// Make sure this stays in sync with the "start listening" method.
		bean.removePropertyChangeListener(LocationBean.LOCATION_PROPERTY, this);
	}

}
