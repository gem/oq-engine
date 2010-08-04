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

package org.opensha.sha.cybershake.gui;

import java.awt.BorderLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.util.ArrayList;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSeparator;
import javax.swing.JTable;
import javax.swing.ListSelectionModel;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;

import org.dom4j.DocumentException;
import org.opensha.sha.cybershake.db.CybershakeHazardCurveRecord;
import org.opensha.sha.cybershake.db.CybershakeRun;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.HazardCurve2DB;
import org.opensha.sha.cybershake.gui.util.AttenRelSaver;
import org.opensha.sha.cybershake.gui.util.ERFSaver;
import org.opensha.sha.cybershake.plot.HazardCurvePlotCharacteristics;
import org.opensha.sha.cybershake.plot.HazardCurvePlotter;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.gui.infoTools.GraphPanel;
import org.opensha.sha.imr.AttenuationRelationship;


public class HazardCurveGUI extends JFrame implements ActionListener, ListSelectionListener {
	
	DBAccess db;
	
	HazardCurve2DB curve2db;
	
	JPanel mainPanel = new JPanel(new BorderLayout());
	
	JPanel bottomPanel = new JPanel();
	
	JButton deleteButton = new JButton("Delete Curve(s)");
	JButton reloadButton = new JButton("Reload Curves");
	JButton plotButton = new JButton("Plot Curve");
	
	JCheckBox plotComparisonsCheck = new JCheckBox("Plot Comparison Curves", false);
	
	JComboBox plotStyleBox = new JComboBox();
	
	private static final String PLOT_STYLE_ROB = "Rob-Style Plot";
	private static final String PLOT_STYLE_TOM = "Tom-Style Plot";
	
	HazardCurveTableModel model;
	JTable table;
	
	boolean readOnly = false;
	
	private HazardCurvePlotter plotter = null;
	
	private static final String ERF_COMPARISON_FILE = "org/opensha/sha/cybershake/conf/MeanUCERF.xml";
	private static final String CB_2008_ATTEN_REL_FILE = "org/opensha/sha/cybershake/conf/cb2008.xml";
	private static final String BA_2008_ATTEN_REL_FILE = "org/opensha/sha/cybershake/conf/ba2008.xml";
	private static final String AS_2008_ATTEN_REL_FILE = "org/opensha/sha/cybershake/conf/as2008.xml";
	private static final String CY_2008_ATTEN_REL_FILE = "org/opensha/sha/cybershake/conf/cy2008.xml";
	
	private EqkRupForecast erf = null;
	private AttenuationRelationship cb2008 = null;
	private AttenuationRelationship ba2008 = null;
	private AttenuationRelationship as2008 = null;
	private AttenuationRelationship cy2008 = null;

	public HazardCurveGUI(DBAccess db) {
		super("Hazard Curves");
		
		this.db = db;
		this.readOnly = db.isReadOnly();
		curve2db = new HazardCurve2DB(db);
		
		model = new HazardCurveTableModel(db);
		
		table = new JTable(model);
		
		JScrollPane scrollpane = new JScrollPane(table);
		
		bottomPanel.setLayout(new BoxLayout(bottomPanel, BoxLayout.X_AXIS));
		
		table.getSelectionModel().addListSelectionListener(this);
		
		deleteButton.addActionListener(this);
		deleteButton.setEnabled(false);
		
		reloadButton.addActionListener(this);
		
		plotButton.addActionListener(this);
		plotButton.setEnabled(false);
		plotComparisonsCheck.setEnabled(false);
		
		plotStyleBox.setEnabled(false);
		plotStyleBox.addItem(PLOT_STYLE_ROB);
		plotStyleBox.addItem(PLOT_STYLE_TOM);
		
		bottomPanel.add(reloadButton);
		bottomPanel.add(new JSeparator());
		bottomPanel.add(plotComparisonsCheck);
		bottomPanel.add(new JSeparator());
		bottomPanel.add(plotStyleBox);
		bottomPanel.add(new JSeparator());
		bottomPanel.add(plotButton);
		bottomPanel.add(new JSeparator());
		bottomPanel.add(deleteButton);
		
		mainPanel.add(scrollpane, BorderLayout.CENTER);
		mainPanel.add(bottomPanel, BorderLayout.SOUTH);
		
		this.setContentPane(mainPanel);
		
		this.setSize(900, 600);
		
		this.setLocationRelativeTo(null);
		
		this.setDefaultCloseOperation(HIDE_ON_CLOSE);
	}
	
