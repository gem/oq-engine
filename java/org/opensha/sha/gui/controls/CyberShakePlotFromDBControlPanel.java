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
import java.awt.Color;
import java.awt.Component;
import java.awt.GridBagLayout;
import java.awt.Window;
import java.awt.event.ActionEvent;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Collections;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSeparator;
import javax.swing.SwingConstants;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.gui.UserAuthDialog;
import org.opensha.commons.param.DoubleDiscreteParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.cybershake.db.CybershakeERF;
import org.opensha.sha.cybershake.db.CybershakeIM;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.CybershakeSiteInfo2DB;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.ERF2DB;
import org.opensha.sha.cybershake.db.ERF2DBAPI;
import org.opensha.sha.cybershake.db.HazardCurve2DB;
import org.opensha.sha.cybershake.db.HazardCurveComputation;
import org.opensha.sha.cybershake.db.PeakAmplitudesFromDBAPI;
import org.opensha.sha.cybershake.db.Runs2DB;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2.MeanUCERF2;
import org.opensha.sha.gui.HazardCurveServerModeApplication;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBean;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBeanAPI;
import org.opensha.sha.gui.beans.EqkRuptureFromERFSelectorPanel;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.gui.beans.IMR_MultiGuiBean;
import org.opensha.sha.gui.beans.IMT_GuiBean;
import org.opensha.sha.gui.beans.IMT_NewGuiBean;
import org.opensha.sha.gui.beans.Site_GuiBean;
import org.opensha.sha.gui.beans.TimeSpanGuiBean;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;

/**
 * <p>Title: CyberShakePlotFromDBControlPanel </p>
 *
 * <p>Description: This allows to view the Deterministic Cybershake Curves with
 * that of OpenSHA using teh Empirical based AttenuationRelationships.
 * </p>
 *
 * @author Nitin Gupta
 * @since March 7,2006
 * @version 1.0
 */
