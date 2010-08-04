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

package org.opensha.commons.data.siteData;

import java.io.IOException;
import java.util.ArrayList;

import org.junit.Test;
import org.opensha.commons.data.siteData.impl.CVM2BasinDepth;
import org.opensha.commons.data.siteData.impl.CVM4BasinDepth;
import org.opensha.commons.data.siteData.impl.USGSBayAreaBasinDepth;
import org.opensha.commons.data.siteData.impl.WillsMap2000TranslatedVs30;
import org.opensha.commons.data.siteData.impl.WillsMap2006;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

import static org.junit.Assert.*;

public class TestSiteDataProviders_Operational {
	
	private static final boolean D = true;
	
	private Location loc1 = new Location(34d, -118d);
	private Location loc2 = new Location(34d, -120d);
	private Location loc3 = new Location(36d, -120d);
	private Location loc4 = new Location(38d, -123d);
	private Location loc5 = new Location(0d, 0d);
	
	private LocationList locs = new LocationList();
	
	public TestSiteDataProviders_Operational() {
		locs.add(loc1);
		locs.add(loc2);
		locs.add(loc3);
		locs.add(loc4);
		locs.add(loc5);
	}
	
	/**
	 * This tests that values were returned, and at least one is valid
	 * 
	 * @param prov
	 * @throws IOException
	 */
	private void testProv(SiteDataAPI prov) throws IOException {
		ArrayList<?> vals = prov.getValues(locs);
		
		boolean hasOneValid = false;
		for (int i=0; i<vals.size(); i++) {
			Object serverGroupVal = vals.get(i);
			
			// just to make sure that the server gives the save values individually as it does in a list
			Object serverSingleVal = prov.getValue(locs.get(i));
			
			assertEquals(serverSingleVal, serverGroupVal);
			if (prov.isValueValid(serverSingleVal))
				hasOneValid = true;
		}
		assertTrue("At least one 'valid' value per test is expected.", hasOneValid);
	}
	
	@Test
	public void testCVM2() throws IOException {
		CVM2BasinDepth prov = new CVM2BasinDepth();
		
		testProv(prov);
	}
	
	@Test
	public void testCVM4_2_5() throws IOException {
		CVM4BasinDepth prov = new CVM4BasinDepth(SiteDataAPI.TYPE_DEPTH_TO_2_5);
		
		testProv(prov);
	}
	
	@Test
	public void testCVM4_1_0() throws IOException {
		CVM4BasinDepth prov = new CVM4BasinDepth(SiteDataAPI.TYPE_DEPTH_TO_1_0);
		
		testProv(prov);
	}
	
	@Test
	public void testUSGSBayArea_2_5() throws IOException {
		USGSBayAreaBasinDepth prov = new USGSBayAreaBasinDepth(SiteDataAPI.TYPE_DEPTH_TO_2_5);
		
		testProv(prov);
	}
	
	@Test
	public void testUSGSBayArea_1_0() throws IOException {
		USGSBayAreaBasinDepth prov = new USGSBayAreaBasinDepth(SiteDataAPI.TYPE_DEPTH_TO_1_0);
		
		testProv(prov);
	}
	
	@Test
	public void testWills2006() throws IOException {
		WillsMap2006 prov = new WillsMap2006();
		
		testProv(prov);
	}
	
	@Test
	public void testWills2000() throws IOException {
		WillsMap2000TranslatedVs30 prov = new WillsMap2000TranslatedVs30();
		
		testProv(prov);
	}
}
