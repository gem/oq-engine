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

package org.opensha.sha.gui.controls;

import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.SystemColor;
import java.awt.Window;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JTextPane;
import javax.swing.Timer;

import org.opensha.commons.data.ArbDiscretizedXYZ_DataSet;
import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.sha.gui.ScenarioShakeMapApp;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

/**
 * <p>Title: GenerateHazusControlPanelForSingleMultipleIMRs</p>
 * <p>Description: This class generates the ShapeFiles for the Hazus for the
 * selected Scenario.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class GenerateHazusControlPanelForSingleMultipleIMRs extends ControlPanel
implements Runnable{

	public static final String NAME = "Generate Hazus Shape files for Scenario";

	private JPanel jPanel1 = new JPanel();
	private JTextPane infoPanel = new JTextPane();
	private BorderLayout borderLayout1 = new BorderLayout();


	//instance of the application calling this control panel.
	private ScenarioShakeMapApp application;


	//Stores the XYZ data set for the SA-0.3, SA-1.0, PGA and PGV, if the calculation
	//have to be done on the standalone system
	private XYZ_DataSetAPI sa03_xyzdata;
	private XYZ_DataSetAPI sa10_xyzdata;
	private XYZ_DataSetAPI pga_xyzdata;
	private XYZ_DataSetAPI pgv_xyzdata;

	//Stores the full path to the file where the XYZ data set objects are stored, if the
	//calculation are to be done on the server
	private String sa_03xyzDataString;
	private String sa_10xyzDataString;
	private String pga_xyzDataString;
	private String pgv_xyzDataString;

	//boolean to check if the calculation are to be done on the server
	private boolean calcOnServer = true;

	//metadata string for the different IMT required to generate the shapefiles for Hazus.
	private String metadata="";
	private JButton generateHazusShapeFilesButton = new JButton();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();

	//records if the user has pressed the button to generate the XYZ data to produce
	//the shapefiles for inout to Hazus
	boolean generatingXYZDataForShapeFiles= false;

	//progress bar
	CalcProgressBar calcProgress;

	//timer instance to show the progress bar component
	Timer timer;

	//to keep track of different stages o show in progress bar
	private int step;
	
	private Component parent;
	private JFrame frame;

	/**
	 * Class constructor.
	 * This will generate the shapefiles for the input to the Hazus
	 * @param parent : parent frame on which to show this control panel
	 * @param api : Instance of the application using this control panel
	 */
	public GenerateHazusControlPanelForSingleMultipleIMRs(Component parent,
			ScenarioShakeMapApp api) {
		super(NAME);
		this.parent = parent;
		this.application = api;
	}
	
	public void doinit() {
		frame = new JFrame();
		// show the window at center of the parent component
		frame.setLocation(parent.getX()+parent.getWidth()/2,
				parent.getY()+parent.getHeight()/2);
		try {
			jbInit();
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	private void jbInit() throws Exception {
		frame.getContentPane().setLayout(borderLayout1);
		jPanel1.setLayout(gridBagLayout1);
		frame.setTitle("Hazus Shapefiles Control");
		infoPanel.setBackground(SystemColor.menu);
		infoPanel.setEnabled(false);
		String info = new String("Info:\n\nClicking the above generates a set of Hazus shapefiles (0.3- and 1.0-sec SA,"+
				" pga, and pgv) for the selected Earthquake "+
				"Rupture and IMR.  Be sure to have selected the "+
				"\"Average-Horizontal\" component, and note that PGV "+
				"is in units of inches/sec in these files (as assumed by Hazus)." +
				"  Note also that the following Map Attributes are temporarliy set for the calculation:"+
				" \"Plot Log\" is deselected); \"Color Scale Limits\" is \"From Data\"; and "+
		"\"Generate Hazus Shape Files\" is selected.");
		infoPanel.setPreferredSize(new Dimension(812, 24));
		infoPanel.setEditable(false);
		infoPanel.setText(info);
		jPanel1.setMinimumSize(new Dimension(350, 220));
		jPanel1.setPreferredSize(new Dimension(350, 300));
		generateHazusShapeFilesButton.setText("Generate Hazus Shape Files");
		generateHazusShapeFilesButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				generateHazusShapeFilesButton_actionPerformed(e);
			}
		});
		frame.getContentPane().add(jPanel1, BorderLayout.CENTER);
		jPanel1.add(infoPanel,  new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 42, 19, 41), 0, 0));
		jPanel1.add(generateHazusShapeFilesButton,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.NORTH, GridBagConstraints.NONE, new Insets(14, 49, 6, 54), 87, 8));
	}


	/**
	 * Generate the dataset to make shapefiles that goes as input to Hazus.
	 * For that it iterates over all the following IMT(SA-1sec, SA-0.3sec, PGA and PGV) to
	 * create the dataset for them.
	 * @param selectedAttenRels : List of the selected AttenuationRelationships selected
	 * @param selectedAttenRelsWts : List of teh wts of the selected AttenRels
	 */
	private void generateHazusFiles(ArrayList selectedAttenRels,ArrayList selectedAttenRelWts) throws
	ParameterException, RuntimeException, RegionConstraintException {

		//metadata String
		metadata="<br>Hazus Metadata: \n<br>"+
		"-------------------\n<br>";

		//gets the EarthquakeRupture Object
		application.getEqkRupture();

		//doing for SA
		hazusCalcForSA(selectedAttenRels,selectedAttenRelWts);

		//Doing for PGV
		doCalcForPGV(selectedAttenRels,selectedAttenRelWts);

		//Doing for PGA
		hazusCalcForPGA(selectedAttenRels,selectedAttenRelWts);

		step =6;
		//generating the maps for the Hazus
		if(!calcOnServer)
			application.makeMapForHazus(sa03_xyzdata,sa10_xyzdata,pga_xyzdata,pgv_xyzdata);
		else
			application.makeMapForHazus(sa_03xyzDataString,sa_10xyzDataString,pga_xyzDataString,pgv_xyzDataString);
	}


	/**
	 * Does the Hazus Calc for the IMT being PGV for all the selected AttenRels
	 * @param selectedAttenRels
	 */
	private void doCalcForPGV(ArrayList selectedAttenRels, ArrayList selectedAttenRelsWts) throws
	ParameterException, RuntimeException, RegionConstraintException {

		step =4;
		metadata += "IMT = PGV"+"<br>\n";

		//creating the 2 seperate list for the attenRels selected, for one suuporting
		//the PGV and results calculated using PGV and other not supporting PGV and result
		//calculated using the SA at 1sec and multiplying by 37.24*2.54.
		ArrayList attenRelListSupportingPGV = new ArrayList();
		ArrayList attenRelListNotSupportingPGV = new ArrayList();

		//List of the Attenuations Wts supporting PGV
		ArrayList attenRelListPGV_Wts = new ArrayList();
		//List of the Attenuations Wts not supporting PGV
		ArrayList attenRelListNot_PGV_Wts = new ArrayList();

		int size = selectedAttenRels.size();
		for(int i=0;i<size;++i){
			AttenuationRelationship attenRel = (AttenuationRelationship)selectedAttenRels.get(i);
			if(attenRel.isIntensityMeasureSupported(PGV_Param.NAME)){
				attenRelListSupportingPGV.add(attenRel);
				attenRelListPGV_Wts.add(selectedAttenRelsWts.get(i));
			}
			else{
				attenRelListNotSupportingPGV.add(attenRel);
				attenRelListNot_PGV_Wts.add(selectedAttenRelsWts.get(i));
			}
		}
		if(!calcOnServer){ // if the calculation are to be done one the standalone system
			//arrayList declaration for the Atten Rel not supporting PGV
			ArrayList list = null;
			//arrayList declaration for the Atten Rel supporting PGV
			ArrayList pgvList = null;
			//XYZ data set supporting the PGV
			XYZ_DataSetAPI xyzDataSet_PGV = null;
			//XYZ data set not supporting the PGV
			XYZ_DataSetAPI xyzDataSet = null;

			if(attenRelListSupportingPGV.size() >0){
				//if the AttenRels support PGV
				xyzDataSet_PGV =hazusCalcForPGV(attenRelListSupportingPGV,attenRelListPGV_Wts,true);
				//ArrayLists containing the Z Values for the XYZ dataset.
				pgvList = xyzDataSet_PGV.getZ_DataSet();
				size = pgvList.size();
			}

			if(attenRelListNotSupportingPGV.size()>0){
				//if the AttenRels do not support PGV
				xyzDataSet = hazusCalcForPGV(attenRelListNotSupportingPGV,attenRelListNot_PGV_Wts,false);
				//ArrayLists containing the Z Values for the XYZ dataset for attenRel not supporting PGV.
				list = xyzDataSet.getZ_DataSet();
				size = list.size();
			}

			if(xyzDataSet_PGV != null && xyzDataSet!=null){
				//ArrayList to store the combine( added) result(from Atten that support PGV
				//and that do not support PGV) of the Z Values for the PGV.
				ArrayList finalPGV_Vals = new ArrayList();
				//adding the values from both the above list for PGV( one calculated using PGV
				//and other calculated using the SA at 1sec and mutipling by the scalar 37.24*2.54).
				for(int i=0;i<size;++i)
					finalPGV_Vals.add(new Double(((Double)pgvList.get(i)).doubleValue()+((Double)list.get(i)).doubleValue()));
				//creating the final dataste for the PGV dataset.
				pgv_xyzdata = new ArbDiscretizedXYZ_DataSet(xyzDataSet_PGV.getX_DataSet(),
						xyzDataSet_PGV.getY_DataSet(),finalPGV_Vals);
			}
			else{
				//if XYZ dataset supporting PGV is null
				if(xyzDataSet_PGV ==null)
					pgv_xyzdata = xyzDataSet;
				//if XYZ dataset not supporting PGV is null
				else if(xyzDataSet ==null)
					pgv_xyzdata = xyzDataSet_PGV;
			}
		}
		else{ //if the calc to be done on the server
			//this function does the PGV calc on the server
			doCalcForPGV_OnServer(attenRelListSupportingPGV,attenRelListNotSupportingPGV,
					attenRelListPGV_Wts,attenRelListNot_PGV_Wts);
		}
	}

	/**
	 * This function does the PGV calc on the server and just save the result there.
	 * For Attenuations not supporting PGV it calculates the result by SA-1sec and the
	 * multiplying by  37.24*2.54.
	 * @param attenRelsSupportingPGV : List of AttenRels supporting PGV
	 * @param attenRelsNotSupportingPGV : List of AttenRels not supporting PGV
	 */
	private void doCalcForPGV_OnServer(ArrayList attenRelsSupportingPGV,
			ArrayList attenRelsNotSupportingPGV,
			ArrayList attenRelListPGV_Wts,
			ArrayList attenRelListNot_PGV_Wts) throws
			RegionConstraintException, ParameterException, RuntimeException {

		//contains the list of all the selected AttenuationRelationship models
		ArrayList attenRelList = new ArrayList();

		//contains the list of all the selected AttenuationRelationship with their wts.
		ArrayList attenRelWtList = new ArrayList();

		//setting the IMT to PGV for the AttenRels supporting PGV
		int size = attenRelsSupportingPGV.size();

		for(int i=0;i<size;++i){
			((ScalarIntensityMeasureRelationshipAPI)attenRelsSupportingPGV.get(i)).setIntensityMeasure(PGV_Param.NAME);
			attenRelList.add((ScalarIntensityMeasureRelationshipAPI)attenRelsSupportingPGV.get(i));
			attenRelWtList.add(attenRelListPGV_Wts.get(i));
		}

		//setting the IMT to SA-1sec for the AttenRels not supporting PGV
		size = attenRelsNotSupportingPGV.size();
		for(int i=0;i<size;++i){
			((ScalarIntensityMeasureRelationshipAPI)attenRelsNotSupportingPGV.get(i)).setIntensityMeasure(SA_Param.NAME);
			attenRelList.add((ScalarIntensityMeasureRelationshipAPI)attenRelsNotSupportingPGV.get(i));
			attenRelWtList.add(attenRelListNot_PGV_Wts.get(i));
		}
		//setting the SA period to 1.0 for the atten rels not supporting PGV
		this.setSA_PeriodForSelectedIMRs(attenRelsNotSupportingPGV,1.0);

		//as the calculation will be done on the server so saves the XYZ object and returns the path to object file.
		pgv_xyzDataString = (String)application.generateShakeMap(attenRelList,attenRelWtList,PGV_Param.NAME);

	}




	/**
	 * Hazus Calculation for PGA
	 * @param selectedAttenRels: List of AttenuationRelation models
	 */
	private void hazusCalcForPGA(ArrayList selectedAttenRels,ArrayList selectedAttenRelsWt) throws
	RegionConstraintException, ParameterException, RuntimeException {
		step =5;
		int size = selectedAttenRels.size();
		for(int i=0;i<size;++i)
			((ScalarIntensityMeasureRelationshipAPI)selectedAttenRels.get(i)).setIntensityMeasure(PGA_Param.NAME);

		if(!calcOnServer) //if calculation are not to be done on the server
			pga_xyzdata = (XYZ_DataSetAPI)application.generateShakeMap(selectedAttenRels,selectedAttenRelsWt,PGA_Param.NAME);
		else //if calculation are to be done on the server
			pga_xyzDataString = (String)application.generateShakeMap(selectedAttenRels,selectedAttenRelsWt,PGA_Param.NAME);
		metadata += "IMT = PGA"+"\n";
	}


	/**
	 * Hazus Calculation for SA at 1sec and 0.3 sec
	 * @param selectedAttenRels: List of AttenuationRelation models
	 */
	private void hazusCalcForSA(ArrayList selectedAttenRels, ArrayList selectedAttenRelsWt) throws
	RegionConstraintException, ParameterException, RuntimeException {
		//Doing for SA
		step =2;
		int size = selectedAttenRels.size();
		for(int i=0;i<size;++i)
			((ScalarIntensityMeasureRelationshipAPI)selectedAttenRels.get(i)).setIntensityMeasure(SA_Param.NAME);

		//Doing for SA-0.3sec
		setSA_PeriodForSelectedIMRs(selectedAttenRels,0.3);

		//if calculation are not to be done on the server
		if(!calcOnServer)
			sa03_xyzdata = (XYZ_DataSetAPI)application.generateShakeMap(selectedAttenRels,selectedAttenRelsWt,SA_Param.NAME);
		else //if calculation are to be done on the server
			sa_03xyzDataString = (String)application.generateShakeMap(selectedAttenRels,selectedAttenRelsWt,SA_Param.NAME);
		metadata += "IMT = SA [ SA Damping = 5.0 ; SA Period = 0.3 ]"+"<br>\n";

		step =3;
		//Doing for SA-1.0sec
		setSA_PeriodForSelectedIMRs(selectedAttenRels,1.0);
		//if calculation are not to be done on the server
		if(!calcOnServer)
			sa10_xyzdata = (XYZ_DataSetAPI)application.generateShakeMap(selectedAttenRels,selectedAttenRelsWt,SA_Param.NAME);
		else
			//if calculation are to be done on the server
			sa_10xyzDataString = (String)application.generateShakeMap(selectedAttenRels,selectedAttenRelsWt,SA_Param.NAME);
		metadata += "IMT = SA [ SA Damping = 5.0 ; SA Period = 1.0 ]"+"<br>\n";
	}

	/**
	 * Hazus Calculation for PGV
	 * @param AttenRelList : List of AttenuationRelation models
	 * @param pgvSupported : Checks if the list of the AttenRels support PGV
	 * @return
	 */
	private XYZ_DataSetAPI hazusCalcForPGV(ArrayList attenRelList, ArrayList attenRelWtList,boolean pgvSupported) throws
	RegionConstraintException, ParameterException, RuntimeException {
		//if the PGV is supportd by the AttenuationRelationships
		XYZ_DataSetAPI pgvDataSet = null;
		int size = attenRelList.size();
		if(pgvSupported){
			for(int i=0;i<size;++i)
				((ScalarIntensityMeasureRelationshipAPI)attenRelList.get(i)).setIntensityMeasure(PGV_Param.NAME);

			pgvDataSet = (XYZ_DataSetAPI)application.generateShakeMap(attenRelList,attenRelWtList,PGV_Param.NAME);
			//metadata += imtParamEditor.getVisibleParameters().getParameterListMetadataString()+"<br>\n";
		}
		else{ //if the List of the attenRels does not support IMT then use SA at 1sec for PGV
			for(int i=0;i<size;++i)
				((ScalarIntensityMeasureRelationshipAPI)attenRelList.get(i)).setIntensityMeasure(SA_Param.NAME);
			this.setSA_PeriodForSelectedIMRs(attenRelList,1.0);

			pgvDataSet = (XYZ_DataSetAPI)application.generateShakeMap(attenRelList,attenRelWtList,SA_Param.NAME);

			//if PGV is not supported by the attenuation then use the SA-1sec pd
			//and multiply the value by scaler 37.24*2.54
			ArrayList zVals = pgvDataSet.getZ_DataSet();
			size = zVals.size();
			for(int i=0;i<size;++i){
				double val = ((Double)zVals.get(i)).doubleValue()*37.24*2.54;
				zVals.set(i,new Double(val));
			}
		}
		return pgvDataSet;
	}


	/**
	 * sets the SA Period in selected IMR's with the argument period
	 */
	private void setSA_PeriodForSelectedIMRs(ArrayList selectedAttenRels, double period) {
		int size = selectedAttenRels.size();
		for(int i=0;i<size;++i)
			((ScalarIntensityMeasureRelationshipAPI)selectedAttenRels.get(i)).getParameter(PeriodParam.NAME).setValue(new Double(period));
	}


	/**
	 *
	 * @returns the metadata for the IMT GUI if this control panel is selected
	 */
	public String getIMT_Metadata(){
		return metadata;
	}


	/**
	 *
	 * @returns the XYZ data set for the SA-0.3sec if calculation are to be done local machine,
	 * else the String to the object file on the server.
	 */
	public Object getXYZ_DataForSA_03(){
		if(!calcOnServer)
			return sa03_xyzdata;
		else
			return sa_03xyzDataString;
	}


	/**
	 *
	 * @return the XYZ data set for the SA-1.0sec if calculation are to be done local machine,
	 * else the String to the object file on the server.
	 */
	public Object getXYZ_DataForSA_10(){
		if(!calcOnServer)
			return sa10_xyzdata;
		else
			return sa_10xyzDataString;
	}

	/**
	 *
	 * @return the XYZ data set for the PGA if calculation are to be done local machine,
	 * else the String to the object file on the server.
	 */
	public Object getXYZ_DataForPGA(){
		if(!calcOnServer)
			return pga_xyzdata;
		else
			return pga_xyzDataString;
	}

	/**
	 *
	 * @return the XYZ data set for the PGV if calculation are to be done local machine,
	 * else the String to the object file on the server.
	 */
	public Object getXYZ_DataForPGV(){
		if(!calcOnServer)
			return pgv_xyzdata;
		else
			return pgv_xyzDataString;
	}


	/**
	 * thread method
	 */
	public void run() {
		try {
			runToGenerateShapeFilesAndMaps();
		}
		catch (RegionConstraintException ee) {
			JOptionPane.showMessageDialog(frame, ee.getMessage(), "Input Error",
					JOptionPane.ERROR_MESSAGE);
			step = 0;
		}
		catch (RuntimeException ee) {
			JOptionPane.showMessageDialog(frame, ee.getMessage(), "Server Problem",
					JOptionPane.INFORMATION_MESSAGE);
			step = 0;
		}
		if(calcProgress != null)
			calcProgress.dispose();
	}


	/**
	 * This method creates the shapefiles data for Hazus and scenario shake maps
	 * for the same data.
	 */
	public void runToGenerateShapeFilesAndMaps() throws RegionConstraintException,
	RuntimeException {
		getRegionAndMapType();
		//checks if the calculation are to be done on the server
		calcOnServer = application.doCalculationOnServer();
		generateShapeFilesForHazus();
	}




	/**
	 * When the Button to generate dataset for hazus is pressed
	 * @param e
	 */
	void generateHazusShapeFilesButton_actionPerformed(ActionEvent e) {
		calcProgress = new CalcProgressBar("Hazus Shape file data","Starting Calculation...");
		timer = new Timer(200, new ActionListener() {
			public void actionPerformed(ActionEvent evt) {
				if(step == 1)
					calcProgress.setProgressMessage("Doing Calculation for the Hazus ShapeFile Data...");
				else if(step == 2)
					calcProgress.setProgressMessage("Doing Calculation for 0.3-sec SA (1 of 4)");
				else if(step == 3)
					calcProgress.setProgressMessage("Doing Calculation for 1.0-sec SA (2 of 4)");
				else if(step == 4)
					calcProgress.setProgressMessage("Doing Calculation for PGV (3 of 4)");
				else if(step == 5)
					calcProgress.setProgressMessage("Doing Calculation for PGA (4 of 4)");
				else if(step == 6)
					calcProgress.setProgressMessage("Generating the Map images for Hazus ...");
				else if(step ==0){
					calcProgress.showProgress(false);
					calcProgress.dispose();
					calcProgress = null;
					timer.stop();
				}
			}
		});
		Thread t = new Thread(this);
		t.start();
	}

	/**
	 * Creates the dataset to generate the shape files that goes as input to Hazus.
	 */
	public void generateShapeFilesForHazus() throws RegionConstraintException,
	ParameterException, RuntimeException {

		//keeps tracks if the user has pressed the button to generate the xyz dataset
		//for prodcing the shapefiles for Hazus.
		setGenerateShapeFilesForHazus(true);
		generateHazusFiles(application.getSelectedAttenuationRelationships(),
				application.getSelectedAttenuationRelationshipsWts());
		step = 0;
	}

	/**
	 * Function accepts true if user wants to generate the hazus shapefiles. On setting
	 * to false it does not generate the hazus shape files. User has to explicitly
	 * set to false if he does not want to generate the shapefiles for hazus once he
	 * has pressed button to generate the shape files for hazus which sets this
	 * generateHazusShapeFiles to true. This function has to be explicitly have to be
	 * called with false in order not to generate the shape files.
	 * @param generateHazusShapeFiles
	 */
	public void setGenerateShapeFilesForHazus(boolean generateHazusShapeFiles){
		generatingXYZDataForShapeFiles = generateHazusShapeFiles;
	}

	/**
	 * This function sets the Gridded region Sites and the type of plot user wants to see
	 * IML@Prob or Prob@IML and it value.
	 */
	public void getRegionAndMapType() throws RuntimeException,
	RegionConstraintException {
		application.getGriddedSitesMapTypeAndSelectedAttenRels();
		step =1;
		if(timer !=null)
			timer.start();
	}

	/**
	 *
	 * @returns if the generate shape files for Hazus being done.
	 * If returns then files for hazus will be generated else if returns
	 * false then files are not being generated.
	 */
	public boolean isGenerateShapeFilesForHazus(){
		return generatingXYZDataForShapeFiles;
	}

	@Override
	public Window getComponent() {
		return frame;
	}

}
