package org.opensha.commons.util;

import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.List;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;

import ucar.ma2.Array;
import ucar.ma2.Index;
import ucar.ma2.InvalidRangeException;
import ucar.nc2.Dimension;
import ucar.nc2.NetcdfFile;
import ucar.nc2.Variable;

/**
 * This class wraps the NetCDF-Java library for use specifically with GMT-style NetCDF files (.grd files).
 * 
 * X and Y values are pre-loaded, and Z values can either be cached (faster when there is ample memory
 * for the file and either a large chunk of the file will be used, or lots of random access) or loaded
 * on demand.
 * 
 * @author kevin
 *
 */
public class GMT_GrdFile {
	
	private NetcdfFile file;
	
	private int xDim, yDim;
	private double xSpacing, ySpacing;
	private Array xData;
	private Array yData;
	
	private Array zData = null;
	private Index zInd = null;
	private Variable zVar;
	
	private static int singleShape[] = {1, 1};
	
	private Region region = null;
	
	/**
	 * Load the given GRD file...it will be cached by default
	 * 
	 * @param fileName
	 * @throws IOException
	 */
	public GMT_GrdFile(String fileName) throws IOException {
		this(fileName, true);
	}
	
	/**
	 * Load the given GRD file...it will be cached if cacheZ is true
	 * 
	 * @param fileName
	 * @param cacheZ
	 * @throws IOException
	 */
	public GMT_GrdFile(String fileName, boolean cacheZ) throws IOException {
		this(NetcdfFile.open(fileName), cacheZ);
	}
	
	/**
	 * Load the given GRD file...it will be cached if cacheZ is true
	 * 
	 * @param fileName
	 * @param cacheZ
	 * @throws IOException
	 */
	public GMT_GrdFile(URI uri) throws IOException {
		this(NetcdfFile.openInMemory(uri), true);
	}
	
	public GMT_GrdFile(NetcdfFile file, boolean cacheZ) throws IOException {
		this.file = file;
		List<Dimension> dims = file.getDimensions();
		xDim = dims.get(0).getLength();
		yDim = dims.get(1).getLength();
		
		List<Variable> vars = file.getVariables();
		Variable xVar = vars.get(0);
		Variable yVar = vars.get(1);
		
		xData = xVar.read();
		xSpacing = calcSpacing(xData);
		yData = yVar.read();
		ySpacing = calcSpacing(yData);
		
		zVar = vars.get(2);
		if (cacheZ) {
			cacheZData();
		}
	}
	
	private double calcSpacing(Array data) {
		long max = 100;
		if (max > data.getSize())
			max = data.getSize();
		double tot = 0;
		int cnt = 0;
		for (int i=0; i<max-1; i++) {
			double val1 = data.getDouble(i);
			double val2 = data.getDouble(i+1);
			tot += Math.abs(val2 - val1);
			cnt++;
		}
		return tot / (double)cnt;
	}
	
	/**
	 * Get the number of X points in the GRD file
	 * 
	 * @return
	 */
	public int getNumX() {
		return xDim;
	}
	
	/**
	 * Get the number of Y points in the GRD file
	 * 
	 * @return
	 */
	public int getNumY() {
		return yDim;
	}
	
	/**
	 * Get the grid spacing in the X dimension
	 * 
	 * @return
	 */
	public double getXSpacing() {
		return xSpacing;
	}
	
	/**
	 * Get the grid spacing in the Y dimension
	 * 
	 * @return
	 */
	public double getYSpacing() {
		return ySpacing;
	}
	
	/**
	 * Get the longitude (X) pt at the given X-index
	 * 
	 * @param x
	 * @return
	 */
	public double getX(int x) {
		return xData.getDouble(x);
	}
	
	/**
	 * Get a NetCDF Array with all of the longitude (X) data
	 * 
	 * @return
	 */
	public Array getXData() {
		return xData;
	}
	
	/**
	 * Get the latitude (Y) pt at the given X-index
	 * 
	 * @param x
	 * @return
	 */
	public double getY(int y) {
		return yData.getDouble(y);
	}
	
	/**
	 * Get a NetCDF Array with all of the latitude (Y) data
	 * 
	 * @return
	 */
	public Array getYData() {
		return yData;
	}
	
	/**
	 * checks whether x index is valid
	 * @param x
	 * @return
	 */
	public boolean isValidX_index(int x){
		if(x>0 && x<getNumX()){
			return true;
		} else {
			return false;
		}
	}
	
	/**
	 * checks whether y index is valid
	 * @param y
	 * @return
	 */
	public boolean isValidY_index(int y){
		if(y>0 && y<getNumY()){
			return true;
		} else {
			return false;
		}
	}
	
	/**
	 * Get the Location at the following X,Y indexes
	 * 
	 * @param x
	 * @param y
	 * @return
	 */
	public Location getLoc(int x, int y) {
		return new Location(getY(y), getX(x));
	}
	
