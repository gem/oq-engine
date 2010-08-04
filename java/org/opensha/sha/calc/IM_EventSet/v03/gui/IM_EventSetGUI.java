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

package org.opensha.sha.calc.IM_EventSet.v03.gui;

import java.awt.BorderLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JTabbedPane;

import org.dom4j.Document;
import org.dom4j.Element;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.data.siteData.gui.beans.OrderedSiteDataGUIBean;
import org.opensha.commons.data.siteData.impl.WillsMap2006;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetCalculation;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetOutputWriter;
import org.opensha.sha.calc.IM_EventSet.v03.outputImpl.HAZ01Writer;
import org.opensha.sha.calc.IM_EventSet.v03.outputImpl.OriginalModWriter;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupForecastBaseAPI;
import org.opensha.sha.gui.HazardCurveLocalModeApplication;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;

public class IM_EventSetGUI extends JFrame implements ActionListener {
	
	private static File cwd = new File(System.getProperty("user.dir"));
	
	private SitesPanel sitesPanel = null;
	private ERF_GuiBean erfGuiBean = null;
	private IMR_ChooserPanel imrChooser = null;
	private IMT_ChooserPanel imtChooser = null;
	private OrderedSiteDataGUIBean dataBean = null;
	
	private JTabbedPane tabbedPane;
	
	private JPanel imPanel = new JPanel();
	private JPanel siteERFPanel = new JPanel();
	
	private JButton calcButton = new JButton("Start Calculation");
	private JButton saveButton = new JButton("Save Calculation Settings");
	private JButton loadButton = new JButton("Load Calculation Settings");
	
	private JFileChooser openChooser;
	private JFileChooser saveChooser;
	private JFileChooser outputChooser;
	
	private JComboBox outputWriterChooser;
	
//	private JProgressBar bar = new JProgressBar();
	
	public IM_EventSetGUI() {
		sitesPanel = new SitesPanel();
		erfGuiBean = createERF_GUI_Bean();
		imtChooser = new IMT_ChooserPanel();
		imrChooser = new IMR_ChooserPanel(imtChooser);
		
		OrderedSiteDataProviderList providers = OrderedSiteDataProviderList.createSiteDataProviderDefaults();
		for (int i=0; i<providers.size(); i++) {
			if (!providers.getProvider(i).getName().equals(WillsMap2006.NAME))
				providers.setEnabled(i, false);
		}
		
		dataBean = new OrderedSiteDataGUIBean(providers);
		
		imPanel.setLayout(new BoxLayout(imPanel, BoxLayout.X_AXIS));
		imPanel.add(imrChooser);
		imPanel.add(imtChooser);
		
		siteERFPanel.setLayout(new BoxLayout(siteERFPanel, BoxLayout.X_AXIS));
		siteERFPanel.add(sitesPanel);
		siteERFPanel.add(erfGuiBean);
		
		tabbedPane = new JTabbedPane();
		
		tabbedPane.addTab("Sites/ERF", siteERFPanel);
		tabbedPane.addTab("IMRs/IMTs", imPanel);
		tabbedPane.addTab("Site Data Providers", dataBean);
		
		JPanel mainPanel = new JPanel(new BorderLayout());
		
		String writers[] = new String[2];
		writers[0] = OriginalModWriter.NAME;
		writers[1] = HAZ01Writer.NAME;
		outputWriterChooser = new JComboBox(writers);
		JPanel outputWriterChooserPanel = new JPanel();
		outputWriterChooserPanel.add(outputWriterChooser);
		
		JPanel bottomPanel = new JPanel();
		bottomPanel.setLayout(new BoxLayout(bottomPanel, BoxLayout.X_AXIS));
		bottomPanel.add(outputWriterChooserPanel);
		bottomPanel.add(calcButton);
		bottomPanel.add(saveButton);
		bottomPanel.add(loadButton);
//		bottomPanel.add(bar);
		calcButton.addActionListener(this);
		saveButton.addActionListener(this);
		loadButton.addActionListener(this);
		
		mainPanel.add(tabbedPane, BorderLayout.CENTER);
		mainPanel.add(bottomPanel, BorderLayout.SOUTH);
		
		this.setTitle("IM Event Set Calculator v3.0");
		
		this.setContentPane(mainPanel);
	}
	
