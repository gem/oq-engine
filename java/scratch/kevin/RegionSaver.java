package scratch.kevin;

import java.io.IOException;
import java.util.ArrayList;

import org.dom4j.Document;
import org.dom4j.Element;
import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.XMLUtils;

public class RegionSaver {
	
	public static void saveRegion(Region region, String fileName, String name) throws IOException {
		region = new Region(region.getBorder(), BorderType.MERCATOR_LINEAR);
		region.setName(name);
		
		Document doc = XMLUtils.createDocumentWithRoot();
		
		Element root = doc.getRootElement();
		
		region.toXMLMetadata(root);
		
		XMLUtils.writeDocumentToFile(fileName, doc);
		
		for (String line : (ArrayList<String>)FileUtils.loadFile(fileName)) {
			System.out.println(line);
		}
	}
	
	public static Region createCyberShakeRegion() {
		LocationList locs = new LocationList();
		
		locs.add(new Location(35.08, -118.75));
		locs.add(new Location(34.19, -116.85));
		locs.add(new Location(33.25, -117.50));
		locs.add(new Location(34.13, -119.38));
		
		return new Region(locs, BorderType.MERCATOR_LINEAR);
	}

	/**
	 * @param args
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
//		saveRegion(new RELM_CollectionRegion(), "/tmp/02_relm_coll.xml", "RELM Collection Region");
//		saveRegion(new RELM_TestingRegion(), "/tmp/01_relm_test.xml", "RELM Testing Region");
//		saveRegion(new EvenlyGriddedSoCalRegion(), "/tmp/03_so_cal.xml", "Southern California Region");
//		saveRegion(new EvenlyGriddedNoCalRegion(), "/tmp/04_nor_cal.xml", "Northern California Region");
		
		saveRegion(new CaliforniaRegions.RELM_COLLECTION_GRIDDED(), "/tmp/02_relm_coll.xml", "RELM Collection Region");
		saveRegion(new CaliforniaRegions.RELM_TESTING(), "/tmp/01_relm_test.xml", "RELM Testing Region");
		saveRegion(new CaliforniaRegions.RELM_SOCAL_GRIDDED(), "/tmp/03_so_cal.xml", "Southern California Region");
		saveRegion(new CaliforniaRegions.RELM_NOCAL_GRIDDED(), "/tmp/04_nor_cal.xml", "Northern California Region");

		saveRegion(createCyberShakeRegion(), "/tmp/05_cybershake.xml", "CyberShake Map Region");
	}
}
