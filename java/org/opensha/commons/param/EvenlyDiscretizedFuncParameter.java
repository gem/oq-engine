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
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.exceptions.EditableException;
import org.opensha.commons.param.editor.EvenlyDiscretizedFuncParameterEditor;
import org.opensha.commons.param.editor.ParameterEditor;

/**
 * <p>Title: EvenlyDiscretizedFuncParameter.java </p>
 * <p>Description: This parameter accepts a EvenlyDiscretizedFunc as a value.
 * It shows the GUI so that user can enter min/max/num values and then the correspoding
 * Y values for the EvelyDiscretizedFunc
 *
 *  This class  has 2 methods for setting the units :
 * 1. setUnits() : This method sets the units for Y values
 * 2. setXUnits(): This method sets the units for X values.
 * Similarly, we have 2 different methods for getting the units.
</p>
 * @author : Nitin Gupta and Vipin Gupta
 * @created : April 01,2004
 * @version 1.0
 */

public class EvenlyDiscretizedFuncParameter extends DependentParameter<EvenlyDiscretizedFunc>
implements java.io.Serializable{


	/** Class name for debugging. */
	protected final static String C = "EvenlyDiscretizedFuncParameter";
	/** If true print out debug statements. */
	protected final static boolean D = false;

	protected final static String PARAM_TYPE ="EvenlyDiscretizedFuncParameter";
	private String xUnits="";

	private DoubleParameter minParam;
	public final static String MIN_PARAM_NAME = "Min ";

	private DoubleParameter maxParam;
	public final static String MAX_PARAM_NAME = "Max ";

	private IntegerParameter numParam;
	public final static String NUM_PARAM_NAME = "Number of Points";

	private ParameterList paramList;
	
	private transient ParameterEditor paramEdit = null;


	/**
	 * No constraints specified, all values allowed. Sets the name and value.
	 *
	 * @param  name   Name of the parameter
	 * @param  discretizedFunc  DiscretizedFunc  object
	 */
	public EvenlyDiscretizedFuncParameter(String name, EvenlyDiscretizedFunc discretizedFunc){
		super(name,null,null,discretizedFunc);
		initParamListAndEditor();
	}


	/**
	 * Creates the min, max and num param for the EvenlyDiscrized Params
	 */
	private void initParamListAndEditor() {

		// Starting
		String S = C + ": initControlsParamListAndEditor(): ";
		EvenlyDiscretizedFunc func = (EvenlyDiscretizedFunc)getValue();
		double min = func.getMinX();
		double max = func.getMaxX();
		int num = func.getNum();
		if (D)
			System.out.println(S + "Starting:");
		minParam = new DoubleParameter(MIN_PARAM_NAME,new Double(min));
		maxParam = new DoubleParameter(MAX_PARAM_NAME,new Double(max));
		numParam = new IntegerParameter(NUM_PARAM_NAME,new Integer(num));

		// put all the parameters in the parameter list
		paramList = new ParameterList();
		paramList.addParameter(this.minParam);
		paramList.addParameter(this.maxParam);
		paramList.addParameter(this.numParam);
		setIndependentParameters(paramList);
	}

	/**
	 * gets the ParameterList for the EvenlyDiscretized parameter
	 * @return ParameterList
	 */
	public ParameterList getEvenlyDiscretizedParams(){
		return paramList;
	}


	/**
	 * Sets the units for X Values. To set the units for Y values, use
	 * the setUnits() method
	 *
	 **/
	public void setXUnits(String units) throws EditableException {
		checkEditable(C + ": setUnits(): ");
		this.xUnits = units;
	}


	/**
	 * Returns the units of X values for  this parameter. To get the units for
	 * Y values, use getUnits() method
	 * represented as a String.
	 * */
	public String getXUnits() {
		return xUnits;
	}


	/**
	 *  Compares the values to if this is less than, equal to, or greater than
	 *  the comparing objects.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         -1 if this value < obj value, 0 if equal,
	 *      +1 if this value > obj value
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a ParameterListParameter.
	 */
	public int compareTo( Object obj ) {
		String S = C + ":compareTo(): ";

		if ( !( obj instanceof EvenlyDiscretizedFunc ) ) {
			throw new ClassCastException( S + "Object not a DiscretizedFuncAPI, unable to compare" );
		}

		EvenlyDiscretizedFuncParameter param = ( EvenlyDiscretizedFuncParameter ) obj;

		if( ( this.value == null ) && ( param.value == null ) ) return 0;
		int result = 0;

		EvenlyDiscretizedFunc n1 = ( EvenlyDiscretizedFunc) this.getValue();
		EvenlyDiscretizedFunc n2 = ( EvenlyDiscretizedFunc ) param.getValue();

		if(n1.equals(n2)) return 0;
		else return -1;
	}

	/**
	 * Compares value to see if equal.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         True if the values are identical
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a LocationListParameter.
	 */
	public boolean equals(Object obj) {
		String S = C + ":equals(): ";

		if (! (obj instanceof EvenlyDiscretizedFunc)) {
			throw new ClassCastException(S +
					"Object not a DiscretizedFuncAPI, unable to compare");
		}
		return ((EvenlyDiscretizedFunc)value).equals(((EvenlyDiscretizedFuncParameter)obj).value);
	}

	/**
	 *  Returns a copy so you can't edit or damage the origial.
	 *
	 * @return    Exact copy of this object's state
	 */
	public Object clone(){

		EvenlyDiscretizedFuncParameter param = null;
		param = new EvenlyDiscretizedFuncParameter(name,(EvenlyDiscretizedFunc)((EvenlyDiscretizedFunc)value).deepClone());
		if( param == null ) return null;
		param.editable = true;
		param.info = info;
		return param;
	}


	/**
	 *
	 * @returns the EvenlyDiscretizedFunc contained in this parameter
	 */
	public EvenlyDiscretizedFunc getParameter(){
		return (EvenlyDiscretizedFunc)getValue();
	}

	/**
	 * Returns the name of the parameter class
	 */
	public String getType() {
		String type = PARAM_TYPE;
		return type;
	}

	/**
	 * This overrides the getmetadataString() method because the value here
	 * does not have an ASCII representation (and we need to know the values
	 * of the independent parameter instead).
	 * @returns Sstring
	 */
	public String getMetadataString() {
		String metadata = getDependentParamMetadataString();
		metadata +="\n"+"Function Info="+" [ ";
		EvenlyDiscretizedFunc func= (EvenlyDiscretizedFunc)getValue();
		int num = func.getNum();
		for(int i=0;i<num;++i)
			metadata +=(float)func.getX(i)+" "+(float)func.getY(i)+" , ";
		metadata = metadata.substring(0,metadata.lastIndexOf(","));
		metadata +=" ]";
		return metadata;
	}


	public boolean setIndividualParamValueFromXML(Element el) {
		// TODO Auto-generated method stub
		return false;
	}

	public ParameterEditor getEditor() {
		if (paramEdit == null)
			try {
				paramEdit = new EvenlyDiscretizedFuncParameterEditor(this);
			} catch (Exception e) {
				throw new RuntimeException(e);
			}
		return paramEdit;
	}


}


