package scratch.martinez.LossCurveSandbox.ui.gui;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.InputEvent;
import java.awt.event.KeyEvent;
import java.beans.PropertyChangeEvent;
import java.beans.PropertyVetoException;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FilenameFilter;
import java.io.IOException;
import java.util.TreeMap;
import java.util.Vector;

import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JMenu;
import javax.swing.JMenuItem;
import javax.swing.JPanel;
import javax.swing.KeyStroke;

import scratch.martinez.LossCurveSandbox.beans.BeanAPI;
import scratch.martinez.LossCurveSandbox.beans.VulnerabilityBean;
import scratch.martinez.LossCurveSandbox.ui.VulnerabilityBeanEditor;
import scratch.martinez.LossCurveSandbox.util.MenuMaker;
import scratch.martinez.LossCurveSandbox.vulnerability.IllegalVulnerabilityFormatException;
import scratch.martinez.LossCurveSandbox.vulnerability.UnsupportedDistributionException;
import scratch.martinez.LossCurveSandbox.vulnerability.VulnerabilityModel;

/**
 * This editor allows a user to select a vulnerability model in a graphical
 * manner. This editor manipulates a <code>VulnerabilityBean</code>.
 * 
 * @author   
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 *
 */
public class VulnerabilityBeanGuiEditor extends AbstractGuiEditor
		implements VulnerabilityBeanEditor {
	
	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------

	// Used for serialization
	private static final long serialVersionUID = 0xF418D5D;
	
	// The title of the windowed version of this editor.
	private static final String EDITOR_TITLE = "Set Vulerability Model";
	// The text displayed when a requested file is not found.
	private static final String FILE_NOT_FOUND_PROMPT = "Could not find the " +
			"specified file.";
	// The text displayed when an I/O error occurs.
	private static final String IO_ERROR_PROMPT = "An I/O error occurred " +
			"while reading the specified file.";
	// The text displayed when an input file requests an unknown distribution.
	private static final String BAD_DISTRIBUTION_PROMPT = "The specified file " +
			"requested a probability distribution that is not currently supported";
	// The text displayed when the input file is poorly formatted.
	private static final String BAD_FORMAT_PROMPT = "The specified file does " +
			"not conform the the defined vulnerability input syntax.";
	// The display text of the default vulnerability model (none).
	private static final String NO_MODEL_SELECTED = "Select a vulnerability " +
			"model...";
	// The text displayed in the containing menu for this editor.
	private static final String EDITOR_MENU_TEXT = "Vulnerabilities";
	// The text displayed in the menu to load a vulnerability.
	private static final String LOAD_MODEL_MENU_TEXT = "Import Vulnerability...";
	// The text displayed when mousing over the panelEditor of this editor.
	private static final String PANEL_TOOLTIP = "Model Used to Estimate Loss";
	
	// The underlying bean that this editor will manipulate.
	private VulnerabilityBean bean = null;
	
	// The windowed component for this editor.
	private JFrame windowEditor = null;
	// The embed-able panel for this editor.
	private JPanel panelEditor = null;
	// The combo box used by this editor to select a vulnerability.
	private JComboBox cmbSelectModel = null;
	
	// A bridge-table mapping between vulnerability models and their names.
	private TreeMap<String, VulnerabilityModel> modelNameBridge = null;
	
	
	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------

	/**
	 * Default no-arg constructor. Since the vulnerability bean follows the
	 * singleton structure, it is safe to get the singleton instance and assume
	 * we can use that as our bean, so we do.
	 */
	public VulnerabilityBeanGuiEditor() {
		this(VulnerabilityBean.getSharedInstance());
	}
	
	/**
	 * Uses the given <code>VulnerabilityBean</code> as this editor's bean. Since
	 * this bean <em>must</em> be the singleton instance (by definition of
	 * singleton), there is no real advantage to use this constructor over the
	 * no-arg constructor, however for style reasons and explicitness of source
	 * code this constructor is provided.
	 * 
	 * @param initialBean The bean to edit with this editor.
	 */
	public VulnerabilityBeanGuiEditor(VulnerabilityBean initialBean) {
		this.bean = initialBean;
		initGuiEditors();
		bean.setEditor(this);
		updateValuesFromBean();
		startListening();
	}
	
	

	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//------------------------- Public Getter Methods -------------------------//
	
	/**
	 * See the general contract declared in the
	 * <code>VulnerabilityBeanEditor</code> interface.
	 */
	public VulnerabilityBean getBean() {
		return bean;
	}

	/**
	 * Gets the panel editor for embedding in a larger panel/window/frame.
	 * @return The panel editor.
	 */
	public JPanel getPanelEditor() {
		return panelEditor;
	}
	
	/**
	 * Gets the window editor for display as a pop-up window.
	 * @return The windowed editor.
	 */
	public JFrame getWindowEditor() {
		return windowEditor;
	}
	
	//------------------------- Public Setter Methods -------------------------//
	
	/**
	 * See the general contract declared in the <code>BeanEditorAPI</code>
	 * interface. Since this editor works with a singleton bean only, this method
	 * exists only as an implementation side-effect.
	 */
	public void setBean(BeanAPI bean) throws IllegalArgumentException {
		if( ! (bean instanceof VulnerabilityBean)) {
			IllegalArgumentException iax = new IllegalArgumentException("A " +
					"vulnerability editor can only accept a vulnerability bean. I " +
					"was given a " + bean.getClass().toString() + " bean that I " +
					"can't use.");
			iax.fillInStackTrace();
			throw iax;
		}
		
		// Set the bean
		this.bean = (VulnerabilityBean) bean;
		
	}
	
	/**
	 * Attempts to set the current model property for the underlying bean. If
	 * this change is vetoed by any interested objects, then no change is made,
	 * otherwise the change is made and objects interested in this change will
	 * be notified.
	 * 
	 * @param newModel The new model to use as the current model.
	 * @return The resulting current model for the underlying bean.
	 */
	public VulnerabilityModel setCurrentModel(VulnerabilityModel newModel) {
		
		// Store away for later.
		VulnerabilityModel oldModel = bean.getCurrentModel();
		
		try {
			// Let interested objects veto if they so choose.
			bean.fireVetoableChange(VulnerabilityBean.CURRENT_MODEL_PROPERTY,
					bean.getCurrentModel(), newModel);
			
			// Update the bean's internal state
			bean.setCurrentModel(newModel);
			
			// Let interested objects know about the change.
			bean.firePropertyChange(VulnerabilityBean.CURRENT_MODEL_PROPERTY,
					oldModel, newModel);
			
		} catch (PropertyVetoException pvx) {
			// Do not change, but we don't need to do anything else here...
		}
		
		return bean.getCurrentModel();
	}
	

	//------------------------ Public Utility Methods -------------------------//
	
	
	/**
	 * Pops up a file chooser dialog for the user to specify which file to
	 * load. Attempts to parse the input file and add the vulnerability to the
	 * list of known vulnerabilities. If something fails for some reason (i.e. an
	 * exception is thrown), the user is notified with another dialog and nothing
	 * is done. Upon successfully adding the new vulnerability to the list of
	 * known vulnerabilities, the new vulnerability as attempted to be listed
	 * as available. If any listeners veto the availability change, then the
	 * vulnerability is still known, but not listed as available.
	 */
	public void loadVulnerability() {
		
		
		String inputFileName = getFileFromUser(new FilenameFilter() {
			public boolean accept(File dir, String name) {
				return (name == null || 
						name.endsWith(".xml") ||
						name.endsWith(".XML")
					);
			}
		});
		
		// Try to create the model and set as available. Note that the model's
		// availability should not be assumed since a listener may veto it.
		if(inputFileName != null) {
			updateBeanModels(new File(inputFileName));
		}
			
	}
	
	/**
	 * Builds a mapping of menu items that should be added to the containing
	 * application's menu if it is going to display this bean.
	 * 
	 * @return A mapping of menu options.
	 */
	public TreeMap<String, JMenuItem> getMenuOptions() {
		
		// Create the object to return.
		TreeMap<String, JMenuItem> menuOptions = new TreeMap<String, JMenuItem>();
		
		// Add our menu to the menuOptions...
		menuOptions.put(MenuMaker.ADV_MENU, createEditorMenu());
		
		// Possibly create other menu items to put in other top-level menus...
		
		
		// Return our menu options
		return menuOptions;
	}
	
	/**
	 * Listen for important changes to the underlying bean's properties. Update
	 * the GUI components of this editor as required.
	 */
	public void propertyChange(PropertyChangeEvent evt) {
		String propertyName = evt.getPropertyName();
		if(propertyName.equals(VulnerabilityBean.CURRENT_MODEL_PROPERTY)) {
			VulnerabilityModel model = (VulnerabilityModel) evt.getNewValue();
			if(model == null) { 
				// No model currently, so go back to default...
				cmbSelectModel.setSelectedItem(NO_MODEL_SELECTED);
				
			} else if ( !model.getDisplayName().equals(
					(String) cmbSelectModel.getSelectedItem())) {
				
				// If the model is different than what we think it is, update it.
				cmbSelectModel.setSelectedItem(model.getDisplayName());
			}
		} else if (propertyName.equals(VulnerabilityBean.KNOWN_MODELS_PROPERTY)) {
			// This list of known/available properties has changed, so let's
			// update what we know about.
			updateValuesFromBean();
		}
	}
	
	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------
	
	/**
	 * Instantiates and initializes the GUI editor components used by this Gui
	 * editor.
	 */
	protected void initGuiEditors() {
		// Create the editor(s)
		panelEditor = new JPanel(new GridBagLayout());
		windowEditor = new JFrame(EDITOR_TITLE);
		
		// Initialize the combo box selector
		cmbSelectModel = new JComboBox();
		updateValuesFromBean();
		cmbSelectModel.setSelectedIndex(0);
		cmbSelectModel.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				try {
					setCurrentModel(modelNameBridge.get(
							cmbSelectModel.getSelectedItem())
						);
				} catch (NullPointerException npx) {
					// Do nothing, this was an intermediate call...
				}
			}
		});
		
		// Add components to the panel editor
		panelEditor.add(cmbSelectModel, new GridBagConstraints(0, 0, 1, 1, 1.0,
				1.0, GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL,
				new Insets(2, 2, 2, 2), 2, 2));
		
		// Finish up the panel component
		panelEditor.setToolTipText(PANEL_TOOLTIP);
		
		// Finish up the  window component
		windowEditor.getContentPane().add(panelEditor);
		windowEditor.pack();
		windowEditor.setLocation(
			(int) (AbstractGuiEditor.screenSize.width - windowEditor.getWidth()) 
				/ 2,
			(int) (AbstractGuiEditor.screenSize.height - windowEditor.getHeight()) 
				/ 2
		);
	}
	
	/**
	 * Reads the <code>inputFile</code> and loads the data into a vulnerability
	 * model in the underlying bean object. If parsing the file fails for some
	 * reason, then no model is loaded.
	 * 
	 * @param inputFile The file to parse for the new model.
	 * @throws FileNotFoundException If the <code>inputFile</code> does not
	 * exist or cannot be opened for reading.
	 * @throws IOException If an I/O error occurs while reading the 
	 * <code>inputFile</code>.
	 * @throws UnsupportedDistributionException If the <code>inputFile</code>
	 * requests a probability distribution that is not currently supported.
	 * @throws IllegalVulnerabilityFormatException If the <code>inputFile</code>
	 * does not conform to the vulnerability input file specification.
	 */
	private void updateBeanModels(File inputFile) {
		if(inputFile == null) { return; }
		
		try {
			bean.updateModels(inputFile, true, true);
		} catch (FileNotFoundException e) {
			infoPrompt(FILE_NOT_FOUND_PROMPT);
		} catch (IOException e) {
			infoPrompt(IO_ERROR_PROMPT);
		} catch (UnsupportedDistributionException e) {
			infoPrompt(BAD_DISTRIBUTION_PROMPT);
		} catch (IllegalVulnerabilityFormatException e) {
			infoPrompt(BAD_FORMAT_PROMPT);
		}
	}
	
	/**
	 * Creates the menu to add to the parent application. This menu allows for
	 * the user to select advanced options associated with this gui editor.
	 * 
	 * @return A menu that can be added to the parent application menu.
	 */
	private JMenu createEditorMenu() {
		// Add the containing menu
		JMenu containingMenu = new JMenu(EDITOR_MENU_TEXT);
		
		// Add a menu option to load a vulnerability model from a file.
		JMenuItem loadModel = new JMenuItem(LOAD_MODEL_MENU_TEXT);
		// CTRL-SHIFT-O (or CMD-SHIFT-O on MacOS)
		loadModel.setAccelerator( KeyStroke.getKeyStroke(KeyEvent.VK_O,
				Toolkit.getDefaultToolkit().getMenuShortcutKeyMask() | 
				InputEvent.SHIFT_MASK)
			);
		// Add the action listener
		loadModel.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent evt) {
				loadVulnerability();
			}
		});
		// Add this menu item to our container.
		containingMenu.add(loadModel);
		
		return containingMenu;
	}
	
	/**
	 * Updates the combo-box selector component to reflect the currently
	 * available models and to select the model that is currently selected in
	 * the underlying bean.
	 */
	protected synchronized void updateValuesFromBean() {
		Vector<VulnerabilityModel> models = bean.getAvailableModels();
		
		// Reset the mapping between the combo-box and the models.
		modelNameBridge = new TreeMap<String, VulnerabilityModel>();
		modelNameBridge.put(NO_MODEL_SELECTED, null);
		cmbSelectModel.removeAllItems();
		
		// Add the default selected item.
		cmbSelectModel.addItem(NO_MODEL_SELECTED);
		
		// Add all the items
		for(int i = 0; i < models.size(); ++i) {
			VulnerabilityModel model = models.get(i);
			String modelName = model.getDisplayName();
			modelNameBridge.put(modelName, model);
			cmbSelectModel.addItem(modelName);
		}
		
		VulnerabilityModel currentModel = bean.getCurrentModel();
		if(currentModel != null) {
			cmbSelectModel.setSelectedItem(currentModel.getDisplayName());
		} else {
			cmbSelectModel.setSelectedIndex(0);
		}
	}

	/**
	 * Starts listening to changes from the current <code>bean</code> object.
	 * This is called at time of instantiation or after the user changes the bean
	 * to modify with this editor.
	 */
	protected synchronized void startListening() {
		// Listen for property changes in the bean and act accordingly
		bean.addPropertyChangeListener(VulnerabilityBean.CURRENT_MODEL_PROPERTY,
				this);
		bean.addPropertyChangeListener(VulnerabilityBean.KNOWN_MODELS_PROPERTY,
				this);
	}
	
	/**
	 * Stops listening to changes from the current <code>bean</code> object. This
	 * is called before the user changes the bean to modify with this editor.
	 */
	protected synchronized void stopListening() {
		// Listen for property changes in the bean and act accordingly
		bean.removePropertyChangeListener(
				VulnerabilityBean.CURRENT_MODEL_PROPERTY, this);
		bean.removePropertyChangeListener(
				VulnerabilityBean.KNOWN_MODELS_PROPERTY, this);
	}
}
