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

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final;


import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Ellsworth_B_WG02_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.param.Parameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.sha.earthquake.ERF_EpistemicList;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.analysis.ParamOptions;

/**
 * It creates UCERF2 Epistemic List for Time Independent model
 * 
 * @author vipingupta
 *
 */
public class UCERF2_TimeIndependentEpistemicList extends ERF_EpistemicList {
	public static final String  NAME = new String("UCERF2 ERF Epistemic List");
	private ArrayList<Double> weights = null;
	private ArrayList<ParameterList> logicTreeParamList = null;
	protected UCERF2 ucerf2 = new UCERF2();
	protected ArrayList<String> logicTreeParamNames; // parameters that are adjusted for logic tree
	protected ArrayList<ParamOptions> logicTreeParamValues; // paramter values and their weights
	private int lastParamIndex;
	private final static double DURATION_DEFAULT = 30;
	private StringParameter backSeisParam, backSeisRupParam, floaterTypeParam;
	
	public UCERF2_TimeIndependentEpistemicList() {
		fillLogicTreeParams(); // fill the parameters that will be adjusted for the logic tree
		lastParamIndex = logicTreeParamNames.size()-1;
		weights = new ArrayList<Double>();
		logicTreeParamList = new ArrayList<ParameterList>();
		findBranches(0, 1);
		// create and add adj params
		initAdjParams();
		// create the time-ind timespan object with start time and duration in years
		timeSpan = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
		timeSpan.setDuration(DURATION_DEFAULT);
		timeSpan.addParameterChangeListener(this);
	}
	
	
	/**
	 * This intializes the adjustable parameters
	 */
	private void initAdjParams() {

		// background seismicity include/exclude  
		ArrayList<String> backSeisOptionsStrings = new ArrayList<String>();
		backSeisOptionsStrings.add(UCERF2.BACK_SEIS_EXCLUDE);
		backSeisOptionsStrings.add(UCERF2.BACK_SEIS_INCLUDE);
		backSeisOptionsStrings.add(UCERF2.BACK_SEIS_ONLY);
		backSeisParam = new StringParameter(UCERF2.BACK_SEIS_NAME, backSeisOptionsStrings, UCERF2.BACK_SEIS_DEFAULT);
		backSeisParam.addParameterChangeListener(this);
		
		// backgroud treated as point sources/finite sources
		ArrayList<String> backSeisRupStrings = new ArrayList<String>();
		backSeisRupStrings.add(UCERF2.BACK_SEIS_RUP_POINT);
		backSeisRupStrings.add(UCERF2.BACK_SEIS_RUP_FINITE);
		backSeisRupStrings.add(UCERF2.BACK_SEIS_RUP_CROSSHAIR);
		backSeisRupParam = new StringParameter(UCERF2.BACK_SEIS_RUP_NAME, backSeisRupStrings, UCERF2.BACK_SEIS_RUP_DEFAULT);

		// Floater Type Param
		ArrayList<String> floaterTypes = new ArrayList<String>();
		floaterTypes.add(UCERF2.FULL_DDW_FLOATER);
		floaterTypes.add(UCERF2.STRIKE_AND_DOWNDIP_FLOATER);
		floaterTypes.add(UCERF2.CENTERED_DOWNDIP_FLOATER);
		floaterTypeParam = new StringParameter(UCERF2.FLOATER_TYPE_PARAM_NAME, floaterTypes, UCERF2.FLOATER_TYPE_PARAM_DEFAULT);
	
		createParamList();
	}
	
	/**
	 * Put parameters in theParameterList
	 */
	private void createParamList() {
		adjustableParams = new ParameterList();
		adjustableParams.addParameter(floaterTypeParam);
		adjustableParams.addParameter(backSeisParam);	
		if(!backSeisParam.getValue().equals(UCERF2.BACK_SEIS_EXCLUDE))
			adjustableParams.addParameter(backSeisRupParam);
	}
	