public class CyberShakePlotFromDBControlPanel
extends ControlPanel implements ParameterChangeListener {

	public static final String NAME = "Plot Cybershake data";
	
	public static final String ERF_NAME = MeanUCERF2.NAME;

	private static final boolean D = false;
	public static final String SITE_SELECTOR_PARAM = "CyberShake Site";
	public static final String ERF_SELECTOR_PARAM = "Earthquake Rupture Forecast";
	public static final String SA_PERIOD_SELECTOR_PARAM = "IM Type";
	public static final String SRC_INDEX_PARAM = "Source Index";
	public static final String RUP_INDEX_PARAM = "Rupture Index";
	public static final String SGT_VAR_PARAM = "SGT Variation ID";
	public static final String RUP_VAR_SCENARIO_PARAM = "Rupture Variation Scenario ID";

	private static final String DETER_PROB_SELECTOR_PARAM = "Curve Type";
	private static final String PROB_CURVE = "Probabilistic Curve";
	private static final String DETER_CURVE = "Deterministic Curve";

	private static final String NONE_AVAILABLE_STRING = "None Available";
	
	String prevUser = "";
	String prevPass = "";
	
	DiscretizedFuncAPI currentHazardCurve;

	JPanel guiPanel = new JPanel();
	JButton submitButton = new JButton();
	JButton paramSettingButton = new JButton();
	JButton publishButton = new JButton("Publish Curve");
	JButton robPlotButton = new JButton("Setup Rob Plot");
	JButton tomPlotButton = new JButton("Setup Tom Plot");
	JLabel controlPanelLabel = new JLabel();
	BorderLayout borderLayout1 = new BorderLayout();

	int selectedSGTVariation = 5;
	int selectedRupVarScenario = 3;

	CalcProgressBar calcProgress = null;

	//Curve type selector param
	private StringParameter curveTypeSelectorParam;

	//Site selection param
	private StringParameter siteSelectionParam;

	//source index parameter
	private StringParameter sgtVarParam;

	//rupture index parameter
	private StringParameter rupVarScenarioParam;

	//SA Period selection param
	private StringParameter saPeriodParam;

	//SA Period selection param
	private StringParameter erfParam;

	//source index parameter
	private StringParameter srcIndexParam;

	//rupture index parameter
	private StringParameter rupIndexParam;

	//Editor to show the parameters in the panel
	private ParameterListEditor listEditor;
	//list to show the parameters
	private ParameterList paramList;

	//handle to the application using this control panel
	private HazardCurveServerModeApplication application;
	
	double prevIMVal = 3;

	//if deterministic curve needs to be plotted
	private boolean isDeterministic ;
	GridBagLayout gridBagLayout1 = new GridBagLayout();

	//Database connection 
	private static final DBAccess db = Cybershake_OpenSHA_DBApplication.db;

	/**
	 * Handle to Cybershake Sites info in DB
	 */
	private CybershakeSiteInfo2DB csSites = new CybershakeSiteInfo2DB(db);
	
	HazardCurve2DB curve2db = new HazardCurve2DB(db);

	private ERF2DBAPI erf2db = new ERF2DB(db);

	private HazardCurveComputation hazCurve = new HazardCurveComputation(db);
	private Runs2DB runs2db = new Runs2DB(db);
	private PeakAmplitudesFromDBAPI peakAmps2DB = hazCurve.getPeakAmpsAccessor();

	//current selection of site, srcId and rupId from the cyberShake database
	private CybershakeSite selectedSite;
	private CybershakeERF selectedERF;
	private int selectedSrcId,selectedRupId;
	boolean curveInDB = false;
	boolean ampsInDB = false;
	private ArrayList<CybershakeIM> ims;
	private ArrayList<Integer> dbCurves;
	private ArrayList<Integer> ampCurves;
	private CybershakeIM im;
	private String imString;

	ArrayList<CybershakeSite> sites;
	ArrayList<String> siteNames;

	ArrayList<CybershakeERF> erfs;
	ArrayList<String> erfNames;

	private JFrame frame;
	
	public CyberShakePlotFromDBControlPanel(HazardCurveServerModeApplication app) {
		super(NAME);
		this.application = app;
	}
	
	public void doinit() {
		frame = new JFrame();
		frame.setTitle(NAME);
		try {
			jbInit();
		}
		catch (Exception exception) {
			exception.printStackTrace();
		}
		frame.pack();
		Component parent = (Component)application;
		// show the window at center of the parent component
		frame.setLocation(parent.getX()+parent.getWidth()/2,
				parent.getY());
//		hazCurve.addProgressListener(this);
	}

	private void jbInit() throws Exception {
		frame.getContentPane().setLayout(borderLayout1);
		guiPanel.setLayout(new BorderLayout());
		submitButton.setText("Plot Curve");
		paramSettingButton.setText("Set Params for Comparison");
		paramSettingButton.setToolTipText("Sets the same parameters in the Pathway-1\n "+
		"application as in Cybershake calculations.");
		publishButton.setToolTipText("Put the hazard curve in the CyberShake database");
		controlPanelLabel.setHorizontalAlignment(SwingConstants.CENTER);
		controlPanelLabel.setHorizontalTextPosition(SwingConstants.CENTER);
		controlPanelLabel.setText("Cybershake Hazard Data Plot Control");
		//creating the Site and SA Period selection for the Cybershake control panel
		initCyberShakeControlPanel();
		frame.getContentPane().add(guiPanel, java.awt.BorderLayout.CENTER);
		guiPanel.add(controlPanelLabel, BorderLayout.NORTH);
		guiPanel.add(listEditor, BorderLayout.CENTER);
		JPanel topButtonPanel = new JPanel();
		JPanel bottomButtonPanel = new JPanel();
		JPanel buttonPanel = new JPanel();
		topButtonPanel.setLayout(new BoxLayout(topButtonPanel, BoxLayout.X_AXIS));
		bottomButtonPanel.setLayout(new BoxLayout(bottomButtonPanel, BoxLayout.X_AXIS));
		buttonPanel.setLayout(new BoxLayout(buttonPanel, BoxLayout.Y_AXIS));
		bottomButtonPanel.add(paramSettingButton);
		bottomButtonPanel.add(publishButton);
		bottomButtonPanel.add(submitButton);
		topButtonPanel.add(new JLabel("Plot Format Helpers: "));
		topButtonPanel.add(robPlotButton);
		topButtonPanel.add(tomPlotButton);
		buttonPanel.add(topButtonPanel);
		buttonPanel.add(new JSeparator());
		buttonPanel.add(bottomButtonPanel);
		robPlotButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				setRobPlotParams(e);
			}
		});
		tomPlotButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				setTomPlotParams(e);
			}
		});
		guiPanel.add(buttonPanel, BorderLayout.SOUTH);
		submitButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				submitButton_actionPerformed(e);
			}
		});
		paramSettingButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				paramSettingButton_actionPerformed(e);
			}
		});
		publishButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				commitButton_actionPerformed(e);
			}
		});
		publishButton.setEnabled(false);
		frame.setSize(400,600);
	}


	/**
	 * Creates the Cybershake site and SA Period GUI elements.
	 * Allows the user to select the Site and SA period value for which
	 * hazard curve needs to be plotted.
	 */
	private void initCyberShakeControlPanel(){
		sites = this.csSites.getAllSitesFromDB();
		siteNames = new ArrayList<String>();
		for (CybershakeSite site : sites) {
			siteNames.add(site.id + ". " + site.name + " (" + site.short_name + ")");
		}


		ArrayList supportedCurvesType = new ArrayList();
		supportedCurvesType.add(PROB_CURVE);
		supportedCurvesType.add(DETER_CURVE);

		curveTypeSelectorParam = new StringParameter(this.DETER_PROB_SELECTOR_PARAM,
				supportedCurvesType,
				(String)
				supportedCurvesType.get(0));

		paramList = new ParameterList();

		// erf param
		erfs = erf2db.getAllERFs();
		erfNames = new ArrayList<String>();
		for (CybershakeERF erf : erfs) {
			erfNames.add(erf.id + ": " + erf.description);
		}
		erfParam = new StringParameter(ERF_SELECTOR_PARAM, erfNames, erfNames.get(0));
		erfParam.addParameterChangeListener(this);
		selectedERF = erfs.get(0);

		// sgt variations
		initSGTVarIDsParam();
		initRupVarScenarioIDsParam();


		//rupVarScenarioIDs

		siteSelectionParam = new StringParameter(SITE_SELECTOR_PARAM,
				siteNames,siteNames.get(0));
		selectedSite = sites.get(siteNames.indexOf((String)siteSelectionParam.getValue()));
		loadSA_PeriodParam();
		this.imString = (String)saPeriodParam.getValue();
		initSrcIndexParam();
		initRupIndexParam();
		paramList.addParameter(curveTypeSelectorParam);
		paramList.addParameter(siteSelectionParam);
		paramList.addParameter(erfParam);
		paramList.addParameter(sgtVarParam);
		paramList.addParameter(rupVarScenarioParam);
		paramList.addParameter(saPeriodParam);
		paramList.addParameter(srcIndexParam);
		paramList.addParameter(rupIndexParam);
		siteSelectionParam.addParameterChangeListener(this);
		curveTypeSelectorParam.addParameterChangeListener(this);
		listEditor = new ParameterListEditor(paramList);
		listEditor.setTitle("Set Params for Cybershake Curve");
		makeParamVisible();
	}


	/**
	 * Creates the SA Period Parameter which allows the user to select the
	 * SA Period for a given site for which hazard data needs to be plotted.
	 */
	private void loadSA_PeriodParam(){
		ims = new ArrayList<CybershakeIM>();
		dbCurves = new ArrayList<Integer>();
		ampCurves = new ArrayList<Integer>();

//		saPeriods = hazCurve.getSupportedSA_PeriodStrings(selectedSite.id, this.selectedERF.id selectedSGTVariation, selectedRupVarScenario);
		ArrayList<Integer> runIDs = runs2db.getRunIDs(selectedSite.id, selectedERF.id, selectedSGTVariation, selectedRupVarScenario, null, null, null, null);
		ArrayList<CybershakeIM> ampIms = null;
		if (runIDs.size() > 0)
			ampIms = hazCurve.getSupportedSA_PeriodStrings(runIDs.get(0));
		else
			ampIms = new ArrayList<CybershakeIM>();
		ArrayList<CybershakeIM> curveIms = curve2db.getSupportedIMs(selectedSite.id, this.selectedERF.id, selectedRupVarScenario, selectedSGTVariation);
		
		if (!isDeterministic) {
			for (CybershakeIM curveIM : curveIms) {
				System.out.println("Adding Curve IM: " + curveIM);
				ims.add(curveIM);
			}
		}
		
		for (CybershakeIM ampIM : ampIms) {
			boolean match = false;
			for (CybershakeIM im : ims) {
				if (im.equals(ampIM)) {
					match = true;
					break;
				}
			}
			if (!match) {
				ims.add(ampIM);
			}
		}
		
		Collections.sort(ims);
		
		if (!isDeterministic) {
			for (CybershakeIM curveIM : curveIms) {
				for (CybershakeIM im : ims) {
					if (curveIM.equals(im)) {
						dbCurves.add(ims.indexOf(im));
						break;
					}
				}
			}
			
			for (CybershakeIM ampIM : ampIms) {
				for (CybershakeIM im : ims) {
					if (ampIM.equals(im)) {
						ampCurves.add(ims.indexOf(im));
						break;
					}
				}
			}
		}

		ArrayList<String> imStrings = new ArrayList<String>();
		if (ims.size() > 0) {
			for (CybershakeIM newIM : ims) {
				imStrings.add(newIM.toString());
			}
			curveInDB = false;
			ampsInDB = false;
			int index = 0;
			for (CybershakeIM im : ims) {
				if (Math.abs(im.getVal() - prevIMVal) < 0.05) {
					index = ims.indexOf(im);
					break;
				}
			}
			im = ims.get(index);
			prevIMVal = im.getVal();
			for (int id : dbCurves) {
				if (id == index) {
					curveInDB = true;
					break;
				}
			}
			for (int id : ampCurves) {
				if (id == index) {
					ampsInDB = true;
					break;
				}
			}
			imString = im.toString();
			this.submitButton.setEnabled(true);
		} else {
			imStrings.add("");
			imString = "";
			im = null;
			this.submitButton.setEnabled(false);
		}

		saPeriodParam = new StringParameter(this.SA_PERIOD_SELECTOR_PARAM,
				imStrings,imString);
		saPeriodParam.addParameterChangeListener(this);
	}


	/**
	 * Makes the parameters visible or invisible based on if it is deterministic
	 * or prob. curve.
	 */
	private void makeParamVisible() {
		String curveType = (String)curveTypeSelectorParam.getValue();
		if(curveType.equals(PROB_CURVE)) {
			this.isDeterministic = false;
			application.setCurveType(HazardCurveServerModeApplication.PROBABILISTIC);
		}
		else {
			this.isDeterministic = true;
			application.setCurveType(HazardCurveServerModeApplication.DETERMINISTIC);
		}
		listEditor.getParameterEditor(SRC_INDEX_PARAM).setVisible(isDeterministic);
		listEditor.getParameterEditor(RUP_INDEX_PARAM).setVisible(isDeterministic);
	}

	private void initSGTVarIDsParam() {
		ArrayList<Integer> ids = peakAmps2DB.getSGTVarIDs();
		ArrayList<String> vals = new ArrayList<String>();
		for (int val : ids) {
			vals.add(val + "");
		}
		sgtVarParam = new StringParameter(SGT_VAR_PARAM, vals, vals.get(0));
		sgtVarParam.addParameterChangeListener(this);
	}

	private void initRupVarScenarioIDsParam() {
		ArrayList<Integer> ids = peakAmps2DB.getRupVarScenarioIDs();
		ArrayList<String> vals = new ArrayList<String>();
		for (int val : ids) {
			vals.add(val + "");
		}
		rupVarScenarioParam = new StringParameter(RUP_VAR_SCENARIO_PARAM, vals, vals.get(0));
		rupVarScenarioParam.addParameterChangeListener(this);
	}

	/**
	 * Creates the Src Id selection parameter displaying all the src ids for a given Cybershake
	 * site for which deterministic calculations can be done.
	 */
	private void initSrcIndexParam(){
		selectedSrcId = -1;
		System.out.println("Updating SRC Indices with ERF ID="+selectedERF.id);
		ArrayList srcIdList = this.csSites.getSrcIDsForSite(selectedSite.short_name, selectedERF.id);
		int size = srcIdList.size();
		if (size > 0) {
			selectedSrcId = ((Integer)srcIdList.get(0));
			
			for(int i=0;i<size;++i)
				srcIdList.set(i, ""+srcIdList.get(i));
		} else {
			srcIdList.add("" + selectedSrcId);
		}

		srcIndexParam = new StringParameter(SRC_INDEX_PARAM,srcIdList,"" + selectedSrcId);
		srcIndexParam.addParameterChangeListener(this);
	}

	/**
	 * Creates the Rupture Id sel = -1;ection parameter displaying all the rup ids for a given Cybershake
	 * site for which deterministic calculations can be done.
	 */
	private void initRupIndexParam(){
		System.out.println("Updating Rup Indices with ERF ID="+selectedERF.id);
		ArrayList rupIdList = this.csSites.getRupIDsForSite(selectedSite.short_name, selectedERF.id, selectedSrcId);
		int size = rupIdList.size();
		if (size > 0) {
			for(int i=0;i<size;++i)
				rupIdList.set(i, ""+rupIdList.get(i));
		} else {
			rupIdList.add(""+(-1));
		}
		
		rupIndexParam = new StringParameter(RUP_INDEX_PARAM,rupIdList,(String)rupIdList.get(0));   
		rupIndexParam.addParameterChangeListener(this);
	}

	private void reloadParams() {
		initSrcIndexParam();
		initRupIndexParam();
		this.loadSA_PeriodParam();
		listEditor.replaceParameterForEditor(SA_PERIOD_SELECTOR_PARAM,saPeriodParam);
		listEditor.replaceParameterForEditor(SRC_INDEX_PARAM,srcIndexParam);
		listEditor.replaceParameterForEditor(RUP_INDEX_PARAM,rupIndexParam);
		this.publishButton.setEnabled(false);
	}

	/**
	 * Updates the list editor when user changes the Cybershake site
	 * @param e ParameterChangeEvent
	 */
	public void parameterChange (ParameterChangeEvent e){
		String paramName = e.getParameterName();
		if(paramName.equals(SITE_SELECTOR_PARAM)){
			selectedSite = sites.get(siteNames.indexOf((String)siteSelectionParam.getValue()));
//			selectedSite = (String)siteSelectionParam.getValue();
			//initSA_PeriodParam();
			this.reloadParams();
		} else if (paramName.equals(ERF_SELECTOR_PARAM)) {
			selectedERF = erfs.get(erfNames.indexOf((String)erfParam.getValue()));
			this.reloadParams();
		} else if (paramName.equals(SGT_VAR_PARAM)) {
			selectedSGTVariation = Integer.parseInt((String)sgtVarParam.getValue());
			this.reloadParams();
		} else if (paramName.equals(RUP_VAR_SCENARIO_PARAM)) {
			selectedRupVarScenario = Integer.parseInt((String)rupVarScenarioParam.getValue());
			this.reloadParams();
		}
		else if(paramName.equals(SRC_INDEX_PARAM)){
			String srcId = (String)this.srcIndexParam.getValue();
			selectedSrcId = Integer.parseInt(srcId);
			initRupIndexParam();
			listEditor.replaceParameterForEditor(RUP_INDEX_PARAM,rupIndexParam);
		}
		else if(paramName.equals(RUP_INDEX_PARAM))
			selectedRupId = Integer.parseInt((String)this.rupIndexParam.getValue());
		else if(paramName.equals(SA_PERIOD_SELECTOR_PARAM)){
			imString = (String)saPeriodParam.getValue();
			im = null;
			for (CybershakeIM newIM : ims) {
				if (newIM.toString().equals(imString)) {
					im = newIM;
					prevIMVal = im.getVal();
					int index = ims.indexOf(newIM);
					ampsInDB = false;
					curveInDB = false;
					for (int id : dbCurves) {
						if (id == index) {
							curveInDB = true;
							break;
						}
					}
					for (int id : ampCurves) {
						if (id == index) {
							ampsInDB = true;
							break;
						}
					}
					break;
				}
			}
			if (im == null)
				throw new RuntimeException("IM String not matched with an IM!");
			System.out.println("IM = "+imString);
		}
		else if(paramName.equals(DETER_PROB_SELECTOR_PARAM)) {
			initSrcIndexParam();
			initRupIndexParam();
			listEditor.replaceParameterForEditor(SRC_INDEX_PARAM,srcIndexParam);
			listEditor.replaceParameterForEditor(RUP_INDEX_PARAM,rupIndexParam);
			this.makeParamVisible();
		}

		listEditor.refreshParamEditor();
	}


	/**
	 * Gets the hazard data from the Cybershake site for the given SA period.
	 * @return ArrayList Hazard Data
	 * @throws RuntimeException
	 */
	private DiscretizedFuncAPI getHazardData(ArrayList imlVals) {
		DiscretizedFuncAPI cyberShakeHazardData = null;
		boolean dbCurve = false;
		
		int siteID = this.selectedSite.id;
		int erfID = this.selectedERF.id;
		int rupVarID = this.selectedRupVarScenario;
		int sgtID = this.selectedSGTVariation;
		int imID = this.im.getID();
		
		if (curveInDB) {
			dbCurve = true;
			if (ampsInDB) {
				// the curve and the amps are both in the database, promt the user
				String message = "A hazard curve already exists for these parameters.\nDo you wish to plot this curve (otherwise curve\n" +
						"will be recalculated)?";
				int response = JOptionPane.showConfirmDialog(frame, message, "Plot Existing Curve?", JOptionPane.YES_NO_OPTION);
				if (response == JOptionPane.NO_OPTION) {
					dbCurve = false;
				}
			}
		}
		
		if (dbCurve) {
			System.out.println("Computing a hazard curve from db for " + selectedSite);
			int id = curve2db.getHazardCurveID(siteID, erfID, rupVarID, sgtID, imID);
			cyberShakeHazardData = curve2db.getHazardCurve(id);
			this.publishButton.setEnabled(false);
		} else {
			System.out.println("Computing a hazard curve for " + selectedSite);
			cyberShakeHazardData= hazCurve.computeHazardCurve(imlVals,selectedSite.short_name,
					erfID, sgtID, rupVarID, im);
			this.publishButton.setEnabled(true);
			currentHazardCurve = cyberShakeHazardData;
		}

		return cyberShakeHazardData;
	}


	/**
	 * 
	 * @return ArbitrarilyDiscretizedFunc Determinitic curve data
	 * @throws RuntimeException
	 */
	private DiscretizedFuncAPI getDeterministicData(ArrayList imlVals) throws
	RuntimeException {
		DiscretizedFuncAPI cyberShakeDeterminicticHazardCurve = hazCurve.computeDeterministicCurve(imlVals, selectedSite.short_name,
				this.selectedERF.id, selectedSGTVariation, selectedRupVarScenario,
				selectedSrcId, selectedRupId, im);

		return cyberShakeDeterminicticHazardCurve;
	}


	/**
	 * Sets the parameters in the OpenSHA application similar to what
	 * is required  by the Cybershake.
	 * @param actionEvent ActionEvent
	 */
	private void paramSettingButton_actionPerformed(ActionEvent actionEvent) {
		setSiteParams();
		setIMR_Params();
		boolean imtSet = setIMT_Params();

		if(!imtSet)
			return;
		application.setCurveXValues(createUSGS_PGA_Function());

		if(isDeterministic)
			setEqkSrcRupSelectorParams();
		else
			setEqkRupForecastParams();
	}
	
	private void setRobPlotParams(ActionEvent actionEvent) {
		this.setPlotLabels();
		float period = (float)this.getPeriodDouble();
		application.setY_Log(true);
		double xMin = 0.0;
		double xMax = 2;
		if (Math.abs(period - 3) < 0.05)
			xMax = 2.0;
		else if (Math.abs(period - 5) < 0.05)
			xMax = 1.0;
		else if (Math.abs(period - 10) < 0.05)
			xMax = 0.5;
		double yMin = Double.parseDouble("1.0E-6");
		double yMax = 1.0;
		application.setAxisRange(xMin, xMax, yMin, yMax);
	}
	
	private void setTomPlotParams(ActionEvent actionEvent) {
		if (isDeterministic)
			return;
//		float period = (float)this.getPeriodDouble();
		double xMin = Double.parseDouble("1.0E-2");
		double xMax = 3;
		double yMin = Double.parseDouble("1.0E-5");
		double yMax = 0.2;
		application.setAxisRange(xMin, xMax, yMin, yMax);
		
		setSiteParams();
		setEqkRupForecastParams();
		application.setCurveXValues(createUSGS_PGA_Function());
		
		ArrayList<PlotCurveCharacterstics> chars = application.getPlottingFeatures();
		
		// assume cybershake is first
		if (chars.size() >= 1) {
			PlotCurveCharacterstics csCurve = chars.get(0);
			csCurve.setCurveColor(Color.RED);
		}
		// assume CB 2008 is next
		if (chars.size() >= 2) {
			PlotCurveCharacterstics csCurve = chars.get(1);
			csCurve.setCurveColor(new Color(0, 100, 0));
		}
		// assume BA 2008 is next
		if (chars.size() >= 3) {
			PlotCurveCharacterstics csCurve = chars.get(2);
			csCurve.setCurveColor(Color.BLACK);
		}
		
		this.setPlotLabels();
		
		application.getButtonControlPanel().setTickLabelFontSize(14);
		application.getButtonControlPanel().setPlotLabelFontSize(14);
		application.getButtonControlPanel().setAxisLabelFontSize(14);
		application.getGraphPanel().setPlotBackgroundColor(Color.white);
		
//		application.setProgressCheckBoxSelected(false);
		
//		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
//		func.set(0d, Double.parseDouble("1.0E-4"));
//		func.set(10d, Double.parseDouble("1.0E-4"));
//		application.addCybershakeCurveData(func);
		
//		imrGui.set
		
		application.setY_Log(true);
		application.setX_Log(true);
		application.getGraphPanel().setPlotBackgroundColor(Color.white);
	}
	
	private void setPlotLabels() {
		String name = this.selectedSite.name;
		String short_name = this.selectedSite.short_name;
		if (name.equals(short_name))
			application.setPlotLabel(name);
		else
			application.setPlotLabel(name + " (" + short_name + ")");
		float period = (float)im.getVal();
		period = period * 100f;
		period = (float)(int)(period + 0.5f) / 100f;
		application.setXAxisLabel(period + "s SA (g)");
		application.setYAxisLabel("Probability Rate (1/yr)");
	}

	/**
	 * Retreives the Cybershake data and plots it in the application.
	 * @param actionEvent ActionEvent
	 */
	private void submitButton_actionPerformed(ActionEvent actionEvent) {
		ArrayList imlVals = application.getIML_Values();
		DiscretizedFuncAPI curveData = null;

		String infoString = "Site: "+ sites.get(siteNames.indexOf((String)siteSelectionParam.getValue())) + ";\n";
		infoString += "ERF: " + this.selectedERF + ";\n";
		infoString += "SGT Variation ID: " + this.selectedSGTVariation + "; Rup Var Scenario ID: " + this.selectedRupVarScenario + ";\n";
		infoString += "SA Period: " + (String)saPeriodParam.getValue() + ";\n";

		if(isDeterministic){
			curveData = getDeterministicData(imlVals);
			String name = "Cybershake deterministic curve";
			infoString += "SourceIndex = "+selectedSrcId+
			"; RuptureIndex = "+selectedRupId;
			curveData.setName(name);
			curveData.setInfo(infoString);
			application.addCybershakeCurveData(curveData);
		}
		else{
//			if (calcProgress == null)
//			calcProgress = new CalcProgressBar("CyberShake Calculation Progress", "Source");
//			calcProgress.setVisible(true);
//			calcProgress.displayProgressBar();
			curveData = this.getHazardData(imlVals);
//			calcProgress.setVisible(false);
			if (curveData == null) {
				JOptionPane.showMessageDialog(frame,
						"There are no Peak Amplitudes in the database for the selected paremters.\n ");
				return;
			}
			String name = "Cybershake hazard curve";
			curveData.setName(name);
			curveData.setInfo(infoString);
			application.addCybershakeCurveData(curveData);

		}
	}
	
	/**
	 * Publishes the curve to the database
	 * @param actionEvent ActionEvent
	 */
	private void commitButton_actionPerformed(ActionEvent actionEvent) {
		try {
			this.putCurveInDB();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}


	/**
	 * This sets the site parameters in the OpenSHA application
	 * based on the chosen Cybershake site
	 */
	private void setSiteParams(){
		Site_GuiBean site = application.getSiteGuiBeanInstance();
		String cyberShakeSite = sites.get(siteNames.indexOf((String)siteSelectionParam.getValue())).short_name;
		Location loc = csSites.getCyberShakeSiteLocation(cyberShakeSite);
		site.getParameterListEditor().getParameterEditor(site.LATITUDE).setValue(new Double(loc.getLatitude()));
		site.getParameterListEditor().getParameterEditor(site.LONGITUDE).setValue(new Double(loc.getLongitude()));
		site.getParameterListEditor().refreshParamEditor();
		application.getCVMControl().setSiteParams();
	}

	/**
	 * Set the Eqk Rup Forecast in the OpenSHA application similar to eqk forecast
	 * params used to do the cybershake calculations.
	 */
	private void setEqkRupForecastParams(){
		ERF_GuiBean gui = application.getEqkRupForecastGuiBeanInstance();
		ParameterListEditor editorList = gui.getERFParameterListEditor();
		String erfName = selectedERF.name;
		if (erfName.endsWith("/08") || erfName.endsWith("/09")) {
			// remove date tags
			erfName = erfName.trim();
			erfName = erfName.substring(0, erfName.lastIndexOf(" "));
			erfName = erfName.trim();
		}
		gui.getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(erfName);
		gui.getERFParameterListEditor().refreshParamEditor();
		gui.getParameter(UCERF2.BACK_SEIS_NAME).setValue(UCERF2.BACK_SEIS_EXCLUDE);
		gui.getParameter(MeanUCERF2.RUP_OFFSET_PARAM_NAME).setValue(new Double(5.0));
		gui.getParameter(MeanUCERF2.CYBERSHAKE_DDW_CORR_PARAM_NAME).setValue(new Boolean(true));
		gui.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_POISSON);

		TimeSpanGuiBean timespan = gui.getSelectedERFTimespanGuiBean();
		timespan.getTimeSpan().setDuration(1.0);
		gui.getERFParameterListEditor().refreshParamEditor();
		timespan.getParameterListEditor().refreshParamEditor();
	}

	/**
	 * Select the same source and rupture in the OpenSHA application for deterministic calculations,
	 * similar to eqk forecast params used to do the cybershake calculations.
	 */
	private void setEqkSrcRupSelectorParams(){
		EqkRupSelectorGuiBean erfRupSelectorGuiBean = application.getEqkSrcRupSelectorGuiBeanInstance();
		erfRupSelectorGuiBean.getParameterEditor(erfRupSelectorGuiBean.RUPTURE_SELECTOR_PARAM_NAME).
		setValue(erfRupSelectorGuiBean.RUPTURE_FROM_EXISTING_ERF);

		EqkRupSelectorGuiBeanAPI erfRupSelGuiBean = erfRupSelectorGuiBean.getEqkRuptureSelectorPanel();
		EqkRuptureFromERFSelectorPanel rupGuiBean = (EqkRuptureFromERFSelectorPanel)erfRupSelGuiBean;
		rupGuiBean.showAllParamsForForecast(false);
		rupGuiBean.getParameterListEditor().getParameterEditor(rupGuiBean.ERF_PARAM_NAME).
		setValue(ERF_NAME);
		ERF_GuiBean erfGuiBean = rupGuiBean.getERF_ParamEditor();
		ParameterListEditor editorList = erfGuiBean.getERFParameterListEditor();
		editorList.getParameterEditor(erfGuiBean.ERF_PARAM_NAME).setValue(ERF_NAME);
		editorList.getParameterEditor(UCERF2.BACK_SEIS_NAME).setValue(UCERF2.BACK_SEIS_EXCLUDE);
		editorList.getParameterEditor(MeanUCERF2.RUP_OFFSET_PARAM_NAME).setValue(new Double(5.0));
		editorList.getParameterEditor(MeanUCERF2.CYBERSHAKE_DDW_CORR_PARAM_NAME).setValue(new Boolean(true));
		editorList.getParameterEditor(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_POISSON);

		TimeSpanGuiBean timespan = erfGuiBean.getSelectedERFTimespanGuiBean();
		timespan.getTimeSpan().setDuration(1.0);
		erfGuiBean.getERFParameterListEditor().refreshParamEditor();
		timespan.getParameterListEditor().refreshParamEditor();
		//rupGuiBean.updateERFAndSourceRupList();
		//rupGuiBean.getParameterListEditor().refreshParamEditor();
		try {
			EqkRupForecastAPI erf = (EqkRupForecastAPI) erfGuiBean.getSelectedERF();
			rupGuiBean.setEqkRupForecast(erf);
		}
		catch (InvocationTargetException ex) {
		}
		String srcIndex = (String)srcIndexParam.getValue();
		int srcNum = Integer.parseInt(srcIndex.trim());
		String rupIndex = (String)rupIndexParam.getValue();
		rupGuiBean.setSourceFromSelectedERF(srcNum);
		rupGuiBean.setRuptureForSelectedSource(Integer.parseInt(rupIndex));
		rupGuiBean.showAllParamsForForecast(true);
	}

	private void setIMR_Params(){
		IMR_MultiGuiBean imrGui = application.getIMRGuiBeanInstance();
		ScalarIntensityMeasureRelationshipAPI imr = imrGui.getSelectedIMR();
//		SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED;

		try {
			StringParameter truncTypeParam = (StringParameter)imr.getParameter(SigmaTruncTypeParam.NAME);

			truncTypeParam.setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);

			DoubleParameter truncLevelParam = (DoubleParameter)imr.getParameter(SigmaTruncLevelParam.NAME);

			truncLevelParam.setValue(3.0);

			imrGui.rebuildGUI();
		} catch (ParameterException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	/**
	 * Select the IMT and SA Period in the OpenSHA application similar to that chosen
	 * in Cybershake control panel.
	 */
	private boolean setIMT_Params(){
		IMT_NewGuiBean imtGui = application.getIMTGuiBeanInstance();
		DecimalFormat format = new DecimalFormat("0.00");
		imtGui.getParameterEditor(IMT_NewGuiBean.IMT_PARAM_NAME).setValue("SA");
		double saPeriodVal = this.im.getVal();
		DoubleDiscreteParameter saPeriodParam = (DoubleDiscreteParameter)imtGui.getParameterEditor(PeriodParam.NAME).getParameter();
		ArrayList allowedVals = saPeriodParam.getAllowedDoubles();
		int size = allowedVals.size();
		double minSaVal = ((Double)allowedVals.get(0)).doubleValue();
		double maxSaVal = ((Double)allowedVals.get(size -1)).doubleValue();
		if ( (saPeriodVal < minSaVal) || (saPeriodVal > maxSaVal)) {
			JOptionPane.showMessageDialog(frame,
					"This attenuation does not support the SA Period\n " +
					"selected in cybershake control panel. Either choose a \n different Attenuation " +
			"Relationship or a different SA Period");
			return false;
		}
		else {
			for (int i = 0; i < size-1; ++i) {
				double saVal_first = Double.parseDouble(format.format(((Double)allowedVals.get(i)).doubleValue()));
				double saVal_second = Double.parseDouble(format.format(((Double)allowedVals.get(i+1)).doubleValue()));
				if(saPeriodVal >= saVal_first && saPeriodVal <= saVal_second){
					if((saPeriodVal - saVal_first) <= (saVal_second - saPeriodVal))
						imtGui.getParameterEditor("SA Period").setValue((Double)allowedVals.get(i));
					else
						imtGui.getParameterEditor("SA Period").setValue((Double)allowedVals.get(i+1));
					break;
				}
			}
		}
		imtGui.refreshParamEditor();
		return true;
	}

	private double getPeriodDouble() {
		return this.im.getVal();
	}

	private void putCurveInDB() throws IOException {
		
		int siteID = this.selectedSite.id;
		int erfID = this.selectedERF.id;
		int rupVarID = this.selectedRupVarScenario;
		int sgtID = this.selectedSGTVariation;
		int imID = this.im.getID();
		
		boolean overwrite = false;
		
		int id = curve2db.getHazardCurveID(siteID, erfID, rupVarID, sgtID, imID);
		
		// check to see if it's already in there
		
		if (id >= 0) {
			String message = "A hazard curve already exists for these parameters.\nOverwite curve? (otherwise curve curve will\n" +
			"be added with original curve left untouched)?";
			int response = JOptionPane.showConfirmDialog(frame, message, "Overwrite Existing Curve?", JOptionPane.YES_NO_CANCEL_OPTION);
			if (response == JOptionPane.YES_OPTION) {
				overwrite = true;
			} else if (response == JOptionPane.CANCEL_OPTION) {
				return;
			}
		}
		
		String user, pass;
		
		if (prevPass.length() == 0 && prevUser.length() == 0) {
			UserAuthDialog dialog = new UserAuthDialog(frame, false);
			
			dialog.setVisible(true);
			
			if (dialog.isCanceled())
				return;
			
			pass = new String(dialog.getPassword());
			user = dialog.getUsername();
		} else {
			user = prevUser;
			pass = prevPass;
		}
		
		boolean fail = true;
		DBAccess db = null;
		while (fail) {
			try {
				db = new DBAccess(Cybershake_OpenSHA_DBApplication.HOST_NAME, Cybershake_OpenSHA_DBApplication.DATABASE_NAME, user, pass);
				fail = false;
			} catch (IOException e) {
				e.printStackTrace();
				
				UserAuthDialog dialog = new UserAuthDialog(frame, false);
				
				if (dialog.isCanceled())
					return;
				
				dialog.setVisible(true);
				
				pass = new String(dialog.getPassword());
				user = dialog.getUsername();
			}
		}
		
		prevUser = user;
		prevPass = pass;
		
		HazardCurve2DB curve2db = new HazardCurve2DB(db);
		
		if (overwrite)
			curve2db.replaceHazardCurve(id, currentHazardCurve);
		else {
			int runID = runs2db.getRunIDs(siteID, erfID, sgtID, rupVarID, null, null, null, null).get(0);
			curve2db.insertHazardCurve(runID,
					imID, currentHazardCurve);
		}
		this.loadSA_PeriodParam();
		listEditor.replaceParameterForEditor(SA_PERIOD_SELECTOR_PARAM,saPeriodParam);
		this.publishButton.setEnabled(false);
		db.destroy();
	}

	/**
	 * initialises the function with the x and y values if the user has chosen the USGS-PGA X Vals
	 * the y values are modified with the values entered by the user
	 */
	public static ArbitrarilyDiscretizedFunc createUSGS_PGA_Function() {
		ArbitrarilyDiscretizedFunc function = new ArbitrarilyDiscretizedFunc();
//		function.set(.005, 1);
//		function.set(.007, 1);
//		function.set(.0098, 1);
//		function.set(.0137, 1);
//		function.set(.0192, 1);
//		function.set(.0269, 1);
//		function.set(.0376, 1);
//		function.set(.0527, 1);
//		function.set(.0738, 1);
//		function.set(.103, 1);
//		function.set(.145, 1);
//		function.set(.203, 1);
//		function.set(.284, 1);
//		function.set(.397, 1);
//		function.set(.556, 1);
//		function.set(.778, 1);
//		function.set(1.09, 1);
//		function.set(1.52, 1);
//		function.set(2.13, 1);
		
		function.set(0.0001,1);
	    function.set(0.00013,1);
		function.set(0.00016,1);
		function.set(0.0002,1);
		function.set(0.00025,1);
		function.set(0.00032,1);
		function.set(0.0004,1);
		function.set(0.0005,1);
		function.set(0.00063,1);
		function.set(0.00079,1);
		function.set(0.001,1);
		function.set(0.00126,1);
		function.set(0.00158,1);
		function.set(0.002,1);
		function.set(0.00251,1);
		function.set(0.00316,1);
		function.set(0.00398,1);
		function.set(0.00501,1);
		function.set(0.00631,1);
		function.set(0.00794,1);
		function.set(0.01,1);
		function.set(0.01259,1);
		function.set(0.01585,1);
		function.set(0.01995,1);
		function.set(0.02512,1);
		function.set(0.03162,1);
		function.set(0.03981,1);
		function.set(0.05012,1);
		function.set(0.0631,1);
		function.set(0.07943,1);
		function.set(0.1,1);
		function.set(0.12589,1);
		function.set(0.15849,1);
		function.set(0.19953,1);
		function.set(0.25119,1);
		function.set(0.31623,1);
		function.set(0.39811,1);
		function.set(0.50119,1);
		function.set(0.63096,1);
		function.set(0.79433,1);
		function.set(1d,1d);
		function.set(1.25893,1);
		function.set(1.58489,1);
		function.set(1.99526,1);
		function.set(2.51189,1);
		function.set(3.16228,1);
		function.set(3.98107,1);
		function.set(5.01187,1);
		function.set(6.30957,1);
		function.set(7.94328,1);
		function.set(10d,1d);
		return function;
	}

	@Override
	public Window getComponent() {
		return frame;
	}

//	public void setProgressIndeterminate(boolean indeterminate) {
//	if (calcProgress != null)
//	calcProgress.setProgressIndeterminate(indeterminate);
//	}

//	public void setProgressMessage(String message) {
//	if (calcProgress != null)
//	calcProgress.setProgressMessage(message);
//	}

//	public void setProgress(int currentIndex, int total) {
//	if (calcProgress != null) {
//	System.out.println("Updating progress: " + currentIndex + " " + total);
//	calcProgress.updateProgress(currentIndex, total);
//	}
//	}

}
