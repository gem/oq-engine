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

package org.opensha.commons.mapping.gmt;

import java.io.Serializable;
import java.util.ArrayList;

import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.mapping.gmt.elements.CoastAttributes;
import org.opensha.commons.mapping.gmt.elements.PSXYPolygon;
import org.opensha.commons.mapping.gmt.elements.PSXYSymbol;
import org.opensha.commons.mapping.gmt.elements.PSXYSymbolSet;
import org.opensha.commons.mapping.gmt.elements.TopographicSlopeFile;
import org.opensha.commons.util.cpt.CPT;

public class GMT_Map implements Serializable {
	
	/**
	 * default serial version UID
	 */
	private static final long serialVersionUID = 1l;

	private Region region;
	
	private String cptFile = null;
	private CPT cpt = null;
	private boolean rescaleCPT = true;
	private double griddedDataInc;
	private XYZ_DataSetAPI griddedData = null;
	
	public enum HighwayFile {
		ALL			("CA All", "ca_hiwys.all.xy"),
		MAIN		("CA Main", "ca_hiwys.main.xy"),
		OTHER		("CA Other", "ca_hiwys.other.xy");
		
		private final String name;
		private final String fileName;
		HighwayFile(String name, String fileName) {
			this.name = name;
			this.fileName = fileName;
		}
		
		public String fileName() { return fileName; }
		public String description() { return name; }
	}
	private HighwayFile highwayFile = null;
	
	public static Region ca_topo_region;
	static {
//		try {
			ca_topo_region  = new Region(
					new Location(32, -126),
					new Location(43, -115));
//		} catch (RegionConstraintException e) {
//			e.printStackTrace();
//		}
	}
	private TopographicSlopeFile topoResolution = null;
	
	private CoastAttributes coast = new CoastAttributes();
	
	private double imageWidth = 6.5;
	
	private String customLabel = null;
	
	private Double customScaleMin = null;
	private Double customScaleMax = null;
	
	private int dpi = 72;
	
	private boolean useGMTSmoothing = true;
	
	private boolean logPlot = false;
	
	private String xyzFileName = GMT_MapGenerator.DEFAULT_XYZ_FILE_NAME;
	private String psFileName = GMT_MapGenerator.DEFAULT_PS_FILE_NAME;
	private String pdfFileName = GMT_MapGenerator.DEFAULT_PDF_FILE_NAME;
	private String pngFileName = GMT_MapGenerator.DEFAULT_PNG_FILE_NAME;
	private String jpgFileName = GMT_MapGenerator.DEFAULT_JPG_FILE_NAME;
	
	private String gmtScriptFileName = GMT_MapGenerator.DEFAULT_GMT_SCRIPT_NAME;
	
	private ArrayList<PSXYSymbol> xySymbols = new ArrayList<PSXYSymbol>();
	private ArrayList<PSXYPolygon> xyLines = new ArrayList<PSXYPolygon>();
	private PSXYSymbolSet xySymbolSet = null;
	
	public GMT_Map(Region region, XYZ_DataSetAPI griddedData,
			double griddedDataInc, String cptFile) {
		this.region = region;
		setGriddedData(griddedData, griddedDataInc, cptFile);
	}
	
	public GMT_Map(Region region, XYZ_DataSetAPI griddedData,
			double griddedDataInc, CPT cpt) {
		this.region = region;
		setGriddedData(griddedData, griddedDataInc, cpt);
	}
	
	/**
	 * Set the gridded XYZ dataset for this map
	 * 
	 * @param griddedData - XYZ dataset
	 * @param griddedDataInc - Degree spacing of dataset
	 * @param cptFile - CPT file
	 */
	public void setGriddedData(XYZ_DataSetAPI griddedData, double griddedDataInc, String cptFile) {
		this.griddedData = griddedData;
		this.griddedDataInc = griddedDataInc;
		this.cptFile = cptFile;
		this.cpt = null;
	}
	
	/**
	 * Set the gridded XYZ dataset for this map
	 * 
	 * @param griddedData - XYZ dataset
	 * @param griddedDataInc - Degree spacing of dataset
	 * @param cpt - CPT object
	 */
	public void setGriddedData(XYZ_DataSetAPI griddedData, double griddedDataInc, CPT cpt) {
		this.griddedData = griddedData;
		this.griddedDataInc = griddedDataInc;
		this.cptFile = null;
		this.cpt = cpt;
	}

	public Region getRegion() {
		return region;
	}

	public void setRegion(Region region) {
		this.region = region;
	}

	public String getCptFile() {
		return cptFile;
	}

	public void setCptFile(String cptFile) {
		this.cptFile = cptFile;
	}

