package org.gem.engine.hazard.memcached;

import static org.junit.Assert.assertEquals;

import java.util.ArrayList;
import java.util.List;

import org.junit.Before;
import org.junit.Test;

public class HazardCurveDTOTest
{

    private HazardCurveDTO hazardCurve;

    @Before
    public void setUp()
    {
        List<Double> probilitiesOfExc = new ArrayList<Double>();
        probilitiesOfExc.add(0.1);
        probilitiesOfExc.add(0.2);
        probilitiesOfExc.add(0.3);
        probilitiesOfExc.add(0.4);

        hazardCurve = new HazardCurveDTO(null, null, null, probilitiesOfExc,
                null, null);
    }

    @Test
    public void givesTheLowestProbOfExc()
    {
        assertEquals(0.1, hazardCurve.getMinProbOfExc(), 0.0);
    }

    @Test
    public void givesTheGreatestProbOfExc()
    {
        assertEquals(0.4, hazardCurve.getMaxProbOfExc(), 0.0);
    }

}
