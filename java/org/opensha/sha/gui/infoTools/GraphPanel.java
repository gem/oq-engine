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

package org.opensha.sha.gui.infoTools;

import java.awt.BasicStroke;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.PrintJob;
import java.awt.Rectangle;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Rectangle2D;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Properties;

import javax.swing.BorderFactory;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTextArea;
import javax.swing.JTextPane;
import javax.swing.text.BadLocationException;
import javax.swing.text.SimpleAttributeSet;
import javax.swing.text.StyleConstants;

import org.apache.commons.lang.SystemUtils;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.ChartUtilities;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.axis.TickUnits;
import org.jfree.chart.labels.StandardXYToolTipGenerator;
import org.jfree.chart.plot.XYPlot;
import org.jfree.chart.renderer.xy.AbstractXYItemRenderer;
import org.jfree.chart.renderer.xy.StackedXYBarRenderer;
import org.jfree.chart.renderer.xy.StandardXYItemRenderer;
import org.jfree.chart.renderer.xy.XYBarRenderer;
import org.jfree.data.Range;
import org.jfree.ui.RectangleInsets;
import org.jfree.util.ShapeUtilities;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.commons.gui.plot.jfreechart.DiscretizedFunctionXYDataSet;
import org.opensha.commons.gui.plot.jfreechart.JFreeLogarithmicAxis;
import org.opensha.commons.gui.plot.jfreechart.MyTickUnits;
import org.opensha.commons.util.DataUtil;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;

import com.lowagie.text.Document;
import com.lowagie.text.DocumentException;
import com.lowagie.text.FontFactory;
import com.lowagie.text.HeaderFooter;
import com.lowagie.text.Phrase;
import com.lowagie.text.pdf.DefaultFontMapper;
import com.lowagie.text.pdf.PdfContentByte;
import com.lowagie.text.pdf.PdfTemplate;
import com.lowagie.text.pdf.PdfWriter;



/**
 * <p>Title: GraphPanel</p>
 * <p>Description: This class shows the JFreechart Panel in a window. It plot curves
 * using JFrechart package and if application supports allowing user to specify
 * different styles, colors and width of each curve the this application plots that
 * for the person.</p>
 * @author : Nitin Gupta
 * @version 1.0
 */

public class GraphPanel extends JSplitPane {



	// mesage needed in case of show data if plot is not available
	private final static String NO_PLOT_MSG = "No Plot Data Available";

	/**
	 * default color scheme for plotting curves
	 */
	Color[] defaultColor = {Color.red,Color.blue,Color.green,Color.darkGray,Color.magenta,Color.cyan,
			Color.orange,Color.pink,Color.yellow,Color.gray};


	private SimpleAttributeSet setLegend;

	// accessible components
	//private JSplitPane chartSplitPane;
	private JPanel chartPane;
	private JTextPane metadataText;
	private JScrollPane dataScrollPane;
	private JTextArea dataTextArea;
	private ChartPanel chartPanel;

	// these are coordinates and size of the circles visible in the plot
	private final static double SIZE = 3;
	private final static double DELTA = SIZE / 2.0;

	private static Dimension minPanelSize = new Dimension(320,120);

	//dataset to handover the data to JFreechart
	private DiscretizedFunctionXYDataSet data = new DiscretizedFunctionXYDataSet();
	//list containing Discretized function set
	private DiscretizedFuncList totalProbFuncs = new DiscretizedFuncList();

	//checks if weighted function exists in the list of functions
	private int weightedfuncListIndex;

	/**
	 * for Y-log, 0 values will be converted to this small value
	 */
	private double Y_MIN_VAL = 1e-16;


	private XYPlot plot;

	// Create the x-axis and y-axis - either normal or log
	//xaxis1 and yAxis1 replica of the x-Axis and y-Axis object, in case error occurs
	//and we have revert back the Axis
	NumberAxis xAxis, xAxis1 ;
	NumberAxis yAxis, yAxis1;

	// light blue color
	private Color lightBlue = new Color( 200, 200, 230 );

	//Keeps track when to toggle between the data and chart.
	private boolean graphOn = false;


	//Instance of the application using this class
	GraphPanelAPI application;



	//List of PlotCurveCharacterstics for each curve
	//that we plot which include the line color,line width.
	private ArrayList<PlotCurveCharacterstics> curvePlottingCharacterstics = new ArrayList<PlotCurveCharacterstics>();

	//This ArrayList stores the legend for various
	private ArrayList<String> legendString;

	/**
	 * class constructor
	 * @param api : Application instance
	 */
	public GraphPanel(GraphPanelAPI api) {
		super(JSplitPane.VERTICAL_SPLIT, true);
		setResizeWeight(1);
		setBorder(null);

		data.setFunctions(this.totalProbFuncs);
		// for Y-log, convert 0 values in Y axis to this small value, it just sets the minimum
		//value
		data.setConvertZeroToMin(true,Y_MIN_VAL);
		//instance of application using this class.
		application = api;
		try {
			jbInit();
		}
		catch(Exception ex) {
			ex.printStackTrace();
		}
	}

