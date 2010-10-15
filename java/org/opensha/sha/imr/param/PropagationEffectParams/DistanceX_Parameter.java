/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.sha.imr.param.PropagationEffectParams;

import org.dom4j.Element;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.sha.earthquake.ProbEqkRupture;
// import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;
// import
// org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2.MeanUCERF2;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

/**
 * <b>Title:</b> DistanceX_Parameter
 * <p>
 * 
 * <b>Description:</b> Special subclass of PropagationEffectParameter. This
 * finds the shortest distance to the rupture trace extended to infinity. Values
 * >= 0 are on the hanging wall, and values < 0 are on the foot wall.
 * <p>
 * 
 * @author Ned Field
 * @version 1.0
 */

public class DistanceX_Parameter extends
        WarningDoublePropagationEffectParameter implements WarningParameterAPI {

    /** Class name used in debug strings */
    protected final static String C = "DistanceJBParameter";
    /** If true debug statements are printed out */
    protected final static boolean D = true;

    /** Hardcoded name */
    public final static String NAME = "DistanceX";
    /** Hardcoded units string */
    private final static String UNITS = "km";
    /** Hardcoded info string */
    private final static String INFO =
            "Horizontal distance to top edge of rupture, measured ppd to strike; neg valuse are on the foot wall";
    /** Hardcoded min allowed value */
    private final static Double MIN = new Double(-1 * Double.MAX_VALUE);
    /** Hardcoded max allowed value */
    private final static Double MAX = new Double(Double.MAX_VALUE);

    /**
     * No-Arg constructor that just calls init() with null constraints. All
     * value are allowed.
     */
    public DistanceX_Parameter() {
        init();
    }

    /** This constructor sets the default value. */
    public DistanceX_Parameter(double defaultValue) {
        init();
        this.setDefaultValue(defaultValue);
    }

    /** Constructor that sets up constraints. This is a constrained parameter. */
    public DistanceX_Parameter(ParameterConstraintAPI warningConstraint)
            throws ConstraintException {
        if ((warningConstraint != null)
                && !(warningConstraint instanceof DoubleConstraint)) {
            throw new ConstraintException(C + " : Constructor(): "
                    + "Input constraint must be a DoubleConstraint");
        }
        init((DoubleConstraint) warningConstraint);
    }

    /**
     * Constructor that sets up constraints & the default value. This is a
     * constrained parameter.
     */
    public DistanceX_Parameter(ParameterConstraintAPI warningConstraint,
            double defaultValue) throws ConstraintException {
        if ((warningConstraint != null)
                && !(warningConstraint instanceof DoubleConstraint)) {
            throw new ConstraintException(C + " : Constructor(): "
                    + "Input constraint must be a DoubleConstraint");
        }
        init((DoubleConstraint) warningConstraint);
        setDefaultValue(defaultValue);
    }

    /** Initializes the constraints, name, etc. for this parameter */
    protected void init(DoubleConstraint warningConstraint) {
        this.warningConstraint = warningConstraint;
        this.constraint = new DoubleConstraint(MIN, MAX);
        this.constraint.setNullAllowed(false);
        this.name = NAME;
        this.constraint.setName(this.name);
        this.units = UNITS;
        this.info = INFO;
        // setNonEditable();
    }

    /** Initializes the constraints, name, etc. for this parameter */
    protected void init() {
        init(null);
    }

    /**
     * Note that this does not throw a warning
     */
    protected void calcValueFromSiteAndEqkRup() {
        if ((this.site != null) && (this.eqkRupture != null)) {

            Location siteLoc = site.getLocation();

            EvenlyGriddedSurfaceAPI rupSurf = eqkRupture.getRuptureSurface();

            // set to zero if it's a point source
            if (rupSurf.getNumCols() == 1) {
                this.setValue(0.0);
            } else {

                // We should probably set something here here too if it's
                // vertical strike-slip
                // (to avoid unnecessary calculations)

                // get points projected off the ends
                Location firstTraceLoc = rupSurf.getLocation(0, 0); // first
                                                                    // trace
                                                                    // point
                Location lastTraceLoc =
                        rupSurf.getLocation(0, rupSurf.getNumCols() - 1); // last
                                                                          // trace
                                                                          // point

                // get point projected from first trace point in opposite
                // direction of the ave trace
                LocationVector dir =
                        LocationUtils.vector(lastTraceLoc, firstTraceLoc);
                dir.setHorzDistance(1000); // project to 1000 km
                Location projectedLoc1 =
                        LocationUtils.location(firstTraceLoc, dir);

                // get point projected from last trace point in ave trace
                // direction
                dir.setAzimuth(dir.getAzimuth() + 180); // flip to ave trace dir
                Location projectedLoc2 =
                        LocationUtils.location(lastTraceLoc, dir);
                // System.out.println("HERE21 "+projectedLoc1+"\t"+projectedLoc2);
                // point down dip by adding 90 degrees to the azimuth
                dir.setAzimuth(dir.getAzimuth() + 90); // now point down dip

                // get points projected in the down dip directions at the ends
                // of the new trace
                Location projectedLoc3 =
                        LocationUtils.location(projectedLoc1, dir);

                Location projectedLoc4 =
                        LocationUtils.location(projectedLoc2, dir);

                LocationList locsForExtendedTrace = new LocationList();
                LocationList locsForRegion = new LocationList();

                locsForExtendedTrace.add(projectedLoc1);
                locsForRegion.add(projectedLoc1);
                for (int c = 0; c < rupSurf.getNumCols(); c++) {
                    locsForExtendedTrace.add(rupSurf.getLocation(0, c));
                    locsForRegion.add(rupSurf.getLocation(0, c));
                }
                locsForExtendedTrace.add(projectedLoc2);
                locsForRegion.add(projectedLoc2);

                // finish the region
                locsForRegion.add(projectedLoc4);
                locsForRegion.add(projectedLoc3);

                // write these out if in debug mode
                if (D) {
                    System.out.println("Projected Trace:");
                    for (int l = 0; l < locsForExtendedTrace.size(); l++) {
                        Location loc = locsForExtendedTrace.get(l);
                        System.out.println(loc.getLatitude() + "\t"
                                + loc.getLongitude() + "\t" + loc.getDepth());
                    }
                    System.out.println("Region:");
                    for (int l = 0; l < locsForRegion.size(); l++) {
                        Location loc = locsForRegion.get(l);
                        System.out.println(loc.getLatitude() + "\t"
                                + loc.getLongitude() + "\t" + loc.getDepth());
                    }
                }

                Region polygon =
                        new Region(locsForRegion, BorderType.MERCATOR_LINEAR);
                boolean isInside = polygon.contains(siteLoc);

                double distToExtendedTrace =
                        locsForExtendedTrace.minDistToLine(siteLoc);

                if (isInside || distToExtendedTrace == 0.0) // zero values are
                                                            // always on the
                                                            // hanging wall
                    this.setValue(distToExtendedTrace);
                else
                    this.setValue(-distToExtendedTrace);
            }
        } else
            this.setValue(null);
    }

    /** This is used to determine what widget editor to use in GUI Applets. */
    public String getType() {
        String type = "DoubleParameter";
        // Modify if constrained
        ParameterConstraintAPI constraint = this.constraint;
        if (constraint != null)
            type = "Constrained" + type;
        return type;
    }

    /**
     * Returns a copy so you can't edit or damage the origial.
     * <P>
     * 
     * Note: this is not a true clone. I did not clone Site or ProbEqkRupture.
     * PE could potentially have a million points, way to expensive to clone.
     * Should not be a problem though because once the PE and Site are set, they
     * can not be modified by this class. The clone has null Site and PE
     * parameters.
     * <p>
     * 
     * This will probably have to be changed in the future once the use of a
     * clone is needed and we see the best way to implement this.
     * 
     * @return Exact copy of this object's state
     */
    public Object clone() {

        DoubleConstraint c1 = null;
        DoubleConstraint c2 = null;

        if (constraint != null)
            c1 = (DoubleConstraint) constraint.clone();
        if (warningConstraint != null)
            c2 = (DoubleConstraint) warningConstraint.clone();

        Double val = null, val2 = null;
        if (value != null) {
            val = (Double) this.value;
            val2 = new Double(val.doubleValue());
        }

        DistanceX_Parameter param = new DistanceX_Parameter();
        param.info = info;
        param.value = val2;
        param.constraint = c1;
        param.warningConstraint = c2;
        param.name = name;
        param.info = info;
        param.site = site;
        param.eqkRupture = eqkRupture;
        if (!this.editable)
            param.setNonEditable();

        return param;

    }

    public boolean setIndividualParamValueFromXML(Element el) {
        // TODO Auto-generated method stub
        return false;
    }

    // /**
    // * This performs simple tests
    // * @param args
    // */
    // public static void main(String[] args) {
    // MeanUCERF2 meanUCERF2 = new MeanUCERF2();
    // meanUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
    // meanUCERF2.updateForecast();
    // // for(int s=0; s<meanUCERF2.getNumSources();s++)
    // // System.out.println(s+"   "+meanUCERF2.getSource(s).getName());
    //
    // // sierra madre is src # 271
    // ProbEqkRupture sierraMadreRup =
    // meanUCERF2.getSource(271).getRupture(meanUCERF2.getSource(271).getNumRuptures()-1);
    //
    // Site site = new Site();
    // site.setLocation(sierraMadreRup.getRuptureSurface().getLocation(0, 0));
    //
    // DistanceX_Parameter distX = new DistanceX_Parameter();
    // distX.setValue(sierraMadreRup, site);
    //
    // }

}
