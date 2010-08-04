package junk.PEER_TestsGroupResults;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Paint;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.io.DataInputStream;
import java.io.InputStream;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.StringTokenizer;

import javax.swing.BorderFactory;
import javax.swing.ImageIcon;
import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTextArea;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.border.Border;
import javax.swing.border.EtchedBorder;

import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.LogarithmicAxis;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.axis.TickUnits;
import org.jfree.chart.labels.StandardXYToolTipGenerator;
import org.jfree.chart.renderer.xy.StandardXYItemRenderer;
import org.jfree.data.Range;
import org.opensha.commons.calc.FunctionListCalc;
import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.commons.gui.plot.jfreechart.DiscretizedFunctionXYDataSet;
import org.opensha.commons.gui.plot.jfreechart.MyTickUnits;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.gui.controls.AxisLimitsControlPanel;
import org.opensha.sha.gui.controls.AxisLimitsControlPanelAPI;



/**
 * <p>Title: PEER_Test_GuiPlotter</p>
 * <p>Description: This class provides the services of plotting PEER test cases
 * result from the differents files</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * @author : Nitin Gupta & Vipin Gupta
 * @created : Dec 06,2002
 * @version 1.0
 */

public class PEER_TestResultsPlotterApplet extends JApplet implements
NamedObjectAPI,
AxisLimitsControlPanelAPI,
ActionListener {
	private boolean isStandalone = false;
	private JPanel mainPanel = new JPanel();
	private JSplitPane mainSplitPane = new JSplitPane();
	private JSplitPane plotSplitPane = new JSplitPane();

	private static final String C="PEER_Test_GuiPlotter";

	private static final boolean D= false;

	// default insets
	Insets defaultInsets = new Insets( 4, 4, 4, 4 );

	//log flags declaration
	private boolean xLog =false;
	private boolean yLog =false;

	// for the data version and data last updated things
	// these will be read from a separate data.version file
	private String dataVersion ;
	private String dataLastUpdated;

	// message string to be dispalayed if user chooses Axis Scale
	// without first clicking on "Add Graph"
	private final static String AXIS_RANGE_NOT_ALLOWED =
		new String("First Choose Add Graph. Then choose Axis Scale option");


	//variables that determine the window size
	protected final static int W = 850;
	protected final static int H = 700;

	//Directory from which to search for all the PEER test files
	String DIR = "GroupTestDataFiles/";
	String FILE_EXTENSION=".dat";

	// mesage needed in case of show data if plot is not available
	final static String NO_PLOT_MSG = "No Plot Data Available";

	private Insets plotInsets = new Insets( 4, 10, 4, 4 );
	protected boolean graphOn = false;


	DiscretizedFuncList functions = new DiscretizedFuncList();
	DiscretizedFunctionXYDataSet data = new DiscretizedFunctionXYDataSet();


	// Create the x-axis and y-axis - either normal or log
	org.jfree.chart.axis.NumberAxis xAxis = null;
	org.jfree.chart.axis.NumberAxis yAxis = null;


	/**
	 * adding scroll pane for showing data
	 */
	JScrollPane dataScrollPane = new JScrollPane();

	// text area to show the data values
	JTextArea pointsTextArea = new JTextArea();

	/**
	 * chart panel, that is plot window
	 */
	ChartPanel chartPanel;

	// AxisLimitsControlPanel
	AxisLimitsControlPanel axisLimits;

	/**
	 * these four values save the custom axis scale specified by user
	 */
	protected double minXValue;
	protected double maxXValue;
	protected double minYValue;
	protected double maxYValue;
	protected boolean customAxis = false;

	// light blue color
	Color lightBlue = new Color( 200, 200, 230 );
	Color AVERAGE_COLOR = Color.red;

	/**
	 * for Y-log, 0 values will be converted to this small value
	 */
	private double Y_MIN_VAL = 1e-16;

	//X and Y AXIS Labels
	private String X_AXIS_TITLE = "Intensity Measure Level";
	private String Y_AXIS_TITLE = "Probability";

	//static definition  of the strings
	private final static String FRAME_TITLE = "PEER Tests Plots";
	private final static String AUTO_SCALE = "Auto Scale";
	private final static String CUSTOM_SCALE = "Custom Scale";
	private final static String JFREECHART_TITLE = "Hazard Curves";
	private final static String STANDALONE_WARNING =
		"Because you are running this application from the stand-alone "+
		" jar file (as opposed to the applet)\nthe data might now be out of date.\n\n"+
		"Downloading the latest version of this jar file  will get you"+
		" the latest results.";
	private final static String GUI_TITLE = "PEER PSHA-Test Results Plotter";

	//images for the OpenSHA
	private final static String FRAME_ICON_NAME = "openSHA_Aqua_sm.gif";
	private final static String POWERED_BY_IMAGE = "PoweredBy.gif";

	//static string for the OPENSHA website
	private final static String OPENSHA_WEBSITE="http://www.OpenSHA.org";


	private JPanel buttonPanel = new JPanel();
	private JPanel topPlotPanel = new JPanel();
	private Border border1;
	private Border border2;
	private Border border3;
	private JCheckBox xLogCheckBox = new JCheckBox();
	private JCheckBox yLogCheckBox = new JCheckBox();
	private Border border4;
	private Border border5;


	// reads the full file names of all the stored files in the directory
	ArrayList testFiles = new ArrayList();

	//ArrayList to store all the checkboxes for the selected test file
	ArrayList checkBoxVector = new ArrayList();
	// vector of check boxes for calculating the average
	ArrayList avgCheckBoxVector = new ArrayList();

	/*setting the colors for the different plots so that legends checkboxes
	 *can be shown with the same color

	 * Here we do not see RED color as we will use it only for average
	 */
	Color[] legendColor ={Color.blue,Color.green,Color.orange,Color.magenta,
			Color.cyan,Color.pink,Color.yellow,Color.gray,new Color(137,114,40),
			new Color(137,199,205),new Color(255,199,205),new Color(255,228,188),
			new Color(125,108,142),new Color(125,108,23), new Color(255,182,23),
			new Color(255,182,255)};
	Paint[] legendPaint;


	private JSplitPane avgSplitPane = new JSplitPane();
	private JPanel avgCasesPanel = new JPanel();
	private JScrollPane avgScrollPane = new JScrollPane();
	private JPanel testCasesPanel = new JPanel();
	private JScrollPane plotScrollPane = new JScrollPane();
	private GridBagLayout gridBagLayout4 = new GridBagLayout();
	private JLabel avgLabel = new JLabel();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private JComboBox testCaseCombo = new JComboBox();
	private JLabel testCaseLabel = new JLabel();
	private JPanel plotPanel = new JPanel();
	private GridBagLayout gridBagLayout2 = new GridBagLayout();
	private GridBagLayout gridBagLayout6 = new GridBagLayout();
	private JLabel testPanelLabel = new JLabel();
	private JCheckBox averageCheck = new JCheckBox();
	private GridBagLayout gridBagLayout5 = new GridBagLayout();
	private JButton toggleButton = new JButton();
	private JLabel guiLabel = new JLabel();
	private JLabel dataVersionLabel = new JLabel();
	JLabel powerLabel = new JLabel();
	private JButton axisScaleButton = new JButton();
	private GridBagLayout gridBagLayout3 = new GridBagLayout();
	private GridBagLayout gridBagLayout7 = new GridBagLayout();
	private BorderLayout borderLayout1 = new BorderLayout();

	//Construct the applet
	public PEER_TestResultsPlotterApplet() {

		// for Y-log, convert 0 values in Y axis to this small value
		data.setConvertZeroToMin(true,Y_MIN_VAL);
	}

	//Initialize the applet
	public void init() {
		try {
			jbInit();

			// show the data version and time data was last updated
			this.readDataVersion();
			this.dataVersionLabel.setText("Data Version:"+this.dataVersion+
					"   Last Updated:"+this.dataLastUpdated);

			//shows the selection for the different Test Cases files
			initTestParamList();
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}
	//Component initialization
	private void jbInit() throws Exception {
		border1 = new EtchedBorder(EtchedBorder.RAISED,Color.white,new Color(178, 178, 178));
		border2 = new EtchedBorder(EtchedBorder.RAISED,Color.white,new Color(178, 178, 178));
		border3 = new EtchedBorder(EtchedBorder.RAISED,Color.white,new Color(178, 178, 178));
		border4 = new EtchedBorder(EtchedBorder.RAISED,Color.white,new Color(178, 178, 178));
		border5 = new EtchedBorder(EtchedBorder.RAISED,Color.white,new Color(178, 178, 178));
		this.setSize(new Dimension(749, 618));
		this.getContentPane().setLayout(borderLayout1);
		mainPanel.setBorder(BorderFactory.createEtchedBorder());
		mainPanel.setLayout(gridBagLayout7);
		mainSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		mainSplitPane.setDividerSize(5);
		buttonPanel.setLayout(gridBagLayout3);
		topPlotPanel.setLayout(gridBagLayout6);
		plotSplitPane.setMinimumSize(new Dimension(545, 0));
		plotSplitPane.setDividerSize(5);
		plotSplitPane.setLastDividerLocation(500);
		buttonPanel.setBorder(border1);
		buttonPanel.setMaximumSize(new Dimension(2147483647, 25));
		buttonPanel.setMinimumSize(new Dimension(739, 25));
		buttonPanel.setPreferredSize(new Dimension(743, 25));
		topPlotPanel.setBorder(border3);
		topPlotPanel.setMinimumSize(new Dimension(467, 500));
		topPlotPanel.setPreferredSize(new Dimension(467, 500));
		// for showing the data on click of "show data" button
		pointsTextArea.setBorder( BorderFactory.createEtchedBorder() );
		pointsTextArea.setText( NO_PLOT_MSG );
		dataScrollPane.setBorder( BorderFactory.createEtchedBorder() );

		xLogCheckBox.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				xLogCheckBox_actionPerformed(e);
			}
		});
		yLogCheckBox.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				yLogCheckBox_actionPerformed(e);
			}
		});
		avgSplitPane.setPreferredSize(new Dimension(308, 480));
		avgSplitPane.setDividerSize(5);
		testCasesPanel.setLayout(gridBagLayout5);
		avgLabel.setForeground(Color.red);
		avgLabel.setHorizontalAlignment(SwingConstants.LEFT);
		avgLabel.setText("Included In Average");
		testCaseCombo.setFont(new java.awt.Font("Lucida Grande", 1, 14));
		testCaseCombo.setForeground(new Color(80, 80, 133));
		testCaseLabel.setFont(new java.awt.Font("Lucida Grande", 1, 14));
		testCaseLabel.setForeground(new Color(80, 80, 133));
		testCaseLabel.setText("Select Test Case:");
		plotPanel.setLayout(gridBagLayout2);
		testPanelLabel.setForeground(new Color(80, 80, 133));
		testPanelLabel.setMaximumSize(new Dimension(63, 18));
		testPanelLabel.setMinimumSize(new Dimension(63, 18));
		testPanelLabel.setHorizontalAlignment(SwingConstants.LEFT);
		testPanelLabel.setText("Data In Plot");
		averageCheck.setForeground(new Color(80, 80, 133));
		averageCheck.setMaximumSize(new Dimension(112, 17));
		averageCheck.setMinimumSize(new Dimension(112, 17));
		averageCheck.setPreferredSize(new Dimension(112, 17));
		averageCheck.setSelected(true);
		averageCheck.setText("Show Average");
		averageCheck.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				averageCheck_actionPerformed(e);
			}
		});
		xLogCheckBox.setForeground(new Color(80, 80, 133));
		xLogCheckBox.setMaximumSize(new Dimension(59, 17));
		xLogCheckBox.setMinimumSize(new Dimension(59, 17));
		xLogCheckBox.setPreferredSize(new Dimension(59, 17));
		yLogCheckBox.setForeground(new Color(80, 80, 133));
		yLogCheckBox.setMaximumSize(new Dimension(59, 17));
		yLogCheckBox.setMinimumSize(new Dimension(59, 17));
		yLogCheckBox.setPreferredSize(new Dimension(59, 17));
		toggleButton.setMaximumSize(new Dimension(87, 27));
		toggleButton.setMinimumSize(new Dimension(87, 27));
		toggleButton.setPreferredSize(new Dimension(87, 27));
		toggleButton.setText("Show Data");
		toggleButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				toggleButton_actionPerformed(e);
			}
		});
		guiLabel.setFont(new java.awt.Font("Dialog", 1, 12));
		guiLabel.setForeground(new Color(80, 80, 133));
		guiLabel.setToolTipText("");
		guiLabel.setHorizontalAlignment(SwingConstants.CENTER);
		guiLabel.setHorizontalTextPosition(SwingConstants.CENTER);
		guiLabel.setText("PEER PSHA-TEST RESULTS PLOTTER");
		dataVersionLabel.setForeground(new Color(80, 80, 133));
		dataVersionLabel.setHorizontalAlignment(SwingConstants.CENTER);
		dataVersionLabel.setHorizontalTextPosition(SwingConstants.CENTER);
		dataVersionLabel.setText("jLabel1");
		testCasesPanel.setMinimumSize(new Dimension(115, 37));
		testCasesPanel.setPreferredSize(new Dimension(121, 37));
		powerLabel.addMouseListener(new java.awt.event.MouseAdapter() {
			public void mouseClicked(MouseEvent e) {
				powerLabel_mouseClicked(e);
			}
		});
		powerLabel.setToolTipText("");
		powerLabel.setIcon(new ImageIcon(FileUtils.loadImage(this.POWERED_BY_IMAGE)));
		axisScaleButton.setText("Set Axis Scale");
		axisScaleButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				axisScaleButton_actionPerformed(e);
			}
		});
		dataScrollPane.getViewport().add( pointsTextArea, null );
		xLogCheckBox.setText("XLog");
		yLogCheckBox.setText("YLog");
		this.getContentPane().add(mainPanel, BorderLayout.CENTER);
		mainPanel.add(mainSplitPane,  new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, -2, 7, 0), -48, 16));
		plotSplitPane.add(topPlotPanel, JSplitPane.LEFT);

		topPlotPanel.add(testCaseLabel,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(1, 1, 0, 0), 22, 7));


		plotSplitPane.add(avgSplitPane, JSplitPane.RIGHT);
		avgSplitPane.add(avgScrollPane, JSplitPane.RIGHT);
		avgSplitPane.add(plotScrollPane, JSplitPane.LEFT);
		plotScrollPane.getViewport().add(testCasesPanel, null);
		testCasesPanel.add(testPanelLabel,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(241, 0, 245, 20), 32, 3));
		avgScrollPane.getViewport().add(avgCasesPanel, null);
		avgCasesPanel.add(avgLabel,     new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(7, 0, 10, 7), 12, 3));
		mainSplitPane.add(plotSplitPane, JSplitPane.TOP);
		buttonPanel.add(yLogCheckBox,   new GridBagConstraints(2, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
		buttonPanel.add(xLogCheckBox,    new GridBagConstraints(1, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 16, 0, 0), 0, 0));
		buttonPanel.add(averageCheck,   new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 10, 0, 0), 0, 0));
		buttonPanel.add(axisScaleButton,   new GridBagConstraints(3, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 86, 0, 0), 44, -6));
		buttonPanel.add(toggleButton,   new GridBagConstraints(4, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 49, 0, 40), 0, 0));
		mainPanel.add(guiLabel,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(-2, 267, 0, 190), 37, 10));
		mainPanel.add(dataVersionLabel,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(0, 139, 0, 171), 394, 3));
		mainPanel.add(powerLabel,  new GridBagConstraints(0, 0, GridBagConstraints.REMAINDER, GridBagConstraints.REMAINDER, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(-2, -2, 0, 0), 0, 0));
		mainSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
		mainSplitPane.setDividerLocation(420);
		plotSplitPane.setDividerLocation(475);
		avgSplitPane.setDividerLocation(140);
		avgCasesPanel.setLayout(gridBagLayout1);
		topPlotPanel.add(plotPanel,  new GridBagConstraints(0, 1, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 1, 2, 0), 462, 490));
		topPlotPanel.add(testCaseCombo,  new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(1, 0, 0, 0), 176, 0));

	}
	//Start the applet
	public void start() {
	}
	//Stop the applet
	public void stop() {
	}
	//Destroy the applet
	public void destroy() {
	}

	//Get Applet information
	public String getAppletInfo() {
		return C;
	}


	/**
	 * This function initiates test cases and files for those test cases after searching
	 * in a common directory.
	 */
	void initTestParamList(){
		// search for the test files
		searchTestFiles();
		testCaseCombo.addActionListener(this);
		addButton();
	}


	//Main method
	public static void main(String[] args) {

		PEER_TestResultsPlotterApplet applet = new PEER_TestResultsPlotterApplet();
		JOptionPane.showMessageDialog(applet,STANDALONE_WARNING,
				"Information Message",JOptionPane.INFORMATION_MESSAGE);
		applet.isStandalone = true;
		JFrame frame = new JFrame();
		//EXIT_ON_CLOSE == 3
		frame.setDefaultCloseOperation(3);
		frame.setTitle(FRAME_TITLE);
		// frame.setIconImage(ImageUtils.loadImage(FRAME_ICON_NAME));
		frame.getContentPane().add(applet, BorderLayout.CENTER);
		applet.init();
		applet.start();
		frame.setSize(W,H);
		Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
		frame.setLocation((d.width - frame.getSize().width) / 2, (d.height - frame.getSize().height) / 2);
		frame.setVisible(true);
	}

	//static initializer for setting look & feel
	static {
		try {
			UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
			//UIManager.setLookAndFeel(UIManager.getCrossPlatformLookAndFeelClassName());
		}
		catch(Exception e) {
		}
	}


	/**removes all the components from the parameter paenl, and adds them in fresh
	 * Based on the selected Test Case checkboxes are added to the panel
	 **/

	public void addButton(){
		int colorIndex=0;
		int displayIndex =1;
		//checking which test case is selected
		String testSet = this.testCaseCombo.getSelectedItem().toString();
		testCasesPanel.removeAll();
		avgCasesPanel.removeAll();
		// clear the function list
		functions.clear();
		testCasesPanel.add(testPanelLabel,   new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL, new Insets(5, 3, 0, 0), 12, 3));
		avgCasesPanel.add(avgLabel,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL, new Insets(5, 3, 0, 0), 12, 3));
		//gets the iterator for the files, so that we can extract the string as the test for the check boxes
		//for the selected test case
		Iterator it=testFiles.iterator();
		checkBoxVector= new ArrayList();
		avgCheckBoxVector = new ArrayList();
		while(it.hasNext()) {
			String tempName=it.next().toString();
			int index=tempName.indexOf("_");
			String tempStr=tempName.substring(0,index);
			if(tempStr.equalsIgnoreCase(testSet)){
				int i= tempName.indexOf(".");
				String testSubmitterName = tempName.substring(index+1,i);

				// tempName is the filename to be added
				// add this file to the function list
				DiscretizedFuncAPI func = loadFile(tempName);
				func.setName(testSubmitterName);
				functions.add(func);

				//adding the checkBoxes for the selceted test case
				JCheckBox testFilesCheck= new JCheckBox(testSubmitterName);
				JCheckBox avgTestFilesCheck= new JCheckBox(testSubmitterName);
				checkBoxVector.add(testFilesCheck);
				avgCheckBoxVector.add(avgTestFilesCheck);
				testFilesCheck.setSelected(true);
				avgTestFilesCheck.setSelected(true);
				testFilesCheck.addActionListener(this);
				avgTestFilesCheck.addActionListener(this);
				testCasesPanel.add(testFilesCheck,
						new GridBagConstraints( 0, displayIndex, 1, 1, 1.0, 1.0,
								GridBagConstraints.NORTH,
								GridBagConstraints.HORIZONTAL, defaultInsets, 0, 0 ));
				avgCasesPanel.add(avgTestFilesCheck,
						new GridBagConstraints( 0, displayIndex, 1, 1, 1.0, 1.0,
								GridBagConstraints.NORTH,
								GridBagConstraints.HORIZONTAL, defaultInsets, 0, 0 ));
				++displayIndex;
			}
		}

		int count = checkBoxVector.size();
		int numColor = legendColor.length;
		for(int j=0;j<count;j++) {
			JCheckBox checkBox=(JCheckBox)checkBoxVector.get(j);
			checkBox.setForeground(legendColor[j%numColor]);
			checkBox = (JCheckBox)avgCheckBoxVector.get(j);
			checkBox.setForeground(AVERAGE_COLOR);
		}

		if(D) System.out.println("functions:"+functions.toString());
		addGraphPanel();

	}


	/**
	 *  Adds a feature to the GraphPanel attribute of the EqkForecastApplet object
	 */
	protected void addGraphPanel() {

		// Starting
		String S = C + ": addGraphPanel(): ";
		if(D) System.out.println(S);
		int k;
		// functions needed to calculate the average
		DiscretizedFuncList avgFunctions = new DiscretizedFuncList();
		//functions for plotting
		DiscretizedFuncList plotFunctions = new DiscretizedFuncList();
		// clearing all the plots before adding them to the functionList
		clearPlot(true);


		// Determine which IM to add to the axis labeling
		String xAxisLabel = X_AXIS_TITLE;
		String yAxisLabel = Y_AXIS_TITLE;


		//create the standard ticks so that smaller values too can plotted on the chart
		TickUnits units = MyTickUnits.createStandardTickUnits();

		//checking which of the checkBoxes are selected
		int size= this.checkBoxVector.size();
		legendPaint= new Paint[size+1];

		//checking which test case is selected at the time of adding of the plot
		k=0;
		for(int i=0;i<size;i++){

			JCheckBox checkBox=(JCheckBox)checkBoxVector.get(i);
			JCheckBox avgCheckBox=(JCheckBox)avgCheckBoxVector.get(i);
			//checking if the check box is selected for the selected test case
			if(checkBox.isSelected() || avgCheckBox.isSelected()) {
				String checkText =checkBox.getText();
				int numFunc = functions.size();
				if(D) System.out.println(S+":numFunc:"+numFunc);
				//getting the correct filename to read the data from
				for(int j=0; j<numFunc; ++j) {
					DiscretizedFuncAPI func= functions.get(j);
					if (D) System.out.println(S+":checkText:"+checkText+",func.getName():"+func.getName());
					if(checkText.equalsIgnoreCase(func.getName())) {
						if(checkBox.isSelected())  {
							plotFunctions.add(func);
							legendPaint[k++]=checkBox.getForeground();
						}
						//see if the Average Check Box is selected, only then add to the functions to calc. average
						if(avgCheckBox.isSelected() && this.averageCheck.isSelected())
							avgFunctions.add(func);
					}
				}
			}
		}

		if(D) System.out.println("Plot functions:"+plotFunctions.toString());


		//see if the average checkBox is selected to calculate the average for all plotted prob's
		if(avgFunctions.size()>0)  {
			DiscretizedFunc avgFunc = FunctionListCalc.getMean(avgFunctions);
			avgFunc.setInfo("Average");
			avgFunc.setName("Average");
			plotFunctions.add(avgFunc);
			legendPaint[k++] = AVERAGE_COLOR;
		}
		// to be shown in show data
		pointsTextArea.setText(plotFunctions.toString());
		/// check if x log is selected or not
		if(xLog) xAxis = new LogarithmicAxis(xAxisLabel);
		else xAxis = new NumberAxis( xAxisLabel );

		try{
			xAxis.setAutoRangeIncludesZero( false );
			xAxis.setStandardTickUnits(units);
			xAxis.setTickMarksVisible(false);

			/// check if y log is selected or not
			if(yLog) yAxis = new LogarithmicAxis(yAxisLabel);
			else yAxis = new NumberAxis( yAxisLabel );

			yAxis.setAutoRangeIncludesZero( false );
			yAxis.setStandardTickUnits(units);
			yAxis.setTickMarksVisible(false);

			int type = StandardXYItemRenderer.LINES;


			StandardXYItemRenderer renderer = new StandardXYItemRenderer( type, new StandardXYToolTipGenerator());


			/* to set the range of the axis on the input from the user if the range combo box is selected*/
			if(this.customAxis) {
				xAxis.setRange(this.minXValue,this.maxXValue);
				yAxis.setRange(this.minYValue,this.maxYValue);
			}
			data.setFunctions(plotFunctions);
			// build the plot
			org.jfree.chart.plot.XYPlot plot
			= new org.jfree.chart.plot.XYPlot(data,
					xAxis, yAxis,renderer);


			plot.setBackgroundAlpha( .8f );
			int numSeries = legendPaint.length;
			for(int i=0; i < numSeries; ++i) renderer.setSeriesPaint(i,legendPaint[i]);
			plot.setRenderer( renderer );
			plot.setDomainCrosshairLockedOnData(false);
			plot.setDomainCrosshairVisible(false);
			plot.setRangeCrosshairLockedOnData(false);
			plot.setRangeCrosshairVisible(false);


			JFreeChart chart = new JFreeChart(JFREECHART_TITLE,JFreeChart.DEFAULT_TITLE_FONT, plot, false );

			chart.setBackgroundPaint( lightBlue );

			// chart.setBackgroundImage(image);
			// chart.setBackgroundImageAlpha(.3f);

			// Put into a panel
			chartPanel = new ChartPanel(chart, true, true, true, true, false);
			//panel.setMouseZoomable(true);

			chartPanel.setBorder( BorderFactory.createEtchedBorder( EtchedBorder.LOWERED ) );
			chartPanel.setMouseZoomable(true);
			chartPanel.setDisplayToolTips(true);
			chartPanel.setHorizontalAxisTrace(false);
			chartPanel.setVerticalAxisTrace(false);
		}catch(Exception e){
			JOptionPane.showMessageDialog(this,e.getMessage(),"Invalid Plot",JOptionPane.OK_OPTION);
			return;
		}
		graphOn = false;
		togglePlot();
	}


	/**
	 *  Description of the Method
	 */
	private void togglePlot() {


		String S= C+":drawPlot";
		plotPanel.removeAll();

		if ( graphOn ) { // if data is to be shown
			toggleButton.setText( "Show Plot" );
			graphOn = false;
			plotPanel.add( dataScrollPane, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
					, GridBagConstraints.CENTER, GridBagConstraints.BOTH, plotInsets, 0, 0 ) );
		} else { // if plot is to be shown
			toggleButton.setText( "Show Data" );
			graphOn = true;
			// panel added here
			if(chartPanel !=null)
				plotPanel.add( chartPanel, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

		}

		validate();
		repaint();

		if ( D ) System.out.println( S + "Ending" );

	}

	/**
	 * This function loads the specified file from the jar file
	 *
	 * @param fileName : filename to be loaded
	 * @return
	 */
	private DiscretizedFuncAPI loadFile(String fileName) {

		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
		try{
			// files.log contains all the files uploaded so far
			InputStream input = PEER_TestResultsPlotterApplet.class.getResourceAsStream("/"+DIR+fileName);
			DataInputStream dataStream = new DataInputStream(input);
			String line;
			// read the file line by line
			while((line=dataStream.readLine())!=null) {
				StringTokenizer st= new StringTokenizer(line);
				// put the x,y values in the function
				while(st.hasMoreTokens())
					func.set(Double.parseDouble(st.nextToken()),Double.parseDouble(st.nextToken()));
				func.setInfo(fileName);
			}
		}catch(Exception e) {
			e.printStackTrace();
		}
		// return the function
		return func;
	}


	/**
	 * This function looks for all the test cases files within the directory
	 * and stores their name in ArrayList
	 */
	private  void searchTestFiles(){
		// ArrayList is needed for the sorted list
		ArrayList testCaseList1 = new ArrayList(); // this list saves SET 1 test case from 1 to 9
		ArrayList testCaseList2 = new ArrayList(); // this list saves SET 1 test case 10 and 11
		ArrayList testCaseList3 = new ArrayList(); // this list saves SET 2 test cases
		try{
			// files.log contains all the files uploaded so far
			InputStream input = PEER_TestResultsPlotterApplet.class.getResourceAsStream("/"+DIR+"files.log");
			DataInputStream dataStream = new DataInputStream(input);
			String line;
			while((line=dataStream.readLine())!=null) {
				if(line.endsWith(FILE_EXTENSION)) testFiles.add(line);
				else continue;

				// this is needed to add a spce between test case and site
				int index=line.indexOf("_");
				String testCases = line.substring(0,index);

				boolean isTenOrEleven = false;
				boolean flag = false;
				boolean isSet2 = false;

				//check whether this is Set 2
				if(testCases.indexOf("Set2")>-1) isSet2 = true;

				// check wther this is test case 10 or 11
				if((testCases.indexOf("Case10")>-1) || (testCases.indexOf("Case11")>-1))
					isTenOrEleven = true;

				// check in list 1
				if(!isTenOrEleven && !isSet2) { // if this is case from 1 through 9
					Iterator it = testCaseList1.iterator();
					while(it.hasNext()) {
						// check whether this set has already been added to list
						if(((String)it.next()).equalsIgnoreCase(testCases)) {
							flag = true;
							break;
						}
					}
					if(!flag) testCaseList1.add(testCases);
				}

				// check in list 2 whether the case exists
				if(isTenOrEleven && !isSet2) { // if this is case 10 or 11
					Iterator it = testCaseList2.iterator();
					while(it.hasNext()) {
						// check whether this set has already been added to list
						if(((String)it.next()).equalsIgnoreCase(testCases)) {
							flag = true;
							break;
						}
					}
					if(!flag) testCaseList2.add(testCases);
				}

				// check in list 3 whether the case exists
				if(isSet2) { // if this is Set2 case
					Iterator it = testCaseList3.iterator();
					while(it.hasNext()) {
						// check whether this set has already been added to list
						if(((String)it.next()).equalsIgnoreCase(testCases)) {
							flag = true;
							break;
						}
					}
					if(!flag) testCaseList3.add(testCases);
				}
			}
			Collections.sort(testCaseList1);
			Collections.sort(testCaseList2);
			Collections.sort(testCaseList3);

			// add to the combo box
			Iterator it =  testCaseList1.iterator();
			while(it.hasNext()) testCaseCombo.addItem(it.next());
			it =  testCaseList2.iterator();
			while(it.hasNext()) testCaseCombo.addItem(it.next());
			it =  testCaseList3.iterator();
			while(it.hasNext()) testCaseCombo.addItem(it.next());


		}catch(Exception e) {
			e.printStackTrace();
		}

	}

	/**
	 * fills in the data version and data last updated
	 * This is stored in  the file data.version
	 */
	private void readDataVersion() {
		try{
			// files.log contains all the files uploaded so far
			InputStream input = PEER_TestResultsPlotterApplet.class.getResourceAsStream("/"+DIR+"data.version");
			DataInputStream dataStream = new DataInputStream(input);
			String line;
			// first line of the file saves the version number
			// second line saves the date aand time data was last updated
			dataVersion = dataStream.readLine();
			dataLastUpdated = dataStream.readLine();
		}catch(Exception e) {
			e.printStackTrace();
		}

	}

	/**
	 * whenever selection is made in the combo box
	 * @param e
	 */
	void axisScaleButton_actionPerformed(ActionEvent e) {

		if(xAxis==null || yAxis==null) {
			JOptionPane.showMessageDialog(this,AXIS_RANGE_NOT_ALLOWED);
			return;
		}

		Range rX = xAxis.getRange();
		Range rY= yAxis.getRange();
		double minX=rX.getLowerBound();
		double maxX=rX.getUpperBound();
		double minY=rY.getLowerBound();
		double maxY=rY.getUpperBound();
		if(this.customAxis) { // select the custom scale in the control window
			if(axisLimits == null) {
				axisLimits=new AxisLimitsControlPanel(this, this,
						AxisLimitsControlPanel.CUSTOM_SCALE, minX,maxX,minY,maxY);
			} else  axisLimits.setParams(AxisLimitsControlPanel.CUSTOM_SCALE,
					minX,maxX,minY,maxY);

		}
		else { // select the auto scale in the control window
			if(axisLimits == null) {
				axisLimits=new AxisLimitsControlPanel(this, this,
						AxisLimitsControlPanel.AUTO_SCALE, minX,maxX,minY,maxY);
			} else  axisLimits.setParams(AxisLimitsControlPanel.AUTO_SCALE,
					minX,maxX,minY,maxY);
		}
		if (!axisLimits.isInitialized())
			axisLimits.init();
		axisLimits.getComponent().pack();
		axisLimits.getComponent().setVisible(true);
	}

	/**
	 * sets the range for X and Y axis
	 * @param xMin : minimum value for X-axis
	 * @param xMax : maximum value for X-axis
	 * @param yMin : minimum value for Y-axis
	 * @param yMax : maximum value for Y-axis
	 */
	public void setAxisRange(double xMin,double xMax, double yMin, double yMax) {
		minXValue=xMin;
		maxXValue=xMax;
		minYValue=yMin;
		maxYValue=yMax;
		this.customAxis=true;
		addGraphPanel();
	}

	/**
	 * set the auto range for the axis. This function is called
	 * from the AxisLimitControlPanel
	 */
	public void setAutoRange() {
		this.customAxis=false;
		addGraphPanel();
	}



	/**
	 *  Clears the plot screen of all traces
	 */
	void clearPlot(boolean clearFunctions) {

		if ( D )
			System.out.println( "Clearing plot area" );

		int loc = this.plotSplitPane.getDividerLocation();
		int newLoc = loc;

		plotPanel.removeAll();

		pointsTextArea.setText( NO_PLOT_MSG );

		validate();
		repaint();
		plotSplitPane.setDividerLocation( newLoc );
	}


	/**
	 * if we select or deselect x log
	 * @param e
	 */
	void xLogCheckBox_actionPerformed(ActionEvent e) {
		xLog  = xLogCheckBox.isSelected();
		data.setXLog(xLog);
		addGraphPanel();
	}

	/**
	 * if we select or deselect y log
	 * @param e
	 */
	void yLogCheckBox_actionPerformed(ActionEvent e) {
		yLog  = yLogCheckBox.isSelected();
		data.setYLog(yLog);
		addGraphPanel();
	}

	/**Handles the ActionEvent Method for the Plot Data Checkboxes, Included  In Average
	 * Checkboxes, and when different set of test case is selected in the combo boxes.
	 */
	public void actionPerformed(ActionEvent e){
		if(e.getSource() instanceof JCheckBox) addGraphPanel();
		if(e.getSource() instanceof JComboBox) addButton();
	}

	/**
	 * This function is called each time an action is performed on the average CheckBox.
	 * @param e
	 */
	void averageCheck_actionPerformed(ActionEvent e) {
		if(this.averageCheck.isSelected()){
			avgSplitPane.add(avgScrollPane, JSplitPane.RIGHT);
			avgSplitPane.setDividerLocation(140);
		}
		else  this.avgSplitPane.setRightComponent(null);
		addGraphPanel();
	}

	/**
	 * this function is called when "show data" button is clicked
	 * @param e
	 */
	void toggleButton_actionPerformed(ActionEvent e) {
		togglePlot();
	}

	void powerLabel_mouseClicked(MouseEvent e) {
		try{
			this.getAppletContext().showDocument(new URL(OPENSHA_WEBSITE),"_opensha");
		}catch(java.net.MalformedURLException ee){
			JOptionPane.showMessageDialog(this,new String("No Internet Connection Available"),
					"Error Connecting to Internet",JOptionPane.OK_OPTION);
		}
	}
	void powerLabel_mousePressed(MouseEvent e) {

	}
	void powerLabel_mouseReleased(MouseEvent e) {

	}
	void powerLabel_mouseEntered(MouseEvent e) {

	}
	void powerLabel_mouseExited(MouseEvent e) {

	}



}
