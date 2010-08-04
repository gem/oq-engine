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

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.gui;


import java.awt.Container;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JScrollPane;

import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis.LogicTreeMFDsPlotter;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis.ReportBulgeFigures;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis.UCERF1ComparisonPlotter;
import org.opensha.sha.gui.beans.ERF_GuiBean;


/**
 * This class allows the user the user to adjust various parameters in EqkRateModel2_ERF and
 * the resulting Mag freq Distributions
 * @author vipingupta
 *
 */
public class UCERF2_GUI extends JFrame implements ActionListener{
	
	//private UCERF2 ucerf2= new UCERF2(); // erf to get the adjustable params
	private ParameterListEditor editor; // editor
	private final static String TITLE = "Eqk Rate Model2 Params";
	private JButton calcButton = new JButton("Calculate");
	private final static int W = 300;
	private final static int H = 800;
	private  JMenuBar menuBar = new JMenuBar();
	private JMenu analysisMenu = new JMenu("Further Analysis");
	private JMenuItem genReportFigMenu = new JMenuItem("Generate MFD Figs for Report");
	private JMenuItem sjSsafReportFigMenu = new JMenuItem("Generate SJF and SSAF MFD Figs for Report");
	private JMenuItem bulgeAnalysisMenu = new JMenuItem("Make Bulge Analysis Plots");
	private JMenuItem logicTreeCumMFDplotMenu = new JMenuItem("Logic tree Cumulative plots");
	private JMenuItem logicTreeIncrMFDplotMenu = new JMenuItem("Logic tree Incremental plots");
	private ERF_GuiBean erfGuiBean;
	
	public final static String WGCEP_UCERF_2_3_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2";
	
	private String dirName=null; 
	private JScrollPane scrollPane = new JScrollPane();
	
	public static void main(String[] args) {
		new UCERF2_GUI();
	}
	
