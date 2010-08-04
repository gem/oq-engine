package scratch.martinez.beans;

import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JProgressBar;
import javax.swing.SwingConstants;

public class ProgressBar implements Runnable {
	private Component parent = null;
	private JLabel textLabel = null;
	private JPanel otherContent = null;
	private JProgressBar progress = null;
	private int maxProgress = 0;
	private String windowTitle = "";
	private JFrame progressWindow = new JFrame();
	private JPanel mainContent = new JPanel(new GridBagLayout());
	
	public ProgressBar(Component parent, String textLabel, String title,
			JPanel otherContent, int maxProgress) {
		
		this.parent = parent;
		this.textLabel = new JLabel(textLabel, SwingConstants.CENTER);
		this.otherContent = otherContent;
		this.maxProgress = maxProgress;
		this.windowTitle = title;
		initialize();
	}
	
	private void initialize() {
		if(maxProgress == 0) {
			progress = new JProgressBar();
			progress.setIndeterminate(true);
		} else {
			progress = new JProgressBar(0, maxProgress);
		}
		
		int ypos = 0;
		// Add the text label if we should
		if(textLabel != null && textLabel.getText().length() > 0) {
			mainContent.add(textLabel, new GridBagConstraints(0, ypos, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 0, 0));
			++ypos;
		}
		// Add the content label if we should
		if(otherContent != null) {
			mainContent.add(otherContent, new GridBagConstraints(0, ypos, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 0, 0));
			++ypos;
		}
		mainContent.add(progress, new GridBagConstraints(0, ypos, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER,
				GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 0, 0));
		
		progressWindow.add(mainContent);
		progressWindow.pack();
		double xloc = 0.0; double yloc = 0.0;
		if(parent != null) {
			xloc = (parent.getX() + (parent.getWidth() / 2)) - (progressWindow.getWidth() / 2);
			yloc = (parent.getY() + (parent.getHeight() / 2)) - (progressWindow.getHeight() / 2);
		} else {
			Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
		    xloc = (dim.width - progressWindow.getSize().width) / 2;
		    yloc = (dim.height - progressWindow.getSize().height) / 2;
		}
		
		progressWindow.setLocation((int) xloc, (int) yloc);
		progressWindow.setTitle(windowTitle);
	}

	public void run() {
		progressWindow.setVisible(true);
		progressWindow.repaint();
	}
	
	public void dispose() {
		progressWindow.dispose();
	}
}
