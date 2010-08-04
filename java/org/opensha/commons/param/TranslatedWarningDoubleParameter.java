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

import java.util.ListIterator;

import org.dom4j.Element;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.exceptions.TranslateException;
import org.opensha.commons.exceptions.WarningException;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.TranslatedWarningDoubleParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.param.translate.LogTranslator;
import org.opensha.commons.param.translate.TranslatorAPI;

/**
 * <b>Title:</b> TranslatedWarningDoubleParameter<p>
 *
 * <b>Description:</b> A subclass of a warning double parameter so
 * it inherits all behavior of the parent class. See the parent class
 * javadocs for a full description of it's behavior. Only the added
 * features of this subclass will be outlined here. <p>
 *
 * The whole purpose of a TranslatedWarningDoubleParameter is to be a
 * "wrapper" for a WarningDoubleParameter and translate all setting,
 * getting values to the warning parameter. This Translated parameter
 * becomes a proxy to the "wrapped" WarningParameter. In object-oriented
 * design patterns this is called the "Decorator Pattern". Instead of
 * subclassing you "wrap" (maintain a variable reference ) to the clss of
 * interest. This class then slightly modifies the behavior of the "wrapped"
 * class transparently. This helps eliminate proliferation of subclasses. <p>
 *
 * The TranslatedWarningDoubleParameter makes use of a second class, a
 * TranslatorAPI that actually performs the translation back and fourth
 * internally. An API was defined so that any type of implementation
 * translation class could be passed in. This translation class is simply
 * some function. The class acts as a pointer to a function, so you can swap
 * out different functions without changing this class. Currently the only
 * concrete translator class implemented is the LogTranslator.  <p>
 *
 * The logical purpose of this class is to input values in one form,
 * then translate them to the desired form, and use the translated values
 * in a calculation. So with this in mind it is really the input values that
 * are translated, and the translator puts them back in the correct form.<p>
 *
 * An example is that in our IMRTesterApplet we let users edit the IMR level
 * in normal space using this Parameter class. The values are internally
 * translated to log space in the contained WarningDoubleParameter. So the user
 * only sees normal values for the current IMR level, and it's constraints, but
 * internally the values are really in log space. The IMR needs the parameter
 * in log space to perform it's calculations.  It is much easier for a user
 * to input normal values say 1-200, than the log of this range. <p>
 *
 * If the translate flag is set to false, this class then acts as a transparent
 * proxy to the underlying WarningDoubleParameter. No translations are made. <p>
 *
 * @see WarningDoubleParameter
 * @see TranslatorAPI
 * @see LogTranslator
 * @author Steven W. Rock
 * @version 1.0
 */

