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

package org.opensha.commons.util.cpt;

import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.dom4j.Element;

/**
 * This class represents a GMT CPT file.
 *
 * @author kevin
 *
 */

public class CPT extends ArrayList<CPTVal> {

	/**
	 * default serial version UID
	 */
	private static final long serialVersionUID = 1l;
	private Color nanColor, belowMinColor, aboveMaxColor, gapColor;
	public Blender blender;
	
//	int nanColor[] = new int[0];

	/**
	 * Constructor which has no colors except for the default nanColor as
	 * Color.ORANGE,gapColor as Color.MAGENTA , belowMin as Color.BLACK, and
	 * aboveMax as Color.WHITE. <b>NOTE: the gapColor and naNColor are not
	 * blended</b>
	 *
	 * Use the ArrayList getters and setter for finer control.
	 *
	 * @see java.util.ArrayList
	 */
	public CPT() {
		super();
		nanColor = Color.BLACK;
		gapColor = Color.BLACK;
		belowMinColor = Color.BLACK;
		aboveMaxColor = Color.BLACK;
		blender = new LinearBlender();
	}

	/**
	 * Sets color to be used when given value is not a number (NaN)
	 *
	 * @see java.awt.Color for more information on rgb values.
	 *
	 * @param r
	 * @param g
	 * @param b
	 */
	public void setNanColor(int r, int g, int b) {
		nanColor = new Color(r, g, b);
	}

	/**
	 * Sets color to be used when given value is not a number (NaN)
	 *
	 * @see java.awt.Color
	 */
	public void setNanColor(Color color) {
		nanColor = color;

	}

	/**
	 * Set The value of the color returned by getColor if the value is below the
	 * range of the CPT class using r,g,b values as used in Color3f.
	 *
	 * @see java.awt.Color
	 *
	 *
	 */
	public void setBelowMinColor(Color color) {
		belowMinColor = color;
	}

	/**
	 * Set The value of the color returned by getColor if the value is above the
	 * range of the CPT class using r,g,b values as used in Color3f.
	 *
	 * @see java.awt.Color
	 *
	 */
	public void setAboveMaxColor(Color color) {
		aboveMaxColor = color;
	}

	/**
	 * Sets the color to be take on for values in the range of the minValue and
	 * maxValue, but without a specified color
	 *
	 * @param color
	 */
	public void setGapColor(Color color) {
		gapColor = color;
	}

	/**
	 * @see setGapColor(Color3f color)
	 * @see java.awt.Color
	 */
	public void setGapColor(int r, int g, int b) {
		gapColor = new Color(r, g, b);
	}

	/**
	 * @see setBelowMinColor(Color3f color)
	 * @see java.awt.Color
	 */
	public void setBelowMinColor(int r, int g, int b) {
		belowMinColor = new Color(r, g, b);
	}

	/**
	 * @see setAboveMaxColor(Color3f color)
	 * @see java.awt.Color
	 */
	public void setAboveMaxColor(int r, int g, int b) {
		aboveMaxColor = new Color(r, g, b);
	}

	/**
	 *
	 * @return The value of the color returned by getColor if the value is above
	 *         the range of the CPT class
	 */
	public Color getAboveMaxColor() {
		return aboveMaxColor;
	}

	/**
	 *
	 * @return The value of the color returned by getColor if the value is below
	 *         the range of the CPT class
	 */
	public Color getBelowMinColor() {
		return belowMinColor;
	}

	/**
	 *
	 * @return the Color3f associated with the minimum value in the CPT color
	 *         range
	 */
	public Color getMinColor() {
		if (this.size() > 0) {
			return this.get(0).minColor;
		}
		return null;
	}

	/**
	 *
	 * @return the Color3f associated with the maximum value in the CPT color
	 *         range or null if the color is undefined
	 */
	public Color getMaxColor() {
		if (this.size() > 0) {
			return this.get(this.size() - 1).maxColor;
		}
		return null;
	}

	public Color getNaNColor() {
		return nanColor;
	}

	/**
	 * @return the color for values within the range of the CPT val/color
	 *         combination, but unspecified
	 */
	public Color getGapColor() {
		return gapColor;
	}

