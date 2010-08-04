package org.opensha.commons.data.siteData.impl;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.siteData.AbstractSiteData;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.util.FileUtils;

public class ShakeMapStableTectonicPolygons extends AbstractSiteData<Boolean> {
	
	public static final String NAME = "ShakeMap Stable Continent Regions";
	public static final String SHORT_NAME = "ShakeMapContinentRegions";
	
	public static final String CRATON_FILENAME = "data/siteData/ShakeMapTectonicPolygons/craton.txt";
	
	ArrayList<Region> polys;
	
	Region region = Region.getGlobalRegion();
	
	public ShakeMapStableTectonicPolygons() throws IOException {
		polys = loadPolygons(CRATON_FILENAME);
	}
	
	public static ArrayList<Region> loadPolygons(String fileName) throws FileNotFoundException, IOException {
		ArrayList<Region> polys = new ArrayList<Region>();
		
		ArrayList<String> lines = FileUtils.loadFile(fileName);
		
		boolean inside = false;
		LocationList locs = null;
		for (String line : lines) {
			if (line.length() == 0 || line.startsWith("#"))
				continue;
			if (inside) {
				StringTokenizer tok = new StringTokenizer(line);
				int tokens = tok.countTokens();
				if (tokens < 2 || tokens > 3)
					throw new RuntimeException("Invalid line found: " + line);
				// lat
				double lat = Double.parseDouble(tok.nextToken());
				// lon
				double lon = Double.parseDouble(tok.nextToken());
				
				Location loc = new Location(lat, lon);
				locs.add(loc);
				
				if (tokens == 2) {
					polys.add(new Region(locs, BorderType.MERCATOR_LINEAR));
					inside = false;
				}
			} else {
				if (line.startsWith("box")) {
					locs = new LocationList();
					inside = true;
					continue;
				}
			}
		}
		
		return polys;
	}

	public Region getApplicableRegion() {
		return region;
	}

	public Location getClosestDataLocation(Location loc) throws IOException {
		return loc;
	}

	public String getDataMeasurementType() {
		return TYPE_FLAG_INFERRED;
	}

	public String getDataType() {
		return "Tectonic Region Type";
	}

	public String getMetadata() {
		return "Metadata";
	}

	public String getName() {
		return NAME;
	}

	public double getResolution() {
		return 0;
	}

	public String getShortName() {
		return SHORT_NAME;
	}

	public Boolean getValue(Location loc) throws IOException {
		for (Region region : polys) {
			if (region.contains(loc))
				return true;
		}
		return false;
	}

	public boolean isValueValid(Boolean el) {
		return true;
	}
	
	public static void main(String args[]) throws IOException {
		ShakeMapStableTectonicPolygons stable = new ShakeMapStableTectonicPolygons();
		
		System.out.println(stable.getValue(new Location(34, -118)));
		System.out.println(stable.getValue(new Location(34, -80)));
	}

}
