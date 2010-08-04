package scratch.martinez.LossCurveSandbox;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;

import javax.swing.ImageIcon;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JWindow;

import scratch.martinez.LossCurveSandbox.beans.VulnerabilityBean;
import scratch.martinez.LossCurveSandbox.ui.gui.AbstractGuiEditor;
import scratch.martinez.LossCurveSandbox.ui.gui.LocationBeanGuiEditor;
import scratch.martinez.LossCurveSandbox.ui.gui.VulnerabilityBeanGuiEditor;
import scratch.martinez.LossCurveSandbox.util.MenuMaker;

/**
 * This is currently a development unit testing class. It does not reflect an
 * intended application.
 * 
 */
public class LossCurveGui {
	public static void main(String [] args) {
		
		String defaultDir = null;
		if(args.length != 0) {
			defaultDir = args[0];
		}
		
		JLabel splashLabel = new JLabel("Hi"/*new ImageIcon(
				LossCurveGui.class.getResource(
						//"/resources/images/splash/lossCurveSplash.png")));
						"/dev/scratch/martinez/lossCurveSplash.png"))*/);
		JWindow splashWindow = new JWindow();
		splashWindow.getContentPane().add(splashLabel);
		splashWindow.pack();
		splashWindow.setLocation(
			(int) (AbstractGuiEditor.screenSize.width - splashWindow.getWidth()) / 2,
			(int) (AbstractGuiEditor.screenSize.height - splashWindow.getHeight()) / 2
		);
		
		splashWindow.setVisible(true);
		
		VulnerabilityBean bean = VulnerabilityBean.getSharedInstance(defaultDir);
		VulnerabilityBeanGuiEditor vulnEditor = 
			new VulnerabilityBeanGuiEditor(bean);
		LocationBeanGuiEditor locEditor = new LocationBeanGuiEditor();
		
		
		JFrame appWindow = new JFrame("Unit Test App");
		appWindow.getContentPane().setLayout(new GridBagLayout());
		appWindow.getContentPane().add(vulnEditor.getPanelEditor(),
				new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
						GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL,
						new Insets(0, 0, 0, 0), 0, 0));
		appWindow.getContentPane().add(locEditor.getPanelEditor(),
				new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0,
						GridBagConstraints.CENTER, GridBagConstraints.BOTH,
						new Insets(0, 0, 0, 0), 0, 0));
		appWindow.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

		MenuMaker.addMenuOptions(vulnEditor.getMenuOptions());
		MenuMaker.addMenuOptions(locEditor.getMenuOptions());
		MenuMaker.setParentFrame(appWindow);
		
		appWindow.pack();
		
		splashWindow.setVisible(false);
		splashWindow.dispose();
		
		appWindow.setVisible(true);
		
	}
}