    /*  This is the main function of this interface. Any time a control
     * If Backgroud seismicity is included, show BACK_SEIS_RUP parameter else hide it
	 *
	 * @param  event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		super.parameterChange(event);
		String paramName = event.getParameterName();
		if (paramName.equalsIgnoreCase(UCERF2.BACK_SEIS_NAME)) {
			createParamList();
		} 
	}
	
	
	/**
	 * Paramters that are adjusted in the runs
	 *
	 */
	protected void fillLogicTreeParams() {
		ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_POISSON);
		this.logicTreeParamNames = new ArrayList<String>();
		this.logicTreeParamValues = new ArrayList<ParamOptions>();
		
		// Deformation model
		logicTreeParamNames.add(UCERF2.DEFORMATION_MODEL_PARAM_NAME);
		ParamOptions options = new ParamOptions();
		options.addValueWeight("D2.1", 0.25);
		options.addValueWeight("D2.2", 0.1);
		options.addValueWeight("D2.3", 0.15);
		options.addValueWeight("D2.4", 0.25);
		options.addValueWeight("D2.5", 0.1);
		options.addValueWeight("D2.6", 0.15);
		logicTreeParamValues.add(options);
		
		// Mag Area Rel
		logicTreeParamNames.add(UCERF2.MAG_AREA_RELS_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(Ellsworth_B_WG02_MagAreaRel.NAME, 0.5);
		options.addValueWeight(HanksBakun2002_MagAreaRel.NAME, 0.5);
		logicTreeParamValues.add(options);
		
		// A-Fault solution type
		logicTreeParamNames.add(UCERF2.RUP_MODEL_TYPE_NAME);
		options = new ParamOptions();
		options.addValueWeight(UCERF2.SEGMENTED_A_FAULT_MODEL, 0.9);
		options.addValueWeight(UCERF2.UNSEGMENTED_A_FAULT_MODEL, 0.1);
		logicTreeParamValues.add(options);
		
		// Aprioti wt param
		logicTreeParamNames.add(UCERF2.REL_A_PRIORI_WT_PARAM_NAME);
		 options = new ParamOptions();
		options.addValueWeight(new Double(1e-4), 0.5);
		options.addValueWeight(new Double(1e10), 0.5);
		logicTreeParamValues.add(options);
		
		//	Connect More B-Faults?
		logicTreeParamNames.add(UCERF2.CONNECT_B_FAULTS_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Boolean(true), 0.5);
		options.addValueWeight(new Boolean(false), 0.5);
		logicTreeParamValues.add(options);
		
		// B-Fault bValue=0
		logicTreeParamNames.add(UCERF2.B_FAULTS_B_VAL_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Double(0.8), 0.5);
		options.addValueWeight(new Double(0.0), 0.5);
		logicTreeParamValues.add(options);
	}
	
	/**
	 * Get weight for parameter and value
	 * 
	 * @param paramName
	 * @param val
	 * @return
	 */
	public double getWtForParamVal(String paramName, Object val) {
		int paramIndex = logicTreeParamNames.indexOf(paramName);
		ParamOptions options = logicTreeParamValues.get(paramIndex);
		int numValues = options.getNumValues();
		for(int i=0; i<numValues; ++i) {
			if(options.getValue(i).equals(val)) return options.getWeight(i);
		}
		return 0;
	}
	
