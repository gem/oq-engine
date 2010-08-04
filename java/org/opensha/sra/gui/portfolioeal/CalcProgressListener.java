package org.opensha.sra.gui.portfolioeal;

import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.rmi.RemoteException;

import javax.swing.Timer;

import org.opensha.sha.gui.infoTools.CalcProgressBar;

/**
 * This class is used to create a progress bar for calculations.
 * @author Jeremy Leakakos
 *
 */
public class CalcProgressListener extends Thread implements ActionListener {

	private Asset asset;
	private Timer timer;
	private CalcProgressBar progressBar;
	private int totalRuptures;
	private int currentRuptures;
	
	/**
	 * The constructor for the listener.  It creates and displays a progress bar.
	 * 
	 * @param asset The asset that is having its EAL calculated
	 */
	public CalcProgressListener( Asset asset ) {
		this.asset = asset;
		progressBar = new CalcProgressBar("Hazard-Curve Calc Status", "Beginning Calculation ");
		progressBar.displayProgressBar();
	}
	
	/**
	 * The actionPerformed method for this listener.  It looks at the asset for the
	 * total and current ruptures, and updates the progress bar based on these numbers.
	 * It uses a timer to synchronize its firing.
	 */
	public void actionPerformed(ActionEvent e) {
		try {
			totalRuptures = asset.getTotalRuptures();
			currentRuptures = asset.getCurrentRuptures();
		} catch ( RemoteException ex ) {
		} catch ( NullPointerException ex) {
		}
		
		boolean isCalculationDone = asset.isCalculationDone();
		boolean rupturesStarted = false;
		
		if( currentRuptures == -1 ) {
			progressBar.setProgressMessage("Please wait, calculating total rutures for asset ....");
		}
		else {
			rupturesStarted = true;
		}
		if( rupturesStarted && !isCalculationDone) {
			progressBar.updateProgress(currentRuptures, totalRuptures);
		}
		if( isCalculationDone ) {
			progressBar.dispose();
			timer.stop();
		}
	}
	
	/**
	 * The run method for this thread subclass.  It creates and starts a timer with
	 * the objects actionListener.
	 */
	@Override
	public void run() {
		timer = new Timer(150, this);
		timer.start();
	}

}
