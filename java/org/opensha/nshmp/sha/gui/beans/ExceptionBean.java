package org.opensha.nshmp.sha.gui.beans;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;


/**
 * <strong>Title:</strong> ExceptionBean<br />
 * <strong>Description:</strong> An encapsulated class that allows non-command-line users to
 * get the benefits of an exception report. In the general case, if one runs a GUI application
 * by clicking on the icon in their OS and an exception (which is handled, right?) occures in 
 * the main thread, then the GUI stays up but nothing happens.  This class is meant to be used 
 * to alert the user the the failing and give a similar output as one might expect on the command line.
 * <br /><br />
 * As this class implements the <code>GuiBeanAPI</code>, one can visualize the bean in multiple
 * manners.  The initial implementation allows for a <code>WEB</code> (javascript alert), or a 
 * <code>SPLASH</code> visualization.  However, the <code>WEB</code> version is limited by the
 * fact that it relies on JavaScript.
 * 
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 * @TODO Button to generate an error report to send to the developer(s).
 * 
 */
public class ExceptionBean implements GuiBeanAPI {
	/* Private Variables */ 
	private String message = "";
	private String title = "";
	private static String DEFAULT_MSG = "An exception has occurred!";
	private static String DEFAULT_TITLE = "Error";
	private Exception exception = null;
	private JFrame splashFrame = null;
	private boolean showDetails = false;
	
	////////////////////////////////////////////////////////////////////////////////
	//                             PUBLIC FUNCTIONS                              //
	////////////////////////////////////////////////////////////////////////////////

	/* PUBLIC CONSTRUCTORS */
	/**
	 * Instantiates an new object with default values for the message and title.
	 */
	public ExceptionBean() {
		this(DEFAULT_MSG, DEFAULT_TITLE);
	}
	/**
	 * Instantiates a new object with a default title and the given message.
	 * @param message The message to show.
	 */
	public ExceptionBean(String message) {
		this(message, DEFAULT_TITLE);
	}
	/**
	 * Instantiates a new object with the given parameters.
	 * @param message The message to show.
	 * @param title The title of the Exception.
	 */
	public ExceptionBean(String message, String title) {
		this.message = message;
		this.title = title;
		// Use the defaults if null or empty
		if(this.message == null || this.message == "")
			this.message = DEFAULT_MSG;
		if(this.title == null || this.title == "")
			this.title = DEFAULT_TITLE;
	}
	/**
	 * Instantiates a new object with the given parameters
	 * @param message The message to show.
	 * @param title The title of the Exception.
	 * @param exception The exception that caued this.
	 */
	public ExceptionBean(String message, String title, Exception exception) {
		this(message, title);
		if(exception != null) {
			// If user provided no message, then use the exception's message
			// if it is available.  Else, just stick with the default.
			if(message.equals(DEFAULT_MSG) && exception.getMessage().length() > 0)
				message = exception.getMessage();
			this.exception = exception;
		}
	}
	
	/* FUNCTIONS TO IMPLEMENT THE GuiBeanAPI INTERFACE */
	/**
	 * See the general contract in <code>GuiBeanAPI</code>
	 * @see GuiBeanAPI
	 */
	public Object getVisualization(int type) throws IllegalArgumentException {
		if(type == GuiBeanAPI.WEB)
			return createWebVisualization();
		if(type == GuiBeanAPI.SPLASH)
			return createSplashVisualization();
		throw new IllegalArgumentException("The given type is not currently supported.");
	}
	/**
	 * See the general contract in <code>GuiBeanAPI</code>
	 * @see GuiBeanAPI
	 */
	public String getVisualizationClassName(int type) {
		if(type == GuiBeanAPI.WEB)
			return "java.lang.String";
		if(type == GuiBeanAPI.SPLASH)
			return "javax.swing.JFrame";
		else
			return null;
	}
	/**
	 * See the general contract in <code>GuiBeanAPI</code>
	 * @see GuiBeanAPI
	 */
	public boolean isVisualizationSupported(int type) {	return (type == GuiBeanAPI.SPLASH || type == GuiBeanAPI.WEB); }

	/* STATIC FUNCTIONS */
	/**
	 * A convenience wrapper function for easily viewing an exception window.
	 * This function call is equivilent to:
	 * <code>
	 * 	(new ExceptionBean(message, title)).getVisualization(GuiBeanAPI.SPLASH).setVisible(true);
	 * </code>
	 */
	public static void showSplashException(String message, String title, Exception ex) {
		ExceptionBean ew = new ExceptionBean(message, title, ex);
		JFrame frame = (JFrame) ew.getVisualization(GuiBeanAPI.SPLASH);
		frame.setVisible(true);
	}

