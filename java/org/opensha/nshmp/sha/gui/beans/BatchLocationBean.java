package org.opensha.nshmp.sha.gui.beans;

import java.awt.Color;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.util.ArrayList;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JTabbedPane;
import javax.swing.JTextField;
import javax.swing.SwingConstants;
import javax.swing.filechooser.FileFilter;

import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedDoubleParameterEditor;
import org.opensha.commons.param.editor.StringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.nshmp.util.BatchFileReader;


public class BatchLocationBean implements GuiBeanAPI, ParameterChangeListener, ParameterChangeFailListener {
	
	/////////////////// EMBEDED VISUALIZATION COMPONENETS /////////////////////
	
	/* Parameter Names */
	public static final String PARAM_BAT = "Input Batch File (*.xls)";
	public static final String PARAM_OUT = "Output File (*.xls)";
	public static final String PARAM_LAT = "Latitude";
	public static final String PARAM_LON = "Longitude";
	public static final String PARAM_ZIP = "5 Digit Zip Code";
	public static final String OUTPUT = "USGS_Output.xls";

	/* Parameter Editors */
	private StringParameterEditor batEditor = null;
	private StringParameterEditor outEditor = null;
	private ConstrainedDoubleParameterEditor latEditor = null;
	private ConstrainedDoubleParameterEditor lonEditor = null;
	private StringParameterEditor zipEditor = null;
	
	/* Parameters */
	private StringParameter batParam = new StringParameter(PARAM_BAT, "");
	private StringParameter outParam = new StringParameter(PARAM_OUT, "");
	private DoubleParameter latParam = new DoubleParameter(PARAM_LAT, -90, 90, "Degrees");
	private DoubleParameter lonParam = new DoubleParameter(PARAM_LON, -180, 180, "Degrees");
	private StringParameter zipParam = new StringParameter(PARAM_ZIP, "");
	
	/* Values */
	private double minlat = -90.0;
	private double maxlat = 90.0;
	private double minlon = -180.0;
	private double maxlon = 180.0;

	// << END EMBEDED VISUALIZATION COMPONENTS >> //
	
	/* Visualization Components */
	private JTabbedPane panel = null;
	private String web = null;
	private JButton btnFileChooser = null;
	private JButton btnOutChooser = null;
	private JLabel latConstraintLabel = null;
	private JLabel lonConstraintLabel = null;
	private JLabel batchConstraintLatLabel = null;
	private JLabel batchConstraintLonLabel = null;
	
	/* Tab Names */
	private static final String GEO_TAB = "Lat/Lon";
	private static final String ZIP_TAB = "Zip Code";
	private static final String BAT_TAB = "Batch File";
	
	/* Tab Indexes */
	public static final int GEO_MODE = 0;
	public static final int ZIP_MODE = 1;
	public static final int BAT_MODE = 2;
	
	/* Flags to determine which type of bean we are using */
	private static final int EMBED_FLAG = 0;
	private static final int WEB_FLAG = 1;
	private int currentMode;
	
	////////////////////////////////////////////////////////////////////////////////
	//                              PUBLIC FUNCTIONS                              //
	////////////////////////////////////////////////////////////////////////////////
	
	/* CONSTRUCTORS */
	public BatchLocationBean() {
		// Empty but that's okay too
	}
	
	public String getOutputFile() {
		String fileName = "";
		try {
			fileName = (String) outParam.getValue();
		} catch (NullPointerException npe) {
			ExceptionBean.showSplashException("File reference was null!", "Null File", npe);
			fileName = "";
		}
		return fileName;
	}
	
	public boolean inputFileExists() {
		String filename = (String) batParam.getValue();
		if(filename == null) {return false;}
		return (new File(filename)).exists();
	}
	public ArrayList<Location> getBatchLocations() {
		String fileName = (String) batParam.getValue();
		if(!(new File(fileName)).exists()) {
			
		}
		BatchFileReader bfr = new BatchFileReader(fileName);
		ArrayList<Location> locations = null;
		if(!bfr.ready()) return null;
		ArrayList<Double> lats = bfr.getColumnVals((short) 0, 0);
		ArrayList<Double> lons = bfr.getColumnVals((short) 1, 0);
		if(lats.size() != lons.size()) {
			ExceptionBean.showSplashException("File contained a different number of latitude an longitudes." +
					" These must be the same!", "Bad File Layout", null);
			return null;
		} else {
			locations = new ArrayList<Location>();
			for(int i = 0; i < lats.size(); ++i)
				locations.add(new Location(lats.get(i), lons.get(i)));
		}
		return locations;
	}
	
