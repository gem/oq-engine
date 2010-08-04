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

import java.awt.Color;
import java.awt.Font;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.ListIterator;

import javax.swing.BorderFactory;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.gui.infoTools.AttenuationRelationshipsInstance;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.event.ScalarIMRChangeEvent;
import org.opensha.sha.imr.event.ScalarIMRChangeListener;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <p>Title: IMR Gui Bean</p>
 * <p>Description: This is the IMR Gui Bean. This bean can be instantiated to be
 * added to the applets.
 * It displays the following :
 *  1. a pick list to choose a IMR.
 *  2. a pick list to choose Gaussian truncation type
 *  3. a pick list to choose std dev type
 *  </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class IMR_GuiBean extends ParameterListEditor
implements ParameterChangeListener,
ParameterChangeWarningListener, ParameterChangeFailListener {

	private ArrayList<ScalarIMRChangeListener> listeners = new ArrayList<ScalarIMRChangeListener>();

	// IMR GUI Editor & Parameter names
	public final static String IMR_PARAM_NAME = "IMR";
	public final static String IMR_EDITOR_TITLE =  "Set IMR";

	//saves the IMR objects, to the parameters related to an IMR.
	private ArrayList<ScalarIntensityMeasureRelationshipAPI> supportedAttenRels ;
	// this flag is needed else messages are shown twice on focus lost
	private boolean inParameterChangeWarning = false;

	//instance of the class to create the objects of the AttenuationRelationships dynamically.
	private AttenuationRelationshipsInstance attenRelInstances;

	//instance of the application using IMR_GuiBean
	private IMR_GuiBeanAPI application;
	private boolean isFirstTimeLaunched = true;
	
	private ScalarIntensityMeasureRelationshipAPI currentAttenRel = null;

	/**
	 * class default constructor
	 * @param classNames
	 */
	public IMR_GuiBean(IMR_GuiBeanAPI api) {
		this(api, AttenuationRelationshipsInstance.getDefaultIMRClassNames());
	}

	/**
	 * class constructor where IMRs can be specified
	 * @param api
	 * @param classNames
	 */
	public IMR_GuiBean(IMR_GuiBeanAPI api, ArrayList<String> classNames) {
		init(api, classNames);
		parameterList = new ParameterList();
		init_imrParamListAndEditor();
	}


	/**
	 * class default constructor
	 * @param classNames
	 */
	public IMR_GuiBean(IMR_GuiBeanAPI api,String currentIMT,
			String retroIMT,double currentPeriod,double retroPeriod) {
		init(api, AttenuationRelationshipsInstance.getDefaultIMRClassNames());
		setIMRParamListAndEditor(currentIMT ,retroIMT, currentPeriod,retroPeriod);
	}
	
	private void init(IMR_GuiBeanAPI api, ArrayList<String> classNames) {
		application  = api;
		attenRelInstances = new AttenuationRelationshipsInstance(classNames);
		supportedAttenRels = attenRelInstances.createIMRClassInstance(this);
		for (ScalarIntensityMeasureRelationshipAPI imr : supportedAttenRels) {
			imr.setParamDefaults();
		}
	}


	public void setIMRParamListAndEditor(String currentIMT,String retroIMT,double currentPeriod,double retroPeriod){
		String selectedAttenRel = null;
		if(parameterList !=null)
			selectedAttenRel = (String)parameterList.getParameter(IMR_PARAM_NAME).getValue();
		ArrayList attenRels  = getAttenRelsSupportedForSelectedIM(currentIMT,retroIMT,currentPeriod,retroPeriod);
		// if we are entering this function for the first time, then make imr objects

		parameterList = new ParameterList();
		Iterator it= attenRels.iterator();

		ArrayList supportedIMRNames = new ArrayList();
		while(it.hasNext()){
			// make the IMR objects as needed to get the site params later
			ScalarIntensityMeasureRelationshipAPI imr = (ScalarIntensityMeasureRelationshipAPI )it.next();
			if(isFirstTimeLaunched)
				imr.setParamDefaults();
			supportedIMRNames.add(imr.getName());
			Iterator it1 = imr.getSiteParamsIterator();
			// add change fail listener to the site parameters for this IMR
			while(it1.hasNext()) {
				ParameterAPI param = (ParameterAPI)it1.next();
				param.addParameterChangeFailListener(this);
			}
		}

		int index = -1;
		if(selectedAttenRel !=null)
			//    checking if the imrNames contains the previously selected AttenRel Name
			index =supportedIMRNames.indexOf(selectedAttenRel);

		//AttenRel Name Param
		StringParameter selectIMR = null;
		if(index !=-1) //if the previuosly selected AttenRel is contained in the list
			// make the IMR selection paramter
			selectIMR = new StringParameter(IMR_PARAM_NAME,supportedIMRNames,(String)supportedIMRNames.get(index));
		else //if previuosly selected AttenRel is not pesent in it.
			selectIMR = new StringParameter(IMR_PARAM_NAME,
					supportedIMRNames,(String)supportedIMRNames.get(0));

		// listen to IMR paramter to change site params when it changes
		selectIMR.addParameterChangeListener(this);
		parameterList.addParameter(selectIMR);


		// initalize imr
		ScalarIntensityMeasureRelationshipAPI imr = (ScalarIntensityMeasureRelationshipAPI)attenRels.get(0);

		// find & set the selectedIMR
		imr = this.getSelectedIMR_Instance();

		// getting the iterator of the Other Parameters for IMR
		/**
		 * Instead of getting hard-coding for getting the selected Params Ned added
		 * a method to get the OtherParams for the selected IMR, Otherwise earlier we
		 * were getting the 3 params associated with IMR's by there name. But after
		 * adding the method to get the otherParams, it can also handle params that
		 * are customary to the selected IMR. So this automically adds the parameters
		 * associated with the IMR, which are : SIGMA_TRUNC_TYPE_NAME, SIGMA_TRUNC_LEVEL_NAME,
		 * STD_DEV_TYPE_NAME and any other param assoctade with the IMR.
		 */
		ListIterator lt = imr.getOtherParamsIterator();
		while(lt.hasNext()){
			ParameterAPI tempParam=(ParameterAPI)lt.next();
			//adding the parameter to the parameterList.
			tempParam.addParameterChangeListener(this);
			parameterList.addParameter(tempParam);
			tempParam.addParameterChangeListener(this);
		}

		this.editorPanel.removeAll();
		addParameters();
		setTitle(IMR_EDITOR_TITLE);

		// get the panel for increasing the font and border
		// this is hard coding for increasing the IMR font
		// the colors used here are from ParameterEditor
		JPanel panel = this.getParameterEditor(this.IMR_PARAM_NAME).getOuterPanel();
		TitledBorder titledBorder1 = new TitledBorder(BorderFactory.createLineBorder(new Color( 80, 80, 140 ),3),"");
		titledBorder1.setTitleColor(new Color( 80, 80, 140 ));
		Font DEFAULT_LABEL_FONT = new Font( "SansSerif", Font.BOLD, 13 );
		titledBorder1.setTitleFont(DEFAULT_LABEL_FONT);
		titledBorder1.setTitle(IMR_PARAM_NAME);
		Border border1 = BorderFactory.createCompoundBorder(titledBorder1,BorderFactory.createEmptyBorder(0,0,3,0));
		panel.setBorder(border1);

		// set the trunc level based on trunc type
		String value = (String)parameterList.getParameter(SigmaTruncTypeParam.NAME).getValue();
		toggleSigmaLevelBasedOnTypeValue(value);
		isFirstTimeLaunched = false;

	}

	/**
	 * Returns the ArrayList of the AttenuationRelation being supported by the selected IM
	 * @return
	 */
	private ArrayList getAttenRelsSupportedForSelectedIM(String currentIMT,String retroIMT,double currentPeriod,double retroPeriod){

		ArrayList attenRelsSupportedForIM = new ArrayList();
		int numSupportedAttenRels = supportedAttenRels.size();
		for(int i=0;i < numSupportedAttenRels;++i){
			AttenuationRelationship attenRel = (AttenuationRelationship)supportedAttenRels.get(i);
			if(isIntensityMeasureSupported(attenRel,currentIMT,currentPeriod) && 
					isIntensityMeasureSupported(attenRel,retroIMT,retroPeriod) )
				attenRelsSupportedForIM.add(attenRel);
		}
		return attenRelsSupportedForIM;
	}
	
	  /**
	   * Checks if the Parameter is a supported intensity-Measure (checking
	   * only the name and Period).
	   * @param intensityMeasure Name of the intensity Measure parameter
	   * @param period Period Param Name is intensity measure is SA
	   * @return
	   */
	  public boolean isIntensityMeasureSupported(AttenuationRelationship attenRel,String intensityMeasure, double period){
		  if(attenRel.isIntensityMeasureSupported(intensityMeasure)){
			ParameterAPI imParam = attenRel.getSupportedIntensityMeasuresList().getParameter(intensityMeasure);
			if(imParam.getName().equals(SA_Param.NAME)){
		        if (attenRel.getParameter(PeriodParam.NAME).isAllowed(period)) {
		          return true;
		        }
		        else {
		          return false;
		        }
			}
			return true;
		  }
		return false;
	  }
	  


	/**
	 *  Create a list of all the IMRs
	 */
	private void init_imrParamListAndEditor() {


		// if we are entering this function for the first time, then make imr objects
		if(!parameterList.containsParameter(IMR_PARAM_NAME)) {
			parameterList = new ParameterList();
			Iterator it= supportedAttenRels.iterator();

			ArrayList supportedIMRNames = new ArrayList();
			while(it.hasNext()){
				// make the IMR objects as needed to get the site params later
				ScalarIntensityMeasureRelationshipAPI imr = (ScalarIntensityMeasureRelationshipAPI )it.next();
				imr.setParamDefaults();
				supportedIMRNames.add(imr.getName());
				Iterator it1 = imr.getSiteParamsIterator();
				// add change fail listener to the site parameters for this IMR
				while(it1.hasNext()) {
					ParameterAPI param = (ParameterAPI)it1.next();
					param.addParameterChangeFailListener(this);
				}
			}

			// make the IMR selection paramter
			StringParameter selectIMR = new StringParameter(IMR_PARAM_NAME,
					supportedIMRNames,(String)supportedIMRNames.get(0));
			// listen to IMR paramter to change site params when it changes
			selectIMR.addParameterChangeListener(this);
			parameterList.addParameter(selectIMR);
		}

		// remove all the parameters except the IMR parameter
		ListIterator it = parameterList.getParameterNamesIterator();
		while(it.hasNext()) {
			String paramName = (String)it.next();
			if(!paramName.equalsIgnoreCase(IMR_PARAM_NAME))
				parameterList.removeParameter(paramName);
		}


		// now find the selceted IMR and add the parameters related to it

		// initalize imr
		ScalarIntensityMeasureRelationshipAPI imr = (ScalarIntensityMeasureRelationshipAPI)supportedAttenRels.get(0);

		// find & set the selectedIMR
		imr = this.getSelectedIMR_Instance();

		// getting the iterator of the Other Parameters for IMR
		/**
		 * Instead of getting hard-coding for getting the selected Params Ned added
		 * a method to get the OtherParams for the selected IMR, Otherwise earlier we
		 * were getting the 3 params associated with IMR's by there name. But after
		 * adding the method to get the otherParams, it can also handle params that
		 * are customary to the selected IMR. So this automically adds the parameters
		 * associated with the IMR, which are : SIGMA_TRUNC_TYPE_NAME, SIGMA_TRUNC_LEVEL_NAME,
		 * STD_DEV_TYPE_NAME and any other param assoctade with the IMR.
		 */
		ListIterator lt = imr.getOtherParamsIterator();
		while(lt.hasNext()){
			ParameterAPI tempParam=(ParameterAPI)lt.next();
			//adding the parameter to the parameterList.
			tempParam.addParameterChangeListener(this);
			parameterList.addParameter(tempParam);
			tempParam.addParameterChangeListener(this);
		}

		this.editorPanel.removeAll();
		addParameters();
		setTitle(IMR_EDITOR_TITLE);

		// get the panel for increasing the font and border
		// this is hard coding for increasing the IMR font
		// the colors used here are from ParameterEditor
		JPanel panel = this.getParameterEditor(this.IMR_PARAM_NAME).getOuterPanel();
		TitledBorder titledBorder1 = new TitledBorder(BorderFactory.createLineBorder(new Color( 80, 80, 140 ),3),"");
		titledBorder1.setTitleColor(new Color( 80, 80, 140 ));
		Font DEFAULT_LABEL_FONT = new Font( "SansSerif", Font.BOLD, 13 );
		titledBorder1.setTitleFont(DEFAULT_LABEL_FONT);
		titledBorder1.setTitle(IMR_PARAM_NAME);
		Border border1 = BorderFactory.createCompoundBorder(titledBorder1,BorderFactory.createEmptyBorder(0,0,3,0));
		panel.setBorder(border1);

		// set the trunc level based on trunc type
		String value = (String)parameterList.getParameter(SigmaTruncTypeParam.NAME).getValue();
		toggleSigmaLevelBasedOnTypeValue(value);
		
		this.fireAttenuationRelationshipChangedEvent(currentAttenRel, imr);
		currentAttenRel = imr;
	}





	/**
	 *  This is the main function of this interface. Any time a control
	 *  paramater or independent paramater is changed by the user in a GUI this
	 *  function is called, and a paramater change event is passed in. This
	 *  function then determines what to do with the information ie. show some
	 *  paramaters, set some as invisible, basically control the paramater
	 *  lists.
	 *
	 * @param  event
	 */
	public void parameterChange( ParameterChangeEvent event ) {

		String S = C + ": parameterChange(): ";
		if ( D ) System.out.println( "\n" + S + "starting: " );

		String name1 = event.getParameterName();

		// if Truncation type changes
		if( name1.equals(SigmaTruncTypeParam.NAME) ){  // special case hardcoded. Not the best way to do it, but need framework to handle it.
			String value = event.getNewValue().toString();
			toggleSigmaLevelBasedOnTypeValue(value);
		}
		// if IMR parameter changes, then get the Gaussian truncation, etc from this selected IMR
		//if(name1.equalsIgnoreCase(this.IMR_PARAM_NAME)) {
		init_imrParamListAndEditor();
		this.updateUI();
		//update the IM for the selected AttenutionRelationship, so similar can be shown by the application
		application.updateIM();
		//update the Site Params for the selected AttenutionRelationship, so the similar can be shown by the application and shown by 
		//siteGuiBean
		application.updateSiteParams();
		//}


	}


	/**
	 * sigma level is visible or not
	 * @param value
	 */
	protected void toggleSigmaLevelBasedOnTypeValue(String value){

		if( value.equalsIgnoreCase(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE) ) {
			if(D) System.out.println("Value = " + value + ", need to set value param off.");
			setParameterVisible( SigmaTruncLevelParam.NAME, false );
		}
		else{
			if(D) System.out.println("Value = " + value + ", need to set value param on.");
			setParameterVisible( SigmaTruncLevelParam.NAME, true );
		}

	}


	/**
	 *  Function that must be implemented by all Listeners for
	 *  ParameterChangeWarnEvents.
	 *
	 * @param  event  The Event which triggered this function call
	 */
	public void parameterChangeWarning( ParameterChangeWarningEvent e ){

		String S = C + " : parameterChangeWarning(): ";
		if(D) System.out.println(S + "Starting");
		WarningParameterAPI param = e.getWarningParameter();

		//check if this parameter exists in the site param list of this IMR
		// if it does not then set its value using ignore warning
		Iterator it = this.getSelectedIMR_Instance().getSiteParamsIterator();
		boolean found = false;
		while(it.hasNext() && !found)
			if(param.getName().equalsIgnoreCase(((ParameterAPI)it.next()).getName()))
				found = true;
		if(!found) {
			param.setValueIgnoreWarning(e.getNewValue());
			return;
		}


		// if it is already processing a warning, then return
		if(inParameterChangeWarning) return;
		inParameterChangeWarning = true;

		StringBuffer b = new StringBuffer();

		try{
			Double min = (Double)param.getWarningMin();
			Double max = (Double)param.getWarningMax();

			String name = param.getName();

			b.append( "You have exceeded the recommended range for ");
			b.append( name );
			b.append( ": (" );
			b.append( min.toString() );

			b.append( " to " );
			b.append( max.toString() );
			b.append( ")\n" );
			b.append( "Click Yes to accept the new value: " );
			b.append( e.getNewValue().toString() );
		}
		catch( Exception ee){

			String name = param.getName();

			b.append( "You have exceeded the recommended range for: \n");
			b.append( name + '\n' );
			b.append( "Click Yes to accept the new value: " );
			b.append( e.getNewValue().toString() );
			b.append( name );
		}
		if(D) System.out.println(S + b.toString());

		int result = 0;

		if(D) System.out.println(S + "Showing Dialog");

		result = JOptionPane.showConfirmDialog( this, b.toString(),
				"Exceeded Recommended Values", JOptionPane.YES_NO_OPTION, JOptionPane.QUESTION_MESSAGE);

		if(D) System.out.println(S + "You choose" + result);

		switch (result) {
		case JOptionPane.YES_OPTION:
			if(D) System.out.println(S + "You choose yes, changing value to " + e.getNewValue().toString() );
			param.setValueIgnoreWarning( e.getNewValue());
			break;
		case JOptionPane.NO_OPTION:
			if(D) System.out.println(S + "You choose no, keeping value = " + e.getOldValue().toString() );
			param.setValueIgnoreWarning( e.getOldValue() );
			break;
		default:
			param.setValueIgnoreWarning( e.getOldValue() );
		if(D) System.out.println(S + "Not sure what you choose, not changing value.");
		break;
		}
		inParameterChangeWarning = false;
		if(D) System.out.println(S + "Ending");
	}

	/**
	 * Whether to show the warning messages or not
	 * In some cases, we may not want to show warning messages.
	 * Presently it is being used in HazardCurveApplet
	 * @param show
	 */
	public void showWarningMessages(boolean show){
		inParameterChangeWarning = !show;
	}

	/**
	 * Shown when a Constraint error is thrown on a ParameterEditor
	 *
	 * @param  e  Description of the Parameter
	 */
	public void parameterChangeFailed( ParameterChangeFailEvent e ) {

		String S = C + " : parameterChangeWarning(): ";
		if(D) System.out.println(S + "Starting");


		StringBuffer b = new StringBuffer();

		ParameterAPI param = ( ParameterAPI ) e.getSource();


		ParameterConstraintAPI constraint = param.getConstraint();
		String oldValueStr = e.getOldValue().toString();
		String badValueStr = e.getBadValue().toString();
		String name = param.getName();

		// only show messages for visible site parameters
		ScalarIntensityMeasureRelationshipAPI imr = getSelectedIMR_Instance();
		ListIterator it = imr.getSiteParamsIterator();
		boolean found = false;
		// see whether this parameter exists in site param list for this IMR
		while(it.hasNext() && !found)
			if(((ParameterAPI)it.next()).getName().equalsIgnoreCase(name))
				found = true;

		// if this parameter for which failure was issued does not exist in
		// site parameter list, then do not show the message box
		if(!found)  return;



		b.append( "The value ");
		b.append( badValueStr );
		b.append( " is not permitted for '");
		b.append( name );
		b.append( "'.\n" );
		b.append( "Resetting to ");
		b.append( oldValueStr );
		b.append( ". The constraints are: \n");
		b.append( constraint.toString() );

		JOptionPane.showMessageDialog(
				this, b.toString(),
				"Cannot Change Value", JOptionPane.INFORMATION_MESSAGE
		);

		if(D) System.out.println(S + "Ending");

	}

	/**
	 * this method will return the name of selected IMR
	 * @return : Selected IMR name
	 */
	public String getSelectedIMR_Name() {
		return parameterList.getValue(IMR_PARAM_NAME).toString();
	}

	/**
	 * This method will return the instance of selected IMR
	 * @return : Selected IMR instance
	 */
	public ScalarIntensityMeasureRelationshipAPI getSelectedIMR_Instance() {
		String selectedIMR = getSelectedIMR_Name();
		return getIMR_Instance(selectedIMR);
	}
	
//	/**
//	 * Setds the selected IMR.
//	 */
//	public void setSelectedIMR_Instance(
//			) {
//		String selectedIMR = getSelectedIMR_Name();
//		return getIMR_Instance(selectedIMR);
//	}

	/**
	 * This method will return the instance of selected IMR
	 * @return : Selected IMR instance
	 */
	public ScalarIntensityMeasureRelationshipAPI getIMR_Instance(String name) {
		ScalarIntensityMeasureRelationshipAPI imr = null;
		int size = supportedAttenRels.size();
		for(int i=0; i<size ; ++i) {
			imr = (ScalarIntensityMeasureRelationshipAPI)supportedAttenRels.get(i);
			if(imr.getName().equalsIgnoreCase(name))
				break;
		}
		return imr;
	}

	/**
	 * return a list of imr instances shown in this gui bean
	 *
	 * @return
	 */
	public ArrayList<ScalarIntensityMeasureRelationshipAPI> getSupportedIMRs() {
		return supportedAttenRels;
	}
	
	public void addAttenuationRelationshipChangeListener(ScalarIMRChangeListener listener) {
		listeners.add(listener);
	}
	
	public void removeAttenuationRelationshipChangeListener(ScalarIMRChangeListener listener) {
		listeners.remove(listener);
	}
	
	public void fireAttenuationRelationshipChangedEvent(ScalarIntensityMeasureRelationshipAPI oldAttenRel,
			ScalarIntensityMeasureRelationshipAPI newAttenRel) {
		if (listeners.size() == 0)
			return;
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> oldMap =
			new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		oldMap.put(TectonicRegionType.ACTIVE_SHALLOW, oldAttenRel);
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> newMap =
			new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		oldMap.put(TectonicRegionType.ACTIVE_SHALLOW, newAttenRel);
		ScalarIMRChangeEvent event = new ScalarIMRChangeEvent(this, oldMap, newMap);
		
		for (ScalarIMRChangeListener listener : listeners) {
			listener.imrChange(event);
		}
	}

}
