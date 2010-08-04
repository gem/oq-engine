/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.calc.hazardMap.old.applet;

import java.awt.BorderLayout;
import java.awt.CardLayout;
import java.awt.Dimension;
import java.util.ArrayList;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JSeparator;

import org.opensha.commons.gui.ConsoleWindow;

public class HazardMapApplet extends JApplet implements OptionPanelListener, Loadable {
	
	boolean isApplet = true;
	
	ConsoleWindow console = new ConsoleWindow();
//	ConsoleWindow console = null;
	
	public static final String VERSION = "0.1";
	
	public static final String CREATE_OPTION = "Create New Dataset";
	public static final String STATUS_OPTION = "Check/Manage Calculation Status";
	public static final String PLOT_RETRIEVE_OPTION = "Plot/Download Data";
	
	public static final String BACK_OPTION = "Back";
	public static final String INITIAL_OPTION = "Initial Options";
	
	CreateDataManager creator = null;
	StatusCheckManager status = null;
	MapManager maps = null;
	
	OptionPanel initialOptionPanel;
	
	CardLayout cl = new CardLayout();
	
	JPanel mainPanel = new JPanel(cl);
	
	DataSetSelector selector = null;
	
	public static final int DEFAULT_WIDTH = 750;
	public static final int DEFAULT_HIGHT = 650;
	
	public HazardMapApplet() {
		super();
		
		this.setContentPane(mainPanel);
	}
	
	public void init() {
		// show the initial options
		System.out.println("Initializing...");
		initInitialOptions();
		
		this.setSize(new Dimension(750, 650));
	}
	
	private void initInitialOptions() {
		String message = "What would you like to do?";
		
		ArrayList<String> options = new ArrayList<String>();
		
		options.add(CREATE_OPTION);
		options.add(STATUS_OPTION);
		options.add(PLOT_RETRIEVE_OPTION);
		
		initialOptionPanel = new OptionPanel(message, options, this, console);
		
		initialOptionPanel.setBackEnabled(false);
		
		mainPanel.add(initialOptionPanel, INITIAL_OPTION);
		cl.show(mainPanel, INITIAL_OPTION);
//		this.setContentPane(initialOptionPanel);
//		this.add(initialOptionPanel, BorderLayout.CENTER);
	}
	
	public void optionSelected(String option) {
		if (option.equals(CREATE_OPTION)) {
			System.out.println("Selected Create Option");
			this.loadCreateOption();
		} else if (option.equals(STATUS_OPTION)) {
			System.out.println("Selected Status Option");
			this.loadStatusOption();
		} else if (option.equals(PLOT_RETRIEVE_OPTION)) {
			System.out.println("Selected Plot Option");
			this.loadMapOption();
		}
	}
	
	private void loadCreateOption() {
		if (creator == null) {
			creator = new CreateDataManager(this);
			
			this.add(creator.getPanel(), CREATE_OPTION);
		}
		
		cl.show(mainPanel, CREATE_OPTION);
		
		System.out.println("Done loading Create Option!");
	}
	
	protected void loadStatusOption() {
		if (status == null) {
			status = new StatusCheckManager(this);
			
			this.add(status.getPanel(), STATUS_OPTION);
		}
		
		cl.show(mainPanel, STATUS_OPTION);
		
		System.out.println("Done loading Status Option!");
	}
	
	protected void loadMapOption() {
		if (maps == null) {
			maps = new MapManager(this);
			
			this.add(maps.getPanel(), PLOT_RETRIEVE_OPTION);
		}
		
		cl.show(mainPanel, PLOT_RETRIEVE_OPTION);
		
		System.out.println("Done loading Map Option!");
	}
	
	public void loadStep() {
		// show the main screen
		cl.show(mainPanel, INITIAL_OPTION);
	}
	
	public ConsoleWindow getConsole() {
		return console;
	}
	
	public static JPanel createBottomPanel(JButton backButton, JButton nextButton, JButton consoleButton) {
		JPanel bottomPanel = new JPanel(new BorderLayout());
		
		JPanel leftPanel = new JPanel();
		leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.X_AXIS));
		if (backButton != null)
			leftPanel.add(backButton);
		
		if (consoleButton != null) {
			leftPanel.add(Box.createRigidArea(new Dimension(10, 0)));
			leftPanel.add(consoleButton);
		}
		
		bottomPanel.add(leftPanel, BorderLayout.WEST);
		
		if (nextButton != null) {
			bottomPanel.add(nextButton, BorderLayout.EAST);
		}
		
		JPanel bottom = new JPanel();
		bottom.setLayout(new BoxLayout(bottom, BoxLayout.Y_AXIS));
		bottom.add(new JSeparator());
		bottom.add(bottomPanel);
		
		return bottom;
	}
	
	public void setIsApplet(boolean isApplet) {
		this.isApplet = isApplet;
	}
	
	public boolean isApplet() {
		return this.isApplet;
	}
	
	public DataSetSelector getSelector() {
		if (selector == null)
			selector = new DataSetSelector();
		return selector;
	}
	
	public static void main(String args[]) {
		System.out.println("Starting Hazard Map Application");
		
		HazardMapApplet haz = new HazardMapApplet();
		
		haz.setIsApplet(false);
		
		JFrame frame = new JFrame();
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setTitle("HazardMapDataCalc App ("+VERSION+" )");
		frame.getContentPane().add(haz, BorderLayout.CENTER);
		haz.init();
		frame.setSize(haz.getSize());
//		frame.setSize(500,400);
//		Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
//		frame.setLocation((d.width - frame.getSize().width) / 2, (d.height - frame.getSize().height) / 2);
		frame.setLocationRelativeTo(null);
		frame.setVisible(true);
	}

}
