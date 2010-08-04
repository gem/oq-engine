package scratch.martinez.beans;

import java.awt.Component;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.SwingConstants;

import org.opensha.commons.util.FileUtils;
import org.opensha.nshmp.sha.gui.beans.GuiBeanAPI;

/**
 * This bean provides a simplified way to give credit to contributors of applications in a
 * cooperative environment. This class implements <code>GuiBeanAPI</code> and can be visualized
 * in three ways, as a JButton (<code>BUTTON</code>), an embeddable JPanel (<code>EMBED</code>),
 * or as a splash screen JFrame (<code>SPLASH</code>).  The <code>EMBED</code> and 
 * <code>SPLASH</code> options are fairly straightforward, however the <code>BUTTON</code>
 * option might benefit from some explaining.  The <code>BUTTON</code> creates a JButton (with
 * optionally specified text), that when clicked will show a <code>SPLASH</code> visualization.
 * By using the <code>BUTTON</code> visualization you can easily add a button to show a credit
 * splash screen.
 *  
 * @TODO Implement a <code>MENUOPT</code> visualization that makes it easier to add this
 * self-visualizing bean as a menu option.
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 * @see GuiBeanAPI
 */
public class CreditBean implements GuiBeanAPI {
	
	/** A known available image to use for credit purposes */
	public static final String USGS = "logos/usgslogo.gif";
	/** A known available image to use for credit purposes */
	public static final String USGS_RES = "logos/usgs_resrisk.gif";
	/** A known available image to use for credit purposes */
	public static final String AGORA = "logos/AgoraOpenRisk.jpg";
	/** A known available image to use for credit purposes */
	public static final String OPENSHA = "logos/PoweredByOpenSHA_Agua.jpg";
	
	private JButton button = null;
	private String buttonText = "";
	private JFrame frame = null;
	private JPanel panel = null;
	private Component parent = null;
	private ArrayList<JLabel> contributors = new ArrayList<JLabel>();
	
	private static final JLabel defaultLabel = new 
		JLabel("A Collaborative Effort", SwingConstants.CENTER);
	private static final String DEFAULTTEXT = "Credits";
	private static ArrayList<JLabel> defaultLabels = new ArrayList<JLabel>();
	private static ArrayList<String> knownImages = new ArrayList<String>();
	
	/* Initialiaze the knownImages */
	static {
		knownImages.add(USGS);
		knownImages.add(USGS_RES);
		knownImages.add(AGORA);
		knownImages.add(OPENSHA);
		defaultLabels.add(defaultLabel);
	}
	
	/**
	 * Creates a new <code>CreditBean</code> with the given parameters.  If any parameter
	 * is ommitted ( or null), a valid default parameter is given.
	 *  
	 * @param parent The parent <code>Component</code> of this bean.  This is used when determining
	 * the location of where to show a <code>SPLASH</code> visualization (or where to pop up the
	 * window from a <code>BUTTON</code> visualization.
	 * @param contributors A list of <code>JLabels</code>s for the contributing parties
	 * to whom credit is deserved.
	 * @param buttonText The text you wish to appear on a <code>BUTTON</code> visualization
	 * of this bean.
	 */
	public CreditBean(Component parent, ArrayList<JLabel> contributors, String buttonText) {
		this.parent = parent;
		if(contributors != null)
			this.contributors = contributors;
		else
			this.contributors = defaultLabels;
		this.buttonText = buttonText;
	}
	
	/**
	 * Creates a new <code>CreditBean</code> with the given parameters.  If any parameter
	 * is ommitted ( or null), a valid default parameter is given.
	 *  
	 * @param parent The parent <code>Component</code> of this bean.  This is used when determining
	 * the location of where to show a <code>SPLASH</code> visualization (or where to pop up the
	 * window from a <code>BUTTON</code> visualization.
	 * @param contributors A list of <code>String</code>s listing off the contributing parties
	 * to whom credit is deserved.  If the passed <code>String</code> matches a known image name,
	 * then the image is used for the underlying label, else the text itself is used.
	 * @param buttonText The text you wish to appear on a <code>BUTTON</code> visualization
	 * of this bean.
	 */
	public CreditBean(Component parent, String [] contributors, String buttonText ) {
		this.parent = parent;
		if(contributors != null) {
			for(int i = 0; i < contributors.length; ++i) {
				this.contributors.add(createLabel(contributors[i]));
			}
		} else {
			this.contributors.add(defaultLabel);
		}
		this.buttonText = buttonText;
	}
	
