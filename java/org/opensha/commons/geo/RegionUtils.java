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

package org.opensha.commons.geo;

import java.awt.Color;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

import org.apache.commons.lang.StringUtils;
import org.apache.commons.lang.SystemUtils;
import org.dom4j.Document;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import org.dom4j.Namespace;
import org.dom4j.io.OutputFormat;
import org.dom4j.io.XMLWriter;
import org.dom4j.tree.DefaultElement;

/**
 * Add comments here
 *
 * 
 * @author Peter Powers
 * @version $Id: RegionUtils.java 6594 2010-04-15 15:13:06Z pmpowers $
 * 
 */
public class RegionUtils {
	
	//private static final String FILE_NAME = "test.kml";
	
	// TODO centralize commonly used constants
	// TODO need to be able to debug regions that throw errors
	
	private static final String NL = SystemUtils.LINE_SEPARATOR;
	
	public enum Style {
		BORDER,
		BORDER_VERTEX,
		GRID_NODE;
	}
		
	// write region
	public static void regionToKML(
			Region region, String filename, Color c) {
		String kmlFileName = filename + ".kml";
		Document doc = DocumentHelper.createDocument();
		Element root = new DefaultElement(
				"kml", 
				new Namespace("", "http://www.opengis.net/kml/2.2"));
		doc.add(root);
		
		Element e_doc = root.addElement("Document");
		Element e_doc_name = e_doc.addElement("name");
		e_doc_name.addText(kmlFileName);
		
		addBorderStyle(e_doc, c);
		addBorderVertexStyle(e_doc);
		addGridNodeStyle(e_doc, c);
		
		Element e_folder = e_doc.addElement("Folder");
		Element e_folder_name = e_folder.addElement("name");
		e_folder_name.addText("region");
		Element e_open = e_folder.addElement("open");
		e_open.addText("1");
		
		addBorder(e_folder, region);
		addPoints(e_folder, "Border Nodes", region.getBorder(), 
				Style.BORDER_VERTEX);
		if (region.getInteriors() != null) {
			for (LocationList interior : region.getInteriors()) {
				addPoints(e_folder, "Interior Nodes", interior, 
						Style.BORDER_VERTEX);
			}
		}
		
		if (region instanceof GriddedRegion) {
			addPoints(e_folder, "Grid Nodes", ((GriddedRegion) 
					region).getNodeList(), Style.GRID_NODE);
		}

		// TODO absolutely need to create seom platform specific output directory
		// that is not in project space (e.g. desktop, Decs and Settings);
		
		
		String outDirName = "sha_kml/";
		File outDir = new File(outDirName);
		outDir.mkdirs();
		String tmpFile = outDirName + kmlFileName;
		
		try {
			//XMLUtils.writeDocumentToFile(tmpFile, doc);
			XMLWriter writer;
			OutputFormat format = new OutputFormat("\t", true);
			writer = new XMLWriter(new FileWriter(tmpFile), format);
			writer.write(doc);
			writer.close();
		} catch (IOException ioe) {
			ioe.printStackTrace();
		}
		//Element e = new Elem
	}
	
	// write region
	public static void locListToKML(
			LocationList locs, String filename, Color c) {
		String kmlFileName = filename + ".kml";
		Document doc = DocumentHelper.createDocument();
		Element root = new DefaultElement(
				"kml", 
				new Namespace("", "http://www.opengis.net/kml/2.2"));
		doc.add(root);
		
		Element e_doc = root.addElement("Document");
		Element e_doc_name = e_doc.addElement("name");
		e_doc_name.addText(kmlFileName);
		
		addBorderStyle(e_doc, c);
		addBorderVertexStyle(e_doc);
		addGridNodeStyle(e_doc, c);
		
		Element e_folder = e_doc.addElement("Folder");
		Element e_folder_name = e_folder.addElement("name");
		e_folder_name.addText("region");
		Element e_open = e_folder.addElement("open");
		e_open.addText("1");
		
		addLocationPoly(e_folder, locs);

		// TODO absolutely need to create seom platform specific output directory
		// that is not in project space (e.g. desktop, Decs and Settings);
		
		
		String outDirName = "sha_kml/";
		File outDir = new File(outDirName);
		outDir.mkdirs();
		String tmpFile = outDirName + kmlFileName;
		
		try {
			//XMLUtils.writeDocumentToFile(tmpFile, doc);
			XMLWriter writer;
			OutputFormat format = new OutputFormat("\t", true);
			writer = new XMLWriter(new FileWriter(tmpFile), format);
			writer.write(doc);
			writer.close();
		} catch (IOException ioe) {
			ioe.printStackTrace();
		}
		//Element e = new Elem
	}

