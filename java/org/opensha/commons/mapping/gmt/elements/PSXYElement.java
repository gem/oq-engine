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

import org.opensha.commons.mapping.gmt.GMT_MapGenerator;

public abstract class PSXYElement implements Serializable {
	
	/**
	 * default serial version UID
	 */
	private static final long serialVersionUID = 1l;
	
	private double penWidth = 1d;
	private Color penColor = Color.BLACK;
	
	private Color fillColor = null;
	
	public PSXYElement() {
		
	}
	
	public PSXYElement(double penWidth, Color penColor, Color fillColor) {
		this.penWidth = penWidth;
		this.penColor = penColor;
		this.fillColor = fillColor;
	}
	
	public String getPenString() {
		if (penColor == null)
			return "-W-";
		if (penWidth <= 0)
			return "-W-";
		
		return "-W" + penWidth + "/" + GMT_MapGenerator.getGMTColorString(penColor);
	}
	
	public String getFillString() {
		if (fillColor == null)
			return "";
		
		return "-G" + GMT_MapGenerator.getGMTColorString(fillColor);
	}

	public double getPenWidth() {
		return penWidth;
	}

	public void setPenWidth(double penWidth) {
		this.penWidth = penWidth;
	}

	public Color getPenColor() {
		return penColor;
	}

	public void setPenColor(Color penColor) {
		this.penColor = penColor;
	}

	public Color getFillColor() {
		return fillColor;
	}

	public void setFillColor(Color fillColor) {
		this.fillColor = fillColor;
	}

}
