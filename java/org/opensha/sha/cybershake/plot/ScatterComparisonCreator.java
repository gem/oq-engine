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

import java.awt.Font;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import javax.imageio.ImageIO;

import org.jfree.chart.ChartFactory;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.annotations.XYTextAnnotation;
import org.jfree.chart.axis.NumberTickUnit;
import org.jfree.chart.axis.TickUnit;
import org.jfree.chart.axis.TickUnits;
import org.jfree.chart.axis.ValueAxis;
import org.jfree.chart.plot.PlotOrientation;
import org.jfree.chart.plot.XYPlot;
import org.jfree.data.xy.XYSeries;
import org.jfree.data.xy.XYSeriesCollection;
import org.jfree.ui.TextAnchor;
import org.opensha.commons.util.XYZClosestPointFinder;
import org.opensha.sha.cybershake.HazardCurveFetcher;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;

public class ScatterComparisonCreator {
	
	HazardCurveFetcher fetcher;
	
	ArrayList<CybershakeSite> sites;
	
	Font labelFont = new Font("Label", Font.PLAIN, 12);
	
	ArrayList<XYTextAnnotation> annotations = new ArrayList<XYTextAnnotation>();
	
	public ScatterComparisonCreator(DBAccess db, ArrayList<Integer> erfIDs, int rupVarScenarioID, int sgtVarID, int imTypeID) {
		fetcher = new HazardCurveFetcher(db, erfIDs, rupVarScenarioID, sgtVarID, imTypeID);
		sites = fetcher.getCurveSites();
	}
	
	public void writeScatterFile(boolean isProbAt_IML, double val, ArrayList<Double> comparisonVals, String fileName) throws IOException {
		ArrayList<Double> vals = fetcher.getSiteValues(isProbAt_IML, val);
		
		if (vals.size() != comparisonVals.size())
			throw new RuntimeException("Value and Comparison Value sizes must be equal!");
		
		FileWriter fw = new FileWriter(fileName);
		
		for (int i=0; i<vals.size(); i++) {
			double x = comparisonVals.get(i);
			double y = vals.get(i);
			String name = sites.get(i).short_name;
			
			fw.write(x + "\t" + y + "\t" + name + "\n");
		}
		
		fw.close();
	}
	
	public XYSeries getSeries(boolean isProbAt_IML, double val, ArrayList<Double> comparisonVals, String name) {
		ArrayList<Double> vals = fetcher.getSiteValues(isProbAt_IML, val);
		
		XYSeries series = new XYSeries(name);
		
		if (vals.size() != comparisonVals.size())
			throw new RuntimeException("Value and Comparison Value sizes must be equal!");
		System.out.println("Series: " + name);
		for (int i=0; i<vals.size(); i++) {
			double x = comparisonVals.get(i);
			double y = vals.get(i);
			annotations.add(makeAnnotation(sites.get(i).short_name, x, y));
			series.add(x, y);
			System.out.println(x + "\t" + y);
		}
		
		return series;
	}
	
	public JFreeChart getChart(String title, String xLabel, String yLabel, ArrayList<XYSeries> series) {
		XYSeriesCollection dataset = new XYSeriesCollection();
		
		for (XYSeries theSeries : series) {
			dataset.addSeries(theSeries);
		}
		
		boolean legend = true;
		boolean tooltips = true;
		boolean urls = false;
		
		JFreeChart chart = ChartFactory.createScatterPlot(title, xLabel, yLabel, dataset, PlotOrientation.VERTICAL, legend, tooltips, urls);
		XYPlot plot = chart.getXYPlot();
		for (XYTextAnnotation annotation : annotations) {
			plot.addAnnotation(annotation);
		}
		annotations.clear();
		setupAxis(plot, 1.6, 1.6);
		
		return chart;
	}
	
	private XYTextAnnotation makeAnnotation(String text, double x, double y) {
		XYTextAnnotation annotation = new XYTextAnnotation(text, x, y);
		annotation.setTextAnchor(TextAnchor.BASELINE_LEFT);
		annotation.setFont(labelFont);
		
		return annotation;
	}
	