	// border polygon
	private static Element addBorder(Element e, Region region) {
		Element e_placemark = e.addElement("Placemark");
		Element e_name = e_placemark.addElement("name");
		e_name.addText("Border");
		Element e_style = e_placemark.addElement("styleUrl");
		e_style.addText("#" + Style.BORDER.toString());
		Element e_poly = e_placemark.addElement("Polygon");
		Element e_tessellate = e_poly.addElement("tessellate");
		e_tessellate.addText("1");

		addPoly(e_poly, "outerBoundaryIs", region.getBorder());
		if (region.getInteriors() != null) {
			for (LocationList interior : region.getInteriors()) {
				addPoly(e_poly, "innerBoundaryIs", interior);
			}
		}

		return e;
	}

	// standalone location list
	private static Element addLocationPoly(Element e, LocationList locs) {
		Element e_placemark = e.addElement("Placemark");
		Element e_name = e_placemark.addElement("name");
		e_name.addText("Border");
		Element e_style = e_placemark.addElement("styleUrl");
		e_style.addText("#" + Style.BORDER.toString());
		Element e_poly = e_placemark.addElement("Polygon");
		Element e_tessellate = e_poly.addElement("tessellate");
		e_tessellate.addText("1");

		addPoly(e_poly, "outerBoundaryIs", locs);
		return e;
	}

	// create lat-lon data string
	private static Element addPoly(
			Element e,
			String polyName, 
			LocationList locations) {
		
		Element e_BI = e.addElement(polyName);
		Element e_LR = e_BI.addElement("LinearRing");
		Element e_coord = e_LR.addElement("coordinates");
		
		StringBuffer sb = new StringBuffer(NL);
		for (Location loc: locations) {
			sb.append(loc.toKML() + NL);
		}
		// region borders do not repeat the first
		// vertex, but kml closed polygons do
		sb.append(locations.get(0).toKML() + NL);
		e_coord.addText(sb.toString());
		
		return e;
	}
	
//	// create lat-lon data string
//	private static String parseBorderCoords(Region region) {
//		LocationList ll = region.getBorder();
//		StringBuffer sb = new StringBuffer(NL);
//		//System.out.println("parseBorderCoords: "); // TODO clean
//		for (Location loc: ll) {
//			sb.append(loc.toKML() + NL);
//			//System.out.println(loc.toKML()); // TODO clean
//		}
//		// region borders do not repeat the first
//		// vertex, but kml closed polygons do
//		sb.append(ll.getLocationAt(0).toKML() + NL);
//		//System.out.println("---"); // TODO clean
//		return sb.toString();
//	}
	
	// node placemarks
	private static Element addPoints(
			Element e, String folderName,
			LocationList locations, Style style) {
		Element e_folder = e.addElement("Folder");
		Element e_folder_name = e_folder.addElement("name");
		e_folder_name.addText(folderName);
		Element e_open = e_folder.addElement("open");
		e_open.addText("0");
		// loop nodes
		for (Location loc: locations) {
			Element e_placemark = e_folder.addElement("Placemark");
			Element e_style = e_placemark.addElement("styleUrl");
			e_style.addText("#" + style.toString());
			Element e_poly = e_placemark.addElement("Point");
			Element e_coord = e_poly.addElement("coordinates");
			//System.out.println(loc.toKML()); // TODO clean
			e_coord.addText(loc.toKML());
		}
		return e;
	}
	
