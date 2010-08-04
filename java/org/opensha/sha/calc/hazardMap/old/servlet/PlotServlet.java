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

package org.opensha.sha.calc.hazardMap.old.servlet;

import java.io.File;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.MalformedURLException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.dom4j.Attribute;
import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.opensha.commons.data.ArbDiscretizedXYZ_DataSet;
import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.gridComputing.StorageHost;
import org.opensha.commons.mapping.gmt.GMT_Map;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.commons.mapping.servlet.GMT_MapGeneratorServlet;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.hazardMap.MakeXYZFromHazardMapDir;

public class PlotServlet extends ConfLoadingServlet {
	
	public static final String XYZ_FILES_DIR = "/scratch/opensha/xyzDatasets/";
//	public static final String XYZ_FILES_DIR = "/home/scec-01/opensha/xyzDatasets/";
	
	public static final String OP_PLOT = "Plot";
	public static final String OP_RETRIEVE = "Retrieve Data";
	
	public static final String PLOT_OVERWRITE_ALWAYS = "Always Overwrite";
	public static final String PLOT_OVERWRITE_NEVER = "Never Overwrite";
	public static final String PLOT_OVERWRITE_IF_INCOMPLETE = "Overwrite if Incomplete";
	
	private GMT_MapGenerator gmt;
	
	/**
	 * Servlet for plotting and retrieving Hazard Map data
	 * 
	 * Object flow:
	 * Client ==> Server:
	 * * Dataset ID (String)
	 * * operation (String)
	 * * isProbAt_IML (Boolean)
	 * * level (Double)
	 * * overwrite setting (String from PLOT_OVERWRITE_*)
	 * * If Map:
	 * ** map specification (GMT_Map)
	 * Server ==> Client:
	 * * If Map:
	 * ** Map url
	 * * Else:
	 * ** XYZ dataset (XYZ_DataSetAPI)
	 */
	public PlotServlet() {
		super("PlotServlet");
		gmt = new GMT_MapGenerator();
	}

	@Override
	public void doGet(HttpServletRequest request, HttpServletResponse response)
			throws ServletException, IOException {
		debug("Handling GET");
		
		// get an input stream from the applet
		ObjectInputStream in = new ObjectInputStream(request.getInputStream());
		ObjectOutputStream out = new ObjectOutputStream(response.getOutputStream());
		
		try {
			String id = (String)in.readObject();
			String op = (String)in.readObject();
			
			boolean isProbAt_IML = (Boolean)in.readObject();
			double level = (Double)in.readObject();
			
			String overwriteMode = (String)in.readObject();
			boolean isOverwriteAlways = overwriteMode.equals(PLOT_OVERWRITE_ALWAYS);
			boolean isOverwriteNever = overwriteMode.equals(PLOT_OVERWRITE_NEVER);
			
			GMT_Map map = null;
			
			if (op.equals(OP_PLOT)) {
				map = (GMT_Map)in.readObject();
			}
			
			String xyzDir = XYZ_FILES_DIR + id;
			File xyzDirFile = new File(xyzDir);
			
			try {
				if (!xyzDirFile.exists())
					if (!xyzDirFile.mkdir())
						fail(out, "Couldn't make directory for xyz files!");
				
				StorageHost storage = this.confLoader.getPresets().getStorageHosts().get(0);
				
				String curveDirName = storage.getPath() + File.separator + id + File.separator + "curves";
				File curveDirFile = new File(curveDirName);
				if (!curveDirFile.exists())
					fail(out, "Couldn't find curves for dataset '" + id + "'");
				
				String curveXYZFile = xyzDir + File.separator + "xyzCurves";
				if (isProbAt_IML)
					curveXYZFile += "_PROB";
				else
					curveXYZFile += "_IML";
				curveXYZFile += "_" + level + ".txt";
				
				File curveXYZFileFile = new File(curveXYZFile);
				XYZ_DataSetAPI xyz = null;
				MakeXYZFromHazardMapDir maker = null;
				if (!curveXYZFileFile.exists() || isOverwriteAlways) {
					maker = new MakeXYZFromHazardMapDir(curveDirName, false, true);
				} else {
					xyz = ArbDiscretizedXYZ_DataSet.loadXYZFile(curveXYZFile);
					if (!isOverwriteNever) {
						// if we're here then it's an overwrite if needed.
						String xmlFile = storage.getPath() + File.separator + id + File.separator + id + ".xml";
						int num = getNumPointsFromXML(xmlFile);
						if (num <= 0 || num > xyz.getX_DataSet().size()) {
							debug("Incomplete dataset...regenerating XYZ file! " +
									"(have " + xyz.getX_DataSet().size() + " expecting " + num + ")");
							maker = new MakeXYZFromHazardMapDir(curveDirName, false, true);
						}
					}
				}
				
				if (maker != null) // this means we don't have a dataset or we are overwriting it
					xyz = maker.getXYZDataset(isProbAt_IML, level, curveXYZFile);
				
				if (map == null) {
					// they just want the data, no plot
					out.writeObject(xyz);
					out.close();
					return;
				}
				// if we made it this far, then we're making a map!
				map.setGriddedData(xyz);
				
				String url = GMT_MapGeneratorServlet.createMap(gmt, map, null, "", "metadata.txt");
				
				out.writeObject(url);
				out.close();
			} catch (Exception e) {
				e.printStackTrace();
				fail(out, e);
			}
		} catch (ClassNotFoundException e) {
			fail(out, "ClassNotFoundException: " + e.getMessage());
			return;
		}
	}
	
	private int getNumPointsFromXML(String xmlFile) {
		try {
			Document doc = XMLUtils.loadDocument(xmlFile);
			Element root = doc.getRootElement();
			
			Element regionEl = root.element(GriddedRegion.XML_METADATA_NAME);
			Attribute numAtt = regionEl.attribute(GriddedRegion.XML_METADATA_NUM_POINTS_NAME);
			
			if (numAtt != null)
				return Integer.parseInt(numAtt.getValue());
			
			GriddedRegion region = GriddedRegion.fromXMLMetadata(regionEl);
			return region.getNodeCount();
		} catch (MalformedURLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			return -1;
		} catch (DocumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			return -1;
		}
	}

}
