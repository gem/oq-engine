package org.gem.engine.hazard.parsers;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

import java.io.File;

import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.util.TectonicRegionType;

// TODO Add support for schema validation on reading
public class RuptureReaderTest
{

    public static final String POINT_RUPTURE_FILE = "docs/schema/examples/point-rupture.xml";
    public static final String SIMPLE_FAULT_RUPTURE_FILE = "docs/schema/examples/simple-fault-rupture.xml";

    private RuptureReader reader;

    @Before
    public void setUp()
    {
        reader = new RuptureReader(new File(POINT_RUPTURE_FILE));
    }

    @Test(expected = IllegalArgumentException.class)
    public void throwsAnErrorWithAnInvalidFile()
    {
        new RuptureReader(new File("invalid-file.xml"));
    }

    @Test
    public void isAbleToReadPointRuptures()
    {
        EqkRupture rupture = reader.read();
        assertNotNull(rupture);
    }

    @Test
    public void readsTheMagnitudeAndTheTectonicRegionForThePointRupture()
    {
        EqkRupture rupture = reader.read();

        assertEquals(6.5, rupture.getMag(), 0.0);
        assertEquals(TectonicRegionType.ACTIVE_SHALLOW, rupture.getTectRegType());
    }

    @Test
    public void readsTheLocationOfTheRuptureForThePointRupture()
    {
        EqkRupture rupture = reader.read();
        Location location = new Location(40.363, -124.704, 30.0);

        assertEquals(location, rupture.getHypocenterLocation());
    }

    @Test
    public void readsTheAverageRakeForThePointRupture()
    {
        EqkRupture rupture = reader.read();
        assertEquals(10.0, rupture.getAveRake(), 0.0);
    }

    @Test
    public void readsTheAverageStrikeAndDipForThePointRupture()
    {
        EqkRupture rupture = reader.read();
        assertEquals(90.0, rupture.getRuptureSurface().getAveDip(), 0.0);
        assertEquals(20.0, rupture.getRuptureSurface().getAveStrike(), 0.0);
    }

    @Test
    public void isAbleToReadSimpleFaultRuptures()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE));
        EqkRupture rupture = reader.read();
        assertNotNull(rupture);
    }

    @Test
    public void readsTheMagnitudeAndTheTectonicRegionForTheSimpleFaultRupture()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE));
        EqkRupture rupture = reader.read();

        assertEquals(7.65, rupture.getMag(), 0.0);
        assertEquals(TectonicRegionType.ACTIVE_SHALLOW, rupture.getTectRegType());
    }

    @Test
    public void readsTheAverageRakeForTheSimpleFaultRupture()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE));
        EqkRupture rupture = reader.read();
        assertEquals(15.0, rupture.getAveRake(), 0.0);
    }

    @Test
    public void readsTheDipUpperAndLowerSeismogenicDepthForTheSimpleFaultRupture()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE));
        EqkRupture rupture = reader.read();

        assertEquals(50.0, rupture.getRuptureSurface().getAveDip(), 0.0);
        assertEquals(12.5, ((StirlingGriddedSurface) rupture.getRuptureSurface()).getUpperSeismogenicDepth(), 0.0);
        assertEquals(19.5, ((StirlingGriddedSurface) rupture.getRuptureSurface()).getLowerSeismogenicDepth(), 0.0);
    }

    @Test
    public void readsTheFaultTraceForTheSimpleFaultRupture()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE));
        EqkRupture rupture = reader.read();

        FaultTrace trace = new FaultTrace(null);
        trace.add(new Location(40.363, -124.704));
        trace.add(new Location(41.214, -124.977));
        trace.add(new Location(42.096, -125.140));

        assertEquals(trace, ((StirlingGriddedSurface) rupture.getRuptureSurface()).getFaultTrace());
    }

}
