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

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.TreeBranchWeightsParameterEditor;

/**
 * <p>Title: TreeBranchWeightsParameter</p>
 * <p>Description: This is a new parameter which contains the parameterList of the
 * different weights for the branches</p>
 * @author : Edward (Ned) Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class TreeBranchWeightsParameter extends ParameterListParameter
implements  java.io.Serializable{

	/** Class name for debugging. */
	protected final static String C = "TreeBranchWeightsParameter";
	/** If true print out debug statements. */
	protected final static boolean D = false;
	protected final static String PARAM_TYPE = C;

	private double tolerance = .01;
	
	private transient ParameterEditor paramEdit = null;

	/**
	 *  No constraints specified for this parameter. Sets the name of this
	 *  parameter.
	 *
	 * @param  name  Name of the parameter
	 */
	public TreeBranchWeightsParameter(String name) {
		super(name);
	}

	/**
	 * No constraints specified, all values allowed. Sets the name and value.
	 *
	 * @param  name   Name of the parameter
	 * @param  paramList  ParameterList  object
	 */
	public TreeBranchWeightsParameter(String name, ParameterList paramList){
		super(name,paramList);
	}


	/**
	 * sets the tolerance for the sums of the weights
	 * @param tolerance
	 */
	public void setTolerence(double tolerance){
		this.tolerance = tolerance;
	}

	/**
	 * gets the tolerence for the sum of branch weights
	 * @return
	 */
	public double getTolerance(){
		return this.tolerance;
	}

	/**
	 * Set's the parameter's value. It checks that all the weights Parameter in this parameterList
	 * should be DoubleParameter.
	 *
	 * @param  value                 The new value for this Parameter
	 * @throws  ParameterException   Thrown if the object is currenlty not
	 *      editable
	 * @throws  ConstraintException  Thrown if the object value is not allowed
	 */
	public void setValue( ParameterList value ) throws ParameterException {

		ListIterator it  = value.getParametersIterator();
		while(it.hasNext()){
			ParameterAPI param = (ParameterAPI)it.next();
			if(!(param instanceof DoubleParameter))
				throw new RuntimeException(C+" Only DoubleParameter allowed in this Parameter");
		}
		setValue(value );
	}

	/**
	 *
	 * @returns true if the Branch Weight Values sum to One, inside the parameterList
	 * lie within the range of "1".
	 * else return false.
	 */
	public boolean doWeightsSumToOne(ParameterList paramList){
		ListIterator it =paramList.getParametersIterator();
		double paramsSum=0;
		while(it.hasNext()){
			paramsSum += ((Double)((ParameterAPI)it.next()).getValue()).doubleValue();
		}
		return isInTolerence(paramsSum);
	}

	/**
	 * check if this parameter values  lies in tolerence
	 * @param num - sum of the parameter value
	 * @return
	 */
	private boolean isInTolerence(double num){
		if((num <= (1+this.tolerance)) && (num >= (1-this.tolerance)))
			return true;
		return false;
	}

	/**
	 * Returns the name of the parameter class
	 */
	public String getType() {
		String type = this.PARAM_TYPE;
		return type;
	}
	
	@Override
	public ParameterEditor getEditor() {
		if (paramEdit == null)
			paramEdit = new TreeBranchWeightsParameterEditor(this);
		return paramEdit;
	}
}


