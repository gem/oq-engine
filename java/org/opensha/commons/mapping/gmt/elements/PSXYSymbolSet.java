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
import java.util.ArrayList;

import org.opensha.commons.util.cpt.CPT;

public class PSXYSymbolSet extends PSXYElement {
	
	/**
	 * default serial version UID
	 */
	private static final long serialVersionUID = 1l;
	
	private CPT cpt;
	private ArrayList<PSXYSymbol> symbols;
	private ArrayList<Double> vals;
	
	public PSXYSymbolSet() {
		super(0, null, null);
		symbols = new ArrayList<PSXYSymbol>();
		vals = new ArrayList<Double>();
	}
	
	public PSXYSymbolSet(CPT cpt, ArrayList<PSXYSymbol> symbols, ArrayList<Double> vals) {
		this(cpt, symbols, vals, 0, null, null);
	}
	
	public PSXYSymbolSet(CPT cpt, ArrayList<PSXYSymbol> symbols, ArrayList<Double> vals,
					double penWidth, Color penColor, Color fillColor) {
		super(penWidth, penColor, fillColor);
		this.cpt = cpt;
		this.symbols = symbols;
		this.vals = vals;
	}
	
	public void addSymbol(PSXYSymbol symbol, double val) {
		symbols.add(symbol);
		vals.add(val);
	}

	public CPT getCpt() {
		return cpt;
	}

	public void setCpt(CPT cpt) {
		this.cpt = cpt;
	}

	public ArrayList<PSXYSymbol> getSymbols() {
		return symbols;
	}

	public void setSymbols(ArrayList<PSXYSymbol> symbols) {
		this.symbols = symbols;
	}

	public ArrayList<Double> getVals() {
		return vals;
	}

	public void setVals(ArrayList<Double> vals) {
		this.vals = vals;
	}

}
