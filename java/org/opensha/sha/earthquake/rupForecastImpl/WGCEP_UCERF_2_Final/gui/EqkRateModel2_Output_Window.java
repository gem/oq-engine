/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.gui;

import java.awt.Container;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTabbedPane;
import javax.swing.JTable;
import javax.swing.JTextArea;

import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UnsegmentedSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.A_Faults.A_FaultSegmentedSourceGenerator;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * This shows the output for the EqkRateModel_ERF_GUI
 * 
 * @author vipingupta
 *
 */
public class EqkRateModel2_Output_Window extends JFrame implements ActionListener, ParameterChangeListener{
	private final static String CUM_PLOT_LABEL = "Cumulative  Rates";
	private final static String INCR_PLOT_LABEL = "Incremental  Rates";
	private JButton plotCumMFDsButton = new JButton("Plot Cum Mag Freq Dist");
	private JButton plotIncrMFDsButton = new JButton("Plot Incr Mag Freq Dist");
	private JButton modSlipRateButton = new JButton("Plot Histogram of Normalized Slip-Rate Residuals ((Final_SR-Orig_SR)/SR_Sigma)");
	private JButton dataERButton = new JButton("Plot Histogram of Normalized Segment Event-Rate Residuals - (Final_ER-Data_ER)/ER_Sigma");
	private JButton predERButton = new JButton("Plot the ratio of Final to Pred Segment Event Rate");
	private JButton rupRatesRatioButton = new JButton("Plot Histogram of (FinalRate-A_PrioriRate)/Max(A_PrioriRate,FinalRate)");
	private JButton aFaultsSegDataButton = new JButton("Table of all A-Faults Segment Data");
	private JButton aFaultsRupDataButton = new JButton("Table of all A-Faults Rupture Data");
	private JButton probContrButton = new JButton("Table of all Probability Contributions");
	private UCERF2 ucerf2;
	//private ArbitrarilyDiscretizedFunc historicalMFD;
	private JTabbedPane tabbedPane = new JTabbedPane();
	private HashMap aFaultSourceMap;
	private SegmentDataPanel segmentDataPanel;
	private RuptureDataPanel ruptureDataPanel;
	private final static int W = 800;
	private final static int H = 800;
	private StringParameter aFaultParam;
	private final static String A_FAULT_PARAM_NAME = "A Fault";
	private boolean isUnsegmented;
	private ArrayList<Double> normModlSlipRateRatioList;
	private ArrayList<Double> normDataER_RatioList;
	private ArrayList<Double> predER_RatioList;
	private ArrayList<Double> normRupRatesRatioList;
	private  boolean isAseisReducesArea;
	private JTable aFaultsSegData, aFaultsRupData, probContrTable;
	private EqkRateModel2_MFDsPlotter cumMfdsPlotter;
	private EqkRateModel2_MFDsPlotter incrMfdsPlotter;
	
