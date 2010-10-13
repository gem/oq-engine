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

package org.opensha.commons.param;

import java.util.ArrayList;
import java.util.ListIterator;

import org.dom4j.Element;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.EditableException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.metadata.XMLSaveable;
import org.opensha.commons.param.event.ParameterChangeEvent;

/**
 * <b>Title: </b> Parameter
 * <p>
 * 
 * <b>Description: </b> Partial (abstract) base implementation for ParameterAPI
 * of common functionality accross all parameter subclasses. The common fields
 * with get and setters are here, as well as a default constructor that sets all
 * these fields, and the setValue field that always checks if the value is
 * allowefd before setting. The fields with gettesr and setters are:
 * 
 * <ul>
 * <li>name
 * <li>units
 * <li>constraint
 * <li>editable
 * <li>value
 * </ul>
 * 
 * These fields are common to all parameters.
 * <p>
 * 
 * @author Steve W. Rock
 * @created February 21, 2002
 * @see ParameterAPI
 * @version 1.0
 */
public abstract class Parameter<E> implements ParameterAPI<E>,
        java.io.Serializable {

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;
    /**
     * Class name used for debug statements and building the parameter type for
     * getType().
     */
    protected final static String C = "Parameter";
    public final static String XML_GROUP_METADATA_NAME = "Parameters";
    public final static String XML_METADATA_NAME = "Parameter";
    public final static String XML_COMPLEX_VAL_EL_NAME = "ComplexValue";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    /** Name of the parameter. */
    protected String name = "";

    /**
     * Information about this parameter. This is usually used to describe what
     * this object represents. May be used in gui tooltips.
     */
    protected String info = "";

    /** The units of this parameter represented as a String */
    protected String units = "";

    /** The constraint for this Parameter. This is consulted when setting values */
    protected ParameterConstraintAPI constraint = null;

    /**
     * This value indicates if fields and constraint in this parameter are
     * editable after it is first initialized.
     */
    protected boolean editable = true;

    /**
     * The value object of this Parameter, subclasses will define the object
     * type.
     */
    protected E value = null;

    /**
     * The default value object of this Parameter, subclasses will define the
     * object type.
     */
    protected E defaultValue = null;

    /**
     * ArrayList of all the objects who want to listen on change of this
     * paramter
     */
    private transient ArrayList changeListeners;

    /**
     * ArrayList of all the objects who want to listen if the value for this
     * paramter is not valid
     */
    private transient ArrayList failListeners;

    /** Empty no-arg constructor. Does nothing but initialize object. */
    public Parameter() {
    }

    /**
     * If the editable boolean is set to true, the parameter value can be
     * edited, else an EditableException is thrown.
     */
    protected void checkEditable(String S) throws EditableException {
        if (!this.editable)
            throw new EditableException(S
                    + "This parameter is currently not editable");
    }

    /**
     * This is the main constructor. All subclass constructors call this one.
     * Constraints must be set first, because the value may not be an allowed
     * one. Null values are always allowed in the constructor.
     * 
     * @param name
     *            Name of this parameter
     * @param constraint
     *            Constraints for this Parameter. May be set to null
     * @param units
     *            The units for this parameter
     * @param value
     *            The value object of this parameter.
     * @throws ConstraintException
     *             This is thrown if the passes in parameter is not allowed.
     */
    public Parameter(String name, ParameterConstraintAPI constraint,
            String units, E value) throws ConstraintException {

        String S = C + ": Constructor(): ";
        if (D)
            System.out.println(S + "Starting");

        if (value != null && constraint != null) {
            if (!constraint.isAllowed(value)) {
                System.out.println(S + "Value not allowed");
                throw new ConstraintException(S + "Value not allowed");
            }
        }

        this.constraint = constraint;
        this.name = name;
        this.value = value;
        this.units = units;

        // if( (constraint != null) && (constraint.getName() == null) )
        // constraint.setName( name );

        if (D)
            System.out.println(S + "Ending");

    }

    /**
     * Uses the constraint object to determine if the new value being set is
     * allowed. If no Constraints are present all values are allowed. This
     * function is now available to all subclasses, since any type of constraint
     * object follows the same api.
     * 
     * @param obj
     *            Object to check if allowed via constraints
     * @return True if the value is allowed
     */
    public boolean isAllowed(E obj) {
        // if it's null, and null isn't allowed, return false
        if (obj == null && !isNullAllowed())
            return false;
        // if there's a constraint, use that
        if (constraint != null)
            return constraint.isAllowed(obj);
        // otherwise just return true
        return true;
    }

    /**
     * Set's the parameter's value.
     * 
     * @param value
     *            The new value for this Parameter.
     * @throws ParameterException
     *             Thrown if the object is currenlty not editable.
     * @throws ConstraintException
     *             Thrown if the object value is not allowed.
     */
    public void setValue(E value) throws ConstraintException,
            ParameterException {
        String S = getName() + ": setValue(): ";

        if (!isAllowed(value)) {
            throw new ConstraintException(S + "Value is not allowed: "
                    + value.toString());
        }

        // do not fire the event if new value is same as current value
        if (this.value != null && this.value.equals(value))
            return;

        org.opensha.commons.param.event.ParameterChangeEvent event =
                new org.opensha.commons.param.event.ParameterChangeEvent(this,
                        getName(), getValue(), value);

        this.value = value;

        firePropertyChange(event);
    }

    /**
     * Set's the default value.
     * 
     * @param defaultValue
     *            The default value for this Parameter.
     * @throws ConstraintException
     *             Thrown if the object value is not allowed.
     */
    public void setDefaultValue(E defaultValue) throws ConstraintException {
        checkEditable(C + ": setDefaultValue(): ");

        if (!isAllowed(defaultValue)) {
            throw new ConstraintException(getName()
                    + ": setDefaultValue(): Value is not allowed: "
                    + defaultValue.toString());
        }

        this.defaultValue = defaultValue;
    }

    /**
     * This sets the value as the default setting
     * 
     * @param value
     */
    public void setValueAsDefault() throws ConstraintException,
            ParameterException {
        setValue(defaultValue);
    }

    /**
     * Returns the parameter's default value. Each subclass defines what type of
     * object it returns.
     */
    public E getDefaultValue() {
        return defaultValue;
    }

    /**
     * Needs to be called by subclasses when field change fails due to
     * constraint problems.
     */
    public void unableToSetValue(E value) throws ConstraintException {

        String S = C + ": unableToSetValue():";
        org.opensha.commons.param.event.ParameterChangeFailEvent event =
                new org.opensha.commons.param.event.ParameterChangeFailEvent(
                        this, getName(), getValue(), value);

        firePropertyChangeFailed(event);

    }

    /**
     * Adds a feature to the ParameterChangeFailListener attribute of the
     * ParameterEditor object
     * 
     * @param listener
     *            The feature to be added to the ParameterChangeFailListener
     *            attribute
     */
    public synchronized
            void
            addParameterChangeFailListener(
                    org.opensha.commons.param.event.ParameterChangeFailListener listener) {
        if (failListeners == null)
            failListeners = new ArrayList();
        if (!failListeners.contains(listener))
            failListeners.add(listener);
    }

    /**
     * Every parameter constraint has a name, this function gets that name.
     * Defaults to the name of the parameter but in a few cases may be
     * different.
     */
    public String getConstraintName() {
        if (constraint != null) {
            String name = constraint.getName();
            if (name == null)
                return "";
            return name;
        }
        return "";
    }

    /**
     * Description of the Method
     * 
     * @param listener
     *            Description of the Parameter
     */
    public synchronized
            void
            removeParameterChangeFailListener(
                    org.opensha.commons.param.event.ParameterChangeFailListener listener) {
        if (failListeners != null && failListeners.contains(listener))
            failListeners.remove(listener);
    }

    /**
     * Description of the Method
     * 
     * @param event
     *            Description of the Parameter
     */
    public void firePropertyChangeFailed(
            org.opensha.commons.param.event.ParameterChangeFailEvent event) {

        String S = C + ": firePropertyChange(): ";
        if (D)
            System.out.println(S
                    + "Firing failed change event for parameter = "
                    + event.getParameterName());
        if (D)
            System.out.println(S + "Old Value = " + event.getOldValue());
        if (D)
            System.out.println(S + "Bad Value = " + event.getBadValue());
        if (D)
            System.out.println(S + "Model Value = "
                    + event.getSource().toString());

        ArrayList vector;
        synchronized (this) {
            if (failListeners == null)
                return;
            vector = (ArrayList) failListeners.clone();
        }

        for (int i = 0; i < vector.size(); i++) {
            org.opensha.commons.param.event.ParameterChangeFailListener listener =
                    (org.opensha.commons.param.event.ParameterChangeFailListener) vector
                            .get(i);
            listener.parameterChangeFailed(event);
        }
    }

    /**
     * Adds a feature to the ParameterChangeListener attribute of the
     * ParameterEditor object
     * 
     * @param listener
     *            The feature to be added to the ParameterChangeListener
     *            attribute
     * 
     */

    public synchronized void addParameterChangeListener(
            org.opensha.commons.param.event.ParameterChangeListener listener) {
        if (changeListeners == null)
            changeListeners = new ArrayList();
        if (!changeListeners.contains(listener))
            changeListeners.add(listener);
    }

    /**
     * Description of the Method
     * 
     * @param listener
     *            Description of the Parameter
     */
    public synchronized void removeParameterChangeListener(
            org.opensha.commons.param.event.ParameterChangeListener listener) {
        if (changeListeners != null && changeListeners.contains(listener))
            changeListeners.remove(listener);
    }

    /**
     * 
     * Description of the Method
     * 
     * @param event
     *            Description of the Parameter
     * 
     *            Every parameter constraint has a name, this function gets that
     *            name. Defaults to the name of the parameter but in a few cases
     *            may be different.
     */
    public void firePropertyChange(ParameterChangeEvent event) {

        String S = C + ": firePropertyChange(): ";
        if (D)
            System.out.println(S + "Firing change event for parameter = "
                    + event.getParameterName());
        if (D)
            System.out.println(S + "Old Value = " + event.getOldValue());
        if (D)
            System.out.println(S + "New Value = " + event.getNewValue());
        if (D)
            System.out.println(S + "Model Value = "
                    + event.getSource().toString());

        ArrayList vector;
        synchronized (this) {
            if (changeListeners == null)
                return;
            vector = (ArrayList) changeListeners.clone();
        }

        for (int i = 0; i < vector.size(); i++) {
            org.opensha.commons.param.event.ParameterChangeListener listener =
                    (org.opensha.commons.param.event.ParameterChangeListener) vector
                            .get(i);
            listener.parameterChange(event);
        }
    }

    /**
     * Proxy function call to the constraint to see if null values are permitted
     */
    public boolean isNullAllowed() {
        if (constraint != null) {
            return constraint.isNullAllowed();
        } else
            return true;
    }

    /**
     * Sets the info string of the Parameter object if editable. This is usually
     * used to describe what this object represents. May be used in gui
     * tooltips.
     */
    public void setInfo(String info) throws EditableException {

        checkEditable(C + ": setInfo(): ");
        this.info = info;
    }

    /** Sets the units string of this parameter. Can be used in tooltips, etc. */
    public void setUnits(String units) throws EditableException {
        checkEditable(C + ": setUnits(): ");
        this.units = units;
    }

    /**
     * Returns the parameter's value. Each subclass defines what type of object
     * it returns.
     */
    public E getValue() {
        return value;
    }

    /** Returns the units of this parameter, represented as a String. */
    public String getUnits() {
        return units;
    }

    /** Gets the constraints of this parameter. */
    public ParameterConstraintAPI getConstraint() {
        return constraint;
    }

    /**
     * Sets the constraints of this parameter. Each subclass may implement any
     * type of constraint it likes. An EditableException is thrown if this
     * parameter is currently uneditable.
     * 
     * @return The constraint value
     */
    public void setConstraint(ParameterConstraintAPI constraint)
            throws EditableException {
        checkEditable(C + ": setConstraint(): ");
        // setting the new constraint for the parameter
        this.constraint = constraint;

        // getting the existing value for the Parameter
        Object value = getValue();

        /**
         * Check to see if the existing value of the parameter is within the new
         * constraint of the parameter, if so then leave the value of the
         * parameter as it is currently else if the value is outside the
         * constraint then give the parameter a temporaray null value, which can
         * be changed later by the user.
         */
        if (!constraint.isAllowed(value)) {

            /*
             * allowing the constraint to have null values.This has to be done
             * becuase if the previous value for the parameter is not within the
             * constraints then it will throw the exception:
             * "Value not allowed". so we have have allow "null" in the
             * parameters.
             */
            constraint.setNullAllowed(true);

            // now set the current param value to be null.
            /*
             * null is just a new temp value of the parameter, which can be
             * changed by setting a value in the parameter that is compatible
             * with the parameter constraints.
             */
            this.setValue(null);
            constraint.setNullAllowed(false);
        }
    }

    /** Returns a description of this Parameter, typically used for tooltips. */
    public String getInfo() {
        return info;
    }

    /**
     * Disables editing units, info, constraints, etc. Basically all set()s
     * disabled except for setValue(). Once set non-editable, it cannot be set
     * back. This is a one-time operation.
     */
    public void setNonEditable() {
        editable = false;
    }

    /** Every parameter has a name, this function returns that name. */
    public String getName() {
        return name;
    }

    /** Every parameter has a name, this function sets that name, if editable. */
    public void setName(String name) {
        checkEditable(C + ": setName(): ");
        this.name = name;
    }

    /**
     * Returns the short class name of this object. Used by the editor framework
     * to dynamically assign an editor to subclasses. If there are constraints
     * present, typically "Constrained" is prepended to the short class name.
     */
    public String getType() {
        return C;
    }

    /** Determines if the value can be edited, i.e. changed once initialized. */
    public boolean isEditable() {
        return editable;
    }

    /**
     * 
     * @returns the matadata string for parameter. This function returns the
     *          metadata which can be used to reset the values of the parameters
     *          created. *NOTE : Look at the function getMetadataXML() which
     *          return the values of these parameters in the XML format and can
     *          used recreate the parameters from scratch.
     */
    public String getMetadataString() {
        if (value != null)
            return name + " = " + value.toString();
        else
            return name + " = " + "null";
    }

    /** Returns a copy so you can't edit or damage the origial. */
    public abstract Object clone();

    public Element toXMLMetadata(Element root) {
        return toXMLMetadata(root, Parameter.XML_METADATA_NAME);
    }

    public Element toXMLMetadata(Element root, String elementName) {
        Element xml = root.addElement(elementName);
        xml.addAttribute("name", getName());
        xml.addAttribute("type", getType());
        xml.addAttribute("units", getUnits());
        Object val = getValue();
        if (val == null)
            xml.addAttribute("value", "");
        else {
            if (val instanceof XMLSaveable) {
                Element valEl = xml.addElement(XML_COMPLEX_VAL_EL_NAME);
                ((XMLSaveable) val).toXMLMetadata(valEl);
            } else {
                xml.addAttribute("value", val.toString());
            }
        }
        if (this instanceof DependentParameterAPI) {
            DependentParameterAPI<E> param = (DependentParameterAPI<E>) this;
            int num = param.getNumIndependentParameters();
            if (num > 0) {
                Element dependent =
                        xml.addElement(DependentParameterAPI.XML_INDEPENDENT_PARAMS_NAME);
                ListIterator<ParameterAPI> it =
                        (ListIterator<ParameterAPI>) param
                                .getIndependentParametersIterator();
                while (it.hasNext()) {
                    dependent = it.next().toXMLMetadata(dependent);
                }
            }
        }
        return root;
    }

    // public boolean setValueFromXMLMetadata(Element el) {
    // String value = el.attribute("value").getValue();
    //
    // if (this.setValueFromString(value)) {
    // return true;
    // } else {
    // System.err.println(this.getType() + " " + this.getName() +
    // " could not be set to " + value);
    // System.err.println("It is possible that the parameter type doesn't yet support loading from XML");
    // return false;
    // }
    // }
}