	public UCERF2_GUI() {
		
		/*// listen to all parameters
		ParameterList paramList = ucerf2.getAdjustableParameterList();
		Iterator it = paramList.getParametersIterator();
		while(it.hasNext()) {
			ParameterAPI param = (ParameterAPI)it.next();
			param.addParameterChangeListener(this);
		}*/
		ArrayList classNames = new ArrayList();
		classNames.add(WGCEP_UCERF_2_3_CLASS_NAME);
		try {
			erfGuiBean  =new ERF_GuiBean(classNames);
		}catch(Exception e) {
			e.printStackTrace();
		}
		createGUI();
		calcButton.addActionListener(this);
		pack();
		Container container = this.getContentPane();
		container.add(this.erfGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		container.validate();
		container.repaint();
		setSize(W, H);
		this.setLocationRelativeTo(null);
		this.setDefaultCloseOperation(EXIT_ON_CLOSE);
		show();
	}
	
	/*public void parameterChange(ParameterChangeEvent event) {
		addParameterListEditor();
	}
	
	private void addParameterListEditor() {
		int val = scrollPane.getVerticalScrollBar().getValue();
		editor = new ParameterListEditor(ucerf2.getAdjustableParameterList());
		editor.setTitle(TITLE);
		scrollPane.setViewportView(editor);
		scrollPane.getVerticalScrollBar().setValue(val);
	}*/
	
	
	/**
	 * Create GUI
	 *
	 */
	private void createGUI() {
		Container container = this.getContentPane();
		container.setLayout(new GridBagLayout());
		//this.addParameterListEditor();
		container.add(this.calcButton,new GridBagConstraints( 0, 1, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		
		 menuBar.add(analysisMenu);
		 analysisMenu.add(genReportFigMenu);
		 analysisMenu.add(sjSsafReportFigMenu);
		 analysisMenu.add(bulgeAnalysisMenu);
		 analysisMenu.add(logicTreeCumMFDplotMenu);
		 analysisMenu.add(logicTreeIncrMFDplotMenu);
		 setJMenuBar(menuBar);	
		 
		 genReportFigMenu.addActionListener(new java.awt.event.ActionListener() {
			 public void actionPerformed(ActionEvent e) {
				 genReportFigMenu_actionPerformed(e);
			 }
		 });
		 sjSsafReportFigMenu.addActionListener(new java.awt.event.ActionListener() {
			 public void actionPerformed(ActionEvent e) {
				 sjSsafReportFigMenu_actionPerformed(e);
			 }
		 });
		 bulgeAnalysisMenu.addActionListener(new java.awt.event.ActionListener() {
			 public void actionPerformed(ActionEvent e) {
				 bulgeAnalysisMenu_actionPerformed(e);
			 }
		 });
		 logicTreeCumMFDplotMenu.addActionListener(new java.awt.event.ActionListener() {
			 public void actionPerformed(ActionEvent e) {
				 logicTreeCumMFDplotMenu_actionPerformed(e);
			 }
		 });
		 logicTreeIncrMFDplotMenu.addActionListener(new java.awt.event.ActionListener() {
			 public void actionPerformed(ActionEvent e) {
				 logicTreeIncrMFDplotMenu_actionPerformed(e);
			 }
		 });
		
	}
	
	/**
	   * Generate Figures for Report
	   * 
	   * @param actionEvent
	   */
	  private void sjSsafReportFigMenu_actionPerformed(ActionEvent actionEvent) {
		  try {
			  UCERF2 ucerf2 = (UCERF2)this.erfGuiBean.getSelectedERF_Instance();
			  UCERF1ComparisonPlotter ucerf1ComparisonPlotter = new UCERF1ComparisonPlotter(ucerf2);
			  //ucerf1ComparisonPlotter.plotA_FaultMFDs_forReport();
			  ucerf1ComparisonPlotter.plot_SJ_SSAF_FaultsDefModels(); 
		  }catch(Exception e) {
			  e.printStackTrace();
		  }
	  }
	
	  /**
	   * Generate Figures for Report
	   * 
	   * @param actionEvent
	   */
	  private void genReportFigMenu_actionPerformed(ActionEvent actionEvent) {
		  //String dirName = getDirectoryName();
		  //if(dirName==null) return;
		  //generateAnalysisFigures(dirName);
		  try {
			  UCERF2 ucerf2 = (UCERF2)this.erfGuiBean.getSelectedERF_Instance();
			  UCERF1ComparisonPlotter ucerf1ComparisonPlotter = new UCERF1ComparisonPlotter(ucerf2);
			  //ucerf1ComparisonPlotter.plotA_FaultMFDs_forReport();
			  ucerf1ComparisonPlotter.plotA_FaultMFDs_forReport("D2.1"); // do for deformation model 2.1
			  ucerf1ComparisonPlotter.plotB_FaultMFDs_forReport();
		  }catch(Exception e) {
			  e.printStackTrace();
		  }
	  }
	  
	  /**
	   * Generate Cumulative MFD Plots for various logic tree branches
	   * 
	   * @param actionEvent
	   */
	  private void logicTreeCumMFDplotMenu_actionPerformed(ActionEvent actionEvent) {
		  LogicTreeMFDsPlotter  logicTreeMFDsPlotter = new LogicTreeMFDsPlotter();
		  logicTreeMFDsPlotter.plotMFDs(null, true);
	  }
	  
	  
	  /**
	   * Generate Incremental MFD Plots for various logic tree branches
	   * 
	   * @param actionEvent
	   */
	  private void logicTreeIncrMFDplotMenu_actionPerformed(ActionEvent actionEvent) {
		  LogicTreeMFDsPlotter  logicTreeMFDsPlotter = new LogicTreeMFDsPlotter();
		  logicTreeMFDsPlotter.plotMFDs(null, false);
	  }
	  
	  /**
	   * Generate Bulge analysis Plots
	   * 
	   * @param actionEvent
	   */
	  private void bulgeAnalysisMenu_actionPerformed(ActionEvent actionEvent) {
		  String dirName = getDirectoryName();
		  if(dirName==null) return;
		  ReportBulgeFigures reportBulgeFigures = new ReportBulgeFigures();
		  reportBulgeFigures.generateAnalysisFigures(dirName);
	  }
	  
	  
	
	 private String getDirectoryName() {
		JFileChooser fileChooser = new JFileChooser();
		fileChooser.setDialogTitle("Choose directory to save files");
		if(dirName!=null) fileChooser.setSelectedFile(new File(dirName));
		fileChooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
	    if (fileChooser.showSaveDialog(this) == JFileChooser.APPROVE_OPTION) { 
	    	dirName = fileChooser.getSelectedFile().getAbsolutePath();
	    } else dirName=null;
		return dirName;
	  }
	  
	
	
	/**
	 * When Calc button is clicked
	 * @param event
	 */
	public void actionPerformed(ActionEvent event) {
		Object source  = event.getSource();
		UCERF2 ucerf2 = null;
		if(source==this.calcButton) {
			//CalcProgressBar progressBar = new CalcProgressBar("Calculating", "Please Wait  (Accessing database takes time) .....");
			//progressBar.setLocationRelativeTo(this);
			try {
				ucerf2 = (UCERF2)this.erfGuiBean.getSelectedERF();
				//ucerf2.updateForecast(); // update forecast
			}catch(Exception e) {
				JOptionPane.showMessageDialog(this, e.getMessage());
				e.printStackTrace();
				return;
			}
			// show the output
			EqkRateModel2_Output_Window outputWindow = new EqkRateModel2_Output_Window(ucerf2);
			outputWindow.setLocationRelativeTo(this);
			//progressBar.showProgress(false);
		} 
	}
}
