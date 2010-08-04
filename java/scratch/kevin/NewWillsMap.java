package scratch.kevin;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.ShortBuffer;
import java.util.ArrayList;

import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.util.binFile.BinaryMesh2DCalculator;
import org.opensha.commons.util.binFile.GeolocatedRectangularBinaryMesh2DCalculator;
import org.opensha.commons.util.interp.BicubicInterpolation2D;
import org.opensha.sha.gui.servlets.siteEffect.WillsSiteClass;

public class NewWillsMap {
	
//	public static final String BIN_FILE = "/home/scec-00/kmilner/wills/out.bin";
	public static final String BIN_FILE = "/home/kevin/OpenSHA/siteClass/out.bin";
	
	public static boolean bicubic = true;
	
	public static final int nx = 49867;
	public static final int ny = 44016;
	
	public static final int maxx = nx - 1;
	public static final int maxy = ny - 1;
	
	public static final double spacing = 0.00021967246502752;
	
	public static final double minLon = -124.52997177169;
	public static final double minLat = 32.441345502265;
	// yul = yll + size * ny
	
	GriddedRegion region;
	
	String willsFileName = "/etc/cvmfiles/usgs_cgs_geology_60s_mod.txt";
	
	public NewWillsMap(GriddedRegion region) {
		this.region = region;
//		System.out.println("XLL: " + xll_corner);
//		System.out.println("YLL: " + yll_corner);
//		System.out.println("YUL: " + yul_corner);
//		System.out.println("XUR: " + xur_corner);
	}
	
	private void calcOld() {
		WillsSiteClass wills = new WillsSiteClass(region.getNodeList(), willsFileName);
		wills.setLoadFromJar(true);
		long start = System.currentTimeMillis();
		ArrayList<String> vals = wills.getWillsSiteClass();
		System.out.println("Loaded " + vals.size() + " locations!");
		long time = System.currentTimeMillis() - start;
		boolean print = false;
		if (print) {
			for (String val : vals) {
				System.out.println(val);
			}
		}
		printTime(time);
		int setVals = 0;
		int num = region.getNodeList().size();
		for (String val : vals) {
			if (!(val.toLowerCase().contains("nan") || val.toLowerCase().contains("na")))
				setVals++;
		}
		System.out.println("Set " + setVals + "/" + num);
	}
	
	private void printTime(long time) {
		double val = (double)time / 1000d;
		System.out.println(val + " seconds");
	}
	
	private static double calcBicubic(RandomAccessFile file, GeolocatedRectangularBinaryMesh2DCalculator calc, byte[] recordBuffer, ShortBuffer shortBuff, Location loc) throws IOException {
		long index[] = calc.calcClosestLocationIndices(loc.getLatitude(), loc.getLongitude());
		
		boolean debug = true;
		
		Location indexLoc = calc.getLocationForPoint(index[0], index[1]);
		
		// true if my point is north of the mesh point
		boolean above = loc.getLatitude() > indexLoc.getLatitude();
		// true if my point is east of the mesh point
		boolean right = loc.getLongitude() > indexLoc.getLongitude();
		
		int startY;
		if (above)
			startY = (int)index[1] - 1;
		else
			startY = (int)index[1] - 2;
		
		int startX;
		if (right)
			startX = (int)index[0] - 1;
		else
			startX = (int)index[0] - 2;
		
		double mat[][] = new double[4][4];
		
		String debugStr = "";
		if (debug) {
			debugStr += "***** LOC: " + loc;
			debugStr += "\n***** INDEX LOC: " + indexLoc + "\n\n";
		}
		
		boolean diff = false;
		double firstVal = Double.MIN_VALUE; 
		for (int x=0; x<4; x++) {
			for (int y=0; y<4; y++) {
				double val = getValAtPt(file, calc, recordBuffer, shortBuff, startX + x, startY + y);
				if (firstVal == Double.MIN_VALUE)
					firstVal = val;
				else if (firstVal != val)
					diff = true;
				mat[x][y] = val;
				if (debug)
					debugStr += val + " ";
			}
			if (debug) {
				debugStr += "\n\n";
			}
		}
		
		if (!diff)
			return firstVal;
		
		// now do a no-nan sweep
		for (int x=0; x<4; x++) {
			for (int y=0; y<4; y++) {
				double val = mat[x][y];
				if (val < 0) {
					return -9999;
				}
			}
		}
		
		BicubicInterpolation2D interp = new BicubicInterpolation2D(mat);
		
		double yDiff;
		if (above)
			yDiff = (loc.getLatitude() - indexLoc.getLatitude()) / spacing;
		else
			yDiff = (indexLoc.getLatitude() - loc.getLatitude()) / spacing;
		
		double xDiff;
		if (right)
			xDiff = (loc.getLongitude() - indexLoc.getLongitude()) / spacing;
		else
			xDiff = (indexLoc.getLongitude() - loc.getLongitude()) / spacing;
		
		if (debug)
			System.out.println(debugStr + xDiff + " " + yDiff);
		
		double retVal = interp.eval(xDiff, yDiff);
		
		if (debug)
			System.out.println("Ret Val: " + retVal + "\n\n");
		
		return retVal;
	}
	
