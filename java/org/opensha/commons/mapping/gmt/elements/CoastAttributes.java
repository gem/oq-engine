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

package org.opensha.commons.mapping.gmt.elements;

import java.awt.Color;
import java.io.Serializable;

public class CoastAttributes implements Serializable {
	/**
	 * default serial version UID
	 */
	private static final long serialVersionUID = 1l;
	
	private Color fillColor = new Color(17, 73, 71);
	
	private Color lineColor = fillColor;
	private double lineSize = 1d;
	
	/**
	 * Default constructor, for filled ocean
	 */
	public CoastAttributes() {
		
	}
	
	/**
	 * Draw coastline only, black with the specified size
	 * 
	 * @param lineSize
	 */
	public CoastAttributes(double lineSize) {
		this(Color.BLACK, lineSize);
	}
	
	/**
	 * Draw coastline only with the specified color/size
	 * 
	 * @param lineColor
	 * @param lineSize
	 */
	public CoastAttributes(Color lineColor, double lineSize) {
		this.lineColor = lineColor;
		this.lineSize = lineSize;
		this.fillColor = null;
	}
	
	/**
	 * Fill the coast with the specified color, the line will be drawn with the same color.
	 * 
	 * @param fillColor
	 */
	public CoastAttributes(Color fillColor) {
		this.lineColor = fillColor;
		this.lineSize = 1d;
		this.fillColor = fillColor;
	}

	public Color getFillColor() {
		return fillColor;
	}

	public void setFillColor(Color fillColor) {
		this.fillColor = fillColor;
	}

	public Color getLineColor() {
		return lineColor;
	}

	public void setLineColor(Color lineColor) {
		this.lineColor = lineColor;
	}

	public double getLineSize() {
		return lineSize;
	}

	public void setLineSize(double lineSize) {
		this.lineSize = lineSize;
	}
}
