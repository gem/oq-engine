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

package org.opensha.sha.param;

import java.util.ArrayList;
import java.util.ListIterator;

import org.dom4j.Element;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.EditableException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DependentParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.EvenlyDiscretizedFuncParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.sha.magdist.ArbIncrementalMagFreqDist;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.magdist.YC_1985_CharMagFreqDist;
import org.opensha.sha.param.editor.MagPDF_ParameterEditor;

/**
 *  <b>Title:</b> MagPDF_Parameter<p>
 *
 *  <b>Description:</b> This Parameter contains (or creates from parameters) an
 *  IncremnetalMagFreqDist that is a probability density function (PDF), where the
 *  sum of the discrete rates is eqaul to one (not the area under the curve).
 *  Optionally, a list of allowed pdfs can be specified in a constraint object. If no
 *  constraint object is present then all MagFreDists are permitted<p>
 *
 * @author     Nitin Gupta, Vipin Gupta
 * @created    Oct 18, 2002
 * @version    1.0
 */

public class MagPDF_Parameter
extends DependentParameter
implements java.io.Serializable
{

	/** Class name for debugging. */
	protected final static String C = "MagPDF_Parameter";
	/** If true print out debug statements. */
	protected final static boolean D = false;

	/**
	 * the string for the distribution choice parameter
	 */
	public final static String DISTRIBUTION_NAME="Distribution Type";

	/**
	 * Name and Info strings of params needed by all distributions
	 */
	public static final String MIN=new String("Min");
	public static final String MIN_INFO=new String("Minimum magnitude of the discetized function");
	public static final String MAX=new String("Max");
	public static final String MAX_INFO=new String("Maximum magnitude of the discetized function");
	public static final String NUM=new String("Num");
	public static final String NUM_INFO=new String("Number of points in  the discetized function");

	/**
	 * Name, units, and info strings for parameters needed by more than one distribution (shared)
	 */
	// Gutenberg-Richter dist stuff (used by Y&C dist as well):
	public static final String GR_MAG_UPPER=new String("Mag Upper");
	public static final String GR_MAG_UPPER_INFO=new String("Magnitude of the last non-zero rate");
	public static final String GR_MAG_LOWER=new String("Mag Lower");
	public static final String GR_MAG_LOWER_INFO=new String("Magnitude of the first non-zero rate");
	public static final String GR_BVALUE=new String("b Value");
	public static final String BVALUE_INFO=new String("b in: log(rate) = a-b*magnitude");


	/**
	 * Single Magnitude Frequency Distribution Parameter names
	 */
	public static final String MAG=new String("Mag");

	/**
	 * Young and Coppersmith, 1985 Char dist. parameter names
	 */
	public static final String YC_DELTA_MAG_CHAR = new String("Delta Mag Char");
	public static final String YC_DELTA_MAG_CHAR_INFO = new String("Width of the characteristic part (below Mag Upper)");
	public static final String YC_MAG_PRIME = new String("Mag Prime");
	public static final String YC_MAG_PRIME_INFO = new String("Last magnitude of the GR part");
	public static final String YC_DELTA_MAG_PRIME = new String("Delta Mag Prime");
	public static final String YC_DELTA_MAG_PRIME_INFO = new String("Distance below Mag Prime where rate on GR equals that on the char. part");


	/**
	 * Gaussian Magnitude Frequency Distribution Parameter string list constant
	 */
	public static final String MEAN=new String("Mean");
	public static final String STD_DEV=new String("Std Dev");
	public static final String TRUNCATION_REQ=new String("Truncation Type");
	public static final String TRUNCATE_UPPER_ONLY= new String("Upper");
	public static final String TRUNCATE_ON_BOTH_SIDES= new String("Upper and Lower");
	public static final String TRUNCATE_NUM_OF_STD_DEV= new String("Truncation Level(# of Std Devs)");
	public static final String NONE= new String("None");


	/**
	 * Make the parameter that lists the choice of distributions
	 * Add all the supported paramters based on the selected
	 */
	private ParameterList parameterList = new ParameterList();

	//EvenlyDiscretized Param
	private EvenlyDiscretizedFuncParameter evenlyDiscrtizedFunc;
	//paramName
	public static final String ARB_INCR_PARAM_NAME = " Arb. Incremental Mag Dist";
	
	private transient ParameterEditor paramEdit = null;


	/**
	 *  No constraints specified, all MagFreqDists allowed. Sets the name of this
	 *  parameter.
	 *
	 * @param  name  Name of the parameter
	 */
	public MagPDF_Parameter( String name ) {
		super( name, null, null, null );
		//initialise the mag dist parameters
		initAdjustableParams();
	}



	/**
	 *  Sets the name, defines the constraints as ArrayList of String values. Creates the
	 *  constraint object from these values.
	 *
	 * @param  name                     Name of the parameter
	 * @param  allowedMagDists          ArrayList of allowed values
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public MagPDF_Parameter( String name, ArrayList allowedMagDists ) throws ConstraintException {
		super( name, new MagPDF_Constraint( allowedMagDists ), null, null );
		//initialise the mag dist parameters
		initAdjustableParams();
	}


	/**
	 *  Sets the name and Constraints object.
	 *
	 * @param  name                     Name of the parameter
	 * @param  constraint               defines vector of allowed values
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public MagPDF_Parameter( String name, MagPDF_Constraint constraint ) throws ConstraintException {
		super( name, constraint, null, null );
		//initialise the mag dist parameters
		initAdjustableParams();
	}



	/**
	 *  No constraints specified, all values allowed. Sets the name and value.
	 *
	 * @param  name   Name of the parameter
	 * @param  value  IncrementalMagFreqDist  object
	 */
	public MagPDF_Parameter( String name, IncrementalMagFreqDist value ) {
		super(name, null, null, value);
		//initialise the mag dist parameters
		initAdjustableParams();
	}


	/**
	 *  Sets the name, and value. Also defines the min and max from which the
	 *  constraint is constructed.
	 *
	 * @param  name                     Name of the parameter
	 * @param  value                    IncrementalMagFreqDist object of this parameter
	 * @param  allowedMagDists          ArrayList  of allowed Mag Dists
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public MagPDF_Parameter( String name, ArrayList allowedMagDists, IncrementalMagFreqDist value )
	throws ConstraintException {
		super( name, new MagPDF_Constraint( allowedMagDists ), null, value );
		//initialise the mag dist parameters
		initAdjustableParams();
	}



	/**
	 *  Sets the name, value and constraint. The value is checked if it is
	 *  within constraints.
	 *
	 * @param  name                     Name of the parameter
	 * @param  constraint               vector of allowed Mag Dists
	 * @param  value                    IncrementalMagFreqDist object
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public MagPDF_Parameter( String name, MagPDF_Constraint constraint,
			IncrementalMagFreqDist value ) throws ConstraintException {
		super( name, constraint, null, value );
		//initialise the mag dist parameters
		initAdjustableParams();

	}




	/**
	 *  Sets the constraint if it is a StringConstraint and the parameter
	 *  is currently editable.
	 */
	public void setConstraint(ParameterConstraintAPI constraint)
	throws ParameterException, EditableException
	{

		String S = C + ": setConstraint(): ";
		checkEditable(S);

		if ( !(constraint instanceof MagPDF_Constraint )) {
			throw new ParameterException( S +
					"This parameter only accepts a MagPDF_Constraint, unable to set the constraint."
			);
		}
		else super.setConstraint( constraint );

	}

	/**
	 *  Gets array list of allowed MagPDFs.
	 *
	 * @return                ArrayList of allowed Mag Dists
	 */
	public ArrayList getAllowedMagPDFs()  {
		if ( constraint != null )
			return ( ( MagPDF_Constraint ) constraint ).getAllowedMagDists();
		else return null;
	}




	/**
	 *  Compares the values to if this is less than, equal to, or greater than
	 *  the comparing objects.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         -1 if this value < obj value, 0 if equal,
	 *      +1 if this value > obj value
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a DoubleParameter, or DoubleDiscreteParameter.
	 */
	public int compareTo( Object obj ) throws UnsupportedOperationException {
		throw new java.lang.UnsupportedOperationException("This method not implemented yet");

	}


	/**
	 *  Set's the parameter's value.
	 *
	 * @param  value                 The new value for this Parameter
	 * @throws  ParameterException   Thrown if the object is currenlty not
	 *      editable
	 * @throws  ConstraintException  Thrown if the object value is not allowed
	 */
	public void setValue( IncrementalMagFreqDist value ) throws ConstraintException, ParameterException {
		setValue( (Object) value );
	}

	/**
	 *  Uses the constraint object to determine if the new value being set is
	 *  allowed. If no Constraints are present all values are allowed. This
	 *  function is now available to all subclasses, since any type of
	 *  constraint object follows the same api.
	 *
	 * @param  obj  Object to check if allowed via constraints
	 * @return      True if the value is allowed
	 */
	public boolean isAllowed( IncrementalMagFreqDist d ) {
		return isAllowed( (Object)d );
	}



	/**
	 *  Compares value to see if equal.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         True if the values are identical
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a DoubleParameter, or DoubleDiscreteParameter.
	 */
	public boolean equals( Object obj ) throws UnsupportedOperationException {
		throw new java.lang.UnsupportedOperationException("This method not implemented yet");

	}


	/**
	 *  Returns a copy so you can't edit or damage the origial.
	 *
	 * @return    Exact copy of this object's state
	 */
	public Object clone() throws UnsupportedOperationException {
		throw new java.lang.UnsupportedOperationException("This method not implemented yet");

	}

	/**
	 * Returns the type(full path with the classname) of the MagDist Classes
	 */
	public String getType() {
		String type = C;
		return type;
	}

	/**
	 *
	 * @returns the adjustable parameterlist
	 */
	public ParameterList getAdjustableParams(){
		return parameterList;
	}

	/**
	 * Creates the adjustable params for the MagFreqDistParameter.
	 * @return
	 */
	private void initAdjustableParams() {

		MagDistStringParameter distributionName =new MagDistStringParameter(DISTRIBUTION_NAME,getAllowedMagPDFs(),
				(String) getAllowedMagPDFs().get(0));

		// make the min, delta and num Parameters
		DoubleParameter minParameter = new DoubleParameter(MIN,new Double(0));
		minParameter.setInfo(MIN_INFO);
		DoubleParameter maxParameter = new DoubleParameter(MAX,new Double(10));
		maxParameter.setInfo(MAX_INFO);
		IntegerParameter numParameter = new IntegerParameter(NUM, (int) 0, Integer.MAX_VALUE, new Integer(101));
		numParameter.setInfo(NUM_INFO);

		// Make the other common parameters (used by more than one distribution)
		DoubleParameter magLower = new DoubleParameter(GR_MAG_LOWER, new Double(5));
		magLower.setInfo(GR_MAG_LOWER_INFO);
		DoubleParameter magUpper = new DoubleParameter(GR_MAG_UPPER, new Double(8));
		magUpper.setInfo(GR_MAG_UPPER_INFO);
		DoubleParameter bValue = new DoubleParameter(GR_BVALUE,Double.NEGATIVE_INFINITY, Double.POSITIVE_INFINITY, new Double(1));
		bValue.setInfo(BVALUE_INFO);

		// add Parameters for single Mag freq dist
		DoubleParameter mag = new DoubleParameter(MAG, new Double(8));

		/**
		 * Make parameters for Gaussian distribution
		 */
		DoubleParameter mean = new DoubleParameter(MEAN, new Double(8));
		DoubleParameter stdDev = new DoubleParameter(STD_DEV, 0, Double.POSITIVE_INFINITY, new Double(0.25));
		ArrayList vStrings=new ArrayList();
		vStrings.add(NONE);
		vStrings.add(TRUNCATE_UPPER_ONLY);
		vStrings.add(TRUNCATE_ON_BOTH_SIDES);
		StringParameter truncType=new StringParameter(TRUNCATION_REQ,vStrings,TRUNCATE_UPPER_ONLY);
		DoubleParameter truncLevel = new DoubleParameter(TRUNCATE_NUM_OF_STD_DEV, 0, Double.POSITIVE_INFINITY, new Double (1));


		/**
		 * Make paramters for Youngs and Coppersmith 1985 char distribution
		 */
		DoubleParameter deltaMagChar = new DoubleParameter(YC_DELTA_MAG_CHAR, 0,
				Double.POSITIVE_INFINITY, new Double(1));
		deltaMagChar.setInfo(YC_DELTA_MAG_CHAR_INFO);
		DoubleParameter magPrime = new DoubleParameter(YC_MAG_PRIME, new Double(7));
		magPrime.setInfo(YC_MAG_PRIME_INFO);
		DoubleParameter deltaMagPrime = new DoubleParameter(YC_DELTA_MAG_PRIME, 0, Double.POSITIVE_INFINITY, new Double(1));
		deltaMagPrime.setInfo(YC_DELTA_MAG_PRIME_INFO);


		// Add the parameters to the list (order is preserved)
		parameterList.addParameter(distributionName);
		parameterList.addParameter( minParameter );
		parameterList.addParameter( numParameter );
		parameterList.addParameter( maxParameter );
		// put ones that are always shown next
		parameterList.addParameter(magLower);
		parameterList.addParameter(magUpper);
		parameterList.addParameter(bValue);
		parameterList.addParameter(deltaMagChar);
		parameterList.addParameter(magPrime);
		parameterList.addParameter(deltaMagPrime);
		parameterList.addParameter(mean);
		parameterList.addParameter(stdDev);
		parameterList.addParameter(truncType);
		parameterList.addParameter(truncLevel);
		parameterList.addParameter(mag);
		initArbIncrementalMagFreqDist();
		parameterList.addParameter(evenlyDiscrtizedFunc);
	}

	/**
	 * Initialisez the Arb. Incremental MagFreq Func
	 */
	private void initArbIncrementalMagFreqDist(){
		ArbIncrementalMagFreqDist arbIncrDist = new ArbIncrementalMagFreqDist(0,10,101);
		evenlyDiscrtizedFunc = new EvenlyDiscretizedFuncParameter(ARB_INCR_PARAM_NAME,
				arbIncrDist);
	}



	/**
	 * Updates the MagFreqDistParams with the new parameters.
	 * @param newParamList Cloned Parameterlist
	 */
	public void setMagDist(ParameterList newParamList) {
		ListIterator it = newParamList.getParametersIterator();
		while(it.hasNext()){
			ParameterAPI tempParam = (ParameterAPI)it.next();
			parameterList.getParameter(tempParam.getName()).setValue(tempParam.getValue());
		}

		setMagDist();
	}

	/**
	 * set the IncrementalMagFreqDist object based on parameters given
	 * @param parameterList
	 * @return
	 */
	public void setMagDist() {
		String S = C + ": getMagDist():";
		String distributionName = parameterList.getParameter(DISTRIBUTION_NAME).getValue().toString();

		//stores the visible parameters for the MagFreqDist parameter as the independent parameters
		ParameterList independentParamList = new ParameterList();
		independentParamList.addParameter(parameterList.getParameter(DISTRIBUTION_NAME));

		IncrementalMagFreqDist magDist = null;
		try {
			Double min = (Double) parameterList.getParameter(MIN).getValue();
			Double max = (Double) parameterList.getParameter(MAX).getValue();
			Integer num = (Integer) parameterList.getParameter(NUM).getValue();

			if (min.doubleValue() > max.doubleValue()) {
				throw new java.lang.RuntimeException(
						"Min Value cannot be less than the Max Value");
			}

			independentParamList.addParameter(parameterList.getParameter(MIN));
			independentParamList.addParameter(parameterList.getParameter(MAX));
			independentParamList.addParameter(parameterList.getParameter(NUM));

			/*
			 * If Single MagDist is selected
			 */
			if (distributionName.equalsIgnoreCase(SingleMagFreqDist.NAME)) {
				if (D) System.out.println(S + " selected distribution is SINGLE");
				SingleMagFreqDist single = new SingleMagFreqDist(min.doubleValue(),
						max.doubleValue(), num.intValue());
				double mag = ( (Double) parameterList.getParameter(MAG).getValue()).
				doubleValue();
				if (mag > max.doubleValue() || mag < min.doubleValue()) {
					throw new java.lang.RuntimeException(
							"Value of Mag must lie between the min and max value");
				}

				independentParamList.addParameter(parameterList.getParameter(MAG));
				try {
					single.setMagAndRate(mag, 1.0);
				}
				catch (RuntimeException e) {
					throw new java.lang.RuntimeException(
							"The chosen magnitude must fall on one of the discrete x-axis values");
				}

				if (D) System.out.println(S + " after setting SINGLE DIST");
				magDist = (IncrementalMagFreqDist) single;
			}

			/*
			 * If Gaussian MagDist is selected
			 */
			else if (distributionName.equalsIgnoreCase(GaussianMagFreqDist.NAME)) {
				Double mean = (Double) parameterList.getParameter(MEAN).getValue();
				Double stdDev = (Double) parameterList.getParameter(STD_DEV).getValue();
				String truncTypeValue = parameterList.getParameter(TRUNCATION_REQ).getValue().toString();
				if (mean.doubleValue() > max.doubleValue() ||
						mean.doubleValue() < min.doubleValue()) {
					throw new java.lang.RuntimeException(
							"Value of Mean must lie between the min and max value");
				}
				independentParamList.addParameter(parameterList.getParameter(MEAN));
				independentParamList.addParameter(parameterList.getParameter(STD_DEV));
				independentParamList.addParameter(parameterList.getParameter(TRUNCATION_REQ));

				int truncType = 0;
				if (truncTypeValue.equalsIgnoreCase(TRUNCATE_UPPER_ONLY))
					truncType = 1;
				else if (truncTypeValue.equalsIgnoreCase(TRUNCATE_ON_BOTH_SIDES))
					truncType = 2;

				Double truncLevel = new Double(Double.NaN);
				if (truncType != 0) {
					truncLevel = (Double) parameterList.getParameter(TRUNCATE_NUM_OF_STD_DEV).getValue();
					independentParamList.addParameter(parameterList.getParameter(TRUNCATE_NUM_OF_STD_DEV));
				}
				GaussianMagFreqDist gaussian = new GaussianMagFreqDist(min.doubleValue(),
						max.doubleValue(), num.intValue());
				gaussian.setAllButTotMoRate(mean.doubleValue(), stdDev.doubleValue(),
						1.0,truncLevel.doubleValue(), truncType);
				magDist = (IncrementalMagFreqDist) gaussian;
			}

			/*
			 * If Gutenberg Richter MagDist is selected
			 */
			else if (distributionName.equalsIgnoreCase(GutenbergRichterMagFreqDist.NAME)) {
				GutenbergRichterMagFreqDist gR =
					new GutenbergRichterMagFreqDist(min.doubleValue(), max.doubleValue(),
							num.intValue());

				Double bValue = (Double) parameterList.getParameter(GR_BVALUE).getValue();

				Double magLower = (Double) parameterList.getParameter(GR_MAG_LOWER).getValue();
				if (magLower.doubleValue() > max.doubleValue() ||
						magLower.doubleValue() < min.doubleValue()) {
					throw new java.lang.RuntimeException(
							"Value of MagLower must lie between the min and max value");
				}

				Double magUpper = (Double) parameterList.getParameter(GR_MAG_UPPER).getValue();
				if (magUpper.doubleValue() > max.doubleValue() ||
						magUpper.doubleValue() < min.doubleValue()) {
					throw new java.lang.RuntimeException(
							"Value of MagUpper must lie between the min and max value");
				}
				if (magLower.doubleValue() > magUpper.doubleValue()) {
					throw new java.lang.RuntimeException(
							"Value of MagLower must be <= to MagUpper");
				}

				try {
					gR.setAllButTotMoRate(magLower.doubleValue(), magUpper.doubleValue(),
							1.0, bValue.doubleValue());
				}
				catch (RuntimeException e) {
					throw new java.lang.RuntimeException(
							"magUpper and MagLower must fall on one of the discrete x-axis values");
				}

				independentParamList.addParameter(parameterList.getParameter(GR_MAG_UPPER));
				independentParamList.addParameter(parameterList.getParameter(GR_MAG_LOWER));
				independentParamList.addParameter(parameterList.getParameter(GR_BVALUE));

				magDist = (IncrementalMagFreqDist) gR;
			}

			/*
			 * If Young and Coppersmith 1985 MagDist is selected
			 */
			else if (distributionName.equalsIgnoreCase(YC_1985_CharMagFreqDist.NAME)) {

				double magLower = ( (Double) parameterList.getParameter(
						GR_MAG_LOWER).getValue()).doubleValue();
				double magUpper = ( (Double) parameterList.getParameter(
						GR_MAG_UPPER).getValue()).doubleValue();
				double deltaMagChar = ( (Double) parameterList.getParameter(
						YC_DELTA_MAG_CHAR).getValue()).doubleValue();
				double magPrime = ( (Double) parameterList.getParameter(
						YC_MAG_PRIME).getValue()).doubleValue();
				double deltaMagPrime = ( (Double) parameterList.getParameter(
						YC_DELTA_MAG_PRIME).getValue()).doubleValue();
				double bValue = ( (Double) parameterList.getParameter(
						GR_BVALUE).getValue()).doubleValue();


				// check that maglowe r value lies betwenn min and max
				if (magLower > max.doubleValue() || magLower < min.doubleValue()) {
					throw new java.lang.RuntimeException(
							"Value of MagLower must lie between the min and max value");
				}
				// check that magUpper value lies between min and max
				if (magUpper > max.doubleValue() || magUpper < min.doubleValue()) {
					throw new java.lang.RuntimeException(
							"Value of MagUpper must lie between the min and max value");
				}

				// creat the distribution
				YC_1985_CharMagFreqDist yc =
					new YC_1985_CharMagFreqDist(min.doubleValue(), max.doubleValue(),
							num.intValue());

				// Check that the mags fall on valid x increments:
				int trialInt;
				try {
					trialInt = yc.getXIndex(magLower);
				}
				catch (RuntimeException e) {
					throw new java.lang.RuntimeException(
							"MagLower must fall on one of the discrete x-axis values");
				}
				try {
					trialInt = yc.getXIndex(magUpper);
				}
				catch (RuntimeException e) {
					throw new java.lang.RuntimeException(
							"MagUpper must fall on one of the discrete x-axis values");
				}
				try {
					trialInt = yc.getXIndex(magPrime);
				}
				catch (RuntimeException e) {
					throw new java.lang.RuntimeException(
							"MagPrime must fall on one of the discrete x-axis values");
				}
				try {
					trialInt = yc.getXIndex(magPrime - deltaMagPrime);
				}
				catch (RuntimeException e) {
					throw new java.lang.RuntimeException(
							"MagPrime-DeltaMagPrime must fall on one of the discrete x-axis values");
				}
				try {
					trialInt = yc.getXIndex(magUpper - deltaMagChar);
				}
				catch (RuntimeException e) {
					throw new java.lang.RuntimeException(
							"MagUpper-DeltaMagChar must fall on one of the discrete x-axis values");
				}
				independentParamList.addParameter(parameterList.getParameter(GR_MAG_LOWER));
				independentParamList.addParameter(parameterList.getParameter(GR_MAG_UPPER));
				independentParamList.addParameter(parameterList.getParameter(YC_DELTA_MAG_CHAR));
				independentParamList.addParameter(parameterList.getParameter(YC_MAG_PRIME));
				independentParamList.addParameter(parameterList.getParameter(YC_DELTA_MAG_PRIME));
				independentParamList.addParameter(parameterList.getParameter(GR_BVALUE));

				yc.setAllButTotMoRate(magLower, magUpper,
						deltaMagChar, magPrime,
						deltaMagPrime, bValue,
						1.0);
				// normalize so total rate is 1.0
				yc.normalizeByTotalRate();

				magDist = (IncrementalMagFreqDist) yc;
			}

		}
		catch (java.lang.NumberFormatException e) {
			throw new NumberFormatException(
					"Value entered must be a valid Numerical Value");
		}
		catch (java.lang.NullPointerException e) {
			throw new NullPointerException("Enter All values");
		}
		this.setValue(magDist);
		//creates the independent parameterList for the MagFreqDist.
		//It only saves those parameters for visible distribution.

		setIndependentParameters(independentParamList);
	}

	/**
	 * This overrides the getmetadataString() method because the value here
	 * does not have an ASCII representation (and we need to know the values
	 * of the independent parameter instead).
	 * @returns Sstring
	 */
	public String getMetadataString() {
		return getDependentParamMetadataString();
	}


	public boolean setIndividualParamValueFromXML(Element el) {
		// TODO Auto-generated method stub
		return false;
	}

	public ParameterEditor getEditor() {
		if (paramEdit == null)
			paramEdit = new MagPDF_ParameterEditor(this);
		return paramEdit;
	}

}
