/*
 * [COPYRIGHT]
 *
 * [NAME] is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this software; if not, write to the Free
 * Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA, or see the FSF site: http://www.fsf.org.
 */

package org.gem.engine.core;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.util.Iterator;

import org.junit.Before;
import org.junit.Test;

public class RegionTest
{

    private static final Double CELL_SIZE = 0.5;

    private Site to;
    private Site from;

    @Before
    public void setUp()
    {
        to = new Site(2.0, 1.0);
        from = new Site(1.0, 2.0);
    }

    @Test
    public void shouldGiveTheNumberOfColumns1()
    {
        Region region = new Region(from, to, 0.5);
        assertEquals(3, region.getColumns());
    }

    @Test
    public void shouldGiveTheNumberOfColumns2()
    {
        Region region = new Region(from, to, 0.3);
        assertEquals(4, region.getColumns());
    }

    @Test
    public void shouldGiveTheNumberOfColumns3()
    {
        Region region = new Region(from, to, 0.6);
        assertEquals(3, region.getColumns());
    }

    @Test
    public void shouldGiveTheNumberOfColumns4()
    {
        Region region = new Region(from, to, 0.1);
        assertEquals(11, region.getColumns());
    }

    @Test
    // a single column
    public void shouldGiveTheNumberOfColumns5()
    {
        to = new Site(1.5, 2.0);
        from = new Site(1.0, 1.0);
        Region region = new Region(from, to, 1);
        assertEquals(1, region.getColumns());
    }

    @Test
    public void shouldGiveTheNumberOfColumns6()
    {
        Site to = new Site(-1.0, -2.0);
        Site from = new Site(-2.0, -1.0);
        Region region = new Region(from, to, 0.5);
        assertEquals(3, region.getColumns());
    }

    @Test
    public void shouldGiveTheNumberOfRows1()
    {
        Region region = new Region(from, to, 0.5);
        assertEquals(3, region.getRows());
    }

    @Test
    public void shouldGiveTheNumberOfRows2()
    {
        Region region = new Region(from, to, 0.3);
        assertEquals(4, region.getRows());
    }

    @Test
    public void shouldGiveTheNumberOfRows3()
    {
        Region region = new Region(from, to, 0.6);
        assertEquals(3, region.getRows());
    }

    @Test
    // a single row
    public void shouldGiveTheNumberOfRows4()
    {
        to = new Site(2.0, 1.5);
        from = new Site(1.0, 1.0);
        Region region = new Region(from, to, 1);
        assertEquals(1, region.getRows());
    }

    @Test
    public void shouldGiveTheNumberOfRows5()
    {
        Site to = new Site(-1.0, -2.0);
        Site from = new Site(-2.0, -1.0);
        Region region = new Region(from, to, 0.5);
        assertEquals(3, region.getRows());
    }

    @Test
    public void shouldGiveTheNumberOfSitesWithinTheRegion()
    {
        Region region = new Region(from, to, 0.5);
        assertEquals(9, region.numberOfCells());
    }

    @Test
    public void singleSiteRegion()
    {
        Region region = Region.singleCellRegion(new Site(1.0, 2.0));
        assertEquals(1, region.getRows());
        assertEquals(1, region.numberOfCells());
        assertEquals(1, region.getColumns());
    }

    // Iterator tests

    @Test
    public void theNumberOfSitesMustBeEqualToTheNumberOfIterations1()
    {
        Region region = new Region(from, to, 0.5);
        assertEquals(region.numberOfCells(), iterations(region));
    }

    @Test
    public void theNumberOfSitesMustBeEqualToTheNumberOfIterations2()
    {
        Site from = new Site(11.9094, 43.4602);
        Site to = new Site(12.2902, 43.2028);
        Region region = new Region(from, to, 0.0083333333333333);
        assertEquals(region.numberOfCells(), iterations(region));
    }

    @Test
    public void theNumberOfSitesMustBeEqualToTheNumberOfIterations5()
    {
        Site to = new Site(1.0, 2.0);
        Site from = new Site(1.0, 2.0);
        Region region = new Region(from, to, 1);
        assertEquals(region.numberOfCells(), iterations(region));
    }

    @Test
    public void theNumberOfSitesMustBeEqualToTheNumberOfIterations3()
    {
        Site from = new Site(11.5965, 43.4843);
        Site to = new Site(12.2898, 42.6709);
        Region region = new Region(from, to, 0.01);
        assertEquals(region.numberOfCells(), iterations(region));
    }

    @Test
    public void theNumberOfSitesMustBeEqualToTheNumberOfIterations4()
    {
        Site from = new Site(10.0054, 44.7123);
        Site to = new Site(13.2506, 42.5187);
        Region region = new Region(from, to, 0.1);
        assertEquals(region.numberOfCells(), iterations(region));
    }

