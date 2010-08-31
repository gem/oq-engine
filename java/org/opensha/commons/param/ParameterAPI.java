/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.param;

import org.dom4j.Element;
import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.metadata.XMLSaveable;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;



/**
 *  <b>Title:</b> ParameterAPI Interface<p>
 *
 *  <b>Description:</b> All parameter classes must implement this API to
 *  "plug" into the framework. A parameter basically contains some type
 *  of java object, such as a String, Double, etc. This parameter
 *  framework extends on the basic Java DataTypes by adding constraint objects,
 *  a name, information string, units string, parameter change fail and succede
 *  listeners, etc. These parameters are "Supercharged" data types with alot
 *  of functionality added. This API defines the basic added functionality and
 *  getter and setter functions for adding these extra features. <p>
 *
 *  The parameter value can be any type of object as defined by subclasses. One
 *  reason for having this framework is to enable new types of parameter
 *  in the future to be defined and added to a Site, ProbEqkRupture,
 *  or PropagationEffect object without having to rewrite the Java code. <p>
 *
 *  By defining the parameter value here as a generic object, one is not
 *  restricted to adding scalar quantities. For example, one could create a
 *  subclass of parameter where the value is a moment tensor (which could then
 *  be added to a ProbEqkRupture object). As another example, one could
 *  define a subclass of parameter where the value is a shear-wave velocity
 *  profile (which could be added to a Site object). <p>
 *
 *  Representing such non-scalar quantities as Parameters might seem confusing
 *  semantically (e.g., perhaps Attribute would be better). However, the term
 *  Parameter is consistent with the notion that an IntensityMeasureRealtionship
 *  will used this information as an independent variable when computing
 *  earthquake motion. <p>
 *
 *  <b>Revision History</b> <br>
 *  1/1/2002 SWR
 *  <ul>
 *    <LI> Removed setName(), setUnits(), setConstraints. These can only be set
 *    in Constructors now. Only the value can be changed after creation.
 *    <LI> Added compareTo() and equals(). This will test if another parameter
 *    is equal to this one based on value, not if they point to the same object
 *    in the Java Virtual Machine as the default equals() does. CompareTo() will
 *    become useful for sorting a list of parameters.
 *    <LI>
 *  </ul>
 *  <p>
 *
 * @author     Steven W. Rock
 * @created    February 21, 2002
 * @version    1.0
 */

public interface ParameterAPI<E> extends NamedObjectAPI, Comparable, XMLSaveable {

    /** Every parameter has a name, this function gets that name. */
    public String getName();

    /** Every parameter has a name, this function sets that name. */
    public void setName(String name);

    /**
     * Every parameter constraint has a name, this
     * function gets that name. Defaults to the name
     * of the parameter but in some cases may be different.
     */
    public String getConstraintName(  );

    /**
     * Returns the constraint of this parameter. Each
     * subclass may store any type of constraint it likes.
     */
    public ParameterConstraintAPI getConstraint();

    /**
     * Sets the constraints of this parameter. Each
     * subclass may store any type of constraint it likes.
     */
    public void setConstraint(ParameterConstraintAPI constraint);


    /** Returns the units of this parameter, represented as a String. */
    public String getUnits();

    /** Sets the string name of units of this parameter */
    public void setUnits(String units);

    /** Returns a description of this Parameter, typically used for tooltips. */
    public String getInfo();

    /** Sets the info attribute of the ParameterAPI object. */
    public void setInfo( String info );

    /** Returns the value stored in this parameter. */
    public E getValue();
    
    /**
     *  Set's the default value.
     *
     * @param  defaultValue          The default value for this Parameter.
     * @throws  ConstraintException  Thrown if the object value is not allowed.
     */
    public void setDefaultValue( E defaultValue );

    /**
     * This sets the value as the default setting
     * @param value
     */
    public void setValueAsDefault();
    
    /** Returns the parameter's default value. Each subclass defines what type of object it returns. */
    public E getDefaultValue();


