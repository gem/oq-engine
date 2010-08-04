package scratch.martinez;

import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Timer;
import java.util.TimerTask;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;

import org.opensha.commons.util.FileUtils;

import scratch.martinez.beans.ProgressBar;

public class ProgressTest {
	private static ProgressBar progress = null;
	private static JFrame app = null;

	public static void main(String [] args) {
		app = createAppUI();
		app.setVisible(true);
		
		
	}
	
	private static JFrame createAppUI() {
		JFrame frame = new JFrame();
		frame.setTitle("Test Progress Bar Application");
		Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
		frame.setLocation(
	    		(dim.width - frame.getSize().width) / 2, 
	    		(dim.height - frame.getSize().height) / 2
	    );
		frame.setSize(new Dimension(100, 100));
		
		JPanel contentPanel = new JPanel(new GridBagLayout());
		JButton pButton = new JButton("Show Progress Bar");
		pButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent event) {
				runProgress();
			}
		});
		contentPanel.add(pButton, new GridBagConstraints(0, 0, 1, 1,
				1.0, 1.0, GridBagConstraints.CENTER, GridBagConstraints.NONE,
				new Insets(2, 2, 2, 2), 2, 2));
		
		frame.add(contentPanel);
		frame.pack();
		return frame;
	}
	
	private static void runProgress() {
		if(progress == null) {
			JPanel pPanel = new JPanel(new GridBagLayout());
			pPanel.add(new JLabel(new ImageIcon(
					FileUtils.loadImage("logos/usgs_logoonly.gif")
			)));
			progress = new ProgressBar(app, "Progress Meter", "Loading...",
					pPanel, 0);
		}
		progress.run();
		
		
		Timer t = new Timer();
		t.schedule(new TimerTask() {
			public void run() {
				endProgress();
			}
		}, 5000);
	}
	
	private static void endProgress() {
		progress.dispose();
	}
}
