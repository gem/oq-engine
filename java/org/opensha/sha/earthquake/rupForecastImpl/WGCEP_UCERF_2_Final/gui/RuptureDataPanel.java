/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.gui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.text.DecimalFormat;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.table.AbstractTableModel;

import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.A_Faults.A_FaultSegmentedSourceGenerator;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.UCERF1MfdReader;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * Show the rupture data in the window
 * 
 * @author vipingupta
 *
 */
public class RuptureDataPanel extends JPanel implements ActionListener, GraphWindowAPI {
	private RuptureTableModel rupTableModel = new RuptureTableModel();
	private JButton mfdButton = new JButton("Plot Selected Fault MFDs");
	private JButton magAreaPlotButton = new JButton("Mag Area Plot (Color coded by Relative Rup Rates)");
	private JButton magAreaPlotButton2 = new JButton("Mag Area Plot (Color coded by Fault names)");
	private JButton aveSlipDataButton= new JButton("Show Ave Slip Data");
	private JButton rupRatesButton= new JButton("Plot A-Priori and final rates");
	private JButton rupRatesRatioButton = new JButton("(FinalRate-A_PrioriRate)/Max(A_PrioriRate,FinalRate)");
	
	private A_FaultSegmentedSourceGenerator source;
	//	Filled Circles for rupture from each plot
	public final PlotCurveCharacterstics PLOT_CHAR1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.BLUE, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.RED, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.GREEN, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR4 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.BLACK, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR5 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.MAGENTA, 2);	
	protected final PlotCurveCharacterstics PLOT_CHAR6 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.ORANGE, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR7 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.PINK, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR8 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.YELLOW, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR9 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.CYAN, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR10 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.DARK_GRAY, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR11 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.LIGHT_GRAY, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR12 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      Color.GRAY, 2);
	
	// solid lines for Mag Area rel
	public final PlotCurveCharacterstics MAG_AREA_PLOT_CHAR1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.BLUE, 2);
	protected final PlotCurveCharacterstics MAG_AREA_PLOT_CHAR2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.RED, 2);
	protected final PlotCurveCharacterstics MAG_AREA_PLOT_CHAR3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.GREEN, 2);
	protected final PlotCurveCharacterstics MAG_AREA_PLOT_CHAR4 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.BLACK, 2);
	protected final PlotCurveCharacterstics MAG_AREA_PLOT_CHAR5 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.MAGENTA, 2);	
	protected final PlotCurveCharacterstics MAG_AREA_PLOT_CHAR6 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.ORANGE, 2);
	protected final PlotCurveCharacterstics MAG_AREA_PLOT_CHAR7 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.PINK, 2);

	private final static double MIN_AREA = 100; // sq km
	private final static double MAX_AREA = 10000; // sq km
	
	private ArrayList plottingFeatures;
	private ArrayList magAreaFuncs;
	private ArrayList aFaultSegmentedSourceList;
	private ArrayList magAreaRels;
	
	
	public RuptureDataPanel() {
		this.setLayout(new GridBagLayout());
		JTable table = new JTable(this.rupTableModel);
		table.setColumnSelectionAllowed(true);
		add(new JScrollPane(table),new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		add(mfdButton,new GridBagConstraints( 0, 1, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		add(magAreaPlotButton,new GridBagConstraints( 0, 2, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		add(magAreaPlotButton2,new GridBagConstraints( 0, 3, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		add(aveSlipDataButton,new GridBagConstraints( 0, 4, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		add(rupRatesButton,new GridBagConstraints( 0, 5, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		add(rupRatesRatioButton,new GridBagConstraints( 0, 6, 1, 1, 1.0, 0.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		aveSlipDataButton.setToolTipText("Show Average Slip for each segment for each rupture");
		mfdButton.addActionListener(this);
		magAreaPlotButton.addActionListener(this);
		magAreaPlotButton2.addActionListener(this);
		aveSlipDataButton.addActionListener(this);
		rupRatesButton.addActionListener(this);
		rupRatesRatioButton.addActionListener(this);
	}
	
	/**
	 * Set source list and mag area relationships for Mag Area plot
	 * 
	 * @param aFaultSegmentedSourceList
	 */
	public void setSourcesForMagAreaPlot(ArrayList aFaultSegmentedSourceList, ArrayList magAreaRels) {
		this.aFaultSegmentedSourceList = aFaultSegmentedSourceList;
		this.magAreaRels = magAreaRels;
	}
	
	/**
	 * Color coding by rup rates
	 *
	 */
	private void createFuncListColorCodingByRupRates() {
		plottingFeatures = new ArrayList();
		magAreaFuncs = new ArrayList();
		magAreaPlotButton.setEnabled(true);
		int numFaults = aFaultSegmentedSourceList.size();
		int numMagAreaRels = magAreaRels.size();
		double area;
		// create function list for all faults
		int numRateDiscretizations=30;
		for(int i=0; i<numRateDiscretizations; ++i) {
			ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
			magAreaFuncs.add(func);
		}
		
		int index;
		double maxRelativeRate = 1.0;
		double minRelativeRate = 0.001;
		double deltaRate = (Math.log10(maxRelativeRate)-Math.log10(minRelativeRate))/numRateDiscretizations;
		//System.out.println("DeltaRate="+deltaRate);
		for(int i=0; i<numFaults; ++i) {
			A_FaultSegmentedSourceGenerator aFaultSegmentedSource = (A_FaultSegmentedSourceGenerator) aFaultSegmentedSourceList.get(i);
			ArbitrarilyDiscretizedFunc func;
			double[] relativeRupRates = getRelativeRupRates(aFaultSegmentedSource);
			for(int j=0; j<aFaultSegmentedSource.getNumRupSources(); ++j) {
				area = aFaultSegmentedSource.getRupArea(j)/1e6; // area to sq km
				
				//if(relativeRupRates[j]<minRelativeRate) System.out.println(" Low relative rate for:"+ 
					//	aFaultSegmentedSource.getFaultSegmentData().getFaultName()+":"+relativeRupRates[j]);
				/*System.out.println(" rate for:"+ 
						aFaultSegmentedSource.getFaultSegmentData().getFaultName()+":"+j+"="+relativeRupRates[j]+","+
						Math.log10(relativeRupRates[j]));*/
				//System.out.println(relativeRupRates[j]+","+Math.log10(relativeRupRates[j])+","+index);
				if(relativeRupRates[j]<=minRelativeRate) index = numRateDiscretizations-1;
				else index = numRateDiscretizations -  (int) ((Math.log10(relativeRupRates[j]) - Math.log10(minRelativeRate))/deltaRate);
				//System.out.println(aFaultSegmentedSource.getFaultSegmentData().getFaultName()+":"+relativeRupRates[j]+","+Math.log10(relativeRupRates[j])+","+index);
				func = (ArbitrarilyDiscretizedFunc)magAreaFuncs.get(index);
				if(func.getXIndex(area)!=-1) System.out.println("RuptureDataPanel::setSourcesForMagAreaPlot()::**********Duplicate Area********");
				func.set(area, aFaultSegmentedSource.getRupMeanMag(j));
			}
			//func.setName(aFaultSegmentedSource.getFaultSegmentData().getFaultName());
		}
		
		
		// remove functions which have 0 elements
		for(int i=0; i<magAreaFuncs.size(); ++i) {
			ArbitrarilyDiscretizedFunc func = (ArbitrarilyDiscretizedFunc)magAreaFuncs.get(i);
			if(func.getNum()==0) {
				magAreaFuncs.remove(i);
				--i;
			}
		}
		
		// add colors
		int minColor = 0;
		int maxColor=255;
		int deltaColor =   (maxColor-minColor)/magAreaFuncs.size();
		int colorVal;
		for(int i=0; i<magAreaFuncs.size(); ++i) {
			colorVal = minColor+i*deltaColor;
			plottingFeatures.add(new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
		      new Color(colorVal, colorVal, colorVal), 2));
			//System.out.println("Number of points in function "+i+"="+((ArbitrarilyDiscretizedFunc)magAreaFuncs.get(i)).getNum());
		}
		
		
		// create function list for mag area relationships
		double min = Math.log10(MIN_AREA);
		double max = Math.log10(MAX_AREA);
		int numPoints =101;
		double delta = (max-min)/(numPoints-1);
		//System.out.println(min+","+max+","+delta);
		for(int i=0; i<numMagAreaRels; ++i) {
			MagAreaRelationship magAreaRel = (MagAreaRelationship)magAreaRels.get(i);
			ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
			for(int j=0; j<=numPoints; ++j) {
				area = Math.pow(10, min+j*delta);
				func.set(area, magAreaRel.getMedianMag(area));
			}
			func.setName(magAreaRel.getName());
			magAreaFuncs.add(func);
		}
		// plotting features for mag area rels
		if(numMagAreaRels>0) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR1);
		if(numMagAreaRels>1) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR2);
		if(numMagAreaRels>2) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR3);
		if(numMagAreaRels>3) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR4);
		if(numMagAreaRels>4) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR5);
		if(numMagAreaRels>5) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR6);
		if(numMagAreaRels>6) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR7);
	}
	
	
	/**
	 * Color Coding by fault names
	 * 
	 * @param aFaultSegmentedSourceList
	 */
	public void setColorCodingbyFaultNames() {
		plottingFeatures = new ArrayList();
		magAreaFuncs = new ArrayList();
		int numFaults = aFaultSegmentedSourceList.size();
		int numMagAreaRels = magAreaRels.size();
		double area;
		// create function list for all faults
		for(int i=0; i<numFaults; ++i) {
			A_FaultSegmentedSourceGenerator aFaultSegmentedSource = (A_FaultSegmentedSourceGenerator) aFaultSegmentedSourceList.get(i);
			ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
			for(int j=0; j<aFaultSegmentedSource.getNumRupSources(); ++j) {
				area = aFaultSegmentedSource.getRupArea(j)/1e6; // area to sq km
				if(func.getXIndex(area)!=-1) System.out.println("RuptureDataPanel::setSourcesForMagAreaPlot()::**********Duplicate Area********");
				func.set(area, aFaultSegmentedSource.getRupMeanMag(j));
			}
			func.setName(aFaultSegmentedSource.getFaultSegmentData().getFaultName());
			magAreaFuncs.add(func);
		}
		
		// create function list for mag area relationships
		double min = Math.log10(MIN_AREA);
		double max = Math.log10(MAX_AREA);
		int numPoints =101;
		double delta = (max-min)/(numPoints-1);
		//System.out.println(min+","+max+","+delta);
		for(int i=0; i<numMagAreaRels; ++i) {
			MagAreaRelationship magAreaRel = (MagAreaRelationship)magAreaRels.get(i);
			ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
			for(int j=0; j<=numPoints; ++j) {
				area = Math.pow(10, min+j*delta);
				func.set(area, magAreaRel.getMedianMag(area));
			}
			func.setName(magAreaRel.getName());
			magAreaFuncs.add(func);
		}
		
		
		// plotting features for rupture area and mag
		if(numFaults>0) plottingFeatures.add(this.PLOT_CHAR1);
		if(numFaults>1) plottingFeatures.add(this.PLOT_CHAR2);
		if(numFaults>2) plottingFeatures.add(this.PLOT_CHAR3);
		if(numFaults>3) plottingFeatures.add(this.PLOT_CHAR4);
		if(numFaults>4) plottingFeatures.add(this.PLOT_CHAR5);
		if(numFaults>5) plottingFeatures.add(this.PLOT_CHAR6);
		if(numFaults>6) plottingFeatures.add(this.PLOT_CHAR7);
		if(numFaults>7) plottingFeatures.add(this.PLOT_CHAR8);
		if(numFaults>8) plottingFeatures.add(this.PLOT_CHAR9);
		if(numFaults>9) plottingFeatures.add(this.PLOT_CHAR10);
		if(numFaults>10) plottingFeatures.add(this.PLOT_CHAR11);
		if(numFaults>11) plottingFeatures.add(this.PLOT_CHAR12);
		
		// plotting features for mag area rels
		if(numMagAreaRels>0) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR1);
		if(numMagAreaRels>1) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR2);
		if(numMagAreaRels>2) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR3);
		if(numMagAreaRels>3) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR4);
		if(numMagAreaRels>4) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR5);
		if(numMagAreaRels>5) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR6);
		if(numMagAreaRels>6) plottingFeatures.add(this.MAG_AREA_PLOT_CHAR7);
	}
	
	/**
	 * Get relative rates of the ruptures
	 * 
	 * @param aFaultSegmentedSource
	 * @return
	 */
	public double[] getRelativeRupRates(A_FaultSegmentedSourceGenerator aFaultSegmentedSource) {
		double[] relativeRates = new double[aFaultSegmentedSource.getNumRupSources()];
		double maxRate=0.0;
		for(int i=0; i< aFaultSegmentedSource.getNumRupSources(); ++i) {
			if(maxRate<aFaultSegmentedSource.getRupRate(i))
				maxRate = aFaultSegmentedSource.getRupRate(i);
		}
		for(int i=0; i< aFaultSegmentedSource.getNumRupSources(); ++i) {
			relativeRates[i]=aFaultSegmentedSource.getRupRate(i)/maxRate;
		}
		return relativeRates;
	}
	
	
	
	public void actionPerformed(ActionEvent event) {
		Object eventSource = event.getSource();
		if(eventSource == mfdButton) { // MFD for selected A Fault
			ArrayList funcs = new ArrayList();
			IncrementalMagFreqDist magFreqDist = source.getTotalRupMFD();
			EvenlyDiscretizedFunc cumRateDist = magFreqDist.getCumRateDistWithOffset();
			cumRateDist.setInfo("Cumulative Mag Freq Dist");
			funcs.add(magFreqDist);
			funcs.add(cumRateDist);
			ArbitrarilyDiscretizedFunc ucerf1Rate = UCERF1MfdReader.getUCERF1IncrementalMFD(source.getFaultSegmentData().getFaultName());
			ArbitrarilyDiscretizedFunc ucerf1CumRate = UCERF1MfdReader.getUCERF1CumMFD(source.getFaultSegmentData().getFaultName());
			funcs.add(ucerf1Rate);
			funcs.add(ucerf1CumRate);
			new GraphWindowAPI_Impl(funcs, "Mag", "Rate", "Mag Rate");
		} else if(eventSource == this.magAreaPlotButton) {
			this.createFuncListColorCodingByRupRates();
			GraphWindow graphWindow= new GraphWindow(this);
		    graphWindow.setPlotLabel("Mag Area Plot");
		    graphWindow.plotGraphUsingPlotPreferences();
		    graphWindow.setLocationRelativeTo(this);
		    graphWindow.setVisible(true);;
		}else if(eventSource == this.magAreaPlotButton2) {
			this.setColorCodingbyFaultNames();
			GraphWindow graphWindow= new GraphWindow(this);
		    graphWindow.setPlotLabel("Mag Area Plot");
		    graphWindow.plotGraphUsingPlotPreferences();
		    graphWindow.setLocationRelativeTo(this);
		    graphWindow.setVisible(true);;
		} else if (eventSource == this.aveSlipDataButton) {
			RupAveSlipTableModel tableModel = new RupAveSlipTableModel(this.source.getSegSlipInRupMatrix());
			JTable table = new JTable(tableModel);
			JFrame frame = new JFrame(source.getFaultSegmentData().getFaultName());
			frame.getContentPane().setLayout(new BorderLayout());
			frame.getContentPane().add(new JScrollPane(table), BorderLayout.CENTER);
			frame.pack();
			frame.setVisible(true);
		} else if(eventSource == rupRatesButton) { // plot A-Priori rupture rates vs Final Rup Rates
			ArrayList<ArbitrarilyDiscretizedFunc> plottingFuncList = new ArrayList<ArbitrarilyDiscretizedFunc>();
			ArbitrarilyDiscretizedFunc aPrioriRatesFunc = new ArbitrarilyDiscretizedFunc();
			aPrioriRatesFunc.setName("A-Priori Rupture Rates");
			ArbitrarilyDiscretizedFunc finalRupRatesFunc = new ArbitrarilyDiscretizedFunc();
			finalRupRatesFunc.setName("Final Rupture Rates");
			int numRups = source.getNumRupSources();
			for(int i=0; i<numRups; ++i) {
				aPrioriRatesFunc.set((double)i+1, source.getAPrioriRupRate(i));
				finalRupRatesFunc.set((double)i+1, source.getRupRate(i));
			}
			plottingFuncList.add(aPrioriRatesFunc);
			plottingFuncList.add(finalRupRatesFunc);
			GraphWindow graphWindow= new GraphWindow(new CreatePlotFromMagRateFile(plottingFuncList));
			graphWindow.setPlotLabel(source.getFaultSegmentData().getFaultName());
			graphWindow.setXAxisLabel("Rupture Index");
			graphWindow.setYAxisLabel("Rupture Rate");
			graphWindow.plotGraphUsingPlotPreferences();
			graphWindow.setTitle("Rupture Rates");
			graphWindow.setVisible(true);
		} else if(eventSource == this.rupRatesRatioButton) {
			// ratio of final rupture rates to A-Priori rupture rates
			ArrayList<ArbitrarilyDiscretizedFunc> plottingFuncList = new ArrayList<ArbitrarilyDiscretizedFunc>();
			ArbitrarilyDiscretizedFunc ratioFunc = new ArbitrarilyDiscretizedFunc();
			ratioFunc.setName("(FinalRate-A_PrioriRate)/Max(A_PrioriRate,FinalRate)");
			int numRups = source.getNumRupSources();
			for(int i=0; i<numRups; ++i) {
				ratioFunc.set((double)i+1, source.getRupRateResid(i));
			}
			plottingFuncList.add(ratioFunc);
			CreatePlotFromMagRateFile plot = new CreatePlotFromMagRateFile(plottingFuncList);
			plot.setYLog(false);
			GraphWindow graphWindow= new GraphWindow(plot);
			graphWindow.setPlotLabel("(FinalRate-A_PrioriRate)/Max(A_PrioriRate,FinalRate)");
			graphWindow.plotGraphUsingPlotPreferences();
			graphWindow.setTitle(source.getFaultSegmentData().getFaultName());
			graphWindow.setVisible(true);
		}
	}
	

	
	
	/**
	 * Set the source to update the rupture info
	 * 
	 * @param aFaultSegmentedSource
	 */
	public void setSource(A_FaultSegmentedSourceGenerator aFaultSegmentedSource) {
		this.source = aFaultSegmentedSource;
		if(source!=null) mfdButton.setEnabled(true);
		else mfdButton.setEnabled(false);
		rupTableModel.setFaultSegmentedSource(aFaultSegmentedSource);
		rupTableModel.fireTableDataChanged();
	}
	
	
	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getCurveFunctionList()
	 */
	public ArrayList getCurveFunctionList() {
		return this.magAreaFuncs;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXLog()
	 */
	public boolean getXLog() {
		return true;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYLog()
	 */
	public boolean getYLog() {
		return false;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXAxisLabel()
	 */
	public String getXAxisLabel() {
		return "Area";
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYAxisLabel()
	 */
	public String getYAxisLabel() {
		return "Mag";
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getPlottingFeatures()
	 */
	public ArrayList getPlottingFeatures() {
		return this.plottingFeatures;
	}
	
	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#isCustomAxis()
	 */
	public boolean isCustomAxis() {
		return true;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinX()
	 */
	public double getMinX() {
		return 40.0;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxX()
	 */
	public double getMaxX() {
		return 10000;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinY()
	 */
	public double getMinY() {
		return 5.5;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxY()
	 */
	public double getMaxY() {
		return 8.5;
	}
}


/**
* Rupture Ave Slip Table Model
* 
* @author vipingupta
*
*/
class RupAveSlipTableModel extends AbstractTableModel {
	//	 column names
	private double [][] segSlipInRupMatrix;
	
	/**
	 * default constructor
	 *
	 */
	public RupAveSlipTableModel(double [][]segSlipInRupMatrix) {
		this.segSlipInRupMatrix = segSlipInRupMatrix;
	}
	
	/**
	 * Get number of columns
	 */
	public int getColumnCount() {
		return segSlipInRupMatrix[0].length+1;
	}
	
	
	/**
	 * Get column name
	 */
	public String getColumnName(int index) {
		if(index==0) return "";
		else return "Rup "+index;
	}
	
	/*
	 * Get number of rows
	 * (non-Javadoc)
	 * @see javax.swing.table.TableModel#getRowCount()
	 */
	public int getRowCount() {
		return segSlipInRupMatrix.length;
	}
	
	
	/**
	 * 
	 */
	public Object getValueAt (int rowIndex, int columnIndex) {
		if(columnIndex==0) { // Show the segment index in the first column
			return "Seg "+(rowIndex+1);
		} else { // show the slip rates
			return (float)segSlipInRupMatrix[rowIndex][columnIndex-1];
		}
	}
}


/**
* Rupture Table Model
* 
* @author vipingupta
*
*/
class RuptureTableModel extends AbstractTableModel {
//	 column names
	public final static String[] columnNames = { "Rup Index", "Area (sq km)", "Mean Mag", 
		"Final Rate", "A Priori Rate", "Moment Rate", "Rup Prob", "Rup Gain", "Short Name", "Long Name"};
	private final static DecimalFormat AREA_LENGTH_FORMAT = new DecimalFormat("0.#");
	private final static DecimalFormat MAG_FORMAT = new DecimalFormat("0.00");
	private final static DecimalFormat RATE_FORMAT = new DecimalFormat("0.000E0");
	private final static DecimalFormat MOMENT_FORMAT = new DecimalFormat("0.000E0");
	private A_FaultSegmentedSourceGenerator aFaultSegmentedSource;
	
	/**
	 * default constructor
	 *
	 */
	public RuptureTableModel() {
		this(null);
	}
	
	/**
	 *  Preferred Fault section data
	 *  
	 * @param faultSectionsPrefDataList  ArrayList of PrefFaultSedctionData
	 */
	public RuptureTableModel(A_FaultSegmentedSourceGenerator aFaultSegmentedSource) {
		setFaultSegmentedSource(aFaultSegmentedSource);
	}
	
	/**
	 * Set the segmented fault data
	 * @param segFaultData
	 */
	public void setFaultSegmentedSource(A_FaultSegmentedSourceGenerator aFaultSegmentedSource) {
		this.aFaultSegmentedSource =   aFaultSegmentedSource;
	}
	
	/**
	 * Get number of columns
	 */
	public int getColumnCount() {
		return columnNames.length;
	}
	
	
	/**
	 * Get column name
	 */
	public String getColumnName(int index) {
		return columnNames[index];
	}
	
	/*
	 * Get number of rows
	 * (non-Javadoc)
	 * @see javax.swing.table.TableModel#getRowCount()
	 */
	public int getRowCount() {
		if(aFaultSegmentedSource==null) return 0;
		return (aFaultSegmentedSource.getNumRupSources()+1); 
	}
	
	
	/**
	 * 
	 */
	public Object getValueAt (int rowIndex, int columnIndex) {
			
		if(aFaultSegmentedSource==null) return "";
		if(rowIndex == aFaultSegmentedSource.getNumRupSources()) return getTotal(columnIndex);
		switch(columnIndex) {
			case 0:
				return ""+(rowIndex+1);
			case 1: 
				return AREA_LENGTH_FORMAT.format(aFaultSegmentedSource.getRupArea(rowIndex)/1e6);
			case 2:
				return MAG_FORMAT.format(aFaultSegmentedSource.getRupMeanMag(rowIndex));
			case 3:
				return RATE_FORMAT.format(aFaultSegmentedSource.getRupRate(rowIndex));
			case 4:
				return RATE_FORMAT.format(aFaultSegmentedSource.getAPrioriRupRate(rowIndex));
			case 5:
				return MOMENT_FORMAT.format(aFaultSegmentedSource.getRupMoRate(rowIndex));
			case 6:
				return MOMENT_FORMAT.format(aFaultSegmentedSource.getRupSourceProb(rowIndex));
			case 7:
				return MAG_FORMAT.format(aFaultSegmentedSource.getRupSourcProbGain(rowIndex));
			case 8:
				return aFaultSegmentedSource.getShortRupName(rowIndex);
			case 9:
				return aFaultSegmentedSource.getLongRupName(rowIndex);
		}
		return "";
	}
	
	/**
	 * 
	 * @param colIndex
	 * @return
	 */
	private String getTotal(int colIndex) {
		double totalRate = 0.0;
		switch(colIndex) {
			case 0:
				return "Total";
			case 3:
				for(int i=0; i<aFaultSegmentedSource.getNumRupSources(); ++i)
					totalRate+=aFaultSegmentedSource.getRupRate(i);
				return RATE_FORMAT.format(totalRate);
			case 4:
				for(int i=0; i<aFaultSegmentedSource.getNumRupSources(); ++i)
					totalRate+=aFaultSegmentedSource.getAPrioriRupRate(i);
				return RATE_FORMAT.format(totalRate);
			case 5:
				if(aFaultSegmentedSource!=null)
					return MOMENT_FORMAT.format(aFaultSegmentedSource.getTotalMoRateFromRups());
		
		}
		return "";
	}
}

