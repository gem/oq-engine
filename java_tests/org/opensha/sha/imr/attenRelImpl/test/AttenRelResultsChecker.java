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

package org.opensha.sha.imr.attenRelImpl.test;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.DoubleDiscreteParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.commons.util.DataUtils;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.PropagationEffectParams.WarningDoublePropagationEffectParameter;


/**
 * <p>Title: AttenRelResultsChecker</p>
 * <p>Description: This class provide the common implementation of the functions for all the
 * AttenuationRelationships testcases classes</p>
 * @author :Ned Field, Nitin Gupta and Vipin Gupta
 * @created :July 7, 2003
 * @version 1.0
 */

public class AttenRelResultsChecker {

	private ParameterList list = new ParameterList();
	private ScalarIntensityMeasureRelationshipAPI imr;
	private String resultFile= null;

	//hardcode strings string val for all the X and Y axis values that are shown
	//in the combo box for the user selection as the control params editor
	public final static String X_AXIS_NAME = "X-Axis";
	public final static String Y_AXIS_NAME = "Y-Axis";
	public final static String Y_AXIS_MEDIAN = "Median";
	public final static String Y_AXIS_STD_DEV = "Std. Dev.";
	public final static String Y_AXIS_EXCEED_PROB = "Exceed Prob.";
	public final static String Y_AXIS_IML_AT_PROB = "IML at Exceed Prob.";

	//static int values for the Y values in IMR
	public final static int MEAN = 1;
	public final static int STD_DEV = 2;
	public final static int EXCEED_PROB = 3;
	public final static int IML_AT_EXCEED_PROB = 4;

	//Deciaml format to restrict the result to 6 places of decimal for the IMR computed values
	private DecimalFormat decimalFormat=new DecimalFormat("0.000000##");

	//stores the parameters settings for the
	private String failedParamsSetting =null;

	//checks if the resulted values lies within the this tolerence range
	private double tolerence = .01; //default value for the tolerence

	private final static String parameterSetString = "SetParameter";
	public final static String getParamValString = "GetValue";
	private final static String intensitySetString = "SetIntensityMeasure";



	//ArrayList to store the failed testCases
	//private ArrayList testCaseNumberVector = new ArrayList();

	//ArrayList to store the ControlParams name and Value
	private ArrayList controlParamVector = new ArrayList();

	//ArrayList to store the IndependentParams name and Value
	private ArrayList independentParamVector = new ArrayList();

	//keeps the counts of the test cases in the file
	int testCaseNumber =0;
	//String to Stores the controls param with their values
	//private String xControlName;
	private String yControlName;
	private String intensityMeasureName=null;


	public AttenRelResultsChecker(ScalarIntensityMeasureRelationshipAPI imr, String file, double tolerence) {
		this.imr = imr;
		this.resultFile = file;
		//initially the parameterList is empty but when te constructr is called
		//we add the parameters to te paramList
		//adding the ExceedProb Params to the ParamList
		ListIterator it =imr.getExceedProbIndependentParamsIterator();
		while(it.hasNext()){
			ParameterAPI param = (ParameterAPI)it.next();
			if ( !( list.containsParameter( param.getName() ) ) )
				list.addParameter( param );
		}

		//adding the IML@ Exceed Prob params to the ParamList
		it =imr.getIML_AtExceedProbIndependentParamsIterator();
		while(it.hasNext()){
			ParameterAPI param = (ParameterAPI)it.next();
			if ( !( list.containsParameter( param.getName() ) ) )
				list.addParameter( param );
		}

		//adding the mean Independent params to the ParamList
		it =imr.getMeanIndependentParamsIterator();
		while(it.hasNext()){
			ParameterAPI param = (ParameterAPI)it.next();
			if ( !( list.containsParameter( param.getName() ) ) )
				list.addParameter( param );
		}

		//adding the Std. Dev Independent params to the ParamList
		it =imr.getStdDevIndependentParamsIterator();
		while(it.hasNext()){
			ParameterAPI param = (ParameterAPI)it.next();
			if ( !( list.containsParameter( param.getName() ) ) )
				list.addParameter( param );
		}

		//set the tolernce value for that IMR
		this.tolerence = tolerence;

	}

