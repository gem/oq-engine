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

package org.opensha.sha.gui.beans;

import java.util.ArrayList;

import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.imr.IntensityMeasureRelationship;

/**
 * <p>Title: IMLorProbSelectorGuiBean</p>
 * <p>Description: This class provides with the ListEditor for the user to make the
 * selection for the Map Type user wants to generate</p>
 * @author: Nitin Gupta & Vipin Gupta
 * @created March 12,2003
 * @version 1.0
 */

public class IMLorProbSelectorGuiBean extends ParameterListEditor implements
ParameterChangeListener{


	//definition of the class final static variables
	public final static String IML_AT_PROB="IML@Prob";
	public final static String PROB_AT_IML="Prob@IML";
	public final static String PROBABILITY="Probability";
	public final static String MAP_TYPE = "Map Type";
	private final static String IML="IML";
	private final static String MAP_INFO="Set What To Plot";
	private final static Double MIN_PROB = IntensityMeasureRelationship.EXCEED_PROB_MIN;
	private final static Double MAX_PROB = IntensityMeasureRelationship.EXCEED_PROB_MAX;
	private final static Double DEFAULT_PROB= new Double(.5);
	private final static Double DEFAULT_IML = new Double(.1);

	private StringParameter imlProbParam;

	//double parameters for inutting the values for the iml or prob.
	private DoubleParameter probParam = new DoubleParameter(PROBABILITY,MIN_PROB,MAX_PROB,DEFAULT_PROB);

	//we have to create a double parameter with constraints if we want to reflect the constarints
	//as the tooltip text in the GUI.
	private DoubleParameter imlParam = new DoubleParameter(IML,Double.MIN_VALUE,Double.MAX_VALUE,DEFAULT_IML);

	/**
	 * class constructor
	 */
	public IMLorProbSelectorGuiBean() {


		//combo Box that provides the user to choose either the IML@prob or vis-a-versa
		ArrayList imlProbVector=new ArrayList();

		imlProbVector.add(IML_AT_PROB);
		imlProbVector.add(PROB_AT_IML);
		imlProbParam = new StringParameter(MAP_TYPE,imlProbVector,imlProbVector.get(0).toString());
		imlProbParam.addParameterChangeListener(this);
		parameterList= new ParameterList();
		parameterList.addParameter(imlProbParam);
		parameterList.addParameter(probParam);
		parameterList.addParameter(imlParam);
		addParameters();
		this.setTitle(MAP_INFO);
		setParams(imlProbParam.getValue().toString());
	}

	/**
	 * this function selects either the IML or Prob. to be entered by the user.
	 * So, we update the site object as well.
	 *
	 * @param e
	 */
	public void parameterChange(ParameterChangeEvent e) {
		String name = e.getParameterName();
		// if user changes the map type desired
		if(name.equalsIgnoreCase(this.MAP_TYPE)) {
			// make the IML@Prob visible or Prob@IML as visible
			setParams(parameterList.getParameter(MAP_TYPE).getValue().toString());
		}
	}

	/**
	 * Make the IML@Prob or Prob@IML as visible, invisible based on map type selected
	 * @param mapType
	 */
	private void setParams(String mapType) {
		if(mapType.equalsIgnoreCase(IML_AT_PROB)) { // if IML@prob is selected
			this.setParameterVisible(IML,false);
			this.setParameterVisible(PROBABILITY, true);
		} else { // if Prob@IML is selected
			this.setParameterVisible(PROBABILITY,false);
			this.setParameterVisible(IML, true);
		}
	}

	/**
	 * Sets the constraint and Default value of the IML Param based on the
	 * selected IMT.
	 * @param imt
	 */
	public void setIMLConstraintBasedOnSelectedIMT(String imt){
		double minVal = IMT_Info.getMinIMT_Val(imt);
		double maxVal = IMT_Info.getMaxIMT_Val(imt);
		double defaultVal = IMT_Info.getDefaultIMT_VAL(imt);
		DoubleConstraint constraint = new DoubleConstraint(minVal,maxVal);
		imlParam.setConstraint(constraint);
		imlParam.setValue(new Double(defaultVal));
		refreshParamEditor();
	}

	/**
	 *
	 * @return the double value for the iml or prob, depending on the MapType
	 * selected by the user.
	 */
	public double getIML_Prob(){
		if(parameterList.getParameter(MAP_TYPE).getValue().toString().equalsIgnoreCase(IML_AT_PROB))
			return ((Double)probParam.getValue()).doubleValue();
		else return ((Double)imlParam.getValue()).doubleValue();
	}
	
	public boolean isProbAt_IML() {
		return imlProbParam.getValue().equals(PROB_AT_IML);
	}

	/**
	 * returns whether IML@Prob is selcted or Prob@IML
	 * @return
	 */
	public String getSelectedOption() {
		return imlProbParam.getValue().toString();
	}
}
