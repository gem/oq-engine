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

package org.opensha.commons.geo;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import static org.opensha.commons.geo.LocationUtils.TOLERANCE;

import java.awt.Color;
import java.awt.geom.Area;
import java.awt.geom.PathIterator;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.List;

import org.apache.commons.math.util.MathUtils;
import org.junit.BeforeClass;
import org.junit.Test;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;

public class RegionTest {
	
	// TODO need to test immutability of border

	// Notes:
	// ===============================================================
	// Don't need to test Dateline-spanning and pole-wrapping cases as
	// they've been declared as unsupported in docs.
	//
	// The 'region creation' parts of the constructor tests were built by 
	// creating a kml output file to visually verify correct border creation.
	// The vertices were then culled from the KML file and are stored in 
	// static arrays at the end of this file as.
	// ===============================================================
	
	// octagonal region
	static Region octRegion;
	static LocationList octRegionList;
	// small rect region (regionLocLoc)
	static Region smRectRegion1;
	// small rect region (regionLocLoc)
	static Region smRectRegion2;
	// small rect region (regionLocLoc)
	static Region smRectRegion3;
	// large rect region (regionLocList)
	static Region lgRectRegion;
	// large rect region (regionLocListBorderType)
	static Region lgRectMercRegion;
	// large rect region (regionLocListBorderType)
	static Region lgRectGCRegion;
	// buffered region (regionLocListDouble)
	static Region buffRegion;
	// circular region (regionLocDouble)
	static Region circRegion;
	// small circular region
	static Region smCircRegion;
	// cicle-lgRect intersect
	static Region circLgRectIntersect;
	// cicle-lgRect union
	static Region circLgRectUnion;
	// smRect-lgRect intersect
	static Region smRectLgRectIntersect;
	// smRect-lgRect union
	static Region smRectLgRectUnion;
	// circle-smRect intersect
	static Region circSmRectIntersect;
	// circle-smRect union
	static Region circSmRectUnion;
	// interior region (smRectRegion3 added to lgRectRegion)
	static Region interiorRegion;
	// multi interior region
	static Region multiInteriorRegion;

	@BeforeClass
	public static void setUp() {
		octRegionList = new LocationList();
		octRegionList.add(new Location(25,-115));
		octRegionList.add(new Location(25,-110));
		octRegionList.add(new Location(30,-105));
		octRegionList.add(new Location(35,-105));
		octRegionList.add(new Location(40,-110));
		octRegionList.add(new Location(40,-115));
		octRegionList.add(new Location(35,-120));
		octRegionList.add(new Location(30,-120));
		octRegion  = new Region(octRegionList, null);
		
		Location a = new Location(39,-117);
		Location b = new Location(41,-113);
		smRectRegion1 = new Region(a,b);
		
		// offset from smRectRegion1; for testing interior overlap
		a = new Location(40,-116);
		b = new Location(42,-112);
		smRectRegion2 = new Region(a,b);

		LocationList ll = new LocationList();
		ll.add(new Location(40,-116));
		ll.add(new Location(40,-112));
		ll.add(new Location(42,-112));
		ll.add(new Location(42,-116));
		smRectRegion3 = new Region(ll, BorderType.MERCATOR_LINEAR);

		a = new Location(35,-125);
		b = new Location(45,-105);
		lgRectRegion = new Region(a,b);
		
		ll = new LocationList();
		ll.add(new Location(35,-125));
		ll.add(new Location(35,-105));
		ll.add(new Location(45,-105));
		ll.add(new Location(45,-125));
		lgRectMercRegion = new Region(ll, BorderType.MERCATOR_LINEAR);
		lgRectGCRegion = new Region(ll, BorderType.GREAT_CIRCLE);

		Location center = new Location(35, -125);
		circRegion = new Region(center, 400);
		Location smCenter = new Location(43, -110);
		smCircRegion = new Region(smCenter, 100);
		
		ll = new LocationList();
		ll.add(new Location(35,-125));
		ll.add(new Location(42,-119));
		ll.add(new Location(40,-113));
		ll.add(new Location(45,-105));
		buffRegion = new Region(ll,100);
		
		// unions and intersections
		circLgRectIntersect = Region.intersect(lgRectMercRegion, circRegion);
		circLgRectUnion = Region.union(lgRectMercRegion, circRegion);
		smRectLgRectIntersect = Region.intersect(lgRectMercRegion, smRectRegion1);
		smRectLgRectUnion = Region.union(lgRectMercRegion, smRectRegion1);
		circSmRectIntersect = Region.intersect(circRegion, smRectRegion1);
		circSmRectUnion = Region.intersect(circRegion, smRectRegion1);
		
		// interior
		interiorRegion = new Region(lgRectRegion);
		interiorRegion.addInterior(smRectRegion3);
		interiorRegion.addInterior(smCircRegion);
		
	}