	//<Folder>
	//	<name>region</name>
	//	<open>1</open>
	//	<Placemark>
	//		<name>test region</name>
	//		<styleUrl>#msn_ylw-pushpin</styleUrl>
	//		<Polygon>
	//			<tessellate>1</tessellate>
	//			<outerBoundaryIs>
	//				<LinearRing>
	//					<coordinates>
	//-118.494013126698,34.12890715714403,0 -118.2726369206852,34.02666906748863,0 -117.9627114364491,34.07186823617815,0 -117.9620310910423,34.2668764027905,0 -118.3264939969918,34.39919060861001,0 -118.5320559633752,34.23801999324961,0 -118.494013126698,34.12890715714403,0 </coordinates>
	//				</LinearRing>
	//			</outerBoundaryIs>
	
//    <innerBoundaryIs>
//    <LinearRing>
//      <coordinates>
//        -122.366212,37.818977,30
//        -122.365424,37.819294,30
//        -122.365704,37.819731,30
//        -122.366488,37.819402,30
//        -122.366212,37.818977,30
//      </coordinates>
//    </LinearRing>
//  </innerBoundaryIs>

	
	//		</Polygon>
	//	</Placemark>
	//	<Placemark>
	//		<LookAt>
	//			<longitude>-118.247043582626</longitude>
	//			<latitude>34.21293007086929</latitude>
	//			<altitude>0</altitude>
	//			<range>60381.34272309824</range>
	//			<tilt>0</tilt>
	//			<heading>-3.115946006858405e-08</heading>
	//			<altitudeMode>relativeToGround</altitudeMode>
	//		</LookAt>
	//		<styleUrl>#msn_placemark_circle</styleUrl>
	//		<Point>
	//			<coordinates>-118.3897877691312,34.24834787236836,0</coordinates>
	//		</Point>
	//	</Placemark>
//</Folder>
	
//    <innerBoundaryIs>
//    <LinearRing>
//      <coordinates>
//        -122.366212593918,37.81897719083808,30 
//        -122.3654241733188,37.81929450992014,30 
//        -122.3657048517827,37.81973175302663,30 
//        -122.3664882465854,37.81940249291773,30 
//        -122.366212593918,37.81897719083808,30 
//      </coordinates>
//    </LinearRing>
//  </innerBoundaryIs>


	// border style elements
	private static Element addBorderStyle(Element e, Color c) {
		Element e_style = e.addElement("Style");
		e_style.addAttribute("id", Style.BORDER.toString());
				
		// line style
		Element e_lineStyle = e_style.addElement("LineStyle");
		Element e_color = e_lineStyle.addElement("color");
		e_color.addText(colorToHex(c));
		Element e_width = e_lineStyle.addElement("width");
		e_width.addText("3");
		
		// poly style
		Element e_polyStyle = e_style.addElement("PolyStyle");
		e_polyStyle.add((Element) e_color.clone());
		Element e_fill = e_polyStyle.addElement("fill");
		e_fill.addText("0");
		
		return e;
	}
	
	// border vertex style elements
	private static Element addBorderVertexStyle(Element e) {
		Element e_style = e.addElement("Style");
		e_style.addAttribute("id", Style.BORDER_VERTEX.toString());
		
		// icon style
		Element e_iconStyle = e_style.addElement("IconStyle");
		Element e_color = e_iconStyle.addElement("color");
		e_color.addText(colorToHex(Color.RED));
		Element e_scale = e_iconStyle.addElement("scale");
		e_scale.addText("0.6");
		Element e_icon = e_iconStyle.addElement("Icon");
		Element e_href = e_icon.addElement("href");
		e_href.addText(
			"http://maps.google.com/mapfiles/kml/shapes/open-diamond.png");
		return e;
	}

	// node style elements
	private static Element addGridNodeStyle(Element e, Color c) {
		Element e_style = e.addElement("Style");
		e_style.addAttribute("id", Style.GRID_NODE.toString());
		
		// icon style
		Element e_iconStyle = e_style.addElement("IconStyle");
		Element e_color = e_iconStyle.addElement("color");
		e_color.addText(colorToHex(c));
		Element e_scale = e_iconStyle.addElement("scale");
		e_scale.addText("0.6");
		Element e_icon = e_iconStyle.addElement("Icon");
		Element e_href = e_icon.addElement("href");
		e_href.addText(
			"http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png");
		return e;
	}
	
	// converts Color to KML compatible ABGR hex value
	private static String colorToHex(Color c) {
		StringBuffer sb = new StringBuffer();
		sb.append(toHex(c.getAlpha()));
		sb.append(toHex(c.getBlue()));
		sb.append(toHex(c.getGreen()));
		sb.append(toHex(c.getRed()));
		return sb.toString();
	}
	
