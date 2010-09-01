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

package org.opensha.commons.data.function;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.StringTokenizer;

import org.dom4j.Element;
import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.util.FileUtils;


/**
 * <b>Title:</b> DiscretizedFunc<p>
 *
 * <b>Description:</b> Abstract implementation of the DiscretizedFuncAPI. Performs standard
 * simple or default functions so that subclasses don't have to keep reimplementing the
 * same function bodies.<p>
 *
 * A Discretized Function is a collection of x and y values grouped together as
 * the points that describe a function. A discretized form of a function is the
 * only ways computers can represent functions. Instead of having y=x^2, you
 * would have a sample of possible x and y values. <p>
 *
 * The basic functions this abstract class implements are:<br>
 * <ul>
 * <li>get, set Name()
 * <li>get, set, Info()
 * <li>get, set, Tolerance()
 * <li>equals() - returns true if all three fields have the same values.
 * </ul>
 *
 * See the interface documentation for further explanation of this framework<p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public abstract class DiscretizedFunc implements DiscretizedFuncAPI,
    NamedObjectAPI,java.io.Serializable{

	private static final long serialVersionUID = 2798699443929196424l;
	
    /** Class name used for debbuging */
    protected final static String C = "DiscretizedFunc";
    /** if true print out debugging statements */
    protected final static boolean D = false;
    
    public final static String XML_METADATA_NAME = "discretizedFunction";
    public final static String XML_METADATA_POINTS_NAME = "Points";
    public final static String XML_METADATA_POINT_NAME = "Point";


    /**
     * The tolerance allowed in specifying a x-value near a real x-value,
     * so that the real x-value is used. Note that the tolerance must be smaller
     * than 1/2 the delta between data points for evenly discretized function, no
     * restriction for arb discretized function, no standard delta.
     */
    protected double tolerance = 0.0;

    /**
     * Information about this function, will be used in making the legend from
     * a parameter list of variables
     */
    protected String info = "";

    /**
     * Name of the function, useful for differentiation different instances
     * of a function, such as in an array of functions.
     */
    protected String name = "";

    //X and Y Axis name
    private String xAxisName,yAxisName;

    /** Returns the name of this function. */
     public String getName(){ return name; }
    /** Sets the name of this function. */
    public void setName(String name){ this.name = name; }


    /** Returns the info of this function. */
    public String getInfo(){ return info; }
    /** Sets the info string of this function. */
     public void setInfo(String info){ this.info = info; }


    /**Returns the tolerance of this function. */
    public double getTolerance() { return tolerance; }
    /**
     * Sets the tolerance of this function. Throws an InvalidRangeException
     * if the tolerance is less than zero, an illegal value.
     */
     public void setTolerance(double newTolerance) throws InvalidRangeException {
        if( newTolerance < 0 )
            throw new InvalidRangeException("Tolerance must be larger or equal to 0");
        tolerance = newTolerance;
    }


    /**
     * Sets the name of the X Axis
     * @param xName String
     */
    public void setXAxisName(String xName){
      xAxisName = xName;
    }

    /**
     * Gets the name of the X Axis
     * @return String
     */
    public String getXAxisName(){
      return xAxisName;
    }

    /**
     * Sets the name of the Y Axis
     * @param yName String
     */
    public void setYAxisName(String yName){
      yAxisName = yName;
    }

    /**
     * Gets the name of the Y Axis
     * @return String
     */
    public String getYAxisName(){
      return yAxisName;
    }



    /**
     * Default equals for all Discretized Functions. Determines if two functions
     * are the same by comparing that the name and info are the same. Can
     * be overridden by subclasses for different requirements
     */
    public boolean equals(DiscretizedFuncAPI function){
        if( !getName().equals(function.getName() )  ) return false;

        if( D ) {
            String S = C + ": equals(): ";
            System.out.println(S + "This info = " + getInfo() );
            System.out.println(S + "New info = " + function.getInfo() );

        }

        if( !getInfo().equals(function.getInfo() )  ) return false;
        return true;
    }
    
    public double getClosestX(double y) {
		double x = Double.NaN;
		double dist = Double.POSITIVE_INFINITY;
		for (int i=0; i<getNum(); i++) {
			double newY = getY(i);
			double newDist = Math.abs(newY - y);
			if (newDist < dist) {
				dist = newDist;
				x = getX(i);
			}
		}
		return x;
	}

	public double getClosestY(double x) {
		double y = Double.NaN;
		double dist = Double.POSITIVE_INFINITY;
		for (int i=0; i<getNum(); i++) {
			double newX = getX(i);
			double newDist = Math.abs(newX - x);
			if (newDist < dist) {
				dist = newDist;
				y = getY(i);
			}
		}
		return y;
	}
    
    
    public Element toXMLMetadata(Element root) {
    	Element xml = root.addElement(DiscretizedFunc.XML_METADATA_NAME);
    	
    	xml.addAttribute("info", this.getInfo());
    	xml.addAttribute("name", this.getName());
    	
    	xml.addAttribute("tolerance", this.getTolerance() + "");
    	xml.addAttribute("xAxisName", this.getXAxisName());
    	xml.addAttribute("yAxisName", this.getYAxisName());
    	xml.addAttribute("num", this.getNum() + "");
    	
    	Element points = xml.addElement(DiscretizedFunc.XML_METADATA_POINTS_NAME);
    	for (int i=0; i<this.getNum(); i++) {
    		Element point = points.addElement(DiscretizedFunc.XML_METADATA_POINT_NAME);
    		point.addAttribute("x", this.getX(i) + "");
    		point.addAttribute("y", this.getY(i) + "");
    	}
    	
    	return root;
    }
    
    public static ArbitrarilyDiscretizedFunc fromXMLMetadata(Element funcElem) {
    	ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
    	
    	String info = funcElem.attributeValue("info");
    	String name = funcElem.attributeValue("name");
    	String xAxisName = funcElem.attributeValue("xAxisName");
    	String yAxisName = funcElem.attributeValue("yAxisName");
    	
    	double tolerance = Double.parseDouble(funcElem.attributeValue("tolerance"));
    	
    	func.setInfo(info);
    	func.setName(name);
    	func.setXAxisName(xAxisName);
    	func.setYAxisName(yAxisName);
    	func.setTolerance(tolerance);
    	
    	Element points = funcElem.element(DiscretizedFunc.XML_METADATA_POINTS_NAME);
    	Iterator<Element> it = points.elementIterator();
    	while (it.hasNext()) {
    		Element point = it.next();
    		double x = Double.parseDouble(point.attributeValue("x"));
    		double y = Double.parseDouble(point.attributeValue("y"));
    		func.set(x, y);
    	}
    	
		return func;
    }
    
    public static void writeSimpleFuncFile(DiscretizedFuncAPI func, String fileName) throws IOException {
    	File outFile = new File(fileName);
		FileWriter fr = new FileWriter(outFile);
		for (int i = 0; i < func.getNum(); ++i)
			fr.write(func.getX(i) + " " + func.getY(i) + "\n");
		fr.close();
    }
    
    public static ArbitrarilyDiscretizedFunc loadFuncFromSimpleFile(String fileName) throws FileNotFoundException, IOException {
		ArrayList<String> fileLines = FileUtils.loadFile(fileName);
		String dataLine;
		StringTokenizer st;
		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();

		for(int i=0;i<fileLines.size();++i) {
			dataLine=(String)fileLines.get(i);
			st=new StringTokenizer(dataLine);
			//using the currentIML and currentProb we interpolate the iml or prob
			//value entered by the user.
			double x = Double.parseDouble(st.nextToken());
			double y= Double.parseDouble(st.nextToken());
			func.set(x, y);
		}
		return func;
	}

}
