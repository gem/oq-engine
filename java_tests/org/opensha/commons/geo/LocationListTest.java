package org.opensha.commons.geo;

import static org.junit.Assert.*;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.ListIterator;

import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

public class LocationListTest {

    private static LocationList ll1, ll2, ul;
    private static Location p1, p2, p3, p4, p5, p6, p7, p8, p9;

    private double result_p3p4_p8 = 78.62078721818267;
    private double result_p4_p8 = 111.19505230826488;
    private double result_p6p7_p9 = 78.62078721818267;
    private double result_p6_p9 = 111.04265949308352;

    @BeforeClass
    public static void setUp() {
        p1 = new Location(-5, 0);
        p2 = new Location(-3, -2);
        p3 = new Location(-2, -2);
        p4 = new Location(0, 0);
        p5 = new Location(2, 2);
        p6 = new Location(3, 2);
        p7 = new Location(5, 0);

        p8 = new Location(-1, 0);
        p9 = new Location(3, 1);

        ll1 = new LocationList();
        ll1.add(p1);
        ll1.add(p2);
        ll1.add(p3);
        ll1.add(p4);
        ll1.add(p5);
        ll1.add(p6);
        ll1.add(p7);

        ll2 = new LocationList();
        ll2.add(p1);
        ll2.add(p3);
        ll2.add(p2);
        ll2.add(p4);
        ll2.add(p6);
        ll2.add(p5);
        ll2.add(p7);

        ul = ll1.unmodifiableList();
    }

    @Test
    public final void testHashCode() {
        LocationList ll_clone = ll1.clone();
        assertTrue(ll_clone.hashCode() == ll1.hashCode());
        assertTrue(ll1.hashCode() != ll2.hashCode());
    }

    @Test
    public final void testReverse() {
        LocationList ll_copy = ll1.clone();
        ll_copy.reverse();
        assertTrue(ll1.get(0).equals(ll_copy.get(6)));
        assertTrue(ll1.get(1).equals(ll_copy.get(5)));
        assertTrue(ll1.get(2).equals(ll_copy.get(4)));
        assertTrue(ll1.get(4).equals(ll_copy.get(2)));
        assertTrue(ll1.get(5).equals(ll_copy.get(1)));
        assertTrue(ll1.get(6).equals(ll_copy.get(0)));
    }

    @Test
    public final void testSplit() {
        List<LocationList> lists = ll1.split(2);
        assertTrue(lists.size() == 4);
        assertTrue(lists.get(0).get(1).equals(p2));
        assertTrue(lists.get(1).get(0).equals(p3));
        assertTrue(lists.get(2).get(1).equals(p6));
        assertTrue(lists.get(3).get(0).equals(p7));
        assertTrue(lists.get(3).size() == 1);
    }

    @Test
    public final void testMinDistToLocation() {
        assertTrue(ll1.minDistToLocation(p8) == result_p4_p8);
        assertTrue(ll1.minDistToLocation(p9) == result_p6_p9);
    }

    @Test
    public final void testMinDistToLine() {
        assertTrue(ll1.minDistToLine(p8) == result_p3p4_p8);
        assertTrue(ll1.minDistToLine(p8) == result_p6p7_p9);
    }

    @Test
    public final void testSubList() {
        LocationList subLocList = ll1.subList(2, 4);
        assertEquals(ll1.get(2), subLocList.get(0));
        // make sure copies were made
        assertTrue(ll1.get(2) != subLocList.get(0));
    }

    @Test
    public final void testClone() {
        LocationList clone = ll1.clone();
        assertTrue(clone.get(0).equals(ll1.get(0)));
        assertTrue(clone.get(2).equals(ll1.get(2)));
        assertTrue(clone.get(4).equals(ll1.get(4)));
        assertTrue(clone.get(6).equals(ll1.get(6)));
    }

    @Test
    public final void testEqualsObject() {
        LocationList eqTest = new LocationList();
        eqTest.add(p1);
        eqTest.add(p2);
        eqTest.add(p3);
        eqTest.add(p4);
        eqTest.add(p5);
        eqTest.add(p6);
        eqTest.add(p7);
        assertTrue(ll1.equals(eqTest));
        assertTrue(!ll1.equals(ll2));
    }