	/** 
	 * Creates a new CreditBean with <code>parent</code>, and then uses defaults
	 * for other parameters.
	 */
	public CreditBean(Component parent) {
		this(parent, defaultLabels, DEFAULTTEXT);
	}
	/**
	 * Create a new <code>CreditBean</code> with <code>contributors</code> listed, and uses
	 * defaults for other parameters.
	 */
	public CreditBean(String [] contributors) {
		this(null, contributors, DEFAULTTEXT);
	}
	/**
	 * Creates a new <code>CreditBean</code> with <code>parent</code> and <code>buttonText</code>
	 * and then uses defaults for other parameters.
	 */
	public CreditBean(Component parent, String buttonText) {
		this(parent, defaultLabels, buttonText);
	}
	/**
	 * Creates a new <code>CreditBean</code> with all default parameters.
	 */
	public CreditBean() {
		this(null, defaultLabels, DEFAULTTEXT);
	}
	
	/**
	 * Allows &quot;after market&quot; setting of the button text for a
	 * <code>BUTTON</code> visualization of this class.  Note that while this
	 * is loosely called &quot;after market&quot;, this change is only realized
	 * in beans that are visualized after a call to this function.
	 * @param text The new text of the </code>BUTTON</code> visualization
	 */
	public void setButtonText(String text) {
		buttonText = text;
		if(button != null)
			button.setText(buttonText);
	}
	
	/**
	 * Creates a <code>SPLASH<code> visualization of this bean and sets its
	 * visibility to <code>visible</code>.  This is a required function, but also a
	 * convenience function as the following statements will have the same effect:<br /><br />
	 * <code>((JFrame) bean.getVisualization(CreditBean.SPLASH)).setVisible(true);</code>
	 * <br />
	 * <code>bean.setVisible(true);</code>
	 * <br />
	 * @param visible <code>true</code> to show the bean, <code>false</code> to hide it
	 */
	public void setVisible(boolean visible) {
		if(frame == null)
			createSplashVisualization();
		frame.setVisible(visible);
	}
	/**
	 * See the general contract in <code>GuiBeanAPI</code>
	 * @see GuiBeanAPI
	 */
	public Object getVisualization(int type) throws IllegalArgumentException {
		if(type == BUTTON)
			return createButtonVisualization();
		else if(type == EMBED)
			return createEmbededVisualization();
		else if(type == SPLASH)
			return createSplashVisualization();
		else
			throw new IllegalArgumentException("This given type is not currently supported.");
	}
	
	/**
	 * See the general contract in <code>GuiBeanAPI</code>
	 * @see GuiBeanAPI
	 */
	public String getVisualizationClassName(int type) {
		if(type == BUTTON)
			return "javax.swing.JButton";
		else if(type == EMBED)
			return "javax.swing.JPanel";
		else if(type == SPLASH)
			return "javax.swing.JFrame";
		else
			return null;
	}

	/**
	 * See the general contract in <code>GuiBeanAPI</code>
	 * @see GuiBeanAPI
	 */
	public boolean isVisualizationSupported(int type) {
		return (type == BUTTON || type == EMBED || type == SPLASH);
	}
	
	/* Creates the appropriate labels for credit purposes */
	private JLabel createLabel(String imgName) {
		JLabel label = null;
		if(knownImages.contains(imgName))
			label = new JLabel(new ImageIcon(FileUtils.loadImage(imgName)));
		else
			label = new JLabel(imgName, SwingConstants.CENTER);
		return label;
	}
	
	/* Private function to actually perform BUTTON visualization */
	private JButton createButtonVisualization() {
		if(button == null) {
			button = new JButton(buttonText);
			button.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent event) {
					setVisible(true);
				}
			});
		}
		return button;
	}

	/* Private function to actually perform EMBED visualization */
	private JPanel createEmbededVisualization() {
		panel = new JPanel(new FlowLayout());
		for(int i = 0; i < contributors.size(); ++i)
			panel.add(contributors.get(i), i);
		return panel;
	}
	
	/* Private function to actually perform SPLASH visualization */
	private JFrame createSplashVisualization() {
		frame = new JFrame();
		if(panel == null)
			createEmbededVisualization();
		frame.add(panel);
		frame.pack();
		if(parent == null) {
			Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
			frame.setLocation(
					(dim.width / 2) - frame.getWidth(),
					(dim.height / 2) - frame.getHeight()
				);
		} else {
			frame.setLocation(
					(parent.getX() + parent.getWidth()) / 2,
					(parent.getY() + parent.getHeight()) /2
					);
		}
		return frame;
	}
}
