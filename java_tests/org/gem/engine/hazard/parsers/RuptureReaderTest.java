package org.gem.engine.hazard.parsers;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

import java.io.File;

import org.gem.engine.hazard.parsers.RuptureReader.InvalidFormatException;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.util.TectonicRegionType;

// TODO Add support for schema validation on reading
public class RuptureReaderTest
{

    private static final String POINT_RUPTURE_FILE = "openquake/nrml/schema/examples/point-rupture.xml";
    private static final String SIMPLE_FAULT_RUPTURE_FILE = "openquake/nrml/schema/examples/simple-fault-rupture.xml";
    private static final String COMPLEX_FAULT_RUPTURE_FILE = "openquake/nrml/schema/examples/complex-fault-rupture.xml";

    private static final String SIMPLE_FAULT_RUPTURE_FILE_NO_DEPTH = "openquake/nrml/schema/examples/failures/simple-fault-rupture-no-depth.xml";
    private static final String COMPLEX_FAULT_RUPTURE_FILE_NO_DEPTH = "openquake/nrml/schema/examples/failures/complex-fault-rupture-no-depth.xml";

    private RuptureReader reader;

    @Before
    public void setUp()
    {
        reader = new RuptureReader(new File(POINT_RUPTURE_FILE), 0.5);
    }

    @Test(expected = IllegalArgumentException.class)
    public void throwsAnErrorWithAnInvalidFile()
    {
        new RuptureReader(new File("invalid-file.xml"), 0.5);
    }

    @Test
    public void isAbleToReadPointRuptures()
    {
        EqkRupture rupture = reader.read();
        assertNotNull(rupture);
    }

    @Test
    public void readsTheMagnitudeAndTheTectonicRegionWhenParsingThePointRupture()
    {
        EqkRupture rupture = reader.read();

        assertEquals(6.5, rupture.getMag(), 0.0);
        assertEquals(TectonicRegionType.ACTIVE_SHALLOW, rupture.getTectRegType());
    }

    @Test
    public void readsTheLocationOfTheRuptureWhenParsingThePointRupture()
    {
        EqkRupture rupture = reader.read();
        Location location = new Location(40.363, -124.704, 30.0);

        assertEquals(location, rupture.getHypocenterLocation());
    }

    @Test
    public void readsTheAverageRakeWhenParsingThePointRupture()
    {
        EqkRupture rupture = reader.read();
        assertEquals(10.0, rupture.getAveRake(), 0.0);
    }

    @Test
    public void readsTheAverageStrikeAndDipWhenParsingThePointRupture()
    {
        EqkRupture rupture = reader.read();
        assertEquals(90.0, rupture.getRuptureSurface().getAveDip(), 0.0);
        assertEquals(20.0, rupture.getRuptureSurface().getAveStrike(), 0.0);
    }

    @Test
    public void isAbleToReadSimpleFaultRuptures()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE), 0.5);
        EqkRupture rupture = reader.read();
        assertNotNull(rupture);
    }

    @Test
    public void readsTheMagnitudeAndTheTectonicRegionWhenParsingTheSimpleFaultRupture()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE), 0.5);
        EqkRupture rupture = reader.read();

        assertEquals(7.65, rupture.getMag(), 0.0);
        assertEquals(TectonicRegionType.ACTIVE_SHALLOW, rupture.getTectRegType());
    }

    @Test
    public void readsTheAverageRakeWhenParsingTheSimpleFaultRupture()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE), 0.5);
        EqkRupture rupture = reader.read();
        assertEquals(15.0, rupture.getAveRake(), 0.0);
    }

    @Test
    public void readsTheDipUpperAndLowerSeismogenicDepthWhenParsingTheSimpleFaultRupture()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE), 0.5);
        EqkRupture rupture = reader.read();

        assertEquals(50.0, rupture.getRuptureSurface().getAveDip(), 0.0);
        assertEquals(12.5, ((StirlingGriddedSurface) rupture.getRuptureSurface()).getUpperSeismogenicDepth(), 0.0);
        assertEquals(19.5, ((StirlingGriddedSurface) rupture.getRuptureSurface()).getLowerSeismogenicDepth(), 0.0);
    }

    @Test
    public void readsTheFaultTraceWhenParsingTheSimpleFaultRupture()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE), 0.5);
        EqkRupture rupture = reader.read();

        FaultTrace trace = new FaultTrace(null);
        trace.add(new Location(40.363, -124.704, 0.1));
        trace.add(new Location(41.214, -124.977, 0.1));
        trace.add(new Location(42.096, -125.140, 0.1));

        assertEquals(trace, ((StirlingGriddedSurface) rupture.getRuptureSurface()).getFaultTrace());
    }

    @Test(expected = InvalidFormatException.class)
    public void theDepthMustAlwaysBeSpecifiedWhenParsingTheSimpleFaultRupture()
    {
        reader = new RuptureReader(new File(SIMPLE_FAULT_RUPTURE_FILE_NO_DEPTH), 0.5);
        reader.read();
    }

    @Test
    public void isAbleToReadComplexFaultRuptures()
    {
        reader = new RuptureReader(new File(COMPLEX_FAULT_RUPTURE_FILE), 0.5);
        EqkRupture rupture = reader.read();
        assertNotNull(rupture);
    }

    @Test
    public void readsTheMagnitudeAndTheTectonicRegionWhenParsingTheComplexFaultRupture()
    {
        reader = new RuptureReader(new File(COMPLEX_FAULT_RUPTURE_FILE), 0.5);
        EqkRupture rupture = reader.read();

        assertEquals(9.0, rupture.getMag(), 0.0);
        assertEquals(TectonicRegionType.SUBDUCTION_INTERFACE, rupture.getTectRegType());
    }

    @Test
    public void readsTheAverageRakeWhenParsingTheComplexFaultRupture()
    {
        reader = new RuptureReader(new File(COMPLEX_FAULT_RUPTURE_FILE), 0.5);
        EqkRupture rupture = reader.read();
        assertEquals(0.0, rupture.getAveRake(), 0.0);
    }

    @Test
    public void readsTheFaultTracesWhenParsingTheComplexFaultRupture()
    {
        reader = new RuptureReader(new File(COMPLEX_FAULT_RUPTURE_FILE), 0.5);
        EqkRupture rupture = reader.read();

        FaultTrace top = new FaultTrace(null);
        top.add(new Location(40.363, -124.704, 0.5493260E+01));
        top.add(new Location(41.214, -124.977, 0.4988560E+01));
        top.add(new Location(42.096, -125.140, 0.4897340E+01));

        FaultTrace bottom = new FaultTrace(null);
        bottom.add(new Location(40.347, -123.829, 0.2038490E+02));
        bottom.add(new Location(41.218, -124.137, 0.1741390E+02));
        bottom.add(new Location(42.115, -124.252, 0.1752740E+02));

        ApproxEvenlyGriddedSurface surface = new ApproxEvenlyGriddedSurface(top, bottom, 0.5);
        LocationList locations = ((ApproxEvenlyGriddedSurface) rupture.getRuptureSurface()).getLocationList();
        assertEquals(surface.getLocationList(), locations);
    }

    @Test(expected = InvalidFormatException.class)
    public void theDepthMustAlwaysBeSpecifiedWhenParsingTheComplexFaultRupture()
    {
        reader = new RuptureReader(new File(COMPLEX_FAULT_RUPTURE_FILE_NO_DEPTH), 0.5);
        reader.read();
    }

}
