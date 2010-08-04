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

package org.opensha.sha.cybershake.plot;

import org.opensha.commons.mapping.gmt.elements.PSXYSymbol;
import org.opensha.sha.cybershake.db.CybershakeSite;

public class ScatterSymbol {
	
	public static final String SYMBOL_SQUARE = PSXYSymbol.Symbol.SQUARE.val();
	public static final String SYMBOL_DIAMOND = PSXYSymbol.Symbol.DIAMOND.val();
	public static final String SYMBOL_CIRCLE = PSXYSymbol.Symbol.CIRCLE.val();
	public static final String SYMBOL_STAR = PSXYSymbol.Symbol.STAR.val();
	public static final String SYMBOL_OCTAGON = PSXYSymbol.Symbol.OCTAGON.val();
	public static final String SYMBOL_HEXAGON = PSXYSymbol.Symbol.HEXAGON.val();
	public static final String SYMBOL_INVERTED_TRIANGLE = PSXYSymbol.Symbol.INVERTED_TRIANGLE.val();
	public static final String SYMBOL_PENTAGON = PSXYSymbol.Symbol.PENTAGON.val();
	public static final String SYMBOL_CROSS = PSXYSymbol.Symbol.CROSS.val();
	public static final String SYMBOL_Y_DASH = PSXYSymbol.Symbol.Y_DASH.val();
	
	public static final String SYMBOL_INVISIBLE = "DO NOT DISPLAY";
	
	String sym;
	
	int siteTypeID;
	
	double scale = 1;
	
	public ScatterSymbol(String sym, int siteTypeID, double scale) {
		this.sym = sym;
		this.siteTypeID = siteTypeID;
		this.scale = scale;
	}
	
	public ScatterSymbol(String sym, int siteTypeID) {
		this(sym, siteTypeID, 1d);
	}
	
	public boolean use(CybershakeSite site) {
		return site.type_id == siteTypeID;
	}
	
	public String getSymbol() {
		return sym;
	}
	
	public void setSymbol(String symbol) {
		this.sym = symbol;
	}
	
	public int getSiteTypeID() {
		return siteTypeID;
	}
	
	public double getScaleFactor() {
		return scale;
	}
}