	@Test
	public final void testRegionLocationLocation() {
		
		// initialization tests
		Location L1 = new Location(32,112);
		Location L2 = new Location(32,118);
		Location L3 = new Location(34,118);
		try {
			Region r = new Region(L1,L2);
			fail("Same lat values not caught");
		} catch (IllegalArgumentException iae) {}
		try {
			Region r = new Region(L2,L3);
			fail("Same lon values not caught");
		} catch (IllegalArgumentException iae) {}
		try {
			L1 = null;
			L2 = null;
			Region r = new Region(L1,L2);
			fail("Null argument not caught");
		} catch (NullPointerException npe) {}
		
		// region creation tests
		LocationList ll1 = smRectRegion1.getBorder();
		LocationList ll2 = createLocList(regionLocLocDat);
		assertTrue(ll1.equals(ll2));
		
		// test that addition of additional N and E offset for insidedness
		// testing is not applied to borders at 90N and 180E
		Location L4 = new Location(80,170);
		Location L5 = new Location(90,170);
		Location L6 = new Location(90,180);
		Location L7 = new Location(80,180);
		Region r1 = new Region(L4, L6);
		LocationList locList1 = new LocationList();
		locList1.add(L4);
		locList1.add(L5);
		locList1.add(L6);
		locList1.add(L7);
		Region r2 = new Region(locList1, BorderType.MERCATOR_LINEAR);
		assertTrue(r1.equals(r2));
		
		// and is applied to other borders
		Location L8 = new Location(80,170);
		Location L9 = new Location(89,170);
		Location L10 = new Location(89,179);
		Location L11 = new Location(80,179);
		Region r3 = new Region(L8, L10);
		LocationList locList2 = new LocationList();
		locList2.add(L8);
		locList2.add(L9);
		locList2.add(L10);
		locList2.add(L11);
		Region r4 = new Region(locList2, BorderType.MERCATOR_LINEAR);
		assertTrue(!r3.equals(r4));
		
		// test serialization
		try {
			// write it
			File objPersist = new File("test_serilaize.obj");
			ObjectOutputStream out = new ObjectOutputStream(
					new FileOutputStream(objPersist));
	        out.writeObject(octRegion);
	        out.close();
	        // read it
	        ObjectInputStream in = new ObjectInputStream(
					new FileInputStream(objPersist));
	        Region r_in = (Region) in.readObject();
	        in.close();
	        assertTrue(octRegion.equals(r_in));
	        objPersist.delete();
		} catch (IOException ioe) {
			fail("Serialization Failed: " + ioe.getMessage());
		} catch (ClassNotFoundException cnfe) {
			fail("Deserialization Failed: " + cnfe.getMessage());
		}
	}

	@Test
	public final void testRegionLocationListBorderType() {
		// null args
		LocationList ll = new LocationList();
		try {
			ll = null;
			Region r = new Region(
					ll, BorderType.MERCATOR_LINEAR);
			fail("Null argument not caught");
		} catch (NullPointerException npe) {}
		
		// too short location list
		ll = new LocationList();
		ll.add(new Location(35,-125));
		ll.add(new Location(35,-75));
		try {
			Region r = new Region(ll, null);
			fail("Location list too short  not caught");
		} catch (IllegalArgumentException iae) {}
		
		// check that start point repeated at end of list is removed
		ll.add(new Location(45,-75));
		ll.add(new Location(35,-125));
		Region rectRegionStartRepeat = new Region(ll, null);
		assertTrue("Repeated start point not clipped",
				rectRegionStartRepeat.getBorder().size() == 3);

		// no-area location list
		ll = new LocationList();
		ll.add(new Location(35,-125));
		ll.add(new Location(35,-124));
		ll.add(new Location(35,-123));
		try {
			Region r = new Region(ll, null);
			fail("Empty Region not caught");
		} catch (IllegalArgumentException iae) {}
			
		// non-singular location list
		ll = new LocationList();
		ll.add(new Location(35,-125));
		ll.add(new Location(35,-124));
		ll.add(new Location(36,-125));
		ll.add(new Location(36,-124));
		try {
			Region r = new Region(ll, null);
			fail("Non-singular Region not caught");
		} catch (IllegalArgumentException iae) {}
				
		// region creation test
		LocationList ll1 = lgRectMercRegion.getBorder();
		LocationList ll2 = createLocList(regionLocListMercatorDat);
		assertTrue(ll1.equals(ll2));
		
		ll1 = lgRectGCRegion.getBorder();
		ll2 = createLocList(regionLocListGreatCircleDat);
		assertTrue(ll1.equals(ll2));
	}

	@Test
	public final void testRegionLocationDouble() {
		Location L1 = new Location(0,0,0);
		try {
			L1 = null;
			Region gr = new Region(L1, 50);
			fail("Null argument not caught");
		} catch (NullPointerException npe) {}
		try {
			L1 = new Location(0,0,0);
			Region gr = new Region(L1, 1001);
			fail("Radius too high not caught");
		} catch (IllegalArgumentException iae) {}
		try {
			L1 = new Location(0,0,0);
			Region gr = new Region(L1, 0);
			fail("Radius too low not caught");
		} catch (IllegalArgumentException iae) {}
		
		// region creation test
		LocationList ll1 = circRegion.getBorder();
		LocationList ll2 = createLocList(regionCircularDat);
		assertTrue(ll1.equals(ll2));
	}

