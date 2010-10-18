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
 * <b>Title:</b> DistanceEpicentralParameter
 * <p>
 * 
 * <b>Description:</b> Special subclass of PropagationEffectParameter. This is
 * the distance to the epicentre.
 * <p>
 * 
 * @author Damiano Monelli
 * @version 1.0
 */
public class DistanceEpicentralParameter extends
        WarningDoublePropagationEffectParameter implements WarningParameterAPI {
    /** Class name used in debug strings */
    protected final static String C = "DistanceEpicentralParameter";
    /** If true debug statements are printed out */
    protected final static boolean D = false;
    /** Hardcoded name */
    public final static String NAME = "DistanceEpicentral";
    /** Hardcoded units string */
    private final static String UNITS = "km";
    /** Hardcoded info string */
    private final static String INFO =
            "Epicentral Distance (distance to surface projection of rupture hypocenter [assumed in the center of the rupture])";
    /** Hardcoded min allowed value */
    private final static Double MIN = new Double(0.0);
    /** Hardcoded max allowed value */
    private final static Double MAX = new Double(Double.MAX_VALUE);

    /**
     * No-Arg constructor that just calls init() with null constraints. All
     * value are allowed.
     */
    public DistanceEpicentralParameter() {
        init();
    } // constructor

    /**
     * This constructor sets the default value.
     */
    public DistanceEpicentralParameter(double defaultValue) {
        init();
        this.setDefaultValue(defaultValue);
    } // constructor

    /**
     * Constructor that sets up constraints. This is a constrained parameter.
     */
    public DistanceEpicentralParameter(ParameterConstraintAPI warningConstraint)
            throws ConstraintException {
        if ((warningConstraint != null)
                && !(warningConstraint instanceof DoubleConstraint)) {
            throw new ConstraintException(C + " : Constructor(): "
                    + "Input constraint must be a DoubleConstraint");
        }
        init((DoubleConstraint) warningConstraint);
    } // constructor

    /**
     * Constructor that sets up constraints & the default value. This is a
     * constrained parameter.
     */
    public DistanceEpicentralParameter(
            ParameterConstraintAPI warningConstraint, double defaultValue)
            throws ConstraintException {
        if ((warningConstraint != null)
                && !(warningConstraint instanceof DoubleConstraint)) {
            throw new ConstraintException(C + " : Constructor(): "
                    + "Input constraint must be a DoubleConstraint");
        }
        init((DoubleConstraint) warningConstraint);
        setDefaultValue(defaultValue);
    } // constructor

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
    } // init()

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
            double distance = Double.NaN;
            // surface rupture
            EvenlyGriddedSurfaceAPI rupSurf = eqkRupture.getRuptureSurface();
            // get number of rows
            int numRows = rupSurf.getNumRows();
            // get number of columns
            int numColumns = rupSurf.getNumCols();
            int indexRow = 0;
            int indexColumn = 0;
            if (numRows == 1 && numColumns == 1) {
                // point source
                distance =
                        LocationUtils.horzDistance(loc1,
                                rupSurf.get(indexRow, indexColumn));
            } else if (numRows == 1 && numColumns > 1) {
                // line source
                indexColumn = numColumns / 2;
                distance =
                        LocationUtils.horzDistance(loc1,
                                rupSurf.get(indexRow, indexColumn));
            } else {
                // 3D surface
                indexRow = numRows / 2;
                indexColumn = numColumns / 2;
                distance =
                        LocationUtils.horzDistance(loc1,
                                rupSurf.get(indexRow, indexColumn));
            }
            this.setValueIgnoreWarning(new Double(distance));
        } else
            this.setValue(null);
    } // calcValueFromSiteAndEqkRup()

    /**
     * This is used to determine what widget editor to use in GUI Applets.
     */
    public String getType() {
        String type = "DoubleParameter";
        // Modify if constrained
        ParameterConstraintAPI constraint = this.constraint;
        if (constraint != null)
            type = "Constrained" + type;
        return type;
    } // getType()

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
        if (constraint != null) {
            c1 = (DoubleConstraint) constraint.clone();
        }
        if (warningConstraint != null) {
            c2 = (DoubleConstraint) warningConstraint.clone();
        }
        Double val = null;
        Double val2 = null;
        if (value != null) {
            val = (Double) this.value;
            val2 = new Double(val.doubleValue());
        }
        DistanceEpicentralParameter param = new DistanceEpicentralParameter();
        param.info = info;
        param.value = val2;
        param.constraint = c1;
        param.warningConstraint = c2;
        param.name = name;
        param.info = info;
        param.site = site;
        param.eqkRupture = eqkRupture;
        if (!this.editable) {
            param.setNonEditable();
        }
        return param;
    } // clone()

    public boolean setIndividualParamValueFromXML(Element el) {
        // TODO
        // This is copied from class "DistanceJBParameter" (...correct?)
        // Auto-generated method stub
        return false;
    } // setIndividualParamValueFromXML()

} // class DistanceEpicentralParameter
