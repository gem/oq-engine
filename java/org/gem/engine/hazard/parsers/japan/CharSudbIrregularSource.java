package org.gem.engine.hazard.parsers.japan;

import java.util.ArrayList;

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

/**
 * This is a class created on purpose to model PSHA in Japan. The concepts of
 * the class are nearly the same used to develop the FaultRuptureSurface
 * 
 * @author marcop
 * @version 0.1
 * 
 */
public class CharSudbIrregularSource extends ProbEqkSource {

    private LocationList locationList;
    private double mag;
    private double rate;
    private double rake;

    /**
     * This creates an Irregular Fault Source with a time independent
     * characteristic model. It is assumed that the char magnitude ruptures the
     * whole fault surface.
     * 
     * @param magnitude
     *            - Char magnitude
     * @param rate
     *            - Occurrence rate for the Char magnitude [ev/yr]
     * @param faultSurface
     *            - The fault surface (that coincides with the rupture surface)
     *            is represented by a LocationList
     * @param rake
     *            - Rake of the fault
     */
    public CharSudbIrregularSource(double mag, double rate,
            LocationList locationList, double rake) {
        this.mag = mag;
        this.rate = rate;
        this.locationList = locationList;
        this.rake = rake;
        this.isPoissonian = false;

        // make the rupture list
        probEqkRupture = new ProbEqkRupture();
        probEqkRupture.setAveRake(rake);
        // probEqkRupture.setRuptureSurface(ruptureSurface);
        // probEqkRupture.setMag(mag);
        // probEqkRupture.setProbability(probability);

    }

    /**
     * This computes the minimum distance from the rupture to the site
     * 
     * @param site
     *            - This is the site where
     */
    public double getMinDistance(Site site) {
        // TODO Auto-generated method stub
        return 0;
    }

    @Override
    public int getNumRuptures() {
        // TODO Auto-generated method stub
        return 0;
    }

    @Override
    public ProbEqkRupture getRupture(int nRupture) {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public LocationList getAllSourceLocs() {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public EvenlyGriddedSurfaceAPI getSourceSurface() {
        // TODO Auto-generated method stub
        return null;
    }

}