	@Test
	public final void testRegionLocationListDouble() {
		LocationList ll = new LocationList();
		try {
			Region gr = new Region(ll, 50);
			fail("Empty location list not caught");
		} catch (IllegalArgumentException iae) {}
		ll.add(new Location(0,0,0));
		try {
			Region gr = new Region(ll, 501);
			fail("Buffer too high not caught");
		} catch (IllegalArgumentException iae) {}
		try {
			Region gr = new Region(ll, 0);
			fail("Buffer too low not caught");
		} catch (IllegalArgumentException iae) {}
		ll = null;
		try {
			Region gr = new Region(ll, 50);
			fail("Null argument not caught");
		} catch (NullPointerException npe) {}

		// region creation test
		LocationList ll1 = buffRegion.getBorder();
		LocationList ll2 = createLocList(regionBufferDat);
		assertTrue(ll1.equals(ll2));
	}

	@Test
	public final void testRegionRegion() {
		circRegion.setName("Cicle Region");
		Region newCircle = new Region(circRegion);
		assertTrue(newCircle.equals(circRegion)); // just tests areas
		// also test transfer of name and border data
		assertTrue(newCircle.getName().equals(circRegion.getName()));
		assertTrue(newCircle.getBorder().equals(circRegion.getBorder()));
		// test that interior gets transferred
		Region newInterior = new Region(interiorRegion);
		assertTrue(newInterior.equals(interiorRegion)); // just tests areas
		assertTrue(newInterior.getBorder().equals(interiorRegion.getBorder()));
		// test that locList interiors match
		List<LocationList> newInteriors = newInterior.getInteriors();
		List<LocationList> interiors = interiorRegion.getInteriors();
		for (int i=0; i<newInteriors.size(); i++) {
			assertTrue(newInteriors.get(i).equals(interiors.get(i)));
		}
		
		// null case
		try {
			Region r1 = null;
			Region r2 = new Region(r1);
			fail("Null argument not caught");
		} catch (NullPointerException npe) {}
		
		// re-test serialization to check region with interior
		try {
			// write it
			File objPersist = new File("test_serilaize.obj");
			ObjectOutputStream out = new ObjectOutputStream(
					new FileOutputStream(objPersist));
	        out.writeObject(interiorRegion);
	        out.close();
	        // read it
	        ObjectInputStream in = new ObjectInputStream(
					new FileInputStream(objPersist));
	        Region r_in = (Region) in.readObject();
	        in.close();
	        assertTrue(interiorRegion.equals(r_in));
	        objPersist.delete();
		} catch (IOException ioe) {
			fail("Serialization Failed: " + ioe.getMessage());
		} catch (ClassNotFoundException cnfe) {
			fail("Deserialization Failed: " + cnfe.getMessage());
		}
		
	}
	
	@Test
	public final void testContainsLocation() {
		
		// insidedness testing is largely unnecessary as we can assume
		// java.awt.Area handles contains correctly. We do want to check
		// that great circle borders are being created correctly and
		// test that here.
				
		Location containsLoc1 = new Location(35.1,-115); // bottom edge
		Location containsLoc2 = new Location(45.1,-115); // top edge
		
		// mercator
		assertTrue(lgRectMercRegion.contains(containsLoc1));
		assertTrue(!lgRectMercRegion.contains(containsLoc2));
		// great circle
		assertTrue(!lgRectGCRegion.contains(containsLoc1));
		assertTrue(lgRectGCRegion.contains(containsLoc2));

		// also need to test that the small offset added to 'rectangular'
		// regions leads to inclusion of points that fall on the north and
		// east borders; also check points on the south and west to be safe
		Region rectRegionLocLoc = new Region(
				new Location(35,-105), new Location(45,-125));
		Location containsEloc = new Location(40,-105);
		Location containsNloc = new Location(45,-115);
		Location containsSloc = new Location(35,-115);
		Location containsWloc = new Location(40,-125);
		
		assertTrue(rectRegionLocLoc.contains(containsEloc));
		assertTrue(rectRegionLocLoc.contains(containsNloc));
		assertTrue(rectRegionLocLoc.contains(containsSloc));
		assertTrue(rectRegionLocLoc.contains(containsWloc));

		assertTrue(!lgRectMercRegion.contains(containsEloc));
		assertTrue(!lgRectMercRegion.contains(containsNloc));
		assertTrue(lgRectMercRegion.contains(containsSloc));
		assertTrue(lgRectMercRegion.contains(containsWloc));
		
		//fail()
	}
	
	@Test
	public final void testContainsRegion() {
		assertTrue(lgRectMercRegion.contains(smRectRegion1));
		assertTrue(!circRegion.contains(smRectRegion1));
		assertTrue(!lgRectMercRegion.contains(circRegion));
	}

	@Test
	public final void testIsRectangular() {
		assertTrue("N/A, covered by Area.isRectangular()", true);
	}
	