	/**
	 * This returns a color given a value for this specific CPT file or null if
	 * the color is undefined
	 *
	 * @param value
	 * @return Color corresponding to value
	 */
	public Color getColor(float value) {
		CPTVal cpt_val = getCPTVal(value);

		if (cpt_val != null) {
			if (value == cpt_val.start) {
				return cpt_val.minColor;
			} else if (value == cpt_val.end) {
				return cpt_val.maxColor;
			} else if (value > cpt_val.start && value < cpt_val.end) {
				float adjVal = (value - cpt_val.start)
						/ (cpt_val.end - cpt_val.start);
				return blendColors(cpt_val.minColor, cpt_val.maxColor, adjVal);
			}
		}

		// if we got here, it's not in the CPT file
		if (value < this.get(0).start)
			return getBelowMinColor();
		else if (value > this.get(this.size() - 1).end)
			return getAboveMaxColor();
		else if (Float.isNaN(value))
			return nanColor;
		else {
			return gapColor;
		}
	}

	private Color blendColors(Color smallColor, Color bigColor, float bias) {
		return blender.blend(smallColor, bigColor, bias);

	}

	/**
	 * This loads a CPT file into a CPT object The CPT format can be found here:
	 * http://hraun.vedur.is/~gg/hugb/gmt/doc/html/tutorial/node68.html
	 *
	 * The default overflow and underflow colors are the colors associated with
	 * the min and max values of the CPT file
	 *
	 * @param dataFile
	 * @return
	 * @throws FileNotFoundException
	 * @throws IOException
	 */
	public static CPT loadFromFile(File dataFile)
	throws FileNotFoundException, IOException
	{
		BufferedReader in = new BufferedReader(new FileReader(dataFile));
		return loadFromBufferedReader(in);
	}

	public static CPT loadFromStream(InputStream is)
	throws IOException
	{
		BufferedReader in = new BufferedReader(new InputStreamReader(is));
		return loadFromBufferedReader(in);
	}
	
	private static Color loadColor(StringTokenizer tok) {
		int R = Integer.parseInt(tok.nextToken());
		int G = Integer.parseInt(tok.nextToken());
		int B = Integer.parseInt(tok.nextToken());
		
		return new Color(R, G, B);
	}

	private static CPT loadFromBufferedReader(BufferedReader in)
	throws IOException
	{
		CPT cpt = new CPT();
		String line;
		int lineNumber = 0;
		
		boolean hasMin = false;
		boolean hasMax = false;
		
		while (in.ready()) {
			lineNumber++;
			line = in.readLine().trim();
			
			if (line.length() == 0)
				continue;

			StringTokenizer tok = new StringTokenizer(line);
			int tokens = tok.countTokens();
			char firstChar = line.charAt(0);
			
			try {
				switch (firstChar) {
				case '#':
					// comment
					continue;
				case 'N':
					tok.nextToken();
					cpt.setNanColor(loadColor(tok));
					continue;
				case 'B':
					tok.nextToken();
					cpt.setBelowMinColor(loadColor(tok));
					hasMin = true;
					continue;
				case 'F':
					tok.nextToken();
					cpt.setAboveMaxColor(loadColor(tok));
					hasMax = true;
					continue;
				default:
					if (tokens < 8) {
						System.out.println("Skipping line: " + lineNumber
								+ "! (Comment or not properly formatted.): " + line);
						continue;
					}
					float start = Float.parseFloat(tok.nextToken());
					Color minColor = loadColor(tok);
					float end = Float.parseFloat(tok.nextToken());
					Color maxColor = loadColor(tok);
					
					CPTVal cpt_val = new CPTVal(start, minColor, end, maxColor);
					cpt.add(cpt_val);
				}
			} catch (NumberFormatException e1) {
				System.out.println("Skipping line: " + lineNumber
						+ "! (bad number parse): " + line);
				continue;
			}
			
			if (tokens < 8 || line.charAt(0) == '#') {
				System.out.println("Skipping line: " + lineNumber
						+ "! (Comment or not properly formatted.): " + line);
				continue;
			}
		}

//		Set the colors that will be taken when the file gets a value out of
//		range to a default of the color associate with the minimum value in
//		the range of the CPT file and similarly for the max
		if (!hasMin)
			cpt.setBelowMinColor(cpt.getMinColor());
		if (!hasMax)
			cpt.setAboveMaxColor(cpt.getMaxColor());

		return cpt;
	}

