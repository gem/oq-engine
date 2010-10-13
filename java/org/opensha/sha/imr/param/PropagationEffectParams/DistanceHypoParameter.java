package org.opensha.sha.imr.param.PropagationEffectParams;

import org.dom4j.Element;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

/**
 * <b>Title:</b> DistanceHypoParameter
 * <p>
 * 
 * <b>Description:</b> Special subclass of PropagationEffectParameter. This
 * finds the hypocentral distance assuming hypocenter to be in the middle of the
 * rupture.
 * <p>
 * 
 * @see DistancehypoParameter
 * @author Damiano Monelli
 * @created 22 September 2010
 * @version 1.0
 */
public class DistanceHypoParameter extends
        WarningDoublePropagationEffectParameter implements WarningParameterAPI {

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;
    /** Class name used in debug strings */
    protected final static String C = "DistanceHypoParameter";
    /** If true debug statements are printed out */
    protected final static boolean D = false;

    /** Hardcoded name */
    public final static String NAME = "DistanceHypo";
    /** Hardcoded units string */
    public final static String UNITS = "km";
    /** Hardcoded info string */
    public final static String INFO =
            "Hypocentral Distance (assuming hypocenter in the middle of rupture)";
    /** Hardcoded min allowed value */
    private final static Double MIN = new Double(0.0);
    /** Hardcoded max allowed value */
    private final static Double MAX = new Double(Double.MAX_VALUE);

    /**
     * No-Arg constructor that calls init(). No constraint so all values are
     * allowed.
     */
    public DistanceHypoParameter() {
        init();
    }

    /** This constructor sets the default value. */
    public DistanceHypoParameter(double defaultValue) {
        init();
        this.setDefaultValue(defaultValue);
    }

    /** Constructor that sets up constraints. This is a constrained parameter. */
    public DistanceHypoParameter(ParameterConstraintAPI warningConstraint)
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
    public DistanceHypoParameter(ParameterConstraintAPI warningConstraint,
            double defaultValue) throws ConstraintException {
        if ((warningConstraint != null)
                && !(warningConstraint instanceof DoubleConstraint)) {
            throw new ConstraintException(C + " : Constructor(): "
                    + "Input constraint must be a DoubleConstraint");
        }
        init((DoubleConstraint) warningConstraint);
        setDefaultValue(defaultValue);
    }

    /** Sets default fields on the Constraint, such as info and units. */
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

    /**
     * Sets the warning constraint to null, then initializes the absolute
     * constraint
     */
    protected void init() {
        init(null);
    }

    /**
     * Note that this doesn not throw a warning
     */
    protected void calcValueFromSiteAndEqkRup() {
        if ((this.site != null) && (this.eqkRupture != null)) {

            double horzDist, vertDist, totalDist;

            // site location
            Location loc1 = site.getLocation();

            // extract hypocenter location as middle of the rupture
            EvenlyGriddedSurfaceAPI rupSurf = eqkRupture.getRuptureSurface();
            int numRows = rupSurf.getNumRows();
            int numCol = rupSurf.getNumCols();
            Location hypo = rupSurf.get((numRows - 1) / 2, (numCol - 1) / 2);

            // calculate hypocentral distance
            horzDist = LocationUtils.horzDistance(loc1, hypo);
            vertDist = LocationUtils.vertDistance(loc1, hypo);
            totalDist = horzDist * horzDist + vertDist * vertDist;
            this.setValue(new Double(Math.pow(totalDist, 0.5)));

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

        DistanceHypoParameter param = new DistanceHypoParameter();
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