	@Test
	public final void testAddInterior() {
		//exception - null arg
		try {
			octRegion.addInterior(null);
			fail("Null argument not caught");
		} catch (NullPointerException e) {}
		//exception - supplied has interior (non-singular)
		try {
			octRegion.addInterior(interiorRegion);
			fail("Illegal argument not caught");
		} catch (IllegalArgumentException e) {}
		//exception - contains: supplied exceeds existing
		try {
			smRectRegion1.addInterior(lgRectMercRegion);
			fail("Illegal argument not caught");
		} catch (IllegalArgumentException e) {}
		//exception - contains: supplied overlaps existing
		try {
			lgRectMercRegion.addInterior(circRegion);
			fail("Illegal argument not caught");
		} catch (IllegalArgumentException e) {}
		//exception - supplied overlaps an existing interior
		try {
			interiorRegion.addInterior(smRectRegion2);
			fail("Illegal argument not caught");
		} catch (IllegalArgumentException e) {}
		
		// test that interiors array remains null after failed add
		assertTrue(octRegion.getInteriors() == null);
		
		// test that interior area was set by checking insidedness of
		// rectangular interior.
		assertTrue(!interiorRegion.contains(new Location(41, -114)));
		// N edge - should include
		assertTrue(interiorRegion.contains(new Location(42, -114)));
		assertTrue(!interiorRegion.contains(new Location(41.9999, -114)));
		// E edge - should include
		assertTrue(interiorRegion.contains(new Location(41, -112)));
		assertTrue(!interiorRegion.contains(new Location(41, -112.0001)));
		// S edge - should NOT include
		assertTrue(!interiorRegion.contains(new Location(40, -114)));
		assertTrue(interiorRegion.contains(new Location(39.9999, -114)));
		// W edge - should NOT include
		assertTrue(!interiorRegion.contains(new Location(41, -116)));
		assertTrue(interiorRegion.contains(new Location(41, -116.0001)));
		// center of small circle
		assertTrue(!interiorRegion.contains(new Location(43, -110)));
		// check some other points that should still be inside
		assertTrue(interiorRegion.contains(new Location(42, -115)));
		assertTrue(interiorRegion.contains(new Location(40, -112)));
		assertTrue(interiorRegion.contains(new Location(38, -115)));
		assertTrue(interiorRegion.contains(new Location(40, -118)));

	}
	
	@Test
	public final void testGetInteriors() {
		assertTrue(octRegion.getInteriors() == null);
		assertTrue(interiorRegion.getInteriors() != null);
		assertTrue(interiorRegion.getInteriors().get(0).equals(
				smRectRegion3.getBorder()));
		assertTrue(interiorRegion.getInteriors().get(1).equals(
				smCircRegion.getBorder()));
	}
	
	@Test(expected=UnsupportedOperationException.class)
	public final void testInteriorBorderListImmutable() {
		interiorRegion.getInteriors().add(new LocationList());
	}
	
	@Test(expected=UnsupportedOperationException.class)
	public final void testInteriorBordersImmutable() {
		interiorRegion.getInteriors().get(0).add(new Location(0,0));
	}
	
	
	@Test
	public final void testGetBorder() {
		// test border is correct
		assertTrue(octRegionList.equals(octRegion.getBorder()));
	}

	@Test(expected=UnsupportedOperationException.class)
	public final void testGetBorderIsImmutable() {
		// test border is immutable
		octRegion.getBorder().add(new Location(0,0));
	}

	@Test
	public final void testEqualsRegion() {
		// compare two differently constructed gridded regions
		// need to take into account offset for rectangular region
		Location l1 = new Location(0, 0);
		Location l2 = new Location(0, 5.000000000001);
		Location l3 = new Location(5.000000000001, 5.000000000001);
		Location l4 = new Location(5.000000000001, 0);
		Location l5 = new Location(5, 5);
		Location anchor = new Location (0.6, 0.6);
		LocationList ll = new LocationList();
		ll.add(l1);
		ll.add(l2);
		ll.add(l3);
		ll.add(l4);
		GriddedRegion gr1 = new GriddedRegion(l1, l5, 0.1, anchor);
		GriddedRegion gr2 = new GriddedRegion(ll, null, 0.1, anchor);
		assertTrue(gr1.equalsRegion(gr2));

		Region interiorRegion2 = new Region(lgRectRegion);
		interiorRegion2.addInterior(smRectRegion3);
		interiorRegion2.addInterior(smCircRegion);
		assertTrue(interiorRegion2.equalsRegion(interiorRegion));
		assertTrue(interiorRegion2.equalsRegion(interiorRegion2));
		// should pass for name change
		interiorRegion2.setName("Name Changed");
		assertTrue(interiorRegion2.equalsRegion(interiorRegion));
	}

	@Test
	public final void testEquals() {
		Region interiorRegion2 = new Region(lgRectRegion);
		interiorRegion2.addInterior(smRectRegion3);
		interiorRegion2.addInterior(smCircRegion);
		assertEquals(interiorRegion2, interiorRegion);
		assertEquals(interiorRegion2, interiorRegion2);
		// should fail for name change 
		interiorRegion2.setName("Name Changed");
		assertTrue(!interiorRegion2.equals(interiorRegion));
		
		assertTrue(smRectRegion3.equals(smRectRegion3));
		assertTrue(!smRectRegion3.equals(new Object()));
	}

	@Test
	public final void testHashCode() {
		Region interiorRegion2 = new Region(lgRectRegion);
		interiorRegion2.addInterior(smRectRegion3);
		interiorRegion2.addInterior(smCircRegion);
		assertEquals(interiorRegion2.hashCode(), interiorRegion.hashCode());
		// change name
		interiorRegion2.setName("Name Changed");
		assertTrue(interiorRegion2.hashCode() != interiorRegion.hashCode());
		// try reverse order locations
		Location l1 = new Location(0,0);
		Location l2 = new Location(0,10);
		Location l3 = new Location(10,10);
		Location l4 = new Location(10,0);
		LocationList ll1 = new LocationList();
		ll1.add(l1);
		ll1.add(l2);
		ll1.add(l3);
		ll1.add(l4);
		LocationList ll2 = new LocationList();
		ll2.add(l1);
		ll2.add(l4);
		ll2.add(l3);
		ll2.add(l2);
		Region r1 = new Region(ll1, null);
		Region r2 = new Region(ll2, null);
		assertEquals(r1.hashCode(), r2.hashCode());
	}
	