    @Test
    public void hasNextWhenCurrentSiteHasNotExceededTheEndOfTheSet1()
    {
        Iterator<Site> sites = region(1, 1).iterator();
        assertTrue(sites.hasNext());
    }

    @Test
    public void hasNextWhenCurrentSiteHasNotExceededTheEndOfTheSet2()
    {
        Iterator<Site> sites = region(2, 1).iterator();
        assertTrue(sites.hasNext());
    }

    @Test
    public void noNextWhenCurrentSiteHasExceededTheEndOfTheSet1()
    {
        Iterator<Site> sites = region(2, 1).iterator();
        sites.next();
        sites.next();

        assertFalse(sites.hasNext());
    }

    @Test
    public void noNextWhenCurrentSiteHasExceededTheEndOfTheSet2()
    {
        Iterator<Site> sites = region(1, 1).iterator();
        sites.next();

        assertFalse(sites.hasNext());
    }

    // Tests with no perfect regions (start and from sites are not the center of the cell)

    @Test
    public void noNextWhenCurrentSiteHasExceededTheEndOfTheSet3()
    {
        Iterator<Site> sites = new Region(new Site(1.1, 2.2), new Site(1.7, 2.6), CELL_SIZE).iterator();

        sites.next();
        sites.next();
        sites.next();
        sites.next();

        assertFalse(sites.hasNext());
    }

    @Test
    public void noNextWhenCurrentSiteHasExceededTheEndOfTheSet4()
    {
        Iterator<Site> sites = new Region(new Site(1.1, 2.2), new Site(1.7, 2.7), CELL_SIZE).iterator();

        sites.next();
        sites.next();
        sites.next();
        sites.next();

        assertFalse(sites.hasNext());
    }

    @Test
    public void noNextWhenCurrentSiteHasExceededTheEndOfTheSet5()
    {
        Iterator<Site> sites = new Region(new Site(1.1, 2.2), new Site(1.7, 2.8), CELL_SIZE).iterator();

        sites.next();
        sites.next();
        sites.next();
        sites.next();

        assertFalse(sites.hasNext());
    }

    @Test
    public void shouldGiveTheNextSiteAtSameLatitudeIfTheEndOfRowHasNotBeenReached()
    {
        Iterator<Site> sites = region(3, 1).iterator();

        assertEquals(region(3, 1).centerOfCellAt(1, 1), sites.next());
        assertEquals(region(3, 1).centerOfCellAt(2, 1), sites.next());
        assertEquals(region(3, 1).centerOfCellAt(3, 1), sites.next());

        assertFalse(sites.hasNext());
    }

    @Test
    public void shouldGiveTheFirstSiteAtNextLatitudeIfTheEndOfRowHasBeenReached()
    {
        Iterator<Site> sites = region(2, 2).iterator();

        sites.next();
        sites.next();

        assertEquals(region(2, 2).centerOfCellAt(2, 1), sites.next());
        assertEquals(region(2, 2).centerOfCellAt(2, 2), sites.next());
    }

    @Test
    public void allSitesWithinTheRegion()
    {
        Iterator<Site> sites = region(3, 2).iterator();

        assertTrue(sites.hasNext());
        assertEquals(region(3, 2).centerOfCellAt(1, 1), sites.next());

        assertTrue(sites.hasNext());
        assertEquals(region(3, 2).centerOfCellAt(1, 2), sites.next());

        assertTrue(sites.hasNext());
        assertEquals(region(3, 2).centerOfCellAt(2, 1), sites.next());

        assertTrue(sites.hasNext());
        assertEquals(region(3, 2).centerOfCellAt(2, 2), sites.next());

        assertTrue(sites.hasNext());
        assertEquals(region(3, 2).centerOfCellAt(3, 1), sites.next());

        assertTrue(sites.hasNext());
        assertEquals(region(3, 2).centerOfCellAt(3, 2), sites.next());

        assertFalse(sites.hasNext());
    }

    // Creates a perfect region (start and from sites are at the center of the cell)
    private Region region(int rows, int columns)
    {
        Site start = new Site(1.23456, 7.89012);

        return new Region(start, start.shiftLongitude(CELL_SIZE * (columns - 1)).shiftLatitude(
                CELL_SIZE * (rows - 1) * -1), CELL_SIZE);
    }

    private int iterations(Region region)
    {
        int counter = 0;
        Iterator<Site> iterator = region.iterator();

        while (iterator.hasNext())
        {
            counter++;
            iterator.next();
        }

        return counter;
    }

}