	private static int getValAtPt(RandomAccessFile file, GeolocatedRectangularBinaryMesh2DCalculator calc, byte[] recordBuffer, ShortBuffer shortBuff, int x, int y) throws IOException {
		if (x < 0)
			x = 0;
		else if (x > maxx)
			x = maxx;
		if (y < 0)
			y = 0;
		else if (y > maxy)
			y = maxy;
		
		long seek = calc.calcFileIndex(x, y);
		
		file.seek(seek);
		file.read(recordBuffer);
		return shortBuff.get(0);
	}
	
	private void calcNew() throws IOException {
		boolean writeXYZ = true;
		FileWriter fw = null;
		
		if (writeXYZ)
			fw = new FileWriter("/tmp/newXYZ.txt");
		
		int num = region.getNodeCount();
		
		RandomAccessFile file = new RandomAccessFile(new File(BIN_FILE), "r");
		
		GeolocatedRectangularBinaryMesh2DCalculator calc = new GeolocatedRectangularBinaryMesh2DCalculator(
				BinaryMesh2DCalculator.TYPE_SHORT,nx, ny, minLat, minLon, spacing);
		
		calc.setStartBottom(false);
		calc.setStartLeft(true);
		
		long start = System.currentTimeMillis();
		int setVals = 0;
		int modVal = 10000;
		long prevSeek = 0;
		int posSeeks = 0;
		int negSeeks = 0;
		
		byte[] recordBuffer = new byte[2];
		ByteBuffer record = ByteBuffer.wrap(recordBuffer);
		record.order(ByteOrder.LITTLE_ENDIAN);
		ShortBuffer shortBuff = record.asShortBuffer();
		for (int i=0; i<num; i++) {
			Location loc = region.locationForIndex(i);
			
			if (loc.getLatitude() < calc.getMinLat() || loc.getLatitude() > calc.getMaxLat()
					|| loc.getLongitude() < calc.getMinLon() || loc.getLongitude() > calc.getMaxLon()) {
//				if (i % modVal == 0)
//					System.out.println("Skipping " + i + " for: " + loc.toString());
				continue;
			}
			
			double val;
			
			if (bicubic) {
				val = calcBicubic(file, calc, recordBuffer, shortBuff, loc);
			} else {
				long seek = calc.calcClosestLocationFileIndex(loc.getLatitude(), loc.getLongitude());
				if (seek - prevSeek < 0)
					negSeeks++;
				else
					posSeeks++;
				prevSeek = seek;
//				if (i % modVal == 0) {
//					System.out.println("Seeking " + i + " to " + seek + " for " + loc.toString() + " pos: " + posSeeks + ", neg: " + negSeeks);
//				}
//				System.out.println("Seeking to " + seek);
				
				file.seek(seek);
				file.read(recordBuffer);
				val = shortBuff.get(0);
			}
			
//			System.out.println(val);
			if (val > 0) {
				setVals++;
//				fw.write(loc.getLongitude() + " " + loc.getLatitude() + " " + val + "\n");
				if (writeXYZ)
					fw.write(loc.getLatitude() + " " + loc.getLongitude() + " " + val + "\n");
			}
//			System.out.println("Read: " + val);
		}
		long time = System.currentTimeMillis() - start;
		System.out.println("Set " + setVals + "/" + num + " pos: " + posSeeks + ", neg: " + negSeeks);
		printTime(time);
		if (writeXYZ)
			fw.close();
	}

	/**
	 * @param args
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
		GriddedRegion region = 
			new GriddedRegion(
					new CaliforniaRegions.RELM_TESTING(),
					0.02,
					new Location(0,0));
		//GriddedRegion region = new EvenlyGriddedRELM_TestingRegion();
		//region.setGridSpacing(0.02);
		
		NewWillsMap wills = new NewWillsMap(region);
		
		wills.calcOld();
		wills.calcNew();
	}

}
