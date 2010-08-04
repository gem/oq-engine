package scratch.kevin;

import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.siteData.impl.WaldAllenGlobalVs30;
import org.opensha.commons.data.siteData.impl.WillsMap2006;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.util.SiteTranslator;

public class CensusVs30Gen {
	
	private static double getNonNanVal(Location loc, WillsMap2006 wills, double mult) throws IOException {
		double spacing = wills.getResolution();
		
		LocationList locs = new LocationList();
		
		double minLat = loc.getLatitude() - mult * spacing;
		double maxLat = loc.getLatitude() + mult * spacing;
		
		double minLon = loc.getLongitude() - mult * spacing;
		double maxLon = loc.getLongitude() + mult * spacing;
		
		double addition = spacing * mult / 20d;
//		if (addition < spacing)
//			addition = spacing;
		
		for (double lat = minLat; lat<=maxLat; lat += addition) {
			for (double lon = minLon; lon<=maxLon; lon += addition) {
				locs.add(new Location(lat, lon));
			}
		}
		
		ArrayList<Double> vals = wills.getValues(locs);
		
		Double retVal = Double.NaN;
		
		double dist =  999;
		
		for (int i=0; i<locs.size(); i++) {
			Double val = vals.get(i);
			Location newLoc = locs.get(i);
			
			if (val.isNaN())
				continue;
			
			double newDist = distCalc(loc, newLoc);
			if (newDist < dist) {
				dist = newDist;
				retVal = val;
			}
		}
		
		if (!retVal.isNaN())
			System.out.println("Replaced NaN with: " + retVal + " at dist: " + dist
				+ " mult: " + mult + " add: " + addition);
		
		return retVal;
	}
	
	private static double distCalc(Location loc1, Location loc2) {
		return Math.sqrt(Math.pow(loc1.getLatitude() - loc2.getLatitude(), 2)
				+ Math.pow(loc1.getLongitude() - loc2.getLongitude(), 2));
	}

	/**
	 * @param args
	 * @throws IOException 
	 * @throws FileNotFoundException 
	 */
	public static void main(String[] args) throws FileNotFoundException, IOException {
		String fileName = "/home/kevin/OpenSHA/hazus/tracts.csv";
		
//		System.out.println(SiteTranslator.getWillsVs30TranslationString());
		
		ArrayList<String> lines = FileUtils.loadFile(fileName);
		
		String header = lines.get(0);
		lines.remove(0);
		
		FileWriter fw = new FileWriter("/home/kevin/OpenSHA/hazus/vs30.csv");
		
		header += ",Wills2006,TopoSlope";
		
		fw.write(header + "\n");
		
		WillsMap2006 wills = new WillsMap2006();
		WaldAllenGlobalVs30 wald = new WaldAllenGlobalVs30();
		wald.setActiveCoefficients();
		
		LocationList locs = new LocationList();
		
		System.out.println("Parsing locations");
		for (String line : lines) {
			if (line.length() < 5)
				continue;
			StringTokenizer tok = new StringTokenizer(line, ",");
			tok.nextToken(); // id
			tok.nextToken(); // tract
			double lat = Double.parseDouble(tok.nextToken()); // lat
			double lon = Double.parseDouble(tok.nextToken()); // lon
			
			locs.add(new Location(lat, lon));
		}
		
		System.out.println("Getting Wills2006 vals");
		ArrayList<Double> willsVals = wills.getValues(locs);
		System.out.println("Getting Wald Allen vals");
		ArrayList<Double> waldVals = wald.getValues(locs);
		
		System.out.println("outputting results");
		int i = 0;
		for (String line : lines) {
			if (line.length() < 5)
				continue;
			Double willsVal = willsVals.get(i);
			double mult = 10;
			while (willsVal.isNaN()) {
				willsVal = getNonNanVal(locs.get(i), wills, mult);
				mult *= 2;
			}
			line += "," + willsVal + "," + waldVals.get(i);
			
			fw.write(line + "\n");
			
			i++;
		}
		
		System.out.println("done!");
		
		fw.close();
	}

}
