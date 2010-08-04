package scratch.martinez.beans;

import java.awt.Dimension;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JFrame;
import javax.swing.JMenuItem;
import javax.swing.JTabbedPane;

import org.opensha.nshmp.sha.gui.beans.GuiBeanAPI;

import scratch.martinez.util.PropertyHandler;

public class PropertiesBean implements GuiBeanAPI {
	
	////////////////////////////////////////////////////////////////////////////////
	//                               PRIVATE VARIABLES                            //
	////////////////////////////////////////////////////////////////////////////////	
	private JFrame frame = null;
	private JTabbedPane tabs = null;
	private JMenuItem menuopt = null;
	private JButton button = null;
	private static PropertyHandler props = PropertyHandler.getInstance();
	private static PropertiesBean instance = null;
	
	////////////////////////////////////////////////////////////////////////////////
	//                                PUBLIC FUNCTIONS                            //
	////////////////////////////////////////////////////////////////////////////////
	
	/**
	 * This method is used to fetch an instance of the properties
	 * bean.  If an instance has already been instantiated, then
	 * that instance is returned, if not, then a new instance is
	 * instantiated and returned.  This method supports the
	 * singleton structure of this class.
	 * 
	 * @param appName Then name of the current application
	 * @return The instance of this singleton class
	 */
	public static PropertiesBean createInstance(String appName) {
		if(instance == null) {
			props = PropertyHandler.createPropertyHandler(appName, null);
			instance = new PropertiesBean();
		}
		return instance;
	}
	
	/**
	 * This method allows the user to add a new tab to the PropertiesBean.
	 * The <code>component</code> should generally be a <code>JScrollPane</code>
	 * or the like since the external object will not have control over how
	 * much real estate they have to display their property options.
	 * @param component The component to create a tab out of.
	 * @param title The title of this new tab
	 */
	public void addPropertyTab(String title, JComponent component) {
		if(tabs == null) createEmbedVisualization();
		tabs.add(title, component);
	}
	
	public void showPreferenceSplash() {
		if(frame==null) { createSplashVisualization(); }
		frame.pack();
		frame.setVisible(true);
	}
	
	/* Minimum functions to implement the GuBeanAPI */
	/**
	 * See the general contract in GuiBeanAPI.
	 * @see GuiBeanAPI
	 */
	public Object getVisualization(int type) throws IllegalArgumentException {
		if(type == GuiBeanAPI.EMBED) {
			return createEmbedVisualization();
		} else if (type == GuiBeanAPI.SPLASH) {
			return createSplashVisualization();
		} else if (type == GuiBeanAPI.MENUOPT) {
			return createMenuVisualization();
		} else if (type == GuiBeanAPI.BUTTON) {
			return createButtonVisualization();
		}
		throw new IllegalArgumentException("The given type is not currently supported!");
	}
	/**
	 * See the general contract in GuiBeanAPI.
	 * @see GuiBeanAPI
	 */
	public String getVisualizationClassName(int type) {
		if(type == GuiBeanAPI.EMBED) {
			return "javax.swing.JTabbedPane";
		} else if (type == GuiBeanAPI.SPLASH) {
			return "javax.swing.JFrame";
		} else if (type == GuiBeanAPI.MENUOPT) {
			return "javax.swing.JMenuItem";
		} else if (type == GuiBeanAPI.BUTTON) {
			return "javax.swing.JButton";
		}
		return null;
	}
	/**
	 * See the general contract in GuiBeanAPI.
	 * @see GuiBeanAPI
	 */
	public boolean isVisualizationSupported(int type) {
		return (type == GuiBeanAPI.EMBED || type == GuiBeanAPI.SPLASH ||
				type == GuiBeanAPI.MENUOPT || type == GuiBeanAPI.BUTTON);
	}

	////////////////////////////////////////////////////////////////////////////////
	//                               PRIVATE FUNCTIONS                            //
	////////////////////////////////////////////////////////////////////////////////
	
	/* Constcutors - Private since this is a singleton implementation */
	/**
	 * Empty because it is private (for singleton purposes), and it does nothing.
	 */
	private PropertiesBean() {}

	
	private JTabbedPane createEmbedVisualization() {
		if(tabs == null) {
			// Create a new tabbed pane with tabs across the top that wrap if there are too many
			tabs = new JTabbedPane(JTabbedPane.TOP, JTabbedPane.WRAP_TAB_LAYOUT);
			
		}
		return tabs;
	}
	
	private JFrame createSplashVisualization() {
		if(frame == null) {
			// A frame needs some content first
			if(tabs == null) { createEmbedVisualization(); }
			frame = new JFrame("Properties");
			frame.getContentPane().add(tabs);
			frame.pack();
			Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
			frame.setLocation( (screenSize.width - frame.getWidth()) / 2,
					(screenSize.height - frame.getHeight()) / 2);
		}
		if(props != null) 
			frame.setTitle(props.getAppName().replace("_", " ") + " Properties");
		return frame;
	}
	
	private JMenuItem createMenuVisualization() {
		if(menuopt == null) {
			// A menu needs a frame to display first
			if(frame == null) { createSplashVisualization(); }
			menuopt = new JMenuItem("Properties");
			menuopt.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent event) {
					showPreferenceSplash();
				}
			});
		}
		return menuopt;
	}
	
	private JButton createButtonVisualization() {
		if(button == null) {
			button = new JButton("Preferences");
			button.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent event) {
					showPreferenceSplash();
				}
			});
		}
		return button;
	}
}