	public static CPT fromXML(Element cptElement)
	{
		CPT cpt = new CPT();

		Element cptValues = cptElement.element("cptValues");
		List<Element> cptVals = cptValues.elements("cptVal");
		for (Element cptValElem:cptVals)
		{
			CPTVal cptVal = CPTVal.fromXML(cptValElem);
			cpt.add(cptVal);
		}

		Element nanColorElem = cptElement.element("nanColor");
		int R = Integer.parseInt(nanColorElem.attributeValue("r"));
		int G = Integer.parseInt(nanColorElem.attributeValue("g"));
		int B = Integer.parseInt(nanColorElem.attributeValue("b"));
		cpt.setNanColor(R, G, B);

		cpt.setBelowMinColor(cpt.getMinColor());
		cpt.setAboveMaxColor(cpt.getMaxColor());

		return cpt;
	}

	public Element toXML(Element cptElement)
	{
		Element cptValues = cptElement.addElement("cptValues");
		for (int i = 0; i < this.size(); i++)
		{
			Element cptVal = cptValues.addElement("cptVal");
			cptVal = this.get(i).toXML(cptVal);
		}

		Element nanColorElem = cptElement.addElement("nanColor");
		nanColorElem.addAttribute("r", Integer.valueOf(Math.round(nanColor.getRed() * 255.0f)).toString());
		nanColorElem.addAttribute("g", Integer.valueOf(Math.round(nanColor.getGreen() * 255.0f)).toString());
		nanColorElem.addAttribute("b", Integer.valueOf(Math.round(nanColor.getBlue() * 255.0f)).toString());

		return cptElement;
	}
	
	private String getCPTValStr(CPTVal val) {
		return val.start + "\t" + val.minColor.getRed() + "\t" + val.minColor + "";
	}
	
	public void writeCPTFile(String fileName) throws IOException {
		FileWriter fw = new FileWriter(fileName);
		fw.write(this.toString());
		fw.close();
	}

	/**
	 * @return this objects blender
	 */
	public Blender getBlender() {
		return blender;
	}

	/**
	 * @param blender,
	 *            the blender to be used
	 * @see interface Blender
	 */

	public void setBlender(Blender blender) {
		this.blender = blender;
	}

	/**
	 * Does a lookup for the color range (CPTVal) associated with this value
	 *
	 * @param containingValue
	 * @return null if the color range was not found
	 */
	public CPTVal getCPTVal(float value) {
		for (CPTVal val : this) {
			if (val.contains(value)) {
				return val;
			}
		}
		return null;
	}

	/**
	 * Adds the cpt_val into this list. Note it will overwrite and replace
	 * intersecting cpt_vals
	 *
	 * @param cpt_val
	 * @return
	 */
	public void setCPTVal(CPTVal newcpt) {
		// We rely on the correct ordering of CPTVals in this list and the
		// intersecting list

		// Is the list empty?
		if (this.size() == 0) {
			// Add to the list
			this.add(newcpt);
		}
		// Is the newcpt supposed to be at the beginning of the list?
		else if (newcpt.compareTo(get(0)) < 0) {
			// Then add to the beginning
			this.add(0, newcpt);
		}
		// Is the newcpt supposed to be at the end of the list?
		else if (newcpt.compareTo(get(this.size() - 1)) > 0) {
			// Then add to the end
			this.add(newcpt);
		}
		// The newcpt must be in the middle of the range or intersecting with
		// the head or tail so fix conflicts by removing and trimming other
		//cpt_vals in the list
		else {
			// There are 4 cases we need to handle:
			// There are cur values contained in the range of newcpt
			// -The cur overlaps with the head or tail of newcpt
			// -The cur is within newcpt
			// The range of newcpt is contained within a cur value

			boolean added = false;
			ListIterator<CPTVal> iter = this.listIterator();

			while (iter.hasNext()) {
				CPTVal cur = iter.next();

				// If cur is completely within the range of the new value remove
				// it
				// NStart--cStart--cEnd--NEnd
				if (newcpt.start <= cur.start && cur.end <= newcpt.end) {
					// Can happen multiple times
					iter.remove();
					if (!added) {
						iter.add(newcpt);
						added = true;
					}
				}
				// If cur is intersecting with the head of the newcpt
				// cStart--NStart--cEnd--NEnd
				else if (newcpt.start <= cur.end && cur.end <= newcpt.end) {
					// This condition should only happen once
					cur.end = newcpt.start;
					if (cur.start == cur.end) {
						iter.remove();
					}
					// We couldn't possible have added before this
					iter.add(newcpt);
					added = true;
					// Now the loop will continue and cleanup
				}
				// If cur is intersecting with the tail of the newcpt
				// NStart--cStart--NEnd--cEnd
				else if (newcpt.start <= cur.start && cur.start <= newcpt.end) {
					cur.start = newcpt.end;
					if (cur.start == cur.end) {
						iter.remove();
					}
					if (!added) {
						iter.add(newcpt);
						added = true;
					}
					return;
				}
				// cur contains newcpt
				// cStart--NStart--NEnd--cEnd
				else if (cur.start <= newcpt.start && newcpt.end <= cur.end) {
					// Create a new node for the second half of cur and truncate
					// cur
					CPTVal newcur = new CPTVal(newcpt.end, newcpt.maxColor,
							cur.end, cur.maxColor);
					cur.end = newcpt.start;
					if (cur.end == cur.start) {
						iter.remove();
					}
					if (newcur.start != newcur.end) {
						iter.add(newcur);
					}
					// now put newcpt in the middle
					iter.add(newcpt);
					// added = true; //no need to go through the rest of the
					// list
					return;
				}
			}
		}
	}

