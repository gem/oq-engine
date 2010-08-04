package scratch.martinez.beans;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.Set;
import java.util.TreeMap;

import javax.swing.JCheckBoxMenuItem;
import javax.swing.JComboBox;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.JToolBar;

import org.jfree.data.Range;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.sha.gui.infoTools.ButtonControlPanel;
import org.opensha.sha.gui.infoTools.ButtonControlPanelAPI;
import org.opensha.sha.gui.infoTools.GraphPanel;
import org.opensha.sha.gui.infoTools.GraphPanelAPI;


/**
 * <p>Title: GraphPane</p>
 *
 * <p>Description: This class allows user to visualise the computed data as graphs.</p>
 * @author Ned Field,Nitin Gupta,E.V.Leyendecker, Eric Martinez
 */
public class GraphPane extends JPanel 
	implements ButtonControlPanelAPI, GraphPanelAPI {
	private static final long serialVersionUID	= 1;
	
	JMenuBar menuBar = new JMenuBar();
	JMenu fileMenu = new JMenu();

	JMenuItem fileExitMenu = new JMenuItem();
	JMenuItem fileSaveMenu = new JMenuItem();
	JMenuItem filePrintMenu = new JCheckBoxMenuItem();
	JToolBar jToolBar = new JToolBar();

	private final static int W = 512;
	private final static int H = 730;
	private JSplitPane chartSplitPane = new JSplitPane();
	private JPanel chartPane = new JPanel();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private BorderLayout borderLayout1 = new BorderLayout();
	private JPanel buttonPanel = new JPanel();
	private FlowLayout flowLayout1 = new FlowLayout();

	//boolean parameters for the Axis to check for log
	private boolean xLog = false;
	private boolean yLog = false;

	//boolean parameter to check for range of the axis
	private boolean customAxis = false;

	private String plotTitle = "Hazard Curves";

	private double minXValue, maxXValue, minYValue, maxYValue;

	//instance for the ButtonControlPanel
	private ButtonControlPanel buttonControlPanel;

	//instance of the GraphPanel class
	private GraphPanel graphPanel;

	private String xAxisName, yAxisName;

	private JComboBox graphListCombo = new JComboBox();

	/**
	 * Creating this Map to keep track of the selected item to plot
	 */
	private TreeMap<String, ArrayList<ArbitrarilyDiscretizedFunc>> map = new
				TreeMap<String, ArrayList<ArbitrarilyDiscretizedFunc>>();

	/**
	 * Class constructor that shows the list of graphs that user can plot.
	 * @param dataList ArrayList List of DiscretizedFunctionList
	 */
	public GraphPane(ArrayList dataList) {
		//adding list of graphs to the shown to the user.
		int size = 0;
		if(dataList != null) size = dataList.size();

		//creating the ArrayList for the plots
		for (int i = 0; i < size; ++i) {
			//getting the functions to plot and creating individual ArrayList for those
			//adding these individual arraylist to the hashmap.
			ArbitrarilyDiscretizedFunc function = (ArbitrarilyDiscretizedFunc)
					dataList.get(i);
			ArrayList<ArbitrarilyDiscretizedFunc> plottingFunction = new ArrayList<ArbitrarilyDiscretizedFunc>();
			plottingFunction.add(function);
			map.put(function.getName(), plottingFunction);
		}

		//adding the functions having same X and Y axis name to HashMap
		for (int i = 0; i < size; ++i) {
			ArbitrarilyDiscretizedFunc function = (ArbitrarilyDiscretizedFunc)
					dataList.get(i);
			ArrayList<ArbitrarilyDiscretizedFunc> plottingFunctions = new ArrayList<ArbitrarilyDiscretizedFunc>();
			String functionXName = function.getXAxisName();
			String functionYName = function.getYAxisName();
			boolean containsSameName = false;
			String name = null;
			for (int j = i + 1; j < size; ++j) {
				ArbitrarilyDiscretizedFunc function1 = (ArbitrarilyDiscretizedFunc)
						dataList.get(j);
				String function1XName = function1.getXAxisName();
				String function1YName = function1.getYAxisName();
				if (functionXName.equals(function1XName) &&
						functionYName.equals(function1YName)) {
					//name = function1YName + " Vs " + function1XName;
					if (functionXName.equals("Damage Factor"))
						name = "Loss Curve Summary";
					else
						name = "Basic Hazard Curve";
					if (!map.containsKey(name)) {
						plottingFunctions.add(function1);
						containsSameName = true;
					}
				}
			}
			if (containsSameName) {
				plottingFunctions.add(function);
				map.put(name, plottingFunctions);
				containsSameName = false;
			}
		}
	 

//Adding the names of the plot to the Combo selection
		Set plotNames = map.keySet();
		Iterator it = plotNames.iterator();
		while (it.hasNext()) {
			graphListCombo.addItem(it.next());
		}

		graphListCombo.setSelectedIndex(0);
		if(graphListCombo.getItemCount() > 1) 
			graphListCombo.setSelectedIndex(1);

		try {
			jbInit();
		}
		catch (Exception exception) {
			exception.printStackTrace();
		}

		graphPanel = new GraphPanel(this);
		graphPanel.setDividerLocation(350);
		drawGraph();
	}

	/**
	 * Component initialization.
	 *
	 * @throws java.lang.Exception
	 */
	private void jbInit() throws Exception {
		setLayout(borderLayout1);
		setSize(new Dimension(W, H));
		
		graphListCombo.addItemListener(new ItemListener() {
			public void itemStateChanged(ItemEvent itemEvent) {
				graphListCombo_itemStateChanged(itemEvent);
			}
		});
		
		chartSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		chartPane.setLayout(gridBagLayout1);

		buttonPanel.setLayout(flowLayout1);
		add(chartSplitPane, BorderLayout.CENTER);
		chartSplitPane.add(chartPane, JSplitPane.TOP);
		chartSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
		chartSplitPane.setDividerLocation(450);
		//object for the ButtonControl Panel
		buttonControlPanel = new ButtonControlPanel(this);
		buttonPanel.add(buttonControlPanel, 0);
		chartPane.add(graphListCombo, new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(4, 4, 4, 4), 0, 0));
	}

	/**
	 *
	 * @return the Range for the X-Axis
	 */
	public Range getX_AxisRange() {
		return graphPanel.getX_AxisRange();
	}

	/**
	 *
	 * @return the Range for the Y-Axis
	 */
	public Range getY_AxisRange() {
		return graphPanel.getY_AxisRange();
	}

	/**
	 * tells the application if the xLog is selected
	 * @param xLog : boolean
	 */
	public void setX_Log(boolean xLog) {
		this.xLog = xLog;
		drawGraph();
	}

	/**
	 * tells the application if the yLog is selected
	 * @param yLog : boolean
	 */
	public void setY_Log(boolean yLog) {
		this.yLog = yLog;
		drawGraph();
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
		minXValue = xMin;
		maxXValue = xMax;
		minYValue = yMin;
		maxYValue = yMax;
		customAxis = true;
		drawGraph();
	}

	/**
	 * set the auto range for the axis. This function is called
	 * from the AxisLimitControlPanel
	 */
	public void setAutoRange() {
		customAxis = false;
		drawGraph();
	}

	/**
	 * to draw the graph
	 */
	private void drawGraph() {

		//getting the list of the curves that we need to plot
		String selectedDataToPlot = (String) graphListCombo.getSelectedItem();

		//show correct graph titles
		plotTitle = selectedDataToPlot;

		ArrayList functionsToPlot = (ArrayList) map.get(selectedDataToPlot);
		ArbitrarilyDiscretizedFunc func = (ArbitrarilyDiscretizedFunc)
		functionsToPlot.get(0);
		xAxisName = func.getXAxisName();
		yAxisName = func.getYAxisName();

		//creating the graph to be shown in the window
		graphPanel.drawGraphPanel(xAxisName, yAxisName, functionsToPlot, xLog, yLog,
				customAxis, plotTitle, buttonControlPanel);
		togglePlot();
		graphPanel.updateUI();
	}

	/**
	 * plots the curves with defined color,line width and shape.
	 */
	public void plotGraphUsingPlotPreferences() {
		drawGraph();
	}

	//checks if the user has plot the data window or plot window
	public void togglePlot() {
		graphPanel.togglePlot(buttonControlPanel);
		chartPane.add(graphPanel, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(2, 2, 2, 2), 0, 0));
		chartPane.validate();
		chartPane.repaint();
	}

	/**
	 *
	 * @return the Min X-Axis Range Value, if custom Axis is choosen
	 */
	public double getMinX() {
		return minXValue;
	}

	/**
	 *
	 * @return the Max X-Axis Range Value, if custom axis is choosen
	 */
	public double getMaxX() {
		return maxXValue;
	}

	/**
	 *
	 * @return the Min Y-Axis Range Value, if custom axis is choosen
	 */
	public double getMinY() {
		return minYValue;
	}

	/**
	 *
	 * @return the Max Y-Axis Range Value, if custom axis is choosen
	 */
	public double getMaxY() {
		return maxYValue;
	}

	/**
	 *
	 * @return the plotting feature like width, color and shape type of each
	 * curve in list.
	 */
	public ArrayList getPlottingFeatures() {
		return graphPanel.getCurvePlottingCharacterstic();
	}

	/**
	 *
	 * @return the X Axis Label
	 */
	public String getXAxisLabel() {
		return xAxisName;
	}

	/**
	 *
	 * @return Y Axis Label
	 */
	public String getYAxisLabel() {
		return yAxisName;
	}

	/**
	 *
	 * @return plot Title
	 */
	public String getPlotLabel() {
		return plotTitle;
	}

	/**
	 *
	 * sets	X Axis Label
	 */
	public void setXAxisLabel(String xAxisLabel) {
		xAxisName = xAxisLabel;
	}

	/**
	 *
	 * sets Y Axis Label
	 */
	public void setYAxisLabel(String yAxisLabel) {
		yAxisName = yAxisLabel;
	}

	/**
	 *
	 * sets plot Title
	 */
	public void setPlotLabel(String plotTitle) {
		this.plotTitle = plotTitle;
	}

	public void graphListCombo_itemStateChanged(ItemEvent itemEvent) {
		graphPanel.removeChartAndMetadata();
		drawGraph();
	}
	
	public void setLogSpace(boolean xlog, boolean ylog) {
		this.xLog = xlog;
		this.yLog = ylog;
		buttonControlPanel.setXLog(xlog);
		buttonControlPanel.setYLog(ylog);
		drawGraph();
	}
}
