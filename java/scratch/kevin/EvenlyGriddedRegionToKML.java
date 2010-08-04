package scratch.kevin;

import java.io.FileWriter;
import java.io.IOException;

import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;

public class EvenlyGriddedRegionToKML {
	
	public EvenlyGriddedRegionToKML(GriddedRegion region, String fileName) throws IOException {
		FileWriter fw = new FileWriter(fileName);
		
		fw.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + "\n");
		fw.write("<kml xmlns=\"http://earth.google.com/kml/2.2\">" + "\n");
		fw.write("  <Folder>" + "\n");
		fw.write("    <name>OpenSHA Gridded Region</name>" + "\n");
		fw.write("    <description>Open Seismic Hazard Analysis Evenly Gridded Region</description>" + "\n");
		
		int numLocs = region.getNodeCount();
		for (int i=0; i<numLocs; i++) {
			Location loc = region.locationForIndex(i);
			
			fw.write("    <Placemark>" + "\n");
			
			fw.write("      <Point id=\"Loc" + i + "\">" + "\n");
			fw.write("        <coordinates>" + loc.getLongitude() + "," + loc.getLatitude() + "," + (-loc.getDepth()) + "</coordinates>" + "\n");
//			fw.write("        <latitude>" + loc.getLatitude() + "</latitude>" + "\n");
//			fw.write("        <altitude>" + (-loc.getDepth()) + "</altitude>" + "\n");
			fw.write("      </Point>" + "\n");
			
			fw.write("    </Placemark>" + "\n");
		}
		
		fw.write("  </Folder>" + "\n");
		fw.write("</kml>" + "\n");
		fw.flush();
		fw.close();
		
		System.out.println("Wrote " + numLocs + " into " + fileName);
	}
	
	public static void main(String args[]) {
		
//		LocationList corners = new LocationList();
//		corners.addLocation(new Location(34.19, -116.60));
//		corners.addLocation(new Location(35.33, -118.75));
//		corners.addLocation(new Location(34.13, -119.63));
//		corners.addLocation(new Location(33.00, -117.50));
//		GriddedRegion region = new GriddedRegion(RegionSaver.createCyberShakeRegion().getRegionOutline(), 0.108);
		GriddedRegion region = 
			new GriddedRegion(
					RegionSaver.createCyberShakeRegion().getBorder(), 
					BorderType.MERCATOR_LINEAR, 
					0.216,
					new Location(0,0));
		
		String fileName = "/var/www/kml/locs_20.kml";
		
		try {
			EvenlyGriddedRegionToKML grid2kml = new EvenlyGriddedRegionToKML(region, fileName);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

}
