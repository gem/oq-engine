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

import java.awt.Color;
import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.util.ArrayList;
import java.util.Iterator;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.metadata.XMLSaveable;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.gui.controls.CyberShakePlotFromDBControlPanel;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;

public class HazardCurvePlotCharacteristics implements XMLSaveable {
	
	public static final String XML_METADATA_NAME = "HazardCurvePlotCharacteristics";
	
	public static final String SHORT_NAME = "%s";
	public static final String LONG_NAME = "%l";
	public static final String COMBINED_NAME = "%n";
	public static final String PERIOD = "%p";
	
	public static HazardCurvePlotCharacteristics createRobPlotChars() {
		double xMin = 0;
		double xMax = 2;
		double yMin = Double.parseDouble("1.0E-6");
		double yMax = 1;
		
		boolean xLog = false;
		boolean yLog = true;
		
		HazardCurvePlotCharacteristics chars = new HazardCurvePlotCharacteristics(xMin, xMax, yMin, yMax, xLog, yLog);
		
		chars.addPeriodDependantXMax(3d, 2d);
		chars.addPeriodDependantXMax(5d, 1d);
		chars.addPeriodDependantXMax(10d, 0.5);
		
		return chars;
	}
	
	public static HazardCurvePlotCharacteristics createTomPlotChars() {
		double xMin = Double.parseDouble("1.0E-2");
		double xMax = 3;
		double yMin = Double.parseDouble("1.0E-5");
		double yMax = 0.2;
		
		boolean xLog = true;
		boolean yLog = true;
		
		HazardCurvePlotCharacteristics chars = new HazardCurvePlotCharacteristics(xMin, xMax, yMin, yMax, xLog, yLog);
		
		chars.setCyberShakeColor(Color.red);
		
		ArrayList<Color> attenRelColors = new ArrayList<Color>();
		attenRelColors.add(new Color(0, 100, 0));
		attenRelColors.add(Color.BLACK);
		attenRelColors.add(Color.YELLOW);
		attenRelColors.add(Color.GREEN);
		attenRelColors.add(Color.BLUE);
		
		chars.setAttenRelColors(attenRelColors);
		
		chars.addPeriodDependantXMax(3d, 3d);
		chars.addPeriodDependantXMax(5d, 1.5d);
		chars.addPeriodDependantXMax(10d, 1d);
		
		return chars;
	}
	
	private ArrayList<Color> attenRelColors;
	
	private double xMin = 0;
	private double xMax = 10;
	private double yMin = 0;
	private double yMax = 1;
	
	private boolean xLog = false;
	private boolean yLog = false;
	
	private boolean customAxis = true;
	
	private String title = COMBINED_NAME;
	
	private String xAxisLabel = PERIOD + "s SA (g)";
	private String yAxisLabel = "Probability Rate (1/yr)";
	
	private Color cyberShakeColor = Color.BLACK;
	
	private String cyberShakeLineType = PlotColorAndLineTypeSelectorControlPanel.LINE_AND_CIRCLES;
	
	private String attenRelLineType = PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE;
	
	private ArrayList<double[]> periodDependantXMaxes = new ArrayList<double[]>();
	
	private ArbitrarilyDiscretizedFunc hazardFunc = null;

	public HazardCurvePlotCharacteristics() {
		this.customAxis = false;
	}
	
	public HazardCurvePlotCharacteristics(double xMin, double xMax, double yMin, double yMax, boolean xLog, boolean yLog) {
		this.attenRelColors = getDefaultColors();
		
		this.customAxis = true;
		
		this.xMin = xMin;
		this.xMax = xMax;
		this.yMin = yMin;
		this.yMax = yMax;
		
		this.xLog = xLog;
		this.yLog = yLog;
		
	}
	
	public ArrayList<Color> getAttenRelColors() {
		return attenRelColors;
	}

	public void setAttenRelColors(ArrayList<Color> attenRelColors) {
		this.attenRelColors = attenRelColors;
	}
	
	private static ArrayList<Color> getDefaultColors() {
		ArrayList<Color> attenRelColors = new ArrayList<Color>();
		
		attenRelColors.add(Color.blue);
		attenRelColors.add(Color.green);
		attenRelColors.add(Color.orange);
		attenRelColors.add(Color.CYAN);
		attenRelColors.add(Color.MAGENTA);
		
		return attenRelColors;
	}
	
