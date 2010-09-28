/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.data;

import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: ArbDiscretizedXYZ_DataSet</p>
 * <p>Description: This class creates a vector for the XYZ dataset.
 * FIX : FIX - The implementation is the quick and dirty solution for the time being and will needed to
 * modified later on based on our requirements.
 * Requires Fixation to be consistent with our implementation of the 2-D data representation</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class ArbDiscretizedXYZ_DataSet implements XYZ_DataSetAPI,java.io.Serializable{
	
	/**
	 * default serial version UID
	 */
	private static final long serialVersionUID = 1l;

	ArrayList<Double> xValues, yValues, zValues;


	/**
	 * Default class constructor
	 */
	public ArbDiscretizedXYZ_DataSet(){
		xValues = new ArrayList<Double>();
		yValues = new ArrayList<Double>();
		zValues = new ArrayList<Double>();
	};
	/**
	 * constructor that takes the xVals,yVals and zVals as the argument
	 * @param xVals = ArrayList containing the xValues
	 * @param yVals = ArrayList containing the yValues
	 * @param zVals = ArrayList containing the zValues
	 */
	public ArbDiscretizedXYZ_DataSet(ArrayList<Double> xVals, ArrayList<Double> yVals,
			ArrayList<Double> zVals) {

		xValues = xVals;
		yValues = yVals;
		zValues = zVals;
	}

	/**
	 * Initialises the x, y and z Values ArrayList
	 * @param xVals
	 * @param yVals
	 * @param zVals
	 */
	public void setXYZ_DataSet(ArrayList<Double> xVals, ArrayList<Double> yVals, ArrayList<Double> zVals){

		xValues = xVals;
		yValues = yVals;
		zValues = zVals;
	}

	/**
	 *
	 * @returns the X Values dataSet
	 */
	public ArrayList<Double> getX_DataSet(){
		return xValues;
	}

	/**
	 *
	 * @returns the Y value DataSet
	 */
	public ArrayList<Double> getY_DataSet(){
		return yValues;
	}


	/**
	 *
	 * @returns the Z value DataSet
	 */
	public ArrayList<Double> getZ_DataSet(){
		return zValues;
	}

	/**
	 *
	 * @returns the minimum of the X Values
	 */
	public double getMinX(){
		return getMin(xValues);
	}

	/**
	 *
	 * @returns the maximum of the X Values
	 */
	public double getMaxX(){
		return getMax(xValues);
	}

	/**
	 *
	 * @returns the minimum of the Y Values
	 */
	public double getMinY(){
		return getMin(yValues);
	}

	/**
	 *
	 * @returns the maximum of the Y values
	 */
	public double getMaxY(){
		return getMax(yValues);
	}

	/**
	 *
	 * @returns the minimum of the Z values
	 */
	public double getMinZ(){
		return getMin(zValues);
	}

	/**
	 *
	 * @returns the maximum of the Z values
	 */
	public double getMaxZ(){
		return getMax(zValues);
	}

	/**
	 *
	 * @returns true if size ArrayList for X,Y and Z dataset values is equal else return false
	 */
	public boolean checkXYZ_NumVals(){
		if((xValues.size() == yValues.size()) && (xValues.size() == zValues.size()))
			return true;
		else
			return false;
	}

	/**
	 * private function of the class that finds the minimum value in the ArrayList
	 * @param xyz
	 * @return
	 */
	private double getMin(ArrayList xyz){
		int size = xyz.size();
		double min = Double.POSITIVE_INFINITY;
		for(int i=1;i<size;++i){
			double val = ((Double)xyz.get(i)).doubleValue();
			if(Double.isNaN(val)) continue;
			if(val < min)
				min = val;
		}
		return min;
	}

	/**
	 * private function of the class that finds the maximum value in the ArrayList
	 * @param xyz
	 * @return
	 */
	private double getMax(ArrayList xyz){
		int size = xyz.size();
		double max = Double.NEGATIVE_INFINITY;
		for(int i=1;i<size;++i){
			double val = ((Double)xyz.get(i)).doubleValue();
			if(Double.isNaN(val)) continue;
			if(val > max)
				max = val;
		}
		return max;
	}
	
	public static void writeXYZFile(XYZ_DataSetAPI xyz, String fileName) throws IOException {
		if (!xyz.checkXYZ_NumVals())
			throw new RuntimeException("Bad XYZ dataset!");
		
		ArrayList<Double> xData = xyz.getX_DataSet();
		ArrayList<Double> yData = xyz.getY_DataSet();
		ArrayList<Double> zData = xyz.getZ_DataSet();
		
		int size = xData.size();
		
		FileWriter fw = new FileWriter(fileName);
		for (int i=0; i<size; i++) {
			fw.write(xData.get(i) + "\t" + yData.get(i) + "\t" + zData.get(i) + "\n");
		}
		fw.close();
	}
	
	public static ArbDiscretizedXYZ_DataSet loadXYZFile(String fileName) throws FileNotFoundException, IOException {
		ArrayList<String> lines = FileUtils.loadFile(fileName);
		
		ArbDiscretizedXYZ_DataSet xyz = new ArbDiscretizedXYZ_DataSet();
		
		for (String line : lines) {
			if (line.startsWith("#"))
				continue;
			if (line.length() < 2)
				continue;
			StringTokenizer tok = new StringTokenizer(line);
			if (tok.countTokens() < 3)
				continue;
			
			double x = Double.parseDouble(tok.nextToken());
			double y = Double.parseDouble(tok.nextToken());
			double z = Double.parseDouble(tok.nextToken());
			
			xyz.addValue(x, y, z);
		}
		
		return xyz;
	}
	
	public void addValue(double xVal, double yVal, double zVal) {
		this.xValues.add(xVal);
		this.yValues.add(yVal);
		this.zValues.add(zVal);
	}
	
	public void addAllValues(ArrayList<Double> xVals, ArrayList<Double> yVals, ArrayList<Double> zVals) {
		this.xValues.addAll(xVals);
		this.yValues.addAll(yVals);
		this.zValues.addAll(zVals);
	}
	
	public void addAllValues(XYZ_DataSetAPI xyz) {
		this.addAllValues(xyz.getX_DataSet(), xyz.getY_DataSet(), xyz.getZ_DataSet());
	}

}
