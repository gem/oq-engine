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

import org.opensha.commons.data.DataPoint2D;

public class PSXYSymbol extends PSXYElement {
	
	/**
	 * default serial version UID
	 */
	private static final long serialVersionUID = 1l;
	
	public enum Symbol {
		SQUARE ("s"),
		DIAMOND ("d"),
		CIRCLE ("c"),
		STAR ("a"),
		OCTAGON ("g"),
		HEXAGON ("h"),
		INVERTED_TRIANGLE ("i"),
		PENTAGON ("n"),
		CROSS ("x"),
		Y_DASH ("y");
		
		private String val;
		Symbol(String val) {
			this.val = val;
		}
		
		public String val() {
			return val;
		}
	}
	
	private Symbol symbol;
	
	private double width;
	
	private DataPoint2D pt;
	
	/**
	 * No-arg constructor for serialization
	 */
	public PSXYSymbol() {};
	
	public PSXYSymbol(DataPoint2D pt, Symbol symbol, double width) {
		super();
		this.symbol = symbol;
		this.width = width;
		this.pt = pt;
	}
	
	public PSXYSymbol(DataPoint2D pt, Symbol symbol, double width, double penWidth, Color penColor, Color fillColor) {
		super(penWidth, penColor, fillColor);
		this.symbol = symbol;
		this.width = width;
		this.pt = pt;
	}
	
	public String getSymbolString() {
		return "-S" + symbol.val() + width + "i";
	}

	public Symbol getSymbol() {
		return symbol;
	}

	public void setSymbol(Symbol symbol) {
		this.symbol = symbol;
	}

	public double getWidth() {
		return width;
	}

	public void setWidth(double width) {
		this.width = width;
	}

	public DataPoint2D getPoint() {
		return pt;
	}

	public void setPoint(DataPoint2D pt) {
		this.pt = pt;
	}

}
