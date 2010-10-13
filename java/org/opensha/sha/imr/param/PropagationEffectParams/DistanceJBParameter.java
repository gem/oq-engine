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

import java.util.ListIterator;

import org.dom4j.Element;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

/**
 * <b>Title:</b> DistanceJBParameter
 * <p>
 * 
 * <b>Description:</b> Special subclass of PropagationEffectParameter. This
 * finds the shortest distance to the surface projection of the fault.
 * <p>
 * 
 * @see DistanceRupParameter
 * @see DistanceSeisParameter
 * @author Steven W. Rock
 * @version 1.0
 */
public class DistanceJBParameter extends
        WarningDoublePropagationEffectParameter implements WarningParameterAPI {

    /** Class name used in debug strings */
    protected final static String C = "DistanceJBParameter";
    /** If true debug statements are printed out */
    protected final static boolean D = false;

    protected boolean fix_dist_JB = false;

    /** Hardcoded name */
    public final static String NAME = "DistanceJB";
    /** Hardcoded units string */
    private final static String UNITS = "km";
    /** Hardcoded info string */
    private final static String INFO =
            "Joyner-Boore Distance (closest distance to surface projection of fault)";
    /** Hardcoded min allowed value */
    private final static Double MIN = new Double(0.0);
    /** Hardcoded max allowed value */
    private final static Double MAX = new Double(Double.MAX_VALUE);

    /**
     * No-Arg constructor that just calls init() with null constraints. All
     * value are allowed.
     */
    public DistanceJBParameter() {
        init();
    }

    /** This constructor sets the default value. */
    public DistanceJBParameter(double defaultValue) {
        init();
        this.setDefaultValue(defaultValue);
    }

    /** Constructor that sets up constraints. This is a constrained parameter. */
    public DistanceJBParameter(ParameterConstraintAPI warningConstraint)
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
    public DistanceJBParameter(ParameterConstraintAPI warningConstraint,
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

            Location loc1 = site.getLocation();
            Location loc2;
            double minDistance = 999999;
            double currentDistance;

            EvenlyGriddedSurfaceAPI rupSurf = eqkRupture.getRuptureSurface();

            // get locations to iterate over depending on dip
            ListIterator it;
            if (rupSurf.getAveDip() > 89)
                it = rupSurf.getColumnIterator(0);
            else
                it = rupSurf.getLocationsIterator();

            while (it.hasNext()) {

                loc2 = (Location) it.next();
                currentDistance = LocationUtils.horzDistance(loc1, loc2);
                if (currentDistance < minDistance)
                    minDistance = currentDistance;
            }

            // fix distanceJB if needed
            if (fix_dist_JB)
                if (rupSurf.getNumCols() > 1 && rupSurf.getNumRows() > 1) {
                    double d1, d2, min_dist;
                    loc1 = rupSurf.getLocation(0, 0);
                    loc2 = rupSurf.getLocation(1, 1);
                    d1 = LocationUtils.horzDistance(loc1, loc2);
                    loc1 = rupSurf.getLocation(0, 1);
                    loc2 = rupSurf.getLocation(1, 0);
                    d2 = LocationUtils.horzDistance(loc1, loc2);
                    min_dist = Math.min(d1, d1) / 2;
                    if (minDistance <= min_dist)
                        minDistance = 0;
                }

            this.setValueIgnoreWarning(new Double(minDistance));
        } else
            this.setValue(null);
    }

    /**
     * Setting this as true will change the calculated distanceJB value to 0.0
     * if it's less than half the distance between diagonally neighboring points
     * on the rupture surface (otherwise it's never exactly zero everywhere
     * above the entire surface). This is useful where differences between 0.0
     * and 0.5 km are important. The default value is false.
     * 
     * @param fixIt
     */
    public void fixDistanceJB(boolean fixIt) {
        fix_dist_JB = fixIt;
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

        DistanceJBParameter param = new DistanceJBParameter();
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

}