	public CPT getCpt() {
		return cpt;
	}

	public void setCpt(CPT cpt) {
		this.cpt = cpt;
	}
	
	public boolean isRescaleCPT() {
		return rescaleCPT;
	}
	
	public void setRescaleCPT(boolean rescaleCPT) {
		this.rescaleCPT = rescaleCPT;
	}

	public double getGriddedDataInc() {
		return griddedDataInc;
	}

	public void setGriddedDataInc(double griddedDataInc) {
		this.griddedDataInc = griddedDataInc;
	}

	public XYZ_DataSetAPI getGriddedData() {
		return griddedData;
	}

	public void setGriddedData(XYZ_DataSetAPI griddedData) {
		this.griddedData = griddedData;
	}

	public HighwayFile getHighwayFile() {
		return highwayFile;
	}

	public void setHighwayFile(HighwayFile highwayFile) {
		this.highwayFile = highwayFile;
	}

	public TopographicSlopeFile getTopoResolution() {
		return topoResolution;
	}

	public void setTopoResolution(TopographicSlopeFile topoResolution) {
		this.topoResolution = topoResolution;
	}

	public CoastAttributes getCoast() {
		return coast;
	}

	public void setCoast(CoastAttributes coast) {
		this.coast = coast;
	}

	public double getImageWidth() {
		return imageWidth;
	}

	public void setImageWidth(double imageWidth) {
		this.imageWidth = imageWidth;
	}

	public String getCustomLabel() {
		return customLabel;
	}

	public void setCustomLabel(String customLabel) {
		this.customLabel = customLabel;
	}
	
	public boolean isCustomScale() {
		return customScaleMin != null && customScaleMax != null && customScaleMin < customScaleMax;
	}
	
	public void clearCustomScale() {
		customScaleMin = null;
		customScaleMax = null;
	}

	public Double getCustomScaleMin() {
		return customScaleMin;
	}

	public void setCustomScaleMin(Double customScaleMin) {
		this.customScaleMin = customScaleMin;
	}

	public Double getCustomScaleMax() {
		return customScaleMax;
	}

	public void setCustomScaleMax(Double customScaleMax) {
		this.customScaleMax = customScaleMax;
	}

	public int getDpi() {
		return dpi;
	}

	public void setDpi(int dpi) {
		this.dpi = dpi;
	}

	public boolean isUseGMTSmoothing() {
		return useGMTSmoothing;
	}

	public void setUseGMTSmoothing(boolean useGMTSmoothing) {
		this.useGMTSmoothing = useGMTSmoothing;
	}

	public boolean isLogPlot() {
		return logPlot;
	}

	public void setLogPlot(boolean logPlot) {
		this.logPlot = logPlot;
	}

	public String getXyzFileName() {
		return xyzFileName;
	}

	public void setXyzFileName(String xyzFileName) {
		this.xyzFileName = xyzFileName;
	}
	
	public String getPSFileName() {
		return psFileName;
	}

	public void setPSFileName(String psFileName) {
		this.psFileName = psFileName;
	}
	
	public String getPDFFileName() {
		return pdfFileName;
	}

	public void setPDFFileName(String psFileName) {
		this.pdfFileName = pdfFileName;
	}
	
	public String getPNGFileName() {
		return pngFileName;
	}

	public void setPNGFileName(String pngFileName) {
		this.pngFileName = pngFileName;
	}
	
	public String getJPGFileName() {
		return jpgFileName;
	}

	public void setJPGFileName(String jpgFileName) {
		this.jpgFileName = jpgFileName;
	}

	public String getGmtScriptFileName() {
		return gmtScriptFileName;
	}

	public void setGmtScriptFileName(String gmtScriptFileName) {
		this.gmtScriptFileName = gmtScriptFileName;
	}

	public ArrayList<PSXYSymbol> getSymbols() {
		return xySymbols;
	}

	public void setSymbols(ArrayList<PSXYSymbol> xySymbols) {
		this.xySymbols = xySymbols;
	}
	
	public void addSymbol(PSXYSymbol symbol) {
		this.xySymbols.add(symbol);
	}

	public ArrayList<PSXYPolygon> getPolys() {
		return xyLines;
	}

	public void setPolys(ArrayList<PSXYPolygon> xyLines) {
		this.xyLines = xyLines;
	}
	
	public void addPolys(PSXYPolygon line) {
		this.xyLines.add(line);
	}

	public PSXYSymbolSet getSymbolSet() {
		return xySymbolSet;
	}

	public void setSymbolSet(PSXYSymbolSet xySymbolSet) {
		this.xySymbolSet = xySymbolSet;
	}

}