	public ArrayList<String> getBatchSiteConditions() {
		String fileName = (String) batParam.getValue();
		BatchFileReader bfr = new BatchFileReader(fileName);
		ArrayList<String> siteConditions = bfr.getColumnStringVals((short) 2);
		// Allowed strings
		 ArrayList<String> siteClasses = new ArrayList<String>();
		 siteClasses.add("A"); siteClasses.add("B"); siteClasses.add("C");
		 siteClasses.add("D"); siteClasses.add("E");
		// Normalize the inputs
		 for(int i = 0; i < siteConditions.size(); ++i) {
			String val = siteConditions.get(i);
			if("".equalsIgnoreCase(val)) {
				val = "D";
				int rowNum = i+1;
				JOptionPane.showMessageDialog(null, "The site class for row "+ rowNum +
						" was not defined.  Defaulting to 'Site Class D' instead.", "Undefined Site Class",
						JOptionPane.ERROR_MESSAGE);
			}
			val = val.substring(val.length() -1, val.length()).toUpperCase();
			if(siteClasses.contains(val)) {
				val = "Site Class " + val;
			} else {
				val = "Site Class D";
				JOptionPane.showMessageDialog(null, "The given site class '"+siteConditions.get(i)+
						"' is not valid.  Using 'Site Class D' instead.", "Invalid Site Class",
						JOptionPane.ERROR_MESSAGE);
			}
			siteConditions.set(i, val);
		} //for
		 return siteConditions;
	}
	
	public Location getSelectedLocation() {
		double lat = (Double) latParam.getValue();
		double lon = (Double) lonParam.getValue();
		return new Location(lat, lon);
	}
	
	/**
	 * Returns the current zip code stored in the zip <code>StringParameter</code>.
	 * This may be null or empty (&quot;&quot;).  Caller should check return status.
	 * @return The current zip code
	 */
	public String getZipCode() {
		return (String) zipParam.getValue();
	}
	
	public int getLocationMode() {
		int answer = -1;
		if(currentMode == EMBED_FLAG) {
			if(panel != null)
				answer = panel.getSelectedIndex();
		} else if (currentMode == WEB_FLAG) {
			answer = -2;
		}
		return answer;
	}
	
	public void updateGuiParams(double minLat, double maxLat, 
								double minLon, double maxLon, 
								boolean zipCodeSupported) {
		// Set these up for external reference
		this.minlat = minLat; this.maxlat = maxLat;
		this.minlon = minLon; this.maxlon = maxLon;
		
		// Create the new parameters
		latParam = new DoubleParameter(PARAM_LAT, this.minlat, this.maxlat, "Degrees");
		lonParam = new DoubleParameter(PARAM_LON, this.minlon, this.maxlon, "Degrees");
		
		// Add some change listeners
		latParam.addParameterChangeListener(this);
		latParam.addParameterChangeFailListener(this);
		lonParam.addParameterChangeListener(this);
		lonParam.addParameterChangeFailListener(this);
		
		// Set the parameters in the editors
		if(latEditor != null)
			latEditor.setParameter(latParam);
		if(lonEditor != null)
			lonEditor.setParameter(lonParam);
		
		// Change the constraint labels
		if(latConstraintLabel != null)
			latConstraintLabel.setText("(" + this.minlat + ", " + this.maxlat + ")");
		if(lonConstraintLabel != null)
			lonConstraintLabel.setText("(" + this.minlon + ", " + this.maxlon + ")");
		if(batchConstraintLatLabel != null)
			batchConstraintLatLabel.setText("Lat: [" + this.minlat + ", " + this.maxlat + "]");
		if(batchConstraintLonLabel != null)
			batchConstraintLonLabel.setText("Lon: ["+ this.minlon + ", " + this.maxlon + "]");
		
		// Set the enabled tabs
		if(panel != null) {
			panel.setEnabledAt(GEO_MODE, true);
			panel.setEnabledAt(ZIP_MODE, zipCodeSupported);
			panel.setEnabledAt(BAT_MODE, true);
		}
	}
	