	////////////////////////////////////////////////////////////////////////////////
	//                             PRIVATE FUNCTIONS                              //
	////////////////////////////////////////////////////////////////////////////////
	/**
	 * This method simply returns the javascript string that would show an alert
	 * with the given message.  There is no way programatically to force the
	 * pop-up from here, so this should be attached to an event somewhere.
	 * <br /><br />
	 * **Note** This function discregards the <code>title</code> since we
	 * cannot display that with an alert.
	 * 
	 * @return A JavaScript string that will cause an alert to be displayed
	 * with the current message.
	 */
	private String createWebVisualization() {
		return "alert('" + message + "');";
	}
	
	/**
	 * This function creates a <code>JFrame</code>, packs, and positions it.
	 * Can be anonymousely viewed with:
	 * <code>
	 * 	(new ExceptionBean("Message", "Title")).getVisualization(GuiBeanAPI.SPLASH).setVisible(true);
	 * </code>
	 * Or similarly with the convenience wrapper:
	 * <code>
	 * 	ExceptionBean.showSplashException("Message", "Title");
	 * </code>
	 * @return The JFrame for visualization.
	 */
	private JFrame createSplashVisualization() {
		splashFrame = new JFrame(title);
		showDetails = false;
		toggleDetails();
		splashFrame.pack();
		Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
		splashFrame.setLocation(
					(dim.width / 2) - splashFrame.getWidth(),
					(dim.height / 2) - splashFrame.getHeight()
				);
		splashFrame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		return splashFrame;
	}

	/**
	 * Destroys the current splash window.
	 */
	private void killSplashFrame() {
		if(splashFrame != null) {
				splashFrame.setVisible(false);
				splashFrame.dispose();
		}
		splashFrame = null;
	}
	
	private JPanel toggleDetails() {

		JPanel panel = (JPanel) splashFrame.getContentPane();
		panel.removeAll();
		
		JTextArea label = new JTextArea(message);
		label.setWrapStyleWord(true);
		label.setLineWrap(true);
		label.setEditable(false);
		float grey = (float) 0.5;
		label.setBackground(new Color(grey, grey, grey, (float) 0.0));
		label.setPreferredSize(new Dimension(300, 40));
		JButton btnDetails = null;
		JButton btnClose = new JButton("Okay");
		btnClose.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				killSplashFrame();	
			}
			
		});
		panel.setLayout(new GridBagLayout());
		panel.add(label, new GridBagConstraints(0, 0, 3, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
				new Insets(5, 5, 5, 5), 3, 3));
		panel.add(btnClose, new GridBagConstraints(2, 2, 1, 1, 1.0, 1.0,
				GridBagConstraints.EAST, GridBagConstraints.NONE,
				new Insets(2, 2, 2, 10), 0, 0));
		if(exception != null) {
			if(!showDetails)
				btnDetails = new JButton("Details>>");
			else
				btnDetails = new JButton("<<Hide");
			btnDetails.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent arg0) {
					toggleDetails();	
				}
			});
			panel.add(btnDetails, new GridBagConstraints(1, 2, 1, 1, 1.0, 1.0,
					GridBagConstraints.EAST, GridBagConstraints.NONE,
					new Insets(2, 50, 2, 2), 0, 0));
		}
		if(showDetails) {
			StringBuffer strBuf = new StringBuffer();
			StackTraceElement trace[] = exception.getStackTrace();
			strBuf.append(exception.getClass().toString()+"\n");
			for(int i = 0; i < trace.length; ++i)
				strBuf.append("   " + trace[i].getClassName() + "(" + 
						trace[i].getFileName() + ": " + 
						trace[i].getLineNumber() + ")\n");
			JScrollPane scroller = new JScrollPane(new JTextArea(strBuf.toString()));
			scroller.setPreferredSize(new Dimension(290, 100));
			scroller.setMinimumSize(new Dimension(290, 100));
			panel.add(scroller,	new GridBagConstraints(0, 1, 3, 1, 1.0, 1.0, GridBagConstraints.CENTER, 
						GridBagConstraints.HORIZONTAL, new Insets(5, 5, 5, 5), 2, 2));
						
		}
		
		// Toggle the details
		showDetails = !showDetails;
		
		panel.repaint();
		splashFrame.pack();
		splashFrame.repaint();
		return panel;
	}
}