	/**
	 * This class calculates the index for the given point in terms of floats. When rounded,
	 * this would be the closest point.
	 * 
	 * @param loc
	 * @return
	 */
	private double[] getFloatIndexes(Location loc) {
		double ret[] = { getFloatIndexY(loc), getFloatIndexX(loc) };
		return ret;
	}
	
	private double getFloatIndexX(Location loc) {
		double lon = loc.getLongitude();
		double minLon = getMinX();
		return (lon - minLon) / xSpacing;
	}
	
	private double getFloatIndexY(Location loc) {
		double lat = loc.getLatitude();
		double minLat = getMinY();
		return (lat - minLat) / ySpacing;
	}
	
	/**
	 * This computes a weight average of the z-values at the nearest four corners, 
	 * ignoring any NaNs encountered, or using just two points if the loc is just
	 * off the edge of the region.
	 * @param loc
	 * @return
	 * @throws IOException
	 * @throws InvalidRangeException
	 */
	public double getWtAveZ(Location loc) throws IOException, InvalidRangeException {
		double ind[] = getFloatIndexes(loc);
		
		double x = ind[1];
		double y = ind[0];
		
		int x0 = (int)ind[1];
		int y0 = (int)ind[0];
		int x1 = x0 + 1;
		int y1 = y0 + 1;
		
		double z00=Double.NaN,z01=Double.NaN,z10=Double.NaN,z11=Double.NaN;
		boolean v00=false, v01=false, v10=false, v11=false;
		
		if(isValidX_index(x0) && isValidY_index(y0)) {
			v00=true;
			z00 = getZ(x0, y0);
		}
		if(isValidX_index(x1) && isValidY_index(y0)) {
			v10=true;
			z10 = getZ(x1, y0);
		}
		if(isValidX_index(x0) && isValidY_index(y1)) {
			v01=true;
			z01 = getZ(x0, y1);
		}
		if(isValidX_index(x1) && isValidY_index(y1)) {
			v11=true;
			z11 = getZ(x1, y1);
		}
		
		double d00 = Math.sqrt((x-x0)*(x-x0)+(y-y0)*(y-y0));
		double d10 = Math.sqrt((x-x1)*(x-x1)+(y-y0)*(y-y0));
		double d01 = Math.sqrt((x-x0)*(x-x0)+(y-y1)*(y-y1));
		double d11 = Math.sqrt((x-x1)*(x-x1)+(y-y1)*(y-y1));
		
		double meanZ=0;
		double wt=0;
		
		if(!Double.isNaN(z00) & v00) {
			meanZ += z00*d00;
			wt += d00;
		}
		if(!Double.isNaN(z10) && v10) {
			meanZ += z10*d10;
			wt += d10;
		}
		if(!Double.isNaN(z01) & v01) {
			meanZ += z01*d01;
			wt += d01;
		}
		if(!Double.isNaN(z11) & v11) {
			meanZ += z11*d11;
			wt += d11;
		}
		
		meanZ /= wt;
		
//		if(!Double.isNaN(meanZ)) System.out.println(loc.getLongitude()+"\t"+loc.getLatitude());
/*		
		System.out.println("wt ave:");
		System.out.println(x0 + ", " + x1 + ", " + x + ", " + y0 + ", " + y1 + ", " + y + "  (x0,x1,x,y0,y1,y)");
		System.out.println(z00 + ", " + z01 + ", " + z10 + ", " + z11 + ": mean=" + meanZ);
		System.out.println(d00 + ", " + d01 + ", " + d10 + ", " + d11 + ": wt=" + wt);
*/	
		return meanZ;
	}

	
	/**
	 * Does a biliniear interpolation between surrounding points to retrieve a value at the specified
	 * location. The given point should always be within the region boundary.
	 * 
	 * If one of the surrounding points is NaN, the resultant value will also be NaN.
	 * 
	 * @param loc
	 * @return
	 * @throws IOException
	 * @throws InvalidRangeException
	 */
	public double getInterpolatedZ(Location loc) throws IOException, InvalidRangeException {
		double ind[] = getFloatIndexes(loc);
		
		int x0 = (int)ind[1];
		int y0 = (int)ind[0];
		int x1 = x0 + 1;
		int y1 = y0 + 1;
		
		float xfrac = (float) (ind[1] - x0);
		float yfrac = (float) (ind[0] - y0);
		
		float s00 = (float) getZ(x0, y0);
		float s01 = (float) getZ(x1, y0);
		float s10 = (float) getZ(x0, y1);
		float s11 = (float) getZ(x1, y1);
		
		float interp = interpolate(s00, s01, s10, s11, xfrac, yfrac);
		
//		System.out.println(s00 + ", " + s01 + ", " + s10 + ", " + s11 + ": " + interp);
//		System.out.println(xfrac + ", " + yfrac);
		
		return interp;
	}