	/**
	 * Calculate MFDs
	 * 
	 * @param paramIndex
	 * @param weight
	 */
	private void findBranches(int paramIndex, double weight) {
		ParamOptions options = logicTreeParamValues.get(paramIndex);
		String paramName = logicTreeParamNames.get(paramIndex);
		int numValues = options.getNumValues();
		for(int i=0; i<numValues; ++i) {
			double newWt;
			if(ucerf2.getAdjustableParameterList().containsParameter(paramName)) {
				ucerf2.getParameter(paramName).setValue(options.getValue(i));	
				newWt = weight * options.getWeight(i);
				if(paramName.equalsIgnoreCase(UCERF2.REL_A_PRIORI_WT_PARAM_NAME)) {
					ParameterAPI param = ucerf2.getParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME);
					if(((Double)param.getValue()).doubleValue()==1e10) {
						ucerf2.getParameter(UCERF2.MIN_A_FAULT_RATE_1_PARAM_NAME).setValue(new Double(0.0));
						ucerf2.getParameter(UCERF2.MIN_A_FAULT_RATE_2_PARAM_NAME).setValue(new Double(0.0));	
					} else {
						ucerf2.getParameter(UCERF2.MIN_A_FAULT_RATE_1_PARAM_NAME).setValue(UCERF2.MIN_A_FAULT_RATE_1_DEFAULT);
						ucerf2.getParameter(UCERF2.MIN_A_FAULT_RATE_2_PARAM_NAME).setValue(UCERF2.MIN_A_FAULT_RATE_2_DEFAULT);	
					}
				}
				// change BPT to Poisson for Unsegmented case
				if(paramName.equalsIgnoreCase(UCERF2.PROB_MODEL_PARAM_NAME) &&
						ucerf2.getParameter(UCERF2.RUP_MODEL_TYPE_NAME).getValue().equals(UCERF2.UNSEGMENTED_A_FAULT_MODEL) &&
						options.getValue(i).equals(UCERF2.PROB_MODEL_BPT)	) {
					ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_POISSON);
				}
			} else {
				if(i==0) newWt=weight;
				else return;
			}
			if(paramIndex==lastParamIndex) { // if it is last paramter in list, save the MFDs
				logicTreeParamList.add((ParameterList)ucerf2.getAdjustableParameterList().clone());
				weights.add(newWt);
			} else { // recursion 
				findBranches(paramIndex+1, newWt);
			}
		}
	}
	
	
	/**
	 * Return the name for this class
	 *
	 * @return : return the name for this class
	 */
	public String getName(){
		return NAME;
	}


	/**
	 * get the number of Eqk Rup Forecasts in this list
	 * @return : number of eqk rup forecasts in this list
	 */
	public int getNumERFs() {
		return this.weights.size();
	}


	/**
	 * Get the ERF in the list with the specified index. 
	 * It returns the updated forecast
	 * Index can range from 0 to getNumERFs-1
	 * 
	 * 
	 * @param index : index of Eqk rup forecast to return
	 * @return
	 */
	public EqkRupForecastAPI getERF(int index) {
		Iterator it = logicTreeParamList.get(index).getParametersIterator();
		while(it.hasNext()) {
			Parameter param = (Parameter)it.next();
			ucerf2.getParameter(param.getName()).setValue(param.getValue());
		}
		ucerf2.setParameter(UCERF2.BACK_SEIS_NAME, backSeisParam.getValue());
		if(this.adjustableParams.containsParameter(backSeisRupParam)) ucerf2.setParameter(UCERF2.BACK_SEIS_RUP_NAME, this.backSeisRupParam.getValue());
		ucerf2.setParameter(UCERF2.FLOATER_TYPE_PARAM_NAME, this.floaterTypeParam.getValue());
		ucerf2.getTimeSpan().setDuration(this.timeSpan.getDuration());
		ucerf2.updateForecast();
		return ucerf2;
	}
	
	/**
	 * Get the ParameterList for ERF at the specified index
	 * 
	 * @param index
	 * @return
	 */
	public ParameterList getParameterList(int index) {
		return logicTreeParamList.get(index);
	}

	/**
	 * get the weight of the ERF at the specified index
	 * @param index : index of ERF
	 * @return : relative weight of ERF
	 */
	public double getERF_RelativeWeight(int index) {
		return this.weights.get(index);
	}

	/**
	 * Return the Arraylist containing the Double values with
	 * relative weights for each ERF
	 * @return : ArrayList of Double values
	 */
	public ArrayList<Double> getRelativeWeightsList() {
		return weights;
	}
	
	
	public static void main(String[] args) {
		UCERF2_TimeIndependentEpistemicList ucerf2EpistemicList = new UCERF2_TimeIndependentEpistemicList();
		int numERFs = ucerf2EpistemicList.getNumERFs();
		System.out.println("Num Branches="+numERFs);
		for(int i=0; i<numERFs; ++i) {
			System.out.println("Weight of Branch "+i+"="+ucerf2EpistemicList.getERF_RelativeWeight(i));
			System.out.println("Parameters of Branch "+i+":");
			System.out.println(ucerf2EpistemicList.getParameterList(i).getParameterListMetadataString("\n"));
			
		}
		
	}

}


