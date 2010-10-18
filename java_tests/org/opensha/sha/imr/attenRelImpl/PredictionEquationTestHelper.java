package org.opensha.sha.imr.attenRelImpl;

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.PointSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceEpicentralParameter;

public class PredictionEquationTestHelper {

    /**
     * Creates an EqkRupture object for a point source.
     */
    public static EqkRupture getPointEqkRupture(double mag, Location hypo,
            double aveRake) {
        EvenlyGriddedSurfaceAPI rupSurf = new PointSurface(hypo);
        EqkRupture rup = new EqkRupture(mag, aveRake, rupSurf, hypo);
        return rup;
    }

    /**
     * Creates an EqkRupture object for a finite source.
     */
    public static EqkRupture getFiniteEqkRupture(double aveDip,
            double lowerSeisDepth, double upperSeisDepth,
            FaultTrace faultTrace, double gridSpacing, double mag,
            Location hypo, double aveRake) {
        StirlingGriddedSurface rupSurf =
                new StirlingGriddedSurface(faultTrace, aveDip, upperSeisDepth,
                        lowerSeisDepth, gridSpacing);
        EqkRupture rup = new EqkRupture(mag, aveRake, rupSurf, hypo);
        return rup;
    }

    /**
     * Applies "Pytagoras" to the horizontal and vertical distances between hypo
     * and location.
     * 
     * @param location
     * @param hypo
     * @return
     */
    public static double calcHypoDist(Location location, Location hypo) {
        double hypoDist =
                Math.sqrt(Math.pow(LocationUtils.horzDistance(hypo, location),
                        2)
                        + Math.pow(LocationUtils.vertDistance(hypo, location),
                                2));
        return hypoDist;
    }

}
