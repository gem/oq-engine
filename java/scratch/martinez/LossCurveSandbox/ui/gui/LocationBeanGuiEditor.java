package scratch.martinez.LossCurveSandbox.ui.gui;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.beans.PropertyChangeEvent;
import java.util.TreeMap;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenuItem;
import javax.swing.JPanel;
import javax.swing.JTextField;

import org.opensha.commons.geo.Location;

import scratch.martinez.LossCurveSandbox.beans.BeanAPI;
import scratch.martinez.LossCurveSandbox.beans.LocationBean;
import scratch.martinez.LossCurveSandbox.ui.LocationBeanEditor;

/**
 * This class can be used by an application to manipulate a 
 * <code>LocationBean</code> in a graphical manner. It displays input fields for
 * the latitude and longitude. Upon successful entering of a new location the
 * editor modifies the stored location in the underlying bean. If modifications
 * fail (due to veto or other reasons), then the reverted values are reflected
 * in the editor input fields.
 * 
 * @author   
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 *
 */
public class LocationBeanGuiEditor extends AbstractGuiEditor
		implements LocationBeanEditor {

	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------

	//---------------------------- Constant Members ---------------------------//

	// Implementation side-effect for serialization
	private static final long serialVersionUID = 0x7E5F7B6;
	
	/**
	 * Title displayed on the editor window for top-level windowed editors.
	 */
	private static final String WINDOW_TITLE = "Set Current Location";
	
	/**
	 * Label text for the latitude editor.
	 */
	private static final String LATITUDE_LABEL_TEXT = "Latitude";
	
	/**
	 * Label text for the longitude editor.
	 */
	private static final String LONGITUDE_LABEL_TEXT = "Longitude";

	/**
	 * Text displayed when mousing over the latitude editor/label.
	 */
	private static final String LATITUDE_TOOLTIP = "Latitude decimal degrees.";
	
	/**
	 * Text displayed when mousing over the longitude editor/label.
	 */
	private static final String LONGITUDE_TOOLTIP = "Longitude decimal degrees."+
			" Use negative values for western longitudes.";

	/**
	 * Message displayed when users enters a non-numeric value into one of the
	 * numeric editor fields (latitude/longitude/depth).
	 */
	private static final String BAD_NUMBER_FORMAT = "Unable to parse an input " +
			"value. All location input values must be numeric.";
	
	//----------------------------  Static Members  ---------------------------//

	//---------------------------- Instance Members ---------------------------//

	/**
	 * The location bean this editor manipulates.
	 */
	private LocationBean bean = null;
	
	/**
	 * GUI component to modify the latitude.
	 */
	private JTextField latEditor = null;
	
	/**
	 * GUI component to modify the longitude.
	 */
	private JTextField lonEditor = null;

	/**
	 * The panel that is suitable for embedding in a containing application
	 * window. This panel contains all the required components to manipulate the
	 * underlying bean.
	 */
	private JPanel editorPanel = null;
	
	/**
	 * The top-level window that can be displayed independently on the screen.
	 * The window will contain the editor panel and a button to gracefully close
	 * the window.
	 */
	private JFrame editorWindow = null;
	
	/**
	 * Flag marking when the displayed latitude has been changed from the
	 * underlying bean's location's latitude. This is only set when the displayed
	 * latitude is changed, not if another editor modifies the bean's location.
	 */
	private boolean latitudeChanged = false;
	
	/**
	 * Flag marking when the displayed longitude has been changed from the
	 * underlying bean's location's longitude. This is only set when the
	 * displayed longitude is changed, not if another editor modifies the bean's
	 * location.
	 */
	private boolean longitudeChanged = false;
	
	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------

	/**
	 * Default, no-arg constructor. Uses the shared instance of the location
	 * bean as its underlying bean instance.
	 */
	public LocationBeanGuiEditor() {
		this(LocationBean.getSharedInstance());
	}
	
	/**
	 * Creates a new instance of an editor for a location bean. Uses the given
	 * <code>defaultBean</code> as the underlying bean instance to modify.
	 * 
	 * @param defaultBean The bean to modify using this editor.
	 */
	public LocationBeanGuiEditor(LocationBean defaultBean) {
		bean = defaultBean;
		initGuiEditors();
		bean.setEditor(this);
		updateValuesFromBean();
		startListening();
	}
	
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//------------------------- Public Setter Methods  ------------------------//

	/**
	 * See the general contract defined in <code>BeanAPI</code>.
	 */
	public void setBean(BeanAPI newBean) throws ClassCastException {
		// Stop listening to changes from the old bean.
		stopListening();
		
		// Make the change.
		bean = (LocationBean) newBean;
		
		// Start listening to changes on the new bean.
		startListening();
	}
	
	//------------------------- Public Getter Methods  ------------------------//

	/**
	 * @return The value of the latitude editor represented as a double. If the
	 * value is empty then <code>Double.NaN</code> is returned, if the value
	 * cannot otherwise be parsed as a double, then a
	 * <code>NumberFormatException</code>.
	 * @throws NumberFormatException If the value is non-empty and cannot be
	 * parsed as a double.
	 */
	public double getLatEditorValue() throws NumberFormatException {
		return getDoubleValue(latEditor);
	}
	
	/**
	 * @return The value of the longitude editor represented as a double. If the
	 * value is empty then <code>Double.NaN</code> is returned, if the value
	 * cannot otherwise be parsed as a double, then a
	 * <code>NumberFormatException</code>.
	 * @throws NumberFormatException If the value is non-empty and cannot be
	 * parsed as a double.
	 */
	public double getLonEditorValue() throws NumberFormatException {
		return getDoubleValue(lonEditor);
	}
	
	/**
	 * @return  The bean we are currently working with.
	 */
	public LocationBean getBean() { return bean; }
	
	/**
	 * See the general contract defined in <code>AbstractGuiEditor</code>.
	 */
	public TreeMap<String, JMenuItem> getMenuOptions() {
		// There are no associated menu options on this editor. One should keep
		// in mind this basic location editor has no constraints, however if
		// a containing class adds constraints to the location, then it should
		// also add a help menu option to explain the constraints.
		return new TreeMap<String, JMenuItem>();
	}

	/**
	 * See the general contract defined in <code>AbstractGuiEditor</code>.
	 */
	public JPanel getPanelEditor() {
		return editorPanel;
	}

	/**
	 * See the general contract defined in <code>AbstractGuiEditor</code>.
	 */
	public JFrame getWindowEditor() {
		return editorWindow;
	}
	
	//------------------------- Public Utility Methods ------------------------//

	/**
	 * See the general contract defined in <code>PropertyChangeListener</code>.
	 */
	public void propertyChange(PropertyChangeEvent evt) {
		String propName = evt.getPropertyName();
		
		if (LocationBean.LOCATION_PROPERTY.equals(propName)) {
			// Entire location changed.
			Location newLoc = (Location) evt.getNewValue();
			latEditor.setText(String.valueOf(newLoc.getLatitude()));
			lonEditor.setText(String.valueOf(newLoc.getLongitude()));
		}
	}
	
	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------
	
	/**
	 * Instantiates and initializes all the GUI components required to edit the
	 * underlying bean.
	 */
	protected void initGuiEditors() {
		
		// Initialize the latitude editor.
		latEditor = new JTextField(8);
		latEditor.setToolTipText(LATITUDE_TOOLTIP);
		latEditor.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent evt) {
				System.err.println("Latitude event...");
				latitudeChanged =  true;
				if(latitudeChanged && longitudeChanged) {
					try {
						setBeanLocation();
					} catch (NumberFormatException nfx) {
						updateValuesFromBean();
					} finally {
						latitudeChanged  = false;
						longitudeChanged = false;
					} // END: try/catch
				} // END: if
				
			} // END: actionPerformed
		});
		
		// Initialize the longitude editor.
		lonEditor = new JTextField(8);
		lonEditor.setToolTipText(LONGITUDE_TOOLTIP);
		lonEditor.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent event) {
				System.err.println("Longitude event...");
				longitudeChanged = true;
				if(latitudeChanged && longitudeChanged) {
					try {
						setBeanLocation();
					} catch(NumberFormatException nfx) {
						updateValuesFromBean();
					} finally {
						latitudeChanged  = false;
						longitudeChanged = false;
					}
				}
			}
		});
		
		// Create some labels that make sense.
		JLabel latLabel   = new JLabel(LATITUDE_LABEL_TEXT);
		JLabel lonLabel   = new JLabel(LONGITUDE_LABEL_TEXT);
		
		latLabel.setToolTipText(LATITUDE_TOOLTIP);
		lonLabel.setToolTipText(LONGITUDE_TOOLTIP);
		
		// Instantiate the editor instances.
		editorPanel  = new JPanel(new GridBagLayout());
		editorWindow = new JFrame(WINDOW_TITLE);
		
		// Add the components to the panel.
		editorPanel.add(latLabel, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		editorPanel.add(lonLabel, new GridBagConstraints(1, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		
		editorPanel.add(latEditor, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		editorPanel.add(lonEditor, new GridBagConstraints(1, 1, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(0, 0, 0, 0), 0, 0));
		
		// Add the components to the window.
		JButton okButton = new JButton("Apply Changes");
		okButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent evt) {
				try {
					setBeanLocation();
					editorWindow.setVisible(false);
				} catch (NumberFormatException nfx) {
					// Latitude and/or longitude could not be parsed as a number.
					infoPrompt(BAD_NUMBER_FORMAT + "\nReverting to old value.");
					// Reset value from bean's current values
					updateValuesFromBean();
				}
			}
		});
		okButton.setToolTipText("Click to apply changes and close the window.");
		
		JButton cancelButton = new JButton("Cancel");
		cancelButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent evt) {
				updateValuesFromBean();
				editorWindow.setVisible(false);
			}
		});
		cancelButton.setToolTipText("Click to close window and revert to " +
				"original values.");
		
		editorWindow.getContentPane().setLayout(new GridBagLayout());
		editorWindow.getContentPane().add(editorPanel, new GridBagConstraints(
				0, 0, 4, 4, 1.0, 1.0, GridBagConstraints.CENTER,
				GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));
		editorWindow.getContentPane().add(cancelButton, new GridBagConstraints(
				3, 4, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
				GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
		editorWindow.getContentPane().add(okButton, new GridBagConstraints(4, 4,
				1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
				GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
		editorWindow.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
		editorWindow.getRootPane().setDefaultButton(okButton);
		
	}
	
	/**
	 * Reverts the displayed latitude and longitude values to those currently
	 * being used by the underlying bean. If the bean does not currently have a
	 * valid location then the displayed values are simply cleared. After
	 * resetting the values they are considered to be &ldquo;unchanged&rduo; from
	 * the beans values.
	 */
	protected synchronized void updateValuesFromBean() {
		
		if(bean.locationReady()) {
			latEditor.setText(String.valueOf(bean.getLocation().getLatitude()));
			lonEditor.setText(String.valueOf(bean.getLocation().getLongitude()));
		} else {
			latEditor.setText("");
			lonEditor.setText("");
		}
		latitudeChanged  = false;
		longitudeChanged = false;
	}
	
	/**
	 * Starts listening to changes from the current <code>bean</code> object.
	 * This is called at time of instantiation or after the user changes the bean
	 * to modify with this editor.
	 */
	protected synchronized void startListening() {
		bean.addPropertyChangeListener(LocationBean.LOCATION_PROPERTY, this);
	}
	
	/**
	 * Stops listening to changes from the current <code>bean</code> object. This
	 * is called before the user changes the bean to modify with this editor.
	 */
	protected synchronized void stopListening() {
		bean.removePropertyChangeListener(LocationBean.LOCATION_PROPERTY, this);
	}
	
	/**
	 * Sets the underlying bean's location using the current latitude and
	 * longitude values stored in the corresponding editor text fields.
	 * 
	 * @throws NumberFormatException If either the latitude or longitude value
	 * was non-empty but could not be parsed as a <code>double</code>.
	 */
	private void setBeanLocation() throws NumberFormatException {
		bean.setLocation(getLatEditorValue(), getLonEditorValue());
		latitudeChanged = false;
		longitudeChanged = false;
	}
	
	/**
	 * Reads the value of the given <code>field</code> and attempts parse it as a
	 * <code>double</code> value.
	 * 
	 * @param field The input field to read from.
	 * @return The <code>double</code> value of the <code>field</code>, or
	 * <code>Double.NaN</code> if the <code>field</code> is empty.
	 * @throws NumberFormatException If the <code>field</code> is non-empty and
	 * cannot be parsed  as a <code>double</code>.
	 */
	private double getDoubleValue(JTextField field)
			throws NumberFormatException {
		String rawValue = field.getText();
		if("".equals(rawValue)) {
			return Double.NaN;
		} else {
			return Double.parseDouble(rawValue);
		}
	}
}
