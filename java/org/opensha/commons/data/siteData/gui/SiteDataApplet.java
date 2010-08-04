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

package org.opensha.commons.data.siteData.gui;

import java.applet.Applet;
import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JTextField;

import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.data.siteData.gui.beans.OrderedSiteDataGUIBean;
import org.opensha.commons.geo.Location;

public class SiteDataApplet extends Applet implements ActionListener {
	
	private OrderedSiteDataGUIBean bean;
	
	private JTextField latField = new JTextField(8);
	private JTextField lonField = new JTextField(8);
	
	private JButton prefButton = new JButton("View Preffered Data");
	private JButton allButton = new JButton("View All Available Data");
	
	public SiteDataApplet() {
		bean = new OrderedSiteDataGUIBean(OrderedSiteDataProviderList.createCachedSiteDataProviderDefaults());
		
		this.setLayout(new BorderLayout());
		
		JPanel locationPanel = new JPanel();
		locationPanel.setLayout(new BoxLayout(locationPanel, BoxLayout.X_AXIS));
		locationPanel.add(new JLabel("Latitude: "));
		locationPanel.add(latField);
		locationPanel.add(new JLabel("Longitude: "));
		locationPanel.add(lonField);
		
		JPanel buttonPanel = new JPanel();
		buttonPanel.setLayout(new BoxLayout(buttonPanel, BoxLayout.X_AXIS));
		buttonPanel.add(prefButton);
		buttonPanel.add(allButton);
		
		JPanel bottomPanel = new JPanel(new BorderLayout());
		bottomPanel.add(locationPanel, BorderLayout.NORTH);
		bottomPanel.add(buttonPanel, BorderLayout.SOUTH);
		
		this.add(bean, BorderLayout.CENTER);
		this.add(bottomPanel, BorderLayout.SOUTH);
		
		prefButton.addActionListener(this);
		allButton.addActionListener(this);
		
		this.setPreferredSize(new Dimension(500, 600));
//		this.setSize(500, 800);
	}
	
	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == prefButton || e.getSource() == allButton) {
			boolean all = e.getSource() == allButton;
			
			Location loc;
			
			try {
				double lat = Double.parseDouble(latField.getText());
				double lon = Double.parseDouble(lonField.getText());
				
				loc = new Location(lat, lon);
			} catch (Exception e1) {
				e1.printStackTrace();
				JOptionPane.showMessageDialog(this, "Please enter a valid location!", "Invalid location!",
						JOptionPane.ERROR_MESSAGE);
				return;
			}
			
			OrderedSiteDataProviderList list = this.bean.getProviderList();
			ArrayList<SiteDataValue<?>> datas;
			if (all)
				datas = list.getAllAvailableData(loc);
			else
				datas = list.getBestAvailableData(loc);
			OrderedSiteDataGUIBean.showDataDisplayDialog(datas, this);
		}
	}
	
	/**
	 * Main class for running this as a regular java application
	 * 
	 * @param args
	 */
	public static void main(String args[]) {
		JFrame frame = new JFrame();
		SiteDataApplet applet = new SiteDataApplet();
		frame.setContentPane(applet);
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setSize(applet.getPreferredSize());
		frame.setVisible(true);
	}

}
