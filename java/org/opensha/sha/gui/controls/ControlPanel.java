package org.opensha.sha.gui.controls;

import java.awt.Window;

import org.opensha.commons.data.NamedObjectAPI;

/**
 * This is an abstract class representing a control panel to be included in one or more
 * applications. Implementing classes should put all setup work in the <code>doinit</code>
 * method, and return a GUI component to be displayed in the <code>getComponent</code> method.
 * 
 * @author kevin
 *
 */
public abstract class ControlPanel implements NamedObjectAPI {
	
	private String name;
	private boolean initialized = false;
	
	public ControlPanel(String name) {
		this.name = name;
	}
	
	/**
	 * This method will be called the first time the control panel is displayed. All
	 * setup should be in this method and not in the constructor, so that the apps can
	 * start quickly.
	 */
	public abstract void doinit();
	
	public boolean isInitialized() {
		return initialized;
	}
	
	public abstract Window getComponent();
	
	public final void init() {
		if (isInitialized())
			return;
		System.out.println(name + ": init()");
		doinit();
		initialized = true;
	}
	
	public String getName() {
		return name;
	}
	
	public void showControlPanel() {
		if (!this.isInitialized()) {
			this.init();
		}
		this.getComponent().setVisible(true);
		this.getComponent().pack();
	}

}
