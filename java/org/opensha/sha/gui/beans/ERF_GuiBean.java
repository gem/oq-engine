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
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Font;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.ListIterator;

import javax.swing.BorderFactory;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.earthquake.ERF_EpistemicList;
import org.opensha.sha.earthquake.EqkRupForecastBaseAPI;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.param.MagFreqDistParameter;
import org.opensha.sha.param.SimpleFaultParameter;
import org.opensha.sha.param.editor.MagFreqDistParameterEditor;
import org.opensha.sha.param.editor.SimpleFaultParameterEditor;

/**
 * <p>Title: ERF_GuiBean </p>
 * <p>Description: It displays ERFs and parameters supported by them</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class ERF_GuiBean extends JPanel implements ParameterChangeFailListener,
		ParameterChangeListener{

	private final static String C = "ERF_GuiBean";

	//this vector saves the names of all the supported Eqk Rup Forecasts
	protected ArrayList<String> erfNamesVector=new ArrayList<String>();
	//this vector holds the full class names of all the supported Eqk Rup Forecasts
	private ArrayList<String> erfClasses;

	// ERF Editor stuff
	public final static String ERF_PARAM_NAME = "Eqk Rup Forecast";
	// these are to store the list of independ params for chosen ERF
	public final static String ERF_EDITOR_TITLE =  "Set Forecast";
	// boolean for telling whether to show a progress bar
	boolean showProgressBar = true;

	//instance of the selected ERF
	EqkRupForecastBaseAPI eqkRupForecast = null;
	//instance of progress bar to show the progress of updation of forecast
	CalcProgressBar progress= null;


	//parameter List to hold the selected ERF parameters
	private ParameterList parameterList;
	private ParameterListEditor listEditor;

	//TimeSpanGui Bean
	private TimeSpanGuiBean timeSpanGuiBean;
	//private JScrollPane erfScrollPane;
	private JPanel erfAndTimespanPanel;

	//checks to see if this a new ERF instance has been given by application to this Gui Bean.
	private boolean isNewERF_Instance;
	
	private HashMap<String, Object> classNameERFMap = new HashMap<String, Object>();
	
	/**
	 * Constructor : It accepts the classNames of the ERFs to be shown in the editor
	 * @param erfClassNames
	 */
	public ERF_GuiBean(ArrayList<String> erfClassNames) throws InvocationTargetException{
		try {
			jbInit();
		}
		catch(Exception e) {
			e.printStackTrace();
		}
		// save the class names of ERFs to be shown\
		erfClasses = erfClassNames;

		// create the instance of ERFs
		init_erf_IndParamListAndEditor();
		// forecast 1  is selected initially
		setParamsInForecast();
	}


	/**
	 * Creates a class instance from a string of the full class name including packages.
	 * This is how you dynamically make objects at runtime if you don't know which\
	 * class beforehand.
	 *
	 */
	private Object createERFClassInstance( String className) throws InvocationTargetException{
		String S = C + ": createERFClassInstance(): ";
		if (classNameERFMap.containsKey(className))
			return classNameERFMap.get(className);
		try {
			Object[] paramObjects = new Object[]{};
			Class[] params = new Class[]{};
			Class erfClass = Class.forName( className );
			Constructor con = erfClass.getConstructor(params);
			Object obj = con.newInstance( paramObjects );
			classNameERFMap.put(className, obj);
			return obj;
		} catch ( ClassCastException e ) {
			System.out.println(S + e.toString());
			throw new RuntimeException( S + e.toString() );
		} catch ( ClassNotFoundException e ) {
			System.out.println(S + e.toString());
			throw new RuntimeException( S + e.toString() );
		} catch ( NoSuchMethodException e ) {
			System.out.println(S + e.toString());
			throw new RuntimeException( S + e.toString() );
		} catch ( IllegalAccessException e ) {
			System.out.println(S + e.toString());
			throw new RuntimeException( S + e.toString() );
		} catch ( InstantiationException e ) {
			System.out.println(S + e.toString());
			throw new RuntimeException( S + e.toString() );
		} catch (InvocationTargetException e) {
			JOptionPane.showMessageDialog(this,"An ERF failed to load because it could not connect to a server, check your internet connection and firewall settings.","Internet Connection Problem",
					JOptionPane.OK_OPTION);
			throw e;
		}
	}

	/**
	 * Gets the name of the ERF and show in the PickList for the ERF's
	 * As the ERF_NAME is defined as the static variable inside the EqkRupForecast class
	 * so it gets the vale for this clas field. Generate the object of the ERF only if the
	 * user chooses it from the pick list.
	 * @param className
	 * @return
	 */
	private String getERFName(String className) {
		try {
			Class<?> erfClass = Class.forName(className);
			Field nameField = erfClass.getField("NAME");
			String name = (String)nameField.get(erfClass);
			return name;
		} catch (ClassNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (SecurityException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (NoSuchFieldException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IllegalArgumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IllegalAccessException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return null;
//		// TODO so this doesn't do what the comment says, it actually creates the ERF.
//		// but because it's not stored, it has to create it again. Adding a fix.
//		try{
//			Object obj = this.createERFClassInstance(className);
//			String name = new String (((EqkRupForecastBaseAPI)obj).getName());
//			obj = null;
//			return name;
//		}catch(Exception e){
//			e.printStackTrace();
//			return null;
//		}
		
	}

	/**
	 * init erf_IndParamList. List of all available forecasts at this time
	 */
	protected void init_erf_IndParamListAndEditor() throws InvocationTargetException{

		this.parameterList = new ParameterList();


		//gets the iterator for the class names of all the ERF's
		Iterator<String> it = erfClasses.iterator();

		//ArrayList to maintain which erf cannot be instatiated and have to be removed from the list
		ArrayList<String> erfFailed = new ArrayList<String>();
		//adding the names of all the ERF's to the erfNamesVector- Pick List for the ERF's
		while(it.hasNext()){
			String erfClass = it.next();
			String name = getERFName(erfClass);
			if(name !=null) erfNamesVector.add(name);
			else erfFailed.add(erfClass);
		}
		
		//removing the erf's from the erfClasses ArrayList which could not be instantiated
		if(erfFailed.size() >0){
			int size =erfFailed.size();
			for(int i=0;i<size;++i){
				System.out.println("Failed ERF Name:"+erfFailed.get(i));
				erfClasses.remove(erfFailed.get(i));
			}
		}

		//Name of the first ERF class that is to be shown as the default ERF in the ERF Pick List
		String erfClassName = (String)erfClasses.get(0);
		// make the ERF objects to get their adjustable parameters
		eqkRupForecast = (EqkRupForecastBaseAPI ) createERFClassInstance(erfClassName);

		// make the forecast selection parameter
		StringParameter selectERF= new StringParameter(ERF_PARAM_NAME,
				erfNamesVector, (String)erfNamesVector.get(0));
		selectERF.addParameterChangeListener(this);
		parameterList.addParameter(selectERF);
	}


	/**
	 * this function is called to add the paramters based on the forecast
	 * selected by the user. Based on the selected Forecast it also creates
	 * timespan and add that to the same panel window that shows the ERF parameters.
	 */
	private void setParamsInForecast() throws InvocationTargetException{

		ParameterAPI chooseERF_Param = parameterList.getParameter(this.ERF_PARAM_NAME);
		parameterList = new ParameterList();
		parameterList.addParameter(chooseERF_Param);
		// get the selected forecast
		getSelectedERF_Instance();
		//getting the EqkRupForecast param List and its iterator
		ParameterList paramList = eqkRupForecast.getAdjustableParameterList();
		Iterator it = paramList.getParametersIterator();

		// make the parameters visible based on selected forecast
		while(it.hasNext()){
			ParameterAPI param = (ParameterAPI)it.next();
			//System.out.println("Param Name: "+param.getName());
			//if(param.getName().equals(EqkRupForecast.TIME_DEPENDENT_PARAM_NAME))
			param.addParameterChangeListener(this);
			param.addParameterChangeFailListener(this);

			parameterList.addParameter(param);
		}

		//remove the parameters if they already exists in the panel.
		if(listEditor !=null){
			erfAndTimespanPanel.remove(listEditor);
			listEditor = null;
		}



		//creating the new instance of ERF parameter list editors
		listEditor = new ParameterListEditor(parameterList);

		// show the ERF gui Bean in JPanel
		erfAndTimespanPanel.add(listEditor, BorderLayout.CENTER);
//		erfAndTimespanPanel.add(listEditor, 
//				new GridBagConstraints(
//						0, 0, 1, 1, 1.0, 1.0,
//						GridBagConstraints.CENTER, 
//						GridBagConstraints.BOTH, 
//						new Insets(4,4,4,4),
//						0, 0));

		// now make the editor based on the paramter list
		listEditor.setTitle(ERF_EDITOR_TITLE);

		// get the panel for increasing the font and border
		// this is hard coding for increasing the IMR font
		// the colors used here are from ParameterEditor
		JPanel panel = listEditor.getParameterEditor(this.ERF_PARAM_NAME).getOuterPanel();
		TitledBorder titledBorder1 = new TitledBorder(
				BorderFactory.createLineBorder(
						new Color( 80, 80, 140 ),3),ERF_PARAM_NAME);
		titledBorder1.setTitleColor(new Color( 80, 80, 140 ));
		Font DEFAULT_LABEL_FONT = new Font( "SansSerif", Font.BOLD, 13 );
		titledBorder1.setTitleFont(DEFAULT_LABEL_FONT);
		Border border1 = BorderFactory.createCompoundBorder(titledBorder1,BorderFactory.createEmptyBorder(0,0,3,0));
		panel.setBorder(border1);
		createTimeSpanPanel();
		this.validate();
		this.repaint();
	}

	//adds the TimeSpan panel to the Gui depending on Timespan from EqkRupForecast.
	private void createTimeSpanPanel(){
		if (timeSpanGuiBean == null) {
			// create the TimeSpan Gui Bean object
			timeSpanGuiBean = new TimeSpanGuiBean(eqkRupForecast.getTimeSpan());
			timeSpanGuiBean.setOpaque(false);
			timeSpanGuiBean.setBorder(
					BorderFactory.createEmptyBorder(8, 0, 0, 0));
		} else {
			erfAndTimespanPanel.remove(timeSpanGuiBean);
		}
		//adding the Timespan Gui panel to the ERF Gui Bean
		timeSpanGuiBean.setTimeSpan(eqkRupForecast.getTimeSpan());
		
		erfAndTimespanPanel.add(timeSpanGuiBean, BorderLayout.PAGE_END);
//		erfAndTimespanPanel.add(timeSpanGuiBean, TODO clean
//				new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0,
//						GridBagConstraints.CENTER,
//						GridBagConstraints.BOTH,
//						new Insets(0,0,0,0), 0, 0));
	}



	/**
	 * gets the lists of all the parameters that exists in the ERF parameter Editor
	 * then checks if the magFreqDistParameter exists inside it , if so then returns the MagEditor
	 * else return null.  The only reason this is public is because at least one control panel
	 * (for the PEER test cases) needs access.
	 * @returns MagFreDistParameterEditor
	 */
	public MagFreqDistParameterEditor getMagDistEditor(){

		ListIterator lit = parameterList.getParametersIterator();
		while(lit.hasNext()){
			ParameterAPI param=(ParameterAPI)lit.next();
			if(param instanceof MagFreqDistParameter){
				MagFreqDistParameterEditor magDistEditor=((MagFreqDistParameterEditor)listEditor.getParameterEditor(param.getName()));
				return magDistEditor;
			}
		}
		return null;
	}


	/**
	 * gets the lists of all the parameters that exists in the ERF parameter Editor
	 * then checks if the simpleFaultParameter exists inside it , if so then returns the
	 * SimpleFaultParameterEditor else return null.  The only reason this is public is
	 * because at least one control panel (for the PEER test cases) needs access.
	 * @returns SimpleFaultParameterEditor
	 */
	public SimpleFaultParameterEditor getSimpleFaultParamEditor(){

		ListIterator lit = parameterList.getParametersIterator();
		while(lit.hasNext()){
			ParameterAPI param=(ParameterAPI)lit.next();
			if(param instanceof SimpleFaultParameter){
				SimpleFaultParameterEditor simpleFaultEditor = ((SimpleFaultParameterEditor)listEditor.getParameterEditor(param.getName()));
				return simpleFaultEditor;
			}
		}
		return null;
	}


	/**
	 * returns the name of selected ERF
	 * @return
	 */
	public String getSelectedERF_Name() {
		return (String)parameterList.getValue(this.ERF_PARAM_NAME);
	}

	/**
	 * get the selected ERF instance
	 * It returns the forecast without updating the forecast
	 * @return
	 */
	public EqkRupForecastBaseAPI getSelectedERF_Instance() throws InvocationTargetException{
		//updating the MagDist Editor
		updateMagDistParam();
		//update the fault Parameter
		updateFaultParam();
		return eqkRupForecast;
	}


	/**
	 * get the selected ERF instance.
	 * It returns the ERF after updating its forecast
	 * @return
	 */
	public EqkRupForecastBaseAPI getSelectedERF() throws InvocationTargetException{
		getSelectedERF_Instance();
		if(this.showProgressBar) {
			// also show the progress bar while the forecast is being updated
			progress = new CalcProgressBar("Forecast","Updating Forecast ...");
			//progress.displayProgressBar();
		}
		// update the forecast
		eqkRupForecast.updateForecast();
		if (showProgressBar) {
			progress.dispose();
			progress = null;
		}
		return eqkRupForecast;

	}

	/**
	 * Save the selected forecast into a file
	 *
	 * @return
	 * @throws InvocationTargetException
	 */
	public String saveSelectedERF() throws InvocationTargetException {
		getSelectedERF_Instance();

		//save the updated forecast in the file as the binary object.
		String location = eqkRupForecast.updateAndSaveForecast();
		//if (this.showProgressBar) progress.dispose();
		return location;
	}

	/**
	 * It sees whether selected ERF is a Epistemic list.
	 * @return : true if selected ERF is a epistemic list, else false
	 */
	public boolean isEpistemicList() {
		try{
			EqkRupForecastBaseAPI eqkRupForecast = getSelectedERF_Instance();
			if(eqkRupForecast instanceof ERF_EpistemicList)
				return true;
		}catch(Exception e){
			e.printStackTrace();
		}
		return false;
	}


	/**checks if the magFreqDistParameter exists inside it ,
	 * if so then gets its Editor and calls the method to update the magDistParams.
	 */
	protected void updateMagDistParam() {
		MagFreqDistParameterEditor magEditor=getMagDistEditor();
		if(magEditor!=null) ((MagFreqDistParameter)magEditor.getParameter()).setMagDist();
	}

	/**checks if the Fault Parameter Editor exists inside it ,
	 * if so then gets its Editor and calls the method to update the faultParams.
	 */
	protected void updateFaultParam() {
		SimpleFaultParameterEditor faultEditor = getSimpleFaultParamEditor();
		if(faultEditor!=null)  faultEditor.getParameterEditorPanel().setEvenlyGriddedSurfaceFromParams();
	}



	/**
	 *  Shown when a Constraint error is thrown on a ParameterEditor
	 *
	 * @param  e  Description of the Parameter
	 */
	public void parameterChangeFailed( ParameterChangeFailEvent e ) {


		StringBuffer b = new StringBuffer();

		ParameterAPI param = ( ParameterAPI ) e.getSource();


		ParameterConstraintAPI constraint = param.getConstraint();
		String oldValueStr = e.getOldValue().toString();
		String badValueStr = e.getBadValue().toString();
		String name = param.getName();

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


		String name1 = event.getParameterName();

		// if ERF selected by the user  changes
		if( name1.equals(this.ERF_PARAM_NAME) && !isNewERF_Instance){
			String value = event.getNewValue().toString();
			int size = this.erfNamesVector.size();
			try{
				for(int i=0;i<size;++i){
					if(value.equalsIgnoreCase((String)erfNamesVector.get(i))){
						eqkRupForecast = (EqkRupForecastBaseAPI)this.createERFClassInstance((String)erfClasses.get(i));
						break;
					}
				}
			}catch(Exception e){
				e.printStackTrace();
			}
		}

		try {
			setParamsInForecast();
		} catch (InvocationTargetException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		createTimeSpanPanel();

		this.validate();
		this.repaint();
	}

	/**
	 * This allows tuning on or off the showing of a progress bar
	 * @param show - set as true to show it, or false to not show it
	 */
	public void showProgressBar(boolean show) {
		this.showProgressBar=show;
	}

	/**
	 * Adds the ERF's to the existing ERF List in the gui bean to be displayed in the gui.
	 * This function allows user to add the more ERF's names to the existing list from the application.
	 * This function allows user with the flexibility that he does not always have to specify the erfNames
	 * at time of instantiating this ERF gui bean.
	 * @param erfList
	 * @throws InvocationTargetException
	 */
	public void addERFs_ToList(ArrayList<String> erfList) throws InvocationTargetException{

		int size = erfList.size();
		for(int i=0;i<size;++i)
			if(!erfClasses.contains(erfList.get(i)))
				erfClasses.add(erfList.get(i));
		// create the instance of ERFs
		erfNamesVector.clear();
		init_erf_IndParamListAndEditor();
		setParamsInForecast();
	}

	/**
	 * This function closes the progress bar window which shows forcast updation,
	 * if user has choosen to see the progress of updation, in the first place.
	 */
	public void closeProgressBar(){
		if(showProgressBar && progress!=null){
			progress.dispose();
			progress = null;
		}
	}

	/**
	 * Removes the ERF's from the existing ERF List in the gui bean to be displayed in the gui.
	 * This function allows user to remove ERF's names from the existing list from the application.
	 * This function allows user with the flexibility that he can always remove the erfNames
	 * later after instantiating this ERF gui bean.
	 * @param erfList
	 * @throws InvocationTargetException
	 */
	public void removeERFs_FromList(ArrayList erfList) throws InvocationTargetException{

		int size = erfList.size();
		for(int i=0;i<size;++i)
			if(erfClasses.contains(erfList.get(i)))
				erfClasses.remove(erfList.get(i));
		// create the instance of ERFs
		erfNamesVector.clear();
		init_erf_IndParamListAndEditor();
		setParamsInForecast();
	}

	/**
	 *
	 * @returns the List of ERF parameters
	 */
	public ParameterList getERFParameterList(){
		return parameterList;
	}

	/**
	 *
	 * @returns the parameter list editor for ERF parameters
	 */
	public ParameterListEditor getERFParameterListEditor(){
		return listEditor;
	}


	/**
	 * Sets the EqkRupForecast in the ERF_GuiBean
	 */
	public void setERF(EqkRupForecastBaseAPI eqkRupForecast){
		this.eqkRupForecast = eqkRupForecast;
		isNewERF_Instance = true;
		String erfName = eqkRupForecast.getName();
		int size = erfNamesVector.size();
		for(int i=0;i<size;++i){
			if(erfName.equalsIgnoreCase( (String) erfNamesVector.get(i))) {
				try{
					listEditor.getParameterEditor(ERF_PARAM_NAME).setValue(erfName);
					setParamsInForecast();
				}catch(Exception e){
					e.printStackTrace();
				}
				isNewERF_Instance = false;
				break;
			}
		}
	}


	/**
	 *
	 * @returns the selected ERF timespan gui bean object
	 */
	public TimeSpanGuiBean getSelectedERFTimespanGuiBean(){
		return timeSpanGuiBean;
	}

	/**
	 *
	 * @param paramName
	 * @returns the parameter with the ParamName
	 */
	public ParameterAPI getParameter(String paramName){
		if(this.parameterList.containsParameter(paramName)){
			if(listEditor.getParameterEditor(paramName).isVisible()){
				return parameterList.getParameter(paramName);
			}
		}
		else{
			timeSpanGuiBean.getParameterList().getParameter(paramName);
		}
		return null;
	}


	private void jbInit() throws Exception {
		
		//setLayout(new GridBagLayout());
		setLayout(new BorderLayout());
		setOpaque(false);
		//erfAndTimespanPanel.setLayout(new BorderLayout());
//		add(erfScrollPane,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
//				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 6, 4, 5),0, 0));
		erfAndTimespanPanel = new JPanel(new BorderLayout());
		erfAndTimespanPanel.setBorder(BorderFactory.createEmptyBorder(0,0,0,4));
		erfAndTimespanPanel.setOpaque(false);

		JScrollPane erfScrollPane = new JScrollPane(erfAndTimespanPanel);
		erfScrollPane.setBorder(null);
		erfScrollPane.setOpaque(false);
		erfScrollPane.getViewport().setOpaque(false);
		//erfScrollPane.setBackground(Color.orange);
		add(erfScrollPane,  BorderLayout.CENTER);
		
		//erfScrollPane.getViewport().add(erfAndTimespanPanel, null);
	}

}