	@Test
	public final void testClone() {
		Region interiorRegion2 = interiorRegion.clone();
		assertEquals(interiorRegion2, interiorRegion);
		Region octRegion2 = octRegion.clone();
		assertEquals(octRegion2, octRegion);
	}
	
	@Test
	public final void testGetMinLat() {
		assertTrue(MathUtils.equals(25, octRegion.getMinLat(), TOLERANCE));
	}

	@Test
	public final void testGetMaxLat() {
		assertTrue(MathUtils.equals(40, octRegion.getMaxLat(), TOLERANCE));
	}

	@Test
	public final void testGetMinLon() {
		assertTrue(MathUtils.equals(-120, octRegion.getMinLon(), TOLERANCE));
	}

	@Test
	public final void testGetMaxLon() {
		assertTrue(MathUtils.equals(-105, octRegion.getMaxLon(), TOLERANCE));
	}

	@Test
	public final void testDistanceToLocation() {
		fail("Not yet implemented");
	}

	@Test
	public final void testGetName() {
		assertTrue(octRegion.getName().equals("Unnamed Region"));
	}

	@Test
	public final void testSetName() {
		octRegion.setName("Oct Region");
		assertTrue(octRegion.getName().equals("Oct Region"));
		octRegion.setName("Unnamed Region");
		assertTrue(octRegion.getName().equals("Unnamed Region"));
	}

	@Test
	public final void testToString() {
		// test that string rep of circle is correct
		assertTrue(circRegion.toString().equals(
				"Region\n" + 
				"\tMinimum Lat: 31.402717641688902\n" +
				"\tMinimum Lon: -129.3886473053924\n" + 
				"\tMaximum Lat: 38.59728235831109\n" + 
				"\tMaximum Lon: -120.61135269460763"));
	}
	
	@Test
	public final void testGetGlobalRegion() {
		Region global = Region.getGlobalRegion();
		assertEquals(180, global.getMaxLon(), 0);
		assertEquals(-180, global.getMinLon(), 0);
		assertEquals(90, global.getMaxLat(), 0);
		assertEquals(-90, global.getMinLat(), 0);
	}

	@Test
	public final void testIntersect() {
		//exceptions
		try {
			Region.intersect(null, interiorRegion);
			fail("Null argument not caught");
		} catch (Exception e) {}
		try {
			Region.intersect(interiorRegion, null);
			fail("Illegal argument not caught");
		} catch (Exception e) {}
		
		LocationList ll1, ll2;
		// partial overlap
		ll1 = circLgRectIntersect.getBorder();
		ll2 = createLocList(regionCircRectIntersectDat);
		assertTrue(ll1.equals(ll2));
		// full overlap - this could be tested by matching a statically 
		// defined region using getRegionOutline(), however, Area operations
		// have a tendency to change the winding direction of border in which
		// case LocatonList.compareTo(LocationList) will fail, even though
		// the borders polygons are the same
		ll1 = smRectLgRectIntersect.getBorder();
		ll2 = createLocList(regionSmRectLgRectIntersectDat);
		assertTrue(ll1.equals(ll2));
		
		// no overlap
		assertTrue(circSmRectIntersect == null);
	}
	
	@Test
	public final void testUnion() {
		//exceptions
		try {
			Region.union(null, interiorRegion);
			fail("Null argument not caught");
		} catch (Exception e) {}
		try {
			Region.union(interiorRegion, null);
			fail("Illegal argument not caught");
		} catch (Exception e) {}

		LocationList ll1, ll2;
		// partial overlap
		ll1 = circLgRectUnion.getBorder();
		ll2 = createLocList(regionCircRectUnionDat);
		assertTrue(ll1.equals(ll2));
		// full overlap - this could be tested by matching a statically 
		// defined region using getRegionOutline(), however, Area operations
		// have a tendency to change the winding direction of border in which
		// case LocatonList.compareTo(LocationList) will fail, even though
		// the borders polygons are the same
		ll1 = smRectLgRectUnion.getBorder();
		ll2 = createLocList(regionSmRectLgRectUnionDat);
		assertTrue(ll1.equals(ll2));
		// no overlap
		assertTrue(circSmRectUnion == null);
	}

	// utility method to create LocationList from data arrays
	private static LocationList createLocList(double[] data) {
		LocationList locList = new LocationList();
		for (int i=0; i<data.length; i+=3) {
			Location loc = new Location(data[i+1], data[i], data[i+2]);
			locList.add(loc);
		}
		return locList;
	}

