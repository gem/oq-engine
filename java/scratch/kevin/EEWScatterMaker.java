package scratch.kevin;

import java.awt.Color;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.util.XYZHashMap;
import org.opensha.commons.util.cpt.CPT;
import org.opensha.sha.cybershake.plot.HazardMapScatterCreator;

public class EEWScatterMaker {
	
	private CPT cpt;
	private String symbol = "c";
	
	public EEWScatterMaker(CPT cpt) {
		this.cpt = cpt;
	}
	
	public void writeScript(String xyzFile, String outFile) throws FileNotFoundException, IOException {
		// really don't need to use the hash map here, but it's already set up to load these files...
		XYZHashMap xyz = new XYZHashMap(xyzFile);
		FileWriter fw = new FileWriter(outFile);
		
		ArrayList<Location> prevLocs = new ArrayList<Location>();
		
		for (Location loc : xyz.keySet()) {
			double val = xyz.get(loc);
			if (Double.isNaN(val))
				continue;
			
			// to deal with overlaps, just move the next (overlapping) one over a bit
			for (Location prev : prevLocs) {
				if (LocationUtils.linearDistance(loc, prev) < 10) {
					loc = new Location(
							loc.getLatitude(),
							loc.getLongitude() + 0.2,
							loc.getDepth());
					//loc.setLongitude(loc.getLongitude() + 0.2);
				}
			}
			prevLocs.add(loc);
			
			Color color = cpt.getColor((float) val);
			double size = 0.15;
			String colorStr = HazardMapScatterCreator.getGMTColorString(color);
			String outline = "-W" + (float)(size * 0.09) + "i,0/0/0";
			String line = "echo " + loc.getLongitude() + " " + loc.getLatitude() + " | ";
			line += "psxy $1 $2 -S" + symbol + size + "i " + colorStr + " " + outline + " -O -K >> $3";
			fw.write(line + "\n");
		}
		
		fw.close();
	}
	
	public static void main(String args[]) throws FileNotFoundException, IOException {
		String dir = "/home/kevin/SCEC/EEW/report_map/";
		
		String inprefix = dir + "converted";
		String outprefix = dir + "scatter";
		String cptFile = dir + "cptFile.cpt";
		
		CPT cpt = null;
		try {
			cpt = CPT.loadFromFile(new File(cptFile));
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(1);
		}
		
		EEWScatterMaker maker = new EEWScatterMaker(cpt);
		
		maker.writeScript(inprefix + "_1.txt", outprefix + "_1.sh");
		maker.writeScript(inprefix + "_2.txt", outprefix + "_2.sh");
		maker.writeScript(inprefix + "_3.txt", outprefix + "_3.sh");
	}

}