    @Test
    public final void testToString() {
        StringBuffer b = new StringBuffer();
        b.append("LocationList size: " + ll1.size() + "\n");
        b.append("LocationList data: ");
        for (Location loc : ll1) {
            b.append(loc + " ");
        }
        assertTrue(b.toString().equals(ll1.toString()));
    }

    // ============================================
    // Pass-through UnmodifiableLocationList methods
    // ============================================

    @Test
    public final void testUnmodPassThruOps() {
        assertEquals(ul.clone(), ll1);
        assertTrue(ul.contains(p2));
        assertTrue(ll1.contains(p2));
        ArrayList<Location> cal = new ArrayList<Location>();
        cal.add(p2);
        cal.add(p3);
        cal.add(p4);
        assertTrue(ul.containsAll(cal));
        assertTrue(ll1.containsAll(cal));
        assertTrue(ul.equals(ll1));
        assertEquals(ul.get(1), p2);
        assertEquals(ul.hashCode(), ll1.hashCode());
        assertEquals(ul.indexOf(p3), ll1.indexOf(p3));
        LocationList emptyList = new LocationList();
        assertTrue(emptyList.isEmpty());
        LocationList emptyUMlist = emptyList.unmodifiableList();
        assertTrue(emptyUMlist.isEmpty());
        assertEquals(ul.lastIndexOf(p4), ll1.lastIndexOf(p4));
        assertEquals(ul.size(), ll1.size());
        assertArrayEquals(ul.toArray(), ll1.toArray());
        assertArrayEquals(ul.toArray(new Location[ul.size()]),
                ll1.toArray(new Location[ll1.size()]));
        assertEquals(ul.toString(), ll1.toString());
        LocationList sll = new LocationList();
        sll.add(p2);
        sll.add(p3);
        sll.add(p4);
        assertEquals(sll, ul.subList(1, 4));
    }

    @Test
    public final void testUnmodPassThruOpsEditability()
            throws UnsupportedOperationException {
        // testing that clone and sublist yield editable LocationLists
        LocationList llClone = ul.clone();
        llClone.add(new Location(0, 0));
        LocationList llSubList = ul.subList(1, 3);
        llSubList.add(new Location(0, 0));
    }

    // ============================================
    // Unsupported UnmodifiableLocationList methods
    // ============================================

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodAdd1() {
        ul.add(new Location(0, 0));
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodAdd2() {
        ul.add(2, new Location(0, 0));
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodAddAll1() {
        ul.addAll(null);
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodAddAll2() {
        ul.addAll(2, null);
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodRemove1() {
        ul.remove(2);
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodRemove2() {
        ul.remove(new Location(0, 0));
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodRemoveAll() {
        ul.removeAll(null);
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodRetainAll() {
        ul.retainAll(null);
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodClear() {
        ul.clear();
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodSet() {
        ul.set(2, new Location(0, 0));
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodIterator() {
        Iterator<Location> it = ul.iterator();
        while (it.hasNext()) {
            Location loc = (Location) it.next();
            it.remove();
        }
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodListIterator1() {
        // touch no-arg constructor method
        ListIterator<Location> it = ul.listIterator();
        while (it.hasNext()) {
            // touch all the pass through methods
            Location next = it.next();
            int i = it.nextIndex();
            int j = it.previousIndex();
            Location prev = it.previous();
            Location next2 = it.next();
            boolean hasPrev = it.hasPrevious();
            boolean hasNext = it.hasNext();
            // test remove
            it.remove();
        }
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodListIterator2() {
        // touch index constructor method
        ListIterator<Location> it = ul.listIterator(2);
        while (it.hasNext()) {
            // test set
            it.set(null);
        }
    }

    @Test(expected = UnsupportedOperationException.class)
    public final void testUnmodListIterator3() {
        ListIterator<Location> it = ul.listIterator();
        while (it.hasNext()) {
            // test add
            it.add(null);
        }
    }

}
