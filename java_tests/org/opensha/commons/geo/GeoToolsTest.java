package org.opensha.commons.geo;

import static org.junit.Assert.*;

import org.junit.BeforeClass;
import org.junit.Test;

import static org.opensha.commons.geo.GeoTools.*;

public class GeoToolsTest {

    @BeforeClass
    public static void setUpBeforeClass() throws Exception {
    }

    // @Test
    public void testValidateLats() {
        fail("Not yet implemented");
    }

    // @Test
    public void testValidateLat() {
        fail("Not yet implemented");
    }

    // @Test
    public void testValidateLons() {
        fail("Not yet implemented");
    }

    // @Test
    public void testValidateLon() {
        fail("Not yet implemented");
    }

    // @Test
    public void testValidateDepths() {
        fail("Not yet implemented");
    }

    // @Test
    public void testValidateDepth() {
        fail("Not yet implemented");
    }

    // @Test
    public void testRadiusAtLocation() {
        fail("Not yet implemented");
    }

    // @Test
    public void testDegreesLatPerKm() {
        fail("Not yet implemented");
    }

    // @Test
    public void testDegreesLonPerKm() {
        fail("Not yet implemented");
    }

    @Test
    public void testDegreesToSec() {
        assertTrue(degreesToSec(10) == 10 * SECONDS_PER_DEGREE);
    }

    @Test
    public void testSecondsToDeg() {
        assertTrue(secondsToDeg(10) == 10 / SECONDS_PER_DEGREE);
    }

}
