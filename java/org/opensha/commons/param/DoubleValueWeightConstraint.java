/**
 * 
 */
package org.opensha.commons.param;

import org.opensha.commons.data.ValueWeight;
import org.opensha.commons.exceptions.EditableException;

/**
 * DoubleValueWeightConstraint : This class accepts a ValueWeight object and checks whether
 * both value and weight are within the allowed range of values.
 * 
 * @author vipingupta
 *
 */
public class DoubleValueWeightConstraint extends ParameterConstraint {
	 /** Class name for debugging. */
    protected final static String C = "DoubleValueWeightConstraint";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    /** The  value  constraint */
    protected DoubleConstraint valueConstraint = null;
    /** The  value  constraint */
    protected DoubleConstraint weightConstraint = null;
    

    /** No-Arg Constructor, constraints are null so all values allowed */
    public DoubleValueWeightConstraint() { super(); }


    /**
     * Constructor for the DoubleValueWeightConstraint object. Sets the min/max values and 
     * min/max weights allowed in this constraint. No checks are performed that min and max are
     * consistant with each other.
     *
     * @param  minVal  The min value allowed
     * @param  maxVal  The max value allowed
     * @param  minWt   The min weight allowed
     * @param  maxWt   The max weight allowed  
     */
    public DoubleValueWeightConstraint( double minVal, double maxVal, double minWt, double maxWt) {
        this(new Double(minVal), new Double(maxVal), new Double(minWt), new Double(maxWt));    
    }


    /**
     * Constructor for the DoubleValueWeightConstraint object. Sets the min/max values and min/max wts
     * allowed in this constraint. No checks are performed that min and max are
     * consistant with each other.
     *
     * @param  minVal  The min value allowed
     * @param  maxVal  The max value allowed
     * @param  minWt   The min weight allowed
     * @param  maxWt   The max weight allowed 
     */
    public DoubleValueWeightConstraint( Double minVal, Double maxVal, Double minWt, Double maxWt ) {
    	valueConstraint = new DoubleConstraint(minVal, maxVal);
    	this.weightConstraint = new DoubleConstraint(minWt, maxWt);
    }

    /**
     * Sets the min and max values and min and max weights allowed in this constraint. No checks
     * are performed that min and max are consistant with each other.
     *
     * @param  minVal  The new min value
     * @param  maxVal  The new max value
     * @param  minWt   The new min weight
     * @param  maxWt   The new max weight
     * 
     * @throws EditableException Thrown when the constraint or parameter
     * containing this constraint has been made non-editable.
     */
    public void setMinMax( double minVal, double maxVal, double minWt, double maxWt) throws EditableException {
        setMinMax(new Double(minVal), new Double(maxVal), new Double(minWt), new Double(maxWt));
    }


    /**
     * Sets the min and max values and min and max weights allowed in this constraint. No checks
     * are performed that min and max are consistant with each other.
     *
     * @param  minVal  The new min value
     * @param  maxVal  The new max value
     * @param  minWt   The new min weight
     * @param  maxWt   The new max weight
     * 
     * @throws EditableException Thrown when the constraint or parameter
     * containing this constraint has been made non-editable.
     */
    public void setMinMax( Double minVal, Double maxVal, Double minWt, Double maxWt ) throws EditableException {
        String S = C + ": setMinMax(Double, Double): ";
        checkEditable(S);
        valueConstraint = new DoubleConstraint(minVal, maxVal);
    	this.weightConstraint = new DoubleConstraint(minWt, maxWt);
    }


    /** Returns the min allowed value of this constraint. */
    public Double getMinVal() { return valueConstraint.getMin(); }

    /** Gets the max allowed value of this constraint */
    public Double getMaxVal() { return valueConstraint.getMax(); }
    
    /** Returns the min allowed weight of this constraint. */
    public Double getMinWt() { return weightConstraint.getMin(); }

    /** Gets the max allowed weight of this constraint */
    public Double getMaxWt() { return weightConstraint.getMax(); }



    /**
     * Checks if the passed in value is within the min and max value and min and max weight, inclusive of
     * the end points. First the value is chekced if it's null and null values
     * are allowed. Then it checks the passed in object is a ValueWeight object. If the
     * constraint min and max values are null, true is returned, else the value
     * is compared against the min and max values. If any of these checks fails
     * false is returned. Otherwise true is returned.
     *
     * @param  obj  The object to check if allowed.
     * @return      True if this is a ValueWeight object and one of the allowed values.
     */
    public boolean isAllowed( Object obj ) {
        if( nullAllowed && ( obj == null ) ) return true;
        else if ( !( obj instanceof ValueWeight ) ) return false;
        else return isAllowed( ( ValueWeight ) obj );

    }


    /**
     * Checks if the passed in value is within the min and max, inclusive of
     * the end points. First the value is chekced if it's null and null values
     * are allowed. Then it checks the passed in object is a ValueWeight. If the
     * constraint min and max values are null, true is returned, else the value
     * is compared against the min and max values. If any of these checks fails
     * false is returned. Otherwise true is returned.
     *
     * @param  obj  The object to check if allowed.
     * @return      True if this is a ValueWeight and one of the allowed values.
     */
    public boolean isAllowed( ValueWeight valueWt ) {
        if( nullAllowed && ( valueWt == null ) ) return true;
        return ( this.valueConstraint.isAllowed(valueWt.getValue()) &&
        		 this.weightConstraint.isAllowed(valueWt.getWeight()));
    }


    /**
     * Checks if the passed in value and weight are within the min and max, inclusive of
     * the end points. First i is checked if it's null and null values
     * are allowed. If the constraint min and max values are null, true is
     * returned, else the value is compared against the min and max values. If
     * any of these checks fails false is returned. Otherwise true is returned.
     *
     * @param  obj  The object to check if allowed.
     * @return      True if this is one of the allowed values.
     */
    public boolean isAllowed( double val, double wt ) { return isAllowed( new ValueWeight( val, wt) ); }


    /** returns the classname of the constraint, and the min & max as a debug string */
    public String toString() {
        String TAB = "    ";
        StringBuffer b = new StringBuffer();
        if( name != null ) b.append( TAB + "Name = " + name + '\n' );
        if( valueConstraint.getMin() != null ) b.append( TAB + "Min Val = " + valueConstraint.getMin().toString() + '\n' );
        if( valueConstraint.getMax() != null ) b.append( TAB + "Max Val = " + valueConstraint.getMax().toString() + '\n' );
        if( weightConstraint.getMin() != null ) b.append( TAB + "Min Weight = " + weightConstraint.getMin().toString() + '\n' );
        if( weightConstraint.getMax() != null ) b.append( TAB + "Max Weight = " + weightConstraint.getMax().toString() + '\n' );
        b.append( TAB + "Null Allowed = " + this.nullAllowed+ '\n' );
        return b.toString();
    }


    /** Creates a copy of this object instance so the original cannot be altered. */
    public Object clone() {
        DoubleValueWeightConstraint c1 = new DoubleValueWeightConstraint( valueConstraint.getMin(), 
        		valueConstraint.getMax(),  weightConstraint.getMin(), weightConstraint.getMax());
        c1.setName( name );
        c1.setNullAllowed( nullAllowed );
        c1.editable = true;
        return c1;
    }
}