	// converts ints to hex values, padding single digits as necessary
	private static String toHex(int i) {
		return StringUtils.leftPad(Integer.toHexString(i), 2, '0');
	}
	
//	private String convertLocations(LocationList ll) {
//		
//	}

	public static void main(String[] args) {
		
//		// visual verification tests for GeographiRegionTest
//		Region gr;
//		
//		Location L1 = new Location(32,112);
//		Location L3 = new Location(34,118);
//		gr = new Region(L1,L3);
//		RegionUtils.regionToKML(gr, "RegionLocLoc", Color.ORANGE);
//		
		
//		GriddedRegion rect_gr = 
//			new GriddedRegion(
//					new Location(40.0,-113),
//					new Location(42.0,-117),
//					0.2,null);
//		KML.regionToKML(
//				rect_gr,
//				"RECT_REGION2",
//				Color.ORANGE);
		
//		GriddedRegion relm_gr = new CaliforniaRegions.RELM_TESTING_GRIDDED();
//		KML.regionToKML(
//				relm_gr,
//				"RELM_TESTanchor",
//				Color.ORANGE);

//		System.out.println(relm_gr.getMinLat());
//		System.out.println(relm_gr.getMinGridLat());
//		System.out.println(relm_gr.getMinLon());
//		System.out.println(relm_gr.getMinGridLon());
//		System.out.println(relm_gr.getMaxLat());
//		System.out.println(relm_gr.getMaxGridLat());
//		System.out.println(relm_gr.getMaxLon());
//		System.out.println(relm_gr.getMaxGridLon());

//		GriddedRegion eggr1 = new CaliforniaRegions.WG02_GRIDDED();
//		KML.regionToKML(
//				eggr1, 
//				"WG02anchor",
//				Color.ORANGE);

//		GriddedRegion eggr2 = new CaliforniaRegions.WG07_GRIDDED();
//		KML.regionToKML(
//				eggr2, 
//				"WG07anchor",
//				Color.ORANGE);
		
		// TODO test that borders for diff constructors end up the same.
		
		
		// test mercator/great-circle region
//		GriddedRegion eggr3 = new GriddedRegion(
//				new Location(35,-125),
//				new Location(45,-90),
//				0.5);
//		KML.regionToKML(
//				eggr3, 
//				"TEST1_box",
//				Color.ORANGE);
		
// SAUSAGE
//		LocationList ll = new LocationList();
//		ll.addLocation(new Location(35,-125));
//		ll.addLocation(new Location(38,-117));
//		ll.addLocation(new Location(37,-109));
//		ll.addLocation(new Location(41,-95));
//		
//		GriddedRegion sausage = 
//			new GriddedRegion(ll,100,0.5,null);
//		KML.regionToKML(
//				sausage,
//				"Sausage",
//				Color.ORANGE);
//
//		GriddedRegion sausageAnchor = 
//			new GriddedRegion(ll,100,0.5,new Location(0,0));
//		KML.regionToKML(
//				sausageAnchor,
//				"SausageAnchor",
//				Color.BLUE);

		
// CIRCLE
//		Location loc = new Location(35, -125);
//		GriddedRegion circle =
//				new GriddedRegion(loc, 400, 0.2, null);
//		KML.regionToKML(circle, "Circle", Color.ORANGE);
//
//		GriddedRegion circleAnchor =
//				new GriddedRegion(loc, 400, 0.2, new Location(0,0));
//		KML.regionToKML(circleAnchor, "CircleAnchor", Color.BLUE);

//		
//		GriddedRegion eggr4 = new GriddedRegion(
//				ll,BorderType.MERCATOR_LINEAR,0.5);
//		KML.regionToKML(
//				eggr4, 
//				"TEST1_loclist_lin",
//				Color.ORANGE);
//		
//		
//		GriddedRegion eggr5 = new GriddedRegion(
//				ll,BorderType.GREAT_CIRCLE,0.5);
//		KML.regionToKML(
//				eggr5, 
//				"TEST1_loclist_gc",
//				Color.ORANGE);
		

	}
}