	/**
	 * Function to add GUI component to Graphpanel class
	 * @throws Exception
	 */
	void jbInit() throws Exception {

		dataTextArea = new JTextArea(NO_PLOT_MSG);
		//dataTextArea.setBorder(BorderFactory.createEtchedBorder());
		dataTextArea.setLineWrap(true);

		dataScrollPane = new JScrollPane();
		//dataScrollPane.setBorder(BorderFactory.createEtchedBorder());
		dataScrollPane.getViewport().add(dataTextArea, null);

		chartPane = new JPanel(new BorderLayout());
		chartPane.setMinimumSize(minPanelSize);
		chartPane.setPreferredSize(minPanelSize);

		metadataText = new JTextPane();
		metadataText.setEditable(false);
		JScrollPane metadataScrollPane = new JScrollPane();
		metadataScrollPane.getViewport().add(metadataText);
		metadataScrollPane.setMinimumSize(minPanelSize);
		metadataScrollPane.setPreferredSize(minPanelSize);
		metadataScrollPane.setBorder(
				BorderFactory.createLineBorder(Color.gray,1));


		setTopComponent(chartPane);
		setBottomComponent(metadataScrollPane);

	}


	/**
	 * For each function in the list it sets the plotting characeterstics of the curve
	 * so that when that list is given to JFreechart , it creates it with these characterstics.
	 * @param lineType : Plotting style
	 * @param color : Plotting cure color
	 * @param curveWidth : size of each plot
	 * @param functionIndex : secondary datset index.
	 * This method creates a new renderer for each dataset based on user's selected
	 * plotting style.If index is zero then set primary renderer else set secondary renderer
	 */
	private void drawCurvesUsingPlottingFeatures(String lineType,Color color,
			double curveWidth,int functionIndex){
		//Solid Line
		if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE)){
			StandardXYItemRenderer SOLID_LINE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.LINES,
					new StandardXYToolTipGenerator()
			);
			SOLID_LINE_RENDERER.setStroke(new BasicStroke((float)curveWidth));
			setRendererInPlot(color, functionIndex, SOLID_LINE_RENDERER);
		}
		//Dashed Line
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.DASHED_LINE)){
			StandardXYItemRenderer DASHED_LINE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.LINES,
					new StandardXYToolTipGenerator()
			);
			setRendererInPlot(color, functionIndex, DASHED_LINE_RENDERER);
			DASHED_LINE_RENDERER.setStroke(new BasicStroke((float)curveWidth,BasicStroke.CAP_BUTT
					,BasicStroke.JOIN_BEVEL,0,new float[] {9},0));
		}
		//Dotted Line
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.DOTTED_LINE)){
			StandardXYItemRenderer DOTTED_LINE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.LINES,
					new StandardXYToolTipGenerator()
			);
			setRendererInPlot(color, functionIndex, DOTTED_LINE_RENDERER);
			DOTTED_LINE_RENDERER.setStroke(new BasicStroke((float)curveWidth,BasicStroke.CAP_BUTT
					,BasicStroke.JOIN_BEVEL,0,new float[] {1},0));
		}
		//Dash and Dotted Line
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.DOT_DASH_LINE)){
			StandardXYItemRenderer DASH_DOTTED_LINE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.LINES,
					new StandardXYToolTipGenerator()
			);
			setRendererInPlot(color, functionIndex, DASH_DOTTED_LINE_RENDERER);
			DASH_DOTTED_LINE_RENDERER.setStroke(new BasicStroke((float)curveWidth,BasicStroke.CAP_BUTT
					,BasicStroke.JOIN_BEVEL,0,new float[] {5,3,2,3},0));
		}
		//Filled Circle
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES)){
			StandardXYItemRenderer FILLED_CIRCLES_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			FILLED_CIRCLES_SHAPE_RENDERER.setShape(new Ellipse2D.Double(-DELTA-curveWidth/2,
					-DELTA-curveWidth/2, SIZE+curveWidth, SIZE+curveWidth));
			setRendererInPlot(color, functionIndex, FILLED_CIRCLES_SHAPE_RENDERER);
		}
		//Circle
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.CIRCLES)){
			StandardXYItemRenderer CIRCLES_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			CIRCLES_SHAPE_RENDERER.setShape(new Ellipse2D.Double(-DELTA-curveWidth/2,
					-DELTA-curveWidth/2, SIZE+curveWidth, SIZE+curveWidth));
			CIRCLES_SHAPE_RENDERER.setShapesFilled(false);
			setRendererInPlot(color, functionIndex, CIRCLES_SHAPE_RENDERER);
		}
		//Filled Triangles
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.FILLED_TRIANGLES)){
			StandardXYItemRenderer FILLED_TRIANGLES_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			FILLED_TRIANGLES_SHAPE_RENDERER.setShape(ShapeUtilities.createUpTriangle((float)curveWidth));
			setRendererInPlot(color, functionIndex, FILLED_TRIANGLES_SHAPE_RENDERER);
		}
		//Triangles
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.TRIANGLES)){
			StandardXYItemRenderer TRIANGLES_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			TRIANGLES_SHAPE_RENDERER.setShape(ShapeUtilities.createUpTriangle((float)curveWidth));
			TRIANGLES_SHAPE_RENDERER.setShapesFilled(false);
			setRendererInPlot(color, functionIndex, TRIANGLES_SHAPE_RENDERER);
		}
		//Filled Inv Triangles
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.FILLED_INV_TRIANGLES)){
			StandardXYItemRenderer FILLED_INV_TRIANGLES_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			FILLED_INV_TRIANGLES_SHAPE_RENDERER.setShape(ShapeUtilities.createDownTriangle((float)curveWidth));
			setRendererInPlot(color, functionIndex, FILLED_INV_TRIANGLES_SHAPE_RENDERER);
		}
		//Inverted Triangles
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.INV_TRIANGLES)){
			StandardXYItemRenderer INV_TRIANGLES_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			INV_TRIANGLES_SHAPE_RENDERER.setShape(ShapeUtilities.createDownTriangle((float)curveWidth));
			INV_TRIANGLES_SHAPE_RENDERER.setShapesFilled(false);
			setRendererInPlot(color, functionIndex, INV_TRIANGLES_SHAPE_RENDERER);
		}
		//Filled Diamonds
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.FILLED_DIAMONDS)){
			StandardXYItemRenderer FILLED_DIAMONDS_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			FILLED_DIAMONDS_SHAPE_RENDERER.setShape(ShapeUtilities.createDiamond((float)curveWidth));
			setRendererInPlot(color, functionIndex, FILLED_DIAMONDS_SHAPE_RENDERER);
		}
		//Diamonds
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.DIAMONDS)){
			StandardXYItemRenderer DIAMONDS_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			DIAMONDS_SHAPE_RENDERER.setShape(ShapeUtilities.createDiamond((float)curveWidth));
			DIAMONDS_SHAPE_RENDERER.setShapesFilled(false);
			setRendererInPlot(color, functionIndex, DIAMONDS_SHAPE_RENDERER);
		}
		//Line and circle
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.LINE_AND_CIRCLES)){
			StandardXYItemRenderer LINE_AND_CIRCLES_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES_AND_LINES,
					new StandardXYToolTipGenerator()
			);
			LINE_AND_CIRCLES_RENDERER.setShape(new Ellipse2D.Double(-DELTA-(curveWidth*4)/2,
					-DELTA-(curveWidth*4)/2, SIZE+(curveWidth*4), SIZE+(curveWidth*4)));
			setRendererInPlot(color, functionIndex, LINE_AND_CIRCLES_RENDERER);
			LINE_AND_CIRCLES_RENDERER.setStroke(new BasicStroke((float)curveWidth));
		}
		//Line and Triangles
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.LINE_AND_TRIANGLES)){
			StandardXYItemRenderer LINE_AND_TRIANGLES_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES_AND_LINES,
					new StandardXYToolTipGenerator()
			);
			LINE_AND_TRIANGLES_RENDERER.setShape(ShapeUtilities.createUpTriangle((float)(curveWidth*4)));
			setRendererInPlot(color, functionIndex, LINE_AND_TRIANGLES_RENDERER);
			LINE_AND_TRIANGLES_RENDERER.setStroke(new BasicStroke((float)curveWidth));
		}
		//X symbols
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.X)){
			StandardXYItemRenderer X_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			X_SHAPE_RENDERER.setShape(ShapeUtilities.createDiagonalCross((float)curveWidth,0.1f));
			X_SHAPE_RENDERER.setShapesFilled(false);
			setRendererInPlot(color, functionIndex, X_SHAPE_RENDERER);
		}
		//+ symbols
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.CROSS_SYMBOLS)){
			StandardXYItemRenderer X_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			X_SHAPE_RENDERER.setShape(ShapeUtilities.createRegularCross((float)curveWidth,0.1f));
			X_SHAPE_RENDERER.setShapesFilled(false);
			setRendererInPlot(color, functionIndex, X_SHAPE_RENDERER);
		}
		//squares
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.SQUARES)){
			StandardXYItemRenderer SQUARE_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			SQUARE_SHAPE_RENDERER.setShape(new Rectangle.Double(-DELTA-curveWidth/2,
					-DELTA-curveWidth/2, SIZE+curveWidth, SIZE+curveWidth));
			SQUARE_SHAPE_RENDERER.setShapesFilled(false);
			setRendererInPlot(color, functionIndex, SQUARE_SHAPE_RENDERER);
		}
		//filled squares
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.FILLED_SQUARES)){
			StandardXYItemRenderer FILLED_SQUARE_SHAPE_RENDERER = new StandardXYItemRenderer(
					StandardXYItemRenderer.SHAPES,
					new StandardXYToolTipGenerator()
			);
			FILLED_SQUARE_SHAPE_RENDERER.setShape(new Rectangle.Double(-DELTA-curveWidth/2,
					-DELTA-curveWidth/2, SIZE+curveWidth, SIZE+curveWidth));
			setRendererInPlot(color, functionIndex, FILLED_SQUARE_SHAPE_RENDERER);
		}
		//histograms
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.HISTOGRAM)){
			XYBarRenderer HISTOGRAM_RENDERER = new XYBarRenderer();
			setRendererInPlot(color, functionIndex, HISTOGRAM_RENDERER);
		}
		//histograms
		else if(lineType.equals(PlotColorAndLineTypeSelectorControlPanel.STACKED_BAR)){
			StackedXYBarRenderer STACK_BAR_RENDERER = new StackedXYBarRenderer();
			setRendererInPlot(color, functionIndex, STACK_BAR_RENDERER);
		}

	}


	private void setRendererInPlot(Color color, int functionIndex,
			AbstractXYItemRenderer xyItemRenderer) {
		plot.setRenderer(functionIndex,xyItemRenderer);
		xyItemRenderer.setPaint(color);
	}


	/**
	 * Draws curves
	 * @param xAxisName : X-Axis Label
	 * @param yAxisName : Y-Axis Label
	 * @param funcList  : ArrayList containing individual functions and weighted functionlist
	 * @param xLog      : boolean tell if xLog is selected
	 * @param yLog      : boolean tells if yLog is selected
	 * @param customAxis : boolean tells if graph needs to ne plotted using custom axis range
	 * @param title  : JFreechart window title
	 * @param buttonControlPanel : Instance of class which called this method.
	 */
	public void drawGraphPanel(String xAxisName, String yAxisName,ArrayList funcList,
			boolean xLog,boolean yLog,boolean customAxis, String title,
			PlotControllerAPI buttonControlPanel ) {

		// Starting
		String S = "drawGraphPanel(): ";


		createColorSchemeAndFunctionList(funcList);


		//flags to check if the exception was thrown on selection of the x-log or y-log.
		boolean logErrorFlag = false;

		//getting the axis font size
		int axisFontSize = buttonControlPanel.getAxisLabelFontSize();
		//getting the tick label font size
		int tickFontSize = buttonControlPanel.getTickLabelFontSize();

		//create the standard ticks so that smaller values too can plotted on the chart
		TickUnits units = MyTickUnits.createStandardTickUnits();

		try{

			/// check if x log is selected or not
			if(xLog) xAxis = new JFreeLogarithmicAxis(xAxisName);
			else xAxis = new NumberAxis( xAxisName );

			//if (!xLog)
			//  xAxis.setAutoRangeIncludesZero(true);
			// else
			xAxis.setAutoRangeIncludesZero( false );
			xAxis.setStandardTickUnits(units);
			xAxis.setTickMarksVisible(false);
			//Axis label font
			Font axisLabelFont = xAxis.getLabelFont();
			xAxis.setLabelFont(new Font(axisLabelFont.getFontName(),axisLabelFont.getStyle(),axisFontSize));

			//tick label font
			Font axisTickFont = xAxis.getTickLabelFont();
			xAxis.setTickLabelFont(new Font(axisTickFont.getFontName(),axisTickFont.getStyle(),tickFontSize));

			//added to have the minimum range within the Upper and Lower Bound of the Axis
			//xAxis.setAutoRangeMinimumSize(.1);

			/* to set the range of the axis on the input from the user if the range combo box is selected*/
			if(customAxis)
				xAxis.setRange(application.getMinX(),application.getMaxX());

		}catch(Exception e){
			//e.printStackTrace();
			JOptionPane.showMessageDialog(this,e.getMessage(),"X-Plot Error",JOptionPane.OK_OPTION);
			graphOn=false;
			xLog = false;
			buttonControlPanel.setXLog(xLog);
			xAxis = xAxis1;
			logErrorFlag = true;
		}

		try{
			/// check if y log is selected or not
			if(yLog) yAxis = new JFreeLogarithmicAxis(yAxisName);
			else yAxis = new NumberAxis( yAxisName );

			if (!yLog)
				yAxis.setAutoRangeIncludesZero(true);
			else
				yAxis.setAutoRangeIncludesZero( false );

			yAxis.setStandardTickUnits(units);
			yAxis.setTickMarksVisible(false);

			//Axis label font
			Font axisLabelFont = yAxis.getLabelFont();
			yAxis.setLabelFont(new Font(axisLabelFont.getFontName(),axisLabelFont.getStyle(),axisFontSize));

			//tick label font
			Font axisTickFont = yAxis.getTickLabelFont();
			yAxis.setTickLabelFont(new Font(axisTickFont.getFontName(),axisTickFont.getStyle(),tickFontSize));
			//added to have the minimum range within the Upper and Lower Bound of the Axis
			//yAxis.setAutoRangeMinimumSize(.1);

			/* to set the range of the axis on the input from the user if the range combo box is selected*/
			if(customAxis)
				yAxis.setRange(application.getMinY(),application.getMaxY());

		}catch(Exception e){
			//e.printStackTrace();
			JOptionPane.showMessageDialog(this,e.getMessage(),"Y-Plot Error",JOptionPane.OK_OPTION);
			graphOn=false;
			yLog = false;
			buttonControlPanel.setYLog(yLog);
			yAxis = yAxis1;
			logErrorFlag = false;
		}


		plot = null;
		// build the plot
		plot = new XYPlot(null, xAxis, yAxis, null);

		//setting the plot properties
		plot.setDomainCrosshairLockedOnData(false);
		plot.setDomainCrosshairVisible(false);
		plot.setRangeCrosshairLockedOnData(false);
		plot.setRangeCrosshairVisible(false);
		plot.setInsets(new RectangleInsets(10, 0, 0, tickFontSize+15));


		//total number of funtions that need to be plotted differently using different characterstics
		int numFuncs = curvePlottingCharacterstics.size();
		//index of dataset from total prob functionlist (list containing each curve as
		//individual discretized function).
		int datasetIndex = 0;

		//secondarydataset index keeps track where do we have to add the seconadary data set in plot
		for(int j=0,dataIndex=0; j < numFuncs; ++j,++dataIndex){
			PlotCurveCharacterstics curveCharaceterstic = (PlotCurveCharacterstics)curvePlottingCharacterstics.get(j);
			Color color = curveCharaceterstic.getCurveColor();
			double lineWidth = curveCharaceterstic.getCurveWidth();
			String lineType = curveCharaceterstic.getCurveType();
			//getting the number of consecutive curves that have same plotting characterstics.
			int numCurves = curveCharaceterstic.getNumContinuousCurvesWithSameCharacterstics();
			//if size of that plot size then don't add it to the dataset
			if(lineWidth ==0){
				//adding the number of consecutive curves with same plotting characterstics to dataset index.
				datasetIndex +=numCurves;
				//decrement the secondary dataset index so that we seconday dataset is added to correct place.
				--dataIndex;
				continue;
			}
			//creating dataset for each curve and its consecutive curves which have same plotting
			//characterstics. Eg: can be weighted functions in weighted functionlist  have same
			//plotting characterstics, also fractiles in weighted function list share same
			//plotting characterstics. So creating dataset for each list of curves with
			//same plotting characterstics.
			DiscretizedFuncList dataFunctions = new DiscretizedFuncList();
			DiscretizedFunctionXYDataSet dataset = new DiscretizedFunctionXYDataSet();
			dataset.setXLog(xLog);
			dataset.setYLog(yLog);
			//converting the zero in Y-axis to some minimum value.
			dataset.setConvertZeroToMin(true,Y_MIN_VAL);
			dataset.setFunctions(dataFunctions);


			//creating the secondary dataset to show it in different color and shapes
			for(int i=datasetIndex;i<(datasetIndex+numCurves);++i){
				dataFunctions.add(totalProbFuncs.get(i));
			}
			datasetIndex +=numCurves;

			//adding the dataset to the plot
			plot.setDataset(dataIndex,dataset);

			//based on plotting characterstics for each curve sending configuring plot object
			//to be send to JFreechart for plotting.
			drawCurvesUsingPlottingFeatures(lineType,color,lineWidth,dataIndex);
		}

		plot.setBackgroundAlpha( .8f );

		//getting the tick label font size
		int plotLabelFontSize = buttonControlPanel.getPlotLabelFontSize();

		Font defaultPlotLabelFont = JFreeChart.DEFAULT_TITLE_FONT;
		Font newPlotLabelFont = new Font(defaultPlotLabelFont.getFontName(),defaultPlotLabelFont.getStyle(),plotLabelFontSize);

		//giving off all the data that needs to be plotted to JFreechart, which return backs
		//a panel fo curves,
		JFreeChart chart = new JFreeChart(title, newPlotLabelFont, plot, false );

		chart.setBackgroundPaint( lightBlue );

		// Put into a panel
		chartPanel = new ChartPanel(chart, true, true, true, true, false);

		//chartPanel.setBorder( BorderFactory.createEtchedBorder( EtchedBorder.LOWERED ) ); TODO clean
		chartPanel.setBorder(BorderFactory.createLineBorder(Color.gray,1));
		chartPanel.setMouseZoomable(true);
		chartPanel.setDisplayToolTips(true);
		chartPanel.setHorizontalAxisTrace(false);
		chartPanel.setVerticalAxisTrace(false);

		// set the font of legend
		int numOfColors = plot.getSeriesCount();

		/**
		 * Adding the metadata text to the Window below the Chart
		 */
		metadataText.removeAll();
		metadataText.setEditable(false);
		setLegend =new SimpleAttributeSet();
		setLegend.addAttribute(StyleConstants.CharacterConstants.Bold,
				Boolean.TRUE);
		javax.swing.text.Document doc = metadataText.getStyledDocument();

		weightedfuncListIndex = -1;
		try {

			/**
			 * formatting the metadata to be added , according to the colors of the
			 * Curves. So now curves and metadata will be displayed in the same color.
			 */
			doc.remove(0,doc.getLength());
			//total number of elements in the list containing individual functions and
			//weighted function list.
			int totalNumofFunctions = funcList.size();
			legendString = new ArrayList();
			//getting the metadata associated with each function in the list
			for(int i=0,plotPrefIndex=0;i<totalNumofFunctions;++i){
				String legend=null;
				//setting the font style for the legend
				setLegend =new SimpleAttributeSet();
				StyleConstants.setFontSize(setLegend,12);
				//checking if element in the list is weighted function list object
				Object obj = funcList.get(i);
				String datasetName = "DATASET #"+(i+1);
				if(obj instanceof WeightedFuncListforPlotting){
					//getting the metadata for weighted functionlist
					WeightedFuncListforPlotting weightedList = (WeightedFuncListforPlotting)obj;

					String listInfo = weightedList.getInfo();

					legend = new String(datasetName+"\n"+
							listInfo+SystemUtils.LINE_SEPARATOR);
					legendString.add(legend);
					StyleConstants.setForeground(setLegend,Color.black);
					doc.insertString(doc.getLength(),legend,setLegend);
					//index where the weighted function list exits if it does in the list of functions.
					weightedfuncListIndex = legendString.size()-1;
					//checking if individual curves need to be plotted
					if(weightedList.areIndividualCurvesToPlot()){
						((PlotCurveCharacterstics)this.curvePlottingCharacterstics.get(plotPrefIndex)).setCurveName(datasetName+" Curves");

						//getting the metadata for each individual curves and creating the legend string
						String listFunctionsInfo = weightedList.getFunctionTraceInfo();

						legend = new String(listFunctionsInfo+SystemUtils.LINE_SEPARATOR);
						legendString.add(legend);
						Color color = ((PlotCurveCharacterstics)this.curvePlottingCharacterstics.get(plotPrefIndex)).getCurveColor();
						StyleConstants.setForeground(setLegend,color);
						doc.insertString(doc.getLength(),legend,setLegend);
						++plotPrefIndex;
					}
					//checking if fractiles need to be plotted
					if(weightedList.areFractilesToPlot()){
						((PlotCurveCharacterstics)this.curvePlottingCharacterstics.get(plotPrefIndex)).setCurveName(
								datasetName+" Fractiles");

						//getting the fractile info for the weighted function list and adding that to the legend
						String fractileListInfo = weightedList.getFractileInfo();

						legend = new String(fractileListInfo+SystemUtils.LINE_SEPARATOR);
						legendString.add(legend);
						Color color = ((PlotCurveCharacterstics)this.curvePlottingCharacterstics.get(plotPrefIndex)).getCurveColor();
						StyleConstants.setForeground(setLegend,color);
						doc.insertString(doc.getLength(),legend,setLegend);
						++plotPrefIndex;
					}
					//checking if mean fractile need to be plotted
					if(weightedList.isMeanToPlot()){
						((PlotCurveCharacterstics)this.curvePlottingCharacterstics.get(plotPrefIndex)).setCurveName(
								datasetName+" Mean");
						//getting the fractileinfo and showing it as legend
						String meanInfo = weightedList.getMeanFunctionInfo();

						legend = new String(meanInfo+SystemUtils.LINE_SEPARATOR);
						legendString.add(legend);
						Color color = ((PlotCurveCharacterstics)this.curvePlottingCharacterstics.get(plotPrefIndex)).getCurveColor();
						StyleConstants.setForeground(setLegend,color);
						doc.insertString(doc.getLength(),legend,setLegend);
						++plotPrefIndex;
					}
				}
				else{ //if element in the list are individual function then get their info and show as legend
					((PlotCurveCharacterstics)this.curvePlottingCharacterstics.get(plotPrefIndex)).setCurveName(
							datasetName);
					DiscretizedFuncAPI func = (DiscretizedFuncAPI)funcList.get(i);
					String functionInfo = func.getInfo();
					String name = func.getName();
					legend = new String(datasetName+"\n"+
							name+"  "+SystemUtils.LINE_SEPARATOR+
							functionInfo+SystemUtils.LINE_SEPARATOR);
					legendString.add(legend);
					Color color = ((PlotCurveCharacterstics)this.curvePlottingCharacterstics.get(plotPrefIndex)).getCurveColor();
					StyleConstants.setForeground(setLegend,color);
					doc.insertString(doc.getLength(),legend,setLegend);
					++plotPrefIndex;
				}
			}
		} catch (BadLocationException e) {
			return;
		}
		graphOn=false;

		//Check to see if there is no log Error and only  xLog or yLog are selected
		if(!logErrorFlag && !xLog)
			xAxis1 = xAxis;
		if(!logErrorFlag && !yLog)
			yAxis1 = yAxis;

		//setting the info in the
		dataTextArea.setText(this.showDataInWindow(funcList,xAxisName,yAxisName));
		return ;
	}

	/**
	 *
	 * @param funcList
	 * @param xAxisName
	 * @param yAxisName
	 * @returns data to be shown in the data window
	 */
	private String showDataInWindow(ArrayList funcList,String xAxisName,String yAxisName){

		int size = funcList.size();

		StringBuffer b = new StringBuffer();
		b.append("\n");
		b.append("X-Axis: " + xAxisName + '\n');
		b.append("Y-Axis: " + yAxisName + '\n');
		b.append("Number of Data Sets: " + size + "\n\n");


		for(int i=0;i<size;++i){
			Object obj = funcList.get(i);

			if(!(obj instanceof WeightedFuncListforPlotting)){ //showing data for the individual function
				DiscretizedFuncAPI function = (DiscretizedFuncAPI)obj;
				b.append("\nDATASET #" + (i+1) + "\n\n");
				b.append(function.toString()+ '\n');
			}
			else{ //showing data for weighted function list
				WeightedFuncListforPlotting weightedList = (WeightedFuncListforPlotting)obj;
				b.append("\nDATASET #" + (i+1) + "   Weighted Function List"+'\n');
				b.append(weightedList.getInfo()+"\n\n");
				//checking if individual curves need to be plotted
				if(weightedList.areIndividualCurvesToPlot()){
					//getting the metadata for each individual curves and creating the legend string
					DiscretizedFuncList list = weightedList.getWeightedFunctionList();
					ArrayList wtList = weightedList.getRelativeWtList();
					int listSize = list.size();
					for(int j=0;j<listSize;++j){
						b.append("\nFunction #"+(j+1)+" of "+listSize+", from Dataset #"+(i+1)+
								", with relative wt = "+(Double)wtList.get(j)+"\n");
						DiscretizedFuncAPI function = (DiscretizedFuncAPI)list.get(j);
						b.append(function.getMetadataString()+ '\n');
					}
				}
				//checking if fractiles need to be plotted
				if(weightedList.areFractilesToPlot()){

					//getting the fractile info for the weighted function list and adding that to the legend
					DiscretizedFuncList list = weightedList.getFractileList();
					ArrayList fractileValueList = weightedList.getFractileValuesList();
					int listSize = list.size();
					for(int j=0;j<listSize;++j){
						b.append("\n"+(Double)fractileValueList.get(j)+" Fractile for Dataset #"+(i+1)+"\n");
						DiscretizedFuncAPI function = (DiscretizedFuncAPI)list.get(j);
						b.append(function.getMetadataString()+ '\n');
					}
				}

				//checking if mean fractile need to be plotted
				if(weightedList.isMeanToPlot()){
					//getting the fractileinfo and showing it as legend
					b.append("\nMean for Dataset #"+(i+1)+"\n");
					b.append(weightedList.getMean().getMetadataString()+"\n");
				}
			}
		}

		return b.toString();
	}


	/**
	 * Sets the metadata in the Data window
	 * @param metadata
	 */
	public void setMetadata(String metadata){
		dataTextArea.setText(metadata);
	}


	/**
	 * Clears the plot and the Metadata Window
	 */
	public void removeChartAndMetadata(){
		chartPane.removeAll();
		chartPanel = null;
		metadataText.setText("");
		dataTextArea.setText(this.NO_PLOT_MSG);
		curvePlottingCharacterstics.clear();
	}


	/**
	 *  Toggle between showing the graph and showing the actual data
	 */
	public void togglePlot(ButtonControlPanel buttonControlPanel) {

		chartPane.removeAll();
		//showing the data window
		if ( graphOn ) {
			if (buttonControlPanel != null)
				buttonControlPanel.setToggleButtonText( "Show Plot" );
			graphOn = false;

			chartPane.add(dataScrollPane, BorderLayout.CENTER);
			//      chartPane.add(dataScrollPane,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
			//          , GridBagConstraints.CENTER, GridBagConstraints.BOTH, plotInsets, 0, 0 ) );
		}
		else {
			//showing the Plot window, if not null
			graphOn = true;
			if (buttonControlPanel != null)
				buttonControlPanel.setToggleButtonText("Show Data");
			// panel added here
			if(chartPanel !=null) {
				chartPane.add(chartPanel, BorderLayout.CENTER);
				//        chartPane.add(chartPanel,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0 TODO clean
				//          , GridBagConstraints.CENTER, GridBagConstraints.BOTH, plotInsets, 0, 0 ) );

			} else {
				chartPane.add(dataScrollPane, BorderLayout.CENTER);
				//    	  chartPane.add(dataScrollPane, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
				//    	          , GridBagConstraints.CENTER, GridBagConstraints.BOTH, plotInsets, 0, 0 ) );
			}

		}
		return ;
	}

	/**
	 * sets the backgound for the plot
	 * @param color
	 */
	public void setPlotBackgroundColor(Color color){
		if(plot !=null)
			plot.setBackgroundPaint(color);
	}
	/**
	 *
	 * @returns the Range for the X-Axis
	 */
	public Range getX_AxisRange(){
		return xAxis.getRange();
	}

	/**
	 *
	 * @returns the Range for the Y-Axis
	 */
	public Range getY_AxisRange(){
		return yAxis.getRange();
	}


	/**
	 *
	 * @returns the list PlotCurveCharacterstics that contain the info about
	 * plotting the curve like plot line color , its width and line type.
	 */
	public ArrayList<PlotCurveCharacterstics> getCurvePlottingCharacterstic(){
		return curvePlottingCharacterstics;
	}


	/**
	 * This sets the plotting prefences for the curves. It takes in the
	 * list of PlotCurveCharacterstics and apply it to each curve in the list.
	 *
	 * @param plotPrefsList: List of PlotCurveCharacterstics for all curves.
	 */
	public void setCurvePlottingCharacterstic(ArrayList plotPrefsList){
		curvePlottingCharacterstics = plotPrefsList;
	}


	/**
	 * This method extracts all the functions from the ArrayList and add that
	 * to the DiscretizedFunction List. This method also creates the color scheme
	 * depending on the different types of DiscretizedFunc added to the list.
	 * @param functionList
	 */
	private void createColorSchemeAndFunctionList(ArrayList functionList){

		totalProbFuncs.clear();
		int numCurves  = functionList.size();
		ArrayList numColorArray = new ArrayList();


		for(int i=0;i<numCurves;++i){

			Object obj = functionList.get(i);
			if(obj instanceof WeightedFuncListforPlotting){
				WeightedFuncListforPlotting weightedList = (WeightedFuncListforPlotting)obj;
				if(weightedList.areIndividualCurvesToPlot()){
					DiscretizedFuncList list= weightedList.getWeightedFunctionList();
					//list.get(0).setInfo(weightedList.getInfo()+"\n"+"(a) "+list.getInfo());
					numColorArray.add(new Integer(list.size()));
					totalProbFuncs.addAll(list);
				}
				if(weightedList.areFractilesToPlot()){
					DiscretizedFuncList list= weightedList.getFractileList();
					// list.get(0).setInfo("(b) "+list.getInfo());
					totalProbFuncs.addAll(list);
					numColorArray.add(new Integer(list.size()));
				}
				if(weightedList.isMeanToPlot()){
					DiscretizedFuncAPI meanFunc = weightedList.getMean();
					//String info = meanFunc.getInfo();
					//meanFunc.setInfo("(c) "+info);
					totalProbFuncs.add(meanFunc);
					numColorArray.add(new Integer(1));
				}
			}
			else{
				totalProbFuncs.add((DiscretizedFuncAPI)obj);
				numColorArray.add(new Integer(1));
			}
		}


		//number of different curves with different plotting characterstics.
		int existingCurvesWithPlotPrefs = this.curvePlottingCharacterstics.size();

		int numDiffColors = numColorArray.size();

		//looping over all the default colors to add those to the color array
		for(int i=0,defaultColorIndex =0;i<numDiffColors;++i,++defaultColorIndex){
			//if the number of curves to be drawn are more in number then default colors then start from first again
			if(defaultColorIndex == defaultColor.length)
				defaultColorIndex = 0;
			int val = ((Integer)numColorArray.get(i)).intValue();
			//adding the new curves to the list for plot preferences.
			if(i>=existingCurvesWithPlotPrefs)
				curvePlottingCharacterstics.add(new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
						defaultColor[defaultColorIndex],1.0,val));
		}
	}



	/**
	 * Opens a file chooser and gives the user an opportunity to save the chart
	 * in PNG format if plot is visible.
	 * If data window is visible then saves the data to a file on users machine.
	 *
	 * @throws IOException if there is an I/O error.
	 */
	public void save() throws IOException {

		JFileChooser fileChooser = new JFileChooser();
		int option = fileChooser.showSaveDialog(this);
		String fileName = null;
		if (option == JFileChooser.APPROVE_OPTION) {
			fileName = fileChooser.getSelectedFile().getAbsolutePath();
			if (!fileName.endsWith(".pdf") && graphOn) {
				fileName = fileName + ".pdf";
			}
			else if (!graphOn)
				fileName = fileName + ".txt";
		}
		else {
			return;
		}

		if (graphOn)
			saveAsPDF(fileName);
		//chartPanel.doSaveAs();
		else
			DataUtil.save(fileName, dataTextArea.getText());
	}

	/**
	 * Allows the user to save the chart as PNG.
	 * @param fileName
	 * @throws IOException
	 */
	public void saveAsPNG(String fileName) throws IOException {
		ChartUtilities.saveChartAsPNG(new File(fileName),chartPanel.getChart() , 
				chartPanel.getWidth(), chartPanel.getHeight());
	}

	/**
	 * Allows the user to save the chart contents and metadata as PDF.
	 * This allows to preserve the color coding of the metadata.
	 * @throws IOException
	 */
	public void saveAsPDF(String fileName) throws IOException {
		int width = chartPanel.getWidth();
		int height = chartPanel.getHeight();
		this.saveAsPDF(fileName, width, height);
	}

	/**
	 * Allows the user to save the chart contents and metadata as PDF.
	 * This allows to preserve the color coding of the metadata.
	 * @throws IOException
	 */
	public void saveAsPDF(String fileName, int width, int height) throws IOException {
		int textLength = metadataText.getStyledDocument().getLength();
		int totalLength = textLength + height;
		// step 1
		Document metadataDocument = new Document(new com.lowagie.text.Rectangle(
				width, height));
		metadataDocument.addAuthor("OpenSHA");
		metadataDocument.addCreationDate();
		HeaderFooter footer = new HeaderFooter(new Phrase("Powered by OpenSHA"), true);
		metadataDocument.setFooter(footer);
		try {
			// step 2
			PdfWriter writer;

			writer = PdfWriter.getInstance(metadataDocument,
					new FileOutputStream(fileName));
			// step 3
			metadataDocument.open();
			// step 4
			PdfContentByte cb = writer.getDirectContent();
			PdfTemplate tp = cb.createTemplate(width, height);
			Graphics2D g2d = tp.createGraphics(width, height,
					new DefaultFontMapper());
			Rectangle2D r2d = new Rectangle2D.Double(0, 0, width, height);
			chartPanel.getChart().draw(g2d, r2d);
			g2d.dispose();
			cb.addTemplate(tp, 0, 0);
			//starts the metadata from the new page.
			metadataDocument.newPage();
			int size = legendString.size();
			for (int i = 0, legendColor = 0; i < size; ++i, ++legendColor) {
				com.lowagie.text.Paragraph para = new com.lowagie.text.Paragraph();
				//checks to see if the WeightFuncList exists in the list of functions
				//then plot it in black else plot in the same as the legend
				if (weightedfuncListIndex != -1 && weightedfuncListIndex == i) {
					para.add(new Phrase( (String) legendString.get(i),
							FontFactory.getFont(
									FontFactory.HELVETICA, 10, Font.PLAIN,
									Color.black)));
					--legendColor;
				}
				else {
					para.add(new Phrase( (String) legendString.get(i),
							FontFactory.getFont(
									FontFactory.HELVETICA, 10, Font.PLAIN,
									( (PlotCurveCharacterstics)
											curvePlottingCharacterstics.get(legendColor)).
											getCurveColor())));
				}
				metadataDocument.add(para);
			}
		}
		catch (DocumentException de) {
			de.printStackTrace();
		}
		// step 5
		metadataDocument.close();
	}


	/**
	 * Creates a print job for the chart if plot is being shown, else print
	 * the chart data if data window is visible.
	 * @param frame JFrame Instance of the Frame using this GraphPanel class
	 */
	public void print(JFrame frame){
		if(graphOn)
			chartPanel.createChartPrintJob();
		else{
			Properties p = new Properties();
			PrintJob pjob = this.getToolkit().getPrintJob(frame,"Printing" , p);
			if (pjob != null) {
				Graphics pg = pjob.getGraphics();
				if (pg != null) {
					DataUtil.print(pjob, pg, dataTextArea.getText());
					pg.dispose();
				}
				pjob.end();
			}

		}
	}


	/**
	 *
	 * @returns the XAxis Label if not null
	 * else return null
	 */
	public String getXAxisLabel(){
		if(xAxis !=null)
			return xAxis.getLabel();
		return null;
	}

	/**
	 *
	 * @returns the YAxis Label if not null
	 * else return null
	 */
	public String getYAxisLabel(){
		if(yAxis !=null)
			return yAxis.getLabel();
		return null;
	}

	/**
	 *
	 * @returns the chart Title if not null
	 * else return null
	 */
	public String getPlotLabel(){
		if(chartPanel !=null)
			return chartPanel.getChart().getTitle().getText();
		return null;
	}


	public ChartPanel getCartPanel() {
		return this.chartPanel;
	}
}
