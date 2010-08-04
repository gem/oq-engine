package scratch.martinez.data;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Hashtable;

import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JTextField;

import scratch.martinez.util.Customizable;
import scratch.martinez.util.PropertyHandler;

public class DataMiner implements Customizable {
	// The two available modes
	private static final String REMOTE_DB = "Remote From Database";
	private static final String LOCAL_FILES = "Local Flat Files";
	
	// Property Keys
	private static final String MODE = "dataMinerMode";
	private static final String PROXY_HOST = "dataMinerProxyHost";
	private static final String PROXY_PORT = "dataMinerProxyPort";
	private static final String LOCAL_DIR = "dataMinerLocalFileDir";
	
	// Default Property Values
	private static final String DEFAULT_MODE = REMOTE_DB;
	private static final String DEFAULT_PROXY_HOST = "";
	private static final String DEFAULT_PROXY_PORT = "80";
	private static final String DEFAULT_LOCAL_DIR = "";
	
	// This can safely be static since this is a singleton class anyway.
	private static PropertyHandler properties = PropertyHandler.getInstance();
	
	// Components for the PropertyPane
	private JPanel componentPanel = null;
	private JRadioButton radioRemoteDB = null;
	private JRadioButton radioLocalFile = null;
	private JTextField txtProxyHost = null;
	private JTextField txtProxyPort = null;
	private JTextField txtLocalDir = null;
	
	// Tooltip texts for the above components
	private static final String radioRemoteDBToolTip = "Select this option to mine data off a server.  (Internet Connection Required).";
	private static final String radioLocalFileToolTip = "Select this option to mine data locally on your machine.  (No Internet Required).";
	private static final String txtProxyHostToolTip = "Set to host of your local proxy. Only required to for use with the remote data mining option.";
	private static final String txtProxyPortToolTip = "Set to port number of your local proxy.  Only required for use with the remote data mining option.";
	private static final String txtLocalDirToolTip = "Set to the local file directory where you saved to data files for this application.  (Fully qualified paths required).";
	
	public DataMiner() {
		// Set up the default values for data mining preferences
		Hashtable<String, String> defaultMining = new Hashtable<String, String>();
		defaultMining.put(MODE, DEFAULT_MODE);
		defaultMining.put(PROXY_HOST, DEFAULT_PROXY_HOST);
		defaultMining.put(PROXY_PORT, DEFAULT_PROXY_PORT);
		defaultMining.put(LOCAL_DIR, DEFAULT_LOCAL_DIR);
		if(properties != null)
			properties.setDefaultProperties(defaultMining);
	}
	
	public JComponent getPropertyPane() {
		if(componentPanel == null) {
			componentPanel = new JPanel(new GridBagLayout());
			
			// Set up the mining mode components
			radioRemoteDB = new JRadioButton("Remote Database");
			radioRemoteDB.setSelected(true);
			radioRemoteDB.setToolTipText(radioRemoteDBToolTip);
			radioRemoteDB.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent arg0) {
					setRemoteMining(true);
				}
			});
			radioLocalFile = new JRadioButton("Local Files");
			radioLocalFile.setToolTipText(radioLocalFileToolTip);
			radioLocalFile.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent e) {
					setRemoteMining(false);
				}
			});
			
			// Set up the parameter components
			txtProxyHost = new JTextField();
			txtProxyHost.setText(DEFAULT_PROXY_HOST);
			txtProxyHost.setToolTipText(txtProxyHostToolTip);
			txtProxyHost.setColumns(15);
			txtProxyHost.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent e) {
					JOptionPane.showMessageDialog(null, e.paramString());
				}
			});
			txtProxyPort = new JTextField();
			txtProxyPort.setText(DEFAULT_PROXY_PORT);
			txtProxyPort.setToolTipText(txtProxyPortToolTip);
			txtProxyPort.setColumns(15);
			txtProxyPort.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent e) {
					JOptionPane.showMessageDialog(null, e.paramString());
				}
			});
			txtLocalDir = new JTextField();
			txtLocalDir.setText(DEFAULT_LOCAL_DIR);
			txtLocalDir.setToolTipText(txtLocalDirToolTip);
			txtLocalDir.setColumns(15);
			txtLocalDir.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent e) {
					JOptionPane.showMessageDialog(null, e.paramString());
				}
			});
		
			componentPanel.add(new JLabel("Select Data Mining Mode"), new GridBagConstraints(0, 0, 2, 1, 1.0, 1.0,
					GridBagConstraints.CENTER, GridBagConstraints.NONE,
					new Insets(0, 0, 0, 0), 0, 0));
			componentPanel.add(radioRemoteDB, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0,
					GridBagConstraints.WEST, GridBagConstraints.NONE,
					new Insets(0, 20, 0, 0), 0, 0));
			componentPanel.add(radioLocalFile, new GridBagConstraints(1, 1, 1, 1, 1.0, 1.0,
					GridBagConstraints.EAST, GridBagConstraints.NONE,
					new Insets(0, 0, 0, 20), 0, 0));
			componentPanel.add(new JLabel("Proxy Host:"), new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0,
					GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
					new Insets(0, 0, 0, 0), 0, 2));
			componentPanel.add(txtProxyHost, new GridBagConstraints(1, 2, 1, 1, 1.0, 1.0,
					GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL,
					new Insets(0, 0, 0, 0), 0, 2));
			componentPanel.add(new JLabel("Proxy Port:"), new GridBagConstraints(0, 3, 1, 1, 1.0, 1.0,
					GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
					new Insets(0, 0, 0, 0), 0, 2));
			componentPanel.add(txtProxyPort, new GridBagConstraints(1, 3, 1, 1, 1.0, 1.0,
					GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
					new Insets(0, 0, 0, 0), 0, 2));
			componentPanel.add(new JLabel("Local File Directory:"), new GridBagConstraints(0, 4, 1, 1, 1.0, 1.0,
					GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
					new Insets(0, 0, 0, 0), 0, 2));
			componentPanel.add(txtLocalDir, new GridBagConstraints(1, 4, 1, 1, 1.0, 1.0,
					GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
					new Insets(0, 0, 0, 0), 0, 2));
			
		}
		return componentPanel;
	}

	private void setRemoteMining(boolean b) {
		if(b)
			properties.setProperty(MODE, REMOTE_DB);
		else
			properties.setProperty(MODE, LOCAL_FILES);
		
		radioRemoteDB.setSelected(b);
		radioLocalFile.setSelected(!b);
		txtLocalDir.setEnabled(!b);
		txtProxyHost.setEnabled(b);
		txtProxyPort.setEnabled(b);
	}
}
