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

package org.opensha.sha.earthquake.util;

import java.text.Collator;
import java.util.Comparator;

import org.opensha.sha.earthquake.ProbEqkSource;

public class EqkSourceNameComparator implements Comparator<ProbEqkSource> {
	// A Collator does string comparisons
	private Collator c = Collator.getInstance();
	
	/**
	 * This is called when you do Arrays.sort on an array or Collections.sort on a collection (IE ArrayList).
	 * 
	 * It simply compares their names using a Collator. 
	 */
	public int compare(ProbEqkSource s1, ProbEqkSource s2) {
		// let the Collator do the string comparison, and return the result
		return c.compare(s1.getName(), s2.getName());
	}

}