	public static void main(String args[]) throws IOException {
		HazardCurveGUI gui = new HazardCurveGUI(Cybershake_OpenSHA_DBApplication.getAuthenticatedDBAccess(true));
		
		gui.setVisible(true);
		gui.setDefaultCloseOperation(EXIT_ON_CLOSE);
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == reloadButton) {
			this.model.reloadCurves();
		} else if (e.getSource() == deleteButton) {
			ListSelectionModel lsm = table.getSelectionModel();
			
			ArrayList<Integer> rows = new ArrayList<Integer>();
			
			for (int i=lsm.getMinSelectionIndex(); i<=lsm.getMaxSelectionIndex(); i++) {
				if (lsm.isSelectedIndex(i)) {
					rows.add(i);
				}
			}
			
			for (int row : rows) {
				CybershakeHazardCurveRecord curve = model.getCurveAtRow(row);
				System.out.println("Deleting curve " + curve.getCurveID());
				
				boolean success = this.curve2db.deleteHazardCurve(curve.getCurveID());
				if (!success)
					System.err.println("Error deleting curve " + curve.getCurveID());
			}
			model.reloadCurves();
		} else if (e.getSource() == plotButton) {
			ListSelectionModel lsm = table.getSelectionModel();
			
			int row = lsm.getMinSelectionIndex();
			CybershakeHazardCurveRecord curve = model.getCurveAtRow(row);
			
			this.plotCurve(curve);
		}
	}

	public void valueChanged(ListSelectionEvent e) {
		// if it's in the middle of a change, ignore
		if (e.getValueIsAdjusting())
			return;
		
		ListSelectionModel lsm = table.getSelectionModel();
		
		if (lsm.isSelectionEmpty()) {
			this.setPlottingElementsEnabled(false);
			deleteButton.setEnabled(false);
		} else {
			this.setPlottingElementsEnabled(lsm.getMinSelectionIndex() == lsm.getMaxSelectionIndex());
			deleteButton.setEnabled(!readOnly);
		}
	}
	
	private void setPlottingElementsEnabled(boolean enabled) {
		plotButton.setEnabled(enabled);
		plotComparisonsCheck.setEnabled(enabled);
		plotStyleBox.setEnabled(enabled);
	}
	
	private void plotCurve(CybershakeHazardCurveRecord curve) {
		CybershakeRun run = model.getRunForCurve(curve);
		HazardCurvePlotter plotter = this.getPlotter();
		
		plotter.setMaxSourceSiteDistance(run.getSiteID());
//		plotter.set
		
		plotter.plotCurve(curve.getCurveID(), run);
		
		GraphPanel gp = plotter.getGraphPanel();
		
		JFrame graphWindow = new JFrame("CyberShake Hazard Curve");
		graphWindow.setContentPane(gp);
		graphWindow.setDefaultCloseOperation(DISPOSE_ON_CLOSE);
		
		graphWindow.setSize(500, 700);
		graphWindow.setLocationRelativeTo(this);
		
		graphWindow.setVisible(true);
	}
	
	private HazardCurvePlotter getPlotter() {
		if (plotter == null) {
			plotter = new HazardCurvePlotter(db);
		}
		if (this.plotComparisonsCheck.isSelected()) {
			try {
				if (erf == null) {
					erf = ERFSaver.LOAD_ERF_FROM_FILE(this.getClass().getResource("/" + ERF_COMPARISON_FILE));
				}
				plotter.setERFComparison(erf);
				plotter.clearAttenuationRelationshipComparisions();
				if (cb2008 == null) {
					cb2008 = AttenRelSaver.LOAD_ATTEN_REL_FROM_FILE(this.getClass().getResource("/" + CB_2008_ATTEN_REL_FILE));
				}
				plotter.addAttenuationRelationshipComparision(cb2008);
				if (ba2008 == null) {
					ba2008 = AttenRelSaver.LOAD_ATTEN_REL_FROM_FILE(this.getClass().getResource("/" + BA_2008_ATTEN_REL_FILE));
				}
				plotter.addAttenuationRelationshipComparision(ba2008);
				if (as2008 == null) {
					as2008 = AttenRelSaver.LOAD_ATTEN_REL_FROM_FILE(this.getClass().getResource("/" + AS_2008_ATTEN_REL_FILE));
				}
				plotter.addAttenuationRelationshipComparision(as2008);
				if (cy2008 == null) {
					cy2008 = AttenRelSaver.LOAD_ATTEN_REL_FROM_FILE(this.getClass().getResource("/" + CY_2008_ATTEN_REL_FILE));
				}
				plotter.addAttenuationRelationshipComparision(cy2008);
			} catch (DocumentException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			} catch (InvocationTargetException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			} catch (MalformedURLException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		} else {
			plotter.setERFComparison(null);
			plotter.clearAttenuationRelationshipComparisions();
		}
		if (this.plotStyleBox.getSelectedItem() == PLOT_STYLE_ROB) {
			plotter.setPlottingCharactersistics(HazardCurvePlotCharacteristics.createRobPlotChars());
		} else if (this.plotStyleBox.getSelectedItem() == PLOT_STYLE_TOM) {
			plotter.setPlottingCharactersistics(HazardCurvePlotCharacteristics.createTomPlotChars());
		}
		return plotter;
	}

}