	public void paintGrid(BufferedImage bi) {
		int width = bi.getWidth();
		int height = bi.getHeight();
		Graphics2D g = bi.createGraphics();

		// Fill in with the gapColor by default
		Color color = getGapColor();
		g.setColor(color);
		g.fillRect(0, 0, width, height);

		//Make sure there are CPTVals to get color information from
		if (size() > 0) {

			// Establish the increase in value for each change in pixel
			float minStart = this.get(0).start;
			float maxEnd = this.get(size() - 1).end;
			float valsPerPixel = (maxEnd - minStart) / width; //To ensure that the last value is included

			// If we've lit pixel +1 pixels the next pixel is lit with the color
			// from valsPerPixel*x + minStart
			int pixel = 0;
			float val = 0;

			for( CPTVal cptval: this ) {
				// Get the CPTVals in order and get then paint the associated lines with colors corresponding to the range of values of that CPTVal
				float start = cptval.start;
				float end = cptval.end;
				Color startC = cptval.minColor;
				Color endC = cptval.maxColor;

				//Compute the value associated with the current pixel
				val = pixel * valsPerPixel + minStart;

				//If there is a gap in coverage skip the gap
				while( val < start){
					pixel++;
					val = pixel * valsPerPixel + minStart;
				}

				//If the CPTVal has only one value in its range just paint one line
				if(start == end){
					//Draw line and go to next pixel
					g.setColor(startC);
					g.drawLine(pixel, 0, pixel, height);
					pixel++;
					continue;
				}

				//Start filling in the gradient
				while (pixel < width && start <= val && val <= end ) {
					//Calculate color of line
					float bias = (val - start) / (end - start);
					Color blend = blender.blend(startC, endC, bias);

					//Draw line and go to next pixel
					g.setColor(blend);
					g.drawLine(pixel, 0, pixel, height);

					pixel++;
					val = pixel * valsPerPixel + minStart;
				}
			}
		}
	}
	
	public static String tabDelimColor(Color color) {
		return color.getRed() + "\t" + color.getGreen() + "\t" + color.getBlue();
	}

	//TODO handle B F N values
	public String toString() {
		String out= 	"# CPT File generated by OpenSHA: " + this.getClass().getName() + "\n";
		out += 			"# Date: " + (new Date()) + "\n";
		for(CPTVal v: this){
			out += v.toString() + "\n";
		}
		if (belowMinColor != null)
			out += "B\t" + tabDelimColor(belowMinColor) + "\n";
		if (aboveMaxColor != null)
			out += "F\t" + tabDelimColor(aboveMaxColor) + "\n";
		if (nanColor != null)
			out += "N\t" + tabDelimColor(nanColor) + "\n";
		//Output out of bounds colors
		return out;
	}
	
	public static void main(String args[]) throws FileNotFoundException, IOException {
		CPT cpt = CPT.loadFromFile(new File("/usr/share/gmt/cpt/GMT_seis.cpt"));
		System.out.println(cpt);
	}
}