	private ERF_GuiBean createERF_GUI_Bean() {
		try {
			return new ERF_GuiBean(HazardCurveLocalModeApplication.getLocalERFClasses());
		} catch (InvocationTargetException e) {
			throw new RuntimeException(e);
		}
	}
	
	public IM_EventSetCalculation getEventSetCalc() {
		EqkRupForecastAPI erf = null;
		try {
			erf = (EqkRupForecastAPI) this.erfGuiBean.getSelectedERF_Instance();
		} catch (InvocationTargetException e) {
			throw new RuntimeException(e);
		}
		ArrayList<EqkRupForecastAPI> erfs = new ArrayList<EqkRupForecastAPI>();
		erfs.add(erf);
		
		ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs = imrChooser.getSelectedIMRs();
		
		ArrayList<String> imts = imtChooser.getIMTStrings();
		ArrayList<Location> locs = sitesPanel.getLocs();
		ArrayList<ArrayList<SiteDataValue<?>>> vals = sitesPanel.getDataLists();
		
		OrderedSiteDataProviderList providers = this.dataBean.getProviderList().clone();
		providers.removeDisabledProviders();
		
		return new IM_EventSetCalculation(locs, vals, erfs, imrs, imts, providers);
	}
	
	private boolean isReadyForCalc(ArrayList<Location> locs, ArrayList<ArrayList<SiteDataValue<?>>> dataLists,
			EqkRupForecastAPI erf, ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs, ArrayList<String> imts) {
		
		if (locs.size() < 1) {
			JOptionPane.showMessageDialog(this, "You must add at least 1 site!", "No Sites Selected!",
					JOptionPane.ERROR_MESSAGE);
			return false;
		}
		if (locs.size() != dataLists.size()) {
			JOptionPane.showMessageDialog(this, "Internal error: Site data lists not same size as site list!",
					"Internal error", JOptionPane.ERROR_MESSAGE);
			return false;
		}
		if (erf == null) {
			JOptionPane.showMessageDialog(this, "Error instantiating ERF!", "Error with ERF!",
					JOptionPane.ERROR_MESSAGE);
			return false;
		}
		if (imrs.size() < 1) {
			JOptionPane.showMessageDialog(this, "You must add at least 1 IMR!", "No IMRs Selected!",
					JOptionPane.ERROR_MESSAGE);
			return false;
		}
		if (imts.size() < 1) {
			JOptionPane.showMessageDialog(this, "You must add at least 1 IMT!", "No IMTs Selected!",
					JOptionPane.ERROR_MESSAGE);
			return false;
		}
		return true;
	}
	
