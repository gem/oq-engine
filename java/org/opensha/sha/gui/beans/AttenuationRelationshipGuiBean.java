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
import java.awt.Container;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.ListIterator;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JDialog;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.DoubleDiscreteParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.editor.DoubleParameterEditor;
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
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <p>Title: AttenuationRelationshipGuiBean</p>
 * <p>Description: This class provides the user with the flexiblity of choosing
 * between the SingleAttenuationRelationship GUI or MultipleAttenuationRelationship
 * GUI. If the person selects the multiple AttenRel the it gives him the flexiblity
 * of inputting the wts to each selected AttenRel. But in the case of the Single
 * AttenRel it gives it the weight of 1.0.
 * This class gives the user the option of selecting attenuationrelationships
 * and their supported parameters. This enables the user to select from only
 * those Attenuationrelationship which support the selected IMT and its parameters.</p>
 * @author : Nitin Gupta and Vipin Gupta
 * @created : 03 May,2004
 * @version 1.0
 */

public class AttenuationRelationshipGuiBean extends JPanel  implements
ActionListener,ItemListener,ParameterChangeListener,
ParameterChangeWarningListener, ParameterChangeFailListener{

	private ArrayList<ScalarIMRChangeListener> listeners = new ArrayList<ScalarIMRChangeListener>();

	private static final String C = "MultipleIMR_GuiBean";
	private static final boolean D = false;

	//list of the supported AttenuationRelationships
	ArrayList<ScalarIntensityMeasureRelationshipAPI> attenRelsSupported;

	//number of the supported Attenuation Relatoinships
	int numSupportedAttenRels ;

	//List of the AttenuationRelations supported by this selected IM param
	ArrayList attenRelsSupportedForIM;

	//list of AttenuationRelationships not supported by the selected IM param


	//Gui elements
	private JScrollPane jScrollPane1 = new JScrollPane();


	//instance of the class to create the objects of the AttenuationRelationships dynamically.
	AttenuationRelationshipsInstance attenRelInstances = new AttenuationRelationshipsInstance();


	//keeps the indexing for the Attenuation Relationship for which any event is generated.
	private int indexOfAttenRel = 0;

	//keeps the index of the last button pressed, so as to keep track of parameter list editor shown
	//So helps in corresponding to shown parameterList editor with the AttenuationRelation model.
	private int lastAttenRelButtonIndex;

	//name of the attenuationrelationship weights parameter
	public static final String wtsParamName = "Wgt-";
	public static final String attenRelParamsButtonName = "Set IMR Params";
	public static final String attenRelNonIdenticalParams = "Set IMT non-identical params";
	public static final String attenRelIdenticalParamsFrameTitle = "IMR's identical params";
	public static final String attenRelIdenticalParams = "Set IMR identical params";

	//Dynamic Gui elements array to generate the AttenRel components on the fly.
	private JCheckBox[] attenRelCheckBox;
	private JButton[] paramButtons;

	//AttenuationRelationship parameters and list declaration
	private DoubleParameter[] wtsParameter;
	private DoubleParameterEditor[] wtsParameterEditor;
	private ParameterList paramList[];
	private ParameterListEditor editor[];
	private JDialog imrParamsFrame[];

	/*private ParameterList otherParams= new ParameterList();
  private ParameterListEditor otherParamsEditor;
  private JDialog otherIMR_paramsFrame;
  private JButton setAllParamButtons = new JButton("Set All Params");*/
	// this flag is needed else messages are shown twice on focus lost
	private boolean inParameterChangeWarning = false;




	//IMT Parameter and List declaration
	private ParameterList imtParamList;
	private ParameterListEditor imtEditorParamListEditor;
	// IMT GUI Editor & Parameter names
	public final static String IMT_PARAM_NAME =  "IMT";
	// IMT Panel title
	public final static String IMT_EDITOR_TITLE =  "Set IMT";

	//stores the IMT Params for the choosen IMR
	private ArrayList<ParameterAPI> imtParam;


	private JPanel imrPanel = new JPanel();
	private JPanel imrimtPanel = new JPanel();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private GridBagLayout gridBagLayout2 = new GridBagLayout();
	private GridBagLayout gridBagLayout3 = new GridBagLayout();


	//static string declaration
	private static String MULTIPLE_ATTEN_REL = "Show Multiple IMRs";
	private static String SINGLE_ATTEN_REL = "Show Single IMR";
	// IMR GUI Editor & Parameter names
	public final static String IMR_PARAM_NAME = "IMR";
	public final static String IMR_EDITOR_TITLE =  "Set IMR";

	//toggle button between the multiple attenuation and single Attenuation relationship GUI.
	private JButton toggleButton = new JButton(SINGLE_ATTEN_REL);

	//Flag to keep check which if single multiple attenRel is being used.
	private boolean singleAttenRelSelected =true;

	//Flag to keep track if we are setting the values of the IMR param for the first time
	private boolean firstTimeIMR_ParamInit = true;

	//ParameterList and Editor declaration for the single AttenRels selection
	ParameterList singleAttenRelParamList =null;
	ParameterListEditor singleAttenRelParamListEditor=null;

	//saves the name of the previuosly selected AttenRel
	String selectedAttenRelName=null;




	//Instance of the application using this Gui Bean.
	AttenuationRelationshipSiteParamsRegionAPI application;


	/**
	 *
	 * @param api : Instance of the application using this GUI bean.
	 */
	public AttenuationRelationshipGuiBean(AttenuationRelationshipSiteParamsRegionAPI api)
	{
		application = api;
		//initializing all the array of the GUI elements to be the number of the supported AtrtenuationRelationships.
		attenRelsSupported = attenRelInstances.createIMRClassInstance(this);

		numSupportedAttenRels = attenRelsSupported.size();

		//setting the default parameters value for all the attenuationRelationship object.
		for(int i=0;i<numSupportedAttenRels;++i)
			((ScalarIntensityMeasureRelationshipAPI)attenRelsSupported.get(i)).setParamDefaults();

		//creates the IMT paameterList editor for the supported IMRs
		init_imtParamListAndEditor();
		//gets the list of the supported IMR's based on the selected IM
		getAttenRelsSupportedForSelectedIM();
		try {
			jbInit();
		}
		catch(Exception ex) {
			ex.printStackTrace();
		}
	}

	/**
	 * function to create the Gui elements
	 * @throws Exception
	 */
	void jbInit() throws Exception {
		this.setLayout(gridBagLayout1);
		imrimtPanel.setLayout(gridBagLayout2);
		imrPanel.setLayout(gridBagLayout3);
		this.setMinimumSize(new Dimension(0, 0));
		this.setPreferredSize(new Dimension(430, 539));
		imrimtPanel.setMinimumSize(new Dimension(0, 0));
		toggleButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				toggleButton_actionPerformed(e);
			}
		});

		this.add(jScrollPane1,  new GridBagConstraints(0, 0, 0, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 3, 5, 5), 377, 469));
		jScrollPane1.getViewport().add(imrimtPanel, null);
		//adding the IMT parameter list editor as the first element in the AttenRel Selection panel
		imrimtPanel.add(imtEditorParamListEditor,new GridBagConstraints(0, 0, 3, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 3, 5, 5), 0, 0));
		//adding the toogle button to the GUI, lets the user switch between the single and multiple AttenRels
		imrimtPanel.add(toggleButton,new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.CENTER, new Insets(7, 20, 5, 5), 10, 5));
		//adding the panel to add the AttenRels and their parameter.
		imrimtPanel.add(imrPanel,new GridBagConstraints(0, 2, 3, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));

		//creates the GUI elements for the single AttenuationRelationship selection
		toggleBetweenSingleAndMultipleAttenRel();


		/*imrPanel.add(setAllParamButtons,new GridBagConstraints(0, numSupportedAttenRels+1, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.EAST, new Insets(7, 200, 5, 5), 15, 5));*/


		/*setAllParamButtons.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        setAllParamButtons_actionPerformed(e);
      }
    });*/
	}


	/**
	 * Creates the GUI elements for multiple AttenuationRelationship
	 */
	private void initMultipleAttenRelParamListAndEditor() throws Exception{
		attenRelCheckBox = new JCheckBox[numSupportedAttenRels];
		paramButtons = new JButton[numSupportedAttenRels];
		wtsParameter = new DoubleParameter[numSupportedAttenRels];
		wtsParameterEditor = new DoubleParameterEditor[numSupportedAttenRels];
		paramList = new ParameterList[numSupportedAttenRels];
		editor = new ParameterListEditor[numSupportedAttenRels];
		imrParamsFrame = new JDialog[numSupportedAttenRels];
		for(int i=0;i<numSupportedAttenRels;++i){
			attenRelCheckBox[i] = new JCheckBox(((ScalarIntensityMeasureRelationshipAPI)attenRelsSupported.get(i)).getName());
			attenRelCheckBox[i].addItemListener(this);
			wtsParameter[i] = new DoubleParameter(wtsParamName+(i+1),new Double(1.0));
			wtsParameterEditor[i] = new DoubleParameterEditor(wtsParameter[i]);
			paramButtons[i] = new JButton(attenRelParamsButtonName);
			paramButtons[i].addActionListener(this);
			attenRelCheckBox[i].setSelected(false);
			attenRelCheckBox[i].setEnabled(false);
			paramButtons[i].setEnabled(false);
			wtsParameterEditor[i].setVisible(false);
		}
		setIMR_Params();
	}

	/**
	 * creates IMR Param listing the supported AttenRels for the
	 * single Attenuation Relationship selection based on the IM param selected.
	 */
	private void initSingleAttenRelIMR_Param(){
		singleAttenRelParamList = new ParameterList();
		ArrayList imrNamesVector=new ArrayList();
		Iterator it= attenRelsSupportedForIM.iterator();
		while(it.hasNext()){
			// make the IMR objects as needed to get the site params later
			ScalarIntensityMeasureRelationshipAPI imr = (ScalarIntensityMeasureRelationshipAPI )it.next();
			//checks to see if we are showing the IMR param for the first time,
			//if so then initialise it with the default param settings.
			if(firstTimeIMR_ParamInit){
				imr.setParamDefaults();
				Iterator it1 = imr.getSiteParamsIterator();

				// add change fail listener to the site parameters for this IMR
				while(it1.hasNext()) {
					ParameterAPI param = (ParameterAPI)it1.next();
					param.addParameterChangeFailListener(this);
				}
			}
			imrNamesVector.add(imr.getName());
		}
		//no need to initialise the IMR params again as they already have the default values.
		firstTimeIMR_ParamInit = false;


		//checking if the imrNames contains the previously selected AttenRel Name
		int index =imrNamesVector.indexOf(selectedAttenRelName);

		//AttenRel Name Param
		StringParameter selectIMR = null;
		if(index !=-1) //if the previuosly selected AttenRel is contained in the list
			// make the IMR selection paramter
			selectIMR = new StringParameter(IMR_PARAM_NAME,imrNamesVector,(String)imrNamesVector.get(index));
		else //if previuosly selected AttenRel is not pesent in it.
			selectIMR = new StringParameter(IMR_PARAM_NAME,imrNamesVector,(String)imrNamesVector.get(0));

		// listen to IMR paramter to change site params when it changes
		selectIMR.addParameterChangeListener(this);
		singleAttenRelParamList.addParameter(selectIMR);
	}


	/**
	 * Creates the ParameterList Editor for the single AttenuationRelationship
	 */
	private void initSingleAttenRelParamListAndEditor() {

		// if we are entering this function for the first time, then make imr objects
		if(singleAttenRelParamList == null || !singleAttenRelParamList.containsParameter(IMR_PARAM_NAME))
			initSingleAttenRelIMR_Param();

		// remove all the parameters except the IMR parameter
		ListIterator it = singleAttenRelParamList.getParameterNamesIterator();
		while(it.hasNext()) {
			String paramName = (String)it.next();
			if(!paramName.equalsIgnoreCase(IMR_PARAM_NAME))
				singleAttenRelParamList.removeParameter(paramName);
		}


		// now find the selceted IMR and add the parameters related to it

		// find & set the selectedIMR
		ScalarIntensityMeasureRelationshipAPI imr = getSelectedIMR_Instance();

		fireAttenuationRelationshipChangedEvent(null, imr);

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
			singleAttenRelParamList.addParameter(tempParam);
		}

		singleAttenRelParamListEditor = null;
		singleAttenRelParamListEditor = new ParameterListEditor(singleAttenRelParamList);

		singleAttenRelParamListEditor.setTitle(IMR_EDITOR_TITLE);

		// get the panel for increasing the font and border
		// this is hard coding for increasing the IMR font
		// the colors used here are from ParameterEditor
		JPanel panel = singleAttenRelParamListEditor.getParameterEditor(this.IMR_PARAM_NAME).getOuterPanel();
		TitledBorder titledBorder1 = new TitledBorder(BorderFactory.createLineBorder(new Color( 80, 80, 140 ),3),"");
		titledBorder1.setTitleColor(new Color( 80, 80, 140 ));
		Font DEFAULT_LABEL_FONT = new Font( "SansSerif", Font.BOLD, 13 );
		titledBorder1.setTitleFont(DEFAULT_LABEL_FONT);
		titledBorder1.setTitle(IMR_PARAM_NAME);
		Border border1 = BorderFactory.createCompoundBorder(titledBorder1,BorderFactory.createEmptyBorder(0,0,3,0));
		panel.setBorder(border1);

		//adding the single AttenRel Gui to the  Panel
		imrPanel.removeAll();
		imrPanel.add(singleAttenRelParamListEditor,new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));
		// set the trunc level based on trunc type
		String value = (String)singleAttenRelParamList.getParameter(SigmaTruncTypeParam.NAME).getValue();
		toggleSigmaLevelBasedOnTypeValue(value);

	}




	/**
	 *
	 * @returns the Object for the supported Attenuation Relationships in a ArrayList
	 */
	public ArrayList getSupportedAttenuationRelationships(){
		return attenRelsSupported;
	}

	/**
	 * Adds all the AttenuationRelationship related parameters to the parameter list for all the
	 * supported AttenuationRelationship. Creates the subsequent editor for these parameterlists
	 * and add them to the frame window.
	 */
	private void setIMR_Params(){
		//Panel Parent
		Container parent = this;
		/*This loops over all the parent of this class until the parent is Frame(applet)
    this is required for the passing in the JDialog to keep the focus on the adjustable params
    frame*/
		while(!(parent instanceof JFrame) && parent != null)
			parent = parent.getParent();

		for(int i=0;i<numSupportedAttenRels;++i){
			paramList[i] = new ParameterList();
			ListIterator it =((ScalarIntensityMeasureRelationshipAPI)attenRelsSupported.get(i)).getOtherParamsIterator();
			//iterating over all the Attenuation relationship parameters for the IMR.
			while(it.hasNext()){
				ParameterAPI tempParam  = (ParameterAPI)it.next();

				/*if(!tempParam.getName().equals(SigmaTruncLevelParam.NAME) &&
           !tempParam.getName().equals(SigmaTruncTypeParam.NAME))*/
				paramList[i].addParameter(tempParam);
				//adding the other common parameters ( same for all attenuation relationship)
				// to the list of the other param list.
				/*else if(!otherParams.containsParameter(tempParam.getName()))
          otherParams.addParameter(tempParam);*/

				//adding the change listener events to the parameters
				tempParam.addParameterChangeFailListener(this);
				tempParam.addParameterChangeListener(this);
			}

			//showing the parameter editors of the AttenRel in a window
			editor[i] = new ParameterListEditor(paramList[i]);
			editor[i].setTitle(attenRelNonIdenticalParams);
			imrParamsFrame[i] = new JDialog((JFrame)parent,((ScalarIntensityMeasureRelationshipAPI)attenRelsSupported.get(i)).getName()+" Params");
			imrParamsFrame[i].setSize(300,200);
			imrParamsFrame[i].getContentPane().setLayout(new GridBagLayout());
			imrParamsFrame[i].getContentPane().add(editor[i],new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
					,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));
			String value = (String)paramList[i].getParameter(SigmaTruncTypeParam.NAME).getValue();
			toggleSigmaLevelBasedOnTypeValue(value,i);
		}

		//creating the parameterList editor for the Other parameters editor and
		//putting this editor in a frame to be shown in the window
		/*otherParamsEditor = new ParameterListEditor(otherParams);
    otherParamsEditor.setTitle(attenRelIdenticalParams);
    otherIMR_paramsFrame = new JDialog((JFrame)parent,attenRelIdenticalParamsFrameTitle);
    otherIMR_paramsFrame.setSize(300,200);
    otherIMR_paramsFrame.getContentPane().setLayout(new GridBagLayout());
    otherIMR_paramsFrame.getContentPane().add(otherParamsEditor,new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));*/

		// set the trunc level based on trunc type
	}


	/**
	 * Method definition for the "Set All Identical Params".
	 * This function will set each of the identical param value in the
	 * selected AttenuationRelationship.
	 * @param e
	 */
	/*public void setAllParamButtons_actionPerformed(ActionEvent e){
    indexOfAttenRel = 0;
    //otherIMR_paramsFrame.pack();
    otherIMR_paramsFrame.setVisible(true);
  }*/

	/**
	 * This is a common function if any action is performed on the AttenuationRelationship
	 * associated parameters button.
	 * It checks what is the source of the action and depending on the source how will it
	 * response to it.
	 * @param e
	 */
	public void actionPerformed(ActionEvent e){
		//checking if the source of the action was the button
		if(e.getSource() instanceof JButton){
			Object button = e.getSource();
			//if the source of the event was IMR param button then loop over all the buttons ot check which
			//is it actually.
			for(int i=0;i<numSupportedAttenRels;++i){
				if(button.equals(paramButtons[i])){
					indexOfAttenRel = i;
					//keeps the track which was the last button pressed, which will correspond to the AttenRel model.
					lastAttenRelButtonIndex = i;

					//getting the AttenRel params from the AttenRel whose button was pressed
					//imrParamsFrame[i].pack();
					imrParamsFrame[i].setVisible(true);

				}
			}
		}
	}

	/**
	 * This is a common function if any action is performed on the AttenuationRelationship
	 * check boxes.
	 * It checks what is the source of the action and depending on the source how will it
	 * response to it.
	 * @param e
	 */
	public void itemStateChanged(ItemEvent e) {
		//if the source of event is CheckBox then perform the action accordingly
		if(e.getSource() instanceof JCheckBox){
			Object attenRelCheck = e.getSource();
			for(int i=0;i<numSupportedAttenRels;++i){
				if(attenRelCheck.equals(attenRelCheckBox[i])){
					if(attenRelCheckBox[i].isSelected()){
						paramButtons[i].setEnabled(true);
						wtsParameterEditor[i].setVisible(true);
					}
					else{
						paramButtons[i].setEnabled(false);
						wtsParameterEditor[i].setVisible(false);
					}
				}
			}
			application.setGriddedRegionSiteParams();
		}
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

		String name1 = event.getParameterName();

		// if IMT selection then update
		if (name1.equalsIgnoreCase(IMT_PARAM_NAME)) {
			updateIMT((String)event.getNewValue());
//			System.out.println("New IMT: " + (String)event.getNewValue());
			//update the AttenRels List supported by the choosen IM
			getAttenRelsSupportedForSelectedIM();
//			System.out.println("# IMRS: " + attenRelsSupportedForIM.size());
			if(singleAttenRelSelected) {
				selectedAttenRelName = (String)singleAttenRelParamList.getParameter(IMR_PARAM_NAME).getValue();
			}
			singleAttenRelParamList = null;
			selectIMRsForChoosenIMT();
		}
		// if Truncation type changes
		else if( name1.equals(SigmaTruncTypeParam.NAME) ){
			// special case hardcoded. Not the best way to do it, but need framework to handle it.
			String value = event.getNewValue().toString();
			if(!singleAttenRelSelected) //if the multipleAtten is selected
				toggleSigmaLevelBasedOnTypeValue(value, lastAttenRelButtonIndex);
			else //if the single attenRel is selected
				toggleSigmaLevelBasedOnTypeValue(value);
		}
		else if(name1.equals(PeriodParam.NAME)){
			//update the AttenRels List supported by the choosen IM
			getAttenRelsSupportedForSelectedIM();
			if(singleAttenRelSelected)
				selectedAttenRelName = (String)singleAttenRelParamList.getParameter(IMR_PARAM_NAME).getValue();
			singleAttenRelParamList = null;
			selectIMRsForChoosenIMT();
		}
		// if IMR parameter changes, then get the Gaussian truncation, etc from this selected IMR
		if(name1.equalsIgnoreCase(IMR_PARAM_NAME)) {
			initSingleAttenRelParamListAndEditor();
			//sets the Site params based on the selected AttenRel model
			application.setGriddedRegionSiteParams();
		}
		this.validate();
		this.repaint();
	}


	/**
	 *  Create a list of all the IMTs
	 */
	private void init_imtParamListAndEditor() {

		imtParamList = new ParameterList();

		//vector to store all the IMT's supported by an IMR
		ArrayList<String> imt=new ArrayList<String>();
		imtParam = new ArrayList<ParameterAPI>();
		for(int i=0;i<numSupportedAttenRels;++i){
			Iterator<ParameterAPI<?>> it =
				((ScalarIntensityMeasureRelationshipAPI)attenRelsSupported.get(i)).getSupportedIntensityMeasuresIterator();

			//loop over each IMT and get their independent parameters
			while ( it.hasNext() ) {
				DependentParameterAPI param = (DependentParameterAPI) it.next();

				String imtName = param.getName();
				DoubleParameter param1 = null;

				//check to see if the IMT param already exists in the vector list,
				//if so the get that parameter, else create new instance of the imt
				//parameter.
				if (imt.contains(imtName)) {
					// this means that we already have this IMT
					for (ParameterAPI tempParam : imtParam) {
						if (tempParam.getName().equals(imtName)) {
							param1 = (DoubleParameter)tempParam;
							break;
						}
					}
					if (param1 == null) {
						throw new RuntimeException("IMT '" + imtName + "' already in list, but parameter not found!");
					}
				}

				if (param1 == null) {
					param1=new DoubleParameter(param.getName(),(Double)param.getValue());
					//add the dependent parameter only if it has not ben added before
					imtParam.add(param1);
					imt.add(param.getName());
				}

				//				//check to see if the IMT param already exists in the vector list,
				//				//if so the get that parameter, else create new instance of the imt
				//				//parameter.
				//				DoubleParameter param1;
				//				if(imt.contains(param.getName())){
				//					//           int index = imtParam.indexOf(param);
				//					int index = -1;
				//					for (ParameterAPI theParam : imtParam) {
				//						if (theParam.getName().equals(param.getName())) {
				//							index = imtParam.indexOf(theParam);
				//							break;
				//						}
				//					}
				//					//        	 for 
				//					if (index < 0)
				//						System.out.println("Duplicate? " + param.getName() + ", IMR: "
				//								+ ((AttenuationRelationshipAPI)attenRelsSupported.get(i)).getName());
				//					param1 = (DoubleParameter)imtParam.get(index);
				//				}
				//				else{
				//					param1=new DoubleParameter(param.getName(),(Double)param.getValue());
				//					//add the dependent parameter only if it has not ben added before
				//					imtParam.add(param1);
				//					imt.add(param.getName());
				//				}

				// add all the independent parameters related to this IMT
				// NOTE: this will only work for DoubleDiscrete independent parameters; it's not general!
				// this also converts these DoubleDiscreteParameters to StringParameters
				ListIterator it2 = param.getIndependentParametersIterator();
				if(D) System.out.println("IMT is:"+param.getName());
				while ( it2.hasNext() ) {
					ParameterAPI param2 = (ParameterAPI ) it2.next();
					DoubleDiscreteConstraint values = ( DoubleDiscreteConstraint )param2.getConstraint();
					// add all the periods relating to the SA
					ArrayList allowedValues = values.getAllowedValues();

					//create the string parameter for the independent parameter with its
					//constarint being the indParamOptions.
					DoubleDiscreteParameter independentParam = new DoubleDiscreteParameter(param2.getName(),
							values, param2.getUnits (), (Double)allowedValues.get(0));

					// added by Ned so the default period is 1.0 sec (this is a hack).
					if( ((String) independentParam.getName()).equals(PeriodParam.NAME)
							&& independentParam.isAllowed(new Double(1.0)))
						independentParam.setValue(new Double(1.0));

					/**
					 * Checks to see if the independent parameter by this name already
					 * exists in the dependent parameterlist, if so then add the new constraints
					 * values to the old ones but without any duplicity. Then create the
					 * new constraint for the independent parameter.
					 */
					if(param1.containsIndependentParameter(independentParam.getName())){
						ParameterAPI tempParam = param1.getIndependentParameter(independentParam.getName());
						ArrayList paramVals = ((DoubleDiscreteConstraint)tempParam.getConstraint()).getAllowedValues();
						//keeps track if the constraint of the independent param has been changed.
						boolean changedFlag = false;
						int size = allowedValues.size();
						for(int j=0;j<size;++j){
							if(!paramVals.contains(allowedValues.get(j))){
								paramVals.add(allowedValues.get(j));
								changedFlag = true;
							}
						}
						if(changedFlag){
							//sorting the arraylist with the double values
							Collections.sort(paramVals);

							DoubleDiscreteConstraint constraint = new DoubleDiscreteConstraint(paramVals);
							//setting the new constraint in the independentParam
							tempParam.setConstraint(constraint);
						}
					}
					else //add the independent parameter to the dependent param list
						param1.addIndependentParameter(independentParam);
				}
			}
		}
		// add the IMT paramter
		StringParameter imtParameter = new StringParameter (IMT_PARAM_NAME,imt,
				(String)imt.get(0));
		imtParameter.addParameterChangeListener(this);
		imtParamList.addParameter(imtParameter);

		/* gets the iterator for each supported IMT and iterates over all its indepenedent
		 * parameters to add them to the common ArrayList to display in the IMT Panel
		 **/

		Iterator it=imtParam.iterator();
		while(it.hasNext()){
			Iterator it1=((DependentParameterAPI)it.next()).getIndependentParametersIterator();
			while(it1.hasNext()){
				ParameterAPI tempParam = (ParameterAPI)it1.next();
				imtParamList.addParameter(tempParam);
				tempParam.addParameterChangeListener(this);
			}
		}

		// now make the editor based on the paramter list
		imtEditorParamListEditor = new ParameterListEditor(imtParamList);
		imtEditorParamListEditor.setTitle( this.IMT_EDITOR_TITLE );
		// update the current IMT
		updateIMT((String)imt.get(0));
	}




	/**
	 * this method will return the name of selected IMR
	 * @return : Selected IMR name
	 */
	private String getSelectedIMR_Name() {
		return singleAttenRelParamList.getValue(IMR_PARAM_NAME).toString();
	}

	/**
	 * This method will return the instance of selected IMR only if the single
	 * AttenuationRelationship is selected else returns null.
	 * @return : Selected IMR instance
	 */
	public ScalarIntensityMeasureRelationshipAPI getSelectedIMR_Instance() {
		ScalarIntensityMeasureRelationshipAPI imr = null;
		if(singleAttenRelSelected){
			String selectedIMR = getSelectedIMR_Name();
			int size = attenRelsSupportedForIM.size();
			for(int i=0; i<size ; ++i) {
				imr = (ScalarIntensityMeasureRelationshipAPI)attenRelsSupportedForIM.get(i);
				if(imr.getName().equalsIgnoreCase(selectedIMR))
					break;
			}
		}
		return imr;
	}



	/**
	 * sigma level is visible or not
	 * @param value
	 */
	private void toggleSigmaLevelBasedOnTypeValue(String value, int buttonIndex){
		if( value.equalsIgnoreCase("none") ) {
			if(D) System.out.println("Value = " + value + ", need to set value param off.");
			editor[buttonIndex].setParameterVisible( SigmaTruncLevelParam.NAME, false );
		}
		else{
			if(D) System.out.println("Value = " + value + ", need to set value param on.");
			editor[buttonIndex].setParameterVisible( SigmaTruncLevelParam.NAME, true );
		}
	}

	/**
	 * sigma level is visible or not
	 * @param value
	 */
	protected void toggleSigmaLevelBasedOnTypeValue(String value){

		if( value.equalsIgnoreCase("none") ) {
			if(D) System.out.println("Value = " + value + ", need to set value param off.");
			singleAttenRelParamListEditor.setParameterVisible( SigmaTruncLevelParam.NAME, false );
		}
		else{
			if(D) System.out.println("Value = " + value + ", need to set value param on.");
			singleAttenRelParamListEditor.setParameterVisible( SigmaTruncLevelParam.NAME, true );
		}
		imrPanel.validate();
		imrPanel.repaint();
	}

	/**
	 * It will return the IMT selected by the user
	 * @return : IMT selected by the user
	 */
	public String getSelectedIMT() {
		return (String)getSelectedIMTparam().getValue();
	}

	/**
	 *
	 * @returns the Selected IMT Parameter
	 */
	public ParameterAPI getSelectedIMTparam(){
		return imtParamList.getParameter(IMT_PARAM_NAME);
	}

	/**
	 *
	 * @param paramName
	 * @returns the parameter with the paramName from the IMT parameter list
	 */
	public ParameterAPI getParameter(String paramName){
		return imtParamList.getParameter(paramName);
	}


	/**
	 * Shown when a Constraint error is thrown on a ParameterEditor
	 *
	 * @param  e  Description of the Parameter
	 */
	public void parameterChangeFailed( ParameterChangeFailEvent e ) {

		String S = C + " : parameterChangeWarning(): ";


		StringBuffer b = new StringBuffer();

		ParameterAPI param = ( ParameterAPI ) e.getSource();


		ParameterConstraintAPI constraint = param.getConstraint();
		String oldValueStr = e.getOldValue().toString();
		String badValueStr = e.getBadValue().toString();
		String name = param.getName();

		// only show messages for visible site parameters
		ScalarIntensityMeasureRelationshipAPI imr = null ;
		//currently I am handling the situation if this event occurs due to some
		//non-identical params for each AttenRel.
		//We might have to think of the situation if event occurs to the identical
		//params for AttenRel's, them I will have to iterate over all the selected AttenRel.
		if(indexOfAttenRel !=0 && !singleAttenRelSelected) //if multiple attenRel selected
			imr = (ScalarIntensityMeasureRelationshipAPI)attenRelsSupported.get(indexOfAttenRel);
		else if(singleAttenRelSelected) //if single attenRel selected
			imr = getSelectedIMR_Instance();

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

	}


	/**
	 *  Function that must be implemented by all Listeners for
	 *  ParameterChangeWarnEvents.
	 *
	 * @param  event  The Event which triggered this function call
	 */
	public void parameterChangeWarning( ParameterChangeWarningEvent e ){

		String S = C + " : parameterChangeWarning(): ";
		WarningParameterAPI param = e.getWarningParameter();

		//check if this parameter exists in the site param list of this IMR
		// if it does not then set its value using ignore warningAttenuationRelationshipAPI imr ;
		// only show messages for visible site parameters
		ScalarIntensityMeasureRelationshipAPI imr =null;
		//currently I am handling the situation if this event occurs due to some
		//non-identical params for each AttenRel.
		//We might have to think of the situation if event occurs to the identical
		//params for AttenRel's, them I will have to iterate over all the selected AttenRel.
		if(indexOfAttenRel !=0  && !this.singleAttenRelSelected)
			imr = (ScalarIntensityMeasureRelationshipAPI)attenRelsSupported.get(indexOfAttenRel);
		else if(singleAttenRelSelected) //if single attenRel selected
			imr = getSelectedIMR_Instance();

		ListIterator it = imr.getSiteParamsIterator();
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


		int result = 0;

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
	 * Selects the AttenuationRelationship models only if they are
	 * supported by the selected IMT.
	 * @param attenRelName : AttenRel name which needs to be
	 * selected to do the calculation.
	 * It makes only one AttenRel selected at a time
	 */
	public void setIMR_Selected(String attenRelName){
		if(!singleAttenRelSelected){ //if multiple attenRel is selected
			for(int i=0;i < numSupportedAttenRels;++i){
				if(attenRelCheckBox[i].getText().equals(attenRelName)){
					if(attenRelCheckBox[i].isEnabled())
						attenRelCheckBox[i].setSelected(true);
					else if(attenRelCheckBox[i].isEnabled() && attenRelCheckBox[i].isSelected())
						attenRelCheckBox[i].setSelected(false);
				}
			}
		}
		//if the single attenRel is selected
		else if(singleAttenRelParamList.getParameter(this.IMR_PARAM_NAME).isAllowed(attenRelName))
			singleAttenRelParamList.getParameter(this.IMR_PARAM_NAME).setValue(attenRelName);
		else
			throw new RuntimeException(attenRelName+" not supported for the choosen IMT");
	}

	/**
	 *
	 * @returns the selected IMRs instances in the ArrayList
	 */
	public ArrayList getSelectedIMRs(){

		ArrayList selectedIMRs = new ArrayList();
		if(!singleAttenRelSelected){ //if the multipleAttenuationRelation is selected
			for(int i=0;i < numSupportedAttenRels;++i)
				if(attenRelCheckBox[i].isEnabled() && attenRelCheckBox[i].isSelected())
					selectedIMRs.add(attenRelsSupported.get(i));
		}
		else{
			int size = attenRelsSupportedForIM.size();
			for(int i=0;i<size;++i){ //if single Attenuation relationship is selected
				String name = ((ScalarIntensityMeasureRelationshipAPI)attenRelsSupportedForIM.get(i)).getName();
				//add the Attenuation that is selected
				if(name.equals((String)singleAttenRelParamListEditor.getParameterEditor(this.IMR_PARAM_NAME).getValue())){
					selectedIMRs.add(attenRelsSupportedForIM.get(i));
					break;
				}
			}
		}
		return selectedIMRs;
	}



	/**
	 * set the IMT parameter in selected IMR's
	 */
	public void setIMT() {
		ParameterAPI param = getSelectedIntensityMeasure();
		ArrayList selectedAttenRels = getSelectedIMRs();
		int size = selectedAttenRels.size();
		for(int i=0;i<size;++i)
			((ScalarIntensityMeasureRelationshipAPI)selectedAttenRels.get(i)).setIntensityMeasure(param);
	}


	/**
	 * gets the selected Intensity Measure Parameter and its dependent Parameter
	 * @return
	 */
	public ParameterAPI getSelectedIntensityMeasure(){
		String selectedImt = imtParamList.getValue(this.IMT_PARAM_NAME).toString();
		//set all the  parameters related to this IMT
		return getSelectedIntensityMeasure(selectedImt);
	}


	/**
	 *
	 * @returns true if single attenuation relationship GUI is selected else
	 * returns false if multiple attenuation relationship GUI is selected.
	 */
	public boolean isSingleAttenRelTypeSelected(){
		return singleAttenRelSelected;
	}



	/**
	 * gets the selected Intensity Measure Parameter and its dependent Parameter
	 * for given IMT name
	 * @param imtName
	 */
	public ParameterAPI getSelectedIntensityMeasure(String imtName){
		Iterator it= imtParam.iterator();
		while(it.hasNext()){
			DependentParameterAPI param=(DependentParameterAPI)it.next();
			if(param.getName().equalsIgnoreCase(imtName))
				return param;
		}
		return null;

	}



	/**
	 *
	 * @returns the site parameters iterator for the selected AttenuationRelationships
	 * It also avoids the duplicity of the site params if AttenuationRelationships
	 * share them.
	 */
	public Iterator getSelectedAttenRelSiteParams(){
		// get the selected IMR
		ArrayList attenRel = getSelectedIMRs();

		//ArrayList to store the siteParams for all selected AttenRel
		ArrayList siteParams = new ArrayList();
		//getting all the selected AttenRels and iterating over their site params
		//adding them as clones to the vector but avoiding the duplicity.
		//There can be a scenario when the AttenRels have same site type, so we
		//don't want to duplicate the site params but do want to set their values in both
		//the selected attenRels.
		for(int i=0;i<attenRel.size();++i){
			ScalarIntensityMeasureRelationshipAPI attenRelApp = (ScalarIntensityMeasureRelationshipAPI)attenRel.get(i);
			ListIterator it = attenRelApp.getSiteParamsIterator();
			while(it.hasNext()){
				ParameterAPI tempParam = (ParameterAPI)it.next();
				boolean flag = true;
				//iterating over all the added siteParams to check if we have added that
				//site param before.
				for(int j=0;j<siteParams.size();++j)
					if(tempParam.getName().equals(((ParameterAPI)siteParams.get(j)).getName()))
						flag= false;
				if(flag){
					ParameterAPI param = (ParameterAPI)tempParam.clone();
					param.addParameterChangeFailListener(this);
					siteParams.add(param);
				}
			}
		}
		return siteParams.iterator();
	}


	/**
	 * this function toggle between the single and multiple Attenuation selection panel
	 * If Single AttenuationRelation panel is selected then it will toggle to the
	 * Multiple AttenuationRelation panel and visa-a-versa.
	 */
	public void toggleBetweenSingleAndMultipleAttenRelGuiSelection(){

		singleAttenRelSelected = !singleAttenRelSelected;
		toggleBetweenSingleAndMultipleAttenRel();
	}

	/**
	 *
	 * @returns the ParameterList editor of the Single AttenuationRelationship
	 * if multiple attenuationrelationship panel is selected then it return null.
	 * so in order for the person to actally get the handle to the single AttenRel
	 * paramlist editor, we have to first select the Single AttenRel Gui Panel and
	 * then get handle to the editor.
	 */
	public ParameterListEditor getSingleAttenRelParamListEditor(){
		if(singleAttenRelParamList != null)
			return singleAttenRelParamListEditor;
		else
			return null;
	}




	/**
	 * This function updates the IMTeditor with the independent parameters for the selected
	 * IMT, by making only those visible to the user.
	 * @param imtName : It is the name of the selected IMT, based on which we make
	 * its independentParameters visible.
	 */

	private void updateIMT(String imtName) {
		Iterator it= imtParamList.getParametersIterator();

		//making all the IMT parameters invisible
		while(it.hasNext())
			imtEditorParamListEditor.setParameterVisible(((ParameterAPI)it.next()).getName(),false);

		//making the choose IMT parameter visible
		imtEditorParamListEditor.setParameterVisible(IMT_PARAM_NAME,true);

		it=imtParam.iterator();
		//for the selected IMT making its independent parameters visible
		while(it.hasNext()){
			DependentParameterAPI param=(DependentParameterAPI)it.next();
			if(param.getName().equalsIgnoreCase(imtName)){
				Iterator it1=param.getIndependentParametersIterator();
				while(it1.hasNext())
					imtEditorParamListEditor.setParameterVisible(((ParameterAPI)it1.next()).getName(),true);
			}
		}

	}

	/**
	 *
	 * @returns the normalised weights for each selected attenuationRelationship
	 */
	public ArrayList getSelectedIMR_Weights(){
		ArrayList wtsList = new ArrayList();
		if(!this.singleAttenRelSelected){ // if multiple attenRel are selected then give it take relative wts
			double totalWts =0;
			for(int i=0;i < numSupportedAttenRels;++i){
				if(wtsParameterEditor[i].isVisible()){
					double value = ((Double)wtsParameterEditor[i].getValue()).doubleValue();
					totalWts +=value;
					wtsList.add(new Double(value));
				}
			}
			int size = wtsList.size();
			for(int i=0;i<size;++i)
				wtsList.set(i,new Double(((Double)wtsList.get(i)).doubleValue()/totalWts));
		}
		else //if the single AttenRel is selecetd give it the wt of 1
			wtsList.add(new Double(1.0));
		return wtsList;
	}



	/**
	 *
	 * @returns the Intensity Measure Parameter Editor
	 */
	public ParameterListEditor getIntensityMeasureParamEditor(){
		return imtEditorParamListEditor;
	}

	/**
	 * Checks to see if the Intensity Measure is supported by the AttenuationRelationship.
	 * If it is supported make its parameters and check box enabled and set the
	 * parameters default values, else disable the choice of that AttenuationRelationship.
	 */
	private void selectIMRsForChoosenIMT(){
		ParameterAPI param = getSelectedIntensityMeasure();
		//Iterating over all the supported AttenRels to check if they support the selected IMT
		String paramName = param.getName();

		//only update the multiple attenRel check boxes if person has once selected it.
		if(attenRelCheckBox !=null){
			int size =0;
			//Keeps records of the previously selected AttenuationRelationships
			LinkedList prevSelectedAttenRel = null;
			//do this processing only if multiple attenRels is selected.
			if(!singleAttenRelSelected){
				prevSelectedAttenRel =  new LinkedList();
				//adding the previuosly already selected AttenRels
				for(int i=0;i< numSupportedAttenRels;++i){
					if(attenRelCheckBox[i].isSelected()) //getting the previously selected AttenRels
						prevSelectedAttenRel.add(attenRelsSupported.get(i));
				}
				size  = prevSelectedAttenRel.size();
			}

			for(int i=0;i < numSupportedAttenRels;++i){
				AttenuationRelationship attenRel = (AttenuationRelationship)attenRelsSupported.get(i);
				if(!attenRel.isIntensityMeasureSupported(param)){ //if AttenRel selected does not support IMT
					attenRelCheckBox[i].setSelected(false);
					attenRelCheckBox[i].setEnabled(false);
				}
				//				else{ //if selectedAttenRel supports IMT
				//
				//					//if there are previously selected AttenRels then iterate over those to
				//					//keep the one previuosly selected.
				//					if(size > 0){
				//						for(int j=0;j < size;++j){
				//							//Attenuation Relation at the index i supports the IMT then see
				//							//if it was previously selected, if so then keep it selected
				//							AttenuationRelationship attenRelTemp = (AttenuationRelationship)prevSelectedAttenRel.get(j);
				//							if(attenRelTemp.getName().equals(((JCheckBox)attenRelCheckBox[i]).getText())){
				//								attenRelCheckBox[i].setEnabled(true);
				//								attenRelCheckBox[i].setSelected(true);
				//								System.out.println("Setting TRUE (sub-loop)");
				//								break;
				//							}
				//						}
				//					}
				else{
					attenRelCheckBox[i].setEnabled(true);
					attenRelCheckBox[i].setSelected(true);
				}
				//				}
			}
		}
		//add the changed gui components based the single or multiple selection
		toggleBetweenSingleAndMultipleAttenRel();
	}


	/**
	 * Returns the ArrayList of the AttenuationRelation being supported by the selected IM
	 * @return
	 */
	private ArrayList getAttenRelsSupportedForSelectedIM(){
		ParameterAPI param = getSelectedIntensityMeasure();
		//Iterating over all the supported AttenRels to check if they support the selected IMT
		String paramName = param.getName();
		attenRelsSupportedForIM = new ArrayList();
		for(int i=0;i < numSupportedAttenRels;++i){
			AttenuationRelationship attenRel = (AttenuationRelationship)attenRelsSupported.get(i);
			if(attenRel.isIntensityMeasureSupported(param))
				attenRelsSupportedForIM.add(attenRel);
		}
		return attenRelsSupportedForIM;
	}



	/**
	 *
	 * @returns the Metadata string for the IMR Gui Bean
	 */
	public String getIMR_ParameterListMetadataString(){
		String metadata = "";
		if(!this.singleAttenRelSelected){
			for(int i=0;i<numSupportedAttenRels;++i){
				if(attenRelCheckBox[i].isSelected()){
					metadata += "IMR = "+((ScalarIntensityMeasureRelationshipAPI)attenRelsSupported.get(i)).getName()+
					" ; "+ wtsParameter[i].getName()+" = "+wtsParameter[i].getValue()+" ; "+
					"Non Identical Param: "+editor[i].getVisibleParameters().toString()+"<br>\n";
				}
			}
		}
		else{
			metadata = this.singleAttenRelParamList.getParameterListMetadataString();
		}
		return metadata+"<br>\n";
	}


	/**
	 *
	 * @returns the Metadata string for the IMT Gui Bean
	 */
	public String getIMT_ParameterListMetadataString(){
		String metadata="";
		ListIterator it = imtEditorParamListEditor.getVisibleParameters().getParametersIterator();
		int paramSize = imtEditorParamListEditor.getVisibleParameters().size();
		while(it.hasNext()){
			//iterates over all the visible parameters
			ParameterAPI tempParam = (ParameterAPI)it.next();
			//if the param name is IMT Param then it is the Dependent param
			if(tempParam.getName().equals(this.IMT_PARAM_NAME)){
				metadata = tempParam.getName()+" = "+(String)tempParam.getValue();
				if(paramSize>1)
					metadata +="[ ";
			}
			else{ //rest all are the independent params
				metadata += tempParam.getName()+" = "+((Double)tempParam.getValue()).doubleValue()+" ; ";
			}
		}
		if(paramSize>1)
			metadata = metadata.substring(0,metadata.length()-3);
		if(paramSize >1)
			metadata +=" ] ";
		return metadata+"\n";
	}


	/**
	 * Switches between the multiple and single attenuation relationhship gui bean.
	 */
	private void toggleBetweenSingleAndMultipleAttenRel(){
		imrPanel.removeAll();
		//if single attenuation relationship is already selected then toggle to multiple attenrel
		if(!singleAttenRelSelected){
			singleAttenRelParamList = null;
			toggleButton.setText(SINGLE_ATTEN_REL);
			if(attenRelCheckBox == null){
				try{
					//if multiAttenRel is selected for first time then create all its gui elements
					initMultipleAttenRelParamListAndEditor();
					//enable only those AttenRels which are supported by choosen IMT
					selectIMRsForChoosenIMT();
				}catch(Exception e){
					e.printStackTrace();
				}
			}
			for(int i=0;i<numSupportedAttenRels;++i){
				imrPanel.add(attenRelCheckBox[i],new GridBagConstraints(0, i+1, 1, 1, 1.0, 1.0
						,GridBagConstraints.WEST, GridBagConstraints.WEST, new Insets(4, 3, 5, 5), 0, 0));
				imrPanel.add(wtsParameterEditor[i],new GridBagConstraints(1, i+1, 1, 1, 1.0, 1.0
						,GridBagConstraints.CENTER, GridBagConstraints.WEST, new Insets(4, 3, 5, 5), 0, 0));
				imrPanel.add(paramButtons[i],new GridBagConstraints(2, i+1, 1, 1, 1.0, 1.0
						,GridBagConstraints.CENTER, GridBagConstraints.WEST, new Insets(4, 3, 5, 5), 0, 0));
			}
			fireAttenuationRelationshipChangedEvent(null, null);
		}
		else{ //if multiple attenuation relationships panel was selected the toggle to single attenrel.
			toggleButton.setText(MULTIPLE_ATTEN_REL);
			initSingleAttenRelParamListAndEditor();
		}

		imrPanel.validate();

		//set the site params for the selected Atten Rels
		application.setGriddedRegionSiteParams();
	}

	/**
	 * this function is called when the person tries to switch between the single
	 * and multiple attenuationRelationship gui bean.
	 * @param e
	 */
	void toggleButton_actionPerformed(ActionEvent e) {
		//toggle between the single and multiple AttenRel Selection.
		toggleBetweenSingleAndMultipleAttenRelGuiSelection();
		validate();
		repaint();
	}

	public void addAttenuationRelationshipChangeListener(ScalarIMRChangeListener listener) {
		listeners.add(listener);
	}

	public void removeAttenuationRelationshipChangeListener(ScalarIMRChangeListener listener) {
		listeners.remove(listener);
	}

	public void fireAttenuationRelationshipChangedEvent(ScalarIntensityMeasureRelationshipAPI oldAttenRel, ScalarIntensityMeasureRelationshipAPI newAttenRel) {
		if (listeners.size() == 0)
			return;
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> oldMap = 
			new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		oldMap.put(TectonicRegionType.ACTIVE_SHALLOW, oldAttenRel);
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> newMap = 
			new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
		newMap.put(TectonicRegionType.ACTIVE_SHALLOW, newAttenRel);
		ScalarIMRChangeEvent event = new ScalarIMRChangeEvent(this, oldMap, newMap);

		for (ScalarIMRChangeListener listener : listeners) {
			listener.imrChange(event);
		}
	}
}
