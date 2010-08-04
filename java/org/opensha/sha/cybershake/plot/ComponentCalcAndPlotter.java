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

package org.opensha.sha.cybershake.plot;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;

import org.jfree.chart.ChartUtilities;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.cybershake.db.CybershakeIM;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.HazardCurve2DB;
import org.opensha.sha.cybershake.db.HazardCurveComputation;
import org.opensha.sha.cybershake.db.Runs2DB;
import org.opensha.sha.cybershake.db.SiteInfo2DB;
import org.opensha.sha.gui.controls.CyberShakePlotFromDBControlPanel;
import org.opensha.sha.gui.infoTools.GraphPanel;
import org.opensha.sha.gui.infoTools.GraphPanelAPI;
import org.opensha.sha.gui.infoTools.PlotControllerAPI;

public class ComponentCalcAndPlotter implements GraphPanelAPI, PlotControllerAPI {
	
	public static final boolean SKIP_EXISTING_CURVES = true;
	
	private CybershakeIM mean3sec;
	private CybershakeIM x3sec;
	private CybershakeIM y3sec;
	
	private HazardCurveComputation curveCalc;
	private SiteInfo2DB sites2db;
	private Runs2DB runs2db;
	
	private ArrayList<Double> imlVals = new ArrayList<Double>();
	
	private GraphPanel gp;
	
	public ComponentCalcAndPlotter(DBAccess db) {
		curveCalc = new HazardCurveComputation(db);
		sites2db = new SiteInfo2DB(db);
		runs2db = new Runs2DB(db);
		
		HazardCurve2DB hc2db = new HazardCurve2DB(db);
		mean3sec = hc2db.getIMFromID(21);
		x3sec = hc2db.getIMFromID(48);
		y3sec = hc2db.getIMFromID(75);
		
		gp = new GraphPanel(this);
		
		ArbitrarilyDiscretizedFunc func = CyberShakePlotFromDBControlPanel.createUSGS_PGA_Function();
		imlVals = new ArrayList<Double>();
		for (int i=0; i<func.getNum(); i++) {
			imlVals.add(func.getX(i));
		}
	}
	
	public void calc(String shortName, String dir) throws IOException {
		CybershakeSite site = sites2db.getSiteFromDB(shortName);
		if (site == null)
			throw new IllegalArgumentException("Site '" + shortName + "' doesn't exist!");
		System.out.println("Detected site ID '" + site.id + "' from short name '" + shortName + "'");
		
		ArrayList<Integer> runs = runs2db.getRunIDs(site.id);
		if (runs == null || runs.size() == 0)
			throw new RuntimeException("No runs exist for site '" + shortName + "'");
		int runID = runs.get(0);
		System.out.println("Detected run ID '" + runID + "' from short name '" + shortName + "'");
		
		if (!dir.endsWith(File.separator))
			dir += File.separator;
		
		
		File meanFile = new File(dir + shortName + "_3sec_mean.txt");
		DiscretizedFuncAPI meanCurve;
		if (meanFile.exists() && SKIP_EXISTING_CURVES) {
			System.out.println(meanFile.getName() + " already exists...skipping calculation!");
			meanCurve = ArbitrarilyDiscretizedFunc.loadFuncFromSimpleFile(meanFile.getAbsolutePath());
		} else {
			meanCurve = curveCalc.computeHazardCurve(imlVals, runID, mean3sec);
			ArbitrarilyDiscretizedFunc.writeSimpleFuncFile(meanCurve, meanFile.getAbsolutePath());
		}
		
		File xFile = new File(dir + shortName + "_3sec_X.txt");
		DiscretizedFuncAPI xCurve;
		if (xFile.exists() && SKIP_EXISTING_CURVES) {
			System.out.println(xFile.getName() + " already exists...skipping calculation!");
			xCurve = ArbitrarilyDiscretizedFunc.loadFuncFromSimpleFile(xFile.getAbsolutePath());
		} else {
			xCurve = curveCalc.computeHazardCurve(imlVals, runID, x3sec);
			ArbitrarilyDiscretizedFunc.writeSimpleFuncFile(xCurve, xFile.getAbsolutePath());
		}
		
		File yFile = new File(dir + shortName + "_3sec_Y.txt");
		DiscretizedFuncAPI yCurve;
		if (yFile.exists() && SKIP_EXISTING_CURVES) {
			System.out.println(yFile.getName() + " already exists...skipping calculation!");
			yCurve = ArbitrarilyDiscretizedFunc.loadFuncFromSimpleFile(yFile.getAbsolutePath());
		} else {
			yCurve = curveCalc.computeHazardCurve(imlVals, runID, y3sec);
			ArbitrarilyDiscretizedFunc.writeSimpleFuncFile(yCurve, yFile.getAbsolutePath());
		}
		
		ArrayList<DiscretizedFuncAPI> curves = new ArrayList<DiscretizedFuncAPI>();
		curves.add(meanCurve);
		curves.add(xCurve);
		curves.add(yCurve);
		
		boolean xLog = false;
		boolean yLog = true;
		
		boolean customAxis = true;
		
		String title = shortName + " CyberShake Curves";
		
		this.gp.drawGraphPanel("3s SA", "Probability Rate (1/yr)", curves, xLog, yLog, customAxis, title, this);
		this.gp.setVisible(true);
		
		this.gp.togglePlot(null);
		
		this.gp.validate();
		this.gp.repaint();
		
		String outFile = dir + shortName + "_curves.png";
		System.out.println("Saving PNG to: " + outFile);
		ChartUtilities.saveChartAsPNG(new File(outFile), gp.getCartPanel().getChart(), 600, 500);
	}

	/**
	 * @param args
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
		ComponentCalcAndPlotter plotter = new ComponentCalcAndPlotter(Cybershake_OpenSHA_DBApplication.db);
		plotter.calc("s724", "/home/kevin/CyberShake/singleComponentCurves");
		plotter.calc("s726", "/home/kevin/CyberShake/singleComponentCurves");
		plotter.calc("s768", "/home/kevin/CyberShake/singleComponentCurves");
		plotter.calc("s770", "/home/kevin/CyberShake/singleComponentCurves");
		
		System.exit(0);
	}

	public double getMaxX() {
		return 2;
	}

	public double getMaxY() {
		return 1;
	}

	public double getMinX() {
		return 0;
	}

	public double getMinY() {
		return Double.parseDouble("1.0E-6");
	}

	public int getAxisLabelFontSize() {
		return 12;
	}

	public int getPlotLabelFontSize() {
		return 14;
	}

	public int getTickLabelFontSize() {
		return 12;
	}

	public void setXLog(boolean flag) {
		// TODO Auto-generated method stub
		
	}

	public void setYLog(boolean flag) {
		// TODO Auto-generated method stub
		
	}

}
