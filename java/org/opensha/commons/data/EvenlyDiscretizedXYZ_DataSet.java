package org.opensha.commons.data;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.util.FileUtils;

public class EvenlyDiscretizedXYZ_DataSet implements XYZ_DataSetAPI {
	
	private double data[][];
	
	private int ncols;
	private int nrows;
	private double minX;
	private double maxX;
	private double minY;
	private double maxY;
	private double gridSpacing;
	
	public EvenlyDiscretizedXYZ_DataSet(int ncols, int nrows, double minX, double minY, double gridSpacing) {
		this(new double[nrows][ncols], minX, minY, gridSpacing);
	}
	
	public EvenlyDiscretizedXYZ_DataSet(double[][] data, double minX, double minY, double gridSpacing) {
		this.data = data;
		this.minX = minX;
		this.minY = minY;
		this.gridSpacing = gridSpacing;
		
		this.ncols = data[0].length;
		this.nrows = data.length;
		
		maxX = minX + gridSpacing * (ncols-1);
		maxY = minY + gridSpacing * (nrows-1);
		
		System.out.println("EvenlyDiscretizedXYZ_DataSet: minX: " + minX + ", maxX: " + maxX
				+ ", minY: " + minY + ", maxY: " + maxY);
	}

	public void addValue(double xVal, double yVal, double zVal) {
		if (xVal < minX || xVal > maxX || yVal < minY || yVal > maxY)
			throw new InvalidRangeException("point must be within range");
		this.addValue(getCol(xVal), getRow(yVal), zVal);
	}
	
	public void addValue(int col, int row, double zVal) {
		this.data[row][col] = zVal;
	}

	public boolean checkXYZ_NumVals() {
		// TODO Auto-generated method stub
		return true;
	}

	public double getMaxX() {
		return maxX;
	}

	public double getMaxY() {
		return maxY;
	}

	public double getMaxZ() {
		double max = Double.MIN_VALUE;
		
		for (int row=0; row<nrows; row++) {
			for (int col=0; col<ncols; col++) {
				double val = getVal(col, row);
				if (val > max)
					max = val;
			}
		}
		
		return max;
	}

	public double getMinX() {
		return minX;
	}

	public double getMinY() {
		return minY;
	}

	public double getMinZ() {
		double min = Double.MAX_VALUE;
		
		for (int row=0; row<nrows; row++) {
			for (int col=0; col<ncols; col++) {
				double val = getVal(col, row);
				if (val < min)
					min = val;
			}
		}
		
		return min;
	}
	
	/**
	 * Get the grid spacing of this evenly discretized dataset
	 * @return
	 */
	public double getGridSpacing() {
		return gridSpacing;
	}
	
	public int getNumX() {
		return ncols;
	}
	
	public int getNumY() {
		return nrows;
	}
	
	public double getVal(int col, int row) {
		return data[row][col];
	}
	
	public double getVal(double x, double y) {
		return data[getRow(y)][getCol(x)];
	}
	
	private int getRow(double y) {
		return (int)((y - minY) / gridSpacing + 0.5);
	}
	
	private int getCol(double x) {
		return (int)((x - minX) / gridSpacing + 0.5);
	}

	public ArrayList<Double> getX_DataSet() {
		// TODO Auto-generated method stub
		return null;
	}

	public ArrayList<Double> getY_DataSet() {
		// TODO Auto-generated method stub
		return null;
	}

	public ArrayList<Double> getZ_DataSet() {
		// TODO Auto-generated method stub
		return null;
	}

	public void setXYZ_DataSet(ArrayList<Double> xVals,
			ArrayList<Double> yVals, ArrayList<Double> zVals) {
		// TODO Auto-generated method stub

	}
	
	public void writeXYZBinFile(String fileNamePrefix) throws IOException {
		FileWriter header = new FileWriter(fileNamePrefix + ".hdr");
		header.write("ncols" + "\t" + ncols + "\n");
		header.write("nrows" + "\t" + nrows + "\n");
		header.write("xllcorner" + "\t" + minX + "\n");
		header.write("yllcorner" + "\t" + minY + "\n");
		header.write("cellsize" + "\t" + gridSpacing + "\n");
		header.write("NODATA_value" + "\t" + "-9999" + "\n");
		header.write("byteorder" + "\t" + "LSBFIRST" + "\n");
		
		header.close();
		
		DataOutputStream out = new DataOutputStream(new FileOutputStream(fileNamePrefix + ".flt"));
		
		for (int row=0; row<nrows; row++) {
			for (int col=0; col<ncols; col++) {
				double val = getVal(col, row);
				out.writeFloat((float)val);
			}
		}
		
		out.close();
	}
	
	private static String getHeaderValue(ArrayList<String> lines, String key) {
		for (String line : lines) {
			if (line.startsWith(key)) {
				StringTokenizer tok = new StringTokenizer(line);
				tok.nextToken();
				return tok.nextToken();
			}
		}
		return null;
	}
	
	public static EvenlyDiscretizedXYZ_DataSet readXYZBinFile(String fileNamePrefix) throws IOException {
		ArrayList<String> lines = FileUtils.loadFile(fileNamePrefix + ".hdr");
		
		int ncols = Integer.parseInt(getHeaderValue(lines, "ncols"));
		int nrows = Integer.parseInt(getHeaderValue(lines, "nrows"));
		double minX = Double.parseDouble(getHeaderValue(lines, "xllcorner"));
		double minY = Double.parseDouble(getHeaderValue(lines, "yllcorner"));
		double gridSpacing = Double.parseDouble(getHeaderValue(lines, "cellsize"));
		
		DataInputStream reader = new DataInputStream(new FileInputStream(fileNamePrefix + ".flt"));
		
		EvenlyDiscretizedXYZ_DataSet data = new EvenlyDiscretizedXYZ_DataSet(ncols, nrows, minX, minY, gridSpacing);
		
		for (int row=0; row<nrows; row++) {
			for (int col=0; col<ncols; col++) {
				double val = (double)reader.readFloat();
				
				data.addValue(col, row, val);
			}
		}
		
		return data;
	}

}
