package org.opensha.nshmp.util;

import java.awt.Dimension;
import java.awt.Toolkit;
import java.text.DecimalFormat;

import javax.swing.JFrame;
import javax.swing.JProgressBar;

public class BatchProgress extends Thread {
	private String frameTitle;
	private int totalSize;
	private int numFinished = 0;
	private JFrame frame = null;
	private JProgressBar progress = null;
	private static final DecimalFormat format = new DecimalFormat("0.0#");
	
	public BatchProgress(String frameTitle, int totalSize) {
		this.totalSize = totalSize;
		this.frameTitle = frameTitle;
	}
	
	public void run() {
		frame = new JFrame(frameTitle);
		progress = new JProgressBar(0, totalSize);
		progress.setStringPainted(true);
		
		frame.getContentPane().add(progress);
		frame.pack();
		frame.setSize(400, 100);
		Dimension screen = Toolkit.getDefaultToolkit().getScreenSize();
		Dimension window = frame.getSize();
		frame.setLocation( (screen.width - window.width) / 2, (screen.height - window.height) / 2);
		
		frame.setVisible(true);
		
		try {
			while(!finished()) {
				int numFinished = getProgress();
				double p = (double) ((double) numFinished) / ((double) totalSize) * 100;
				String percent = format.format(p);
				
				String title = "" + numFinished + " of " + totalSize + " completed. (" +
						percent + "%)";
				
				progress.setString(title);
				progress.setValue(numFinished);
				//progress.updateUI();
				//frame.repaint();
				
				Thread.sleep(100);
			}
		} catch (InterruptedException e) {
			e.printStackTrace();
		} finally {
			progress.setValue(totalSize);
			progress.setString("Completed");
			frame.setVisible(false);
			frame.dispose();
			frame = null;
		}
	}

	public synchronized void update(int count) {
		this.numFinished = Math.min(count, totalSize);
	}
	
	public synchronized int getProgress() {return this.numFinished;}
	
	public boolean finished() {
		// Should never be >, but whatever
		return getProgress() >= totalSize;
	}
}