	public void addPeriodDependantXMax(double period, double xMax) {
		double it[] = {period, xMax};
		
		this.periodDependantXMaxes.add(it);
	}
	
	public double getXMin() {
		return xMin;
	}

	public void setXMin(double min) {
		xMin = min;
	}

	public double getXMax() {
		return xMax;
	}
	
	public double getXMax(double period) {
		int perInt = (int)(period * 100 + 0.5);
		for (double[] perMax : periodDependantXMaxes) {
			int perMatch = (int)(perMax[0] * 100 + 0.5);
			if (perInt == perMatch) {
				System.out.println("Matched xMax of " + perMax[1] + " with period=" + period);
				return perMax[1];
			}
		}
		return xMax;
	}

	public void setXMax(double max) {
		xMax = max;
	}

	public double getYMin() {
		return yMin;
	}

	public void setYMin(double min) {
		yMin = min;
	}

	public double getYMax() {
		return yMax;
	}

	public void setYMax(double max) {
		yMax = max;
	}

	public boolean isXLog() {
		return xLog;
	}

	public void setXLog(boolean log) {
		xLog = log;
	}

	public boolean isYLog() {
		return yLog;
	}

	public void setYLog(boolean log) {
		yLog = log;
	}

	public boolean isCustomAxis() {
		return customAxis;
	}

	public void setCustomAxis(boolean customAxis) {
		this.customAxis = customAxis;
	}
	
	public static String getReplacedTitle(String title, CybershakeSite site) {
		title = title.replace(COMBINED_NAME, site.getFormattedName());
		title = title.replace(SHORT_NAME, site.short_name);
		title = title.replace(LONG_NAME, site.name);
		
		return title;
	}
	
	public String getTitle() {
		return title;
	}

	public void setTitle(String title) {
		this.title = title;
	}
	
	public static String getReplacedXAxisLabel(String xAxisLabel, double period) {
		return xAxisLabel.replace(PERIOD, HazardCurvePlotter.getPeriodStr(period));
	}

	public String getXAxisLabel() {
		return xAxisLabel;
	}

	public void setXAxisLabel(String axisLabel) {
		xAxisLabel = axisLabel;
	}

	public String getYAxisLabel() {
		return yAxisLabel;
	}

	public void setYAxisLabel(String axisLabel) {
		yAxisLabel = axisLabel;
	}

	public Color getCyberShakeColor() {
		return cyberShakeColor;
	}

	public void setCyberShakeColor(Color cyberShakeColor) {
		this.cyberShakeColor = cyberShakeColor;
	}

	public String getCyberShakeLineType() {
		return cyberShakeLineType;
	}

	public void setCyberShakeLineType(String cyberShakeLineType) {
		this.cyberShakeLineType = cyberShakeLineType;
	}
	
	public String getAttenRelLineType() {
		return attenRelLineType;
	}

	public void setAttenRelLineType(String attenRelLineType) {
		this.attenRelLineType = attenRelLineType;
	}
	
	public ArbitrarilyDiscretizedFunc getHazardFunc() {
		if (hazardFunc == null)
			hazardFunc = CyberShakePlotFromDBControlPanel.createUSGS_PGA_Function();
		return hazardFunc;
	}

