package scratch.martinez.beans;

import java.awt.Color;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTextArea;

import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.renderer.xy.XYItemRenderer;
import org.jfree.data.Range;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.nshmp.sha.gui.beans.GuiBeanAPI;
import org.opensha.sha.gui.infoTools.ButtonControlPanelAPI;
import org.opensha.sha.gui.infoTools.GraphPanelAPI;

/**
 * <strong>Title</strong>: GraphingBean<br />
 * <strong>Description</strong>: This bean implements a versatile method to output graphical
 * information.  This class is fully self contained, but can be expanded upon by some "container".
 * For implementation of this bean, currently supported visualizations include:<br />
 * <ul>
 * 	<li>EMBED</li>
 * 	<li>SPLASH</li>
 * 	<li>BUTTON</li>
 * </ul>
 * <br />
 * This bean is powered by the <a href="www.jfreechart.org">JFreeChart</a> <small>(API)</small> graphing package.
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 *
 */
public class GraphingBean implements GuiBeanAPI, GraphPanelAPI,
		ButtonControlPanelAPI {

	//////////////////////////////////////////////////////////////////////////////////
	//                  Private Variables for this Bean to Run                      //
	//////////////////////////////////////////////////////////////////////////////////
	
	/* Important Visualization Variables */
	private JPanel embedVis = null;
	private JFrame splashVis = null;
	private JButton buttonVis = null;
	
	/* Utility Variables for Visualization */
	private static Color[] defaultColor = { Color.red, Color.blue, Color.green, Color.darkGray,
			Color.magenta, Color.cyan, Color.orange, Color.pink, Color.yellow, Color.gray };
	private JSplitPane chartSplitPane = null;	// This split pane holds the graph on top and meta data on bottom
	private JPanel buttonPanel = null;			// This is the button control panel for the graphing
	
	// Variables for the chart portion of the bean
	private JFreeChart chart = null;
	private ChartPanel chartPanel = null; // The chart for the top of the chartSplitPane
	private XYItemRenderer itemRenderer = null;
	private NumberAxis xAxis = null;
	private NumberAxis yAxis = null;
	
	// Variables for the textual output
	JScrollPane metaDataScroll = null; // The scroll pane for the bottom of the chartSplitPane
	JTextArea metaTextArea = null;
	JScrollPane outputDataScroll = null; // The output pane for the "flip" side of this bean
	JTextArea outputTextArea = null;
	
	//////////////////////////////////////////////////////////////////////////////////
	//               Public Constructors to Instantiate this Bean                   //
	//////////////////////////////////////////////////////////////////////////////////
	
	//////////////////////////////////////////////////////////////////////////////////
	//               Public Functions to Aid in Use of the Bean                     //
	//////////////////////////////////////////////////////////////////////////////////
	
	/**
	 * Sets the single function to graph in the GraphPane.  A wrapper function to
	 * <code>setGraphFunctions(DiscretizedFuncList funcList)</code>.  The graph will
	 * be updated and repainted as required to update the end-user graph.
	 * 
	 * @param func The function to show on the graph.
	 */
	public void setGraphFunction(DiscretizedFuncAPI func) {
		
	}
	
	//////////////////////////////////////////////////////////////////////////////////
	//                   FUNCTIONS TO IMPLEMENT THE GuiBeanAPI                      //
	//////////////////////////////////////////////////////////////////////////////////
	
	/** See the general contract in <code>GuiBeanAPI</code> */
	public Object getVisualization(int type) throws IllegalArgumentException {
		if(type == GuiBeanAPI.EMBED)
			return getEmbeddedVisualization();
		else if(type == GuiBeanAPI.SPLASH)
			return getSplashVisualization();
		else if(type == GuiBeanAPI.BUTTON)
			return getButtonVisualization();
		else
			throw new IllegalArgumentException("The given type is not currently suported.");
	}

	/** See the general contract in <code>GuiBeanAPI</code> */
	public String getVisualizationClassName(int type) {
		if(type == GuiBeanAPI.EMBED)
			return "javax.swing.JPanel";
		else if(type == GuiBeanAPI.SPLASH)
			return "javax.swing.JFrame";
		else if(type == GuiBeanAPI.BUTTON)
			return "javax.swing.JButton";
		else
			return null;
	}

	/** See the general contract in <code>GuiBeanAPI</code> */
	public boolean isVisualizationSupported(int type) {
		if(type == GuiBeanAPI.EMBED)
			return true;
		else if(type == GuiBeanAPI.SPLASH)
			return true;
		else if(type == GuiBeanAPI.BUTTON)
			return true;
		else
			return false;
	}

	//////////////////////////////////////////////////////////////////////////////////
	//                 FUNCTIONS TO IMPLEMENT THE GraphPanelAPI                     //
	//////////////////////////////////////////////////////////////////////////////////
	public double getMaxX() {
		// TODO Auto-generated method stub
		return 0;
	}

	public double getMaxY() {
		// TODO Auto-generated method stub
		return 0;
	}

	public double getMinX() {
		// TODO Auto-generated method stub
		return 0;
	}

	public double getMinY() {
		// TODO Auto-generated method stub
		return 0;
	}

	//////////////////////////////////////////////////////////////////////////////////
	//             FUNCTIONS TO IMPLEMENT THE ButtonControlPanelAPI                 //
	//////////////////////////////////////////////////////////////////////////////////
	public String getPlotLabel() {
		// TODO Auto-generated method stub
		return null;
	}

	public ArrayList getPlottingFeatures() {
		// TODO Auto-generated method stub
		return null;
	}

	public String getXAxisLabel() {
		// TODO Auto-generated method stub
		return null;
	}

	public Range getX_AxisRange() {
		// TODO Auto-generated method stub
		return null;
	}

	public String getYAxisLabel() {
		// TODO Auto-generated method stub
		return null;
	}

	public Range getY_AxisRange() {
		// TODO Auto-generated method stub
		return null;
	}

	public void plotGraphUsingPlotPreferences() {
		// TODO Auto-generated method stub

	}

	public void setPlotLabel(String plotTitle) {
		// TODO Auto-generated method stub

	}

	public void setXAxisLabel(String xAxisLabel) {
		// TODO Auto-generated method stub

	}

	public void setX_Log(boolean xLog) {
		// TODO Auto-generated method stub

	}

	public void setYAxisLabel(String yAxisLabel) {
		// TODO Auto-generated method stub

	}

	public void setY_Log(boolean yLog) {
		// TODO Auto-generated method stub

	}

	public void togglePlot() {
		// TODO Auto-generated method stub

	}

	public void setAutoRange() {
		// TODO Auto-generated method stub

	}

	public void setAxisRange(double xMin, double xMax, double yMin, double yMax) {
		// TODO Auto-generated method stub

	}

	//////////////////////////////////////////////////////////////////////////////////
	//                    Private Utility Functions Used Above                      //
	//////////////////////////////////////////////////////////////////////////////////
	/** Creates an embeddable JPanel visualization of this bean. */
	private JPanel getEmbeddedVisualization() {
		if(embedVis == null) {
			
		}
		return embedVis;
	}
	
	/** Creates a "pop-up" JFrame (splash) visualization of this bean. */
	private JFrame getSplashVisualization() {
		if(splashVis == null) {
			
		}
		return splashVis;
	}
	
	/** 
	 * Creates a JButton visualization of this bean.  
	 * When clicked, the SPLASH visualization is shown. 
	 */
	private JButton getButtonVisualization() {
		if(buttonVis == null) {
			
		}
		return buttonVis;
	}
}
