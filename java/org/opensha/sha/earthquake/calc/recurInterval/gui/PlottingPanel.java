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

package org.opensha.sha.earthquake.calc.recurInterval.gui;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.io.IOException;
import java.util.ArrayList;

import javax.swing.JFrame;
import javax.swing.JPanel;

import org.jfree.data.Range;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.gui.infoTools.ButtonControlPanel;
import org.opensha.sha.gui.infoTools.GraphPanel;
import org.opensha.sha.gui.infoTools.GraphPanelAPI;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;


/**
 * It represents a tab in each tabbed pane of the Probability Dist GUI
 * 
 * @author vipingupta
 *
 */
public class PlottingPanel extends JPanel implements GraphPanelAPI, GraphWindowAPI {
	
	private GraphPanel graphPanel;
	private String xAxisName, yAxisName;
	private boolean xLog, yLog,  isCustomAxis;
	private double minX, maxX, minY, maxY;
	private ArrayList funcList;
	//	instance for the ButtonControlPanel
	private ButtonControlPanel buttonControlPanel;
	private String plotTitle;
	
	public PlottingPanel(ButtonControlPanel buttonControlPanel) {
		this.setLayout(new GridBagLayout());
		this.buttonControlPanel = buttonControlPanel;
		funcList = new ArrayList();
		graphPanel = new GraphPanel(this);
		this.add(graphPanel, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
				  , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));

	}
	
	
	/**
	 * Set custom axis range for this plot
	 * @param xMin
	 * @param xMax
	 * @param yMin
	 * @param yMax
	 */
	  public void setAxisRange(double xMin, double xMax, double yMin, double yMax) {   
	      this.minX = xMin;
	      this.maxX = xMax;
	      this.minY = yMin;
	      this.maxY = yMax;
	      this.isCustomAxis=true;
	      this.addGraphPanel();
	  }

	  /**
	   * Set Auto Range for this plot
	   *
	   */
	  public void setAutoRange() {
	      isCustomAxis=false;
	      this.addGraphPanel();
	  }

	  /**
	   * Set X Log
	   * @param xLog
	   */
	  public void setX_Log(boolean xLog) {
	    this.xLog = xLog;
	    this.addGraphPanel();
	  }
	  
	  
	  /**
	   * Set Y Log
	   * 
	   * @param yLog
	   */
	  public void setY_Log(boolean yLog) {
	    this.yLog = yLog;
	    this.addGraphPanel();
	  }

	  /**
	   * Add Graph Panel
	   *
	   */
	  public void addGraphPanel() {
		  this.graphPanel.drawGraphPanel(this.xAxisName,yAxisName,
                  this.funcList,xLog,yLog,this.isCustomAxis,
                  plotTitle, buttonControlPanel);
		  graphPanel.togglePlot(buttonControlPanel);
		  graphPanel.validate();
		  graphPanel.repaint();
	  }
	  
	  
	  public void setPlotTitle(String plotTitle) {
		  this.plotTitle = plotTitle;
	  }
	  
	  public String getPlotTitle() {
		  return this.plotTitle;
	  }
	  
	  public Range getX_AxisRange() {
		  return graphPanel.getX_AxisRange();
	   
	  }

	  public Range getY_AxisRange() {
	      return graphPanel.getY_AxisRange();
	  }

	  public ArrayList getPlottingFeatures() {
	      return graphPanel.getCurvePlottingCharacterstic();
	  }

	  public void plotGraphUsingPlotPreferences() {
		  this.clearPlot();
		  this.addGraphPanel();
	  }

	  public String getXAxisLabel() {
	    return this.xAxisName;
	  }

	  public String getYAxisLabel() {
	   return this.yAxisName;
	  }

	  public void setXAxisLabel(String xAxisLabel) {
	    this.xAxisName = xAxisLabel;
	  }

	  public void setYAxisLabel(String yAxisLabel) {
	   this.yAxisName = yAxisLabel;

	  }

	  public ArrayList getCurveFunctionList() {
	    return this.funcList;

	  }

	  public boolean getXLog() {
	    return xLog;
	  }

	  public boolean getYLog() {
	    return yLog;
	  }

	  public boolean isCustomAxis() {
		  return this.isCustomAxis;
	  }
	
	  /**
	   *
	   * @returns the Min X-Axis Range Value, if custom Axis is choosen
	   */
	  public double getMinX() {
	    return this.minX;
	  }

	  /**
	   *
	   * @returns the Max X-Axis Range Value, if custom axis is choosen
	   */
	  public double getMaxX() {
	    return this.maxX;
	  }

	  /**
	   *
	   * @returns the Min Y-Axis Range Value, if custom axis is choosen
	   */
	  public double getMinY() {
	    return this.minY;
	  }

	  /**
	   *
	   * @returns the Max X-Axis Range Value, if custom axis is choosen
	   */
	  public double getMaxY() {
	   return this.maxY;
	  }
	  
	  public void save() {
		  try {
			this.graphPanel.save();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	  }
	  
	  public void print(JFrame frame) {
		  this.graphPanel.print(frame);
	  }

	  public void peelOff() {
		  GraphWindow graphWindow = new GraphWindow(this);
		  graphWindow.setVisible(true);
	  }
	  
	  public void clearPlot() {
		  this.graphPanel.removeChartAndMetadata();
		  this.funcList.clear();
		  this.isCustomAxis = false;
		  graphPanel.validate();
		  graphPanel.repaint();
	  }
	  
	  public void togglePlot() {
		  this.removeAll();
		  this.graphPanel.togglePlot(this.buttonControlPanel);
		  this.add(graphPanel, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
				  , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		  this.validate();
		  this.repaint();
	  }
	  
	  /**
	   * Add a function to the list of functions to be plotted
	   * 
	   * @param func
	   */
	  public void addFunc(DiscretizedFuncAPI func) {
		  funcList.add(func);
		  this.addGraphPanel();
	  }
}
