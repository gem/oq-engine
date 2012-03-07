/*
    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify it
    under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
*/

package org.gem.ipe;

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.PointSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;

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
     * Creates an real world example EqkRupture object for a finite source. The
     * example data is from fault trace "Elsinore".
     * 
     * @return FiniteEqkRupture with a StirlingGriddedSurface
     */
    public static EqkRupture getElsinoreRupture() {
        double aveDip = 90.0;
        double lowerSeisDepth = 13.0;
        double upperSeisDepth = 0.0;
        FaultTrace trace = new FaultTrace("Elsinore;GI");
        trace.add(new Location(33.82890, -117.59000));
        trace.add(new Location(33.81290, -117.54800));
        trace.add(new Location(33.74509, -117.46332));
        trace.add(new Location(33.73183, -117.44568));
        trace.add(new Location(33.71851, -117.42415));
        trace.add(new Location(33.70453, -117.40265));
        trace.add(new Location(33.68522, -117.37270));
        trace.add(new Location(33.62646, -117.27443));
        double gridSpacing = 1.0;

        double mag = 6.889;
        double aveRake = 0.0;
        Location hypo = new Location(33.73183, -117.44568);
        Site site = new Site(new Location(33.8, -117.6, 0.0));
        return getFiniteEqkRupture(aveDip, lowerSeisDepth, upperSeisDepth,
                trace, gridSpacing, mag, hypo, aveRake);
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