	public static void main(String[] args) {
		
//		Location smCenter = new Location(43, -110);
//		smCircRegion = new Region(smCenter, 100);
//		System.out.println(smCircRegion.getBorder().size());

		
		//RegionTest.setUp();
				
		//LocationList ll = octRegion.getBorder();
		//ll.remove(2);
		//System.out.println(circRegion);
		// The code below was used to create KML files for visual verification
		// of regions. The border vertices were then culled from the KML and 
		// are stored in arrays (below) for use in this test class
		
//		// RECT
//		RegionUtils.regionToKML(smRectRegion1, "RegionLocLoc", Color.ORANGE);
//		
//		// LOCATION LIST border - mercator and great circle
//		RegionUtils.regionToKML(lgRectMercRegion, "RegionLocListMercator", Color.ORANGE);
//		RegionUtils.regionToKML(lgRectGCRegion, "RegionLocListGreatCircle", Color.ORANGE);
//
//		// CIRCLE
//		RegionUtils.regionToKML(circRegion, "RegionLocDouble", Color.ORANGE);
//		RegionUtils.regionToKML(smCircRegion, "RegionLocDoubleSm", Color.ORANGE);
//		
//		// BUFFER
//		RegionUtils.regionToKML(buffRegion,"RegionLocListDouble",Color.ORANGE);
//
//		// CIRCLE-RECT INTERSECT and UNION
//		RegionUtils.regionToKML(circLgRectIntersect,"RegionCircleRectIntersect",Color.ORANGE);
//		RegionUtils.regionToKML(circLgRectUnion,"RegionCircleRectUnion",Color.ORANGE);
//		RegionUtils.regionToKML(smRectLgRectIntersect,"RegionSmRectLgRectIntersect",Color.ORANGE); 
//		RegionUtils.regionToKML(smRectLgRectUnion,"RegionSmRectLgRectUnion",Color.ORANGE);
//		
//		// INTERIOR REGION
//		RegionUtils.regionToKML(interiorRegion,"RegionInterior",Color.ORANGE);
	}
	
	/* debugging utility method to read Area coordinates */
	private static void readArea(Area area) {
		PathIterator pi = area.getPathIterator(null);
		double[] vertex = new double[6];
		while (!pi.isDone()) {
			pi.currentSegment(vertex);
			System.out.println("AreaCoord: " + vertex[1] + " " + vertex[0]);
			pi.next();
		}
	}
	
	// note: always strip the last set of coordinates; they are required to
	// close kml polygons but not needed internally for the region
	// class to define a border shape
	private static double[] regionLocLocDat = new double[] {
		-117.0,39.0,0.0,
		-112.999999999999,39.0,0.0,
		-112.999999999999,41.000000000001,0.0,
		-117.0,41.000000000001,0.0};
	
	private static double[] regionLocListMercatorDat = new double[] {
		-125.00000000000001,35.0,0.0,
		-105.00000000000001,35.0,0.0,
		-105.00000000000001,45.0,0.0,
		-125.00000000000001,45.0,0.0};
	
	private static double[] regionLocListGreatCircleDat = new double[] {
		-125.00000000000001,45.0,0.0,
		-125.00000000000001,44.10067941042222,0.0,
		-125.00000000000001,43.20135882084444,0.0,
		-125.00000000000001,42.30203823126668,0.0,
		-125.00000000000001,41.40271764168891,0.0,
		-125.00000000000001,40.50339705211114,0.0,
		-125.00000000000001,39.604076462533364,0.0,
		-125.00000000000001,38.704755872955594,0.0,
		-125.00000000000001,37.80543528337782,0.0,
		-125.00000000000001,36.906114693800035,0.0,
		-125.00000000000001,36.006794104222266,0.0,
		-125.00000000000001,35.10747351464449,0.0,
		-125.00000000000001,35.0,0.0,
		-123.90653798948061,35.085592130113874,0.0,
		-122.81091097846249,35.16134907214925,0.0,
		-121.71337463033095,35.22722479719028,0.0,
		-120.61418921803805,35.28317908424677,0.0,
		-119.51361902309098,35.329177626029804,0.0,
		-118.41193171276342,35.36519211989672,0.0,
		-117.30939769874021,35.391200343379346,0.0,
		-116.20628948059749,35.407186213805,0.0,
		-115.10288097767602,35.41313983161952,0.0,
		-113.99944685302863,35.40905750712752,0.0,
		-112.89626183320445,35.39494177047309,0.0,
		-111.79360002767748,35.37080136479483,0.0,
		-110.69173425173024,35.33665122260072,0.0,
		-109.59093535656724,35.292512425518716,0.0,
		-108.49147157035662,35.23841214768841,0.0,
		-107.39360785378389,35.17438358316468,0.0,
		-106.29760527355164,35.10046585780575,0.0,
		-105.20372039707333,35.016703926214404,0.0,
		-105.00000000000001,35.0,0.0,
		-105.00000000000001,35.89932058957777,0.0,
		-105.00000000000001,36.79864117915554,0.0,
		-105.00000000000001,37.69796176873331,0.0,
		-105.00000000000001,38.59728235831109,0.0,
		-105.00000000000001,39.496602947888874,0.0,
		-105.00000000000001,40.39592353746666,0.0,
		-105.00000000000001,41.295244127044434,0.0,
		-105.00000000000001,42.19456471662221,0.0,
		-105.00000000000001,43.09388530619999,0.0,
		-105.00000000000001,43.993205895777756,0.0,
		-105.00000000000001,44.892526485355525,0.0,
		-105.00000000000001,45.0,0.0,
		-106.26441389761406,45.104300219326454,0.0,
		-107.53314494046661,45.19460008895267,0.0,
		-108.80559338537427,45.2708108644386,0.0,
		-110.08114498816013,45.33285709948135,0.0,
		-111.35917327714841,45.38067699642667,0.0,
		-112.63904194133286,45.414222696425206,0.0,
		-113.9201073119681,45.433460506037214,0.0,
		-115.20172091468531,45.43837105776023,0.0,
		-116.48323206797615,45.4289494026752,0.0,
		-117.76399050305312,45.40520503416367,0.0,
		-119.04334897970904,45.36716184242728,0.0,
		-120.3206658728697,45.31485800032494,0.0,
		-121.59530770506407,45.24834578181594,0.0,
		-122.8666516010072,45.16769131504565,0.0,
		-124.13408764187633,45.07297427281596,0.0};
	
