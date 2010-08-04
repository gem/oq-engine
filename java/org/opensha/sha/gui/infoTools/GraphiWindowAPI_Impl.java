/**
 * 
 */
package org.opensha.sha.gui.infoTools;

import java.awt.Color;
import java.io.IOException;
import java.util.ArrayList;

import org.jfree.data.Range;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;

/**
 * This class accepts a function list and plots it using Jfreechart
 * 
 * @author vipingupta
 *
 */
public class GraphiWindowAPI_Impl implements GraphWindowAPI {

	private ArrayList funcs;


	private final PlotCurveCharacterstics PLOT_CHAR1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			Color.BLUE, 2);
	private final PlotCurveCharacterstics PLOT_CHAR2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			Color.BLACK, 2);
	private final PlotCurveCharacterstics PLOT_CHAR3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			Color.GREEN, 2);
	private final PlotCurveCharacterstics PLOT_CHAR4 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			Color.MAGENTA, 2);
	private final PlotCurveCharacterstics PLOT_CHAR5 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			Color.PINK, 2);
	private final PlotCurveCharacterstics PLOT_CHAR6 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			Color.LIGHT_GRAY, 5);
	private final PlotCurveCharacterstics PLOT_CHAR7 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			Color.RED, 2);

	private boolean xLog = false, yLog = false;
	private ArrayList<PlotCurveCharacterstics> plotChars;
	private String plotTitle;
	private GraphWindow graphWindow;
	private boolean isCustomAxis = false;

	public GraphiWindowAPI_Impl(ArrayList funcs, String plotTitle) {
		this.funcs = funcs;
		ArrayList<PlotCurveCharacterstics> list = new ArrayList<PlotCurveCharacterstics>();
		list.add(this.PLOT_CHAR1);
		list.add(this.PLOT_CHAR2);
		list.add(this.PLOT_CHAR3);
		list.add(this.PLOT_CHAR4);
		list.add(this.PLOT_CHAR5);
		list.add(this.PLOT_CHAR6);
		list.add(this.PLOT_CHAR7);
		int numChars = list.size();
		plotChars = new ArrayList<PlotCurveCharacterstics>();
		for(int i=0; i<funcs.size(); ++i)
			plotChars.add(list.get(i%numChars));

		graphWindow= new GraphWindow(this);
		graphWindow.setPlotLabel(plotTitle);
		graphWindow.plotGraphUsingPlotPreferences();
		graphWindow.setVisible(true);
	}

	
	public GraphiWindowAPI_Impl(ArrayList funcs, String plotTitle, ArrayList<PlotCurveCharacterstics> plotChars) {
		this.funcs=funcs;
		this.plotChars = plotChars;
		graphWindow= new GraphWindow(this);
		graphWindow.setPlotLabel(plotTitle);
		graphWindow.plotGraphUsingPlotPreferences();
		graphWindow.setVisible(true);
	}

	/**
	 * Plot Graph using preferences
	 *
	 */
	public void refreshPlot() {
		graphWindow.plotGraphUsingPlotPreferences();
	}

	/**
	 * Set plot Title
	 * @param plotTitle
	 */
	public void setPlotTitle(String plotTitle) {
		this.plotTitle = plotTitle;
		graphWindow.setPlotLabel(plotTitle);
	}

	/**
	 * Get plot title
	 * 
	 * @return
	 */
	public String getPlotTitle() {
		return this.plotTitle;
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
	public void setXLog(boolean xLog) {
		this.xLog = xLog;
		graphWindow.setX_Log(xLog);
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYLog()
	 */
	public void setYLog(boolean yLog) {
		this.yLog = yLog;
		graphWindow.setY_Log(yLog);
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXLog()
	 */
	public boolean getXLog() {
		return this.xLog;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYLog()
	 */
	public boolean getYLog() {
		return yLog;
	}

	public void setX_AxisLabel(String xAxisLabel) {
		graphWindow.setXAxisLabel(xAxisLabel);
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXAxisLabel()
	 */
	public String getXAxisLabel() {
		if(graphWindow==null) return "X";
		return graphWindow.getXAxisLabel();
	}

	public void setY_AxisLabel(String yAxisLabel) {
		graphWindow.setYAxisLabel(yAxisLabel);
	}


	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYAxisLabel()
	 */
	public String getYAxisLabel() {
		if(graphWindow==null) return "Y";
		return graphWindow.getYAxisLabel();
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getPlottingFeatures()
	 */
	public ArrayList getPlottingFeatures() {
		return plotChars;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getPlottingFeatures()
	 */
	public void setPlottingFeatures(ArrayList<PlotCurveCharacterstics> curveCharacteristics) {
		plotChars   = curveCharacteristics;
		this.graphWindow.setPlottingFeatures(curveCharacteristics);
	}

	/**
	 * sets the range for X and Y axis
	 * @param xMin : minimum value for X-axis
	 * @param xMax : maximum value for X-axis
	 * @param yMin : minimum value for Y-axis
	 * @param yMax : maximum value for Y-axis
	 *
	 */
	public void setAxisRange(double xMin, double xMax, double yMin, double yMax) {
		this.graphWindow.setAxisRange(xMin, xMax, yMin, yMax);
		isCustomAxis = true;
	}

	/**
	 * sets the range for X axis
	 * @param xMin : minimum value for X-axis
	 * @param xMax : maximum value for X-axis
	 *
	 */
	public void setX_AxisRange(double xMin, double xMax) {
		Range yAxisRange = graphWindow.getY_AxisRange();
		setAxisRange(xMin, xMax, yAxisRange.getLowerBound(), yAxisRange.getUpperBound());
	}
	
	/**
	 * sets the range for  Y axis
	 * @param yMin : minimum value for Y-axis
	 * @param yMax : maximum value for Y-axis
	 *
	 */
	public void setY_AxisRange(double yMin, double yMax) {
		Range xAxisRange = graphWindow.getX_AxisRange();
		setAxisRange(xAxisRange.getLowerBound(), xAxisRange.getUpperBound(), yMin, yMax);
	}
	
	
	/**
	 * Whether this is custom axis
	 */
	public boolean isCustomAxis() {
		return this.isCustomAxis;
	}

	/**
	 * set the auto range for the axis. 
	 */
	public void setAutoRange() {
		this.isCustomAxis = false;
		this.graphWindow.setAutoRange();
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinX()
	 */
	public double getMinX() {
		return graphWindow.getMinX();
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxX()
	 */
	public double getMaxX() {
		return graphWindow.getMaxX();
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinY()
	 */
	public double getMinY() {
		return graphWindow.getMinY();
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxY()
	 */
	public double getMaxY() {
		return graphWindow.getMaxY();
	}

	/**
	 * Set plot label font size
	 * 
	 * @param fontSize
	 */
	public void setPlotLabelFontSize(int fontSize) {
		this.graphWindow.setPlotLabelFontSize(fontSize);
	}



	/**
	 * Set the tick label font size
	 * 
	 * @param fontSize
	 */
	public void setTickLabelFontSize(int fontSize) {
		graphWindow.setTickLabelFontSize(fontSize);
	}
	
	/**
	 * Set the axis label font size
	 * 
	 * @param fontSize
	 */
	public void setAxisAndTickLabelFontSize(int fontSize) {
		graphWindow.setAxisLabelFontSize(fontSize);
		graphWindow.setTickLabelFontSize(fontSize);
	}

	/**
	 *
	 * @returns the tick label font
	 * Default is 10
	 */
	public int getTickLabelFontSize(){
		return this.graphWindow.getTickLabelFontSize();
	}


	/**
	 *
	 * @returns the axis label font size
	 * Default is 12
	 */
	public int getPlotLabelFontSize(){
		return this.graphWindow.getPlotLabelFontSize();
	}



	public static void main(String args[]) {
		ArrayList funcs = new ArrayList();

		ArbitrarilyDiscretizedFunc func  = new ArbitrarilyDiscretizedFunc();
		func.set(2.0, 3.0);
		func.set(0.5, 3.5);
		func.set(6.0, 1.0);
		funcs.add(func);

		func  = new ArbitrarilyDiscretizedFunc();
		func.set(1.0, 6);
		func.set(10.0, 7);
		func.set(2.0, 2);
		funcs.add(func);

		GraphiWindowAPI_Impl graphWindowImpl = new GraphiWindowAPI_Impl(funcs, "Test");
		//graphWindowImpl.setXLog(true);
		//graphWindowImpl.setYLog(true);
		graphWindowImpl.setPlotTitle("Test Title");
		graphWindowImpl.setX_AxisRange(0, 5);
		graphWindowImpl.setAutoRange();
		PlotCurveCharacterstics PLOT_CHAR5 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
				Color.PINK, 2);
		PlotCurveCharacterstics PLOT_CHAR6 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
				Color.LIGHT_GRAY, 5);
		ArrayList<PlotCurveCharacterstics> list = new ArrayList<PlotCurveCharacterstics>();
		list.add(PLOT_CHAR5);
		list.add(PLOT_CHAR6);
		graphWindowImpl.setPlottingFeatures(list);
	}
	

	public void saveAsPDF(String fileName) throws IOException {
		graphWindow.saveAsPDF(fileName);
	}

	public void saveAsPNG(String fileName) throws IOException {
		graphWindow.saveAsPNG(fileName);
	}


}
