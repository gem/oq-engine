package scratch.martinez.LossCurveSandbox.ui.gui;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.beans.PropertyChangeEvent;
import java.util.TreeMap;
import java.util.Vector;

import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenuItem;
import javax.swing.JPanel;

import scratch.martinez.LossCurveSandbox.beans.BeanAPI;
import scratch.martinez.LossCurveSandbox.beans.NSHMPHazardBean;
import scratch.martinez.LossCurveSandbox.ui.HazardBeanEditor;

/**
 * This class is an GUI deployment editor for an <code>NSHMPHazardBean</code>.
 * This will allow users to modify the bean state to compute hazard curves.
 * 
 * @author  
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 */
public class NSHMPHazardBeanGuiEditor extends AbstractGuiEditor
		implements HazardBeanEditor, ActionListener {

	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------
	
	
	//---------------------------- Constant Members ---------------------------//
	
	// Implementation side-effect for serialization
	private static final long serialVersionUID = 0x7C87C09;
	
	/**
	 * Text labeling the data edition editor.
	 */
	private static final String EDITION_LABEL_TEXT = "Data Edition:";
	
	/**
	 * Text labeling the IMT editor.
	 */
	private static final String IMT_LABEL_TEXT = "Hazard Curve Type:";
	
	/**
	 * Text displayed when mousing over the edition editor/label.
	 */
	private static final String EDITION_TOOLTIP = "Select the data edition of " +
			"the hazard curve you want. Note that not all editions are " +
			"available for all locations.";
	
	/**
	 * Text displayed when mousing over the IMT editor/label.
	 */
	private static final String IMT_TOOLTIP = "Select an intensity measure " +
			"type (IMT) to use for the hazard curve.";
	
	//----------------------------  Static Members  ---------------------------//
	
	//---------------------------- Instance Members ---------------------------//
	
	/**
	 * The underlying bean that this editor will interact with.
	 */
	private NSHMPHazardBean bean = null;
	
	/**
	 * GUI component to edit the data edition.
	 */
	private JComboBox editionEditor = null;
	
	/**
	 * GUI component to edit the imt selection.
	 */
	private JComboBox imtEditor = null;
	
	/**
	 * GUI component to edit the location.
	 */
	LocationBeanGuiEditor locationEditor = null;
	
	/**
	 * Panel containing all the raw editor components. This panel is suitable to
	 * be embedded into a larger pane for complex components.
	 */
	private JPanel editorPanel = null;
	
	/**
	 * A top-level window that can be "popped up" by a parent application. This
	 * window displays the <code>editorPanel</code> with a button to accept the
	 * changes.
	 */
	private JFrame editorWindow = null;
	

	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------
	
	/**
	 * Default no-arg constructor.
	 */
	public NSHMPHazardBeanGuiEditor() {
		this(NSHMPHazardBean.getSharedInstance());
	}
	
	/**
	 * Creates an instance of an <code>NSHMPHazardBeanGuiEditor</code> using the
	 * given <code>defaultBean</code> as this editors <code>currentBean</code>.
	 * 
	 * @param defaultBean The bean to edit.
	 */
	public NSHMPHazardBeanGuiEditor(NSHMPHazardBean defaultBean) {
		bean = defaultBean;
		initGuiEditors();
		bean.setBeanEditor(this);
		updateValuesFromBean();
		startListening();
	}
	
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------
	
	//------------------------- Public Setter Methods -------------------------//

	/**
	 * See the general contract declared in <code>BeanEditorAPI</code>. 
	 */
	public void setBean(BeanAPI newBean) throws ClassCastException {
		bean = (NSHMPHazardBean) newBean;
	}
	
	//------------------------- Public Getter Methods -------------------------//

	/**
	 * See the general contract declared in <code>AbstractGuiEditor</code>. 
	 */
	public TreeMap<String, JMenuItem> getMenuOptions() {
		// TODO Auto-generated method stub
		return null;
	}
	
	/**
	 * See the general contract declared in <code>AbstractGuiEditor</code>. 
	 */
	public JPanel getPanelEditor() {
		return editorPanel;
	}
	
	
	/**
	 * See the general contract declared in <code>AbstractGuiEditor</code>. 
	 */
	public JFrame getWindowEditor() {
		return editorWindow;
	}
	
	//------------------------- Public Utility Methods ------------------------//
	
	/**
	 * See the general contract declared in <code>PropertyChangeListener</code>. 
	 */
	public void propertyChange(PropertyChangeEvent evt) {
		// TODO Auto-generated method stub

	}

	/**
	 * See the general contract declared in <code>ActionListener</code>.
	 */
	public void actionPerformed(ActionEvent evt) {
		// TODO
	}
	
	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------
	
	/**
	 * Instantiates and initializes default values for the GUI components that
	 * are used to modify the underlying bean's state. This editor's
	 * <code>currentBean</code> must be non-null before a call can be made to
	 * this method.
	 */
	protected void initGuiEditors() {
		// Initialize the edition editor.
		editionEditor = new JComboBox();
		editionEditor.setToolTipText(EDITION_TOOLTIP);
		updateEditionEditor();
		editionEditor.addActionListener(this);
		
		// Initialize the IMT editor.
		imtEditor = new JComboBox();
		imtEditor.setToolTipText(IMT_TOOLTIP);
		updateImtEditor();
		imtEditor.addActionListener(this);
		
		// Initialize the Location editor.
		locationEditor = new LocationBeanGuiEditor();
		
		// Initialize the labels for simple components.
		JLabel editionLabel = new JLabel(EDITION_LABEL_TEXT);
		editionLabel.setToolTipText(EDITION_TOOLTIP);
		editionLabel.setLabelFor(editionEditor);
		
		JLabel imtLabel = new JLabel(IMT_LABEL_TEXT);
		imtLabel.setToolTipText(IMT_TOOLTIP);
		imtLabel.setLabelFor(imtEditor);
		
		editorPanel = new JPanel(new GridBagLayout());
		
		// Add the edition stuff
		editorPanel.add(editionLabel, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		editorPanel.add(editionEditor, new GridBagConstraints(1, 0, 1, 1, 1.0,
				1.0, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));
		
		// Add the imt stuff
		editorPanel.add(imtLabel, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		editorPanel.add(imtEditor, new GridBagConstraints(1, 1, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(0, 0, 0, 0), 0, 0));
		
		//  Add the location panel.
		editorPanel.add(locationEditor.getPanelEditor(), new GridBagConstraints(
				0, 2, 2, 2, 1.0, 1.0, GridBagConstraints.CENTER,
				GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));
	}
	
	/**
	 * Updates what is available and selected in the <code>editionEditor</code>.
	 * This method is called at initial instantiation and then again whenever a
	 * change in location (in the underlying bean) results in a region change
	 * that does not have data for the current set of editions.
	 */
	private void updateEditionEditor() {
		// Ask the bean for available editions.
		Vector<String> availableEditions = bean.getAvailableDataEditions(
				bean.getGeographicRegion(bean.getLocation())
			);
		
		// Remove any old items.
		editionEditor.removeAllItems();
		
		// Add the new items.
		for(int i = 0; i < availableEditions.size(); ++i) {
			editionEditor.addItem(availableEditions.get(i));
		}
		
		// Set the currently selected item.
		editionEditor.setSelectedItem(bean.getDataEdition());
	}
	
	/**
	 * Updates what is available and selected in the <code>imtEditor</code>. This
	 * method is called at initial instantiation and then again whenever the
	 * data edition of the underlying bean changes.
	 */
	private void updateImtEditor() {
		
	}

	/**
	 * Updates the displayed values by reading the stored values in the 
	 * underlying bean. This is useful when we are required to revert to old
	 * values for some reason.
	 */
	protected void updateValuesFromBean() {
		// TODO Auto-generated method stub
		
	}
	

	/**
	 * Starts listening to changes from the current <code>bean</code> object.
	 * This is called at time of instantiation or after the user changes the bean
	 * to modify with this editor.
	 */
	protected synchronized void startListening() {
		
	}
	
	/**
	 * Stops listening to changes from the current <code>bean</code> object. This
	 * is called before the user changes the bean to modify with this editor.
	 */
	protected synchronized void stopListening() {
	}
}