public class TranslatedWarningDoubleParameter
    implements WarningParameterAPI<Double>, DependentParameterAPI<Double>
{


    /** Class name for debugging. */
    protected final static String C = "TranslatedWarningDoubleParameter";
    /** If true print out debug statements. */
    protected final static boolean D = false;


    /**
     * Default translator is LogTranslator. The translator class is basically
     * a pointer to a function with translate and reverse operations.
     */
    protected TranslatorAPI trans = new LogTranslator();

    /**
     * If true, translation will occur on get, and setValue operations. If false
     * this class acts as a passthrough to the underlying WarningDoubleParameter,
     * in other words this subclass becomes transparent and has no affect.
     */
    protected boolean translate = true;

    /** Returns true if translation is in affect, false otherwise */
    public boolean isTranslate() { return translate; }

    /**
     * Public api that allows enabling or disabling translation. If disabled,
     * this class acts as if it was transparent, i.e. it does noting, just provides
     * passthrough to the underlying WarningDoubleParameter functions.
     */
    public void setTranslate(boolean translate) { this.translate = translate; }

    /** Internal reference to the wrapped parameter */
    protected WarningDoubleParameter param = null;
    
    private transient ParameterEditor paramEdit = null;

    /**
     * Allows setting the parameter upon construction. The translator defaults to
     * the LogTranslator. This form allows passing in normal values that get
     * translated to log values and set in the underlying parameter.<p>
     *
     * Note: No translation changes are applied to the passed in parameter. It is
     * assumed that the parameter is already in translated log space.
     */
    public TranslatedWarningDoubleParameter( WarningDoubleParameter param ) { this.param = param; }

    /**
     * Allows setting the translator upon construction. Overides the default LogTranslator.
     * This provides the ability to set the translator to anything you want. Such
     * examples include SinTranslator and AbsTranslator, which takes the sin() and
     * absolute value respectivly. <p>
     *
     * Note that ths SinTranslator is an example of a one-to-one mapping. Reverse can
     * restore any data. AbsTranslator is unrecoverable, it cannot restore negative
     * values, only positive ones.
     *
     */
    public TranslatedWarningDoubleParameter( TranslatorAPI trans ) { this(null, trans); }

    /**
     * Allows setting the parameter for translation access, and setting
     * the translator function upon construction.<p>
     *
     * Note: No translation changes are applied to the passed in parameter. It is
     * assumed that the parameter is already in translated space.
     */
    public TranslatedWarningDoubleParameter( WarningDoubleParameter param, TranslatorAPI trans ) {
        this.trans = trans;
        this.param = param;
    }

    /**
     * Public access to the wrapped parameter, allows setting the parameter.<p>
     *
     * Note: No translation changes are applied to the passed in parameter. It is
     * assumed that the parameter is already in translated space.
     */
    public void setParameter(WarningDoubleParameter param){ this.param = param; }

    /**
     * Public access to the wrapped parameter, allows getting the parameter.
     * This is useful for normal access to the parameter in translated space.<p>
     *
     * Note: No translation changes are applied to the fetched parameter. It is
     * assumed that the parameter is returned in translated space.
     */
    public WarningDoubleParameter getParameter(){ return param; }



    /**
     *  Gets the min value of the constraint object. Does a reverse translation
     *  on the underlying Parameter data if the translate flag is set.
     *
     * @return                The reverse translated min value.
     * @exception  Exception  Thrown if any mathmatical exceptions occur.
     */
    public Double getWarningMin() throws TranslateException, Exception {
        Double min = (Double)param.getWarningMin();
        if( min  == null || !translate ) return min;
        else return new Double( trans.reverse( min.doubleValue() ) );
    }


    /**
     *  Translated proxy values to constraint check when setting a value.
     *
     * @param  value  Description of the Parameter
     * @return        The allowed value
     */
    public boolean isAllowed( Double value ){

        if( value == null || ( value instanceof Double) || !translate  ){
            return param.isAllowed( value );
        }
        else{
            double d = ((Double)value).doubleValue();
            return param.isAllowed( trans.translate( d ) );
        }

    }

    /**
     *  Gets the max value of the constraint object. Does a reverse translation
     *  on the underlying Parameter data if the translate flag is set.
     *
     * @return                The reverse translated max value.
     * @exception  Exception  Thrown if any mathmatical exceptions occur.
     */
    public Double getWarningMax() throws TranslateException {
        Double max = (Double)param.getWarningMax();
        if( max  == null || !translate ) return max;
        else return new Double( trans.reverse( max.doubleValue() ) );
    }


    /**
     *  Set's the parameter's value in the underlying parameter. Translation is
     *  performed on the value if the translate flag is set before passing to the
     *  WarningDoubleParameter. Note, if this object is not a Double, it is passed
     *  through without translation. WarningDoubleParameter constraint will fail.
     *
     * @param  value                 The new value for this Parameter
     * @throws  ParameterException   Thrown if the object is currenlty not
     *      editable
     * @throws  ConstraintException  Thrown if the object value is not allowed
     */
    public synchronized void setValue( Double value ) throws ConstraintException, WarningException {
        String S = getName() + ": setValue(): ";
        if(D) System.out.println(S + "Starting: ");

        if ( value == null  || !translate ||  !( value instanceof Double ) )
            param.setValue( value );
        else{

            Double dUntranslated = (Double)value;
            Double dTranslated = new Double( trans.translate( dUntranslated.doubleValue() ) );

            if( !param.isAllowed( dTranslated ) ) {
                String err = S + "Value is not allowed: ";
                if( value != null ) err += dUntranslated.toString();
                if(D) System.out.println(err);
                throw new ConstraintException( err );
            }
            else if ( !param.isRecommended( dTranslated ) ) {

                if(D) System.out.println(S + "Firing Warning Event");

                ParameterChangeWarningEvent event = new
                      ParameterChangeWarningEvent( (Object)this, this, this.getValue(), dUntranslated );

                fireParameterChangeWarning( event );
                throw new WarningException( S + "Value is not recommended: " + dUntranslated.toString() );
            }
            else {
                if(D) System.out.println(S + "Setting allowed and recommended value: ");
                param.setValue( dTranslated );
                org.opensha.commons.param.event.ParameterChangeEvent event = new org.opensha.commons.param.event.ParameterChangeEvent(
                       this, getName(),
                       getValue(), value
                   );

                firePropertyChange( event );
            }
        }
    }


    /**
      *  Needs to be called by subclasses when field change fails
      *  due to constraint problems
      *
      * @param  value                    Description of the Parameter
      * @exception  ConstraintException  Description of the Exception
      */
     public void unableToSetValue( Double value ) throws ConstraintException {
       param.unableToSetValue(value);
     }




    /**
     *  Returns the parameter's value. Each subclass defines what type of
     *  object. it returns
     *
     * @return    The value value
     */
    public Double getValue() {

        Double value = param.getValue();
        if ( value == null || !translate || !(value instanceof Double) ) return value;
        else{
            double d = ((Double)value).doubleValue();
            d = trans.reverse( d );
            return new Double( d ) ;
        }
    }
    
    /**
     *  Set's the default value.
     *
     * @param  defaultValue          The default value for this Parameter.
     * @throws  ConstraintException  Thrown if the object value is not allowed.
     */
    public void setDefaultValue( Double defaultValue ) throws ConstraintException {
    	/*
    	checkEditable(C + ": setDefaultValue(): ");
        if ( !isAllowed( defaultValue ) ) {
            throw new ConstraintException( getName() + ": setDefaultValue(): Value is not allowed: " + value.toString() );
        }
        this.defaultValue = defaultValue;
        */
        throw new RuntimeException("not yet implemented");
    }
    

    /**
     * This sets the value as the default setting
     * @param value
     */
    public void setValueAsDefault() throws ConstraintException, ParameterException {
    	throw new RuntimeException("not yet implemented");
    	//setValue(value);
    }
    
    
    /** Returns the parameter's default value. Each subclass defines what type of object it returns. */
    public Double getDefaultValue()  { 
    	throw new RuntimeException("not yet implemented");
    	// return defaultValue;
    }

    
   


    /**
     *  Set's the parameter's value in the underlying parameter. Translation is
     *  performed on the value if the translate flag is set before passing to the
     *  WarningDoubleParameter. The warning constraints are ignored. <p>
     *
     *  Note, if this object is not a Double, it is passed
     *  through without translation. WarningDoubleParameter constraint will fail.
     *
     * @param  value                 The new value for this Parameter
     * @throws  ParameterException   Thrown if the object is currenlty not
     *      editable
     * @throws  ConstraintException  Thrown if the object value is not allowed
     */
    public void setValueIgnoreWarning( Double value ) throws ConstraintException, ParameterException {
        String S = C + ": setValueIgnoreWarning(): ";
        if(D) System.out.println(S + "Setting value ignoring warning and constraint: ");

        if ( value == null || !translate || !( value instanceof Double ) )
            param.setValueIgnoreWarning( value );
        else{
            double d = trans.translate( ((Double)value).doubleValue() );
            param.setValueIgnoreWarning( new Double( d ) );
        }
    }


    /**
     *  Uses the constraint object to determine if the new value being set is
     *  within recommended range. If no Constraints are present all values are recommended.
     *  Translation is performed on the value if the translate flag is
     *  set before passing to the WarningDoubleParameter function.
     *
     * @param  obj  Object to check if allowed via constraints
     * @return      True if the value is allowed
     */
    public boolean isRecommended( Double obj ) {

        if ( obj == null || !translate || !( obj instanceof Double ) ) return param.isRecommended( obj );
        else{
            double d = trans.translate( ((Double)obj).doubleValue() );
            return param.isRecommended( new Double( d ) );
        }

    }


    /**
     *  Gets the min value of the constraint object. Does a reverse translation
     *  on the underlying Parameter data if the translate flag is set.
     *
     * @return                The min value
     * @exception  Exception  Description of the Exception
     */
    public Double getMin() throws Exception {

        Double min = param.getMin();
        if( min  == null || !translate ) return min;
        else return new Double( trans.reverse( min.doubleValue() ) );

    }


    /**
     *  Returns the maximum allowed value of the constraint object.
     *  Does a reverse translation on the underlying Parameter
     *  data if the translate flag is set.
     *
     * @return    The max value
     */
    public Double getMax() {

        Double max = param.getMax();
        if( max  == null || !translate ) return max;
        else return new Double(  trans.reverse( max.doubleValue() ) );

    }


    // *******************************************
    // *******************************************
    // These function are not translated
    // *******************************************
    // *******************************************

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void setIgnoreWarning(boolean ignoreWarning) {
        param.setIgnoreWarning(ignoreWarning);
    }
    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public boolean isIgnoreWarning() { return param.isIgnoreWarning(); }



    // *******************************************
    // WarningDoubleParameterAPI Proxy methods
    // *******************************************

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void setWarningConstraint(ParameterConstraint warningConstraint){
        param.setWarningConstraint(warningConstraint); }

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public ParameterConstraint getWarningConstraint() throws ParameterException{
        return param.getWarningConstraint();}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void addParameterChangeWarningListener( ParameterChangeWarningListener listener ){
        param.addParameterChangeWarningListener( listener ) ;}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void removeParameterChangeWarningListener( ParameterChangeWarningListener listener ){
        param.removeParameterChangeWarningListener( listener ) ;
    }



    /**
     *  Adds a feature to the ParameterChangeFailListener attribute of the
     *  ParameterEditor object
     *
     * @param  listener  The feature to be added to the
     *      ParameterChangeFailListener attribute
     */
    public synchronized void addParameterChangeFailListener( org.opensha.commons.param.event.ParameterChangeFailListener listener ) {
      param.addParameterChangeFailListener(listener);
    }

    /**
     *  Description of the Method
     *
     * @param  listener  Description of the Parameter
     */
    public synchronized void removeParameterChangeFailListener( org.opensha.commons.param.event.ParameterChangeFailListener listener ) {
        param.removeParameterChangeFailListener(listener);
    }


    /**
     *  Adds a feature to the ParameterChangeListener attribute of the
     *  ParameterEditor object
     *
     * @param  listener  The feature to be added to the ParameterChangeListener
     *      attribute
     */
    public synchronized void addParameterChangeListener( org.opensha.commons.param.event.ParameterChangeListener listener ) {
      param.addParameterChangeListener(listener);
    }



  /**
    *  Description of the Method
    *
    * @param  listener  Description of the Parameter
    */
   public synchronized void removeParameterChangeListener( org.opensha.commons.param.event.ParameterChangeListener listener ) {
     param.removeParameterChangeListener(listener);
   }


    /**
     *  Description of the Method
     *
     * @param  event  Description of the Parameter
     */
    public void firePropertyChange( ParameterChangeEvent event ) {
        param.firePropertyChange(event);
    }

    /**
    *  Description of the Method
    *
    * @param  event  Description of the Parameter
    */
   public void firePropertyChangeFailed( org.opensha.commons.param.event.ParameterChangeFailEvent event ) {
     param.firePropertyChangeFailed(event);
   }



    /**
     *  Description of the Method
     *
     * @param  event  Description of the Parameter
     */
    public void fireParameterChangeWarning( ParameterChangeWarningEvent event ){
        param.fireParameterChangeWarning( event ) ;
    }


    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public boolean equals( Object obj ) throws ClassCastException { return param.equals( obj ) ;}

    /** Returns a copy so you can't edit or damage the origial. */
    public Object clone(){

        TranslatedWarningDoubleParameter param1 = new TranslatedWarningDoubleParameter( (WarningDoubleParameter)param.clone() );
        param1.setTranslate( this.translate );
        return param1;

    }




    // *******************************************
    // DependentParameterAP Proxy methods
    // *******************************************

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public ListIterator getIndependentParametersIterator(){
        return param.getIndependentParametersIterator();}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public ParameterAPI getIndependentParameter(String name)throws ParameterException{
        return param.getIndependentParameter(name);}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void setIndependentParameters(ParameterList list){
        param.setIndependentParameters(list);}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void addIndependentParameter(ParameterAPI parameter) throws ParameterException{
        param.addIndependentParameter(parameter) ;}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public boolean containsIndependentParameter(String name){
        return param.containsIndependentParameter(name) ;}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void removeIndependentParameter(String name) throws ParameterException{
        param.removeIndependentParameter(name) ;}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public String getIndependentParametersKey(){
        return param.getIndependentParametersKey() ;}
    
    /** Direct proxy to wrapped parameter. See that class for documentation. */
	  public int getNumIndependentParameters() {
		  return param.getNumIndependentParameters();
	  }






    // *******************************************
    // ParameterAP Proxy methods
    // *******************************************



    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public String getName(){ return param.getName();}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void setName(String name){ param.setName(name);}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public String getConstraintName(  ){ return param.getConstraintName();}

    /**
     *  Gets the constraints of this parameter. Each subclass may implement any
     *  type of constraint it likes. This version returns a clone with reverse
     *  translated min and max values.
     *
     * @return    The constraint value
     */
    public ParameterConstraintAPI getConstraint(){

        if( param.getConstraint() == null || !translate ) return param.getConstraint();
        DoubleConstraint constraint = (DoubleConstraint)param.getConstraint();

        double transMin = trans.reverse( constraint.getMin().doubleValue() );
        double transMax = trans.reverse( constraint.getMax().doubleValue() );
        DoubleConstraint constraint2 =  new DoubleConstraint(transMin, transMax);
        return constraint2;

    }

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void setConstraint(ParameterConstraintAPI constraint){ param.setConstraint(constraint); }


    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public String getUnits(){ return param.getUnits();}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void setUnits(String units){ param.setUnits(units);}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public String getInfo(){ return param.getInfo();}

    /** Direct proxy to wrapped parameter. See that class for documentation. */
    public void setInfo( String info ){ param.setInfo( info );}


    /**
     *  Returns the data type of the value object. Used to determine which type
     *  of Editor to use in a GUI.
     *
     * @return    The type value - i.e. the class name.
     */
    public String getType(){ return "TranslatedWarningDoubleParameter";}


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
    public int compareTo( Object parameter ) throws ClassCastException{ return param.compareTo( parameter );}

    /**
     *  Determines if the value can be edited, i.e. changed once set.
     *
     * @return    The editable value
     */
    public boolean isEditable(){ return param.isEditable();}


    /**
     *  Disables editing the value once it is set.
     */
    public void setNonEditable(){ param.setNonEditable();}

    /**
     *
     * @returns the matadata string for parameter.
     * This function returns the metadata which can be used to reset the values
     * of the parameters created.
     * *NOTE : Look at the function getMetadataXML() which return the values of
     * these parameters in the XML format and can used recreate the parameters
     * from scratch.
     */
    public String getMetadataString() {
      return getName()+" = "+getValue().toString();
    }


    /**
     * Rather than giving the name and value info, this returns the name and the name/value
     * pairs for all the parameters in the IndependentParameterList of this parameter.
     * This can be used for any parameters where the value does not have a sensible
     * ascii representation (e.g., a ParameterListParameter).
     * @return
     */
    public String getDependentParamMetadataString() {
      StringBuffer metadata = new StringBuffer();
      metadata.append(getName()+" [ ");
      ListIterator list = getIndependentParametersIterator();
      while(list.hasNext()){
        ParameterAPI tempParam = (ParameterAPI)list.next();
        metadata.append(tempParam.getMetadataString()+" ; ");
       /* Note that the getmetadatSring is called here rather than the
          getDependentParamMetadataString() method becuase the former is
          so far overriden in all Parameter types that have independent
          parameters; we may want to change this later on. */
      }
      metadata.replace(metadata.length()-2,metadata.length()," ]");
      return metadata.toString();
    }


    public boolean isNullAllowed(){ return param.isNullAllowed();}
    public TranslatorAPI getTrans() {
        return trans;
    }

	public Element toXMLMetadata(Element root) {
		return toXMLMetadata(root, ParameterAPI.XML_METADATA_NAME);
	}
	
	public Element toXMLMetadata(Element root, String elementName) {
		// TODO Auto-generated method stub
		return null;
	}

	public boolean setValueFromXMLMetadata(Element el) {
		// TODO Auto-generated method stub
		return false;
	}

	public ParameterEditor getEditor() {
		if (paramEdit == null)
			try {
				paramEdit = new TranslatedWarningDoubleParameterEditor(this);
			} catch (Exception e) {
				throw new RuntimeException(e);
			}
		return paramEdit;
	}

	
}