	private static double[] regionCircularDat = new double[] {
		-125.00000000000001,38.59728235831109,0.0,
		-124.20187521891582,38.54006261520573,0.0,
		-123.43154813253027,38.37040942497109,0.0,
		-122.7154475001905,38.094238585064794,0.0,
		-122.07740014623062,37.721079794476424,0.0,
		-121.53764305100701,37.26361813849858,0.0,
		-121.11214447342081,36.73711711291146,0.0,
		-120.8122474476649,36.158772316429776,0.0,
		-120.64460556798912,35.547041982631974,0.0,
		-120.61135269460763,34.92099200062621,0.0,
		-120.71043709701615,34.29968203898452,0.0,
		-120.9360537843138,33.70160858498978,0.0,
		-121.2791210939385,33.144211965723926,0.0,
		-121.72776358927327,32.64344849972986,0.0,
		-122.26777877508107,32.21342575605921,0.0,
		-122.8830776328335,31.866097874107226,0.0,
		-123.55609762241335,31.61101823189181,0.0,
		-124.26819181059294,31.455147692998462,0.0,
		-125.00000000000001,31.402717641688902,0.0,
		-125.73180818940709,31.455147692998462,0.0,
		-126.44390237758668,31.61101823189181,0.0,
		-127.11692236716654,31.866097874107226,0.0,
		-127.73222122491894,32.21342575605921,0.0,
		-128.27223641072675,32.64344849972986,0.0,
		-128.72087890606153,33.144211965723926,0.0,
		-129.06394621568623,33.70160858498978,0.0,
		-129.28956290298387,34.29968203898452,0.0,
		-129.3886473053924,34.92099200062621,0.0,
		-129.35539443201094,35.547041982631974,0.0,
		-129.18775255233513,36.158772316429776,0.0,
		-128.88785552657922,36.73711711291146,0.0,
		-128.462356948993,37.26361813849858,0.0,
		-127.9225998537694,37.721079794476424,0.0,
		-127.28455249980952,38.094238585064794,0.0,
		-126.56845186746975,38.37040942497109,0.0,
		-125.7981247810842,38.54006261520573,0.0};
	
	private static double[] regionBufferDat = new double[] {
		-125.18861603358866,34.11419576043066,0.0,
		-125.37167953006093,34.1543468631209,0.0,
		-125.54378623670229,34.219949531171125,0.0,
		-125.69982614653524,34.30906712544795,0.0,
		-125.83512469033597,34.41906194277621,0.0,
		-125.94557647778464,34.54666729275529,0.0,
		-126.02776858293272,34.68807794624364,0.0,
		-126.07908999837065,34.83905719174881,0.0,
		-126.0978235238231,34.99505824515036,0.0,
		-126.08321608800617,35.15135722580647,0.0,
		-126.03552342334434,35.303194352334856,0.0,
		-125.95602522406752,35.44591945280394,0.0,
		-125.93394390814777,35.47209227946612,0.0,
		-125.93394390814774,35.47209227946612,0.0,
		-125.93626501147745,35.473281291368515,0.0,
		-120.0574738186964,42.44153167811818,0.0,
		-120.05747381869642,42.44153167811818,0.0,
		-120.05545155559999,42.44484635641829,0.0,
		-120.04678764913807,42.45419821154589,0.0,
		-119.99008524629348,42.521408719215664,0.0,
		-119.98636572365713,42.519417878460715,0.0,
		-119.93552582787424,42.574294664371656,0.0,
		-119.78640240869746,42.68625321319505,0.0,
		-119.61260274946349,42.77721788105355,0.0,
		-119.4194956377728,42.844327362261126,0.0,
		-119.21312406990106,42.885462430952025,0.0,
		-119.0,42.899320589577776,0.0,
		-118.78687593009894,42.885462430952025,0.0,
		-118.5805043622272,42.844327362261126,0.0,
		-118.54484436749892,42.83193463511023,0.0,
		-118.5437957077006,42.83387863625673,0.0,
		-113.18982230862002,41.044779607309266,0.0,
		-113.18982230862004,41.044779607309266,0.0,
		-105.85659285732784,45.665133409109416,0.0,
		-105.85659285732783,45.665133409109416,0.0,
		-105.8274780912261,45.685956018023866,0.0,
		-105.80866131342721,45.695333022057355,0.0,
		-105.8086613134272,45.695333022057355,0.0,
		-105.78448372828561,45.71056628295138,0.0,
		-105.78223895977906,45.708500128529096,0.0,
		-105.78223895977904,45.708500128529096,0.0,
		-105.64470542097861,45.777037503092096,0.0,
		-105.44153198094067,45.84424276912569,0.0,
		-105.22433620499467,45.88544059466057,0.0,
		-105.00000000000001,45.89932058957776,0.0,
		-104.77566379500536,45.88544059466057,0.0,
		-104.55846801905936,45.84424276912569,0.0,
		-104.3552945790214,45.777037503092096,0.0,
		-104.17252190877394,45.685956018023866,0.0,
		-104.0158058511157,45.573874156612746,0.0,
		-103.88989622740132,45.444311254401825,0.0,
		-103.79849582519203,45.30130901084315,0.0,
		-103.74416514668954,45.14929587811963,0.0,
		-103.72827305078295,44.992942664178926,0.0,
		-103.75099073605496,44.837014856347054,0.0,
		-103.8113245599498,44.68622670225956,0.0,
		-103.90718203382836,44.545101438075974,0.0,
		-104.03546491535985,44.41784132788408,0.0,
		-104.19218349640474,44.30821045325954,0.0,
		-104.23695860624183,44.286176255570524,0.0,
		-104.23695860624186,44.286176255570524,0.0,
		-104.2348061931071,44.28419510789139,0.0,
		-112.20785891228773,39.33893526115657,0.0,
		-112.21034058787744,39.34097779540197,0.0,
		-112.25289953108579,39.30866947005198,0.0,
		-112.41960264025548,39.219709485656814,0.0,
		-112.60335811496977,39.154234736432116,0.0,
		-112.79873538620447,39.11416688762416,0.0,
		-113.0,39.10067941042222,0.0,
		-113.20126461379554,39.11416688762416,0.0,
		-113.39664188503025,39.154234736432116,0.0,
		-113.50273747334609,39.19203813820628,0.0,
		-113.50273747334613,39.19203813820629,0.0,
		-113.50273747334613,39.19203813820628,0.0,
		-113.50460369881688,39.18907869284662,0.0,
		-118.55087047853937,40.8672210378919,0.0,
		-124.07458343636014,34.51961347186208,0.0,
		-124.07684001933153,34.520769432468136,0.0,
		-124.16487530966404,34.41906194277621,0.0,
		-124.30017385346477,34.30906712544795,0.0,
		-124.45621376329774,34.219949531171125,0.0,
		-124.6283204699391,34.1543468631209,0.0,
		-124.81138396641136,34.11419576043066,0.0,
		-125.00000000000001,34.10067941042223,0.0};
	