	/**
	 * This function reads the AttenuationRelationship Result set data file,
	 * does the calculation for each test set in the file and compares whether
	 * the result produced by the SHA code is within the acceptable range of the
	 * actual result that is stored in the file with each test set.
	 * Each test set corresponds to different parameters setting to get the target result.
	 * That result set is like a benchMark for us to compare the SHA outputs for those parameters
	 * settings with the result in the file.
	 * @throws IOException 
	 */
	public boolean readResultFile() throws IOException{
//		return readResultFile(resultFile + "_new.txt");
		return readResultFile(resultFile);
	}

	/**
	 * This function reads the AttenuationRelationship Result set data file,
	 * does the calculation for each test set in the file and compares whether
	 * the result produced by the SHA code is within the acceptable range of the
	 * actual result that is stored in the file with each test set.
	 * Each test set corresponds to different parameters setting to get the target result.
	 * That result set is like a benchMark for us to compare the SHA outputs for those parameters
	 * settings with the result in the file.
	 * @throws IOException 
	 */
	public boolean readResultFile(String newOutFile) throws IOException{
		boolean result = true;

		StringBuffer outBuff = null;
		if (newOutFile != null) {
			outBuff = new StringBuffer();
		}
		//which file to read for the AttenREl testcase
//		FileReader fr = new FileReader(resultFile);
//		BufferedReader br = new BufferedReader(fr);
		BufferedReader br = new BufferedReader(new InputStreamReader(this.getClass().getResourceAsStream(resultFile)));
		//read the first line in the file which is the name of the AttenuationRelationship and discard it
		//becuase we do nothing with it currently
		String str = br.readLine().trim();
		if (outBuff != null) outBuff.append(str + "\n");

		// reads the first line in the file
		str = (br.readLine()).trim();

		//keep reading the file until file pointer reaches the end of file.
		while(str !=null){
			str= str.trim();
			//       System.out.println("Line Read: "+str);
			//if the line contains nothing, just skip that line and read next
			if(str.equalsIgnoreCase("")) {
				str = br.readLine();
				if (outBuff != null) outBuff.append("\n");
				//if the line contains some data
			} else {
				// System.out.println("Line Read: "+str);
				//if the String read is the Intensity Measure value in the file
				if(str.trim().startsWith(intensitySetString)){
					if (outBuff != null) outBuff.append(str + "\n");
					//setting the imr parameters default value with the start of new test case
					//set the defaults values for that AttenuationRelationship
					imr.setParamDefaults();
					String st = str.substring(str.indexOf("(")+1,str.indexOf(")")).trim();
					imr.setIntensityMeasure(st);
					intensityMeasureName = st;

					ListIterator supportedIntensityMeasureIterator =imr.getSupportedIntensityMeasuresIterator();
					//Adding the independent Parameters to the param List
					while ( supportedIntensityMeasureIterator.hasNext() ) {
						DependentParameterAPI param = ( DependentParameterAPI ) supportedIntensityMeasureIterator.next();
						//System.out.println("Intensity Measure Param Name:"+param.getName());
						if(param.getName().equalsIgnoreCase(intensityMeasureName)){
							//adding the intensity measure parameter
							if(!list.containsParameter(param))
								list.addParameter(param);
							Iterator it=param.getIndependentParametersIterator();
							//adding the independent Params for the intensity Measure Param
							while(it.hasNext()){
								ParameterAPI  tempParam =(ParameterAPI)it.next();
								if(!list.containsParameter(tempParam))
									this.list.addParameter(tempParam);
							}
						}
					}
					//System.out.println("Intensity Measure Name: "+st);
					++this.testCaseNumber;
					failedParamsSetting = "\n\nTest Case Number: "+ testCaseNumber+"\n";
					failedParamsSetting += "Intensity Measure Type: "+intensityMeasureName+"\n";
				}

				//if the String read is the Param name and its value from the file
				else if(str.startsWith(parameterSetString)){
					if (outBuff != null) outBuff.append(str + "\n");
					//getting the parameterName
					String paramName = str.substring(str.indexOf("\"")+1,str.indexOf("\")")).trim();

					//getting teh parameter Value
					String paramVal = str.substring(str.indexOf("=")+1).trim();
					if(paramVal.startsWith("\""))
						paramVal = paramVal.substring(paramVal.indexOf("\"")+1,paramVal.lastIndexOf("\"")).trim();

					failedParamsSetting += "\t"+"\""+paramName+"\""+" = "+ paramVal+"\n";

					//System.out.println("ParameterName: "+paramName);
					//System.out.println("ParameterVal: "+paramVal);
					//we only need to get the parameters whose names have been given in the
					//file, result of the params will be set with the default values
					ParameterAPI tempParam = list.getParameter(paramName);

					//setting the value of the param based on which type it is: StringParameter,
					//DoubleParameter,IntegerParameter or WarningDoublePropagationEffectParameter(special parameter for propagation)
					if(tempParam instanceof StringParameter)
						tempParam.setValue(paramVal);
					if(tempParam instanceof DoubleParameter)
						tempParam.setValue(new Double(paramVal));
					if(tempParam instanceof IntegerParameter)
						tempParam.setValue(new Integer(paramVal));
					if(tempParam instanceof DoubleDiscreteParameter)
						tempParam.setValue(new Double(paramVal));
					if(tempParam instanceof WarningDoublePropagationEffectParameter) {
						((WarningDoublePropagationEffectParameter)tempParam).setIgnoreWarning(true);
						tempParam.setValue(new Double(paramVal));
					}


				}
				else if(str.startsWith(getParamValString)){
					//stores the int value for the selected Y-axis param
					int yAxisValue =0;
					String st = str.substring(str.indexOf("\"")+1,str.lastIndexOf("\"")).trim();
					if(st.equalsIgnoreCase(Y_AXIS_MEDIAN))
						yAxisValue = MEAN;
					else if(st.equalsIgnoreCase(Y_AXIS_STD_DEV))
						yAxisValue = STD_DEV;
					else if(st.equalsIgnoreCase(Y_AXIS_EXCEED_PROB))
						yAxisValue = EXCEED_PROB;
					else if(st.equalsIgnoreCase(Y_AXIS_IML_AT_PROB))
						yAxisValue = IML_AT_EXCEED_PROB;
					//name and value for the Y-Control Parameter
					this.yControlName = st;

					//getting the value of the Y_Axis Param as specified in the file from the test cases
					//which will be compared to the SHA value for the Y_Axis Param
					double yAxisParamVal =new Double(str.substring(str.indexOf("=")+1).trim()).doubleValue();
					decimalFormat.setMaximumFractionDigits(6);
					failedParamsSetting += "GetValue For Param: "+"\""+yControlName+"\": "+"\n";
					double yAxisParamValFromSHA =this.getCalculation(yAxisValue);
					double orignNoRoundSHAVal = yAxisParamValFromSHA;
					yAxisParamValFromSHA = Double.parseDouble(decimalFormat.format(yAxisParamValFromSHA));
					failedParamsSetting += "\tOpenSHA value for: "+"\""+yControlName+"\" = "+yAxisParamValFromSHA;
					failedParamsSetting += ",\tbut it should be : "+ yAxisParamVal+"\n";

					// this line has the old rounding error we found
					//						if (outBuff != null) outBuff.append(getParamValString + "(\"" + st + "\") = " + decimalFormat.format(yAxisParamValFromSHA) + "\n");
					// this line makes files without the rounding error
					if (outBuff != null) outBuff.append(getParamValString + "(\"" + st + "\") = " + decimalFormat.format(orignNoRoundSHAVal) + "\n");

					//compare the computed result using SHA with the target result for the defined set of parameters
					boolean tempRsult =compareResults(yAxisParamValFromSHA, yAxisParamVal);
					//if the test was failure the add it to the test cases Vecotr that stores the values for  that failed
					if(tempRsult == false) {
						System.out.println("RESULT FALSE!!!!");
						if (outBuff == null)
							return tempRsult;
						else
							result = tempRsult;
					}
					//  this.testCaseNumberVector.add(new Integer(this.testCaseNumber));*/

					//adding the Control Param names and Value to ArrayList for all the test cases
					this.controlParamVector.add(this.getControlParametersValueForTest());
					//adding the Independent Param names and Value to ArrayList for all the test cases
					this.independentParamVector.add(this.getIndependentParametersValueForTest());
				}
				//reads the next line in the file
				str = br.readLine();
			}
		}
		if (!result && outBuff != null) {
			FileWriter fw;
			try {
				fw = new FileWriter(newOutFile);
				fw.write(outBuff.toString());
				fw.close();
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}

		// test cases vector that contains the failed test number
		//if the size of this vector is not zero then return false(to make sure that some test did failed)
		/*if(this.testCaseNumberVector.size() >0)
      return false;*/
		return result;
	}

	/**
	 * This function compares the values we obtained after running the values for
	 * the IMR and the target Values( our benchmark)
	 * @param valFromSHA = values we got after running the OpenSHA code for the IMR
	 * @param targetVal = values we are comparing with to see if OpenSHA does correct calculation
	 * @return
	 */
	private boolean compareResults(double valFromSHA,
			double targetVal){
		//comparing each value we obtained after doing the IMR calc with the target result
		//and making sure that values lies with the .01% range of the target values.
		//comparing if the values lies within the actual tolerence range of the target result
		double result = 0;
		if(targetVal!=0) {
//			result =(StrictMath.abs(valFromSHA-targetVal)/targetVal)*100;
			result = DataUtils.getPercentDiff(valFromSHA, targetVal);
		}
		
		

		//System.out.println("Result: "+ result);
		if(result < this.tolerence) {
			return true;
		} else {
			System.out.println("bad result. myVal: " + valFromSHA + " target: " + targetVal + " diff: " + result + "%");
			return false;
		}
	}


	/**
	 *
	 * @returns the formatted String for the Failed test result
	 */
	public String getFailedTestParamsSettings(){
		return this.failedParamsSetting;
	}

	/**
	 *  Returns the intensity measure relationship calculation for either mean,
	 *  std. dev or exceedence probability depending on which type is desired.
	 *
	 * @param  type  1 for mean, 2 for std. dev. and 3 for exceedence
	 *      probability
	 * @return       The imr calculation
	 */
	private double getCalculation( int type ) {
		double result =  0.0;
		/**
		 * @todo FIX - Legend AttenRel translation done here.
		 * may be poor design, what if AttenRel types change to another type in future.
		 * Translated parameters should deal directly with ParameterAPI, not specific subclass
		 * types.
		 */

		ParameterAPI imParam = (ParameterAPI)imr.getIntensityMeasure();
		if( imParam instanceof WarningDoubleParameter){
			WarningDoubleParameter warnParam = (WarningDoubleParameter)imParam;
			if(((Double)imParam.getValue()).doubleValue() >0)
				warnParam.setValueIgnoreWarning(new Double(Math.log(((Double)imParam.getValue()).doubleValue())));
		}

		switch ( type ) {
		case MEAN:
			result = Math.exp( imr.getMean() );
			break;
		case EXCEED_PROB:
			result = imr.getExceedProbability();
			break;
		case STD_DEV:
			result = imr.getStdDev();
			break;
		case IML_AT_EXCEED_PROB :
			result = Math.exp(imr.getIML_AtExceedProb());
			break;
		}
		return result;
	}




	/**
	 *
	 * @returns the name and value for the independent params setting for the test cases
	 */
	private String getIndependentParametersValueForTest(){
		String independentParamValue="";

		ListIterator it  = list.getParametersIterator();
		while(it.hasNext()){
			ParameterAPI tempParam = (ParameterAPI)it.next();
			independentParamValue +=tempParam.getName()+" = "+tempParam.getValue()+"\n\t";
		}
		return independentParamValue +"\n\t";
	}

	/**
	 *
	 * @returns the name and Value for the control params setting of the test cases IMR
	 */
	private String getControlParametersValueForTest(){
		return this.intensityMeasureName+";"+this.yControlName+"\n\t";
	}

	/**
	 *
	 * @returns the ArrayList that contains the Values for control param value for all the test cases
	 */

	public ArrayList getControlParamsValueForAllTests(){
		return this.controlParamVector;
	}

	/**
	 *
	 * @returns the ArrayList that contains the Values for independent param value for all the test cases
	 */
	public ArrayList getIndependentParamsValueForAllTests(){
		return this.independentParamVector;
	}

	/**
	 *
	 * @returns the ArrayList for the testCases number that failed
	 */
	/* public ArrayList getFailedTestResultNumberList(){
    return this.testCaseNumberVector;
  }*/
}