	private void setupAxis(XYPlot plot, double xMax, double yMax) {
		ValueAxis xAxis = plot.getDomainAxis();
		ValueAxis yAxis = plot.getRangeAxis();
		xAxis.setAutoRange(false);
		yAxis.setAutoRange(false);
//		xAxis.setAutoTickUnitSelection(false);
//		yAxis.setAutoTickUnitSelection(false);
		
		TickUnits tus = new TickUnits();
		TickUnit tu = new NumberTickUnit(0.2);
		tus.add(tu);
		
		xAxis.setStandardTickUnits(tus);
		yAxis.setStandardTickUnits(tus);
		
		xAxis.setRange(0, xMax);
		yAxis.setRange(0, yMax);
	}
	
	
	
	public void saveChartPNG(JFreeChart chart, int width, int height, String fileName) throws IOException {
		BufferedImage image = chart.createBufferedImage(width, height);
		ImageIO.write(image, "png", new File(fileName));
	}
	
	public ArrayList<Double> getComparisonValsFromXYZ(String xyzFile) throws FileNotFoundException, IOException {
		ArrayList<Double> vals = new ArrayList<Double>();
		
		XYZClosestPointFinder close = new XYZClosestPointFinder(xyzFile);
		
		for (CybershakeSite site : sites) {
			double val = close.getClosestVal(site.lat, site.lon);
			vals.add(val);
		}
		
		return vals;
	}
	
	public static void main(String args[]) {
		DBAccess db = Cybershake_OpenSHA_DBApplication.db;
		
		int rupVarScenID = 3;
		int sgtVarID = 5;
		int imTypeID = 21;
		
		boolean isProbAt_IML = false;
		double val = 0.0;
		
		System.out.println("Creating Scatter Creator");
		ArrayList<Integer> erfIDs = new ArrayList<Integer>();
		erfIDs.add(34);
		erfIDs.add(35);
		ScatterComparisonCreator creator = new ScatterComparisonCreator(db, erfIDs, rupVarScenID, sgtVarID, imTypeID);
		
		boolean two = true;
		boolean ten = false;
		
		String nameAdd = "";
		
		if (two)
			nameAdd += "_2";
		if (ten)
			nameAdd += "_10";
		
		ArrayList<Double> comparisonVals;
		try {
			// CB 2008
			System.out.println("Getting Comparison Values");
			
			System.out.println("Creating Chart");
			ArrayList<XYSeries> series = new ArrayList<XYSeries>();
			XYSeries xy2;
			XYSeries xy10;
			if (two) {
				val = 0.0004;
				comparisonVals = creator.getComparisonValsFromXYZ("/home/kevin/CyberShake/scatterMap/base_cb.txt");
				xy2 = creator.getSeries(isProbAt_IML, val, comparisonVals, "2% in 50 yrs");
				
				series.add(xy2);
			}
			if (ten) {
				val = 0.002;
				comparisonVals = creator.getComparisonValsFromXYZ("/home/kevin/CyberShake/baseMaps/cb2008/xyzCurves_IML_0.002.txt");
				xy10 = creator.getSeries(isProbAt_IML, val, comparisonVals, "10% in 50 yrs");

				series.add(xy10);
			}
			
			JFreeChart chart = creator.getChart("3-Sec SA", "Campbell & Bozorgnia 2008", "CyberShake", series);
			
			String outFile = "/home/kevin/CyberShake/scatterPlot/cb_scatter_plot" + nameAdd + ".png";
			
			System.out.println("Saving Chart");
			creator.saveChartPNG(chart, 800, 800, outFile);
			
			// BA 2008
			System.out.println("Getting Comparison Values");
			
			System.out.println("Creating Chart");
			series = new ArrayList<XYSeries>();
			if (two) {
				val = 0.0004;
				comparisonVals = creator.getComparisonValsFromXYZ("/home/kevin/CyberShake/scatterMap/base_ba.txt");
				xy2 = creator.getSeries(isProbAt_IML, val, comparisonVals, "2% in 50 yrs");

				series.add(xy2);
			}
			if (ten) {
				val = 0.002;
				comparisonVals = creator.getComparisonValsFromXYZ("/home/kevin/CyberShake/baseMaps/ba2008/xyzCurves_IML_0.002.txt");
				xy10 = creator.getSeries(isProbAt_IML, val, comparisonVals, "10% in 50 yrs");

				series.add(xy10);
			}
			
			chart = creator.getChart("3-Sec SA", "Boore & Atkinson 2008", "CyberShake", series);
			
			outFile = "/home/kevin/CyberShake/scatterPlot/ba_scatter_plot" + nameAdd + ".png";
			
			System.out.println("Saving Chart");
			creator.saveChartPNG(chart, 800, 800, outFile);
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		System.out.println("Done");
		System.exit(0);
	}

}