	public void actionPerformed(ActionEvent e) {
		if (e.getSource().equals(calcButton)) {
			// make sure we're ready to calculate first
			ArrayList<Location> locs = null;
			ArrayList<ArrayList<SiteDataValue<?>>> dataLists = null;
			EqkRupForecastAPI erf = null;
			ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs = null;
			ArrayList<String> imts = null;
			try {
				locs = sitesPanel.getLocs();
				dataLists = sitesPanel.getDataLists();
				erf = (EqkRupForecastAPI)erfGuiBean.getSelectedERF();
				imrs = imrChooser.getSelectedIMRs();
				imts = imtChooser.getIMTStrings();
				
				if (!isReadyForCalc(locs, dataLists, erf, imrs, imts))
					return;
			} catch (Exception e2) {
				e2.printStackTrace();
				JOptionPane.showMessageDialog(this, e2.getMessage(), "Exception Preparing Calculation",
						JOptionPane.ERROR_MESSAGE);
			}
			
			if (outputChooser == null) {
				outputChooser = new JFileChooser(cwd);
				outputChooser.setDialogTitle("Select Output Directory");
				outputChooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
			}
			int returnVal = outputChooser.showOpenDialog(this);;
			if (returnVal == JFileChooser.APPROVE_OPTION) {
				File outputDir = outputChooser.getSelectedFile();
				GUICalcAPI_Impl calc = new GUICalcAPI_Impl(locs, dataLists,
						outputDir, dataBean.getProviderList());
				IM_EventSetOutputWriter writer;
				String writerName = (String) outputWriterChooser.getSelectedItem();
				if (writerName.equals(OriginalModWriter.NAME))
					writer = new OriginalModWriter(calc);
				else if (writerName.equals(HAZ01Writer.NAME))
					writer = new HAZ01Writer(calc);
				else
					throw new RuntimeException("Unknown writer: " + writerName);
				try {
//					bar.setIndeterminate(true);
//					bar.setString("Calculating...");
//					bar.setStringPainted(true);
					this.calcButton.setEnabled(false);
					this.validate();
					writer.writeFiles(erf, imrs, imts);
				} catch (Exception e1) {
//					bar.setIndeterminate(false);
//					bar.setStringPainted(false);
					this.calcButton.setEnabled(true);
					throw new RuntimeException(e1);
				}
				this.calcButton.setEnabled(true);
//				bar.setIndeterminate(false);
//				bar.setStringPainted(false);
			}
		} else if (e.getSource().equals(saveButton)) {
			if (saveChooser == null)
				saveChooser = new JFileChooser(cwd);
			int returnVal = saveChooser.showSaveDialog(this);
			if (returnVal == JFileChooser.APPROVE_OPTION) {
				IM_EventSetCalculation calc = getEventSetCalc();
				File file = saveChooser.getSelectedFile();
				Document doc = XMLUtils.createDocumentWithRoot();
				Element root = doc.getRootElement();
				calc.toXMLMetadata(root);
				try {
					XMLUtils.writeDocumentToFile(file.getAbsolutePath(), doc);
				} catch (IOException e1) {
					e1.printStackTrace();
				}
			}
		} else if (e.getSource().equals(loadButton)) {
			if (openChooser == null)
				openChooser = new JFileChooser(cwd);
			int returnVal = openChooser.showOpenDialog(this);
			if (returnVal == JFileChooser.APPROVE_OPTION) {
				File file = openChooser.getSelectedFile();
				Document doc = null;
				try {
					doc = XMLUtils.loadDocument(file.getAbsolutePath());
				} catch (Exception e1) {
					// TODO Auto-generated catch block
					e1.printStackTrace();
					JOptionPane.showMessageDialog(this, "Error loading XML file:\n" + e1.getMessage(),
							"Error loading XML!", JOptionPane.ERROR_MESSAGE);
					return;
				}
				try {
					Element eventSetEl = doc.getRootElement().element(IM_EventSetCalculation.XML_METADATA_NAME);
					IM_EventSetCalculation calc = IM_EventSetCalculation.fromXMLMetadata(eventSetEl);
					
					// sites
					this.sitesPanel.clear();
					ArrayList<Location> sites = calc.getSites();
					ArrayList<ArrayList<SiteDataValue<?>>> sitesData = calc.getSitesData();
					for (int i=0; i<calc.getSites().size(); i++) {
						this.sitesPanel.addSite(sites.get(i), sitesData.get(i));
					}
					
					// erf
					ArrayList<EqkRupForecastAPI> erfs = calc.getErfs();
					if (erfs.size() > 0) {
						EqkRupForecastAPI erf = erfs.get(0);
						this.erfGuiBean.getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(erf.getName());
						EqkRupForecastBaseAPI myERF = erfGuiBean.getSelectedERF_Instance();
						for (ParameterAPI myParam : myERF.getAdjustableParameterList()) {
							for (ParameterAPI xmlParam : erf.getAdjustableParameterList()) {
								if (myParam.getName().equals(xmlParam.getName())) {
									myParam.setValue(xmlParam.getValue());
								}
							}
						}
						TimeSpan timeSpan = erf.getTimeSpan();
						myERF.setTimeSpan(timeSpan);
						erfGuiBean.getERFParameterListEditor().refreshParamEditor();
						erfGuiBean.getSelectedERFTimespanGuiBean().setTimeSpan(timeSpan);
					}
					
					// imrs
					ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs = calc.getIMRs();
					imrChooser.setForIMRS(imrs);
					
					// imts
					imtChooser.setIMRs(imrChooser.getSelectedIMRs());
					imtChooser.setIMTs(calc.getIMTs());
					
					// site data providers
					OrderedSiteDataProviderList provs = calc.getProviders();
					OrderedSiteDataProviderList defaultProvs = dataBean.getProviderList();
					defaultProvs.mergeWith(provs);
					if (provs != null)
						dataBean.setProviderList(defaultProvs);
				} catch (Exception e1) {
					// TODO Auto-generated catch block
					e1.printStackTrace();
				}
			}
		}
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		IM_EventSetGUI gui = new IM_EventSetGUI();
		gui.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		gui.setSize(900, 700);
		
		gui.setVisible(true);
	}

}
