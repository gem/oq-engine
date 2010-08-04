package org.opensha.sha.faultSurface.simulators;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;

public class SimulatorFaultSurface extends EvenlyGriddedSurface {
	
//	private static final int ncols = 2;
//	private static final int nrows = 8;
	
	private String name;
	
	private int elementID;
	private int faultID;
	private int sectionID;
	private int numAlongStrike;
	private int numDownDip;
	private double slipRate;
	private double elementStrength;
	private FocalMechanism focalMechanism;
	
	public SimulatorFaultSurface(int elementID, Location pts[][], String name,
			int faultID, int sectionID, int numAlongStrike, int numDownDip,
			double slipRate, double elementStrength, FocalMechanism focalMechanism) {
		super(pts[0].length, pts.length, 1d);
		
		int count = 0;
		for (int j=0; j<pts[0].length; j++) {
			for (int i=0; i<pts.length; i++) {
				Location loc = pts[i][j];
				
				setLocation(j, i, loc);
				
				count++;
			}
		}
		
		this.name = name;
		this.elementID = elementID;
		this.faultID = faultID;
		this.sectionID = sectionID;
		this.numAlongStrike = numAlongStrike;
		this.numDownDip = numDownDip;
		this.slipRate = slipRate;
		this.elementStrength = elementStrength;
		this.focalMechanism = focalMechanism;
	}

	public int getNumAlongStrike() {
		return numAlongStrike;
	}

	public void setNumAlongStrike(int numAlongStrike) {
		this.numAlongStrike = numAlongStrike;
	}

	public int getNumDownDip() {
		return numDownDip;
	}

	public void setNumDownDip(int numDownDip) {
		this.numDownDip = numDownDip;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public int getFaultID() {
		return faultID;
	}

	public void setFaultID(int faultID) {
		this.faultID = faultID;
	}

	public int getSectionID() {
		return sectionID;
	}

	public void setSectionID(int sectionID) {
		this.sectionID = sectionID;
	}
	
	public double getSlipRate() {
		return slipRate;
	}
	
	public FocalMechanism getFocalMechanism() {
		return focalMechanism;
	}

	public int getElementID() {
		return elementID;
	}

	public void setElementID(int elementID) {
		this.elementID = elementID;
	}

	public double getElementStrength() {
		return elementStrength;
	}
	
	public String getNameLine() {
		// TODO implement
		return "";
	}
	
	public String getElementLine() {
		Location newTop1 = get(0, 0);
		Location newTop2 = get(0, 1);
		Location newBot1 = get(1, 0);
		Location newBot2 = get(1, 1);
		String line = elementID + "\t"+
			numAlongStrike + "\t"+
			numDownDip + "\t"+
			faultID + "\t"+
			sectionID + "\t"+
			(float)slipRate + "\t"+
			(float)elementStrength + "\t"+
			(float)focalMechanism.getStrike() + "\t"+
			(float)focalMechanism.getDip() + "\t"+
			(float)focalMechanism.getRake() + "\t"+
			(float)newTop1.getLatitude() + "\t"+
			(float)newTop1.getLongitude() + "\t"+
			(float)newTop1.getDepth()*-1000 + "\t"+
			(float)newBot1.getLatitude() + "\t"+
			(float)newBot1.getLongitude() + "\t"+
			(float)newBot1.getDepth()*-1000 + "\t"+
			(float)newBot2.getLatitude() + "\t"+
			(float)newBot2.getLongitude() + "\t"+
			(float)newBot2.getDepth()*-1000 + "\t"+
			(float)newTop2.getLatitude() + "\t"+
			(float)newTop2.getLongitude() + "\t"+
			(float)newTop2.getDepth()*-1000 + "\t"+
			name;
		return line;
	}
	
	@Override
	public String toString() {
		return getElementLine();
	}

	public static SimulatorFaultSurface loadFromLine(String line) {
		StringTokenizer tok = new StringTokenizer(line);

		int elementID = Integer.parseInt(tok.nextToken()); // unique number ID for each element, not needed
		int numAlongStrike = Integer.parseInt(tok.nextToken()); // Number along strike
		int numDownDip = Integer.parseInt(tok.nextToken()); // Number down dip
		int faultID = Integer.parseInt(tok.nextToken()); // Fault Number
		int secID = Integer.parseInt(tok.nextToken()); // Segment Number
		double slip = Double.parseDouble(tok.nextToken()); // Slip Rate in m/y.
		double strength = Double.parseDouble(tok.nextToken()); // Element Strength in Bars.
		double strike = Double.parseDouble(tok.nextToken()); // stike
		double dip = Double.parseDouble(tok.nextToken()); // dip
		double rake = Double.parseDouble(tok.nextToken()); // rake

		Location jPts[] = new Location[4];
		for (int j=0; j<4; j++) {
			//				int jMod2 = j % 2;
			double lat = Double.parseDouble(tok.nextToken());
			double lon = Double.parseDouble(tok.nextToken());
			double alt = Double.parseDouble(tok.nextToken()) / -1000d;
			jPts[j] = new Location(lat, lon, alt);
			//				pts[iCnt][jMod2] = new Location(lat, lon, alt);
			//				pts.add(new Location(lat, lon, alt));
		}
		Location pts[][] = new Location[2][2];
		pts[0][0] = jPts[0];
		pts[0][1] = jPts[1];
		pts[1][0] = jPts[3];
		pts[1][1] = jPts[2];
		
		String name = null;
		while (tok.hasMoreTokens()) {
			if (name == null)
				name = "";
			else
				name += " ";
			name += tok.nextToken();
		}
		
		return new SimulatorFaultSurface(elementID, pts, name,
				faultID, secID, numAlongStrike, numDownDip,
				slip, strength, new FocalMechanism(strike, dip, rake));
	}
	
	public static ArrayList<SimulatorFaultSurface> loadFromLines(ArrayList<String> lines) {
		ArrayList<SimulatorFaultSurface> surfaces = new ArrayList<SimulatorFaultSurface>();
		
		for (String line : lines) {
			if (line == null || line.length() == 0)
				continue;
			surfaces.add(loadFromLine(line));
		}
		
		return surfaces;
	}
	
	public static void writeToFile(ArrayList<SimulatorFaultSurface> surfaces, String fileName)
	throws IOException {
		FileWriter efw = new FileWriter(fileName);
		for (SimulatorFaultSurface surface : surfaces) {
			efw.write(surface.getElementLine() + "\n");
		}
		efw.close();
	}

}
