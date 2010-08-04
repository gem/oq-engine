package org.opensha.sra.riskmaps;

import java.io.DataInputStream;
import java.io.EOFException;
import java.io.FileInputStream;
import java.util.ArrayList;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.sra.riskmaps.func.DiscreteInterpExterpFunc;

public class BinaryHazardCurveReader {
	private DataInputStream reader = null;
	private ArrayList<Double> imlvals = new ArrayList<Double>();
	private double latitude, longitude;
	
	public BinaryHazardCurveReader(String filename) throws Exception {
		// Set up the reader
		reader = new DataInputStream(new FileInputStream(filename));
		
		// Pre-populate the IML values
		int imlcount = reader.readInt();
		for ( int i = 0; i < imlcount; ++i ) {
			imlvals.add(reader.readDouble());
		}
	}
	
	public ArbitrarilyDiscretizedFunc nextCurve() throws Exception {
		ArbitrarilyDiscretizedFunc function = new ArbitrarilyDiscretizedFunc();
		try {
			latitude = reader.readDouble();
			longitude = reader.readDouble();
			for ( int i = 0; i < imlvals.size(); ++i ) {
				function.set((double) imlvals.get(i), reader.readDouble());
			}
		} catch (EOFException eof) {
			return null;
		}
		return function;
	}
	
	public DiscreteInterpExterpFunc nextDiscreteCurve() throws Exception {
		double xVals[] = new double[imlvals.size()];
		double yVals[] = new double[imlvals.size()];
		try {
			latitude = reader.readDouble();
			longitude = reader.readDouble();
			for ( int i = 0; i < imlvals.size(); ++i ) {
				xVals[i] = (double) imlvals.get(i);
				yVals[i] = reader.readDouble();
			}
		} catch (EOFException eof) {
			return null;
		}
		return new DiscreteInterpExterpFunc(xVals, yVals);
	}
	
	public Location currentLocation() {
		return new Location(latitude, longitude);
	}
	
	public double[] currentLocationArray() {
		double result[] = { latitude, longitude };
		return result;
	}
	
	public int getNumVals() {
		return imlvals.size();
	}
}
