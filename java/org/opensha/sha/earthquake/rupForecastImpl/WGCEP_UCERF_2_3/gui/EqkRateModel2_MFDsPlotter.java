/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.gui;

import java.awt.Color;
import java.util.ArrayList;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * This class is used for plotting the MFDs for the EqkRateModel2.1
 * @author vipingupta
 *
 */
public class EqkRateModel2_MFDsPlotter implements GraphWindowAPI {
	private final static String X_AXIS_LABEL = "Magnitude";
	private final static String Y_AXIS_LABEL = "Rate";
	
	private ArrayList funcs;
	
	private final PlotCurveCharacterstics PLOT_CHAR1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.BLUE, 2);
	private final PlotCurveCharacterstics PLOT_CHAR2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.LIGHT_GRAY, 2);
	private final PlotCurveCharacterstics PLOT_CHAR3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.GREEN, 2);
	private final PlotCurveCharacterstics PLOT_CHAR4 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.MAGENTA, 2);
	private final PlotCurveCharacterstics PLOT_CHAR5 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.PINK, 2);
	private final PlotCurveCharacterstics PLOT_CHAR6 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.BLACK, 5);
	private final PlotCurveCharacterstics PLOT_CHAR7 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.RED, 2);
	private final PlotCurveCharacterstics PLOT_CHAR8 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.CROSS_SYMBOLS,
		      Color.RED, 5);
	private final PlotCurveCharacterstics PLOT_CHAR9 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.ORANGE, 2);
	
	private final static String A_FAULTS_METADATA = "Type A-Faults Total Mag Freq Dist";
	private final static String B_FAULTS_CHAR_METADATA = "Type B-Faults Total Char Mag Freq Dist";
	private final static String B_FAULTS_GR_METADATA = "Type B-Faults Total GR Mag Freq Dist";
	private final static String NON_CA_B_FAULTS_METADATA = "Non-CA Type B-Faults Total Mag Freq Dist";
	private final static String BACKGROUND_METADATA = "BackGround Total  Mag Freq Dist";
	private final static String C_ZONES_METADATA = "C Zone Total  Mag Freq Dist";
	private final static String TOTAL_METADATA = "Total  Mag Freq Dist";
	
	public EqkRateModel2_MFDsPlotter(UCERF2 ucerf2, boolean isCumMFD) {
		if(isCumMFD) createCumFunctionList(ucerf2);
		else createIncrFunctionList(ucerf2);
	}
	
	/**
	 * Create Cum Function List
	 *
	 */
	private void createCumFunctionList(UCERF2 ucerf2) {
	
		funcs = new ArrayList();
		
		// Type A faults cum Dist
		EvenlyDiscretizedFunc cumDist = ucerf2.getTotal_A_FaultsMFD().getCumRateDistWithOffset();
		cumDist.setInfo(A_FAULTS_METADATA);
		funcs.add(cumDist);
		 // Type B faults Char cum Dist
		cumDist = ucerf2.getTotal_B_FaultsCharMFD().getCumRateDistWithOffset();
		cumDist.setInfo(B_FAULTS_CHAR_METADATA);
		funcs.add(cumDist);
		//	Type B faults GR cum Dist
		cumDist = ucerf2.getTotal_B_FaultsGR_MFD().getCumRateDistWithOffset();
		cumDist.setInfo(B_FAULTS_GR_METADATA);
		funcs.add(cumDist);
		// Non-CA Type B faults
		cumDist = ucerf2.getTotal_NonCA_B_FaultsMFD().getCumRateDistWithOffset();
		cumDist.setInfo(NON_CA_B_FAULTS_METADATA);
		funcs.add(cumDist);
		//	Background cum Dist
		cumDist = ucerf2.getTotal_BackgroundMFD().getCumRateDistWithOffset();
		cumDist.setInfo(BACKGROUND_METADATA);
		funcs.add(cumDist);
		//	C zone cum Dist
		cumDist = ucerf2.getTotal_C_ZoneMFD().getCumRateDistWithOffset();
		cumDist.setInfo(C_ZONES_METADATA);
		funcs.add(cumDist);
		//	Total cum Dist
		cumDist = ucerf2.getTotalMFD().getCumRateDistWithOffset();
		cumDist.setInfo(TOTAL_METADATA);
		funcs.add(cumDist);
		
		
		boolean includeAfterShocks = ucerf2.areAfterShocksIncluded();
		
		ArrayList<EvenlyDiscretizedFunc> obsCumMFD = ucerf2.getObsCumMFD(includeAfterShocks);
		
		// historical best fit cum dist
		//funcs.add(eqkRateModel2ERF.getObsBestFitCumMFD(includeAfterShocks));
		funcs.add(obsCumMFD.get(0));
		// historical cum dist
		funcs.addAll(obsCumMFD);
		
		
	}
	
	
	/**
	 * Create Incr Function List
	 *
	 */
	private void createIncrFunctionList(UCERF2 eqkRateModelERF) {
	
		funcs = new ArrayList();
		
		// Type A faults cum Dist
		IncrementalMagFreqDist incrMFD = eqkRateModelERF.getTotal_A_FaultsMFD();
		incrMFD.setInfo(A_FAULTS_METADATA);
		funcs.add(incrMFD);
		 // Type B faults Char cum Dist
		incrMFD = eqkRateModelERF.getTotal_B_FaultsCharMFD();
		incrMFD.setInfo(B_FAULTS_CHAR_METADATA);
		funcs.add(incrMFD);
		//	Type B faults GR cum Dist
		incrMFD = eqkRateModelERF.getTotal_B_FaultsGR_MFD();
		incrMFD.setInfo(B_FAULTS_GR_METADATA);
		funcs.add(incrMFD);
		// Non-CA Type B faults
		incrMFD = eqkRateModelERF.getTotal_NonCA_B_FaultsMFD();
		incrMFD.setInfo(NON_CA_B_FAULTS_METADATA);
		funcs.add(incrMFD);	
		//	Background cum Dist
		incrMFD = eqkRateModelERF.getTotal_BackgroundMFD();
		incrMFD.setInfo(BACKGROUND_METADATA);
		funcs.add(incrMFD);
		//	C zone cum Dist
		incrMFD = eqkRateModelERF.getTotal_C_ZoneMFD();
		incrMFD.setInfo(C_ZONES_METADATA);
		funcs.add(incrMFD);
		//	Total cum Dist
		incrMFD = eqkRateModelERF.getTotalMFD();
		incrMFD.setInfo(TOTAL_METADATA);
		funcs.add(incrMFD);
		
		boolean includeAfterShocks = eqkRateModelERF.areAfterShocksIncluded();
		ArrayList<ArbitrarilyDiscretizedFunc> obsIncrMFDList = eqkRateModelERF.getObsIncrMFD(includeAfterShocks);
		
		// historical best fit cum dist
		//funcs.add(eqkRateModel2ERF.getObsBestFitCumMFD(includeAfterShocks));
		funcs.add(obsIncrMFDList.get(0));
		// historical cum dist
		funcs.addAll(obsIncrMFDList);
		
	}


	
	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getCurveFunctionList()
	 */
	public ArrayList getCurveFunctionList() {
		return funcs;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXLog()
	 */
	public boolean getXLog() {
		return false;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYLog()
	 */
	public boolean getYLog() {
		return true;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXAxisLabel()
	 */
	public String getXAxisLabel() {
		return X_AXIS_LABEL;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYAxisLabel()
	 */
	public String getYAxisLabel() {
		return Y_AXIS_LABEL;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getPlottingFeatures()
	 */
	public ArrayList getPlottingFeatures() {
		 ArrayList list = new ArrayList();
		 list.add(this.PLOT_CHAR1);
		 list.add(this.PLOT_CHAR2);
		 list.add(this.PLOT_CHAR3);
		 list.add(this.PLOT_CHAR9);
		 list.add(this.PLOT_CHAR4);
		 list.add(this.PLOT_CHAR5);
		 list.add(this.PLOT_CHAR6);
		 if(funcs.size()>7) list.add(this.PLOT_CHAR7);
		 if(funcs.size()>8)	 list.add(this.PLOT_CHAR8);
		 if(funcs.size()>9)	 list.add(this.PLOT_CHAR8);
		 if(funcs.size()>10)	 list.add(this.PLOT_CHAR8);
		 return list;
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
		return 5.0;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxX()
	 */
	public double getMaxX() {
		return 9.255;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinY()
	 */
	public double getMinY() {
		return 1e-4;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxY()
	 */
	public double getMaxY() {
		return 10;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}
}