	private static double[] regionCircRectIntersectDat = new double[] {
		-125.00000000000001,35.0,0.0,
		-125.00000000000001,38.59728235831109,0.0,
		-124.20187521891582,38.54006261520573,0.0,
		-123.43154813253027,38.37040942497109,0.0,
		-122.7154475001905,38.094238585064794,0.0,
		-122.07740014623062,37.721079794476424,0.0,
		-121.53764305100701,37.26361813849858,0.0,
		-121.11214447342081,36.73711711291146,0.0,
		-120.8122474476649,36.158772316429776,0.0,
		-120.64460556798912,35.547041982631974,0.0,
		-120.61554923334226,35.0,0.0};

	private static double[] regionCircRectUnionDat = new double[] {
		-125.73180818940709,31.455147692998462,0.0,
		-126.44390237758668,31.61101823189181,0.0,
		-127.11692236716654,31.866097874107226,0.0,
		-127.73222122491894,32.21342575605921,0.0,
		-128.27223641072675,32.64344849972986,0.0,
		-128.72087890606153,33.144211965723926,0.0,
		-129.06394621568623,33.70160858498978,0.0,
		-129.28956290298387,34.29968203898452,0.0,
		-129.3886473053924,34.92099200062621,0.0,
		-129.35539443201094,35.547041982631974,0.0,
		-129.18775255233513,36.158772316429776,0.0,
		-128.88785552657922,36.73711711291146,0.0,
		-128.462356948993,37.26361813849858,0.0,
		-127.9225998537694,37.721079794476424,0.0,
		-127.28455249980952,38.094238585064794,0.0,
		-126.56845186746975,38.37040942497109,0.0,
		-125.7981247810842,38.54006261520573,0.0,
		-125.00000000000001,38.59728235831109,0.0,
		-125.00000000000001,45.0,0.0,
		-105.00000000000001,45.0,0.0,
		-105.00000000000001,35.0,0.0,
		-120.61554923334226,35.0,0.0,
		-120.61135269460763,34.92099200062621,0.0,
		-120.71043709701615,34.29968203898452,0.0,
		-120.9360537843138,33.70160858498978,0.0,
		-121.2791210939385,33.144211965723926,0.0,
		-121.72776358927327,32.64344849972986,0.0,
		-122.26777877508107,32.21342575605921,0.0,
		-122.8830776328335,31.866097874107226,0.0,
		-123.55609762241335,31.61101823189181,0.0,
		-124.26819181059294,31.455147692998462,0.0,
		-125.00000000000001,31.402717641688902,0.0};
	
	private static double[] regionSmRectLgRectIntersectDat = new double[] {
		-117.0,39.0,0.0,
		-117.0,41.000000000001,0.0,
		-112.999999999999,41.000000000001,0.0,
		-112.999999999999,39.0,0.0};
	
	private static double[] regionSmRectLgRectUnionDat = new double[] {
		-125.00000000000001,35.0,0.0,
		-125.00000000000001,45.0,0.0,
		-105.00000000000001,45.0,0.0,
		-105.00000000000001,35.0,0.0};
}
