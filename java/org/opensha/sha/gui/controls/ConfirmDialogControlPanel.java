package org.opensha.sha.gui.controls;

import java.awt.Component;
import java.awt.Window;

import javax.swing.JOptionPane;

/**
 * This is a special type of <code>ControlPanel</code> which instead of displaying a
 * GUI component where the user makes selections, simply presents a confirmation dialog
 * and applys changes if the user selects "OK".
 * 
 * @author kevin
 *
 */
public abstract class ConfirmDialogControlPanel extends ControlPanel {
	
	private String message;
	private Component parent;
	
	public ConfirmDialogControlPanel(String name, String message, Component parent) {
		super(name);
		this.message = message;
		this.parent = parent;
	}

	@Override
	public Window getComponent() {
		return null;
	}

	@Override
	public void showControlPanel() {
		if (!this.isInitialized()) {
			this.init();
		}
		int selectedOption = JOptionPane.showConfirmDialog(parent, message,
				getName(), JOptionPane.OK_CANCEL_OPTION);
		if(selectedOption == JOptionPane.OK_OPTION){
			applyControl();
		}
	}
	
	/**
	 * This method will be called if the user selects "OK" in the confirmation dialog.
	 */
	public abstract void applyControl();

}