	/**
	 * 
	 * @param ucerf2
	 * @param historicalMFD
	 */
	public EqkRateModel2_Output_Window(UCERF2 ucerf2) {
		this.ucerf2 = ucerf2;
		//this.historicalMFD = historicalMFD;
		createGUI();
		this.pack();
		setSize(W,H);
		this.show();
	}
	
	
	private void createGUI() {
//		isAseisReducesArea = ((Boolean)this.eqkRateModelERF.getParameter(EqkRateModel2_ERF.ASEIS_INTER_PARAM_NAME).getValue()).booleanValue();
		isAseisReducesArea = true;	// hard coded according to final definition
		JPanel aFaultSummaryPanel = getA_FaultSummaryGUI();
		tabbedPane.addTab("Total Model Summary", getTotalModelSummaryGUI());
		tabbedPane.addTab("A Fault Summary", aFaultSummaryPanel);
		tabbedPane.addTab("B Fault Summary", getB_FaultSummaryGUI());
		tabbedPane.addTab("C Zones Summary", getC_ZonesSummaryGUI());
		if(!this.isUnsegmented) {
			calcNormModSlipRateResids();
			calcNormDataER_Resids();
			calcPredERRatio();
			calcNormRupRatesDiff();
			calcA_FaultRupData();
			calcA_FaultSegData();
			probContrTable = new JTable(new ProbsTableModel(this.ucerf2)); 
		} else {
			this.modSlipRateButton.setVisible(false);
			this.predERButton.setVisible(false);
			this.dataERButton.setVisible(false);
			rupRatesRatioButton.setVisible(false);
			this.aFaultsRupDataButton.setVisible(false);
			this.aFaultsSegDataButton.setVisible(false);
		}
		Container container = this.getContentPane();
		container.setLayout(new GridBagLayout());
		container.add(tabbedPane,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
	}
	
	
	/**
	 * Get Total Model Summary
	 * 
	 * @return
	 */
	private JPanel getTotalModelSummaryGUI() {
		JPanel panel = new JPanel(new GridBagLayout());
		cumMfdsPlotter = new EqkRateModel2_MFDsPlotter(this.ucerf2, true);
		incrMfdsPlotter = new EqkRateModel2_MFDsPlotter(this.ucerf2, false);
		JTextArea textArea = new JTextArea();
		textArea.setText("");
		textArea.setLineWrap(true);
		textArea.setWrapStyleWord(true);
		
		if(ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).getValue().equals(UCERF2.PROB_MODEL_EMPIRICAL)) {
		textArea.append("Important Note: The influence of the Empirical Model is not included " +
				"in the magnitude-frequency distributions plotted here.  However, the " +
				"influence is included in the rupture and segment probabilities and gains " +
				"shown for the Type A faults. The influence is also included in Total Prob "+
				"for B-Faults\n\n");
		}
		
		IncrementalMagFreqDist totalMFD = this.ucerf2.getTotalMFD();
		textArea.append("Total Rate (M>=5) = "+(float)totalMFD.getTotalIncrRate()+"\n");
		boolean includeAfterShocks = ucerf2.areAfterShocksIncluded();
		textArea.append("Predicted 6.5 rate over observed = "+(totalMFD.getCumRate(6.5+totalMFD.getDelta()/2)/this.ucerf2.getObsCumMFD(includeAfterShocks).get(0).getInterpolatedY(6.5+totalMFD.getDelta()/2))+"\n");
		textArea.append("Total Moment Rate = "+(float)totalMFD.getTotalMomentRate()+"\n");
		
		// Display the general prediction error in case of Segmented A-Faults
		if(!this.isUnsegmented) { // for segmented faults, get the general prediction error
			textArea.append("\nTotal A-Fault Pred Errors:"+"\n");
			textArea.append("\n\tGen Pred Error = "+(float)ucerf2.getGeneralPredErr()+"\n");
			textArea.append("\tSeg Slip Rate Error = "+(float)ucerf2.getModSlipRateError()+"\n");
			textArea.append("\tSeg Event Rate Error = "+(float)ucerf2.getDataER_Err()+"\n");
			textArea.append("\tA-Priori Rup Rate Error = "+(float)ucerf2.getNormalizedA_PrioriRateErr()+"  ");
			textArea.append("(non-normalized = "+(float)ucerf2.getNonNormalizedA_PrioriRateErr()+")\n\n\n");
		}
		
		
		textArea.append("\tRate (M>=5)\tRate (M>=6.5)\tMoment Rate\n");
		textArea.append("------------------------------------------------\n");
		textArea.append("A Faults\t"+(float)this.ucerf2.getTotal_A_FaultsMFD().getTotalIncrRate()+"\t"+
				(float)this.ucerf2.getTotal_A_FaultsMFD().getCumRate(6.5+totalMFD.getDelta()/2)+"\t"+
				(float)this.ucerf2.getTotal_A_FaultsMFD().getTotalMomentRate()+"\n");
		textArea.append("B Char\t"+(float)this.ucerf2.getTotal_B_FaultsCharMFD().getTotalIncrRate()+"\t"+
				(float)this.ucerf2.getTotal_B_FaultsCharMFD().getCumRate(6.5+totalMFD.getDelta()/2)+"\t"+
				(float)this.ucerf2.getTotal_B_FaultsCharMFD().getTotalMomentRate()+"\n");
		textArea.append("B GR\t"+(float)this.ucerf2.getTotal_B_FaultsGR_MFD().getTotalIncrRate()+"\t"+
				(float)this.ucerf2.getTotal_B_FaultsGR_MFD().getCumRate(6.5+totalMFD.getDelta()/2)+"\t"+
				(float)this.ucerf2.getTotal_B_FaultsGR_MFD().getTotalMomentRate()+"\n");
		textArea.append("B (Non-CA)\t"+(float)this.ucerf2.getTotal_NonCA_B_FaultsMFD().getTotalIncrRate()+"\t"+
				(float)this.ucerf2.getTotal_NonCA_B_FaultsMFD().getCumRate(6.5+totalMFD.getDelta()/2)+"\t"+
				(float)this.ucerf2.getTotal_NonCA_B_FaultsMFD().getTotalMomentRate()+"\n");
		textArea.append("C Zone\t"+(float)this.ucerf2.getTotal_C_ZoneMFD().getTotalIncrRate()+"\t"+
				(float)this.ucerf2.getTotal_C_ZoneMFD().getCumRate(6.5+totalMFD.getDelta()/2)+"\t"+
				(float)this.ucerf2.getTotal_C_ZoneMFD().getTotalMomentRate()+"\n");
		textArea.append("Background\t"+(float)this.ucerf2.getTotal_BackgroundMFD().getTotalIncrRate()+"\t"+
				(float)this.ucerf2.getTotal_BackgroundMFD().getCumRate(6.5+totalMFD.getDelta()/2)+"\t"+
				(float)this.ucerf2.getTotal_BackgroundMFD().getTotalMomentRate()+"\n");
		textArea.append("Total\t"+(float)totalMFD.getTotalIncrRate()+"\t"+
				(float)totalMFD.getCumRate(6.5+totalMFD.getDelta()/2)+"\t"+
				(float)totalMFD.getTotalMomentRate()+"\n\n");
		textArea.append("Adjustable Params Metadata:\n");
		textArea.append(ucerf2.getAdjustableParameterList().getParameterListMetadataString("\n"));
		textArea.append("\n"+ucerf2.getTimeSpan().getAdjustableParams().getParameterListMetadataString("\n"));
		panel.add(new JScrollPane(textArea),new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		panel.add(plotCumMFDsButton,new GridBagConstraints( 0, 1, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		panel.add(plotIncrMFDsButton,new GridBagConstraints( 0, 2, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		panel.add(this.modSlipRateButton,new GridBagConstraints( 0, 3, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		panel.add(predERButton,new GridBagConstraints( 0, 4, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		panel.add(dataERButton,new GridBagConstraints( 0, 5, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		panel.add(rupRatesRatioButton,new GridBagConstraints( 0, 6, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		panel.add(aFaultsRupDataButton,new GridBagConstraints( 0, 7, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		panel.add(aFaultsSegDataButton,new GridBagConstraints( 0, 8, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		panel.add(probContrButton,new GridBagConstraints( 0, 9, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		

		textArea.setEditable(false);
		plotCumMFDsButton.addActionListener(this);
		plotIncrMFDsButton.addActionListener(this);
		this.modSlipRateButton.addActionListener(this);
		this.predERButton.addActionListener(this);
		this.dataERButton.addActionListener(this);
		rupRatesRatioButton.addActionListener(this);
		this.aFaultsRupDataButton.addActionListener(this);
		this.aFaultsSegDataButton.addActionListener(this);
		this.probContrButton.addActionListener(this);
		return panel;
	}
	
	/**
	 * Calculate A Fault Segment Data
	 *
	 */
	private void calcA_FaultSegData() {
		ArrayList<String> faultNames  = aFaultParam.getAllowedStrings();
		int totalRows=faultNames.size();
		for(int srcIndex=0; srcIndex<faultNames.size(); ++srcIndex) {
			A_FaultSegmentedSourceGenerator source =  (A_FaultSegmentedSourceGenerator) aFaultSourceMap.get(faultNames.get(srcIndex));
			totalRows+=source.getFaultSegmentData().getNumSegments()+1;// include totals
		} 
		int totalCols = SegmentDataTableModel.columnNames.length;
		Object[][] rowData = new Object[totalRows][totalCols];
		int rowIndex=0;
		SegmentDataTableModel segTableModel = new SegmentDataTableModel();
		for(int srcIndex=0; srcIndex<faultNames.size(); ++srcIndex) {
			A_FaultSegmentedSourceGenerator source =  (A_FaultSegmentedSourceGenerator) aFaultSourceMap.get(faultNames.get(srcIndex));
			FaultSegmentData faultSegmentData = source.getFaultSegmentData();
			rowData[rowIndex][0]=faultSegmentData.getFaultName();
			for(int colIndex=1; colIndex<totalCols;++colIndex) rowData[rowIndex][colIndex]="";
			++rowIndex;
			segTableModel.setFaultData(faultSegmentData, source, null);
			for(int segIndex=0; segIndex<=faultSegmentData.getNumSegments(); ++segIndex, ++rowIndex) {
				for(int colIndex=0; colIndex<totalCols;++colIndex)
					rowData[rowIndex][colIndex]=segTableModel.getValueAt(segIndex, colIndex);
			}
		} 
		 aFaultsSegData = new JTable(rowData, SegmentDataTableModel.columnNames);
		 aFaultsSegData.setColumnSelectionAllowed(true);
	}
	
	/**
	 * Calculate Rupture Data forall A-Faults
	 *
	 */
	private void calcA_FaultRupData() {
		ArrayList<String> faultNames  = aFaultParam.getAllowedStrings();
		int totalRows=faultNames.size();
		for(int srcIndex=0; srcIndex<faultNames.size(); ++srcIndex) {
			A_FaultSegmentedSourceGenerator source =  (A_FaultSegmentedSourceGenerator) aFaultSourceMap.get(faultNames.get(srcIndex));
			totalRows+=source.getNumRupSources()+1; // also include totals
		} 
		int totalCols = RuptureTableModel.columnNames.length;
		Object[][] rowData = new Object[totalRows][totalCols];
		int rowIndex=0;
		RuptureTableModel rupTableModel = new RuptureTableModel();
		for(int srcIndex=0; srcIndex<faultNames.size(); ++srcIndex) {
			A_FaultSegmentedSourceGenerator source =  (A_FaultSegmentedSourceGenerator) aFaultSourceMap.get(faultNames.get(srcIndex));
			FaultSegmentData faultSegmentData = source.getFaultSegmentData();
			rowData[rowIndex][0]=faultSegmentData.getFaultName();
			for(int colIndex=1; colIndex<totalCols;++colIndex) rowData[rowIndex][colIndex]="";
			++rowIndex;
			rupTableModel.setFaultSegmentedSource(source);
			for(int rupIndex=0; rupIndex<=source.getNumRupSources(); ++rupIndex, ++rowIndex) {
				for(int colIndex=0; colIndex<totalCols;++colIndex)
					rowData[rowIndex][colIndex]=rupTableModel.getValueAt(rupIndex, colIndex);
			}
		} 
		 aFaultsRupData = new JTable(rowData, RuptureTableModel.columnNames);
		 aFaultsRupData.setColumnSelectionAllowed(true);
	}
	
	/**
	 * A Fault summary GUI
	 * 
	 * @return
	 */
	private JPanel getA_FaultSummaryGUI() {
		JPanel panel = new JPanel(new GridBagLayout());
		aFaultSourceMap = new HashMap();
		ArrayList aFaultSourceGenerators = this.ucerf2.get_A_FaultSourceGenerators();
		
		// whether this is segmented or unsegmented
		String rupModel = (String)ucerf2.getParameter(UCERF2.RUP_MODEL_TYPE_NAME).getValue();
		if(rupModel.equalsIgnoreCase(UCERF2.UNSEGMENTED_A_FAULT_MODEL)) {
			this.isUnsegmented = true;
			this.predERButton.setVisible(false);
			this.dataERButton.setVisible(false);
		}
		else {
			this.isUnsegmented = false;
			this.predERButton.setVisible(true);
			this.dataERButton.setVisible(true);
		}
		
		if(aFaultSourceGenerators==null) return panel;
		segmentDataPanel = new SegmentDataPanel();
		ArrayList faultNames = new ArrayList();
		for(int i=0; i<aFaultSourceGenerators.size(); ++i) {
			Object source = aFaultSourceGenerators.get(i);
			FaultSegmentData faultSegmentData = getFaultSegmentData(source);
			faultNames.add(faultSegmentData.getFaultName());
			aFaultSourceMap.put(faultSegmentData.getFaultName(), source);
		}
		this.aFaultParam = new StringParameter(A_FAULT_PARAM_NAME, faultNames, (String)faultNames.get(0));
		aFaultParam.addParameterChangeListener(this);
		ConstrainedStringParameterEditor paramEditor = new ConstrainedStringParameterEditor(aFaultParam);
		panel.add(paramEditor,new GridBagConstraints( 0, 0, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		JTabbedPane segmentInfoTabbedPane = new JTabbedPane();
		segmentInfoTabbedPane.addTab("Segment Info", segmentDataPanel);
		if(this.isUnsegmented) {
			B_FaultDataPanel bFaultDataPanel = new B_FaultDataPanel();
			bFaultDataPanel.setB_FaultSources(aFaultSourceGenerators);
			segmentInfoTabbedPane.addTab("Rupture Info", bFaultDataPanel);
		} else {
			ruptureDataPanel = new RuptureDataPanel();
			segmentInfoTabbedPane.addTab("Rupture Info", ruptureDataPanel);
			ruptureDataPanel.setSourcesForMagAreaPlot(aFaultSourceGenerators, this.ucerf2.getMagAreaRelationships());
		}
		panel.add(segmentInfoTabbedPane,new GridBagConstraints( 0, 1, 1, 1, 1.0, 1.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		
		updateA_FaultTableData();
		return panel;
	}
	
	/**
	 * Get fault segment data based on A fault source type (whether it is segmented or unsegmented)
	 * @param source
	 * @return
	 */
	private FaultSegmentData getFaultSegmentData(Object source) {
		if(this.isUnsegmented) return ((UnsegmentedSource)source).getFaultSegmentData();
		else return ((A_FaultSegmentedSourceGenerator)source).getFaultSegmentData();
	}
	
	/**
	 * B faults sources
	 * @return
	 */
	private JPanel getB_FaultSummaryGUI() {
		JPanel panel = new JPanel(new GridBagLayout());
		ArrayList bFaultSources = this.ucerf2.get_B_FaultSources();
		B_FaultDataPanel bFaultDataPanel = new B_FaultDataPanel();
		bFaultDataPanel.setB_FaultSources(bFaultSources);
		panel.add(bFaultDataPanel,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		return panel;
	}
	
	
	/**
	 * C Zones
	 * @return
	 */
	private JPanel getC_ZonesSummaryGUI() {
		JPanel panel = new JPanel(new GridBagLayout());
		ArrayList<IncrementalMagFreqDist> cZonesMFDs = this.ucerf2.getC_ZoneMFD_List();
		C_ZoneDataPanel cZonesDataPanel = new C_ZoneDataPanel();
		cZonesDataPanel.setC_ZonesMFD_List(cZonesMFDs);
		panel.add(cZonesDataPanel,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		return panel;
	}
	
	/**
	 * 
	 * @param event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		updateA_FaultTableData();
	}
	
	
	/**
	 * update the A fault table data based on the selected A fault
	 *
	 */
	private void updateA_FaultTableData() {
		String selectedFault = (String)aFaultParam.getValue();
		Object source =   aFaultSourceMap.get(selectedFault);
		if(!this.isUnsegmented)  {
			ruptureDataPanel.setSource((A_FaultSegmentedSourceGenerator)source);
			this.segmentDataPanel.setFaultSegmentData((A_FaultSegmentedSourceGenerator)source, null, isAseisReducesArea, this.ucerf2.getMagAreaRelationships());
		} else {
			segmentDataPanel.setEventRatesList(this.ucerf2.getA_FaultsFetcher().getEventRatesList());
			this.segmentDataPanel.setFaultSegmentData(null, (UnsegmentedSource)source, isAseisReducesArea, this.ucerf2.getMagAreaRelationships());
		}
	} 


	/**
	 * When Calc button is clicked
	 * @param event
	 */
	public void actionPerformed(ActionEvent event) {
		Object src = event.getSource();
		if(src == this.plotCumMFDsButton) {
			GraphWindow graphWindow= new GraphWindow(cumMfdsPlotter);
			graphWindow.setPlotLabel(CUM_PLOT_LABEL);
			graphWindow.plotGraphUsingPlotPreferences();
			graphWindow.setVisible(true);
		} else if(src == plotIncrMFDsButton) {
			GraphWindow graphWindow= new GraphWindow(incrMfdsPlotter);
			graphWindow.setPlotLabel(INCR_PLOT_LABEL);
			graphWindow.plotGraphUsingPlotPreferences();
			graphWindow.setVisible(true);
		}else if(src == this.modSlipRateButton) { // ratio of modified slip rates
			String plotLabel = "Normalized Segment Slip-Rate Residuals\n((Final_SR-Orig_SR)/SR_Sigma)";
			showHistograms(normModlSlipRateRatioList, plotLabel, "Normalized Segment Slip-Rate Residuals");
		}else if(src == this.dataERButton) { // ratio of final Event rate and data Event rate
			String plotLabel = "Normalized Segment Event-Rate Residuals\n((Final_ER-Data_ER)/ER_Sigma)";
			showHistograms(normDataER_RatioList, plotLabel, "Normalized Segment Event-Rate Residuals");
		}else if(src == this.predERButton) { // ratio of final event rate and pred Event rate
			String plotLabel = "Final vs Pred Segment Event Rate Ratios";
			showHistograms(predER_RatioList, plotLabel, "Ratio of final Event Ratio to Pred Event Ratio");
		} else if(src == this.rupRatesRatioButton) { // ratio of final rates to A-Priori Rates
			String plotLabel = "Histogram of (FinalRate-A_PrioriRate)/Max(A_PrioriRate,FinalRate)";
			showHistograms(normRupRatesRatioList, plotLabel, plotLabel);
		} else if(src==this.aFaultsSegDataButton) {
			JFrame frame = new JFrame();
			frame.getContentPane().setLayout(new  GridBagLayout());
			frame.getContentPane().add(new JScrollPane(this.aFaultsSegData), new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
		      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
			frame.pack();
			frame.show();
		} else if(src == this.aFaultsRupDataButton) {
			JFrame frame = new JFrame();
			frame.getContentPane().setLayout(new  GridBagLayout());
			frame.getContentPane().add(new JScrollPane(this.aFaultsRupData), new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
		      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
			frame.pack();
			frame.show();
		}else if(src == this.probContrButton) {
			
			JFrame frame = new JFrame();
			frame.getContentPane().setLayout(new  GridBagLayout());
			frame.getContentPane().add(new JScrollPane(probContrTable), new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
		      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
			frame.pack();
			frame.show();
		}
	}

	/**
	 * Plot Histogram of (FinalRate-A_PrioriRate)/A_PrioriRate
	 *
	 */
	private void calcNormRupRatesDiff() {
		ArrayList<A_FaultSegmentedSourceGenerator> sourceGeneratorList = this.ucerf2.get_A_FaultSourceGenerators();
		normRupRatesRatioList = new ArrayList<Double>();
		// iterate over all sources
		for(int i=0; i<sourceGeneratorList.size(); ++i) {
			A_FaultSegmentedSourceGenerator source = sourceGeneratorList.get(i);
			int numRuptures = source.getNumRupSources();
			// iterate over all ruptures
			for(int rupIndex = 0; rupIndex<numRuptures; ++rupIndex) {
				normRupRatesRatioList.add(source.getRupRateResid(rupIndex));
			}
		}
	}
	

	
	/**
	 * Plot Normalized Segment Slip-Rate Residuals (where orig slip-rate and stddev are reduces by the fraction of moment rate removed)
	 *
	 */
	private void calcNormModSlipRateResids() {
		ArrayList<A_FaultSegmentedSourceGenerator> sourceGeneratorList = ucerf2.get_A_FaultSourceGenerators();
		normModlSlipRateRatioList = new ArrayList<Double>();
		// iterate over all sources
		for(int i=0; i<sourceGeneratorList.size(); ++i) {
			A_FaultSegmentedSourceGenerator source = sourceGeneratorList.get(i);
			double normModResids[] = source.getNormModSlipRateResids();
			for(int segIndex = 0; segIndex<normModResids.length; ++segIndex) normModlSlipRateRatioList.add(new Double(normModResids[segIndex]));
		}
	}
	
	/**
	 * Plot Normalized Event-Rate Residuals
	 *
	 */
	private void calcNormDataER_Resids() {
		ArrayList<A_FaultSegmentedSourceGenerator> sourceGeneratorList = ucerf2.get_A_FaultSourceGenerators();
		normDataER_RatioList = new ArrayList<Double>();
		// iterate over all sources
		for(int i=0; i<sourceGeneratorList.size(); ++i) {
			A_FaultSegmentedSourceGenerator source = sourceGeneratorList.get(i);
			double normDataER_Resids[] = source.getNormDataER_Resids();
			for(int segIndex = 0; segIndex<normDataER_Resids.length; ++segIndex) 
				if(!Double.isNaN(normDataER_Resids[segIndex])) normDataER_RatioList.add(new Double(normDataER_Resids[segIndex]));
		}
	}
	
	/**
	 * Plot the ratio of Event Rates
	 *
	 */
	private void calcPredERRatio() {
		ArrayList<A_FaultSegmentedSourceGenerator> sourceGeneratorList = this.ucerf2.get_A_FaultSourceGenerators();
		predER_RatioList = new ArrayList<Double>();
		// iterate over all sources
		for(int i=0; i<sourceGeneratorList.size(); ++i) {
			A_FaultSegmentedSourceGenerator source = sourceGeneratorList.get(i);
			int numSegments = source.getFaultSegmentData().getNumSegments();
			// iterate over all segments
			for(int segIndex = 0; segIndex<numSegments; ++segIndex) 
				predER_RatioList.add(source.getFinalSegmentRate(segIndex)/source.getSegRateFromAprioriRates(segIndex));
		}
	}

	/**
	 * Show histograms
	 * @param func
	 * @param plotLabel
	 */
	private void showHistograms(ArrayList<Double> ratioList, String plotLabel, String funcName) {
		double min = Math.floor(Collections.min(ratioList));
		double max = Math.ceil(Collections.max(ratioList));
		double delta = 0.2;
		EvenlyDiscretizedFunc func = new EvenlyDiscretizedFunc(min, (int)Math.round((max-min)/delta)+1, delta);
		func.setTolerance(func.getDelta());
		int xIndex;
		for(int i=0; i<ratioList.size(); ++i) {
			xIndex = func.getXIndex(ratioList.get(i));
			func.add(xIndex, 1.0);
		}
		ArrayList funcs = new ArrayList();
		funcs.add(func);
		String yAxisLabel = "Count";
		GraphWindow graphWindow= new GraphWindow(new CreateHistogramsFromSegSlipRateFile(funcs, plotLabel, yAxisLabel));
		graphWindow.setPlotLabel(plotLabel);
		graphWindow.plotGraphUsingPlotPreferences();
		graphWindow.setVisible(true);
	}

}
