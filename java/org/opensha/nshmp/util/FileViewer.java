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

package org.opensha.nshmp.util;

import org.opensha.nshmp.sha.io.NEHRP_Record;

public class FileViewer {
	private static float lat;
	private static float lon;
	private static float vals[];
	private static String fileName = "/Users/emartinez/Desktop/rndFiles/2003-PRVI-Retrofit-10-050-a.rnd";
	private static String TAB = "\t";
	public static void main (String args[]) {
		NEHRP_Record rec = new NEHRP_Record();
		for ( int i = 1; i < 16267; ++i ) {
			rec.getRecord(fileName, i);
			lat = rec.getLatitude();
			lon = rec.getLongitude();
			vals = rec.getPeriods();
			System.out.println("" + i + "" + TAB + "" + lat + "" + TAB + "" + lon + "" + TAB + vals[0] + "" + TAB + "" + vals[1]);
		}
	}
}