    /**
     *  Set's the parameter's value.
     *
     * @param  value                 The new value for this Parameter
     * @throws  ParameterException   Thrown if the object type of value to set
     *      is not the correct type.
     * @throws  ConstraintException  Thrown if the object value is not allowed
     */
    public void setValue( E value ) throws ConstraintException, ParameterException;
    
    /**
     * Sets the value of this parameter from am XML element
     * @param el
     * @return
     */
    public boolean setValueFromXMLMetadata(Element el);
    
    /**
     * Method for saving this parameter to XML with the specified element name
     * instead of the default.
     * @param root
     * @param elementName
     * @return
     */
    public Element toXMLMetadata(Element root, String elementName);


     /** Needs to be called by subclasses when field change fails due to constraint problems. */
     public void unableToSetValue( E value ) throws ConstraintException;



    /**
     *  Adds a feature to the ParameterChangeFailListener attribute
     *
     * @param  listener  The feature to be added to the
     *      ParameterChangeFailListener attribute
     */
    public void addParameterChangeFailListener( org.opensha.commons.param.event.ParameterChangeFailListener listener );


    /**
     *  Description of the Method
     *
     * @param  listener  Description of the Parameter
     */
    public void removeParameterChangeFailListener( org.opensha.commons.param.event.ParameterChangeFailListener listener );

    /**
     *  Description of the Method
     *
     * @param  event  Description of the Parameter
     */
    public void firePropertyChangeFailed( org.opensha.commons.param.event.ParameterChangeFailEvent event ) ;


    /**
     *  Adds a feature to the ParameterChangeListener attribute
     *
     * @param  listener  The feature to be added to the ParameterChangeListener
     *      attribute
     */
    public void addParameterChangeListener( org.opensha.commons.param.event.ParameterChangeListener listener );
    /**
     *  Description of the Method
     *
     * @param  listener  Description of the Parameter
     */
    public void removeParameterChangeListener( org.opensha.commons.param.event.ParameterChangeListener listener );

    /**
     *  Description of the Method
     *
     * @param  event  Description of the Parameter
     */
    public void firePropertyChange( ParameterChangeEvent event ) ;


    /**
     *  Returns the data type of the value object. Used to determine which type
     *  of Editor to use in a GUI.
     */
    public String getType();


    /**
     *  Compares the values to see if they are the same. Returns -1 if obj is
     *  less than this object, 0 if they are equal in value, or +1 if the object
     *  is greater than this.
     *
     * @param  parameter            the parameter to compare this object to.
     * @return                      -1 if this value < obj value, 0 if equal, +1
     *      if this value > obj value
     * @throws  ClassCastException  Thrown if the object type of the parameter
     *      argument are not the same.
     */
    public int compareTo( Object parameter ) throws ClassCastException;


    /**
     *  Compares passed in parameter value to this one to see if equal.
     *
     * @param  parameter            the parameter to compare this object to.
     * @return                      True if the values are identical
     * @throws  ClassCastException  Thrown if the object type of the parameter
     *      argument are not the same.
     */
    public boolean equals( Object parameter ) throws ClassCastException;


    /**
     * Proxy to constraint check when setting a value. If no
     * constraint then this always returns true.
     */
    public boolean isAllowed( E value );


    /** Determines if the value can be edited, i.e. changed after initialization .*/
    public boolean isEditable();


    /**
     *  Disables editing units, info, constraints, etc. Basically all set()s disabled
     *  except for setValue(). Once set non-editable, it cannot be set back.
     *  This is a one-time operation.
     */
    public void setNonEditable();


    /** Returns a copy so you can't edit or damage the origial. */
    public Object clone();

    /**
     * Checks if null values are permitted via the constraint. If true then
     * nulls are allowed.
     */
    public boolean isNullAllowed();

    /**
     *
     * @returns the matadata string for parameter.
     * This function returns the metadata which can be used to reset the values
     * of the parameters created.
     * *NOTE : Look at the function getMetadataXML() which return the values of
     * these parameters in the XML format and can used recreate the parameters
     * from scratch.
     */
    public String getMetadataString() ;
    
    /**
     * This returns an editor for this parameter. The parameter editor shouldn't be
     * instantiated until the first call to this method in order to save memory.
     */
    public ParameterEditor getEditor();
}
