/**
 * 
 */
package org.opensha.sha.earthquake.calc.recurInterval.gui;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.IOException;
import java.util.ArrayList;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JCheckBoxMenuItem;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.JToolBar;

import org.jfree.data.Range;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.calc.recurInterval.BPT_DistCalc;
import org.opensha.sha.earthquake.calc.recurInterval.EqkProbDistCalc;
import org.opensha.sha.earthquake.calc.recurInterval.ExponentialDistCalc;
import org.opensha.sha.earthquake.calc.recurInterval.LognormalDistCalc;
import org.opensha.sha.gui.infoTools.ButtonControlPanel;
import org.opensha.sha.gui.infoTools.ButtonControlPanelAPI;


/**
 * 
 *  This GUI will plot various probability distributions
 *  
 * @author vipingupta
 *
 */
public class ProbabilityDistGUI extends JFrame implements ButtonControlPanelAPI, 
ParameterChangeListener{
	private final static int W = 870;
	private final static int H = 750;
	private final boolean D = false;
	private JSplitPane mainSplitPane = new JSplitPane();
	private JSplitPane paramSplitPane = new JSplitPane();
	private JTabbedPane plotTabPane = new JTabbedPane();
	private JPanel editorPanel = new JPanel();
	
	// List of all plotting Panels
	private ArrayList<PlottingPanel>plottingPanelsList;
	// Name of all plotting Panels
	private ArrayList<String> plottingPanelNames;
	
	// list of all probability distribution names
	private ArrayList<EqkProbDistCalc> probDistList;
	private ArrayList<String> probDistNames;
	
	//	instance for the ButtonControlPanel
	private ButtonControlPanel buttonControlPanel;

	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private final static String POWERED_BY_IMAGE = "logos/PoweredByOpenSHA_Agua.jpg";

	private static final String PROB_DIST_PARAM_NAME = "Probability Distribution";
	private StringParameter probDistParam;


	public ProbabilityDistGUI() {
		try {
			makeProbDistList(); // list of supported probability distributions
			jbInit();
			this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		}
		catch (Exception exception) {
			exception.printStackTrace();
		}
	}

	private void jbInit() throws Exception {
		getContentPane().setLayout(new BorderLayout());
		//object for the ButtonControl Panel
		buttonControlPanel = new ButtonControlPanel(this);
		JButton addButton = new JButton();
		addButton.setText("Plot-Dist");
		addButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				addButton_actionPerformed(e);
			}
		});
		JButton peelOffButton = new JButton();
		peelOffButton.setText("Peel-Off");
		peelOffButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				peelOffButton_actionPerformed(e);
			}
		});

		JButton clearButton = new JButton();
		clearButton.setText("Clear-Plot");
		clearButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				clearButton_actionPerformed(e);
			}
		});

		JPanel buttonPanel = new JPanel();
		buttonPanel.setLayout(new FlowLayout());
		buttonPanel.add(addButton, 0);
		buttonPanel.add(clearButton, 1);
		buttonPanel.add(peelOffButton, 2);
		buttonPanel.add(buttonControlPanel, 3);
		JLabel imgLabel = new JLabel(new ImageIcon(FileUtils.loadImage(POWERED_BY_IMAGE)));

		buttonPanel.add(imgLabel, 4);

		// Menubar
		setMenuBar();
		// Toolbar
		setToolBar();
		editorPanel.setLayout(gridBagLayout1);
		// supported Prob dist
		this.initSupportedProbDistParamAndEditor();
		// show adjustable params based on selected Prob Dist
		this.showAdjParams();
		
		
		JSplitPane plotSplitPane = new JSplitPane();
		mainSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		plotSplitPane.setOrientation(JSplitPane.HORIZONTAL_SPLIT);
		


		plotSplitPane.add(plotTabPane, JSplitPane.LEFT);
		mainSplitPane.add(plotSplitPane, JSplitPane.TOP);
		plotSplitPane.add(paramSplitPane, JSplitPane.RIGHT);
		mainSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
		paramSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		paramSplitPane.setDividerLocation(100);
		paramSplitPane.add(editorPanel,JSplitPane.BOTTOM);
		this.getContentPane().add(mainSplitPane, java.awt.BorderLayout.CENTER);
		plotSplitPane.setDividerLocation(600);
		mainSplitPane.setDividerLocation(570);
		
		makePlottingPanels();
		
		for(int i=0; i<plottingPanelNames.size(); ++i)
			plotTabPane.add(plottingPanelNames.get(i), plottingPanelsList.get(i));
	
		this.setSize( W, H );
		Dimension dm = Toolkit.getDefaultToolkit().getScreenSize();
		setLocation( ( dm.width - this.getSize().width ) / 2, ( dm.height - this.getSize().height ) / 2 );
		this.setTitle("Probability Distribution Application");
		this.setVisible( true );
	}
	
	/**
	 * All plotting panels to be showed in tabbed pane
	 *
	 */
	private void makePlottingPanels() {
		plottingPanelsList = new ArrayList<PlottingPanel>();
		plottingPanelNames = new ArrayList<String>();
		int numPlottingPanels = 4;
		for(int i=0; i<numPlottingPanels; ++i)
			plottingPanelsList.add(new PlottingPanel(this.buttonControlPanel));
		plottingPanelNames.add("PDF");
		plottingPanelNames.add("CDF");
		plottingPanelNames.add("Cond Prob");
		plottingPanelNames.add("Haz Func");	
	}
	
	/**
	 * Make a list of all supported probability distributions
	 *
	 */
	private void makeProbDistList() {
		// list of all probability distribution names
		probDistList = new ArrayList<EqkProbDistCalc>();
		probDistList.add(new BPT_DistCalc());
		probDistList.add(new LognormalDistCalc());
		probDistList.add(new ExponentialDistCalc());
		
		probDistNames = new ArrayList<String>();
		for(int i=0; i<probDistList.size(); ++i)
			probDistNames.add(probDistList.get(i).getName());
	}

	private void setToolBar() {
		JToolBar jToolBar = new JToolBar();

		JButton closeButton = new JButton();
		ImageIcon closeFileImage = new ImageIcon(FileUtils.loadImage("icons/closeFile.png"));

		JButton printButton = new JButton();
		ImageIcon printFileImage = new ImageIcon(FileUtils.loadImage("icons/printFile.jpg"));

		JButton saveButton = new JButton();
		ImageIcon saveFileImage = new ImageIcon(FileUtils.loadImage("icons/saveFile.jpg"));

		closeButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent actionEvent) {
				closeButton_actionPerformed(actionEvent);
			}
		});
		printButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent actionEvent) {
				printButton_actionPerformed(actionEvent);
			}
		});
		saveButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent actionEvent) {
				saveButton_actionPerformed(actionEvent);
			}
		});

		closeButton.setIcon(closeFileImage);
		closeButton.setToolTipText("Exit Application");
		Dimension d = closeButton.getSize();
		jToolBar.add(closeButton);
		printButton.setIcon(printFileImage);
		printButton.setToolTipText("Print Graph");
		printButton.setSize(d);
		jToolBar.add(printButton);
		saveButton.setIcon(saveFileImage);
		saveButton.setToolTipText("Save Graph as image");
		saveButton.setSize(d);
		jToolBar.add(saveButton);
		jToolBar.setFloatable(false);
		this.getContentPane().add(jToolBar, BorderLayout.NORTH);
	}

	private void setMenuBar() {
		JMenuBar menuBar = new JMenuBar();
		JMenu fileMenu = new JMenu();


		JMenuItem fileExitMenu = new JMenuItem();
		JMenuItem fileSaveMenu = new JMenuItem();
		JMenuItem filePrintMenu = new JCheckBoxMenuItem();
		fileMenu.setText("File");
		fileExitMenu.setText("Exit");
		fileSaveMenu.setText("Save");
		filePrintMenu.setText("Print");

		fileExitMenu.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				fileExitMenu_actionPerformed(e);
			}
		});

		fileSaveMenu.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				fileSaveMenu_actionPerformed(e);
			}
		});

		filePrintMenu.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				filePrintMenu_actionPerformed(e);
			}
		});

		menuBar.add(fileMenu);
		fileMenu.add(fileSaveMenu);
		fileMenu.add(filePrintMenu);
		fileMenu.add(fileExitMenu);

		setJMenuBar(menuBar);
	}

	/**
	 * Shows a pick list of  supported probability distributions 
	 */
	private void initSupportedProbDistParamAndEditor() {
		probDistParam = new StringParameter(PROB_DIST_PARAM_NAME,
				this.probDistNames,
				probDistNames.get(0));
		ConstrainedStringParameterEditor probDistParamEditor = new ConstrainedStringParameterEditor(probDistParam);
		probDistParam.addParameterChangeListener(this);
		JPanel probDistSelectorPanel = new JPanel();
		probDistSelectorPanel.setLayout(gridBagLayout1);
		probDistSelectorPanel.add(probDistParamEditor,
				new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(1, 1, 1, 1), 0, 0));
		probDistSelectorPanel.validate();
		probDistSelectorPanel.repaint();
		this.paramSplitPane.add(probDistSelectorPanel,paramSplitPane.TOP);
		
	}

	  /**
	   * Show adjustable params based on selected probability distribution
	   */
	  private void showAdjParams(){
		EqkProbDistCalc selectedProbDist = getSelectedProbDist();
	    editorPanel.removeAll();
	    ParameterListEditor paramListEditor = new ParameterListEditor(selectedProbDist.getAdjParams());
	    editorPanel.add(paramListEditor,
                new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
                                       , GridBagConstraints.CENTER,
                                       GridBagConstraints.BOTH,
                                       new Insets(2, 2, 2, 2), 0, 0));
	    editorPanel.validate();
	    editorPanel.repaint();
	  }
	  
	  
	  /**
	   * Get selected BPT Dist calc
	   * 
	   * @return
	   */
	  private EqkProbDistCalc getSelectedProbDist() {
		  String selectedProbDistName = (String)probDistParam.getValue();
		  int selectedProbDistIndex = probDistNames.indexOf(selectedProbDistName);
		  EqkProbDistCalc selectedProbDist = this.probDistList.get(selectedProbDistIndex);
		  return selectedProbDist;
		  
	  }

	  /**
	  *  Adds a feature to the GraphPanel attribute of the EqkForecastApplet object
	  */
	 private void addGraphPanel() {
		 for(int i=0; i<this.plottingPanelsList.size(); ++i)
				this.plottingPanelsList.get(i).addGraphPanel();
	  }

	  //checks if the user has plot the data window or plot window
	  public void togglePlot(){
		  for(int i=0; i<this.plottingPanelsList.size(); ++i)
				this.plottingPanelsList.get(i).togglePlot();
	  }


	  /**
	   * this function is called when "Add Dist" button is clicked
	   * @param e
	   */
	  void addButton_actionPerformed(ActionEvent e) {
	     addButton();
	  }


	  /**
	   * This causes the model data to be calculated and a plot trace added to
	   * the current plot
	   *
	   * @param  e  The feature to be added to the Button_mouseClicked attribute
	   */
	  private void addButton() {

	    if (D)
	      System.out.println("Starting");

	    try {
	    	EqkProbDistCalc selectedProbDist = getSelectedProbDist();
	    	 this.plottingPanelsList.get(0).addFunc(selectedProbDist.getPDF());
	    	 this.plottingPanelsList.get(1).addFunc(selectedProbDist.getCDF());
	    	 this.plottingPanelsList.get(2).addFunc(selectedProbDist.getCondProbFunc());
	    	 this.plottingPanelsList.get(3).addFunc(selectedProbDist.getHazFunc());

	      // catch the error and display messages in case of input error
	    }
	    catch (NumberFormatException e) {
	      e.printStackTrace();
	      JOptionPane.showMessageDialog(this,
	                                    new String("Enter a Valid Numerical Value"),
	                                    "Invalid Data Entered",
	                                    JOptionPane.ERROR_MESSAGE);
	    }
	    catch (NullPointerException e) {
	      e.printStackTrace();
	      //JOptionPane.showMessageDialog(this,new String(e.getMessage()),"Data Not Entered",JOptionPane.ERROR_MESSAGE);
	      e.printStackTrace();
	    }
	    catch (Exception e) {
	      e.printStackTrace();
	      JOptionPane.showMessageDialog(this, new String(e.getMessage()),
	                                    "Invalid Data Entered",
	                                    JOptionPane.ERROR_MESSAGE);
	    }

	    if (D)
	      System.out.println("Ending");

	  }


	  /**
	   * this function is called when "clear plot" is selected
	   *
	   * @param e
	   */
	  void clearButton_actionPerformed(ActionEvent e) {
		for(int i=0; i<this.plottingPanelsList.size(); ++i)
			this.plottingPanelsList.get(i).clearPlot();
	  }

	
	  /**
	   * File | Exit action performed.
	   *
	   * @param actionEvent ActionEvent
	   */
	  private void fileSaveMenu_actionPerformed(ActionEvent actionEvent) {
	    try {
	      save();
	    }
	    catch (IOException e) {
	      JOptionPane.showMessageDialog(this, e.getMessage(), "Save File Error",
	                                    JOptionPane.OK_OPTION);
	      return;
	    }
	  }

	  /**
	   * File | Exit action performed.
	   *
	   * @param actionEvent ActionEvent
	   */
	  private void filePrintMenu_actionPerformed(ActionEvent actionEvent) {
	    print();
	  }

	  /**
	   * Opens a file chooser and gives the user an opportunity to save the chart
	   * in PNG format.
	   *
	   * @throws IOException if there is an I/O error.
	   */
	  public void save() throws IOException {
		int selectedIndex = this.plotTabPane.getSelectedIndex();
		this.plottingPanelsList.get(selectedIndex).save();
	  }

	  /**
	   * Creates a print job for the chart.
	   */
	  public void print() {
		  int selectedIndex = this.plotTabPane.getSelectedIndex();
		  this.plottingPanelsList.get(selectedIndex).print(this);
	  }


	  /**
	   * Actual method implementation of the "Peel-Off"
	   * This function peels off the window from the current plot and shows in a new
	   * window. The current plot just shows empty window.
	   */
	  private void peelOffCurves(){
		  int selectedIndex = this.plotTabPane.getSelectedIndex();
		  this.plottingPanelsList.get(selectedIndex).peelOff();
	  }


	  /**
	   * Action method to "Peel-Off" the curves graph window in a seperate window.
	   * This is called when the user presses the "Peel-Off" window.
	   * @param e
	   */
	  void peelOffButton_actionPerformed(ActionEvent e) {
	    peelOffCurves();
	  }


	  /**
	   * File | Exit action performed.
	   *
	   * @param actionEvent ActionEvent
	   */
	  private void fileExitMenu_actionPerformed(ActionEvent actionEvent) {
	    close();
	  }

	  /**
	   *
	   */
	  private void close() {
	    int option = JOptionPane.showConfirmDialog(this,
	        "Do you really want to exit the application?\n" +
	                                               "You will loose all unsaved data.",
	                                               "Exit App",
	                                               JOptionPane.OK_CANCEL_OPTION);
	    if (option == JOptionPane.OK_OPTION)
	      System.exit(0);
	  }

	  public void closeButton_actionPerformed(ActionEvent actionEvent) {
	    close();
	  }

	  public void printButton_actionPerformed(ActionEvent actionEvent) {
	    print();
	  }

	  public void saveButton_actionPerformed(ActionEvent actionEvent) {
	    try {
	      save();
	    }
	    catch (IOException e) {
	      JOptionPane.showMessageDialog(this, e.getMessage(), "Save File Error",
	                                    JOptionPane.OK_OPTION);
	      return;
	    }
	  }


	  public void parameterChange(ParameterChangeEvent event) {
	    String paramName = event.getParameterName();
	    if(paramName.equals(PROB_DIST_PARAM_NAME)){
	      this.showAdjParams();
	    }
	  }


	   /**
	    * tells the application if the xLog is selected
	    * @param xLog : boolean
	    */
	   public void setX_Log(boolean xLog) {  
		   for(int i=0; i<plottingPanelsList.size(); ++i)
			   this.plottingPanelsList.get(i).setX_Log(xLog);
	   }

	   /**
	    * tells the application if the yLog is selected
	    * @param yLog : boolean
	    */
	   public void setY_Log(boolean yLog) {
		   for(int i=0; i<plottingPanelsList.size(); ++i)
			   this.plottingPanelsList.get(i).setY_Log(yLog);
	   }

	   /**
	    * Gets the range for the X-Axis
	    * @return
	    */
	   public Range getX_AxisRange() {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
			return this.plottingPanelsList.get(selectedIndex).getX_AxisRange();	
	   }

	   /**
	    * Gets the range for the Y-Axis
	    * @return
	    */
	   public Range getY_AxisRange() {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
			return this.plottingPanelsList.get(selectedIndex).getY_AxisRange();	
	   }

	   /**
	    *
	    * @returns the plotting feature like width, color and shape type of each
	    * curve in list.
	    */
	   public ArrayList getPlottingFeatures() {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
			return this.plottingPanelsList.get(selectedIndex).getPlottingFeatures();
	   }

	   /**
	    * plots the curves with defined color,line width and shape.
	    *
	    */
	   public void plotGraphUsingPlotPreferences()  {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
		   this.plottingPanelsList.get(selectedIndex).plotGraphUsingPlotPreferences();
	   }

	   /**
	    *
	    * @returns the X Axis Label
	    */
	   public String getXAxisLabel() {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
			return this.plottingPanelsList.get(selectedIndex).getXAxisLabel();	
	   }

	   /**
	    *
	    * @returns Y Axis Label
	    */
	   public String getYAxisLabel() {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
			return this.plottingPanelsList.get(selectedIndex).getYAxisLabel();	
	   }

	   /**
	    *
	    * @returns plot Title
	    */
	   public String getPlotLabel() {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
			return this.plottingPanelsList.get(selectedIndex).getPlotTitle();	
	   }


	   /**
	    *
	    * sets  X Axis Label
	    */
	   public void setXAxisLabel(String xAxisLabel) {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
			 this.plottingPanelsList.get(selectedIndex).setXAxisLabel(xAxisLabel);
	   }

	   /**
	    *
	    * sets Y Axis Label
	    */
	   public void setYAxisLabel(String yAxisLabel) {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
		   this.plottingPanelsList.get(selectedIndex).setYAxisLabel(yAxisLabel);
		   
	   }

	   /**
	    *
	    * sets plot Title
	    */
	   public void setPlotLabel(String plotTitle) {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
			 this.plottingPanelsList.get(selectedIndex).setPlotTitle(plotTitle);
	   }
	   
	   /**
	    * sets the range for X and Y axis
	    * @param xMin : minimum value for X-axis
	    * @param xMax : maximum value for X-axis
	    * @param yMin : minimum value for Y-axis
	    * @param yMax : maximum value for Y-axis
	    *
	    */
	   public void setAxisRange(double xMin,double xMax, double yMin, double yMax) {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
			 this.plottingPanelsList.get(selectedIndex).setAxisRange(xMin, xMax, yMin, yMax);
	   }

	   /**
	    * This function sets auto range for axis
	    */
	   public void setAutoRange() {
		   int selectedIndex = this.plotTabPane.getSelectedIndex();
			 this.plottingPanelsList.get(selectedIndex).setAutoRange();
	   }
	   
	   public static void main(String[] args) {
		   ProbabilityDistGUI probDistGUI = new ProbabilityDistGUI();
		   probDistGUI.setVisible(true);
	   }

}