	public ParameterList getLocationParameters() {
		ParameterList list = new ParameterList();
		list.addParameter(latParam);
		list.addParameter(lonParam);
		list.addParameter(zipParam);
		list.addParameter(batParam);
		return list;
	}
	
	public void createNoLocationGUI() {
		if(panel != null) {
			// All modes are unavailable
			panel.setEnabledAt(GEO_MODE, false);
			panel.setEnabledAt(ZIP_MODE, false);
			panel.setEnabledAt(BAT_MODE, false);
			panel.setSelectedIndex(BAT_MODE);
			JOptionPane.showMessageDialog(null, "Spectral Values are constant across the selected region.", 
					"Batch Mode Required", JOptionPane.INFORMATION_MESSAGE);
		}
	}
	
	/**
	 * Always returns true.  Exists for legacy reasons only.
	 * 
	 * @return Whether or not the bean has a valid location
	 */
	public boolean hasLocation() {
		if(panel != null) {
			int mode = panel.getSelectedIndex();
			if(mode == GEO_MODE) {
				Object latObj = latParam.getValue();
				Object lonObj = lonParam.getValue();
				double latVal = (latObj==null)?99.0:((Double) latObj);
				double lonVal = (lonObj==null)?380.0:((Double) lonObj);
				try {
					return (latParam.getMin() <= latVal && latVal <= latParam.getMax() &&
							lonParam.getMin() <= lonVal && lonVal <= lonParam.getMax());
				} catch (Exception ex) {
					return false;
				}
			} else if (mode == ZIP_MODE) {
				String zipVal = (String) zipParam.getValue();
				return zipVal.length() == 5;
			} else if (mode == BAT_MODE) {
				String input = (String) batParam.getValue();
				String output = (String) outParam.getValue();
				return ( input.length() > 0 && (new File(input)).exists() &&
						 output.length() > 0 );
			} else if ( !panel.isEnabledAt(GEO_MODE) && !panel.isEnabledAt(ZIP_MODE) &&
					!panel.isEnabledAt(BAT_MODE)) {
				return true;
			}
		}
		return false;
	}
	
	/* MINIMUM FUNCTIONS TO IMPLEMENT GuiBeanAPI */
	/**
	 * See the general contract in <code>GuiBeanAPI</code>
	 * @see GuiBeanAPI
	 */
	public Object getVisualization(int type) throws IllegalArgumentException {
		if(type == GuiBeanAPI.EMBED) {
			return getEmbedVisualization();
		} else if (type == GuiBeanAPI.WEB) {
			return getWebVisualization();
		}
		throw new IllegalArgumentException("The given type is not currently supported");
	}
	/**
	 * See the general contract in <code>GuiBeanAPI</code>
	 * @see GuiBeanAPI
	 */
	public String getVisualizationClassName(int type) {
		if(type == GuiBeanAPI.EMBED)
			return "javax.swing.JTabbedPane";
		else if (type == GuiBeanAPI.WEB)
			return "java.lang.String";
		else
			return null;
	}
	/**
	 * See the general contract in <code>GuiBeanAPI</code>
	 * @see GuiBeanAPI
	 */
	public boolean isVisualizationSupported(int type) {
		return (type == GuiBeanAPI.EMBED || type == GuiBeanAPI.WEB);
	}

	/* MINIMUM FUNCTIONS TO IMPLEMENT ParameterChangeListener AND ParameterChangeFailListener */
	/**
	 * See the general contract in <code>ParameterChangeListener</code>.
	 * @see ParameterChangeListener
	 */
	public void parameterChange(ParameterChangeEvent event) {
		String paramName = event.getParameterName();
		if(paramName.equals(PARAM_ZIP)) {
			String zipCode = (String) event.getNewValue();
			if(zipCode.length() != 5 && zipCode.length() != 0) {
				ExceptionBean.showSplashException("Please enter a valid 5 digit Zip Code", 
						"Invalid Zip Code", null);
				zipParam.setValue("");
			}
		}
	}