	public void setHazardFunc(ArbitrarilyDiscretizedFunc hazardFunc) {
		this.hazardFunc = hazardFunc;
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		String robXML = "org/opensha/sha/cybershake/conf/robPlot.xml";
		String tomXML = "org/opensha/sha/cybershake/conf/tomPlot.xml";
		
		HazardCurvePlotCharacteristics chars = createRobPlotChars();
		try {
			XMLUtils.writeObjectToXMLAsRoot(chars, robXML);
			
			chars = createTomPlotChars();
			XMLUtils.writeObjectToXMLAsRoot(chars, tomXML);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		System.exit(0);
	}
	
	

	public Element toXMLMetadata(Element root) {
		Element el = root.addElement(XML_METADATA_NAME);
		
		el.addAttribute("xMin", xMin + "");
		el.addAttribute("xMax", xMax + "");
		el.addAttribute("yMin", yMin + "");
		el.addAttribute("yMax", yMax + "");
		
		el.addAttribute("xLog", xLog + "");
		el.addAttribute("yLog", yLog + "");
		
		XMLUtils.colorToXML(el, this.getCyberShakeColor(), "CyberShakeColor");
		
		Element attenRelEl = el.addElement("AttenRelColors");
		
		for (Color color : this.getAttenRelColors()) {
			XMLUtils.colorToXML(attenRelEl, color);
		}
		
		Element periodDepXMaxEl = el.addElement("PeriodDependentXMaxes");
		
		for (double[] depMax : this.periodDependantXMaxes) {
			Element per = periodDepXMaxEl.addElement("PeriodDependentXMax");
			
			per.addAttribute("period", depMax[0] + "");
			per.addAttribute("xMax", depMax[1] + "");
		}
		
		el.addAttribute("title", this.getTitle());
		el.addAttribute("xAxisLabel", this.getXAxisLabel());
		el.addAttribute("yAxisLabel", this.getYAxisLabel());
		
		el.addAttribute("customAxis", this.isCustomAxis() + "");
		
		el.addAttribute("cyberShakeLineType", this.cyberShakeLineType);
		el.addAttribute("attenRelLineType", this.attenRelLineType);
		
		ArbitrarilyDiscretizedFunc func = this.getHazardFunc();
		
		el = func.toXMLMetadata(el);
		
		return el;
	}
	
	public static HazardCurvePlotCharacteristics fromXMLMetadata(String xmlFile) throws MalformedURLException, DocumentException {
		SAXReader reader = new SAXReader();
        Document document = reader.read(new File(xmlFile));
        
        Element el = document.getRootElement();
        
        Element charsEl = el.element(XML_METADATA_NAME);
        
        return fromXMLMetadata(charsEl);
	}
	
	public static HazardCurvePlotCharacteristics fromXMLMetadata(Element charsEl) {
		double xMin = Double.parseDouble(charsEl.attributeValue("xMin"));
		double xMax = Double.parseDouble(charsEl.attributeValue("xMax"));
		double yMin = Double.parseDouble(charsEl.attributeValue("yMin"));
		double yMax = Double.parseDouble(charsEl.attributeValue("yMax"));
		
		boolean xLog = Boolean.parseBoolean(charsEl.attributeValue("xLog"));
		boolean yLog = Boolean.parseBoolean(charsEl.attributeValue("yLog"));
		
		HazardCurvePlotCharacteristics chars = new HazardCurvePlotCharacteristics(xMin, xMax, yMin, yMax, xLog, yLog);
		
		chars.setCyberShakeColor(XMLUtils.colorFromXML(charsEl.element("CyberShakeColor")));
		
		Iterator<Element> attenRelColorsIt = charsEl.element("AttenRelColors").elementIterator();
		
		ArrayList<Color> attenRelColors = new ArrayList<Color>();
		while (attenRelColorsIt.hasNext()) {
			Element colorEl = attenRelColorsIt.next();
			attenRelColors.add(XMLUtils.colorFromXML(colorEl));
		}
		
		Iterator<Element> periodDependantXMaxesIt = charsEl.element("PeriodDependentXMaxes").elementIterator();
		
		while (periodDependantXMaxesIt.hasNext()) {
			Element perEl = periodDependantXMaxesIt.next();
			double period = Double.parseDouble(perEl.attributeValue("period"));
			double xMaxPer = Double.parseDouble(perEl.attributeValue("xMax"));
			chars.addPeriodDependantXMax(period, xMaxPer);
		}
		
		chars.setTitle(charsEl.attributeValue("title"));
		chars.setXAxisLabel(charsEl.attributeValue("xAxisLabel"));
		chars.setYAxisLabel(charsEl.attributeValue("yAxisLabel"));
		
		chars.setCyberShakeLineType(charsEl.attributeValue("cyberShakeLineType"));
		chars.setAttenRelLineType(charsEl.attributeValue("attenRelLineType"));
		
		Element funcEl = charsEl.element(ArbitrarilyDiscretizedFunc.XML_METADATA_NAME);
		
		ArbitrarilyDiscretizedFunc func = ArbitrarilyDiscretizedFunc.fromXMLMetadata(funcEl);
		
		chars.setHazardFunc(func);
		
		return chars;
	}

}