	private static float interpolate(float s00, float s01,
			float s10, float s11,
			float xfrac, float yfrac) {
		float s0 = (s01 - s00)*xfrac + s00;
		float s1 = (s11 - s10)*xfrac + s10;
		return (s1 - s0)*yfrac + s0;
	}


	/**
	 * Returns the closest point in the format (y,x)
	 * 
	 * @param loc
	 * @return
	 */
	public int[] getClosestPt(Location loc) {
		double[] fltPt = getFloatIndexes(loc);
		int y = (int) (fltPt[0] + 0.5);
		int x = (int) (fltPt[1] + 0.5);
		
		if (x < 0)
			x = 0;
		if (y < 0)
			y = 0;
		if (x >= xDim)
			x = xDim - 1;
		if (y >= yDim)
			y = yDim - 1;
		
		int pt[] = {y, x};
		return pt;
	}
	
	/**
	 * Get the Z value of the closest point in the file.
	 * 
	 * @param loc
	 * @return
	 * @throws IOException
	 * @throws InvalidRangeException
	 */
	public double getClosestZ(Location loc) throws IOException, InvalidRangeException {
		return getZ(getClosestPt(loc));
	}
	
	/**
	 * Get the Z value at the given X,Y indexes
	 * 
	 * @param x
	 * @param y
	 * @return
	 * @throws IOException
	 * @throws InvalidRangeException
	 */
	public double getZ(int x, int y) throws IOException, InvalidRangeException {
		int pt[] = {y, x};
		return getZ(pt);
	}
	
	/**
	 * Get the Z value at the given pt. The given point should be a 2-dimensional
	 * integer array in the format (y,x)
	 * 
	 * @param x
	 * @param y
	 * @return
	 * @throws IOException
	 * @throws InvalidRangeException
	 */
	public double getZ(int pt[]) throws IOException, InvalidRangeException {
		if (zData != null) {
			zInd.set(pt);
			return zData.getDouble(zInd);
		} else {
			Array data = zVar.read(pt, singleShape).reduce();
			return data.getDouble(0);
		}
	}
	
	/**
	 * Load the entire Z data into memory if it hasn't already been loaded
	 * 
	 * @throws IOException
	 */
	public void cacheZData() throws IOException {
		if (zData == null) {
			zData = zVar.read();
			zInd = zData.getIndex();
		}
	}
	
	/**
	 * Get a NetCDF Array with all of the Z data. It will be cached if needed.
	 * 
	 * @return
	 * @throws IOException
	 */
	public Array getZData() throws IOException {
		cacheZData();
		return zData;
	}
	
	/**
	 * Return the name field embedded into this GRD file.
	 * 
	 * @return
	 */
	public String getZName() {
		return zVar.getName();
	}
	
	/**
	 * Returns the min longitude (X) value
	 * 
	 * @return
	 */
	public double getMinX() {
		return getX(0);
	}
	
	/**
	 * Returns the max longitude (X) value
	 * 
	 * @return
	 */
	public double getMaxX() {
		return getX(getNumX() - 1);
	}
	
	/**
	 * Returns the min latitude (X) value
	 * 
	 * @return
	 */
	public double getMinY() {
		return getY(0);
	}
	
	/**
	 * Returns the max latitude (X) value
	 * 
	 * @return
	 */
	public double getMaxY() {
		return getY(getNumY() - 1);
	}
	
	/**
	 * Returns the region for this GRD file
	 * 
	 * @return
	 */
	public Region getRegion() {
		if (region == null) {
			Location loc1 = new Location(getMinY(), getMinX());
			Location loc2 = new Location(getMaxY(), getMaxX());
			region = new Region(loc1, loc2);
		}
		
		return region;
	}

	/**
	 * @param args
	 * @throws IOException 
	 * @throws InvalidRangeException 
	 * @throws URISyntaxException 
	 */
	public static void main(String[] args) throws IOException, InvalidRangeException, URISyntaxException {
		boolean cacheZ = true;	// if 'true', all Z values will be loaded up front. otherwise they will
								// be loaded on demand (slower if you need a lot of the file)
		GMT_GrdFile grd = new GMT_GrdFile(new URI("http://geohazards.cr.usgs.gov/staffweb/ghayes/Site/Slab1.0_files/sum_slab1.0_clip.grd"));
//		GMT_GrdFile grd = new GMT_GrdFile("/tmp/sum_slab1.0_clip.grd", cacheZ);
		
		System.out.println("NumX: " + grd.getNumX() + " NumY: " + grd.getNumY());
		System.out.println("SpacingX: " + grd.getXSpacing() + " SpacingY: " + grd.getYSpacing());
		System.out.println(grd.getRegion());
		
		int x = 1649;
		int y = 146;
		System.out.println(grd.getLoc(x, y) + ": " + grd.getZ(x, y));
		Location newLoc = new Location(-8.804, 123.9);
		System.out.println(newLoc + ": interp: " + grd.getInterpolatedZ(newLoc));
		System.out.println(newLoc + ":  close: " + grd.getClosestZ(newLoc));
	}

}