	public void parameterChangeFailed(ParameterChangeFailEvent event) {
		String paramName = event.getParameterName();
		if(paramName.equals(PARAM_LAT))
			JOptionPane.showMessageDialog(panel, "The given latitude is out of range!",
					"Out of Range", JOptionPane.ERROR_MESSAGE);
		if(paramName.equals(PARAM_LON))
			JOptionPane.showMessageDialog(panel, "The given longitude is out of range!",
					"Out of Range", JOptionPane.ERROR_MESSAGE);
		if(paramName.equals(PARAM_ZIP))
			JOptionPane.showMessageDialog(panel, "The given zip code is out of range!",
					"Out of Range", JOptionPane.ERROR_MESSAGE);
		if(paramName.equals(PARAM_BAT))
			JOptionPane.showMessageDialog(panel, "The given file is invalid!",
					"Bad File", JOptionPane.ERROR_MESSAGE);
		if(paramName.equals(PARAM_OUT))
			JOptionPane.showMessageDialog(panel, "The given direcotory is invalid!",
					"Bad Directory", JOptionPane.ERROR_MESSAGE);
	}
	
	////////////////////////////////////////////////////////////////////////////////
	//                             PRIVATE FUNCTIONS                              //
	////////////////////////////////////////////////////////////////////////////////
	
