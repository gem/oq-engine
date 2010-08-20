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

package org.gem.engine.risk.io.reader;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.gem.engine.risk.BaseTestCase;
import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.data.HazardCurve;
import org.gem.engine.risk.io.reader.AsciiFileHazardCurveReader;
import org.gem.engine.risk.io.reader.definition.ESRIRasterFileDefinition;
import org.gem.engine.risk.io.reader.definition.reader.HazardCurveESRIRasterFileDefinitionReader;
import org.junit.Before;
import org.junit.Test;

public class AsciiFileHazardCurveReaderTest extends BaseTestCase
{

    private AsciiFileHazardCurveReader curves;

    @Before
    public void setUp()
    {
        String filename = pathFor("Hazard_curve.txt");
        ESRIRasterFileDefinition definition = new HazardCurveESRIRasterFileDefinitionReader(filename).read();
        curves = new AsciiFileHazardCurveReader(pathFor("Hazard_curve.txt"), definition);
    }

    @Test
    public void shouldLoadTheTimeSpan()
    {
        HazardCurve curve = curves.readAt(new Site(27.250, 41.500));
        assertEquals(50, curve.getTimeSpan());
    }

    @Test
    public void shouldLoadTheIntensityMeasureType()
    {
        HazardCurve curve = curves.readAt(new Site(27.250, 41.500));
        assertEquals("MMI", curve.getIMT());
    }

    @Test
    public void shouldLoadTheCurveType()
    {
        HazardCurve curve = curves.readAt(new Site(27.250, 41.500));
        assertEquals("Mean", curve.ofType());
    }

    @Test
    public void shouldLoadTheEarthquakeRuptureForecastType()
    {
        HazardCurve curve = curves.readAt(new Site(27.250, 41.500));
        assertEquals("UCERF2", curve.getERF());
    }

    @Test
    public void shouldLoadTheProbabilisticType()
    {
        HazardCurve curve = curves.readAt(new Site(27.350, 41.500));
        assertEquals("PO", curve.getProbabilisticType());
    }

    @Test
    public void shouldLoadTheListOfIMLs()
    {
        HazardCurve curve = curves.readAt(new Site(27.350, 41.500));
        assertArrayEquals(new Double[] { 6.0, 7.0, 8.0, 9.0, 10.0 }, curve.getDomain().toArray());
    }

    @Test
    public void notComputableIfProbabilitiesAreNotDefined()
    {
        HazardCurve curve = curves.readAt(new Site(27.250, 41.500));
        assertFalse(curve.isComputable());
    }

    @Test
    public void computableIfProbabilitiesAreDefined()
    {
        HazardCurve curve = curves.readAt(new Site(27.350, 41.500));
        assertTrue(curve.isComputable());
    }

    @Test
    public void shouldLoadTheProbabilitiesWhenValid1()
    {
        HazardCurve curve = curves.readAt(new Site(27.350, 41.500));
        assertEquals(0.16348, curve.getFor(6.0), 0.0);
        assertEquals(0.08889, curve.getFor(7.0), 0.0);
        assertEquals(0.06138, curve.getFor(8.0), 0.0);
        assertEquals(0.02112, curve.getFor(9.0), 0.0);
        assertEquals(0.00594, curve.getFor(10.0), 0.0);
    }

    @Test
    public void shouldLoadTheProbabilitiesWhenValid2()
    {
        HazardCurve curve = curves.readAt(new Site(27.450, 41.500));
        assertEquals(0.19982, curve.getFor(6.0), 0.0);
        assertEquals(0.10865, curve.getFor(7.0), 0.0);
        assertEquals(0.07460, curve.getFor(8.0), 0.0);
        assertEquals(0.02825, curve.getFor(9.0), 0.0);
        assertEquals(0.00726, curve.getFor(10.0), 0.0);
    }

    @Test
    public void shouldLoadTheProbabilitiesWhenValid3()
    {
        HazardCurve curve = curves.readAt(new Site(27.450, 41.800));
        assertEquals(0.18165, curve.getFor(6.0), 0.0);
        assertEquals(0.09877, curve.getFor(7.0), 0.0);
        assertEquals(0.06782, curve.getFor(8.0), 0.0);
        assertEquals(0.02568, curve.getFor(9.0), 0.0);
        assertEquals(0.00660, curve.getFor(10.0), 0.0);
    }

}