	private JTabbedPane getEmbedVisualization() {
		if(panel == null) {
			// Create the parameters
			batParam = new StringParameter(PARAM_BAT, "");
			outParam = new StringParameter(PARAM_OUT, "");
			zipParam = new StringParameter(PARAM_ZIP, "");
			
			// Create the editors
			try {
				batEditor = new StringParameterEditor(batParam);
				outEditor = new StringParameterEditor(outParam);
				latEditor = new ConstrainedDoubleParameterEditor(latParam);
				lonEditor = new ConstrainedDoubleParameterEditor(lonParam);
				zipEditor = new StringParameterEditor(zipParam);
			} catch (Exception ex) {
				ex.printStackTrace();
			}
			
			outEditor.setToolTipText("A file called \""+OUTPUT+"\" will be generated and placed here.");
			
			// Add some listeners
			batParam.addParameterChangeListener(this);
			batParam.addParameterChangeFailListener(this);
			outParam.addParameterChangeListener(this);
			outParam.addParameterChangeFailListener(this);
			zipParam.addParameterChangeListener(this);
			zipParam.addParameterChangeFailListener(this);
			
			/* The latParam and lonParam get their listeners in the
			 * updateGuiParams() function */
			
			btnFileChooser = new JButton(new ImageIcon(
					FileUtils.loadImage("icons/openFile.png")));
			btnFileChooser.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent arg0) {
					btnFileChooser_actionPerformed();
				}
			});
			
			btnOutChooser = new JButton(new ImageIcon(
					FileUtils.loadImage("icons/openFile.png")));
			btnOutChooser.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent arg0) {
					btnOutChooser_actionPerformed();
				}
			});
			
			// The panels for the three types of input
			JPanel geoPanel = new JPanel(new GridBagLayout());
			JPanel zipPanel = new JPanel(new GridBagLayout());
			JPanel batPanel = new JPanel(new GridBagLayout());
			
			// The lat/lon constraints
			latConstraintLabel = new JLabel("(" + minlat + ", " + maxlat + ")", SwingConstants.CENTER);
			lonConstraintLabel = new JLabel("(" + minlon + ", " + maxlon + ")", SwingConstants.CENTER);
			batchConstraintLatLabel = new JLabel("Lat: [" + this.minlat + ", " + this.maxlat + "]", SwingConstants.CENTER);
			batchConstraintLonLabel = new JLabel("Lon: ["+ this.minlon + ", " + this.maxlon + "]", SwingConstants.CENTER);
			
			latConstraintLabel.setForeground(new Color(80, 80, 133));
			lonConstraintLabel.setForeground(new Color(80, 80, 133));
			batchConstraintLatLabel.setForeground(new Color(80, 80, 133));
			batchConstraintLonLabel.setForeground(new Color(80, 80, 133));
			
			Font constraintFont = new Font("Lucida Grande", Font.PLAIN, 11);
			batchConstraintLatLabel.setFont(constraintFont);
			batchConstraintLonLabel.setFont(constraintFont);
			
			// Set up the geoPanel
			geoPanel.add(latEditor, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 2, 0));
			geoPanel.add(lonEditor, new GridBagConstraints(1, 0, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 2, 0));
			geoPanel.add(latConstraintLabel, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 2, 0));
			geoPanel.add(lonConstraintLabel, new GridBagConstraints(1, 1, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 2, 0));
			
			// Set up the zipPanel
			zipPanel.add(zipEditor, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 2, 0));
			
			// Set up the batPanel
			batPanel.add(batEditor, new GridBagConstraints(0, 0, 2, 1, 5.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 2, 0));
			batPanel.add(btnFileChooser, new GridBagConstraints(2, 0, 1, 1, 0.5, 1.0, GridBagConstraints.EAST,
					GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
			batPanel.add(outEditor, new GridBagConstraints(0, 1, 2, 1, 5.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 2, 0));
			batPanel.add(btnOutChooser, new GridBagConstraints(2, 1, 1, 1, 0.5, 1.0, GridBagConstraints.EAST,
					GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
			batPanel.add(batchConstraintLatLabel, new GridBagConstraints(3, 0, 2, 1, 1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 2, 0));
			batPanel.add(batchConstraintLonLabel, new GridBagConstraints(3, 1, 2, 1, 1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 2, 0));
			
			// Now add the panels to the tabs...
			panel = new JTabbedPane(JTabbedPane.TOP, JTabbedPane.SCROLL_TAB_LAYOUT);
			panel.addTab(GEO_TAB, geoPanel);
			panel.addTab(ZIP_TAB, zipPanel);
			panel.addTab(BAT_TAB, batPanel);
		}
		currentMode = EMBED_FLAG;
		return panel;
	}
	
	private String getWebVisualization() {
		if(web == null) {
			web = "Visualization Not Implemented"; // Not really supported yet
		}
		currentMode = WEB_FLAG;
		return web;
	}
	
	private void btnFileChooser_actionPerformed() {
		JFileChooser chooser = new JFileChooser();
		chooser.setFileFilter(new FileFilter() {
			public boolean accept(File arg0) {
				return (arg0.getAbsolutePath().endsWith("xls") || arg0.isDirectory());
			}
			public String getDescription() {
				return "Microsoft Excel File (*.xls)";
			}
		});
		chooser.setDialogTitle("Select Input Batch File");
		JFrame frame = new JFrame("Select a batch file");
		int returnVal = chooser.showOpenDialog(frame);
		String newFileName = (String) batParam.getValue();
		if(returnVal == JFileChooser.APPROVE_OPTION) {
			newFileName = chooser.getSelectedFile().getAbsolutePath();
			try {
				batParam.setValue(newFileName);
				( (JTextField) batEditor.getValueEditor()).setText(newFileName);
			} catch (Exception ex) {
				batParam.unableToSetValue(newFileName);
			}
		}
	}

	private void btnOutChooser_actionPerformed() {
		JFileChooser chooser = new JFileChooser();
		chooser.setDialogTitle("Select Output Excel File");
		JFrame frame = new JFrame("Select Output File");
		int returnVal = chooser.showSaveDialog(frame);
		if(returnVal == JFileChooser.APPROVE_OPTION) {
			String newOutFile = chooser.getSelectedFile().getAbsolutePath();
			if(!newOutFile.endsWith(".xls"))
				newOutFile += ".xls";
			try {
				outParam.setValue(newOutFile);
				( (JTextField) outEditor.getValueEditor()).setText(newOutFile);
			} catch (Exception ex) {
				outParam.unableToSetValue(newOutFile);
			}
		}
	}
	

}
